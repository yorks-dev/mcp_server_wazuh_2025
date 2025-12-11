import datetime
from typing import Optional, Dict, Any

from mcp.schemas import (
    AlertQuery,
    HealthStatus,
)
from app.wazuh_client import WazuhClient
from app.llm_client import parse_natural_language_query, format_wazuh_response
from app.dsl_builder import build_dsl
from app.schemas import WazuhSearchPlan
from app.es_client import execute_query
from app.validators import is_index_allowed, validate_filters, enforce_time_window

class MCPHandlers:
    """
    Responsible for executing all MCP-visible tools.
    Clean separation between tools.json and implementation logic.
    """
    def __init__(self, wazuh_url: str, username: str, password: str, timeout: int = 60):
        self.client = WazuhClient(wazuh_url, username, password, timeout)
    # -------------------------------------------------------------
    # 🔥 FETCH ALERTS
    # -------------------------------------------------------------
    async def wazuh_get_alerts(self, params: Dict[str, Any]):
        query = AlertQuery(**params)
        raw_alerts = await self.client.get_alerts(
            agent_id=query.agent_id,
            severity=query.severity,
            limit=query.limit,
        )
        return raw_alerts
    # -------------------------------------------------------------
    # 🔥 FETCH AGENTS
    # -------------------------------------------------------------
    async def wazuh_get_agents(self, _params=None):
        raw_agents = await self.client.get_agents()
        return raw_agents
    # -------------------------------------------------------------
    # 🔥 RESTART MANAGER
    # -------------------------------------------------------------
    async def wazuh_restart_manager(self, _params=None):
        success = await self.client.restart_manager()
        return {"status": "ok" if success else "error"}
    # -------------------------------------------------------------
    # 🔥 MCP HEALTH CHECK
    # -------------------------------------------------------------
    async def mcp_health_check(self, _params=None):
        api_ok = await self.client.check_api()
        indexer_ok = await self.client.check_indexer()

        return HealthStatus(
            mcp_server="running",
            wazuh_api=api_ok,
            wazuh_indexer=indexer_ok,
            timestamp=datetime.datetime.utcnow().isoformat(),
        ).model_dump()
    
    # -------------------------------------------------------------
    # 🔥 NATURAL LANGUAGE QUERY (with DSL Builder)
    # -------------------------------------------------------------
    async def wazuh_natural_query(self, params: Dict[str, Any]):
        """
        Natural language query with LLM + DSL Builder:
        User Query → LLM Parse → WazuhSearchPlan → DSL Builder → Indexer → LLM Format → Natural Response
        """
        query = params.get("query")
        if not query:
            return {"error": "Query is required"}
        
        try:
            # Step 1: Parse natural language to WazuhSearchPlan structure
            parsed = parse_natural_language_query(query)
            
            # Step 2: Create WazuhSearchPlan
            try:
                plan = WazuhSearchPlan(**parsed)
            except Exception as e:
                return {"error": f"Invalid query structure: {str(e)}"}
            
            # Step 3: Validate plan
            if not is_index_allowed(plan.indices):
                return {"error": "Index not allowed"}
            if not enforce_time_window(plan.time.from_, plan.time.to):
                return {"error": "Time window too large or invalid"}
            
            try:
                validate_filters(plan.filters or [])
                validate_filters(plan.must_not or [])
            except Exception as e:
                return {"error": f"Invalid filters: {str(e)}"}
            
            # Step 4: Build DSL from plan
            dsl = build_dsl(plan)
            
            # Step 5: Execute query against Wazuh Indexer
            raw_data = execute_query(plan.indices, dsl)
            
            # Step 6: Format response to natural language
            natural_response = format_wazuh_response(raw_data, query)
            
            return {
                "query": query,
                "parsed_plan": parsed,
                "dsl": dsl,
                "raw_data": raw_data,
                "response": natural_response
            }
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
    
    # -------------------------------------------------------------
    # 🔥 SIMPLE NATURAL LANGUAGE QUERY (Wazuh API)
    # -------------------------------------------------------------
    async def wazuh_simple_query(self, params: Dict[str, Any]):
        """
        Simple natural language query using Wazuh API directly (no DSL).
        """
        query = params.get("query")
        if not query:
            return {"error": "Query is required"}
        
        query_lower = query.lower()
        
        if "agent" in query_lower:
            raw_data = await self.client.get_agents()
        else:
            limit = 50
            severity = None
            if "critical" in query_lower:
                severity = "12"
            elif "high" in query_lower:
                severity = "8"
            
            raw_data = await self.client.get_alerts(severity=severity, limit=limit)
        
        natural_response = format_wazuh_response(raw_data, query)
        
        return {
            "query": query,
            "raw_data": raw_data,
            "response": natural_response
        }
    
    async def close(self):
        """Cleanup resources"""
        await self.client.close()
