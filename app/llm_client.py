from openai import AsyncOpenAI
from app.config import settings
from app.schemas import WazuhSearchPlan
import json
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)

# Initialize async client with timeout
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=httpx.Timeout(60.0, connect=10.0)  # 60s total, 10s connect
)

# Global agent cache (refreshed periodically)
_agent_cache = {"agents": [], "last_updated": 0}
_agent_cache_ttl = 300  # 5 minutes


async def get_agent_context(wazuh_client=None) -> Dict[str, Any]:
    """
    Get current agent list from Wazuh to provide context for GPT.
    This prevents hallucinating agent names.
    """
    import time
    
    # Return cached if still valid
    if time.time() - _agent_cache["last_updated"] < _agent_cache_ttl and _agent_cache["agents"]:
        return _agent_cache
    
    # Fetch fresh agent list
    if wazuh_client:
        try:
            result = await wazuh_client.get_agents()
            agents = result.get("data", {}).get("affected_items", [])
            
            agent_list = []
            for agent in agents:
                agent_list.append({
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "ip": agent.get("ip"),
                    "status": agent.get("status"),
                    "os": agent.get("os", {}).get("name", "Unknown")
                })
            
            _agent_cache["agents"] = agent_list
            _agent_cache["last_updated"] = time.time()
            logger.info(f"Updated agent cache: {len(agent_list)} agents")
            return _agent_cache
        except Exception as e:
            logger.error(f"Failed to fetch agent context: {e}")
    
    # Return cached even if expired
    return _agent_cache


def format_agent_context(agents: List[Dict]) -> str:
    """Format agent list for GPT context."""
    if not agents:
        return "No agents available."
    
    context = ""
    for agent in agents[:20]:  # Limit to 20 to avoid token overflow
        context += f"- Agent {agent['id']}: {agent['name']} ({agent['os']}) - Status: {agent['status']}\n"
    
    if len(agents) > 20:
        context += f"\n... and {len(agents) - 20} more agents (not shown)\n"
    
    return context


def analyze_query_intent(user_query: str) -> Dict[str, Any]:
    """
    Analyze user query to provide hints for GPT parsing.
    Returns metadata about query complexity and intent.
    """
    query_lower = user_query.lower()
    
    metadata = {
        "is_security_incident": False,
        "is_compliance_query": False,
        "is_performance_query": False,
        "suggested_limit": 50,
        "needs_aggregation": False,
        "time_sensitive": False
    }
    
    # Security incident indicators
    security_keywords = ["attack", "breach", "intrusion", "malware", "exploit", "vulnerability", 
                        "brute force", "unauthorized", "suspicious", "malicious", "threat"]
    if any(kw in query_lower for kw in security_keywords):
        metadata["is_security_incident"] = True
        metadata["suggested_limit"] = 100
    
    # Pattern detection needs more data
    pattern_keywords = ["pattern", "multiple", "repeated", "summarize", "count by", "group by"]
    if any(kw in query_lower for kw in pattern_keywords):
        metadata["needs_aggregation"] = True
        metadata["suggested_limit"] = 200
    
    # Time-sensitive queries
    time_keywords = ["now", "recent", "latest", "last", "today", "yesterday", "real-time"]
    if any(kw in query_lower for kw in time_keywords):
        metadata["time_sensitive"] = True
    
    return metadata


