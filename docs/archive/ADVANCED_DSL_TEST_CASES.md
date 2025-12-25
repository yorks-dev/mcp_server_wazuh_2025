# Advanced DSL Test Cases - Security Analytics

## Overview
This document covers advanced security analytics test cases that validate complex DSL queries for authentication attacks, malware detection, file integrity monitoring, vulnerability management, and agent health monitoring.

## Quick Test Execution

```bash
# Run all advanced security analytics tests
./test_advanced_dsl.py

# Expected: ALL ADVANCED TESTS PASSED! (5/5)
```

---

## ✅ TEST CASE 1: Authentication Attack Detection

### Purpose
Detect high-severity failed login attempts and potential brute force attacks

### User Query (Natural Language)
```
Show high-severity failed login attempts in the last 12 hours
```

### MCP Tool Invoked
- `wazuh_indexer_search`

### DSL Logic Generated
```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-12h"
            }
          }
        },
        {
          "range": {
            "rule.level": {
              "gte": 10
            }
          }
        },
        {
          "terms": {
            "rule.groups": ["authentication_failed"]
          }
        }
      ]
    }
  }
}
```

### Expected Output Fields
- ✓ `agent.name` - Which host had failed logins
- ✓ `data.srcip` - Source IP of attacker
- ✓ `data.dstuser` - Username attempted
- ✓ `rule.description` - What happened
- ✓ `rule.level` - Severity (10+ = high)

### LLM Enhancement
The LLM analyzes results and provides:
- Count of failed attempts
- Pattern detection (repeated IPs)
- Context: "Possible brute force attack from 192.168.1.50"
- Recommendations: "Block IP, enable MFA, review user account"

### Confirmation
✔ **LLM → DSL → MCP → Indexer → Agent logs**  
✔ **High-severity filtering (rule.level ≥ 10)**  
✔ **Time-based analysis (last 12 hours)**

### Test Result
✅ **PASS** - Query successfully generated and executed

---

## ✅ TEST CASE 2: Malware / Suspicious Process Detection

### Purpose
Identify malware infections and suspicious executable launches

### User Query (Natural Language)
```
Any malware or suspicious executables detected this week?
```

### MCP Tool Invoked
- `wazuh_indexer_search`

### DSL Logic Generated
```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-7d"
            }
          }
        },
        {
          "terms": {
            "rule.groups": ["malware", "rootkit"]
          }
        }
      ]
    }
  }
}
```

### Expected Output Fields
- ✓ `process.name` - Executable name
- ✓ `agent.name` - Infected host
- ✓ `rule.id` - Detection rule
- ✓ `rule.mitre.technique` - MITRE ATT&CK mapping
- ✓ `full_log` - Complete log details

### MITRE ATT&CK Integration
Results include MITRE technique mappings:
- **T1059** - Command and Scripting Interpreter
- **T1071** - Application Layer Protocol
- **T1055** - Process Injection

### LLM Enhancement
- Explains malware type and behavior
- Severity assessment
- Containment recommendations
- Links to MITRE ATT&CK techniques

### Confirmation
✔ **Security analytics + MITRE mapping**  
✔ **Process detection capabilities**  
✔ **Rule group filtering (malware)**

### Test Result
✅ **PASS** - Query successfully generated and executed

---

## ✅ TEST CASE 3: File Integrity Monitoring (FIM)

### Purpose
Track critical file modifications on production servers

### User Query (Natural Language)
```
Which critical files were modified on production servers today?
```

### MCP Tool Invoked
- `wazuh_indexer_search`

### DSL Logic Generated
```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-1d"
            }
          }
        },
        {
          "terms": {
            "rule.groups": ["syscheck", "ossec"]
          }
        },
        {
          "terms": {
            "asset.criticality": ["High"]
          }
        }
      ]
    }
  }
}
```

### Expected Output Fields
- ✓ `syscheck.path` - File path modified
- ✓ `agent.name` - Host where change occurred
- ✓ `syscheck.event` - Change type (added/modified/deleted)
- ✓ `@timestamp` - When it happened

### Asset Enrichment
MCP enriches query with:
- Asset DB → criticality = High
- Production server identification
- File classification (config, binary, sensitive)

### Common File Changes Detected
- `/etc/passwd` - User account modifications
- `/etc/shadow` - Password changes
- `/bin/*` - Binary replacements
- `/var/www/html/*` - Web content changes

### LLM Enhancement
- Prioritizes critical files
- Explains change significance
- Security implications
- Forensic recommendations

### Confirmation
✔ **LLM + MCP + Asset enrichment**  
✔ **FIM (syscheck) detection**  
✔ **Critical file prioritization**

### Test Result
✅ **PASS** - Query successfully generated and executed

---

## ✅ TEST CASE 4: Vulnerability Severity Overview

### Purpose
Aggregate and summarize vulnerability data across all hosts

### User Query (Natural Language)
```
Summarize high and critical vulnerabilities across all hosts
```

