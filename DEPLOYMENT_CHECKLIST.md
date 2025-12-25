# 🚀 Deployment Checklist - Multi-Wazuh Support

This guide ensures your MCP server works with **ANY** Wazuh multi-node Docker installation.

## ✅ Pre-Deployment Checklist

### 1. Find Your Wazuh Network Name

```bash
# List all Docker networks
docker network ls

# Find the Wazuh network (look for patterns like):
# - multi-node_default
# - wazuh-docker_default
# - wazuh_default
# - wazuh
```

**Example output:**
```
NETWORK ID     NAME                 DRIVER    SCOPE
29e89bb6224b   multi-node_default   bridge    local
```

### 2. Find Your Wazuh Container Names

```bash
# List all Wazuh containers
docker ps --format "table {{.Names}}\t{{.Networks}}" | grep -E "wazuh|indexer|master"
```

**Example output:**
```
multi-node-wazuh.master-1      multi-node_default
multi-node-wazuh1.indexer-1    multi-node_default
multi-node-wazuh2.indexer-1    multi-node_default
multi-node-wazuh3.indexer-1    multi-node_default
```

### 3. Configure Your Environment

```bash
# Copy the example file
cp .env.example .env

# Edit the configuration
nano .env
```

**Update these values with YOUR actual names:**

```bash
# ═══════════════════════════════════════════════════════════════
# 🎯 STEP 1: Set your Wazuh Docker network name
# ═══════════════════════════════════════════════════════════════
WAZUH_NETWORK=multi-node_default  # ← Change to YOUR network name

# ═══════════════════════════════════════════════════════════════
# 🎯 STEP 2: Set your Wazuh Manager container name
# ═══════════════════════════════════════════════════════════════
WAZUH_API_HOST=https://multi-node-wazuh.master-1  # ← Change to YOUR manager name
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=your-password

# ═══════════════════════════════════════════════════════════════
# 🎯 STEP 3: Set your Wazuh Indexer container name
# ═══════════════════════════════════════════════════════════════
WAZUH_INDEXER_HOST=https://multi-node-wazuh1.indexer-1  # ← Change to YOUR indexer name
WAZUH_INDEXER_PORT=9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=your-password

# OpenSearch (should match indexer)
OPENSEARCH_HOST=https://multi-node-wazuh1.indexer-1:9200  # ← Same as indexer
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-password

# ═══════════════════════════════════════════════════════════════
# 🎯 STEP 4: Add your OpenAI API key
# ═══════════════════════════════════════════════════════════════
OPENAI_API_KEY=sk-proj-your-key-here

# SSL (set to false for self-signed certs)
WAZUH_VERIFY_SSL=false
```

### 4. Verify No Port Conflicts

```bash
# Check if ports 8000, 8080, 8443 are available
lsof -i :8000 2>/dev/null && echo "❌ Port 8000 in use" || echo "✅ Port 8000 available"
lsof -i :8080 2>/dev/null && echo "❌ Port 8080 in use" || echo "✅ Port 8080 available"
lsof -i :8443 2>/dev/null && echo "❌ Port 8443 in use" || echo "✅ Port 8443 available"
```

**If ports are in use**, you can change them in `docker-compose.yml`:

```yaml
services:
  mcp-server:
    ports:
      - "8001:8000"  # Change 8000 → 8001
  
  mcp-frontend:
    ports:
      - "8081:80"    # Change 8080 → 8081
      - "8444:443"   # Change 8443 → 8444
```

---

## 🚀 Deployment

### Option 1: Automated Script (Recommended)

```bash
./scripts/docker-deploy.sh
```

This will:
- ✅ Validate network exists
- ✅ Build containers
- ✅ Start services
- ✅ Test connectivity
- ✅ Show access URLs

### Option 2: Manual Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## ✅ Verification Tests

### 1. Check Container Status

```bash
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# wazuh-mcp-server    Up (healthy)        0.0.0.0:8000->8000/tcp
# wazuh-mcp-frontend  Up (healthy)        0.0.0.0:8080->80/tcp, 0.0.0.0:8443->443/tcp
```

### 2. Verify Network Connectivity

```bash
# Check all containers are on the same network
docker network inspect multi-node_default | grep -E "Name|IPv4"

# Should show both MCP containers and Wazuh containers
```

### 3. Test Backend Health

```bash
# From host
curl http://localhost:8000/health

# Expected: {"mcp_server":"running","wazuh_api":true,"wazuh_indexer":true,...}
```

### 4. Test Container-to-Container Communication

```bash
# From MCP server → Wazuh Manager
docker exec wazuh-mcp-server curl -k https://multi-node-wazuh.master-1:55000

# From MCP server → Wazuh Indexer
docker exec wazuh-mcp-server curl -k https://multi-node-wazuh1.indexer-1:9200

# From Frontend → Backend
docker exec wazuh-mcp-frontend curl -s http://mcp-server:8000/health
```

### 5. Test Full Stack

