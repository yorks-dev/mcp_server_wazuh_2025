# 🛡️ Wazuh MCP Server

  > **Natural Language Security Operations Platform**  
  > Transform your Wazuh deployment into an AI-powered security assistant. Ask questions in plain English, get intelligent security insights powered by GPT-4o.

  [![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
  [![GPT-4o](https://img.shields.io/badge/GPT--4o-Powered-orange.svg)](https://openai.com/)
  [![Wazuh](https://img.shields.io/badge/Wazuh-4.x-blue.svg)](https://wazuh.com/)
  [![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

  ---

  ## 📚 Table of Contents

  - [Quick Start](#-quick-start)
  - [Features](#-features)
  - [Architecture](#-architecture)
  - [Deployment Options](#-deployment-options)
  - [Example Queries](#-example-queries)
  - [Documentation Index](#-documentation-index)
  - [Project Structure](#-project-structure)
  - [Contributing](#-contributing)
  - [License](#-license)

  ---

  ## 🚀 Quick Start

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


  ## ✨ Features

  ### 🤖 Natural Language Interface
  - **Ask questions in plain English**: "Show me critical alerts from the last hour"
  - **GPT-4o understanding**: AI comprehends security context and intent
  - **Conversational queries**: "What are the top 10 attacked hosts?"

  ### 🎯 Intelligent Query Routing
  - **Automatic pipeline selection**: AI chooses between Wazuh API or Indexer
  - **Simple queries** → Wazuh Manager API (faster, simpler)
  - **Complex queries** → Wazuh Indexer with DSL (powerful, flexible)
  - **Confidence scores**: See AI's reasoning and confidence level

  ### 🔬 Hybrid Query Modes
  1. **Pure Natural Language**: `"Show me failed login attempts"`
  2. **Direct DSL**: Full Elasticsearch query control
  3. **Hybrid NL+DSL**: Natural language context + DSL precision

  ### 📊 AI-Powered Insights
  - **GPT-4o summaries**: Intelligent analysis of query results
  - **Markdown formatting**: Rich text with headers, lists, code blocks
  - **Smart sampling**: Efficient processing of large result sets
  - **Security context**: AI understands security implications

  ### 🎨 Modern Web Interface
  - **Beautiful UI**: Clean, responsive design
  - **Real-time results**: Instant query execution
  - **Markdown rendering**: Formatted summaries with syntax highlighting
  - **Query history**: Track your investigations
  - **Dark mode ready**: Eye-friendly interface


  ### 🐳 Production Ready
  - **Docker Compose setup**: One-command deployment
  - **Scalable**: Works with single-node or multi-node Wazuh

  ---

  ## 🏗️ Architecture

  ```
  ┌─────────────────────────────────────────────────────────────┐
  │                    User Interface                           │
  │  ┌──────────────────────────────────────────────────────┐   │
  │  │  Web Frontend (HTTPS on port 8443)                   │   │
  │  │  • Natural language input                            │   │
  │  │  • Real-time results display                         │   │
  │  │  • Markdown-rendered summaries                       │   │
  │  └──────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────┘
                              ↓ API Request
  ┌─────────────────────────────────────────────────────────────┐
  │              FastAPI Backend (Port 8000)                    │
  │  ┌──────────────────────────────────────────────────────┐   │
  │  │  GPT-4o Query Router                                 │   │
  │  │  • Analyzes user query                               │   │
  │  │  • Classifies complexity                             │   │
  │  │  • Chooses optimal pipeline                          │   │
  │  └──────────────────────────────────────────────────────┘   │
  │           ↓                              ↓                  │
  │  ┌──────────────────┐         ┌──────────────────────┐     │
  │  │ SIMPLE_PIPELINE  │         │ ADVANCED_PIPELINE    │     │
  │  │ • Agent info     │         │ • Complex queries    │     │
  │  │ • Basic alerts   │         │ • DSL support        │     │
  │  │ • Quick lookups  │         │ • Aggregations       │     │
  │  └──────────────────┘         └──────────────────────┘     │
  │           ↓                              ↓                  │
  └─────────────────────────────────────────────────────────────┘
                ↓                              ↓
  ┌───────────────────────┐      ┌──────────────────────────┐
  │  Wazuh Manager API    │      │  Wazuh Indexer           │
  │  (Port 55000)         │      │  (OpenSearch - Port 9200)│
  │  • Agents             │      │  • wazuh-alerts-*        │
  │  • Rules              │      │  • wazuh-archives-*      │
  │  • Security info      │      │  • Complex searches      │
  └───────────────────────┘      └──────────────────────────┘
  ```

  ### Query Flow

  1. **User Input** → Natural language query via web interface
  2. **GPT-4o Analysis** → AI determines query complexity and intent
  3. **Pipeline Selection**:
    - **SIMPLE**: Wazuh API for straightforward queries
    - **ADVANCED**: Indexer/DSL for complex analytics
  4. **Execution** → Query runs against appropriate backend
  5. **GPT-4o Summarization** → AI analyzes and formats results
  6. **Markdown Rendering** → Rich display in web interface

  ---

  ## 🚀 Deployment Options

  ### 1. Docker Deployment (Recommended)

  **Best for**: Production, same-host Wazuh installations

  ```bash
  # Quick deploy
  ./scripts/docker-deploy.sh

  # Custom network
  WAZUH_NETWORK=my-wazuh-network docker-compose up -d
  ```

  **Features**:
  - ✅ HTTPS with auto-generated SSL certificates
  - ✅ Works with any Wazuh Docker setup
  - ✅ Health checks and auto-restart
  - ✅ Isolated network security
  - ✅ No SSH tunnels needed

  📖 **Documentation**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md), [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### 2. Multi-Wazuh Environments

  ```bash
  # Configure for each environment
  cp .env.prod .env
  WAZUH_NETWORK=prod-wazuh_default docker-compose up -d
  ```

  📖 **Documentation**: [DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md#scenario-3-multiple-wazuh-environments)

  ---

  ## 💬 Example Queries

  ### Natural Language Queries

  ```bash
  # Security operations
  "Show me all critical alerts from the last 24 hours"
  "Which agents have failed logins in the last hour?"
  "List top 10 most triggered rules today"

  # Investigation
  "What are the most attacked hosts?"
  "Show me Windows authentication failures"
  "Find all alerts related to brute force attacks"

  # Analysis
  "Summarize security events from agent web-server-01"
  "What vulnerabilities were detected this week?"
  "Show me network connection attempts on port 22"
  ```

  ### API Examples

  **Natural Language**:
  ```bash
  curl -X POST http://localhost:8000/query/nl \
    -H "Content-Type: application/json" \
    -d '{
      "query": "Show me critical alerts from the last hour",
      "use_gpt_summary": true
    }'
  ```

  **Direct DSL**:
  ```bash
  curl -X POST http://localhost:8000/query/dsl \
    -H "Content-Type: application/json" \
    -d '{
      "index": "wazuh-alerts-*",
      "query": {
        "bool": {
          "must": [
            {"range": {"rule.level": {"gte": 12}}},
            {"range": {"@timestamp": {"gte": "now-1h"}}}
          ]
        }
      },
      "size": 50
    }'
  ```

  **Hybrid NL+DSL**:
  ```bash
  curl -X POST http://localhost:8000/query/nl \
    -H "Content-Type: application/json" \
    -d '{
      "query": "Analyze these alerts: {\"index\":\"wazuh-alerts-*\",\"query\":{\"match\":{\"rule.id\":\"5710\"}}}",
      "use_gpt_summary": true
    }'
  ```

  ---

  ## 📖 Documentation Index

  ### Getting Started
  - **[README.md](README.md)** *(this file)* - Project overview and quick start
  - **[QUICK_START.md](QUICK_START.md)** - One-page command reference
  - **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step deployment guide

  ### Deployment & Configuration
  - **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Complete Docker setup guide
  - **[DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md)** - Network configuration for multi-Wazuh setups
  - **[.env.example](.env.example)** - Configuration template with comments
  - **[.env.sample](.env.sample)** - Comprehensive configuration reference

  ### Technical Documentation
  - **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete API reference and architecture
  - **[SECURITY_NOTES.md](SECURITY_NOTES.md)** - Security best practices
  - **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
  - **[tests/README.md](tests/README.md)** - Testing guide

  ### Quick References
  - **[DOCKER_QUICK_REF.txt](DOCKER_QUICK_REF.txt)** - Docker commands cheat sheet
  - **[PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt)** - ASCII art project summary

  ### Scripts
  - **[scripts/docker-deploy.sh](scripts/docker-deploy.sh)** - Automated Docker deployment
  - **[scripts/docker-stop.sh](scripts/docker-stop.sh)** - Stop all containers
  - **[scripts/docker-logs.sh](scripts/docker-logs.sh)** - View container logs
  - **[scripts/docker-rebuild.sh](scripts/docker-rebuild.sh)** - Rebuild and restart

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

Edit `.env` in the root directory:

```bash
# Docker Network (match your Wazuh deployment)
WAZUH_NETWORK=multi-node_default

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Wazuh Manager API (use Docker service names)
WAZUH_API_HOST=https://wazuh.manager
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=admin
WAZUH_API_PASSWORD=your-password

# Wazuh Indexer (use Docker service names)
WAZUH_INDEXER_HOST=https://wazuh.indexer
WAZUH_INDEXER_PORT=9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=your-indexer-password

# OpenSearch (same as indexer)
OPENSEARCH_HOST=https://wazuh.indexer:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-indexer-password
```

**Note**: Use Docker service names (e.g., `wazuh.manager`, `wazuh.indexer`) instead of localhost or IP addresses. Find your network name with `docker network ls`.


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
  **Last Updated**: December 26, 2025  
  **Maintainer**: Wazuh MCP Team
