from openai import OpenAI
from app.config import settings
import json
from typing import Dict, Any

# Initialize client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


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
