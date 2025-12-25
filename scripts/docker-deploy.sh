#!/bin/bash

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🚀 Deploying Wazuh MCP Server (Docker Network - No Tunnel)  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env with your credentials:"
    echo "   - Wazuh API credentials"
    echo "   - OpenSearch credentials"
    echo "   - OpenAI API key"
    echo ""
    echo "📝 Note: Using Docker service names (wazuh.manager, wazuh.indexer)"
    echo "   No SSH tunnel needed! All services on same Docker network."
    echo ""
    echo "Run this script again after configuring .env"
    exit 1
fi

# Check if Wazuh Docker network exists
echo "🔍 Checking for Wazuh Docker network..."
if ! docker network ls | grep -q "wazuh"; then
    echo "⚠️  Wazuh Docker network 'wazuh' not found."
    echo ""
    echo "Creating external network 'wazuh'..."
    docker network create wazuh
    echo "✅ Network created"
    echo ""
    echo "📝 Note: If your Wazuh uses a different network name:"
    echo "   1. Run: docker network ls"
    echo "   2. Update docker-compose.yml networks section"
    echo "   3. Common names: wazuh-docker_default, wazuh_default"
fi

# Check if required environment variables are set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-proj-your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY not configured in .env"
    echo "   Please add your OpenAI API key to .env file"
    exit 1
fi

# Check if ports are available
echo "🔍 Checking port availability..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use."
    read -p "   Stop existing service? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti:8000)
        kill $PID 2>/dev/null || true
        sleep 2
    else
        exit 1
    fi
fi

if lsof -Pi :8443 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8443 is already in use."
    read -p "   Stop existing service? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti:8443)
        kill $PID 2>/dev/null || true
        sleep 2
    else
        exit 1
    fi
fi

# Create logs directory
mkdir -p logs

# Build and start services
echo ""
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy (30s)..."
sleep 10

# Check container status
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🏥 Checking service health..."
sleep 5

# Test API health
echo ""
echo "Testing API health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
    curl -s http://localhost:8000/health | jq '.' || true
else
    echo "❌ API health check failed"
    echo "📝 Check logs: docker-compose logs mcp-server"
fi

# Test Wazuh connectivity from inside container
echo ""
echo "Testing Wazuh Manager connectivity..."
if docker exec wazuh-mcp-server curl -k -s https://wazuh.manager:55000 > /dev/null 2>&1; then
    echo "✅ Can reach Wazuh Manager (wazuh.manager:55000)"
else
    echo "❌ Cannot reach Wazuh Manager"
    echo "📝 Check: docker network inspect wazuh"
fi

echo ""
echo "Testing Wazuh Indexer connectivity..."
if docker exec wazuh-mcp-server curl -k -s https://wazuh.indexer:9200 > /dev/null 2>&1; then
    echo "✅ Can reach Wazuh Indexer (wazuh.indexer:9200)"
else
    echo "❌ Cannot reach Wazuh Indexer"
    echo "📝 Check: docker network inspect wazuh"
fi

# Test frontend
echo ""
echo "Testing frontend..."
if curl -k -s https://localhost:8443/ > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend check failed"
    echo "📝 Check logs: docker-compose logs mcp-frontend"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Deployment Complete!                    ║"
echo "╚══Check network:    docker network inspect wazuh"
echo "   Test Wazuh:       docker exec wazuh-mcp-server curl -k https://wazuh.manager:55000"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""
echo "🎉 Docker Network Deployment:"
echo "   ✅ No SSH tunnels needed"
echo "   ✅ All services on same Docker network"
echo "   ✅ Uses Docker service names (wazuh.manager, wazuh.indexer)"
echo "   ✅ Fast, secure, production-ready
echo "📊 Access your services:"
echo "   ┌─────────────────────────────────────────────────────────┐"
echo "   │ Wazuh Dashboard:   https://localhost         (port 443) │"
echo "   │ MCP Frontend:      https://localhost:8443    (port 8443)│"
echo "   │ MCP Frontend HTTP: http://localhost:8080 (→ HTTPS:8443) │"
echo "   │ MCP API:           http://localhost:8000                │"
echo "   │ API Docs:          http://localhost:8000/docs           │"
echo "   └─────────────────────────────────────────────────────────┘"
echo ""
echo "⚠️  Browser Security Warning:"
echo "   Using self-signed certificate. Browser will show security warning."
echo "   Click 'Advanced' → 'Proceed to localhost' to continue."
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   View API logs:    docker-compose logs -f mcp-server"
echo "   View web logs:    docker-compose logs -f mcp-frontend"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""
echo "🔒 Production SSL:"
echo "   Place your certificates in ssl/ directory:"
echo "   - ssl/cert.crt (certificate + chain)"
echo "   - ssl/cert.key (private key)"
echo "   Then restart: docker-compose restart mcp-frontend"
echo ""
