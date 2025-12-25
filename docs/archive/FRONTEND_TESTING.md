# Frontend Testing Guide

## ✅ Frontend is Running

- **URL**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Status**: Both services are active

## 🎨 Enhanced Features

### 1. **Updated Example Queries**
New examples showcase the enhanced capabilities:
- "Show me all agents" - Simple pipeline
- "Critical alerts from today" - Time-aware query
- "SSH login failures from last hour" - Rule mapping + time awareness
- "Brute force attempts" - Security pattern detection
- "Windows failed logins" - Windows Event mapping
- "File modifications today" - FIM events

### 2. **Enhanced Routing Display**
- **Pipeline badges** with icons (🔍 Simple / 🚀 Advanced)
- **Color-coded confidence** (Green ≥90%, Yellow ≥70%, Red <70%)
- **Detailed reasoning** explanation
- **Parsed query details** for advanced queries showing:
  - Number of filters applied
  - Time range used
  - Result limit
  - Aggregation type (if used)

### 3. **Better Error Handling**
When queries fail, frontend now shows:
- Original error message
- Possible causes
- Troubleshooting suggestions
- Link to check server logs

### 4. **Agent Context Display**
For agent-specific queries, the UI shows which agents are being targeted.

### 5. **Time Awareness Indicators**
Queries with time ranges display:
- Exact time range (e.g., "now-1h to now")
- Formatted in human-readable format

## 🧪 Testing Steps

### Test 1: Simple Agent Query
```
1. Open http://localhost:8080
2. Click "Show me all agents" example chip
3. Click "Execute Query"
4. Verify:
   ✓ Shows "🔍 Simple Pipeline" badge
   ✓ High confidence (90%+)
   ✓ Lists 4 agents
   ✓ Displays agent details (name, OS, status)
```

### Test 2: Time-Aware Query
```
1. Enter: "Critical alerts from today"
2. Execute
3. Verify:
   ✓ Shows "🚀 Advanced Pipeline" badge
   ✓ Routing reason mentions "today"
   ✓ Parsed query shows time: "now/d to now"
   ✓ Filter shows rule.level >= 12
```

### Test 3: Rule Mapping
```
1. Click "SSH failures" example
2. Execute
3. Verify:
   ✓ Advanced pipeline selected
   ✓ Shows multiple filters (decoder.name, rule.id)
   ✓ Rules 5710, 5551 mentioned in filters
   ✓ Results show SSH-related alerts
```

### Test 4: Agent-Specific Query
```
1. Enter: "Show me logs from Linux_VM agent"
2. Execute
3. Verify:
   ✓ Advanced pipeline
   ✓ Filter shows agent.name = "Linux_VM"
   ✓ Results filtered to that agent only
```

### Test 5: Brute Force Detection
```
1. Click "Brute force" example
2. Execute
3. Verify:
   ✓ Advanced pipeline
   ✓ Shows rules 5720, 87801, etc.
   ✓ Higher result limit (100+)
   ✓ Pattern detection mentioned
```

### Test 6: Direct DSL Query
```
1. Click "Direct DSL" button
2. Click "Load Template"
3. Modify as needed
4. Execute
5. Verify:
   ✓ No routing info (direct query)
   ✓ Raw DSL shown in DSL tab
   ✓ Results displayed correctly
```

## 🎯 Visual Indicators

### Pipeline Badges
- **🔍 Simple Pipeline** - Blue gradient, for agent queries
- **🚀 Advanced Pipeline** - Green gradient, for time-based/alert queries

### Confidence Colors
- **Green (90-100%)** - High confidence routing
- **Yellow (70-89%)** - Medium confidence
- **Red (<70%)** - Low confidence (ambiguous query)

### Query Details
Advanced queries show expandable details:
```
🔧 Query Details:
  • Filters: 3 active
  • Time: now-24h to now
  • Limit: 100 results
  • Aggregation: terms
```

## 📱 Responsive Design

The UI adapts to different screen sizes:
- Desktop: Side-by-side layout
- Tablet: Stacked with full width
- Mobile: Single column, touch-friendly

## ⚡ Performance

Expected response times:
- Agent queries: 1-3 seconds
- Time-based queries: 3-10 seconds
- Complex aggregations: 10-20 seconds

Loading spinner appears during query execution.

## 🐛 Known Issues & Workarounds

### Issue: Timeout on very large queries
**Workaround**: Reduce time window or add more specific filters

### Issue: Empty results
**Workaround**: Check if time range has data (try "last 7 days" instead of "last hour")

## 🚀 Quick Start Commands

```bash
# Start backend (if not running)
cd /home/kaustubh/mcp_server_wazuh_2025
/home/kaustubh/mcp_server_wazuh_2025/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# Start frontend (if not running)
cd /home/kaustubh/mcp_server_wazuh_2025/frontend
python3 -m http.server 8080 &

# Open browser
xdg-open http://localhost:8080  # Linux
open http://localhost:8080      # macOS
start http://localhost:8080     # Windows
```

## ✨ New Capabilities Summary

| Feature | Before | After |
|---------|--------|-------|
| Example queries | Generic | Agent/time/rule-aware |
| Routing display | Basic badge | Detailed with confidence colors |
| Error messages | Generic | Specific with troubleshooting |
| Query details | Hidden | Visible with breakdown |
| Time awareness | Not shown | Displays exact ranges |
| Agent context | Not shown | Shows targeted agents |
| Rule mapping | Not shown | Shows matched rules |

---

**Frontend is production-ready with full backend feature support!** 🎉
