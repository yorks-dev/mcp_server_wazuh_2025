# Getting Started with Wazuh MCP Server

## Prerequisites

- Python 3.8+
- Access to Wazuh server (API and Indexer)
- OpenAI API key
- SSH access to Wazuh server (for dev mode)

---

## Installation

### 1. Clone and Setup

```bash
# Navigate to project
cd mcp_server_wazuh_2025

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required variables:**
```bash
# Wazuh API
WAZUH_API_HOST=https://10.21.236.157:55000
WAZUH_USERNAME=wazuh
WAZUH_PASSWORD=your-password

# Wazuh Indexer (for dev: use localhost with tunnel)
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-indexer-password

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here
```

---

## Quick Start (Development)

### Option 1: Automated Start (Recommended)

```bash
# This will:
# 1. Setup SSH tunnel to Wazuh Indexer
# 2. Start the server with auto-reload
./scripts/dev_start.sh
```

Server will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### Option 2: Manual Start

```bash
# 1. Setup SSH tunnel
./scripts/setup_dev_tunnel.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## First Test

### Health Check

```bash
# Check server is running
curl http://localhost:8000/

# Expected response:
# {
#   "message": "Welcome to the MCP Server for Wazuh...",
#   "authenticated": true,
#   "wazuh_url": "https://10.21.236.157:55000"
# }
```

### Connection Test

```bash
# Test Wazuh API connection
curl http://localhost:8000/test

# Expected response:
# {
#   "status": "connected",
#   "token_valid": true,
#   "agents_count": 4,
#   "sample_agents": [...]
# }
```

---

## Try the Three Pipelines

### 1. Simple Natural Language Query

```bash
curl -X POST http://localhost:8000/query/simple \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all active agents"
  }'
```

**What happens:**
- Your question → GPT-4o → Wazuh API → GPT-4o → Natural language answer
- Fast, no Indexer needed

### 2. Advanced Natural Language with DSL

```bash
curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show high severity alerts from last 24 hours"
  }'
```

**What happens:**
- Your question → GPT-4o parses → DSL built → Wazuh Indexer queries → GPT-4o formats → Natural language answer
- Complex searches, time ranges, aggregations

### 3. Pre-built DSL Query

```bash
curl -X POST http://localhost:8000/mcp/wazuh.search \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "wazuh-alerts-*",
    "time": {"from": "now-24h", "to": "now"},
    "filters": [
      {"field": "rule.level", "op": "gte", "value": 8}
    ],
    "limit": 10
  }'
```

**What happens:**
- Pre-built query → Validate → Wazuh Indexer → Raw JSON results
- Fastest, for automation

---

## Interactive API Documentation

Open in browser: `http://localhost:8000/docs`

Features:
- Try all endpoints interactively
- See request/response schemas
- Test authentication
- Copy curl commands

---

## Run Tests

```bash
# Comprehensive test suite
./scripts/run_tests.sh
```

This will:
1. Check dependencies
2. Verify configuration
3. Test all three pipelines
4. Show results

---

## Stop Development Environment

```bash
# Stop server (Ctrl+C in terminal where it's running)

# Stop SSH tunnel
./scripts/stop_dev_tunnel.sh
```

---

## Common Issues

### "Port 8000 already in use"

```bash
# Kill existing server
pkill -f "uvicorn app.main:app"

# Or find and kill process
lsof -ti:8000 | xargs kill
```

### "Connection refused to localhost:9200"

```bash
# Check if SSH tunnel is running
lsof -ti:9200

# If not, setup tunnel
./scripts/setup_dev_tunnel.sh

# Test connection
curl -k -u admin:password https://localhost:9200/_cluster/health
```

### "Authentication failed"

```bash
# Check .env file credentials
cat .env | grep WAZUH

# Test direct connection
curl -k -u wazuh:password https://your-wazuh-server:55000/
```

---

## Next Steps

1. **Read Complete Guide**: [docs/COMPLETE_PIPELINE_GUIDE.md](COMPLETE_PIPELINE_GUIDE.md)
2. **API Reference**: `http://localhost:8000/docs`
3. **Quick Commands**: [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

---

## Production Deployment

For production deployment, see [README.md](../README.md) "Production Deployment" section.

Key differences:
- Deploy server on Wazuh VM (no SSH tunnel needed)
- Use systemd for auto-start
- Configure nginx reverse proxy
- Enable proper SSL certificates
- Set up authentication
- Configure rate limiting

---

**You're ready to start querying Wazuh with natural language! 🚀**
