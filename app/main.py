# FastAPI Server
# Full endpoint for wazuh.search 

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from .schemas import WazuhSearchPlan
from .validators import is_index_allowed, validate_filters, enforce_time_window
from .dsl_builder import build_dsl
from .es_client import validate_query, execute_query
from .llm_client import ask_openai
from .wazuh_client import WazuhClient
from .config import settings
from mcp import MCPHandlers
import logging

app = FastAPI(title = "MCP Server for Wazuh")

# CORS - allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],                                                                                                                                                                
    allow_headers=["*"],
)

# Initialize Wazuh client and MCP handlers on startup
wazuh_client = None
mcp_handlers = None

@app.on_event("startup")
async def startup_event():
    global wazuh_client, mcp_handlers
    wazuh_url = f"{settings.WAZUH_API_HOST}:{settings.WAZUH_API_PORT}"
    wazuh_client = WazuhClient(wazuh_url, settings.WAZUH_API_USERNAME, settings.WAZUH_API_PASSWORD)
    await wazuh_client.authenticate()
    
    # Initialize MCP handlers
    mcp_handlers = MCPHandlers(
        wazuh_url=wazuh_url,
        username=settings.WAZUH_API_USERNAME,
        password=settings.WAZUH_API_PASSWORD
    )
    await mcp_handlers.client.authenticate()
    
    if wazuh_client.token:
        logging.info(f"✓ Wazuh authenticated successfully")
        logging.info(f"✓ MCP handlers initialized")
    else:
        logging.error("✗ Wazuh authentication failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    global wazuh_client, mcp_handlers
    if wazuh_client:
        await wazuh_client.close()
        logging.info("✓ Wazuh client closed")
    if mcp_handlers:
        await mcp_handlers.close()
        logging.info("✓ MCP handlers closed")

@app.get("/")
def home():
    return {
        "message": "Welcome to the MCP Server for Wazuh. The MCP Server has been started successfully.",
        "authenticated": wazuh_client.token is not None if wazuh_client else False,
        "wazuh_url": f"{settings.WAZUH_API_HOST}:{settings.WAZUH_API_PORT}",
        "mcp_enabled": mcp_handlers is not None
    }

@app.get("/health")
async def health_check():
    """MCP Health check endpoint"""
    if not mcp_handlers:
        raise HTTPException(status_code=503, detail="MCP handlers not initialized")
    
    health_status = await mcp_handlers.mcp_health_check()
    return health_status

@app.get("/agents")
async def get_wazuh_agents():
    """Get all Wazuh agents"""
    if not wazuh_client or not wazuh_client.token:
        raise HTTPException(status_code=401, detail="Not authenticated to Wazuh")
    
    result = await wazuh_client.get_agents()
    return result

@app.get("/test")
async def test_wazuh_connection():
    """Test Wazuh connection"""
    if not wazuh_client or not wazuh_client.token:
        raise HTTPException(status_code=401, detail="Not authenticated to Wazuh")
    
    result = await wazuh_client.get_agents()
    agents = result.get("agents", [])
    return {
        "status": "connected",
        "token_valid": True,
        "agents_count": len(agents),
        "sample_agents": [{"id": a["id"], "name": a["name"], "status": a["status"]} for a in agents[:3]]
    }

# ✅ Natural Language Query Endpoint (Complete Flow with DSL)
@app.post("/query/")
async def natural_language_query(data: dict):
    """
    Natural language query endpoint with complete LLM + DSL flow:
    User Query → LLM Parse → WazuhSearchPlan → DSL Builder → Indexer → LLM Format → Natural Response
    
    Example: {"query": "Show me critical alerts from the last 24 hours"}
    """
    from .llm_client import parse_natural_language_query, format_wazuh_response
    
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        # Step 1: LLM parses natural language to WazuhSearchPlan structure
        parsed = parse_natural_language_query(query)
        logging.info(f"Parsed query: {parsed}")
        
        # Step 2: Validate and create WazuhSearchPlan
        try:
            plan = WazuhSearchPlan(**parsed)
        except ValidationError as e:
            logging.error(f"Invalid search plan: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid query structure: {str(e)}")
        
        # Step 3: Validate plan
        if not is_index_allowed(plan.indices):
            raise HTTPException(400, "Index not allowed")
        if not enforce_time_window(plan.time.from_, plan.time.to):
            raise HTTPException(400, "Time window too large or invalid")
        
        try:
            validate_filters(plan.filters or [])
            validate_filters(plan.must_not or [])
        except Exception as e:
            raise HTTPException(400, f"Invalid filters: {str(e)}")
        
        # Step 4: Build DSL from plan
        dsl = build_dsl(plan)
        logging.info(f"Generated DSL: {dsl}")
        
        # Step 5: Execute query against Wazuh Indexer
        raw_data = execute_query(plan.indices, dsl)
        logging.info(f"Query results: {raw_data.get('hits', {}).get('total', 0)} hits")
        
        # Step 6: LLM formats response to natural language
        natural_response = format_wazuh_response(raw_data, query)
        
        return {
            "query": query,
            "parsed_plan": parsed,
            "dsl": dsl,
            "raw_data": raw_data,
            "response": natural_response
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Natural language query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# ✅ Simple Natural Language Query (Wazuh API - No DSL)
@app.post("/query/simple")
async def simple_natural_language_query(data: dict):
    """
    Simple natural language query using Wazuh API directly (no DSL).
    Faster but less flexible than /query/ endpoint.
    
    Example: {"query": "Show me recent alerts"}
    """
    from .llm_client import format_wazuh_response
    
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if not wazuh_client or not wazuh_client.token:
        raise HTTPException(status_code=401, detail="Not authenticated to Wazuh")
    
    try:
        # Simple keyword detection for query routing
        query_lower = query.lower()
        
        if "agent" in query_lower:
            raw_data = await wazuh_client.get_agents()
        else:
            # Default to alerts with basic params
            limit = 50
            if "critical" in query_lower:
                raw_data = await wazuh_client.get_alerts(severity="12", limit=limit)
            elif "high" in query_lower:
                raw_data = await wazuh_client.get_alerts(severity="8", limit=limit)
            else:
                raw_data = await wazuh_client.get_alerts(limit=limit)
        
        # Format response
        natural_response = format_wazuh_response(raw_data, query)
        
        return {
            "query": query,
            "raw_data": raw_data,
            "response": natural_response
        }
    
    except Exception as e:
        logging.exception("Simple query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# ✅ Simple LLM Query (for testing)
@app.post("/query_llm/")
async def query_llm(data: dict):
    """
    Simple endpoint to query OpenAI LLM.
    Example body: { "prompt": "Summarize recent alerts from Wazuh" }
    """
    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    response = ask_openai(prompt)
    return {"response": response}

@app.post("/mcp/wazuh.search")
async def wazuh_search(plan: WazuhSearchPlan):
    # Step 1: index allowlist
    if not is_index_allowed(plan.indices):
        raise HTTPException(400, "index not allowed")
    # Step 2: validate time window
    if not enforce_time_window(plan.time.from_, plan.time.to):
        raise HTTPException(400, "time window too large or invalid")
    # Step 3: validate filters semantics
    try:
        validate_filters(plan.filters or [])
        validate_filters(plan.must_not or [])
    except Exception as e:
        raise HTTPException(400, str(e))
    # Step 4: build DSL server-side
    dsl = build_dsl(plan)
    # Step 5: preflight validate
    if plan.dry_run:
        try:
            v = validate_query(plan.indices, dsl)
            return {"validation": v}
        except Exception as e:
            logging.exception("validate failed")
            raise HTTPException(500, f"validate failed: {e}")
    # Step 6: execute with safe defaults / try-catch
    try:
        res = execute_query(plan.indices, dsl)
        # optionally post-process mask fields etc.
        return {"result": res}
    except Exception as e:
        logging.exception("search failed")
        raise HTTPException(500, f"search failed: {e}")

# ==================== NEW UNIFIED QUERY ENDPOINTS ====================

@app.post("/query/nl")
async def query_natural_language_unified(data: dict):
    """
    Unified Natural Language query endpoint with intelligent routing.
    GPT-4o automatically decides between SIMPLE_PIPELINE and ADVANCED_PIPELINE.
    
    Supports:
    1. Pure NL: "Show me failed logins" → GPT routes & executes
    2. Hybrid NL+DSL: "Analyze this query: {DSL}" → GPT provides insights on DSL results
    3. GPT automatically routes to appropriate pipeline
    
    Example: {"query": "Show me all agents"}
    """
    from .llm_client import route_query, parse_simple_query, parse_query_to_plan, format_results
    import re
    import json
    import time
    
    query = data.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Check if query contains embedded DSL
        embedded_dsl = None
        nl_context = query
        
        # Try to extract JSON from the query
        json_match = re.search(r'\{[\s\S]*\}', query)
        if json_match:
            try:
                potential_dsl = json.loads(json_match.group(0))
                # Validate it looks like a DSL query
                if "query" in potential_dsl or "index" in potential_dsl or "indices" in potential_dsl:
                    embedded_dsl = potential_dsl
                    # Extract the NL part (text before/after the JSON)
                    nl_context = query[:json_match.start()].strip() + " " + query[json_match.end():].strip()
                    nl_context = nl_context.strip() or "Analyze these query results"
                    logging.info("✓ Detected embedded DSL in NL query")
                    logging.info(f"NL Context: {nl_context}")
                    logging.info(f"Embedded DSL: {json.dumps(embedded_dsl, indent=2)}")
            except json.JSONDecodeError:
                # Not valid JSON, treat as pure NL
                pass
        
        # If embedded DSL found, execute it directly with NL insights
        if embedded_dsl:
            logging.info("=== Executing Hybrid NL+DSL Query ===")
            
            start_time = time.time()
            
            # Extract index
            index = embedded_dsl.get("index") or embedded_dsl.get("indices", "wazuh-alerts-*")
            dsl_body = {k: v for k, v in embedded_dsl.items() if k not in ["index", "indices"]}
            
            # Validate index
            if not is_index_allowed(index):
                raise HTTPException(400, "Index not allowed")
            
            # Execute the DSL query
            logging.info(f"Executing DSL on index: {index}")
            raw_results = execute_query(index, dsl_body)
            
            execution_time = time.time() - start_time
            
            # Extract hit count
            hits = raw_results.get("hits", {})
            total_hits = hits.get("total", {})
            if isinstance(total_hits, dict):
                total_count = total_hits.get("value", 0)
            else:
                total_count = total_hits
            
            logging.info(f"✓ DSL executed in {execution_time:.2f}s, found {total_count} results")
            
            # Generate AI insights based on NL context
            logging.info("=== Generating AI Insights ===")
            start_format = time.time()
            
            # Use the NL context to guide the formatting
            formatted_response = await format_results(nl_context, raw_results)
            
            format_time = time.time() - start_format
            logging.info(f"✓ Insights generated in {format_time:.2f}s")
            
            return {
                "pipeline": "HYBRID_NL_DSL",
                "query": query,
                "nl_context": nl_context,
                "embedded_dsl": embedded_dsl,
                "success": True,
                "total_hits": total_count,
                "query_time": f"{execution_time:.2f}s",
                "format_time": f"{format_time:.2f}s",
                "summary": formatted_response,
                "formatted_response": formatted_response,
                "raw_data": raw_results,
                "raw_results": raw_results,
                "dsl": dsl_body,
                "routing": {
                    "pipeline": "HYBRID_NL_DSL",
                    "confidence": 1.0,
                    "reasoning": "Embedded DSL query detected with natural language context for insights"
                }
            }
        
        # Step 1: Route the query (pure NL)
        routing = await route_query(query)
        pipeline = routing["pipeline"]
        logging.info(f"Routing decision: {pipeline} (confidence: {routing['confidence']})")
        
        # Step 2: Execute the appropriate pipeline
        if pipeline == "SIMPLE_PIPELINE":
            # Use Wazuh Manager API for simple queries
            parsed = await parse_simple_query(query)
            logging.info(f"Simple query parsed: {parsed}")
            
            # Execute based on parsed intent
            if parsed["operation"] == "list_agents":
                raw_results = await wazuh_client.get_agents()
                
                # Apply client-side filtering if status is specified
                status_filter = parsed["filters"].get("status")
                if status_filter:
                    agents = raw_results.get("agents", [])
                    filtered_agents = [
                        agent for agent in agents 
                        if agent.get("status", "").lower() == status_filter.lower()
                    ]
                    raw_results = {
                        "total": len(filtered_agents),
                        "agents": filtered_agents,
                        "data": {"affected_items": filtered_agents}
                    }
                else:
                    # Add data wrapper for consistency with API format
                    raw_results["data"] = {"affected_items": raw_results.get("agents", [])}
                    
            elif parsed["operation"] == "get_agent":
                agent_id = parsed["filters"].get("agent_id")
                # Check if get_agent_by_id exists, otherwise filter from get_agents
                if hasattr(wazuh_client, 'get_agent_by_id'):
                    raw_results = await wazuh_client.get_agent_by_id(agent_id)
                else:
                    all_agents = await wazuh_client.get_agents()
                    agents = all_agents.get("agents", [])
                    agent = next((a for a in agents if a.get("id") == agent_id), None)
                    if agent:
                        raw_results = {"data": {"affected_items": [agent]}}
                    else:
                        raw_results = {"data": {"affected_items": []}}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported operation: {parsed['operation']}"
                )
            
            # Format results
            formatted_response = await format_results(query, raw_results)
            
            return {
                "success": True,
                "routing": routing,
                "pipeline": pipeline,
                "parsed_query": parsed,
                "summary": formatted_response,
                "raw_data": raw_results,
                "dsl": None  # No DSL for simple queries
            }
            
        elif pipeline == "ADVANCED_PIPELINE":
            # Use Elasticsearch/OpenSearch Indexer for advanced queries
            import time
            parse_start = time.time()
            parsed_plan = await parse_query_to_plan(query, wazuh_client)
            parse_time = time.time() - parse_start
            logging.info(f"Advanced query plan (parse took {parse_time:.2f}s): {parsed_plan}")
            
            # Create WazuhSearchPlan from parsed data
            try:
                plan = WazuhSearchPlan(**parsed_plan)
            except ValidationError as e:
                logging.error(f"Invalid search plan: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid query structure: {str(e)}")
            
            # Validate plan
            if not is_index_allowed(plan.indices):
                raise HTTPException(400, "Index not allowed")
            if not enforce_time_window(plan.time.from_, plan.time.to):
                raise HTTPException(400, "Time window too large or invalid")
            
            try:
                validate_filters(plan.filters or [])
                validate_filters(plan.must_not or [])
            except Exception as e:
                raise HTTPException(400, f"Invalid filters: {str(e)}")
            
            # Build DSL query
            dsl_query = build_dsl(plan)
            logging.info(f"Generated DSL: {dsl_query}")
            
            # Execute query
            query_start = time.time()
            raw_results = execute_query(plan.indices, dsl_query)
            query_time = time.time() - query_start
            total_hits = raw_results.get('hits', {}).get('total', 0)
            logging.info(f"Query results: {total_hits} hits (query took {query_time:.2f}s)")
            
            # Format results
            format_start = time.time()
            formatted_response = await format_results(query, raw_results)
            format_time = time.time() - format_start
            logging.info(f"Results formatted (took {format_time:.2f}s)")
            
            return {
                "success": True,
                "routing": routing,
                "pipeline": pipeline,
                "parsed_query": parsed_plan,
                "summary": formatted_response,
                "raw_data": raw_results,
                "dsl": dsl_query
            }
        
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown pipeline: {pipeline}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Unified NL query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/query/dsl")
async def query_direct_dsl(data: dict):
    """
    Direct DSL query endpoint for advanced users with optional LLM summarization.
    Accepts raw OpenSearch DSL queries.
    
    Example: {"index": "wazuh-alerts-*", "query": {...}, "size": 50, "sort": [...], "include_summary": true}
    """
    from .llm_client import format_results
    import time
    import json
    
    index = data.get("index", "wazuh-alerts-*")
    include_summary = data.get("include_summary", True)  # Default to true
    
    # Extract the query body (everything except 'index' and 'include_summary')
    dsl_body = {k: v for k, v in data.items() if k not in ["index", "include_summary"]}
    
    if not dsl_body or (len(dsl_body) == 1 and "query" not in dsl_body):
        raise HTTPException(status_code=400, detail="DSL query body cannot be empty")
    
    try:
        # Validate index
        if not is_index_allowed(index):
            raise HTTPException(400, "Index not allowed")
        
        # Execute the DSL query directly
        start_time = time.time()
        raw_results = execute_query(index, dsl_body)
        execution_time = time.time() - start_time
        
        # Extract hit count
        hits = raw_results.get("hits", {})
        total_hits = hits.get("total", {})
        if isinstance(total_hits, dict):
            total_count = total_hits.get("value", 0)
        else:
            total_count = total_hits
        
        documents = hits.get("hits", [])
        
        logging.info(f"Direct DSL results: {total_count} hits (executed in {execution_time:.2f}s)")
        
        response_data = {
            "success": True,
            "pipeline": "DIRECT_DSL",
            "query_time": f"{execution_time:.2f}s",
            "total_hits": total_count,
            "returned_count": len(documents),
            "raw_data": raw_results,
            "raw_results": raw_results,
            "dsl": dsl_body
        }
        
        # Add GPT summarization if requested
        if include_summary and documents:
            try:
                logging.info("Generating natural language summary for DSL query...")
                
                # Create a simple query context from the DSL
                query_context = f"User executed a direct DSL query on index '{index}'"
                
                # Add filter context
                if "query" in dsl_body and "bool" in dsl_body["query"]:
                    must_filters = dsl_body["query"]["bool"].get("must", [])
                    if must_filters:
                        query_context += " with filters: "
                        filter_descriptions = []
                        for f in must_filters:
                            if "range" in f:
                                field = list(f["range"].keys())[0]
                                filter_descriptions.append(f"{field} time range")
                            elif "term" in f:
                                field = list(f["term"].keys())[0]
                                value = f["term"][field]
                                filter_descriptions.append(f"{field}={value}")
                            elif "terms" in f:
                                field = list(f["terms"].keys())[0]
                                filter_descriptions.append(f"{field} in list")
                        query_context += ", ".join(filter_descriptions)
                
                # Format results with GPT
                start_format = time.time()
                summary = await format_results(query_context, raw_results)
                format_time = time.time() - start_format
                
                response_data["summary"] = summary
                response_data["formatted_response"] = summary
                response_data["format_time"] = f"{format_time:.2f}s"
                logging.info(f"Summary generated successfully in {format_time:.2f}s")
                
            except Exception as summary_error:
                logging.warning(f"Failed to generate summary: {summary_error}")
                response_data["summary"] = None
                response_data["summary_error"] = str(summary_error)
        
        return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Direct DSL query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


async def connect_to_wazuh():
    # Build full URL properly
    wazuh_url = f"{settings.WAZUH_API_HOST}:{settings.WAZUH_API_PORT}"
    username = settings.WAZUH_API_USERNAME
    password = settings.WAZUH_API_PASSWORD

    client = WazuhClient(wazuh_url, username, password, timeout=60)
    await client.authenticate()

    if not client.token:
        print("[!] Failed to authenticate to Wazuh API")
        return

    # Example: Fetch agents
    result = await client.get_agents()
    agents = result.get("agents", [])
    print(f"\n[+] Connected Agents: {len(agents)}")
    for agent in agents[:5]:
        print(f"- ID: {agent['id']}, Name: {agent['name']}, Status: {agent['status']}")

    # Example: Fetch alerts
    alert_result = await client.get_alerts(limit=3)
    alerts = alert_result.get("alerts", [])
    print(f"\n[+] Recent Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"- Timestamp: {alert.get('timestamp', 'N/A')}")
        print(f"  Rule: {alert.get('rule', {}).get('description', 'N/A')}")
        print(f"  Level: {alert.get('rule', {}).get('level', 'N/A')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(connect_to_wazuh())
    # Start server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




    


    



    
    


        
    

    
