# Wazuh MCP Server - Quick Reference

## 🚀 Start Server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔗 SSH Tunnel (Remote Wazuh)

```bash
# Start
./scripts/setup_dev_tunnel.sh

# Stop
./scripts/stop_dev_tunnel.sh

# Manual
ssh -f -N -L 9200:localhost:9200 user@wazuh-server
```

## 🌐 URLs

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Frontend: `frontend/index.html`

## 📡 API Endpoints

### Natural Language Query
```bash
POST /query/nl
{"query": "Show me critical alerts from today"}
```

### Direct DSL Query
```bash
POST /query/dsl
{
  "index": "wazuh-alerts-*",
  "query": {"match_all": {}},
  "size": 50,
  "include_summary": true
}
```

### Hybrid NL+DSL
```bash
POST /query/nl
{"query": "Analyze this: {\"index\":\"wazuh-alerts-*\",\"query\":{...}}"}
```

## 🧪 Testing

```bash
./tests/test_queries.py          # All tests
./tests/test_mcp_cases.py         # MCP tests (5/5)
./tests/test_advanced_dsl.py      # DSL tests (5/5)
./tests/diagnose_timeout.py       # Performance
```

## 🔧 Common Issues

| Problem | Solution |
|---------|----------|
| Port 9200 refused | `./scripts/setup_dev_tunnel.sh` |
| 401 Unauthorized | Check `.env` credentials |
| 429 Rate limit | Wait 60s or `include_summary: false` |
| Frontend blank | Check `curl localhost:8000/health` |

## 📋 Example Queries

**Show all agents**
```json
{"query": "Show me all agents"}
```

**Critical alerts (last 24h)**
```json
{
  "index": "wazuh-alerts-*",
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-24h"}}},
        {"range": {"rule.level": {"gte": 12}}}
      ]
    }
  }
}
```

**Failed SSH logins**
```json
{"query": "Show me SSH login failures from the last hour"}
```

**Brute force attempts**
```json
{"query": "Show me brute force attempts"}
```

## 📁 File Locations

- Config: `.env`
- Backend: `app/main.py`
- Frontend: `frontend/index.html`
- Tests: `tests/`
- Scripts: `scripts/`
- Docs: `DOCUMENTATION.md`

## 🔐 Environment Variables

```bash
OPENAI_API_KEY=sk-...
WAZUH_API_HOST=https://10.21.232.103
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=admin
WAZUH_API_PASSWORD=***
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=***
```

## 📚 Documentation

**Full docs**: [DOCUMENTATION.md](DOCUMENTATION.md)

---

**Quick tip**: Use `include_summary: false` in DSL queries for faster responses without GPT analysis.
