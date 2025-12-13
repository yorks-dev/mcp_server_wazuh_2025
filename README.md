# Wazuh MCP Server

A Model Context Protocol (MCP) server for Wazuh SIEM integration with natural language query capabilities powered by GPT-4o.

## 🚀 Quick Start

```bash
# Clone and setup
cd mcp_server_wazuh_2025
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start development server
./scripts/dev_start.sh
```

Server runs at `http://localhost:8000` with API docs at `/docs`

---

## 📋 Features

### Three Query Approaches

1. **Simple Natural Language** - Basic queries via Wazuh API
   - `POST /query/simple`
   - Best for: Quick agent status, simple questions
   - No OpenSearch required

2. **Advanced Natural Language** - Complex queries with DSL
   - `POST /query/`
   - Best for: Time ranges, filtering, aggregations
   - Full NL → GPT-4o → DSL → Wazuh Indexer pipeline

3. **Pre-built DSL** - Direct OpenSearch queries
   - `POST /mcp/wazuh.search`
   - Best for: Programmatic access, automation
   - Fastest response time

---

## 🏗️ Architecture

```
┌─────────────┐
│  Operator   │ "Show me high severity alerts from last 24h"
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│         MCP Server (FastAPI)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Simple  │  │ Advanced │  │ Pre-built│ │
│  │    NL    │  │ NL + DSL │  │   DSL    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼─────────────┼─────────────┼────────┘
        │             │             │
        │      ┌──────▼──────┐      │
        │      │   GPT-4o    │      │
        │      │  (Parse &   │      │
        │      │   Format)   │      │
        │      └──────┬──────┘      │
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌──────────────────────────┐
│  Wazuh API  │ │   Wazuh Indexer          │
│  (Agents,   │ │   (OpenSearch)           │
│   Alerts)   │ │   Complex queries, DSL   │
└─────────────┘ └──────────────────────────┘
```

---

## 📦 Project Structure

```
mcp_server_wazuh_2025/
├── app/
│   ├── main.py              # FastAPI application
│   ├── wazuh_client.py      # Async Wazuh API client
│   ├── llm_client.py        # GPT-4o integration
│   ├── dsl_builder.py       # OpenSearch DSL generator
│   ├── es_client.py         # OpenSearch client
│   ├── schemas.py           # Pydantic models
│   ├── validators.py        # Field validation
│   ├── config.py            # Configuration
│   └── utils.py             # Utilities
├── mcp/
│   ├── handlers.py          # MCP protocol handlers
│   ├── schemas.py           # MCP schemas
│   └── tools.json           # Tool definitions
├── scripts/
│   ├── dev_start.sh         # Start dev environment
│   ├── setup_dev_tunnel.sh  # Setup SSH tunnel
│   ├── stop_dev_tunnel.sh   # Stop tunnel
│   └── run_tests.sh         # Test suite
├── docs/
│   ├── PIPELINE_TEST_SUCCESS.md  # Test results
│   ├── QUICKSTART.md             # Quick start
│   └── OLD_README.md             # Previous docs
├── .env                     # Environment config
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Wazuh API
WAZUH_API_HOST=https://your-wazuh-server:55000
WAZUH_USERNAME=wazuh
WAZUH_PASSWORD=your-password

# Wazuh Indexer (OpenSearch)
WAZUH_INDEXER_HOST=https://your-indexer:9200
WAZUH_INDEXER_USER=admin
WAZUH_INDEXER_PASSWORD=your-indexer-password

# OpenSearch (same as Indexer)
OPENSEARCH_HOST=https://your-indexer:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-indexer-password

# OpenAI
OPENAI_API_KEY=sk-proj-...
```

### Development Setup (SSH Tunnel)

For dev environments where Wazuh Indexer is only accessible via localhost:

```bash
# Automatically sets up SSH tunnel
./scripts/dev_start.sh

# Or manually
./scripts/setup_dev_tunnel.sh
source .venv/bin/activate
uvicorn app.main:app --reload

# Stop tunnel when done
./scripts/stop_dev_tunnel.sh
```

---

## 🔌 API Endpoints

### Health & Status

- `GET /` - Server health check
- `GET /test` - Wazuh connection test

### Query Endpoints

#### Simple Natural Language
```bash
POST /query/simple
Content-Type: application/json

{
  "query": "Show me all active agents"
}
```

#### Advanced Natural Language with DSL
```bash
POST /query/
Content-Type: application/json

{
  "query": "Show high severity alerts from last 24 hours"
}
```

#### Pre-built DSL Query
```bash
POST /mcp/wazuh.search
Content-Type: application/json

{
  "indices": "wazuh-alerts-*",
  "time": {"from": "now-24h", "to": "now"},
  "filters": [
    {"field": "rule.level", "op": "gte", "value": 8}
  ],
  "limit": 50
}
```

---

## 🧪 Testing

```bash
# Run comprehensive test suite
./scripts/run_tests.sh

# Or test individual endpoints
curl http://localhost:8000/test
curl -X POST http://localhost:8000/query/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "List all agents"}'
```

See [docs/PIPELINE_TEST_SUCCESS.md](docs/PIPELINE_TEST_SUCCESS.md) for complete test results.

---

## 📚 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Getting started guide (start here!)
- **[docs/COMPLETE_PIPELINE_GUIDE.md](docs/COMPLETE_PIPELINE_GUIDE.md)** - Detailed pipeline documentation
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference
- **API Docs**: `http://localhost:8000/docs` (interactive, when running)

---

## 🛠️ Development Scripts

All scripts are in `scripts/` directory:

| Script | Purpose |
|--------|---------|
| `dev_start.sh` | Start dev environment (tunnel + server) |
| `setup_dev_tunnel.sh` | Setup SSH tunnel to Wazuh Indexer |
| `stop_dev_tunnel.sh` | Stop SSH tunnel and cleanup |
| `run_tests.sh` | Run comprehensive test suite |

Make executable: `chmod +x scripts/*.sh`

---

## 🚀 Production Deployment

### Recommended Architecture

Deploy MCP server on the same VM as Wazuh:

```
┌──────────────────────────────────────┐
│         VM (Wazuh Server)            │
│                                      │
│  MCP Server :8000 (public)          │
│       ↓                              │
│  Wazuh API :55000 (localhost)       │
│  Wazuh Indexer :9200 (localhost)    │
└──────────────────────────────────────┘
         ↑
    Operators
```

### Security Checklist

- [ ] Use proper SSL certificates (not self-signed)
- [ ] Enable API authentication
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable comprehensive logging
- [ ] Use firewall rules
- [ ] Rotate credentials regularly
- [ ] Monitor server health

---

## 🐛 Troubleshooting

### Connection Issues

**Wazuh Indexer not accessible:**
```bash
# Check if SSH tunnel is running
lsof -ti:9200

# Test connection
curl -k -u admin:password https://localhost:9200/_cluster/health
```

**Wazuh API authentication fails:**
```bash
# Check credentials in .env
# Test direct connection
curl -k -u wazuh:password https://wazuh-server:55000/
```

---

## 📊 Performance Metrics

| Operation | Avg Time | Notes |
|-----------|----------|-------|
| Simple NL | ~2s | Includes GPT-4o processing |
| Advanced NL | ~3s | Full pipeline |
| Pre-built DSL | <1s | Direct indexer access |
| Aggregation | ~2s | Depends on data volume |

---

## 🔧 Tech Stack

- **FastAPI** - Async web framework
- **httpx** - Async HTTP client
- **OpenAI GPT-4o** - Natural language processing
- **OpenSearch Python** - Indexer client
- **Pydantic v2** - Data validation

---

**Built for SOC operators** 🛡️