# Router System Prompt - Decides which pipeline to use
ROUTER_PROMPT = """You are a Wazuh SIEM query router. Your job is to determine which pipeline should handle the user's query.

**Pipeline Options:**

1. **SIMPLE_PIPELINE** (Wazuh Manager API)
   - ONLY for agent information queries (list agents, agent status, agent details)
   - Manager status and configuration
   - Cluster health
   - NO time-based queries
   - NO security data (alerts/logs/events)

2. **ADVANCED_PIPELINE** (Wazuh Indexer - OpenSearch)
   - Security alerts and events
   - Log searches and analysis
   - Authentication logs
   - File integrity monitoring
   - Vulnerability scans
   - Compliance audits
   - ALL time-based queries (ANY mention of time/date)
   - Historical data queries

**CRITICAL ROUTING RULES (MUST FOLLOW):**
1. ANY query with time references → ALWAYS use ADVANCED_PIPELINE
   - "last hour", "past 24 hours", "yesterday", "last week", "recent", "from X to Y"
   - "in the last N minutes/hours/days"
   - ANY time-based filtering
   
2. Alerts/Logs/Events → ALWAYS use ADVANCED_PIPELINE
   - "alerts", "logs", "events", "incidents", "security events"
   
3. ONLY use SIMPLE_PIPELINE for:
   - "show me all agents" (no time filter)
   - "list agents" (no time filter)
   - "agent status" (current status only)
   - Pure agent inventory queries
   
4. If ANY doubt → use ADVANCED_PIPELINE

**Response Format:**
Return JSON with EXACTLY this structure:
{
  "pipeline": "SIMPLE_PIPELINE" or "ADVANCED_PIPELINE",
  "reasoning": "Brief explanation of why this pipeline was chosen",
  "confidence": "high" or "medium" or "low"
}

Examples:
- "Show me all agents" → {"pipeline": "SIMPLE_PIPELINE", "reasoning": "Pure agent inventory query with no time filter", "confidence": "high"}
- "List active agents" → {"pipeline": "SIMPLE_PIPELINE", "reasoning": "Current agent status query", "confidence": "high"}
- "Critical alerts from last hour" → {"pipeline": "ADVANCED_PIPELINE", "reasoning": "Time-based query (last hour) for alerts", "confidence": "high"}
- "Get logs from last 15 minutes" → {"pipeline": "ADVANCED_PIPELINE", "reasoning": "Time-based query (last 15 minutes) for logs", "confidence": "high"}
- "Alerts from past 24 hours" → {"pipeline": "ADVANCED_PIPELINE", "reasoning": "Time-based query (past 24 hours) for alerts", "confidence": "high"}
- "Show recent alerts" → {"pipeline": "ADVANCED_PIPELINE", "reasoning": "Implicit time reference (recent) for alerts", "confidence": "high"}
- "High severity events yesterday" → {"pipeline": "ADVANCED_PIPELINE", "reasoning": "Time-based query (yesterday) for events", "confidence": "high"}
"""


async def route_query(user_query: str) -> Dict[str, Any]:
    """Route query to appropriate pipeline using GPT-4o."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": f"Route this query: {user_query}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        logger.debug(f"Raw routing response: {content}")
        
        if not content or not content.strip():
            logger.error("Router returned empty response")
            raise ValueError("Router returned empty response")
        
        # Remove any markdown formatting if present
        content_clean = content.strip()
        if content_clean.startswith("```json"):
            content_clean = content_clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        elif content_clean.startswith("```"):
            content_clean = content_clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
        routing = json.loads(content_clean)
        
        # Convert confidence to numeric
        confidence_map = {"high": 0.95, "medium": 0.75, "low": 0.5}
        routing["confidence"] = confidence_map.get(routing.get("confidence", "medium"), 0.75)
        
        logger.info(f"Query routed to {routing['pipeline']}: {routing['reasoning']}")
        return routing
        
    except json.JSONDecodeError as e:
        logger.error(f"Query routing JSON parse failed: {e}. Content was: {content if 'content' in locals() else 'NO CONTENT'}", exc_info=True)
        # Default to advanced pipeline on error
        return {
            "pipeline": "ADVANCED_PIPELINE",
            "reasoning": "Routing JSON parsing failed, using advanced pipeline as fallback",
            "confidence": 0.5
        }
    except Exception as e:
        logger.error(f"Query routing failed: {e}", exc_info=True)
        # Default to advanced pipeline on error
        return {
            "pipeline": "ADVANCED_PIPELINE",
            "reasoning": "Routing failed, using advanced pipeline as fallback",
            "confidence": 0.5
        }


def ask_openai(prompt: str) -> str:
    """Send user prompt to OpenAI LLM."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an intelligent MCP server assistant.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        return content if content is not None else "LLM returned empty response."
    except Exception as e:
        print(f"[ERROR] OpenAI request failed: {e}")
        return "LLM request failed."


