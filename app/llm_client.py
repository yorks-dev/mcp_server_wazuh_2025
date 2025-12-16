from openai import AsyncOpenAI
from app.config import settings
from app.schemas import WazuhSearchPlan
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Initialize async client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": f"Route this query: {user_query}"}
            ],
            temperature=0.1,
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
            model="gpt-4o",
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
            model="gpt-4o",
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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1
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


async def parse_query_to_plan(user_query: str) -> Dict[str, Any]:
    """Parse natural language for ADVANCED_PIPELINE (Indexer) - returns WazuhSearchPlan dict."""
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
  "must_not": [],
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

**CRITICAL - DO NOT filter by severity unless explicitly mentioned:**
- "logs from last 15 minutes" → NO severity filter (filters: [])
- "recent logs" → NO severity filter (filters: [])
- "critical alerts" → ADD severity filter (rule.level >= 12)
- "high severity" → ADD severity filter (rule.level >= 8)

Time formats:
- "last 24 hours" → {"from": "now-24h", "to": "now"}
- "last hour" → {"from": "now-1h", "to": "now"}
- "last 15 minutes" → {"from": "now-15m", "to": "now"}
- "last week" → {"from": "now-7d", "to": "now"}
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Parser returned empty response")
        
        result = content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        parsed = json.loads(result)
        logger.info(f"Advanced query plan: {parsed}")
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
    """Format results to natural language summary."""
    system_prompt = """You are a security analyst assistant. Convert technical Wazuh SIEM data into clear, actionable natural language summaries.

Provide:
1. Brief summary (1-2 sentences)
2. Key findings with counts
3. Notable patterns or concerns if any

Be concise, specific, and security-focused."""

    user_prompt = f"""Original query: {query}

Wazuh data:
{json.dumps(results, indent=2)}

Provide a natural language summary of this security data."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
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
