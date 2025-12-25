# MCP Server Updates - December 15, 2025

## ✅ Changes Implemented

### 1. **Security Improvements**
- **File**: [`mcp/mcp_server_metadata.json`](../mcp/mcp_server_metadata.json)
- **Change**: Removed hardcoded credentials
- **Before**: Direct passwords in JSON
- **After**: Environment variable references (`env:WAZUH_API_PASSWORD`)

### 2. **MCP Integration**
- **File**: [`app/main.py`](../app/main.py)
- **Changes**:
  - Imported `MCPHandlers` class
  - Initialize `mcp_handlers` on startup
  - Added `/health` endpoint for MCP health check
  - Cleanup handlers on shutdown
- **Benefit**: Proper separation of concerns, MCP protocol ready

### 3. **Query Filter Fix**
- **File**: [`app/llm_client.py`](../app/llm_client.py)
- **Change**: Updated LLM system prompt
- **Added**: "Only add severity filters when explicitly mentioned"
- **Result**: Queries like "logs from last 15 minutes" now return **ALL logs**, not just critical ones

### 4. **Frontend Display**
- **Status**: Already working correctly!
- **Features**:
  - Natural language summary (📝 tab)
  - Formatted data with severity badges (structured cards)
  - Raw JSON with full indexer response
  - Generated DSL query display
- **No changes needed**: Frontend was already properly displaying both views

### 5. **Testing**
- **New File**: [`tests/test_query_filters.py`](../tests/test_query_filters.py)
- **Purpose**: Validate that time-based queries return all logs
- **Test Cases**:
  1. Time-based only (no severity) ✓
  2. Recent logs (no severity) ✓
  3. Logs from last hour ✓
  4. Critical logs (with severity) ✓
  5. Simple query test ✓

### 6. **Documentation**
- **New File**: [`docs/QUERY_GUIDE.md`](../docs/QUERY_GUIDE.md)
- **Content**:
  - Query types explained
  - Frontend display guide
  - Example queries
  - Troubleshooting tips
  - Operator best practices

---

## 🎯 Key Capabilities Now Available

### ✅ Retrieve ALL Logs
Operators can now query:
```
"get logs from last 15 minutes"
"show me recent logs"
"logs from last hour"
```
**Result**: Returns **ALL** logs regardless of severity

### ✅ Filter by Severity (When Needed)
```
"critical alerts from last 24 hours"
"high severity incidents today"
```
**Result**: Returns **ONLY** filtered logs

### ✅ Dual View for Operators
Every query provides:
1. **Natural Language Summary** - For quick understanding
2. **Technical Details** - For deep analysis
   - Formatted cards with severity badges
   - Raw JSON from indexer
   - Generated DSL query

---

## 🔧 Technical Details

### MCP Handler Integration
```python
# Startup
mcp_handlers = MCPHandlers(
    wazuh_url=wazuh_url,
    username=settings.WAZUH_API_USERNAME,
    password=settings.WAZUH_API_PASSWORD
)
await mcp_handlers.client.authenticate()

# Health Check
@app.get("/health")
async def health_check():
    return await mcp_handlers.mcp_health_check()
```

### LLM Prompt Update
```python
IMPORTANT: Only add severity filters when explicitly mentioned. 
For queries like "logs from last 15 minutes" or "show me recent logs", 
use empty filters array to return ALL logs regardless of severity.
```

### Query Response Structure
```json
{
  "query": "get logs from last 15 minutes",
  "parsed_plan": {
    "indices": "wazuh-alerts-*",
    "time": {"from": "now-15m", "to": "now"},
    "filters": [],  // Empty = ALL logs
    "limit": 50
  },
  "dsl": {...},  // Generated OpenSearch query
  "raw_data": {  // Full indexer response
    "hits": {
      "total": {"value": 247},
      "hits": [...]
    }
  },
  "response": "Natural language summary..."
}
```

---

## 📊 Verification Steps

### 1. Start Server
```bash
cd /home/kaustubh/mcp_server_wazuh_2025
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start SSH Tunnel
```bash
./scripts/setup_dev_tunnel.sh
```

### 3. Serve Frontend
```bash
python3 -m http.server 8080 --directory frontend
```

### 4. Test Queries
```bash
cd tests
python test_query_filters.py
```

### 5. Check Health
```bash
curl http://localhost:8000/health | jq
```

---

## 🎨 Frontend Usage

### Access
Open: http://localhost:8080

### Try These Queries
1. **All Logs**: "get logs from last 15 minutes"
2. **Critical Only**: "critical alerts from last hour"
3. **Agent Specific**: "logs from agent web-01 today"

### View Results
- Click **Formatted** tab → See structured cards
- Click **Raw JSON** tab → See complete response
- Click **DSL** tab → See generated query

---

## 🔐 Security Notes

### Credentials
- All sensitive data now in `.env`
- Metadata file references environment variables
- No hardcoded passwords in git

### Indexer Access
- Frontend → MCP Server → SSH Tunnel → Indexer
- No direct browser access to indexer
- CORS handled by MCP server
- TLS issues avoided via tunnel

---

## 📚 Additional Resources

- **Query Guide**: [`docs/QUERY_GUIDE.md`](../docs/QUERY_GUIDE.md)
- **Quick Reference**: [`QUICK_REFERENCE.md`](../QUICK_REFERENCE.md)
- **Security Checklist**: [`SECURITY_CHECKLIST.md`](../SECURITY_CHECKLIST.md)
- **Complete Pipeline**: [`docs/COMPLETE_PIPELINE_GUIDE.md`](../docs/COMPLETE_PIPELINE_GUIDE.md)

---

## ✅ Summary

**All requirements met:**
1. ✅ MCP layer properly integrated
2. ✅ Hardcoded credentials removed
3. ✅ Queries retrieve ALL logs when no severity specified
4. ✅ Frontend displays both natural language and raw technical data
5. ✅ Operator can see structured formatted view
6. ✅ Test suite validates behavior
7. ✅ Documentation added for operators

**The operator now gets the best of both worlds:**
- Natural language summaries for quick insights
- Raw technical data for deep analysis
- Time-based queries return ALL logs
- Severity filters work when explicitly requested
