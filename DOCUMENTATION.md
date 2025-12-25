# Wazuh MCP Server - Complete Documentation

> **Natural Language Security Operations Platform**  
> Powered by GPT-4o, FastAPI, and Wazuh SIEM

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Query Methods](#query-methods)
5. [API Endpoints](#api-endpoints)
6. [GPT Summarization](#gpt-summarization)
7. [Frontend Interface](#frontend-interface)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [Security](#security)
11. [Troubleshooting](#troubleshooting)
12. [Development](#development)

---

## Overview

### What is This?

A Model Context Protocol (MCP) server that bridges natural language queries with Wazuh SIEM data. Analysts can ask questions in plain English and get intelligent, formatted security insights powered by GPT-4o.

### Key Features

- ✅ **Natural Language Queries** - Ask questions in plain English
- ✅ **Intelligent Routing** - AI automatically chooses optimal pipeline
- ✅ **GPT-4o Summaries** - AI-generated security insights
- ✅ **Hybrid NL+DSL** - Combine context with direct queries
- ✅ **Modern Web UI** - Beautiful, responsive interface
- ✅ **Three Query Modes** - Simple, Advanced, Direct DSL
- ✅ **Markdown Formatting** - Rich, formatted responses
- ✅ **SSH Tunnel Support** - Secure remote Wazuh access

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python 3.13) |
| **AI Engine** | GPT-4o-2024-11-20 |
| **SIEM** | Wazuh 4.x |
| **Indexer** | OpenSearch |
| **Frontend** | Vanilla JS, HTML5, CSS3 |
| **Protocol** | Model Context Protocol (MCP) |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Wazuh deployment (single-node or multi-node)
- OpenAI API key
- Access to Wazuh API and Indexer

### Docker Deployment (Recommended)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd mcp_server_wazuh_2025

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your Wazuh credentials and OpenAI API key

# 3. Deploy with Docker
./scripts/docker-deploy.sh

# 4. Access the application
# Frontend: https://localhost:8443
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

### Environment Configuration

```bash
# .env file

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here

# Wazuh Manager API
WAZUH_API_HOST=https://your-wazuh-server
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=admin
WAZUH_API_PASSWORD=your-password

# Wazuh Indexer (OpenSearch)
WAZUH_INDEXER_HOST=wazuh.indexer
WAZUH_INDEXER_PORT=9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=your-indexer-password

# OpenSearch (legacy - same as indexer)
OPENSEARCH_HOST=https://wazuh.indexer:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-indexer-password

# Docker Network (for multi-Wazuh environments)
WAZUH_NETWORK=multi-node_default
```

### Docker Management

```bash
# Deploy/Start containers
./scripts/docker-deploy.sh

# View logs
./scripts/docker-logs.sh

# Stop containers
./scripts/docker-stop.sh

# Rebuild and restart
./scripts/docker-rebuild.sh
```

### Development Setup (Alternative)

For local development without Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

- **Frontend**: https://localhost:8443 (HTTPS with auto-generated SSL)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser (HTTPS)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Frontend Container (Nginx - Port 8443)            │
│  • Natural Language Input                                    │
│  • DSL Query Editor                                          │
│  • Markdown Rendering                                        │
│  • Auto-generated SSL/TLS                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Backend Container (FastAPI - Port 8000)           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │        Query Router (GPT-4o Intelligence)           │    │
│  │  • Detects embedded DSL                             │    │
│  │  • Routes to appropriate pipeline                   │    │
│  │  • Extracts NL context                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│         ┌────────────────────┼────────────────────┐          │
│         ▼                    ▼                    ▼          │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐      │
│  │  Simple  │        │ Advanced │        │  Direct  │      │
│  │ Pipeline │        │ Pipeline │        │   DSL    │      │
│  │(Wazuh API)│       │(Indexer) │        │(Indexer) │      │
│  └──────────┘        └──────────┘        └──────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                      │                    │
         ▼                      ▼                    ▼
┌─────────────┐        ┌─────────────────────────────────┐
│  Wazuh API  │        │   Wazuh Indexer (OpenSearch)    │
│ (Port 55000)│        │   External Docker Network       │
└─────────────┘        └─────────────────────────────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        ▼
              ┌──────────────────┐
              │  Wazuh Deployment │
              │  (Manager + Indexer)│
              └──────────────────┘
```

### Query Flow

```
1. User enters query → Frontend
2. Frontend sends to FastAPI
3. GPT-4o analyzes query intent
4. Router selects pipeline:
   • Simple → Wazuh Manager API
   • Advanced → Parse to DSL → Indexer
   • Direct DSL → Validate → Indexer
   • Hybrid → Extract DSL + NL context → Indexer
5. Execute query
6. GPT-4o formats results
7. Return to frontend with markdown
8. Frontend renders formatted response
```

---

## Query Methods

### 1. Natural Language Queries

Ask questions in plain English. AI automatically routes to the best pipeline.

**Endpoint**: `POST /query/nl`

**Examples**:

```json
// Simple query (Wazuh API)
{"query": "Show me all agents"}

// Advanced query (Indexer + DSL)
{"query": "Show me critical alerts from the last 24 hours"}

// Hybrid query (NL context + embedded DSL)
{
  "query": "Analyze this for security issues: {\"index\":\"wazuh-alerts-*\",\"query\":{\"match_all\":{}}}"
}
```

**Response**:
```json
{
  "success": true,
  "pipeline": "ADVANCED_PIPELINE",
  "summary": "**Summary:** Found 47 alerts...",
  "total_hits": 47,
  "raw_data": {...},
  "dsl": {...},
  "routing": {
    "pipeline": "ADVANCED_PIPELINE",
    "confidence": 0.95,
    "reasoning": "Complex query requires time-based filtering"
  }
}
```

### 2. Direct DSL Queries

For advanced users who know OpenSearch DSL syntax.

**Endpoint**: `POST /query/dsl`

**Example**:

```json
{
  "index": "wazuh-alerts-*",
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "timestamp": {
              "gte": "now-1h"
            }
          }
        },
        {
          "term": {
            "rule.level": 12
          }
        }
      ]
    }
  },
  "size": 50,
  "sort": [{"timestamp": {"order": "desc"}}],
  "include_summary": true
}
```

**Response**:
```json
{
  "success": true,
  "pipeline": "DIRECT_DSL",
  "total_hits": 23,
  "query_time": "0.15s",
  "format_time": "1.23s",
  "summary": "**Summary:** Found 23 critical alerts...",
  "raw_results": {...},
  "dsl": {...}
}
```

### 3. MCP Protocol

For programmatic access via Model Context Protocol.

**Endpoint**: `POST /mcp/wazuh.search`

**Payload**: WazuhSearchPlan schema

```json
{
  "indices": "wazuh-alerts-*",
  "filters": [
    {
      "field": "rule.level",
      "operator": "gte",
      "value": 8
    }
  ],
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "limit": 100,
  "dry_run": false
}
```

---

## API Endpoints

### Query Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/query/nl` | POST | Natural language query with intelligent routing | No |
| `/query/dsl` | POST | Direct DSL query with optional GPT summary | No |
| `/query/simple` | POST | Simple NL query via Wazuh API only | No |
| `/mcp/wazuh.search` | POST | MCP protocol query | No |

