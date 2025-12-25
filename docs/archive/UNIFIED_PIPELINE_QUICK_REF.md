# Unified NL Pipeline - Quick Reference

## 🎯 Two Query Methods

### 1. Natural Language (Intelligent Routing)
**Endpoint**: `POST /query/nl`  
**Body**: `{"query": "Show me all agents"}`

**How it works**:
1. GPT-4o analyzes your question
2. Routes to SIMPLE_PIPELINE (Wazuh API) or ADVANCED_PIPELINE (Indexer)
3. Executes query on appropriate backend
4. Returns results with routing metadata

**Example Response**:
```json
{
  "success": true,
  "routing": {
    "pipeline": "SIMPLE_PIPELINE",
    "reasoning": "Query asks for agent information",
    "confidence": 0.95
  },
  "summary": "Found 4 agents: 1 active, 3 disconnected",
  "raw_data": {...},
  "dsl": null
}
```

---

### 2. Direct DSL (Expert Mode)
**Endpoint**: `POST /query/dsl`  
**Body**: 
```json
{
  "index": "wazuh-alerts-*",
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-24h", "lte": "now"}}},
        {"range": {"rule.level": {"gte": 12}}}
      ]
    }
  },
  "size": 50
}
```

---

## 🔀 Routing Examples

### → SIMPLE_PIPELINE (Wazuh API)
- "Show me all agents"
- "List active agents"
- "Get agent 001 details"
- "How many disconnected agents?"

### → ADVANCED_PIPELINE (Indexer)
- "Critical alerts from last 24 hours"
- "Get logs from last 15 minutes"
- "High severity alerts from last week"
- "Show alerts with rule level >= 10"

---

## 🚀 Quick Start

### Terminal 1: SSH Tunnel (for Advanced queries)
```bash
./scripts/setup_dev_tunnel.sh
# Tunnels localhost:9200 → VM:9200
```

### Terminal 2: FastAPI Server
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Frontend
```bash
cd frontend
python3 -m http.server 8080
```

Open browser: http://localhost:8080

---

## ⚙️ Backend Architecture

```
Natural Language Query
        ↓
    route_query()  ←  GPT-4o decides
    /          \
SIMPLE        ADVANCED
   ↓              ↓
Wazuh API    Indexer
(port 55000)  (port 9200)
   ↓              ↓
  Results    ←  format_results()
```

---

## 🧪 Test Queries

### Test 1: Simple Routing
```
Input: "Show me all agents"
Expected Routing: SIMPLE_PIPELINE
Expected Result: 4 agents listed
```

### Test 2: Advanced Routing
```
Input: "Critical alerts from last 24 hours"
Expected Routing: ADVANCED_PIPELINE
Expected Result: Alerts with rule.level >= 12
```

### Test 3: No Severity Filter (Bug Fix Test)
```
Input: "Get logs from last 15 minutes"
Expected Routing: ADVANCED_PIPELINE
Expected Filters: [] (empty - NO severity filter!)
Expected Result: ALL logs, not just critical
```

---

## 📋 Files Changed

| File | Status | Description |
|------|--------|-------------|
| `app/llm_client.py` | ✅ Complete rewrite | Routing + parsing logic |
| `app/main.py` | ✅ Added endpoints | `/query/nl` and `/query/dsl` |
| `frontend/index.html` | ✅ Updated UI | 2-button pipeline selector |
| `frontend/app.js` | ✅ New logic | Calls unified endpoints |
| `frontend/styles.css` | ✅ Added styles | Routing info display |

---

## 🐛 Known Issues

None! All previous issues fixed:
- ✅ Severity filter bug (fixed with updated prompt)
- ✅ Agent routing bug (now goes to SIMPLE_PIPELINE)
- ✅ CORS issues (middleware configured)
- ✅ SSH tunnel requirement (documented)

---

## 📖 Documentation

- **UNIFIED_PIPELINE_SUMMARY.md**: Full implementation details
- **QUERY_GUIDE.md**: Query examples and capabilities
- **COMPLETE_PIPELINE_GUIDE.md**: End-to-end flow diagrams
- **QUICKSTART.md**: Setup instructions