def parse_natural_language_query(user_query: str) -> Dict[str, Any]:
    """Convert natural language query to structured WazuhSearchPlan for DSL builder."""
    system_prompt = """You are a Wazuh SIEM query translator. Convert natural language security queries into structured JSON for OpenSearch/Elasticsearch queries.

Output ONLY valid JSON matching this WazuhSearchPlan schema:
{
  "indices": "wazuh-alerts-*",
  "time": {
    "from": "now-24h",
    "to": "now",
    "timezone": "UTC"
  },
  "filters": [
    {"field": "rule.level", "op": "gte", "value": 12}
  ],
  "must_not": [
    {"field": "agent.name", "op": "eq", "value": "test-agent"}
  ],
  "query_string": null,
  "aggregation": null,
  "limit": 50,
  "dry_run": false
}

Operators: "eq", "neq", "gt", "gte", "lt", "lte", "contains", "in"

Field mappings:
- severity/critical → rule.level >= 12
- high severity → rule.level >= 8
- medium severity → rule.level >= 5
- agent name → agent.name
- source IP → data.srcip
- rule ID → rule.id
- manager → manager.name
- vulnerability → vulnerability.severity

**CRITICAL - DO NOT filter by severity unless explicitly mentioned:**
- "logs from last 15 minutes" → NO severity filter (filters: [])
- "recent logs" → NO severity filter (filters: [])
- "critical alerts" → ADD severity filter (rule.level >= 12)
- "high severity" → ADD severity filter (rule.level >= 8)

Time formats:
- "last 24 hours" → {"from": "now-24h", "to": "now"}
- "today" → {"from": "now/d", "to": "now"}
- "last week" → {"from": "now-7d", "to": "now"}
- "last hour" → {"from": "now-1h", "to": "now"}

For aggregations:
- "count by X" → {"type": "terms", "field": "X", "size": 10}
- "total count" → {"type": "count"}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")

        result = content.strip()
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            result = result.rsplit("```", 1)[0]

        parsed = json.loads(result)
        return parsed
    except Exception as e:
        print(f"[ERROR] Failed to parse query: {e}")
        # Fallback to basic query
        return {
            "indices": "wazuh-alerts-*",
            "time": {"from": "now-24h", "to": "now", "timezone": "UTC"},
            "filters": [],
            "must_not": [],
            "query_string": None,
            "aggregation": None,
            "limit": 50,
            "dry_run": False,
        }


def format_wazuh_response(raw_data: Dict[str, Any], original_query: str) -> str:
    """Convert cryptic Wazuh JSON response to natural language summary."""
    system_prompt = """You are a security analyst assistant. Convert technical Wazuh SIEM data into clear, actionable natural language summaries.

Provide:
1. Brief summary (1-2 sentences)
2. Key findings with counts
3. Notable patterns or concerns
4. Recommended actions if critical

Be concise, specific, and security-focused."""

    user_prompt = f"""Original query: {original_query}

Wazuh data:
{json.dumps(raw_data, indent=2)}

Provide a natural language summary of this security data."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        return content if content is not None else "Unable to format response."
    except Exception as e:
        print(f"[ERROR] Failed to format response: {e}")
        return f"Retrieved {len(raw_data.get('alerts', raw_data.get('agents', [])))} items from Wazuh."


# ==================== NEW UNIFIED PIPELINE FUNCTIONS ====================

