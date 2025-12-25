#!/bin/bash

echo "=========================================="
echo "Starting Wazuh MCP Server (Development)"
echo "=========================================="

# 1. Setup SSH tunnel
echo "Step 1: Setting up SSH tunnel..."
./setup_dev_tunnel.sh

if [ $? -ne 0 ]; then
    echo "Failed to setup tunnel. Exiting."
    exit 1
fi

# 2. Activate environment
echo ""
echo "Step 2: Activating virtual environment..."
source .venv/bin/activate

# 3. Start server with auto-reload
echo ""
echo "Step 3: Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
