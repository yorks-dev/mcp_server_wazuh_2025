# 🚀 Wazuh MCP Server - Quick Reference

## One-Line Start

```bash
./scripts/dev_start.sh
```

Access: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

---

## 📋 Common Commands

```bash
# Start development server (with SSH tunnel)
./scripts/dev_start.sh

# Run tests
./scripts/run_tests.sh

# Stop tunnel
./scripts/stop_dev_tunnel.sh

# Manual start (no tunnel)
source .venv/bin/activate
uvicorn app.main:app --reload
```

---

## 🔌 API Quick Tests

```bash
# Health check
curl http://localhost:8000/

# Connection test
curl http://localhost:8000/test

# Simple query
curl -X POST http://localhost:8000/query/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all active agents"}'

# Advanced query with DSL
curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show high severity alerts from last 24 hours"}'

# Pre-built DSL
curl -X POST http://localhost:8000/mcp/wazuh.search \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "wazuh-alerts-*",
    "time": {"from": "now-24h", "to": "now"},
    "filters": [{"field": "rule.level", "op": "gte", "value": 8}],
    "limit": 10
  }'
```

---

## 📁 Project Layout

```
mcp_server_wazuh_2025/
├── app/              → Core application
├── mcp/              → MCP protocol handlers
├── scripts/          → Dev & deployment scripts
├── docs/             → Documentation
├── docker/           → Docker configs
├── .env              → Environment config
└── README.md         → Main documentation
```

---

## ⚙️ Configuration (.env)

```bash
# Required
WAZUH_API_HOST=https://10.21.236.157:55000
WAZUH_USERNAME=wazuh
WAZUH_PASSWORD=your-password

OPENSEARCH_HOST=https://localhost:9200  # Dev with tunnel
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-password

OPENAI_API_KEY=sk-proj-...
```

---

## 🛠️ Scripts Reference

| Script | What it does |
|--------|--------------|
| `dev_start.sh` | Sets up tunnel + starts server |
| `setup_dev_tunnel.sh` | SSH tunnel only |
| `stop_dev_tunnel.sh` | Stops tunnel + cleanup |
| `run_tests.sh` | Comprehensive tests |

---

## 🔍 Troubleshooting

```bash
# Check if tunnel is running
lsof -ti:9200

# Check if server is running
curl http://localhost:8000/

# View server logs
tail -f server.log

# Test Wazuh Indexer (through tunnel)
curl -k -u admin:password https://localhost:9200/_cluster/health

# Kill stuck processes
pkill -f "uvicorn app.main:app"
lsof -ti:9200 | xargs kill
```

---

## 📊 Query Examples

### Simple Queries (No DSL)
- "Show me all active agents"
- "List agents by status"
- "What agents are disconnected?"

### Advanced Queries (With DSL)
- "Show high severity alerts from last 24 hours"
- "Count alerts by rule level in last 7 days"
- "Show authentication failures from last week"
- "Find alerts from agent DC01"

---

## 🎯 Quick Tips

1. **Dev mode**: Always use `./scripts/dev_start.sh` for local testing
2. **Tunnel needed**: If Wazuh Indexer is VM-local only
3. **No tunnel**: Direct connection if Indexer exposed
4. **Test first**: Run `./scripts/run_tests.sh` before deploying
5. **Check logs**: `tail -f server.log` for debugging

---

## 📚 Documentation

- [README.md](README.md) - Complete guide
- [docs/PIPELINE_TEST_SUCCESS.md](docs/PIPELINE_TEST_SUCCESS.md) - Test results
- [docs/QUICKSTART.md](docs/QUICKSTART.md) - Getting started
- API Docs: `http://localhost:8000/docs` (interactive)

---

## 🆘 Common Issues

**Port 8000 in use:**
```bash
pkill -f "uvicorn app.main:app"
```

**Tunnel failed:**
```bash
./scripts/stop_dev_tunnel.sh
./scripts/setup_dev_tunnel.sh
```

**OpenSearch connection refused:**
- Check if tunnel is running: `lsof -ti:9200`
- Verify credentials in `.env`
- Test connection: `curl -k -u admin:pass https://localhost:9200`

---

**Last updated:** December 9, 2025
