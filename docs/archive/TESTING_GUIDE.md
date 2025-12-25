# Testing Quick Reference

## Server Status
✅ Server is running on: http://localhost:8000
🔍 Health check: http://localhost:8000/health

## Quick Test Commands

### 1. Simple curl test
```bash
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all agents"}' | jq
```

### 2. Run automated test suite (bash)
```bash
./test_queries.sh
```

### 3. Run comprehensive test suite (Python)
```bash
python3 test_queries.py
# or
/home/kaustubh/mcp_server_wazuh_2025/.venv/bin/python test_queries.py
```

### 4. Check server logs
```bash
# Watch live logs
tail -f /tmp/wazuh_query.log

# Check errors only
grep ERROR /tmp/wazuh_query.log
```

## Test Query Categories

### Agent Context Tests
- ✅ "Show me all agents" (SIMPLE_PIPELINE)
- ✅ "List active agents" (SIMPLE_PIPELINE)
- ✅ "Get alerts from Windows agent" (ADVANCED + agent context)
- ✅ "Show logs from agent 001" (ADVANCED + agent validation)

### Time-Aware Tests
- ✅ "Recent alerts" (uses current UTC time)
- ✅ "Logs from last 15 minutes" (time calculation)
- ✅ "Critical events today" (today calculation)
- ✅ "Failed logins in last hour" (relative time)

### Rule Mapping Tests
- ✅ "SSH login failures" (rules 5710, 5551)
- ✅ "Windows failed logins" (EventID 4625, rule 60204)
- ✅ "Brute force attempts" (rules 5720, 87801)
- ✅ "File modifications" (FIM rules 31101-31103)

### Field Validation Tests
- ✅ "High severity alerts" (severity → rule.level)
- ✅ "Logs from agent X" (agent → agent.name)
- ✅ "Alerts from IP X" (source_ip → data.srcip)

### Decoder Tests
- ✅ "Show me SSH logs" (decoder.name = sshd)
- ✅ "Windows events" (decoder.name = windows)
- ✅ "Firewall logs" (decoder.name = firewall)

## Expected Behaviors

### Routing Logic
- **SIMPLE_PIPELINE**: "Show me all agents", "List agents", "Agent status"
- **ADVANCED_PIPELINE**: Any query with time reference or alert/log data

### Agent Context
- GPT receives list of real agents before parsing
- Prevents hallucination of non-existent agent names
- Cached for 5 minutes (300s)

### Time Context
- GPT knows current UTC time
- Correctly calculates "today", "yesterday", "this week"
- Defaults to last 24h if no time specified

### Rule Context
- GPT knows common security rules
- Maps "SSH failures" → rules 5710, 5551
- Maps "Windows failures" → EventID 4625

### Field Corrections
- Auto-corrects common mistakes
- severity → rule.level
- agent → agent.name
- source_ip → data.srcip

## Validation Checklist

After running tests, verify:

✅ **Agent Context Working**
- [ ] Queries reference real agent names from your system
- [ ] No invented/hallucinated agent names in filters

✅ **Time Awareness Working**
- [ ] "today" queries use now/d
- [ ] "last hour" queries use now-1h
- [ ] Time ranges are correctly calculated

✅ **Rule Mapping Working**
- [ ] SSH failures use rules 5710/5551
- [ ] Windows failures use EventID 4625
- [ ] Brute force uses rules 5720/87801

✅ **Field Validation Working**
- [ ] All filters use valid field names
- [ ] No "severity" field (should be rule.level)
- [ ] No "agent" field (should be agent.name)

✅ **Pipeline Routing Working**
- [ ] Agent queries → SIMPLE_PIPELINE
- [ ] Time-based queries → ADVANCED_PIPELINE
- [ ] Confidence scores are present

## Debugging Tips

### If queries fail:
1. Check server logs: `tail -f /tmp/wazuh_query.log`
2. Verify Wazuh connection: `curl http://localhost:8000/health`
3. Check GPT responses in logs (look for "Raw routing response")
4. Verify .env file has correct credentials

### If agent context not working:
1. Test agent API: `curl http://localhost:8000/agents`
2. Check logs for "Updated agent cache" message
3. Verify Wazuh Manager API is accessible

### If field corrections not working:
1. Look for "Corrected field" in logs
2. Check validate_and_correct_plan function
3. Verify FIELD_CORRECTIONS dict has the mapping

### If time parsing wrong:
1. Check "CURRENT TIME CONTEXT" in system prompt
2. Verify datetime.now(timezone.utc) is correct
3. Look for time parsing in GPT response

## Sample Expected Outputs

### Good Output (Success)
```json
{
  "success": true,
  "routing": {
    "pipeline": "ADVANCED_PIPELINE",
    "reasoning": "Time-based query for alerts",
    "confidence": 0.95
  },
  "parsed_query": {
    "filters": [
      {"field": "rule.level", "op": "gte", "value": 8}
    ],
    "time": {
      "from": "now-24h",
      "to": "now"
    }
  },
  "summary": "Found 15 high severity alerts...",
  "raw_data": {...}
}
```

### Error Output (Failed)
```json
{
  "detail": "Invalid query structure: field 'severity' not valid"
}
```

## Performance Benchmarks

Expected response times:
- Simple queries (agents): 200-500ms
- Advanced queries (indexer): 1-3s
- Complex aggregations: 3-5s

If slower:
- Check Wazuh Indexer performance
- Verify network latency
- Review query complexity

## Next Steps

After testing:
1. Document any failed queries
2. Note edge cases that need improvement
3. Check if agent fuzzy matching is needed
4. Consider adding more rule mappings
5. Evaluate if query limits need adjustment