```bash
# Test HTTPS frontend
curl -k https://localhost:8443

# Test API proxy
curl -k https://localhost:8443/api/health
```

---

## 🔧 Common Scenarios

### Scenario 1: Different Wazuh Installation Name

**Your Wazuh uses prefix `prod-wazuh-` instead of `multi-node-`**

```bash
# In .env:
WAZUH_NETWORK=prod-wazuh_default
WAZUH_API_HOST=https://prod-wazuh.master-1
WAZUH_INDEXER_HOST=https://prod-wazuh1.indexer-1
OPENSEARCH_HOST=https://prod-wazuh1.indexer-1:9200
```

### Scenario 2: Single-Node Wazuh

**Your Wazuh is single-node with different names**

```bash
# In .env:
WAZUH_NETWORK=wazuh-docker_default
WAZUH_API_HOST=https://wazuh-manager
WAZUH_INDEXER_HOST=https://wazuh-indexer
OPENSEARCH_HOST=https://wazuh-indexer:9200
```

### Scenario 3: Multiple Wazuh Environments

**You have dev, staging, and prod Wazuh setups**

Create separate `.env` files:

```bash
.env.dev       # WAZUH_NETWORK=dev-wazuh_default
.env.staging   # WAZUH_NETWORK=staging-wazuh_default
.env.prod      # WAZUH_NETWORK=prod-wazuh_default

# Deploy to specific environment:
cp .env.prod .env
docker-compose up -d
```

### Scenario 4: Port Conflicts

**Ports already in use by other services**

```yaml
# docker-compose.yml
services:
  mcp-server:
    ports:
      - "8001:8000"  # Use different external port
  
  mcp-frontend:
    ports:
      - "8081:80"
      - "9443:443"   # Use 9443 instead of 8443
```

Then access at: `https://localhost:9443`

---

## 🐛 Troubleshooting

### Problem: Network not found

```
ERROR: Network multi-node_default declared as external, but could not be found
```

**Solution:**
```bash
# Find the correct network name
docker network ls | grep wazuh

# Update .env with the correct name
WAZUH_NETWORK=your-actual-network-name
```

### Problem: Cannot connect to Wazuh services

**Solution:**
```bash
# Verify containers are on same network
docker network inspect your-network-name

# Verify Wazuh containers are running
docker ps | grep wazuh

# Test DNS resolution
docker exec wazuh-mcp-server ping -c 2 multi-node-wazuh.master-1

# Check container names match
docker ps --format "{{.Names}}" | grep wazuh
# Update .env with actual names
```

### Problem: Backend keeps restarting

```bash
# Check logs
docker-compose logs mcp-server

# Common issues:
# 1. Missing environment variables → Check .env file
# 2. Wrong container names → Update WAZUH_API_HOST and WAZUH_INDEXER_HOST
# 3. Network mismatch → Update WAZUH_NETWORK
```

### Problem: Frontend shows "Server Offline"

```bash
# Test backend directly
curl http://localhost:8000/health

# Test from frontend container
docker exec wazuh-mcp-frontend curl http://mcp-server:8000/health

# If backend test works but frontend doesn't:
# - Check nginx config
# - Restart frontend: docker-compose restart mcp-frontend
```

---

## 📚 Quick Reference

| Configuration | Where to Set | Example Value |
|--------------|-------------|---------------|
| Network Name | `.env` → `WAZUH_NETWORK` | `multi-node_default` |
| Manager Name | `.env` → `WAZUH_API_HOST` | `https://multi-node-wazuh.master-1` |
| Indexer Name | `.env` → `WAZUH_INDEXER_HOST` | `https://multi-node-wazuh1.indexer-1` |
| Ports | `docker-compose.yml` → `ports` | `8000`, `8080`, `8443` |

### Quick Commands

```bash
# Find network:  docker network ls
# Find containers: docker ps --format "{{.Names}}"
# Check config:  docker-compose config
# Deploy:        ./scripts/docker-deploy.sh
# Stop:          docker-compose down
# Logs:          docker-compose logs -f
# Restart:       docker-compose restart
# Rebuild:       docker-compose up -d --build
```

---

## ✅ Final Verification Checklist

Before considering deployment complete:

- [ ] `.env` file configured with YOUR actual values
- [ ] `WAZUH_NETWORK` matches your Docker network
- [ ] `WAZUH_API_HOST` matches your manager container name
- [ ] `WAZUH_INDEXER_HOST` matches your indexer container name
- [ ] No port conflicts (8000, 8080, 8443)
- [ ] `docker-compose ps` shows both containers as "healthy"
- [ ] `curl http://localhost:8000/health` returns success
- [ ] `docker network inspect <network>` shows all containers
- [ ] Frontend accessible at `https://localhost:8443`
- [ ] Can query "Show me all agents" successfully

---

**🎉 You're ready to deploy alongside ANY Wazuh multi-node installation!**

The configuration is now fully flexible and will work with any Docker network and container naming scheme.
