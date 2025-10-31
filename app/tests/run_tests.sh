#!/bin/bash
# Test script for Python-based MCP Server connected with OpenAI API
# This script runs unit, integration, and functional tests for the Python MCP Server

set -e

echo "============================================"
echo "Starting Python MCP Server Tests..."
echo "============================================"

# Activate virtual environment
echo "Activating virtual environment..."
source ../venv/Scripts/activate

# Set environment variables (replace YOUR_API_KEY with your actual key or use .env file)
export OPENAI_API_KEY=${OPENAI_API_KEY:-"YOUR_API_KEY_HERE"}
export LOG_LEVEL=info

echo "Environment variables set:"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:6}******"
echo "  LOG_LEVEL: $LOG_LEVEL"

# Define cleanup for any background processes
cleanup() {
    echo ""
    echo "Cleaning up..."
    pkill -f "python -m app.mcp_server" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "=== Running Unit Tests ==="
pytest tests/unit --maxfail=1 --disable-warnings -q

echo ""
echo "=== Running Integration Tests ==="
pytest tests/integration --maxfail=1 --disable-warnings -q

echo ""
echo "=== Testing MCP Server Startup ==="
echo "Starting MCP Server in background..."
python -m app.mcp_server &
SERVER_PID=$!

sleep 5
echo "Checking MCP Server health endpoint or log output..."
# You can replace this with curl or a log check
if ps -p $SERVER_PID > /dev/null; then
    echo "Server is running successfully (PID: $SERVER_PID)"
else
    echo "❌ Server failed to start!"
    exit 1
fi

echo ""
echo "Stopping MCP Server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "=== All Tests Complete ==="
echo ""
echo "Test Summary:"
echo "✓ Unit tests for core Python modules"
echo "✓ Integration tests with mock OpenAI API"
echo "✓ MCP Server startup test"
echo ""
echo "To manually test MCP Server:"
echo "  export OPENAI_API_KEY=your-api-key"
echo "  python -m app.mcp_server"
echo ""
echo "Then send MCP commands via stdin or HTTP (depending on your server design):"
echo "  echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}' | python -m app.mcp_server"
echo ""
echo "============================================"
echo "Python MCP Server Test Run Finished"
echo "============================================"
