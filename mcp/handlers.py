import datetime
from typing import Optional, Dict, Any

from mcp.schemas import (
    AlertQuery,
    AlertsResponse,
    AgentsResponse,
    HealthStatus,
)
from mcp.wazuh_client import WazuhClient
class MCPHandlers:
    """
    Responsible for executing all MCP-visible tools.
    Clean separation between tools.json and implementation logic.
    """
    def __init__(self, config):
        self.client = WazuhClient(config)
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
        return AlertsResponse(
            total=raw_alerts.get("total", 0),
            alerts=raw_alerts.get("alerts", []),
        ).model_dump()
    # -------------------------------------------------------------
    # 🔥 FETCH AGENTS
    # -------------------------------------------------------------
    async def wazuh_get_agents(self, _params=None):
        raw_agents = await self.client.get_agents()

        return AgentsResponse(
            total=raw_agents.get("total", 0),
            agents=raw_agents.get("agents", []),
        ).model_dump()
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
