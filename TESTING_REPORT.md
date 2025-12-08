# Wazuh MCP Server - Route Testing Results
**Date:** December 2, 2025
**Server:** http://localhost:8000

## ✅ Working Routes (Wazuh API Connected)

### 1. GET / - Home/Status
**Status:** ✅ Working  
**Response:**
```json
{
  "message": "Welcome to the MCP Server for Wazuh. The MCP Server has been started successfully.",
  "authenticated": true,
  "wazuh_url": "https://10.21.236.157:55000"
}
```

### 2. GET /test - Connection Test
**Status:** ✅ Working  
**Wazuh Connection:** ✅ Authenticated  
**Response:**
```json
{
  "status": "connected",
  "token_valid": true,
  "agents_count": 4,
  "sample_agents": [
    {"id": "000", "name": "hpotwaz", "status": "active"},
    {"id": "001", "name": "client01", "status": "disconnected"},
    {"id": "002", "name": "DC01", "status": "disconnected"}
  ]
}
```

### 3. GET /agents - Get All Agents
**Status:** ✅ Working  
**Total Agents:** 4  
**Data Retrieved:**
| ID  | Name     | Status       | IP            | OS                                    |
|-----|----------|--------------|---------------|---------------------------------------|
| 000 | hpotwaz  | active       | 127.0.0.1     | Ubuntu                                |
| 001 | client01 | disconnected | 10.21.237.9   | Microsoft Windows 10 Pro              |
| 002 | DC01     | disconnected | 10.21.234.210 | Microsoft Windows Server 2019         |
| 003 | tpot     | disconnected | 10.21.234.73  | Ubuntu                                |

## ⚠️ Partial Routes (Missing Dependencies)

### 4. POST /query_llm/ - LLM Query
**Status:** ⚠️ Endpoint works, LLM connection failed  
**Issue:** OpenAI API key not configured or invalid  
**Response:**
```json
{
  "response": "LLM request failed."
}
```
**Fix Required:** Update `OPENAI_API_KEY` in `.env` or `app/config.py`

## ❌ Routes Requiring Additional Services

### 5. POST /mcp/wazuh.search - Wazuh Search (DSL Query)
**Status:** ❌ Not functional  
**Issue:** OpenSearch/Elasticsearch not running  
**Error:** Connection refused to OpenSearch at `http://localhost:9200`  
**Services Required:**
- Wazuh Indexer (OpenSearch) must be running
- Configure in `app/config.py`:
  ```python
  OPENSEARCH_HOST: str = "http://localhost:9200"
  OPENSEARCH_USER: str = "admin"
  OPENSEARCH_PASS: str = "NxFdeGIYQMtZ8077IQ?qJRABNpPsPYoa"
  ```

## Summary

### ✅ Fully Working (3/5 routes)
- Home/Status endpoint
- Connection test with Wazuh
- Agent retrieval from Wazuh API

### ⚠️ Needs Configuration (1/5 routes)
- LLM query endpoint (needs OpenAI API key)

### ❌ Needs External Service (1/5 routes)
- Wazuh search endpoint (needs Wazuh Indexer/OpenSearch)

## Wazuh API Integration Status
- **Authentication:** ✅ Working
- **Bearer Token:** ✅ Valid and cached
- **Agent API:** ✅ Connected
- **API Endpoint:** `https://10.21.236.157:55000`
- **Credentials:** Configured correctly

## Next Steps to Enable All Routes

1. **Enable LLM Queries:**
   ```bash
   # Add to .env or config.py
   OPENAI_API_KEY=sk-proj-your-actual-key
   ```

2. **Enable Wazuh Search:**
   - Ensure Wazuh Indexer is running at `https://10.21.236.157:9200`
   - Or update `OPENSEARCH_HOST` to correct location
   - Verify indexer credentials are correct

## Test Commands

```powershell
# Test basic routes
Invoke-WebRequest "http://localhost:8000/" | Select-Object -ExpandProperty Content
Invoke-WebRequest "http://localhost:8000/test" | Select-Object -ExpandProperty Content
Invoke-WebRequest "http://localhost:8000/agents" | Select-Object -ExpandProperty Content

# Test LLM (after configuring API key)
$body = @{ prompt = "Hello" } | ConvertTo-Json
Invoke-WebRequest "http://localhost:8000/query_llm/" -Method POST -Body $body -ContentType "application/json"

# Test search (after starting OpenSearch)
$searchBody = @{
  indices = "wazuh-alerts-*"
  time = @{ from = (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ssZ"); to = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ") }
  filters = @(@{ field = "rule.level"; op = "gte"; value = 5 })
  dry_run = $true
} | ConvertTo-Json -Depth 5
Invoke-WebRequest "http://localhost:8000/mcp/wazuh.search" -Method POST -Body $searchBody -ContentType "application/json"
```
