#!/bin/bash

echo "=========================================="
echo "Wazuh MCP Server - Dev Environment Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# VM_IP="10.21.236.157"
# VM_USER="hpotwazuh"

VM_IP="YOUR VM IP"
VM_USER="YOUR VM USER"

echo -e "\n${YELLOW}Setting up SSH tunnel to Wazuh Indexer...${NC}"
echo "This will forward VM's localhost:9200 to your Mac's localhost:9200"
echo ""

# Check if tunnel already exists
if lsof -Pi :9200 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Port 9200 is already in use. Checking if it's our tunnel...${NC}"
    EXISTING_PID=$(lsof -ti:9200)
    echo "Killing existing process on port 9200 (PID: $EXISTING_PID)"
    kill $EXISTING_PID 2>/dev/null || true
    sleep 2
fi

# Create SSH tunnel in background
echo -e "${GREEN}Creating SSH tunnel...${NC}"
ssh -f -N -L 9200:localhost:9200 ${VM_USER}@${VM_IP}

if [ $? -eq 0 ]; then
    TUNNEL_PID=$(lsof -ti:9200)
    echo -e "${GREEN}✓ SSH tunnel established (PID: $TUNNEL_PID)${NC}"
    echo ""
    echo "Tunnel details:"
    echo "  Local:  https://localhost:9200"
    echo "  Remote: ${VM_USER}@${VM_IP}:9200"
    echo ""
    
    # Test the tunnel
    echo -e "${YELLOW}Testing tunnel connection...${NC}"
    if curl -k -s -u "admin:NxFdeGIYQMtZ8077IQ?qJRABNpPsPYoa" \
        https://localhost:9200/_cluster/health?pretty > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Tunnel is working!${NC}"
        
        # Show cluster info
        echo ""
        echo "Cluster status:"
        curl -k -s -u "admin:NxFdeGIYQMtZ8077IQ?qJRABNpPsPYoa" \
            https://localhost:9200/_cluster/health?pretty | grep -E "cluster_name|status|number_of"
    else
        echo -e "${RED}✗ Tunnel connection test failed${NC}"
        exit 1
    fi
    
    # Update .env file
    echo ""
    echo -e "${YELLOW}Updating .env for development...${NC}"
    
    # Backup original .env
    if [ ! -f .env.backup ]; then
        cp .env .env.backup
        echo "✓ Backed up .env to .env.backup"
    else
        echo "✓ .env.backup already exists"
    fi
    
    # Update hosts to use localhost for dev
    sed -i '' "s|OPENSEARCH_HOST=.*|OPENSEARCH_HOST=https://localhost:9200|" .env
    sed -i '' "s|WAZUH_INDEXER_HOST=.*|WAZUH_INDEXER_HOST=https://localhost:9200|" .env
    
    echo -e "${GREEN}✓ .env updated for dev environment${NC}"
    
    # Save tunnel PID for cleanup
    echo $TUNNEL_PID > .ssh_tunnel.pid
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Dev environment ready!${NC}"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: ./run_tests.sh"
    echo "  2. Start server: source .venv/bin/activate && uvicorn app.main:app --reload"
    echo ""
    echo "To stop the tunnel:"
    echo "  ./stop_dev_tunnel.sh"
    echo ""
    
else
    echo -e "${RED}✗ Failed to create SSH tunnel${NC}"
    echo "Please check:"
    echo "  1. SSH access to ${VM_USER}@${VM_IP}"
    echo "  2. SSH keys are set up"
    echo "  3. VM is reachable"
    exit 1
fi