### Management Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Server info and status |
| `/health` | GET | Health check |
| `/agents` | GET | List all Wazuh agents |
| `/test` | GET | Test Wazuh connection |

### Request/Response Examples

#### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "wazuh_authenticated": true,
  "mcp_enabled": true
}
```

#### Natural Language Query

```bash
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me failed SSH logins from the last hour"}'
```

#### Direct DSL Query

```bash
curl -X POST http://localhost:8000/query/dsl \
  -H "Content-Type: application/json" \
  -d '{
    "index": "wazuh-alerts-*",
    "query": {"match_all": {}},
    "size": 10,
    "include_summary": true
  }'
```

---

## GPT Summarization

### How It Works

Every query automatically gets GPT-4o analysis for natural language insights.

### Smart Sampling

To avoid OpenAI token limits, the system intelligently samples data:

- **Indexer Results**: First 10 documents + total count + aggregations
- **Manager API**: First 10 items + total count
- **Large Datasets**: Automatic truncation while preserving metrics

### Configuration

```python
# In app/llm_client.py
model = "gpt-4o-2024-11-20"
temperature = 0.3
max_tokens = 500
timeout = 60.0
```

### Example Output

**Query**: "Show me failed SSH logins"

**GPT Summary**:
```markdown
**Summary:** Found 47 failed SSH login attempts in the last hour from 12 unique IP addresses.

**Key Findings:**
- 23 attempts from 192.168.1.100 (most active)
- 8 attempts targeting root user
- Geographic distribution: Russia (15), China (12), USA (8)

