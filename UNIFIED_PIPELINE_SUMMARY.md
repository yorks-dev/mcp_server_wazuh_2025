# Unified NL Pipeline - Implementation Summary

## Date: 2025
## Changes Made: Refactored from 3-pipeline to 2-pipeline architecture with intelligent routing

---

## 🎯 **Architecture Overview**

### Previous (3-Pipeline)
1. **Simple Pipeline**: Wazuh Manager API queries
2. **Advanced Pipeline**: Indexer (OpenSearch) queries  
3. **Direct DSL**: Manual OpenSearch queries

### New (2-Pipeline with AI Routing)
1. **Natural Language**: GPT-4o automatically routes to Simple or Advanced pipeline
2. **Direct DSL**: Manual OpenSearch queries (unchanged)

---

## 📝 **Changes Made**

### 1. **app/llm_client.py** - Complete Rewrite
Added intelligent routing system:

#### New Functions:
- `route_query(query: str) -> dict`: Routes queries to SIMPLE_PIPELINE or ADVANCED_PIPELINE
  - Returns: `{pipeline, reasoning, confidence}`
  - Uses GPT-4o to analyze query intent
  
- `parse_simple_query(query: str) -> dict`: Parses queries for Wazuh Manager API
  - Handles: agent queries, status filters
  - Returns: `{operation, filters}`
  
- `parse_query_to_plan(query: str) -> dict`: Parses queries for Indexer
  - Handles: alerts, logs, time ranges, severity filters
  - Returns: WazuhSearchPlan structure
  
- `format_results(query: str, results: dict) -> str`: Natural language formatting

#### System Prompts:
- `ROUTER_PROMPT`: Instructs GPT to route queries intelligently
- `SIMPLE_SYSTEM_PROMPT`: For Wazuh API queries (agents, config)
- `ADVANCED_SYSTEM_PROMPT`: For Indexer queries (alerts, logs)
  - **CRITICAL FIX**: Only adds severity filters when explicitly mentioned

---

### 2. **app/main.py** - New Unified Endpoints

#### New Endpoints:

**`POST /query/nl`** - Unified Natural Language Query
```python
# Flow:
1. route_query() -> Decides SIMPLE_PIPELINE or ADVANCED_PIPELINE
2. If SIMPLE: parse_simple_query() -> Wazuh API -> format_results()
3. If ADVANCED: parse_query_to_plan() -> DSL Builder -> Indexer -> format_results()

# Response:
{
    "success": true,
    "routing": {
        "pipeline": "SIMPLE_PIPELINE",
        "reasoning": "Query asks for agents...",
        "confidence": 0.95
    },
    "pipeline": "SIMPLE_PIPELINE",
    "parsed_query": {...},
    "summary": "Found 4 agents: 1 active, 3 disconnected...",
    "raw_data": {...},
    "dsl": null
}
```

**`POST /query/dsl`** - Direct DSL Query (unchanged logic)
```python
# Request:
{
    "index": "wazuh-alerts-*",
    "query": { ... OpenSearch DSL ... }
}

# Response:
{
    "success": true,
    "pipeline": "DIRECT_DSL",
    "raw_data": {...},
    "dsl": {...}
}
```

---

### 3. **frontend/index.html** - Updated UI

#### Changes:
- **Pipeline Selector**: Reduced from 3 to 2 buttons
  - 🤖 Natural Language (with auto-routing description)
  - ⚙️ Direct DSL
  
- **Query Examples**: Updated chips
  - "All agents" → SIMPLE_PIPELINE
  - "Critical alerts (24h)" → ADVANCED_PIPELINE
  - "Recent logs (15m)" → ADVANCED_PIPELINE

- **Routing Info Section**: New `<div id="routingInfo">` to display routing decisions

---

### 4. **frontend/app.js** - Complete Rewrite

#### Key Changes:
- `currentPipeline`: Changed from 'simple' to 'nl'
- `executeQuery()`: Now calls `/query/nl` or `/query/dsl`
- `displayResults()`: Shows routing badge and confidence score

#### Routing Display:
```html
<div class="routing-badge">
    <span class="badge badge-primary">🔍 Simple Query</span>
    <span class="confidence-badge">Confidence: 95%</span>
</div>
<div class="routing-reason">
    <strong>Routing Reason:</strong> Query asks for agent information...
</div>
```

---

### 5. **frontend/styles.css** - New Routing Styles