### MCP Tool Invoked
- `wazuh_indexer_aggregate`

### DSL Logic Generated
```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        {
          "terms": {
            "vulnerability.severity": ["High", "Critical"]
          }
        }
      ]
    }
  },
  "aggs": {
    "by_severity": {
      "terms": {
        "field": "vulnerability.severity",
        "size": 10
      }
    },
    "by_agent": {
      "terms": {
        "field": "agent.name",
        "size": 10
      }
    }
  }
}
```

### Expected Output
**Aggregation Results:**
```
Critical: 23 vulnerabilities
High: 87 vulnerabilities

Top Affected Agents:
1. web-server-01: 15 critical
2. db-server-01: 8 critical
3. app-server-02: 5 critical
```

### LLM Enhancement
- Prioritizes by severity
- Identifies most vulnerable hosts
- Recommends patching order
- Risk assessment summary

### Confirmation
✔ **Aggregation + summarization**  
✔ **Multi-dimensional grouping (severity + agent)**  
✔ **Vulnerability management**

### Test Result
✅ **PASS** - Query successfully generated and executed

---

## ✅ TEST CASE 5: Agent Health & Heartbeat

### Purpose
Identify agents that stopped reporting (disconnected/offline)

### User Query (Natural Language)
```
Which agents stopped sending logs in the last 30 minutes?
```

### MCP Tool Options

**Option 1: Wazuh API**
```
GET /agents?status=disconnected
```

**Option 2: Indexer Aggregation**
```json
{
  "size": 0,
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-30m"
      }
    }
  },
  "aggs": {
    "active_agents": {
      "terms": {
        "field": "agent.name",
        "size": 100
      }
    }
  }
}
```

### Expected Output
- ✓ `agent.id` - Agent identifier
- ✓ `agent.name` - Hostname
- ✓ Last seen timestamp
- ✓ Status (disconnected/never_connected)

### Health Indicators
- **Active**: Logs within last 5 minutes
- **Warning**: No logs 5-30 minutes
- **Critical**: No logs > 30 minutes
- **Disconnected**: Agent status = disconnected

### LLM Enhancement
- Identifies potentially compromised agents
- Network connectivity issues
- Agent service failures
- Remediation steps

### Confirmation
✔ **Agent health monitoring**  
✔ **Heartbeat detection**  
✔ **Wazuh API connectivity** (if available)

### Test Result
✅ **PASS** - Query successfully generated and executed

---

## How the Final Response Flows

### 1. Query Parsing (LLM)
```
User: "Show high-severity failed logins"
  ↓
LLM: Identifies intent → authentication attack detection
```

### 2. DSL Generation (MCP)
```
MCP Tool: wazuh_indexer_search
  ↓
DSL Query: {
  bool: {
    filter: [
      {range: {rule.level: {gte: 10}}},
      {terms: {rule.groups: ["authentication_failed"]}}
    ]
  }
}
```

### 3. Data Retrieval (Indexer)
```
Elasticsearch Query Execution
  ↓
Raw JSON: {
  hits: [
    {agent: "web-01", srcip: "192.168.1.50", ...},
    {agent: "web-01", srcip: "192.168.1.50", ...}
  ]
}
```

### 4. MCP Processing
```
MCP Server:
  - Cleans data
  - Structures results
  - Enforces limits (1000 docs)
  - Applies policy rules
```

### 5. LLM Summarization
```
LLM receives structured data:
  ↓
Generates summary:
  - "Detected 15 failed login attempts from 192.168.1.50"
  - "This indicates a possible brute force attack"
  - "Recommendation: Block IP, enable MFA"
  - "Priority: High - immediate action required"
```

### 6. Operator Response
```
Clean table + explanation:

┌──────────┬──────────────────┬───────────┬──────────┐
│ Agent    │ Source IP        │ User      │ Count    │
├──────────┼──────────────────┼───────────┼──────────┤
│ web-01   │ 192.168.1.50     │ admin     │ 15       │
│ web-01   │ 192.168.1.50     │ root      │ 8        │
└──────────┴──────────────────┴───────────┴──────────┘

🚨 **Analysis**: Brute force attack detected
📋 **Recommendation**: Block 192.168.1.50 immediately
```

---

## Response Enhancement by LLM

The LLM adds critical value:

### 1. Explanation
- "This pattern indicates credential stuffing"
- "15 attempts in 2 minutes suggests automated tool"

### 2. Prioritization
- **Critical**: Active brute force (immediate response)
- **High**: Malware detected (isolate host)
- **Medium**: File change on dev server (investigate)

### 3. Contextualization
- Historical comparison: "3x higher than normal"
- Related events: "Same IP attempted MySQL access"
- Kill chain position: "Initial access phase"

### 4. Next-Step Recommendations
- **Immediate**: "Block IP at firewall"
- **Short-term**: "Reset user password, enable MFA"
- **Long-term**: "Implement rate limiting, deploy SIEM alerts"

