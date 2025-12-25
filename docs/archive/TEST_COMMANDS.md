# Testing Summary & Commands

## ✅ Server Status: RUNNING
- URL: http://localhost:8000
- Status: ✓ Healthy (Successfully authenticated to Wazuh)
- Available Agents: 4 (wazuh.master, Linux_VM x2, Honeypot)

## 🎯 Quick Test Commands

### 1. Test Simple Query (Agent List)
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all agents"}' | jq
```
**Expected**: SIMPLE_PIPELINE, confidence 0.95, list of 4 agents

### 2. Test Time-Aware Query
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me critical alerts from the last hour"}' | jq
```
**Expected**: ADVANCED_PIPELINE, time from "now-1h", rule.level >= 12

### 3. Test Agent Context (with real agent)
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Get alerts from Linux_VM agent"}' | jq
```
**Expected**: Filter with agent.name = "Linux_VM"

### 4. Test Rule Mapping (SSH failures)
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me SSH login failures"}' | jq
```
**Expected**: Rules 5710, 5551, decoder.name = "sshd"

### 5. Test Windows Events
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Windows failed logins in last 24 hours"}' | jq
```
**Expected**: EventID 4625, rule 60204, time from "now-24h"

### 6. Test Brute Force Detection
```bash
curl -s -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me brute force attempts"}' | jq
```
**Expected**: Rules 5720/87801, limit >= 100

## 🧪 Run Test Suites

### Bash Test Suite (26 automated tests)
```bash
chmod +x test_queries.sh
./test_queries.sh
```

### Python Test Suite (comprehensive with validation)
```bash
python3 test_queries.py
# or with venv
/home/kaustubh/mcp_server_wazuh_2025/.venv/bin/python test_queries.py
```

## 📊 What Each Test Suite Covers

### Bash Script (`test_queries.sh`)
- ✅ Agent context (3 tests)
- ✅ Time awareness (4 tests)
- ✅ Rule mapping (4 tests)
- ✅ Severity levels (3 tests)
- ✅ Pattern detection (3 tests)
- ✅ Decoder filters (3 tests)

### Python Script (`test_queries.py`)
- ✅ Agent context validation
- ✅ Time awareness checks
- ✅ Rule mapping verification
- ✅ Field name corrections
- ✅ Interactive mode for manual testing

## 🔍 What to Look For

### ✅ SUCCESS Indicators:
1. **Routing Works**: Simple queries → SIMPLE_PIPELINE, time queries → ADVANCED_PIPELINE
2. **Agent Context**: Queries reference real agent names (Linux_VM, Honeypot, wazuh.master)
3. **Time Parsing**: "last hour" → now-1h, "today" → now/d
4. **Rule Mapping**: "SSH failures" → rules 5710/5551
5. **Field Corrections**: Uses rule.level (not severity), agent.name (not agent)
6. **Confidence Scores**: High (0.95) for clear queries, medium/low for ambiguous ones

### ⚠️ WARNING Signs:
1. Agent names not in your system (hallucination)
2. Wrong pipeline selection
3. Invalid field names in filters
4. Missing time ranges
5. No rule filters when security event mentioned

### ❌ ERROR Indicators:
1. HTTP 400/500 errors
2. "field not valid" errors
3. Empty parsed_query
4. Missing routing information
5. Timeout errors

## 📝 Sample Test Scenarios

### Scenario 1: Agent-Aware Query
**Query**: "Show me logs from the Honeypot agent"
**Verify**:
- [ ] Uses real agent name "Honeypot"
- [ ] Filter: {"field": "agent.name", "op": "eq", "value": "Honeypot"}
- [ ] Pipeline: ADVANCED_PIPELINE

### Scenario 2: Time-Sensitive Query
**Query**: "Get alerts from today"
**Verify**:
- [ ] Time from: "now/d"
- [ ] Time to: "now"
- [ ] Uses current UTC time context

### Scenario 3: Security Event Mapping
**Query**: "Show me failed login attempts"
**Verify**:
- [ ] Rules: 5710, 5551, 5503, or EventID 4625
- [ ] Decoder filter present (sshd or windows)
- [ ] Limit >= 50

### Scenario 4: Complex Pattern Query
**Query**: "Summarize brute force attacks by IP"
**Verify**:
- [ ] Limit >= 100 (pattern detection)
- [ ] Rules 5720 or 87801
- [ ] rule.level >= 7

## 🐛 Debugging Commands

### Check Server Logs
```bash
# Real-time logs
tail -f /tmp/wazuh_query.log

# Recent errors
tail -100 /tmp/wazuh_query.log | grep ERROR

# GPT responses
grep "Raw routing response" /tmp/wazuh_query.log | tail -5
```

### Check Agent Cache
```bash
curl -s http://localhost:8000/agents | jq '.data.affected_items[] | {id, name, os: .os.name, status}'
```

### Test Specific Components
```bash
# Health check
curl http://localhost:8000/health | jq

# Direct DSL query
curl -s -X POST http://localhost:8000/query/dsl \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 10,
    "index": "wazuh-alerts-*"
  }' | jq
```

## 📈 Performance Benchmarks

Expected response times:
- **Simple queries**: 200-800ms
- **Advanced queries**: 1-3s
- **Large result sets**: 3-5s
- **Agent cache refresh**: 300-500ms

## 🎓 Example Test Flow

1. **Start fresh**:
   ```bash
   # Clear old logs
   > /tmp/wazuh_query.log
   
   # Restart server
   pkill -f uvicorn
   /home/kaustubh/mcp_server_wazuh_2025/.venv/bin/uvicorn app.main:app --reload
   ```

2. **Run automated suite**:
   ```bash
   ./test_queries.sh | tee test_results.txt
   ```

3. **Check results**:
   ```bash
   grep "✓ SUCCESS" test_results.txt | wc -l  # Count successes
   grep "✗ FAILED" test_results.txt  # Check failures
   ```

4. **Interactive testing**:
   ```bash
   python3 test_queries.py
   # Choose option 1 for manual mode
   ```

5. **Review logs**:
   ```bash
   grep -A5 "Advanced query plan" /tmp/wazuh_query.log | tail -20
   ```

## ✨ Expected Improvements From Enhancements

### Before Enhancements:
- ❌ GPT hallucinated agent names
- ❌ Time parsing inconsistent
- ❌ Generic security queries had no rule mapping
- ❌ Field names often wrong (severity, agent, source_ip)
- ⚠️ No decoder context

### After Enhancements:
- ✅ Agent names validated against real list
- ✅ Current time injected for accurate relative queries
- ✅ 10+ common security rules mapped
- ✅ Field auto-correction (severity→rule.level)
- ✅ Decoder context (SSH, Windows, firewall)
- ✅ Enhanced field mappings (25+ valid fields)
- ✅ Query intent analyzer
- ✅ Latest GPT model (gpt-4o-2024-11-20)

## 🚀 Next Steps After Testing

1. **Document edge cases** found during testing
2. **Note query patterns** that work well
3. **Identify improvements** needed
4. **Test with real security scenarios** from your environment
5. **Adjust limits/thresholds** based on data volume
6. **Consider adding** custom rules specific to your deployment

## 💡 Pro Tips

- Use `jq` for pretty JSON output
- Save successful queries as templates
- Monitor GPT token usage in logs
- Test with your actual security events
- Verify agent cache updates every 5 minutes
- Check timezone handling for your region
- Test edge cases (empty results, no agents, etc.)

---

**Ready to test!** Start with: `./test_queries.sh` or `python3 test_queries.py`
