from pydantic import BaseModel
from typing import Optional, List

# ================================
# WAZUH: ALERT SCHEMA
# ================================
class AlertQuery(BaseModel):
    agent_id: Optional[str] = None
    severity: Optional[str] = None
    limit: int = 20

class Alert(BaseModel):
    id: str
    rule_id: int
    level: int
    description: str
    agent_name: str
    timestamp: str

class AlertsResponse(BaseModel):
    total: int
    alerts: List[Alert]

# ================================
# WAZUH: AGENT SCHEMA
# ================================
class Agent(BaseModel):
    id: str
    name: str
    status: str
    version: Optional[str] = None

class AgentsResponse(BaseModel):
    total: int
    agents: List[Agent]
# ================================
# MCP HEALTH CHECK SCHEMA
# ================================
class HealthStatus(BaseModel):
    mcp_server: str
    wazuh_api: bool
    wazuh_indexer: bool
    timestamp: str