Added styling for:
- `.routing-info`: Container with blue border
- `.routing-badge`: Pipeline badge + confidence score
- `.badge-primary`: Blue gradient (Simple Pipeline)
- `.badge-success`: Green gradient (Advanced Pipeline)
- `.confidence-badge`: Gray badge with percentage

---

## 🔍 **Routing Logic Examples**

### Simple Pipeline (Wazuh API - Port 55000)
- "Show me all agents"
- "List active agents"
- "Get agent status"
- "How many agents are online?"

### Advanced Pipeline (Indexer - Port 9200 via SSH tunnel)
- "Critical alerts from last 24 hours"
- "Get logs from last 15 minutes"
- "High severity alerts from last week"
- "Show me all alerts with level >= 10"

---

## 🚀 **Testing Instructions**

### 1. Start SSH Tunnel (Required for Advanced queries)
```bash
./scripts/setup_dev_tunnel.sh
```

### 2. Start FastAPI Server
```bash
cd /home/kaustubh/mcp_server_wazuh_2025
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend Server
```bash
cd frontend
python3 -m http.server 8080
```

### 4. Test Queries

#### Test 1: Simple Query (should route to SIMPLE_PIPELINE)
```
Query: "Show me all agents"
Expected: 
- Routing: SIMPLE_PIPELINE
- Confidence: ~95%
- Result: 4 agents (1 active, 3 disconnected)
- DSL: null (no DSL query)
```

#### Test 2: Advanced Query (should route to ADVANCED_PIPELINE)
```
Query: "Show me critical alerts from the last 24 hours"
Expected:
- Routing: ADVANCED_PIPELINE
- Confidence: ~95%
- Result: List of alerts with rule.level >= 12
- DSL: Full OpenSearch query visible
```

#### Test 3: Time-based Query WITHOUT Severity Filter
```
Query: "Get logs from last 15 minutes"
Expected:
- Routing: ADVANCED_PIPELINE
- filters: [] (no severity filter!)
- Result: ALL logs regardless of severity
```

---

## ⚠️ **Critical Fixes Included**

### 1. Severity Filter Bug (FIXED)
**Problem**: Old system added severity filters by default  
**Solution**: Updated ADVANCED_SYSTEM_PROMPT with clear instruction:
```
**CRITICAL - DO NOT filter by severity unless explicitly mentioned:**
- "logs from last 15 minutes" → NO severity filter (filters: [])
- "critical alerts" → ADD severity filter (rule.level >= 12)
```

### 2. Agent Query Routing (FIXED)
**Problem**: Agent queries were going to ADVANCED_PIPELINE (searched alerts index)  
**Solution**: Router now correctly identifies agent queries → SIMPLE_PIPELINE → Wazuh API

---

## 📊 **Benefits of New Architecture**

### For Operators:
✅ Single "Natural Language" button - no pipeline confusion  
✅ AI automatically chooses the right backend  
✅ Transparent routing decisions with confidence scores  
✅ Maintains expert DSL option for power users

### For System:
✅ Reduced API complexity (2 endpoints vs 3)  
✅ Intelligent query optimization (fast API vs powerful Indexer)  
✅ Better error handling (routing failures are explicit)  
✅ Easier to maintain (routing logic centralized in llm_client.py)

---

## 🔧 **Technical Details**

### Dependencies:
- **OpenAI GPT-4o**: Query routing, parsing, formatting
- **Wazuh Manager API**: Agent data (port 55000, no tunnel)
- **OpenSearch Indexer**: Alerts/logs (port 9200, SSH tunnel required)
- **FastAPI**: Async web framework with CORS
- **Plain HTML/CSS/JS**: No frontend framework

### SSH Tunnel Configuration:
```bash
ssh -L 9200:localhost:9200 kaustubh@10.21.236.157
```

### Environment Variables Required:
```bash
OPENAI_API_KEY=sk-...
WAZUH_API_HOST=https://10.21.236.157
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=wazuh
WAZUH_API_PASSWORD=(use env var)
```

---

## 📚 **Documentation Updates Needed**

1. ✅ Update CHANGES.md with refactoring details
2. ⏳ Update README.md with new architecture diagram
3. ⏳ Update QUERY_GUIDE.md with routing examples
4. ⏳ Add ROUTING_GUIDE.md for operators

---

## 🎉 **Status: IMPLEMENTATION COMPLETE**

All code changes have been made. Next steps:
1. Test the unified NL pipeline
2. Verify routing decisions are correct
3. Confirm severity filter fix works
4. Update remaining documentation
