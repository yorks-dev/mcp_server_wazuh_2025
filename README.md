# Wazuh MCP Server

> **Natural Language Security Operations Platform**  
> Ask questions in plain English, get intelligent security insights powered by GPT-4o

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![GPT-4o](https://img.shields.io/badge/GPT--4o-Powered-orange.svg)](https://openai.com/)
[![Wazuh](https://img.shields.io/badge/Wazuh-4.x-blue.svg)](https://wazuh.com/)

---

## 🚀 Quick Start

```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure (edit .env with your credentials)
cp .env.example .env

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Setup SSH tunnel for remote Wazuh (if needed)
./scripts/setup_dev_tunnel.sh
```

**Access**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: Open `frontend/index.html`

---

## ✨ Features

- 🤖 **Natural Language Queries** - Ask questions in plain English
- 🎯 **Intelligent Routing** - AI chooses optimal pipeline automatically
- 🔬 **Hybrid NL+DSL** - Combine natural language context with direct queries
- 📊 **GPT-4o Summaries** - AI-generated security insights with markdown formatting
- 🎨 **Modern Web UI** - Beautiful, responsive interface
- 🔒 **Secure** - SSH tunnel support, index allowlist, time limits

---

## 📖 Documentation

**[→ Read Complete Documentation (DOCUMENTATION.md)](DOCUMENTATION.md)**

The complete documentation includes:
- Detailed architecture diagrams
- All API endpoints with examples
- Query method comparisons
- GPT summarization guide
- Frontend features
- Testing guide
- Configuration options
- Security checklist
- Troubleshooting
- Development guide

---

## 🎯 Example Queries

**Natural Language**:
```bash
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me critical alerts from the last hour"}'
```

**Direct DSL**:
```bash
curl -X POST http://localhost:8000/query/dsl \
  -H "Content-Type: application/json" \
  -d '{
    "index": "wazuh-alerts-*",
    "query": {"bool": {"must": [{"range": {"rule.level": {"gte": 12}}}]}},
    "size": 50
  }'
```

**Hybrid NL+DSL**:
```bash
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze security issues: {\"index\":\"wazuh-alerts-*\",\"query\":{\"match_all\":{}}}"}'
```

---

## 🏗️ Architecture

```
User Query → Frontend → FastAPI → GPT-4o Router
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              Simple Pipeline   Advanced Pipeline   Direct DSL
              (Wazuh API)       (Parse→DSL)        (Execute DSL)
                    │                 │                 │
                    └────────┬────────┴─────────────────┘
                             ▼
                      Wazuh Manager + Indexer
                             │
                             ▼
                      GPT-4o Summary → Frontend
```

---

## 🧪 Testing

```bash
# Run all tests
./tests/test_queries.py

# Run specific test suite
./tests/test_mcp_cases.py      # 5/5 passing
./tests/test_advanced_dsl.py   # 5/5 passing

# Performance diagnostics
./tests/diagnose_timeout.py
```

---

## 🔧 Configuration

Edit `.env`:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
WAZUH_API_HOST=https://your-wazuh-server
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=admin
WAZUH_API_PASSWORD=your-password
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-indexer-password
```

For remote Wazuh, configure SSH tunnel in `scripts/setup_dev_tunnel.sh`:

```bash
VM_IP="10.21.232.103"
VM_USER="waserver"
```

---

## 🛡️ Security

- ✅ Index allowlist validation
- ✅ Time window limits (max 90 days)
- ✅ Filter validation
- ✅ SSH tunnel support
- ✅ No hardcoded credentials
- ✅ HTTPS support

**⚠️ Production Checklist**: See [DOCUMENTATION.md](DOCUMENTATION.md#security) for hardening guide.

---

## 📁 Project Structure

```
mcp_server_wazuh_2025/
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Main application
│   ├── llm_client.py      # GPT-4o integration
│   └── ...
├── frontend/              # Web UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── mcp/                   # MCP protocol handlers
├── scripts/               # Utility scripts
├── tests/                 # Test suites
├── .env                   # Configuration
├── requirements.txt       # Dependencies
├── DOCUMENTATION.md       # Complete docs (read this!)
└── README.md             # This file
```

---

## 🚨 Troubleshooting

**Connection refused on port 9200?**
```bash
./scripts/setup_dev_tunnel.sh
```

**OpenAI rate limit?**
- Wait 60 seconds or set `include_summary: false`

**Wazuh auth failed?**
- Check credentials in `.env`

**Frontend blank?**
- Check `curl http://localhost:8000/health`
- Check browser console for errors

See [DOCUMENTATION.md#troubleshooting](DOCUMENTATION.md#troubleshooting) for detailed solutions.

---

## 📊 Status

- **Backend**: ✅ Running on port 8000
- **Frontend**: ✅ Open `frontend/index.html`
- **Tests**: ✅ 21/22 passing (95%)
- **Documentation**: ✅ Consolidated in DOCUMENTATION.md

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Make changes and add tests
4. Commit (`git commit -m 'feat: Add amazing feature'`)
5. Push and create Pull Request

---

## 📜 License

MIT License - See LICENSE file for details

---

## 📚 Resources

- **Complete Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **API Docs**: http://localhost:8000/docs
- **Wazuh Docs**: https://documentation.wazuh.com/
- **OpenAI API**: https://platform.openai.com/docs

---

**Version**: 2.0  
**Last Updated**: December 25, 2025  
**Maintainer**: Wazuh MCP Team
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