async def parse_simple_query(user_query: str) -> Dict[str, Any]:
    """Parse natural language for SIMPLE_PIPELINE (Wazuh Manager API)."""
    system_prompt = """You are a Wazuh API query parser. Convert natural language agent queries into structured JSON.

Output ONLY valid JSON matching this structure:
{
  "operation": "list_agents" or "get_agent",
  "filters": {
    "status": "active" or "disconnected" or null,
    "agent_id": "001" or null
  }
}

Examples:
- "Show me all agents" → {"operation": "list_agents", "filters": {"status": null, "agent_id": null}}
- "List active agents" → {"operation": "list_agents", "filters": {"status": "active", "agent_id": null}}
- "Get agent 001" → {"operation": "get_agent", "filters": {"status": null, "agent_id": "001"}}
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Parser returned empty response")
        
        result = content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        parsed = json.loads(result)
        logger.info(f"Simple query parsed: {parsed}")
        return parsed
        
    except Exception as e:
        logger.error(f"Simple query parsing failed: {e}", exc_info=True)
        # Default fallback
        return {
            "operation": "list_agents",
            "filters": {"status": None, "agent_id": None}
        }


def validate_and_correct_plan(plan: Dict[str, Any], original_query: str, wazuh_client=None) -> Dict[str, Any]:
    """
    Validate and correct the GPT-generated query plan to ensure it works with DSL builder.
    Fixes common issues like invalid field names, incorrect operators, agent name resolution, etc.
    
    Args:
        plan: Query plan dict from GPT
        original_query: Original user query string
        wazuh_client: Optional WazuhClient for agent validation
        
    Returns:
        Corrected and validated plan dict
    """
    # Valid field names in Wazuh
    VALID_FIELDS = {
        "rule.level", "rule.description", "rule.id", "rule.mitre.technique",
        "agent.name", "agent.id", "agent.ip",
        "data.srcip", "data.dstip", "data.srcuser", "data.dstuser",
        "data.win.eventdata.targetUserName", "data.win.system.eventID",
        "decoder.name", "decoder.parent",
        "location", "full_log",
        "timestamp", "@timestamp"
    }
    
    # Common field name corrections
    FIELD_CORRECTIONS = {
        "severity": "rule.level",
        "level": "rule.level",
        "agent": "agent.name",
        "host": "agent.name",
        "hostname": "agent.name",
        "source_ip": "data.srcip",
        "src_ip": "data.srcip",
        "destination_ip": "data.dstip",
        "dst_ip": "data.dstip",
        "user": "data.srcuser",
        "username": "data.srcuser",
        "event_id": "data.win.system.eventID",
        "eventid": "data.win.system.eventID",
    }
    
    VALID_OPERATORS = {"eq", "neq", "gt", "gte", "lt", "lte", "contains", "in"}
    
    # Ensure required fields exist
    plan.setdefault("indices", "wazuh-alerts-*")
    plan.setdefault("time", {"from": "now-24h", "to": "now", "timezone": "UTC"})
    plan.setdefault("filters", [])
    plan.setdefault("must_not", [])
    plan.setdefault("query_string", None)
    plan.setdefault("aggregation", None)
    plan.setdefault("limit", 50)
    plan.setdefault("dry_run", False)
    
    # Validate and correct filters
    corrected_filters = []
    for filter_item in plan.get("filters", []):
        if not isinstance(filter_item, dict):
            logger.warning(f"Invalid filter (not a dict): {filter_item}, skipping")
            continue
        
        field = filter_item.get("field", "")
        op = filter_item.get("op", "eq")
        value = filter_item.get("value")
        
        # Correct field name if needed
        if field not in VALID_FIELDS:
            corrected_field = FIELD_CORRECTIONS.get(field.lower(), field)
            if corrected_field != field:
                logger.info(f"Corrected field '{field}' → '{corrected_field}'")
                field = corrected_field
            elif field not in VALID_FIELDS:
                logger.warning(f"Unknown field '{field}', keeping as-is")
        
        # Validate operator
        if op not in VALID_OPERATORS:
            logger.warning(f"Invalid operator '{op}', defaulting to 'eq'")
            op = "eq"
        
        # Skip filters with no value (unless it's checking for existence)
        if value is None or value == "":
            logger.warning(f"Filter has empty value, skipping: {filter_item}")
            continue
        
        corrected_filters.append({
            "field": field,
            "op": op,
            "value": value
        })
    
    plan["filters"] = corrected_filters
    
    # Validate time range
    time_config = plan.get("time", {})
    if not isinstance(time_config, dict):
        logger.warning(f"Invalid time config, using default 24h")
        plan["time"] = {"from": "now-24h", "to": "now", "timezone": "UTC"}
    else:
        time_config.setdefault("from", "now-24h")
        time_config.setdefault("to", "now")
        time_config.setdefault("timezone", "UTC")
        plan["time"] = time_config
    
    # Validate limit
    limit = plan.get("limit", 50)
    try:
        limit = int(limit)
        if limit < 1:
            limit = 50
        elif limit > 10000:
            limit = 10000
    except (ValueError, TypeError):
        limit = 50
    plan["limit"] = limit
    
    # For brute force or pattern detection queries, increase limit
    query_lower = original_query.lower()
    if any(keyword in query_lower for keyword in ["brute force", "pattern", "multiple", "repeated", "summarize"]):
        if plan["limit"] < 100:
            logger.info(f"Increasing limit to 100 for pattern detection query")
            plan["limit"] = 100
    
    return plan


async def parse_query_to_plan(user_query: str, wazuh_client=None) -> Dict[str, Any]:
    """Parse natural language for ADVANCED_PIPELINE (Indexer) - returns WazuhSearchPlan dict.
    
    Args:
        user_query: Natural language query from user
        wazuh_client: Optional WazuhClient instance for fetching agent context
        
    Returns:
        Dict containing WazuhSearchPlan structure with validated fields
    """
    from datetime import datetime, timezone
    
    # Fetch agent context to prevent hallucination
    agent_context_str = ""
    if wazuh_client:
        try:
            agent_ctx = await get_agent_context(wazuh_client)
            if agent_ctx.get("agents"):
                agent_context_str = f"\n\n**AVAILABLE AGENTS (use ONLY these agent names/IDs):**\n{format_agent_context(agent_ctx['agents'])}\n"
        except Exception as e:
            logger.warning(f"Could not fetch agent context: {e}")
    
    # Add time context for relative queries
    now = datetime.now(timezone.utc)
    time_context = f"""