**Security Concerns:** Multiple brute-force attempts detected. Recommend IP blocking for repeat offenders.
```

### Disabling Summary

For faster responses without AI analysis:

```json
{
  "index": "wazuh-alerts-*",
  "query": {...},
  "include_summary": false
}
```

### Token Optimization

- **Input**: ~2,000 tokens (sampled data)
- **Output**: ~500 tokens (summary)
- **Total**: ~2,500 tokens per query
- **Capacity**: ~12 queries/minute within OpenAI limits

---

## Frontend Interface

### Features

- 🎨 **Modern Dark Theme** - Easy on the eyes for SOC analysts
- 📱 **Responsive Design** - Works on desktop and mobile
- 🔍 **Three Query Modes** - NL, DSL, Hybrid
- 📊 **Tabbed Results** - Summary, Formatted, Raw JSON, DSL
- 🎯 **Smart Routing Display** - Shows which pipeline was used
- ✨ **Markdown Rendering** - Rich formatted GPT responses
- 🚀 **Real-time Status** - Server connection indicator
- 💡 **Example Queries** - Quick-start templates

### Query Interface

**Natural Language Tab**:
- Text area for free-form questions
- Example query chips for common use cases
- Supports both pure NL and hybrid NL+DSL

**Direct DSL Tab**:
- JSON editor for manual DSL construction
- Template loader for common patterns
- Syntax validation

### Results Display

**Four Tabs**:

1. **Summary** - GPT-generated natural language insights
2. **Formatted** - Structured table view of results
3. **Raw JSON** - Complete API response
4. **DSL Query** - Generated/executed DSL query

**Routing Info**:
- Pipeline used (Simple/Advanced/Direct/Hybrid)
- Confidence score with color coding
- Reasoning for routing decision
- Query execution metrics

### Accessing Frontend

**Docker Deployment** (Recommended):
```bash
# Frontend served via Nginx with HTTPS
https://localhost:8443

# SSL certificates auto-generated in ssl/ directory
# Accept the self-signed certificate warning in browser
```

**Development** (Alternative):
```bash
# Option 1: Open directly
open frontend/index.html

# Option 2: Serve with Python
cd frontend
python -m http.server 8080
# Visit http://localhost:8080
```

---

## Testing

### Test Structure

```
tests/
├── test_queries.py           # General NL query tests (11/12 passing)
├── test_mcp_cases.py          # MCP functionality tests (5/5 passing)
├── test_advanced_dsl.py       # Advanced DSL tests (5/5 passing)
├── test_query_filters.py      # Filter validation tests
├── diagnose_timeout.py        # Performance diagnostics
├── test_queries.sh            # Shell script wrapper
└── README.md                  # Test documentation
```

### Running Tests

```bash
# Run all tests
./tests/test_queries.py

# Run specific test suite
./tests/test_mcp_cases.py
./tests/test_advanced_dsl.py

# Run with shell script
./tests/test_queries.sh

# Diagnose performance issues
./tests/diagnose_timeout.py
```

### Test Cases

#### Natural Language Tests

```python
# Test cases include:
- "Show me all agents"
- "Show me critical alerts from today"
- "SSH login failures from last hour"
- "Show me brute force attempts"
- "List file modifications from the last 24 hours"
```

#### DSL Test Cases

```python
# Advanced security analytics:
- Failed authentication attempts
- Malware detection events
- File Integrity Monitoring (FIM)
- Vulnerability detection
- Agent health monitoring
```

#### MCP Test Cases

```python
# Basic MCP functionality:
- Health check
- Agent listing
- Alert queries with filters
- Time-based queries
- Field filtering
```

### Example Test Execution

```bash
$ ./tests/test_mcp_cases.py

========================================
Wazuh MCP Test Cases
========================================

Test 1: Health Check
✓ PASSED - Server healthy

Test 2: List All Agents
✓ PASSED - Found 8 agents

Test 3: Critical Alerts (Last 24h)
✓ PASSED - Found 23 alerts

Test 4: Failed Logins
✓ PASSED - Found 12 events

Test 5: File Modifications
✓ PASSED - Found 45 changes

========================================
Results: 5/5 tests passed (100%)
========================================
```

---

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxx              # Required: OpenAI API key

# Wazuh Manager API
WAZUH_API_HOST=https://10.21.232.103    # Wazuh Manager URL
WAZUH_API_PORT=55000                     # Wazuh Manager port
WAZUH_API_USERNAME=admin                 # API username
WAZUH_API_PASSWORD=SecurePass123         # API password

# Wazuh Indexer (OpenSearch)
OPENSEARCH_HOST=https://localhost:9200   # Indexer URL (via tunnel)
OPENSEARCH_USER=admin                    # Indexer username
OPENSEARCH_PASS=IndexerPass456           # Indexer password

# Optional: Development Settings
DEBUG=false                              # Enable debug logging
LOG_LEVEL=INFO                           # Logging level
```

