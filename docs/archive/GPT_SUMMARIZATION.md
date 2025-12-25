# GPT Summarization

## Overview

All query endpoints automatically send results to GPT-4o for natural language summarization. This provides security analysts with clear, actionable insights from raw SIEM data.

## How It Works

### 1. Data Collection
Query results are collected from either:
- **Wazuh Manager API** (Simple Pipeline)
- **Wazuh Indexer/OpenSearch** (Advanced Pipeline, Direct DSL, Hybrid)

### 2. Smart Sampling
To avoid OpenAI token limits, the system intelligently samples data:
- **Indexer Results**: Sends first 10 documents + total count + aggregations
- **Manager API**: Sends first 10 items + total count
- **Large Datasets**: Automatically truncates while preserving key metrics

### 3. GPT Analysis
Sample data is sent to GPT-4o with:
- **System Prompt**: Security analyst context
- **User Prompt**: Original query + sampled data
- **Temperature**: 0.3 (focused, consistent)
- **Max Tokens**: 500 (concise summaries)

### 4. Natural Language Output
GPT returns:
1. **Brief Summary** (1-2 sentences)
2. **Key Findings** with counts
3. **Notable Patterns** or security concerns

## Endpoints with GPT Summarization

### ✅ `/query/nl` - Natural Language Query
```json
{
  "query": "Show me critical alerts from the last hour"
}
```
**Response includes:**
- `summary`: GPT-generated natural language summary
- `raw_data`: Full raw results (for reference)

### ✅ `/query/dsl` - Direct DSL Query
```json
{
  "index": "wazuh-alerts-*",
  "query": { "match_all": {} },
  "size": 50,
  "include_summary": true  // Default: true
}
```
**Response includes:**
- `summary`: GPT analysis (if `include_summary=true`)
- `formatted_response`: Same as summary
- `raw_results`: Full raw data

**Disable summarization:**
```json
{
  "include_summary": false  // Skip GPT call for faster response
}
```

### ✅ Hybrid NL+DSL Query
```json
{
  "query": "Analyze this query for security issues: {\"index\": \"wazuh-alerts-*\", \"query\": {...}}"
}
```
**Response includes:**
- `summary`: GPT insights based on NL context
- `nl_context`: Extracted natural language prompt
- `embedded_dsl`: Detected DSL query
- `raw_results`: Full query results

## Token Optimization

The system uses several strategies to stay within OpenAI limits:

### 1. Smart Sampling
```python
# Only send first 10 documents
"sample_documents": documents[:10]

# Include total count for context
"total_hits": 5234  # GPT knows there are 5234 total
```

### 2. Field Selection
- Sends only relevant fields to GPT
- Aggregations are included in full (usually compact)
- Large text fields are truncated

### 3. Fallback Handling
If GPT call fails (rate limit, timeout):
```python
return f"Found {count} results from Wazuh Indexer."
```

## Example Summaries

### Query: "Show me failed SSH logins"
**GPT Summary:**
> **Summary:** Found 47 failed SSH login attempts in the last hour from 12 unique IP addresses.
> 
> **Key Findings:**
> - 23 attempts from 192.168.1.100 (most active)
> - 8 attempts targeting root user
> - Geographic distribution: Russia (15), China (12), USA (8)
> 
> **Security Concerns:** Multiple brute-force attempts detected. Recommend IP blocking for repeat offenders.

### Query: "List all agents"
**GPT Summary:**
> **Summary:** System has 8 total agents, all currently active and reporting.
> 
> **Key Findings:**
> - 3 Windows agents (Server 2019)
> - 3 Ubuntu agents (20.04 LTS)
> - 2 CentOS agents (7.9)
> 
> **Status:** All agents healthy with recent check-ins.

## Configuration

GPT summarization is enabled by default. To configure:

### Environment Variables
```bash
OPENAI_API_KEY=sk-...  # Required
```

### Code Settings
```python
# In app/llm_client.py
model = "gpt-4o-2024-11-20"
temperature = 0.3
max_tokens = 500
timeout = 60.0  # seconds
```

## Performance

- **Sample Preparation**: ~5ms
- **GPT API Call**: ~1-3 seconds
- **Total Overhead**: ~1-3 seconds per query

## Rate Limits

OpenAI limits (gpt-4o):
- **TPM**: 30,000 tokens per minute
- **RPM**: 500 requests per minute

With sampling, typical usage:
- **Input**: ~2,000 tokens (sampled data)
- **Output**: ~500 tokens (summary)
- **Total**: ~2,500 tokens per query

**Capacity**: ~12 queries per minute safely within limits.

## Best Practices

### 1. Use Sampling for Large Datasets
✅ **Good**: Let system sample automatically
```json
{"query": "Show all alerts from last week"}  // System samples 10 docs
```

❌ **Bad**: Don't request full dataset for summarization
```json
{"query": "Show all 50,000 alerts", "size": 50000}  // Will fail
```

### 2. Disable Summary for Raw Analysis
If you don't need AI insights:
```json
{
  "index": "wazuh-alerts-*",
  "query": {...},
  "include_summary": false  // Faster response
}
```

### 3. Use Hybrid Mode for Targeted Analysis
Provide context for better insights:
```json
{
  "query": "Are there any indicators of lateral movement in: {DSL_QUERY}"
}
```

## Troubleshooting

### "Rate limit exceeded"
**Cause**: Too many requests or too large input
**Solution**: 
- Wait 60 seconds
- Reduce query frequency
- Disable `include_summary` for some queries

### "Timeout"
**Cause**: GPT API slow or network issues
**Solution**: System automatically falls back to count-based summary

### "No summary returned"
**Cause**: GPT returned empty content
**Solution**: System uses fallback summary with counts

## Future Enhancements

- [ ] Streaming summaries for real-time updates
- [ ] Custom summary templates per user
- [ ] Summary caching for identical queries
- [ ] Multi-language summaries
- [ ] Severity-based summarization strategies