**CURRENT TIME CONTEXT:**
- UTC Now: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Use this for calculating "today", "yesterday", "this week", "recent"
"""
    
    # Add common rules context
    rules_context = """
**COMMON WAZUH RULES (reference these when user mentions security events):**
- Rule 5710: SSH - Attempt to login using non-existent user
- Rule 5551: SSH - Multiple authentication failures
- Rule 5503: PAM - User login failed
- Rule 60204: Windows - User Logon Failure (EventID 4625)
- Rule 87801: Windows - Possible Brute Force Attack
- Rule 5502: User missed password multiple times
- Rule 5720: SSH - Brute force attack attempt
- Rule 31101: FIM - File added to system
- Rule 31103: FIM - File modified
- Rule 80790: Vulnerability detected in system
"""
    
    # Add decoder context
    decoder_context = """
**LOG SOURCES (decoder.name field - use for filtering by log type):**
- sshd: SSH authentication/connection logs
- pam: Linux PAM authentication
- windows: Windows event logs
- json: JSON-formatted application logs
- web-accesslog: Apache/Nginx web access
- firewall: Firewall logs
- aws-cloudtrail: AWS CloudTrail
- docker: Docker container logs
"""
    
    # Add field examples
    field_examples = """
**FIELD VALUE EXAMPLES:**
- rule.level: 0-15 (0=info, 3=low, 5+=notable, 7+=important, 10+=critical, 12+=attack, 15=severe)
- agent.os.platform: linux, windows, darwin
- data.win.system.eventID: 4624 (success), 4625 (failed), 4672 (admin), 4720 (user created)
- rule.mitre.technique: T1110 (Brute Force), T1078 (Valid Accounts), T1059 (Command Execution)
"""
    
    system_prompt = f"""You are a Wazuh SIEM query translator. Convert natural language security queries into structured JSON for OpenSearch/Elasticsearch queries.

**IMPORTANT: Use ONLY the exact field names listed below. DO NOT invent field names.**{agent_context_str}{time_context}{rules_context}{decoder_context}{field_examples}

