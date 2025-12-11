# FastAPI Server
# Full endpoint for wazuh.search 

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from .schemas import WazuhSearchPlan
from .validators import is_index_allowed, validate_filters, enforce_time_window
from .dsl_builder import build_dsl
from .es_client import validate_query, execute_query
from .llm_client import ask_openai
from .wazuh_client import WazuhClient
from .config import settings
import logging

app = FastAPI(title = "MCP Server for Wazuh")

# Initialize Wazuh client on startup
wazuh_client = None

@app.on_event("startup")
async def startup_event():
    global wazuh_client
    wazuh_url = f"{settings.WAZUH_API_HOST}:{settings.WAZUH_API_PORT}"
    wazuh_client = WazuhClient(wazuh_url, settings.WAZUH_API_USERNAME, settings.WAZUH_API_PASSWORD)
    await wazuh_client.authenticate()
    if wazuh_client.token:
        logging.info(f"✓ Wazuh authenticated successfully")
    else:
        logging.error("✗ Wazuh authentication failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    global wazuh_client
    if wazuh_client:
        await wazuh_client.close()
        logging.info("✓ Wazuh client closed")

@app.get("/")
def home():
    return {
        "message": "Welcome to the MCP Server for Wazuh. The MCP Server has been started successfully.",
        "authenticated": wazuh_client.token is not None if wazuh_client else False,
        "wazuh_url": f"{settings.WAZUH_API_HOST}:{settings.WAZUH_API_PORT}"
    }

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




    


    



    
    


        
    

    