### Docker Network Configuration

Edit `.env` to match your Wazuh deployment:

```bash
# Find your Wazuh network name
docker network ls | grep wazuh

# Set in .env
WAZUH_NETWORK=multi-node_default  # or wazuh-docker_default, etc.
```

### Index Patterns

Default allowed indices (configured in `app/validators.py`):

```python
ALLOWED_INDICES = [
    "wazuh-alerts-*",
    "wazuh-archives-*",
    "wazuh-monitoring-*"
]
```

### Time Window Limits

Maximum query time windows (security feature):

```python
MAX_TIME_WINDOW_DAYS = 90  # Maximum 90 days
```

---

## Security

### Security Features

✅ **Index Allowlist** - Only whitelisted indices accessible  
✅ **Time Window Limits** - Prevents excessive data queries  
✅ **Filter Validation** - Validates all query filters  
✅ **SSH Tunnel Support** - Secure remote connections  
✅ **Environment Variables** - No hardcoded credentials  
✅ **HTTPS Support** - TLS for API connections  

### Security Checklist

- [ ] Change default Wazuh API password
- [ ] Use strong OpenSearch credentials
- [ ] Rotate OpenAI API key regularly
- [ ] Enable SSH key authentication
- [ ] Restrict CORS origins in production
- [ ] Use HTTPS for all connections
- [ ] Monitor API usage and logs
- [ ] Implement rate limiting
- [ ] Regular security audits
- [ ] Keep dependencies updated

### Production Hardening

```python
# app/main.py - Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specific domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Access Control

Currently no authentication is implemented. For production:

1. Add JWT authentication
2. Implement role-based access control (RBAC)
3. Add API rate limiting
4. Enable request logging
5. Implement audit trails

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused to Wazuh Indexer

**Problem**: `ConnectionError: Failed to establish connection to Wazuh Indexer`

**Solution**:
```bash
# Check Docker network configuration
docker network ls | grep wazuh

# Verify WAZUH_NETWORK in .env matches your Wazuh deployment
cat .env | grep WAZUH_NETWORK

# Check backend logs
./scripts/docker-logs.sh backend

# Test connection from backend container
docker-compose exec backend curl -k -u admin:password https://wazuh.indexer:9200/_cluster/health
```

#### 2. OpenAI Rate Limit

**Problem**: `Error code: 429 - Rate limit exceeded`

**Solution**:
- Wait 60 seconds before retrying
- Reduce query frequency
- Set `include_summary: false` for some queries
- Check OpenAI dashboard for quota

#### 3. Wazuh Authentication Failed

**Problem**: `401 Unauthorized from Wazuh API`

**Solution**:
```bash
# Verify credentials in .env
cat .env | grep WAZUH

# Test authentication manually
curl -k -X POST https://10.21.232.103:55000/security/user/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

#### 4. GPT No Summary Returned

**Problem**: `summary: null` in response

**Solution**:
- Check OpenAI API key validity
- Verify internet connection
- Check logs for detailed error: `tail -f logs/app.log`
- System falls back to count-based summary automatically

#### 5. Frontend Not Loading

**Problem**: Blank page or connection errors

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings
# Open browser console for errors

# Try different browser or clear cache
```

### Debug Mode

Enable detailed logging:

```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart server
./scripts/dev_start.sh

# View logs
tail -f logs/app.log
```

### Performance Issues

```bash
# Run diagnostics
./tests/diagnose_timeout.py

# Check query execution time
# Look for slow queries in logs

# Optimize DSL queries
# Add proper indices
# Reduce result size
```

---

## Development

### Project Structure

```
mcp_server_wazuh_2025/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── llm_client.py        # OpenAI integration
│   ├── wazuh_client.py      # Wazuh API client
│   ├── es_client.py         # OpenSearch client
│   ├── dsl_builder.py       # DSL query builder
│   ├── validators.py        # Query validators
│   ├── schemas.py           # Pydantic schemas
│   └── utils.py             # Utilities
├── mcp/
│   ├── __init__.py
│   ├── handlers.py          # MCP handlers
│   ├── schemas.py           # MCP schemas
│   └── tools.json           # MCP tool definitions
├── frontend/
│   ├── index.html           # Main UI
│   ├── app.js               # Frontend logic
│   └── styles.css           # Styling
├── scripts/
│   ├── docker-deploy.sh     # Deploy containers
│   ├── docker-stop.sh       # Stop containers
│   ├── docker-logs.sh       # View logs
│   ├── docker-rebuild.sh    # Rebuild containers
│   └── archive/             # Old development scripts
├── tests/
│   ├── test_queries.py
│   ├── test_mcp_cases.py
│   └── test_advanced_dsl.py
├── docs/
│   └── (archived documentation)
├── .env                     # Environment config
├── requirements.txt         # Python dependencies
└── DOCUMENTATION.md         # This file
```

### Adding New Features

#### 1. Add New Query Filter

```python
# app/validators.py
def validate_custom_filter(filter_obj):
    # Add validation logic
    pass