Output ONLY valid JSON matching this WazuhSearchPlan schema:
{{
  "indices": "wazuh-alerts-*",
  "time": {{
    "from": "now-24h",
    "to": "now",
    "timezone": "UTC"
  }},
  "filters": [
    {{"field": "rule.level", "op": "gte", "value": 12}}
  ],
  "must_not": [],
  "query_string": null,
  "aggregation": null,
  "limit": 50,
  "dry_run": false
}}

**VALID OPERATORS:** "eq", "neq", "gt", "gte", "lt", "lte", "contains", "in"

**VALID FIELD NAMES (use exactly as shown):**
- rule.level (integer 0-15)
- rule.description (string)
- rule.id (string - e.g., "5710", "60204")
- rule.mitre.technique (array - e.g., ["T1110", "T1078"])
- rule.mitre.tactic (string - e.g., "Credential Access")
- agent.name (string - exact match or wildcard)
- agent.id (string - e.g., "001", "002")
- agent.ip (IP address)
- agent.os.platform (string: "linux", "windows", "darwin")
- data.srcip (source IP address)
- data.dstip (destination IP address)
- data.srcuser (source username)
- data.dstuser (destination username)
- data.srcport (source port number)
- data.dstport (destination port number)
- data.protocol (protocol: tcp, udp, icmp)
- data.win.eventdata.targetUserName (Windows target user)
- data.win.system.eventID (Windows Event ID - string)
- data.win.system.channel (Windows log channel)
- decoder.name (string: "sshd", "windows", "pam", "json", "firewall")
- decoder.parent (parent decoder name)
- location (log source path)
- full_log (full log message - use "contains" operator)
- timestamp (ISO timestamp)
- @timestamp (ISO timestamp)

**CRITICAL SECURITY EVENT MAPPINGS:**

1. **Failed Login Attempts:**
   - SSH Failed: {{"field": "decoder.name", "op": "eq", "value": "sshd"}} AND {{"field": "rule.id", "op": "in", "value": ["5710", "5551", "5503"]}}
   - Windows Failed: {{"field": "data.win.system.eventID", "op": "eq", "value": "4625"}}
   - Linux PAM: {{"field": "decoder.name", "op": "eq", "value": "pam"}} AND {{"field": "rule.level", "op": "gte", "value": 5}}
   
2. **Successful Logins:**
   - Windows Success: {{"field": "data.win.system.eventID", "op": "eq", "value": "4624"}}
   - SSH Success: {{"field": "rule.id", "op": "eq", "value": "5715"}}

3. **Brute Force Detection:**
   - Use failed login filters (above)
   - Set limit to 100-200 to capture patterns
   - Add rule.level >= 7 for confirmed attacks
   - Consider aggregation by data.srcip

4. **File Integrity Monitoring:**
   - File Added: {{"field": "rule.id", "op": "eq", "value": "31101"}}
   - File Modified: {{"field": "rule.id", "op": "eq", "value": "31103"}}
   - File Deleted: {{"field": "rule.id", "op": "eq", "value": "31102"}}

5. **Privilege Escalation:**
   - MITRE T1548: {{"field": "rule.mitre.technique", "op": "contains", "value": "T1548"}}
   - Windows Admin Logon: {{"field": "data.win.system.eventID", "op": "eq", "value": "4672"}}

6. **Severity Levels:**
   - ONLY add severity filter if explicitly mentioned in query
   - critical/severe → rule.level >= 12
   - high → rule.level >= 8
   - medium → rule.level >= 5
   - low → rule.level >= 3

4. **Time Formats:**
   - "last 24 hours" → {{"from": "now-24h", "to": "now"}}
   - "last hour" → {{"from": "now-1h", "to": "now"}}
   - "last 15 minutes" → {{"from": "now-15m", "to": "now"}}
   - "past week" → {{"from": "now-7d", "to": "now"}}
   - "yesterday" → {{"from": "now-1d/d", "to": "now/d"}}

**AGENT NAMES:**
- If query mentions agent but doesn't specify name → use {{"field": "agent.name", "op": "contains", "value": "*"}}
- If uncertain about exact agent name → use wildcard or omit the filter
- Common agents: "Ubuntu", "Windows", "CentOS", etc.

