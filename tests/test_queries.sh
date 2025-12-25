#!/bin/bash
# Comprehensive Test Suite for Enhanced NL Query System
# Tests agent context, time awareness, rule mapping, and field validation

API_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Wazuh NL Query System - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to test a query
test_query() {
    local name="$1"
    local query="$2"
    local expected_pipeline="$3"
    
    echo -e "${BLUE}Test: ${name}${NC}"
    echo -e "Query: \"${query}\""
    
    response=$(curl -s -X POST "${API_URL}/query/nl" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"${query}\"}")
    
    # Extract pipeline and success status
    pipeline=$(echo "$response" | jq -r '.routing.pipeline // "ERROR"')
    success=$(echo "$response" | jq -r '.success // false')
    summary=$(echo "$response" | jq -r '.summary // "No summary"' | head -c 200)
    
    if [ "$success" = "true" ]; then
        echo -e "  ${GREEN}✓ SUCCESS${NC}"
        echo -e "  Pipeline: ${pipeline}"
        echo -e "  Summary: ${summary}..."
        
        # Check if pipeline matches expected
        if [ "$expected_pipeline" != "" ] && [ "$pipeline" != "$expected_pipeline" ]; then
            echo -e "  ${RED}⚠ WARNING: Expected ${expected_pipeline}, got ${pipeline}${NC}"
        fi
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        echo -e "  Error: ${error}"
    fi
    echo ""
}

# Wait for server to be ready
echo "Checking server health..."
for i in {1..10}; do
    if curl -s "${API_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is ready${NC}\n"
        break
    fi
    echo "Waiting for server... ($i/10)"
    sleep 2
done

echo -e "${BLUE}=== CATEGORY 1: Agent Context Tests ===${NC}\n"

test_query \
    "List all agents (SIMPLE)" \
    "Show me all agents" \
    "SIMPLE_PIPELINE"

test_query \
    "Active agents only (SIMPLE)" \
    "List active agents" \
    "SIMPLE_PIPELINE"

test_query \
    "Logs from specific agent (ADVANCED)" \
    "Show me logs from the first agent in last 24 hours" \
    "ADVANCED_PIPELINE"

test_query \
    "Windows agent specific" \
    "Get alerts from Windows agents" \
    "ADVANCED_PIPELINE"

echo -e "${BLUE}=== CATEGORY 2: Time-Aware Queries ===${NC}\n"

test_query \
    "Recent logs (time-sensitive)" \
    "Show me recent alerts" \
    "ADVANCED_PIPELINE"

test_query \
    "Last 15 minutes" \
    "Get logs from last 15 minutes" \
    "ADVANCED_PIPELINE"

test_query \
    "Today's events" \
    "Show me critical alerts from today" \
    "ADVANCED_PIPELINE"

test_query \
    "Last hour" \
    "Failed logins in the last hour" \
    "ADVANCED_PIPELINE"

echo -e "${BLUE}=== CATEGORY 3: Rule Mapping Tests ===${NC}\n"

test_query \
    "SSH failed logins" \
    "Show me SSH login failures" \
    "ADVANCED_PIPELINE"

test_query \
    "Windows failed logins" \
    "Get Windows login failures from last 24 hours" \
    "ADVANCED_PIPELINE"

test_query \
    "Brute force detection" \
    "Show me brute force attempts" \
    "ADVANCED_PIPELINE"

test_query \
    "File integrity monitoring" \
    "Show me files that were modified today" \
    "ADVANCED_PIPELINE"

echo -e "${BLUE}=== CATEGORY 4: Severity & Field Tests ===${NC}\n"

test_query \
    "Critical alerts" \
    "Show me critical severity alerts" \
    "ADVANCED_PIPELINE"

test_query \
    "High severity from specific IP" \
    "High severity alerts from IP 192.168.1.100" \
    "ADVANCED_PIPELINE"

test_query \
    "No severity filter" \
    "Show me all logs from last hour" \
    "ADVANCED_PIPELINE"

echo -e "${BLUE}=== CATEGORY 5: Complex Pattern Queries ===${NC}\n"

test_query \
    "Multiple failed attempts" \
    "Show me multiple failed login attempts" \
    "ADVANCED_PIPELINE"

test_query \
    "Pattern detection" \
    "Summarize security events by source IP" \
    "ADVANCED_PIPELINE"

test_query \
    "MITRE technique" \
    "Show me attacks using brute force technique" \
    "ADVANCED_PIPELINE"

echo -e "${BLUE}=== CATEGORY 6: Decoder-Specific Queries ===${NC}\n"

test_query \
    "SSH logs only" \
    "Show me SSH logs from last 24 hours" \
    "ADVANCED_PIPELINE"

test_query \
    "Windows Event logs" \
    "Get Windows events from today" \
    "ADVANCED_PIPELINE"

test_query \
    "Firewall logs" \
    "Show me firewall logs" \
    "ADVANCED_PIPELINE"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Suite Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo "To see detailed logs, run:"
echo "  tail -f /tmp/wazuh_query.log"
echo ""
echo "To test interactively, use:"
echo "  curl -X POST http://localhost:8000/query/nl -H 'Content-Type: application/json' -d '{\"query\": \"your query here\"}' | jq"