# app/dsl_builder.py
def build_custom_filter(filter_obj):
    # Build DSL for new filter
    pass
```

#### 2. Add New Pipeline

```python
# app/main.py
@app.post("/query/custom")
async def custom_pipeline(data: dict):
    # Implement custom pipeline logic
    pass
```

#### 3. Extend Frontend

```javascript
// frontend/app.js
function addCustomFeature() {
    // Add new UI feature
}
```

### Code Style

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ES6+, async/await, clear naming
- **CSS**: BEM methodology, CSS custom properties

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-pipeline

# Make changes and test
./tests/test_queries.py

# Commit with clear message
git commit -m "feat: Add custom query pipeline"

# Push and create PR
git push origin feature/new-pipeline
```

### Dependencies

Key packages:

```txt
fastapi==0.115.6          # Web framework
uvicorn==0.34.0           # ASGI server
openai==1.58.1            # OpenAI API
httpx==0.28.1             # HTTP client
pydantic==2.10.4          # Data validation
opensearch-py==2.8.0      # OpenSearch client
```

---

## Quick Reference

### Common Commands

```bash
# Deploy/Start Docker containers
./scripts/docker-deploy.sh

# View logs
./scripts/docker-logs.sh
# Or specific container:
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop containers
./scripts/docker-stop.sh

# Rebuild after changes
./scripts/docker-rebuild.sh

# Check container status
docker-compose ps

# Run tests (inside container)
docker-compose exec backend python tests/test_queries.py
```

### Example DSL Queries

**Failed Authentication**:
```json
{
  "index": "wazuh-alerts-*",
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"match": {"rule.description": "authentication failed"}}
      ]
    }
  },
  "size": 50
}
```

**Critical Alerts**:
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
  },
  "size": 100
}
```

**Specific Agent**:
```json
{
  "index": "wazuh-alerts-*",
  "query": {
    "bool": {
      "must": [
        {"term": {"agent.id": "001"}}
      ]
    }
  },
  "size": 50
}
```

---

## Support & Contributing

### Getting Help

- **Issues**: Report bugs via GitHub Issues
- **Questions**: Use GitHub Discussions
- **Security**: Email security@example.com

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### License

MIT License - See LICENSE file for details

---

## Changelog

### Version 2.0 (Current)

- ✅ Unified NL query endpoint with intelligent routing
- ✅ Hybrid NL+DSL query support
- ✅ GPT-4o summarization with smart sampling
- ✅ Markdown rendering in frontend
- ✅ SSH tunnel support for remote Wazuh
- ✅ Enhanced error handling
- ✅ Improved test organization

### Version 1.0

- ✅ Basic NL to DSL conversion
- ✅ Direct DSL query support
- ✅ MCP protocol implementation
- ✅ Simple web interface

---

## Appendix

### Wazuh Indices

| Index Pattern | Description |
|---------------|-------------|
| `wazuh-alerts-*` | Security alerts from all agents |
| `wazuh-archives-*` | Archived events |
| `wazuh-monitoring-*` | Agent health monitoring |

### Common Rule Levels

| Level | Severity | Description |
|-------|----------|-------------|
| 0-3 | Informational | System events |
| 4-7 | Low/Medium | Warnings |
| 8-11 | High | Important alerts |
| 12-15 | Critical | Severe security events |

### OpenSearch DSL Operators

| Operator | DSL Equivalent | Example |
|----------|----------------|---------|
| `eq` | `term` | `{"term": {"field": "value"}}` |
| `gte` | `range.gte` | `{"range": {"field": {"gte": 8}}}` |
| `contains` | `match` | `{"match": {"field": "text"}}` |
| `in` | `terms` | `{"terms": {"field": ["a", "b"]}}` |

---

**Last Updated**: December 26, 2025  
**Version**: 2.0  
**Maintainer**: Wazuh MCP Team