**QUERY EXAMPLES:**

Input: "Show me high-severity failed login attempts from the last 24 hours"
Output:
{{
  "indices": "wazuh-alerts-*",
  "time": {{"from": "now-24h", "to": "now", "timezone": "UTC"}},
  "filters": [
    {{"field": "rule.level", "op": "gte", "value": 8}},
    {{"field": "decoder.name", "op": "in", "value": ["sshd", "pam", "windows"]}}
  ],
  "must_not": [],
  "query_string": null,
  "aggregation": null,
  "limit": 100,
  "dry_run": false
}}

Input: "Get logs from last 15 minutes"
Output:
{{
  "indices": "wazuh-alerts-*",
  "time": {{"from": "now-15m", "to": "now", "timezone": "UTC"}},
  "filters": [],
  "must_not": [],
  "query_string": null,
  "aggregation": null,
  "limit": 50,
  "dry_run": false
}}

**RESPOND WITH JSON ONLY. NO EXPLANATIONS.**
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Parser returned empty response")
        
        result = content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        parsed = json.loads(result)
        
        # Validate and correct the parsed plan (pass wazuh_client for agent validation)
        parsed = validate_and_correct_plan(parsed, user_query, wazuh_client)
        
        logger.info(f"Advanced query plan (validated): {parsed}")
        return parsed
        
    except Exception as e:
        logger.error(f"Advanced query parsing failed: {e}", exc_info=True)
        # Default fallback
        return {
            "indices": "wazuh-alerts-*",
            "time": {"from": "now-24h", "to": "now", "timezone": "UTC"},
            "filters": [],
            "must_not": [],
            "query_string": None,
            "aggregation": None,
            "limit": 50,
            "dry_run": False
        }


async def format_results(query: str, results: Dict[str, Any]) -> str:
    """Format results to natural language summary - sends only sample to GPT to avoid token limits."""
    system_prompt = """You are a security analyst assistant. Convert technical Wazuh SIEM data into clear, actionable natural language summaries.

Provide:
1. Brief summary (1-2 sentences)
2. Key findings with counts
3. Notable patterns or concerns if any

Be concise, specific, and security-focused."""

    # Extract key metrics and sample data to avoid token limits
    summary_data = {}
    
    if "hits" in results:
        # Indexer results
        hits_data = results.get("hits", {})
        total = hits_data.get("total", {})
        total_count = total.get("value", total) if isinstance(total, dict) else total
        
        documents = hits_data.get("hits", [])
        
        summary_data = {
            "total_hits": total_count,
            "returned_count": len(documents),
            "sample_documents": documents[:10]  # Only send first 10 docs
        }
        
        # Extract aggregations if present
        if "aggregations" in results:
            summary_data["aggregations"] = results["aggregations"]
    
    elif "data" in results and "affected_items" in results["data"]:
        # Wazuh Manager API results
        items = results["data"]["affected_items"]
        summary_data = {
            "total_items": len(items),
            "sample_items": items[:10]  # Only send first 10 items
        }
    
    else:
        # Unknown format - send minimal data
        summary_data = {"raw": str(results)[:1000]}  # Truncate to 1000 chars

    user_prompt = f"""Original query: {query}

Wazuh data summary (showing sample of results):
{json.dumps(summary_data, indent=2, default=str)}

Note: If total_hits/total_items > sample size, this is a representative sample.

Provide a natural language summary of this security data."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500  # Limit output tokens
        )
        
        content = response.choices[0].message.content
        return content if content is not None else "Unable to format response."
        
    except Exception as e:
        logger.error(f"Failed to format results: {e}", exc_info=True)
        # Fallback summary
        if "data" in results and "affected_items" in results["data"]:
            return f"Found {len(results['data']['affected_items'])} items from Wazuh Manager API."
        elif "hits" in results:
            total = results.get("hits", {}).get("total", {})
            count = total.get("value", total) if isinstance(total, dict) else total
            return f"Found {count} results from Wazuh Indexer."
        else:
            return "Retrieved results from Wazuh."
