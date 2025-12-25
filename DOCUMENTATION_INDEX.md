# 📚 Documentation Index

## Overview

This document provides a comprehensive index of all documentation for the Wazuh MCP Server project. Use this as your navigation guide to find the information you need quickly.

---

## 📖 Core Documentation

### 🚀 Getting Started (5 minutes)

| Document | Purpose | Target Audience |
|----------|---------|----------------|
| **[README.md](README.md)** | Project overview, quick start, features | Everyone (start here!) |
| **[QUICK_START.md](QUICK_START.md)** | One-page command reference | Returning users |
| **[PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt)** | ASCII art summary | Quick visual overview |

### 🐳 Deployment (15-30 minutes)

| Document | Purpose | Complexity |
|----------|---------|------------|
| **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** | Complete Docker setup guide | ⭐⭐ Intermediate |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Step-by-step deployment for any Wazuh setup | ⭐⭐⭐ Advanced |
| **[DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md)** | Network configuration & troubleshooting | ⭐⭐⭐ Advanced |
| **[DOCKER_QUICK_REF.txt](DOCKER_QUICK_REF.txt)** | Quick Docker commands cheat sheet | ⭐ Beginner |

### 🔧 Configuration (10 minutes)

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[.env.example](.env.example)** | Basic configuration template | First-time setup |
| **[.env.sample](.env.sample)** | Comprehensive configuration reference | Advanced configuration |
| **[docker/.env.example](docker/.env.example)** | Docker-specific config template | Docker deployment only |

### 📘 Technical Reference (As needed)

| Document | Purpose | Lines | Best For |
|----------|---------|-------|----------|
| **[DOCUMENTATION.md](DOCUMENTATION.md)** | Complete API reference & architecture | 1,068 | API integration, architecture deep-dive |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Contribution guidelines & standards | 716 | Contributors & developers |
| **[SECURITY_NOTES.md](SECURITY_NOTES.md)** | Security best practices | 223 | Security review, production deployment |

### 🧪 Testing (20 minutes)

| Document | Purpose | Required Knowledge |
|----------|---------|-------------------|
| **[tests/README.md](tests/README.md)** | Testing guide & test suites | Python, pytest basics |
| **[tests/test_queries.py](tests/test_queries.py)** | Query test cases | Python development |
| **[tests/test_advanced_dsl.py](tests/test_advanced_dsl.py)** | DSL test cases | Elasticsearch DSL |
| **[tests/test_mcp_cases.py](tests/test_mcp_cases.py)** | MCP integration tests | MCP protocol |

---

## 🗂️ Documentation by Use Case

### "I want to deploy Wazuh MCP Server"

**Follow this path:**

