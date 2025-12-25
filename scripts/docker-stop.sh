#!/bin/bash

echo "🛑 Stopping Wazuh MCP Server..."
docker-compose down

echo ""
echo "✅ Services stopped"
echo ""
echo "To start again:"
echo "  ./scripts/docker-deploy.sh"
