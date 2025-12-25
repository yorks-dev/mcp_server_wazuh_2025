# Query Guide: Understanding MCP Server Query Capabilities

## 🎯 Overview

The MCP Server supports **flexible querying** - you can retrieve **ALL logs** or filter by severity, time, agent, and more.

---

## 📊 Query Types

### 1. **Time-Based Queries (ALL Logs)**

These queries retrieve **ALL logs** regardless of severity level:

```
"get logs from last 15 minutes"
"show me recent logs"
"logs from last hour"
"show me logs from today"
"recent activity"
```

**What you get:**
- ✅ Natural language summary
- ✅ Raw indexer data (JSON)
- ✅ Generated DSL query
- ✅ ALL log levels (info, low, medium, high, critical)

---

### 2. **Severity-Filtered Queries**

These queries filter by security severity:

```
"show me critical alerts from last 24 hours"
"high severity incidents today"
"medium level alerts this week"
```

**Severity Mappings:**
- **Critical**: `rule.level >= 12`
- **High**: `rule.level >= 8`
- **Medium**: `rule.level >= 5`
- **Low**: `rule.level < 5`

---

### 3. **Agent-Specific Queries**

Filter by specific agents:

```
"show me logs from agent web-server-01"
"alerts from production agents"
"activity on database server"
```

---

### 4. **Custom Filters**

Combine multiple filters:

```
"critical alerts from agent web-01 in last hour"
"show me SSH authentication failures today"
"file integrity changes from last week"
```

---

## 🔍 Frontend Display

The frontend shows **BOTH** natural language and technical details:

### Natural Language Summary
- 📝 Plain English explanation
- Key findings and counts
- Security insights
- Recommended actions

### Technical Details (3 Tabs)

1. **Formatted Tab**
   - Structured cards for each log/alert
   - Rule description
   - Severity badges (color-coded)
   - Agent info
   - Timestamps
   - Source IPs

2. **Raw JSON Tab**
   - Complete API response
   - Parsed plan structure
   - DSL query
   - Full indexer response
   - Metadata

3. **DSL Tab**
   - Generated OpenSearch query
   - Filters applied
   - Time range
   - Aggregations (if any)

---

## 📝 Example Queries

### Retrieve ALL Logs (No Filtering)

**Query:**
```
get logs from last 15 minutes
```

**What happens:**
1. LLM parses: `{"filters": [], "time": {"from": "now-15m", "to": "now"}}`
2. No severity filter applied
3. Returns **ALL** logs from last 15 minutes
4. Shows natural language summary + raw data

**Frontend Display:**
```
📝 Summary: "Retrieved 247 logs from the last 15 minutes across 12 agents..."

📊 Formatted:
   - Auth success on web-01 (Level: 3)
   - File modified on db-02 (Level: 5)
   - Critical rule triggered on app-03 (Level: 15)
   ...

📄 Raw JSON: {...full response...}
⚙️  DSL: {query: {bool: {filter: [{range: {...}}]}}}
```

---

### Retrieve Critical Only

**Query:**
```
show me critical alerts from last hour
```

**What happens:**
1. LLM parses: `{"filters": [{"field": "rule.level", "op": "gte", "value": 12}]}`
2. Severity filter applied
3. Returns **ONLY** critical logs (level >= 12)

---

## 🚀 Three Pipeline Options

### 1. Simple Query (`POST /query/simple`)
- Fast, keyword-based
- Uses Wazuh API directly
- Best for: Quick agent/alert checks
- **No DSL generation**

### 2. Advanced Query (`POST /query/`)
- Full NL → LLM → DSL → Indexer pipeline
- Complex filtering & time ranges
- Best for: Detailed security analysis
- **Returns raw indexer data**

### 3. Direct DSL (`POST /mcp/wazuh.search`)
- Pre-built OpenSearch queries
- Programmatic access
- Best for: Automation, scripts
- **Full control over query**

---

## 🎨 Frontend Features

### Query Interface
- 3 pipeline buttons (Simple/Advanced/DSL)
- Example query chips for quick testing
- DSL template loader
- Ctrl+Enter to execute

### Results Display
- Loading spinner with status
- Error messages with details
- Success state with tabs
- Natural language at top
- Technical details below

### Visual Indicators
- **Severity Badges**:
  - 🔴 Critical (red)
  - 🟠 High (orange)
  - 🔵 Medium (blue)
  - 🟢 Low (green)

- **Execution Time**: Shows query performance
- **Result Count**: Total hits from indexer
- **Server Status**: Online/offline indicator

---

## 🔐 Security Note

The operator can see:
- ✅ Natural language summaries (safe for executives)
- ✅ Technical details (for security analysts)
- ✅ Raw indexer responses (for debugging)
- ✅ Generated DSL queries (for learning/auditing)

This dual-view approach means:
- **Executives**: Read the summary
- **Analysts**: Dive into technical details
- **Engineers**: Inspect DSL and raw data

---

## 🧪 Testing Your Queries

Use the test script:

```bash
cd tests
python test_query_filters.py
```

This validates:
- ✅ Time-based queries return ALL logs
- ✅ Severity filters work correctly
- ✅ Frontend displays both views
- ✅ Raw data is accessible

---

## 💡 Tips for Operators

1. **Start Simple**: Use time-based queries first
   - "logs from last 10 minutes"
   - Gets you familiar with all activity

2. **Add Filters Gradually**: Narrow down as needed
   - "critical logs from last 10 minutes"
   - "high severity on web servers"

3. **Use Example Chips**: Click to load common queries

4. **Check All Tabs**: 
   - Summary for quick insights
   - Formatted for detailed review
   - Raw for debugging

5. **Watch Execution Time**: Slower queries = more data

---

## 🆘 Troubleshooting

**No results returned?**
- Check time range (may be too narrow)
- Verify agents are sending logs
- Try broader query first

**Only seeing critical logs?**
- Ensure query doesn't mention "critical" or "high"
- Use "all logs" or just time range

**Frontend not updating?**
- Check server status indicator
- Verify MCP server is running
- Check browser console for errors

**Raw data missing?**
- Should always be present in Raw JSON tab
- Check if query succeeded
- Verify indexer connectivity
