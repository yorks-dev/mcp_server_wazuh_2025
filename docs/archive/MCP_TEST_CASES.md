# MCP Server Test Cases - Reference Guide

## Quick Test Execution

```bash
# Run all comprehensive test cases
./test_mcp_cases.py

# Run individual test case via curl
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent logs from last 15 minutes"}'
```

---

## ✅ TEST CASE 1 — Fetch Recent Logs (Basic Query Test)

**Purpose:** Verify the MCP Server can query Wazuh Indexer and retrieve recent log entries.

**Natural Language Query:**
```
Show me recent logs from last 15 minutes
```

**Expected Behavior:**
- HTTP 200 from Indexer
- JSON output containing log documents
- Fields present: `rule.id`, `agent.id`, `timestamp`, `@timestamp`

**Pass Conditions:**
- ✓ Logs are returned (even if 0 results for empty time window)
- ✓ No errors: invalid token, index not found, unauthorized, connection refused
- ✓ Required fields are accessible in response

**Test Result:** ✅ PASS

---

## ✅ TEST CASE 2 — Test Search by Agent ID

**Purpose:** Verify Indexer logs can be filtered by Agent ID — crucial for threat investigation.

**Natural Language Query:**
```
Get logs for agent 001 in last 1 hour
```

**Expected DSL Conversion:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"agent.id": "001"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

**Expected Results:**
- Logs only from agent 001
- No unrelated agent logs
- Minimum 1 document returned (if agent is active)

**Pass Conditions:**
- ✓ All returned logs contain: `"agent": {"id": "001"}`
- ✓ Agent filter properly applied in parsed_query
- ✓ No data leakage from other agents

**Test Result:** ✅ PASS

---

## ✅ TEST CASE 3 — Validate Rule Hit Logs (Security Rule Detection)

**Purpose:** Check whether Wazuh Indexer can return logs triggered by a specific Wazuh rule.

**Natural Language Query:**
```
Show security alerts for rule 5501
```

**Expected DSL Conversion:**
```json
{
  "query": {
    "term": {"rule.id": "5501"}
  }
}
```

**Expected Results:**
- At least one log with `"rule.id": "5501"`
- Fields included:
  - `rule.description`
  - `rule.level`
  - `timestamp`
  - `agent.id`

**Pass Conditions:**
- ✓ All logs contain: `"rule": {"id": "5501"}`
- ✓ Rule metadata fields are present
- ✓ Query executes without field validation errors

**Test Result:** ✅ PASS

---

## ✅ TEST CASE 4 — Invalid Query / Zero Logs Returned (Error Handling)

**Purpose:** Ensure MCP handles errors from Indexer properly and gracefully.

**Natural Language Query:**
```
Get logs for agent 99999 in last 5 minutes
```
*(Such an agent should not exist)*

**Expected Result:**
- MCP returns: "No logs found for agent 99999" or similar graceful message
- HTTP 200 (not HTTP 500)
- Zero results returned

**Pass Conditions:**
- ✓ No Python exceptions in MCP Server response
- ✓ No stack trace visible to user
- ✓ No HTTP 500 errors
- ✓ Clean graceful response with clear message
- ✓ System remains stable after invalid query

**Test Result:** ✅ PASS

---

## ⭐ BONUS TEST — Threat Hunting Query (IP Search)

**Purpose:** Validate threat hunting capability by searching logs via source IP.

**Natural Language Query:**
```
Show logs where source IP is 8.8.8.8
```

**Expected DSL Conversion:**
```json
{
  "query": {
    "term": {"data.srcip": "8.8.8.8"}
  }
}
```

**Expected Results:**
- Should return security/network logs involving that IP
- Indexer must not throw:
  - ❌ bad request
  - ❌ unknown field
  - ❌ authentication failure

**Pass Conditions:**
- ✓ Query executes successfully (HTTP 200)
- ✓ No field validation errors
- ✓ `data.srcip` filter properly applied
- ✓ Results contain source IP in `data.srcip` field (if data exists)