1. **[README.md](README.md#quick-start)** - Get overview (5 min)
2. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step guide (15 min)
3. **[.env.example](.env.example)** - Configure environment (10 min)
4. **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Deploy with Docker (15 min)
5. **[DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md#verification)** - Verify deployment (5 min)

**Total time: ~50 minutes**

### "I'm a developer contributing to the project"

**Follow this path:**

1. **[README.md](README.md#development-setup)** - Get started (10 min)
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Understand standards (30 min)
3. **[DOCUMENTATION.md](DOCUMENTATION.md#architecture)** - Learn architecture (20 min)
4. **[tests/README.md](tests/README.md)** - Set up testing (15 min)
5. **[SECURITY_NOTES.md](SECURITY_NOTES.md)** - Security guidelines (10 min)

**Total time: ~1.5 hours**

### "I need to troubleshoot an issue"

**Follow this path:**

1. **[DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md#troubleshooting)** - Network issues
2. **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md#troubleshooting)** - Deployment issues
3. **[README.md](README.md#troubleshooting)** - Common problems
4. **[DOCUMENTATION.md](DOCUMENTATION.md#troubleshooting)** - API/Backend issues
5. Check logs: `docker-compose logs -f`

### "I want to understand the architecture"

**Follow this path:**

1. **[README.md](README.md#architecture)** - High-level overview (5 min)
2. **[DOCUMENTATION.md](DOCUMENTATION.md#architecture)** - Detailed architecture (20 min)
3. **[DOCUMENTATION.md](DOCUMENTATION.md#query-flow)** - Understand query flow (10 min)
4. **[DOCUMENTATION.md](DOCUMENTATION.md#api-endpoints)** - API structure (15 min)

**Total time: ~50 minutes**

### "I need to secure my deployment"

**Follow this path:**

1. **[SECURITY_NOTES.md](SECURITY_NOTES.md)** - Complete security guide (15 min)
2. **[.env.example](.env.example)** - Review sensitive variables (5 min)
3. **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md#ssl-certificates)** - SSL setup (10 min)
4. **[DOCUMENTATION.md](DOCUMENTATION.md#security-features)** - Security features (10 min)

**Total time: ~40 minutes**

---

## 📊 Documentation Statistics

```
Total Documentation:    3,745 lines across 8 main files
Average read time:      ~2.5 hours for complete coverage
Quick start:            5 minutes (README.md)
Full deployment:        50 minutes (deployment guides)
Developer onboarding:   1.5 hours (technical docs)
```

### By Category

| Category | Files | Lines | Read Time |
|----------|-------|-------|-----------|
| Getting Started | 3 | 651 | ~20 min |
| Deployment | 4 | 1,087 | ~45 min |
| Technical Reference | 2 | 1,784 | ~1 hour |
| Security & Testing | 2 | 223 | ~15 min |

### By Complexity

| Level | Documents | Best For |
|-------|-----------|----------|
| ⭐ Beginner | README.md, QUICK_START.md, .env.example | New users |
| ⭐⭐ Intermediate | DOCKER_DEPLOYMENT.md, DOCUMENTATION.md | Regular users |
| ⭐⭐⭐ Advanced | DEPLOYMENT_CHECKLIST.md, DOCKER_NETWORK_GUIDE.md, CONTRIBUTING.md | Power users, contributors |

---

## 🔍 Quick Find

### Looking for specific information?

| I want to... | Go to... |
|--------------|----------|
| **Deploy quickly** | [README.md#quick-start](README.md#quick-start) |
| **Configure environment** | [.env.example](.env.example) or [.env.sample](.env.sample) |
| **Understand Docker networking** | [DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md) |
| **Fix deployment issues** | [DOCKER_NETWORK_GUIDE.md#troubleshooting](DOCKER_NETWORK_GUIDE.md#troubleshooting) |
| **Learn the API** | [DOCUMENTATION.md#api-endpoints](DOCUMENTATION.md#api-endpoints) |
| **Set up development** | [CONTRIBUTING.md#development-setup](CONTRIBUTING.md#development-setup) |
| **Run tests** | [tests/README.md](tests/README.md) |
| **Secure my deployment** | [SECURITY_NOTES.md](SECURITY_NOTES.md) |
| **Find commands** | [DOCKER_QUICK_REF.txt](DOCKER_QUICK_REF.txt) |
| **Contribute code** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Understand architecture** | [DOCUMENTATION.md#architecture](DOCUMENTATION.md#architecture) |
| **Example queries** | [README.md#example-queries](README.md#example-queries) |
| **Deploy to prod** | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| **Configure for multiple Wazuh** | [DOCKER_NETWORK_GUIDE.md#scenario-3](DOCKER_NETWORK_GUIDE.md#scenario-3-multiple-wazuh-environments) |

---

## 📚 Documentation Hierarchy

```
README.md (Start Here!)
│
├── Quick Start
│   ├── QUICK_START.md ...................... Command reference
│   └── PROJECT_SUMMARY.txt ................. Visual summary
│
├── Deployment
│   ├── DOCKER_DEPLOYMENT.md ................ Docker setup
│   ├── DEPLOYMENT_CHECKLIST.md ............. Step-by-step guide
│   ├── DOCKER_NETWORK_GUIDE.md ............. Network config
│   ├── DOCKER_QUICK_REF.txt ................ Commands cheat sheet
│   └── DOCKER_SETUP_COMPLETE.txt ........... Deployment summary
│
├── Configuration
│   ├── .env.example ........................ Basic template
│   ├── .env.sample ......................... Complete reference
│   └── docker/.env.example ................. Docker template
│
├── Technical Reference
│   ├── DOCUMENTATION.md .................... Complete API docs
│   ├── CONTRIBUTING.md ..................... Contribution guide
│   └── SECURITY_NOTES.md ................... Security practices
│
└── Testing
    ├── tests/README.md ..................... Testing guide
    ├── tests/test_queries.py ............... Query tests
    ├── tests/test_advanced_dsl.py .......... DSL tests
    └── tests/test_mcp_cases.py ............. MCP tests
```

---

## 🎯 Recommended Reading Order

### For New Users (First Time Setup)

1. **[README.md](README.md)** - Overview and features (5 min)
2. **[QUICK_START.md](QUICK_START.md)** - Quick reference (2 min)
3. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Deployment steps (20 min)
4. **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Docker setup (15 min)
5. **[README.md#example-queries](README.md#example-queries)** - Try some queries (10 min)

**Total: ~50 minutes to productive use**

### For Developers (Contributing)

1. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines (30 min)
2. **[DOCUMENTATION.md](DOCUMENTATION.md)** - Architecture & API (45 min)
3. **[SECURITY_NOTES.md](SECURITY_NOTES.md)** - Security practices (15 min)
4. **[tests/README.md](tests/README.md)** - Testing (10 min)

**Total: ~1.5 hours to start contributing**

### For System Administrators (Production)

1. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Deployment (20 min)
2. **[DOCKER_NETWORK_GUIDE.md](DOCKER_NETWORK_GUIDE.md)** - Networking (25 min)
3. **[SECURITY_NOTES.md](SECURITY_NOTES.md)** - Security (15 min)
4. **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md#production)** - Production tips (15 min)

**Total: ~1.25 hours to production-ready**

---

## 🔄 Documentation Updates

### Last Updated
- README.md: Dec 26, 2025
- DOCUMENTATION.md: Dec 26, 2025
- DOCKER_DEPLOYMENT.md: Dec 26, 2025
- DEPLOYMENT_CHECKLIST.md: Dec 26, 2025
- DOCKER_NETWORK_GUIDE.md: Dec 26, 2025
- SECURITY_NOTES.md: Dec 26, 2025
- CONTRIBUTING.md: Dec 26, 2025

### Version
- Documentation Version: 2.0.0
- Corresponds to: Docker-enabled multi-Wazuh deployment

---

## 💡 Documentation Tips

### For Best Results:

1. **Start with README** - Always begin with the overview
2. **Follow the paths** - Use the "Documentation by Use Case" section
3. **Use search** - Ctrl+F to find specific topics
4. **Check examples** - Real examples are in every guide
5. **Consult troubleshooting** - Issues? Check troubleshooting sections first
6. **Ask for help** - If stuck, create a GitHub issue

### Reading Tips:

- 📖 **Beginner?** Start with README.md and QUICK_START.md
- 🔧 **Deploying?** Go straight to DEPLOYMENT_CHECKLIST.md
- 👨‍💻 **Developer?** Read CONTRIBUTING.md and DOCUMENTATION.md
- 🔒 **Security focus?** SECURITY_NOTES.md is your friend
- 🐛 **Having issues?** Check troubleshooting sections in each guide

---

## 📞 Getting Help

If you can't find what you need in the documentation:

1. **Search the docs** - Use Ctrl+F in each document
2. **Check examples** - Look at example queries and configurations
3. **Review troubleshooting** - Each guide has a troubleshooting section
4. **GitHub Issues** - Ask questions or report problems
5. **Read CONTRIBUTING.md** - For development questions

---

**Last Updated**: December 26, 2025  
**Documentation Version**: 2.0.0  
**Total Pages**: 8 main documents + supporting files  
**Total Lines**: 3,745 lines of documentation
