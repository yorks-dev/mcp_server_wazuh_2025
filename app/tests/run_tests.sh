#!/bin/bash
# ============================================
# Test script for Python-based MCP Server connected with Wazuh and OpenAI API
# ============================================
set -e

echo "============================================"
echo "Starting MCP Server Test Suite..."
echo "============================================"

# Activate virtual environment
echo "Activating virtual environment..."
source ./.venv/Scripts/activate

# Set environment variables (use .env file or export manually)
export OPENAI_API_KEY=${OPENAI_API_KEY:-"YOUR_API_KEY_HERE"}
export LOG_LEVEL=info

echo "Environment variables set:"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:6}******"
echo "  LOG_LEVEL: $LOG_LEVEL"

echo ""
echo "=== Running Unit Tests ==="
pytest app/tests/test_dsl_builder.py --maxfail=1 --disable-warnings -q
pytest app/tests/test_schema.py --maxfail=1 --disable-warnings -q

echo ""
echo "=== MCP Server Startup Check ==="
echo "Starting FastAPI MCP Server in background..."
python -m app.main &
SERVER_PID=$!

# Allow server some time to start
sleep 5

# Check if server process is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ MCP Server (FastAPI) is running successfully (PID: $SERVER_PID)"
else
    echo "❌ MCP Server failed to start!"
    exit 1
fi

echo ""
echo "Stopping MCP Server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "=== All Tests Completed Successfully ==="
echo ""
echo "Test Summary:"
echo "✓ test_dsl_builder.py - DSL query builder validation"
echo "✓ test_schema.py - Schema validation"
echo "✓ MCP Server - FastAPI startup test"
echo ""
echo "============================================"
echo "MCP Server Test Run Finished"
echo "============================================"