**Test Result:** ✅ PASS

---

## Test Results Summary

| Test Case | Status | Description |
|-----------|--------|-------------|
| Test 1 | ✅ PASS | Basic log retrieval |
| Test 2 | ✅ PASS | Agent ID filtering |
| Test 3 | ✅ PASS | Rule ID filtering |
| Test 4 | ✅ PASS | Error handling (non-existent agent) |
| Bonus | ✅ PASS | Threat hunting (IP search) |

**Overall:** 5/5 PASSED (100% success rate)

---

## Running Tests

### Automated Test Suite
```bash
# Run all tests with detailed output
./test_mcp_cases.py

# Exit code 0 = all pass, 1 = some failed
echo $?
```

### Manual Testing via Frontend
1. Open http://localhost:8080
2. Use the example queries:
   - "Show me critical alerts from today"
   - "SSH login failures from last hour"
   - "Show me brute force attempts"
3. Verify routing info, confidence scores, and results

### Manual Testing via curl
```bash
# Test Case 1
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent logs from last 15 minutes"}'

# Test Case 2
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Get logs for agent 001 in last 1 hour"}'

# Test Case 3
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show security alerts for rule 5501"}'

# Test Case 4
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Get logs for agent 99999 in last 5 minutes"}'

# Bonus Test
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show logs where source IP is 8.8.8.8"}'
```

---

## Validation Checklist

### ✅ Functionality Tests
- [x] Natural language parsing works
- [x] DSL query generation is correct
- [x] Agent filtering works properly
- [x] Rule filtering works properly
- [x] Time range filtering works
- [x] IP/network field filtering works
- [x] Error handling is graceful

### ✅ Performance Tests
- [x] Queries complete within timeout (60s)
- [x] No memory leaks or resource exhaustion
- [x] Concurrent queries handled properly

### ✅ Security Tests
- [x] No SQL/NoSQL injection possible
- [x] Field allowlist enforced
- [x] Index allowlist enforced
- [x] Authentication errors handled
- [x] No data leakage between agents

### ✅ Integration Tests
- [x] Elasticsearch connection stable
- [x] Wazuh API integration working
- [x] GPT-4o parsing accurate
- [x] Frontend displays results correctly

---

## Troubleshooting

### Test Failures

**"Connection refused"**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**"No logs found" for all tests**
```bash
# Check Elasticsearch connectivity
curl -u admin:SecretPassword https://localhost:9200/_cluster/health?pretty -k

# Verify indices exist
curl -u admin:SecretPassword https://localhost:9200/_cat/indices?v -k
```

**"Timeout" errors**
- Check `app/llm_client.py` timeout settings (60s default)
- Verify GPT API key is valid
- Check network connectivity to OpenAI
- Review timing logs: parse, query, format stages

**"Field validation" errors**
- Verify field is in FIELD_ALLOWLIST (`app/config.py`)
- Check FIELD_TYPES mapping (`app/validators.py`)
- Review field naming (e.g., `data.srcip` not `srcip`)

---

## Performance Benchmarks

**Typical Query Times:**
- Parse stage: 8-13 seconds (GPT-4o processing)
- Query stage: 1-5 seconds (Elasticsearch)
- Format stage: 3-8 seconds (GPT-4o summary)
- **Total: 12-26 seconds** (varies with GPT API load)

**Acceptable Ranges:**
- ✅ < 30s: Excellent
- ⚠️ 30-60s: Acceptable (during peak times)
- ❌ > 60s: Timeout (investigate bottleneck)

---

## Related Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Comprehensive testing procedures
- [FRONTEND_TESTING.md](FRONTEND_TESTING.md) - UI-specific test scenarios
- [TEST_COMMANDS.md](TEST_COMMANDS.md) - Additional test commands
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API reference

---

**Last Updated:** 2025-12-23  
**Test Suite Version:** 1.0  
**Status:** ✅ All Tests Passing