---

## Test Results Summary

| Test Case | Status | Key Capability |
|-----------|--------|----------------|
| Authentication Attacks | ✅ PASS | High-severity filtering, rule.level ≥ 10 |
| Malware Detection | ✅ PASS | MITRE mapping, rule groups |
| File Integrity | ✅ PASS | FIM (syscheck), asset enrichment |
| Vulnerability Overview | ✅ PASS | Aggregations, severity grouping |
| Agent Health | ✅ PASS | Agent monitoring, heartbeat detection |

**Overall: 5/5 PASSED (100% success rate)**

---

## Key Confirmations

### ✔ Technical Capabilities
- [x] LLM → DSL conversion working
- [x] MCP → Indexer queries executing
- [x] Complex bool queries with multiple filters
- [x] Time range filtering (12h, 1 week, today, 30m)
- [x] Rule groups (authentication_failed, malware, syscheck)
- [x] Severity filtering (rule.level ≥ 10)
- [x] Field extraction (agent, srcip, process, file)
- [x] MITRE technique mapping
- [x] Aggregations (vulnerability, agent, severity)
- [x] LLM summarization + recommendations

### ✔ Security Analytics
- [x] Authentication attack detection
- [x] Malware/rootkit identification
- [x] File integrity monitoring (FIM)
- [x] Vulnerability management
- [x] Agent health monitoring
- [x] Threat intelligence enrichment
- [x] MITRE ATT&CK framework integration

### ✔ Operational Features
- [x] Natural language query processing
- [x] Automated DSL generation
- [x] Real-time data retrieval
- [x] Intelligent summarization
- [x] Actionable recommendations
- [x] Priority-based alerting

---

## Running Tests

### Automated Test Suite
```bash
# Run all advanced tests
./test_advanced_dsl.py

# Expected output: ALL ADVANCED TESTS PASSED! (5/5)
```

### Manual Testing via Frontend
```bash
# Start frontend
cd frontend && python3 -m http.server 8080 &

# Open browser
http://localhost:8080

# Try queries:
- "Show high-severity failed logins from last 12 hours"
- "Any malware detected this week?"
- "Which files were modified today?"
- "Summarize critical vulnerabilities"
- "Which agents are offline?"
```

### Manual Testing via curl
```bash
# Test 1: Authentication Attacks
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show high-severity failed login attempts in the last 12 hours"}'

# Test 2: Malware Detection
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Any malware or suspicious executables detected this week?"}'

# Test 3: File Integrity
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Which critical files were modified on production servers today?"}'

# Test 4: Vulnerabilities
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize high and critical vulnerabilities across all hosts"}'

# Test 5: Agent Health
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Which agents stopped sending logs in the last 30 minutes?"}'
```

---

## Performance Notes

**Typical Query Times:**
- Authentication queries: 12-18 seconds
- Malware detection: 15-22 seconds (MITRE enrichment)
- FIM queries: 10-16 seconds
- Aggregations: 18-25 seconds
- Agent health: 8-14 seconds

**Factors Affecting Performance:**
- GPT-4o API latency (8-13s for parsing)
- Elasticsearch query complexity
- Result set size (1000 doc limit)
- Aggregation computation
- Network latency

---

## Troubleshooting

### No Results Returned
**Symptoms:** Query succeeds but returns 0 documents

**Possible Causes:**
- No matching data in time range
- Wazuh agents not generating relevant events
- Rule groups not matching

**Solutions:**
```bash
# Check if any data exists
curl -u admin:SecretPassword \
  'https://localhost:9200/wazuh-alerts-*/_count' -k

# Check specific rule group
curl -u admin:SecretPassword \
  'https://localhost:9200/wazuh-alerts-*/_search?q=rule.groups:authentication_failed' -k
```

### Field Not Found Errors
**Symptoms:** Query fails with "field not found" or "unknown field"

**Solutions:**
- Verify field in FIELD_ALLOWLIST ([app/config.py](app/config.py#L15-L45))
- Check FIELD_TYPES mapping ([app/validators.py](app/validators.py#L8-L40))
- Use correct field name (e.g., `data.srcip` not `srcip`)

### Timeout Issues
**Symptoms:** Query takes > 60 seconds

**Solutions:**
- Check GPT API performance
- Review timing logs: parse, query, format stages
- Consider query complexity reduction
- Check Elasticsearch cluster health

---

## Related Documentation

- [MCP_TEST_CASES.md](MCP_TEST_CASES.md) - Basic test cases
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete testing procedures
- [FRONTEND_TESTING.md](FRONTEND_TESTING.md) - UI testing scenarios
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API quick reference
- [UNIFIED_PIPELINE_SUMMARY.md](UNIFIED_PIPELINE_SUMMARY.md) - Pipeline architecture

---

**Last Updated:** 2025-12-23  
**Test Suite Version:** 1.0  
**Status:** ✅ All Tests Passing (5/5)
