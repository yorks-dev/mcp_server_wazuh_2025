# Docker Network Setup Guide

## 🐳 Same-Host Deployment (No SSH Tunnels!)

Your MCP server will run in Docker **on the same machine** as your Wazuh deployment. All services communicate via Docker's internal network - no SSH tunnels required!

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Host Machine (Same as Wazuh)               │
│                                                         │
│   Docker Network: "wazuh"                              │
│   ┌───────────────────────────────────────────────┐    │
│   │  Existing Wazuh Services:                     │    │
│   │  • wazuh.manager     :55000                   │    │
│   │  • wazuh.indexer     :9200                    │    │
│   │  • wazuh.dashboard   :443                     │    │
│   ├───────────────────────────────────────────────┤    │
│   │  New MCP Services:                            │    │
│   │  • mcp-server        :8000  ←── NEW!         │    │
│   │  • mcp-frontend      :8443  ←── NEW!         │    │
│   └───────────────────────────────────────────────┘    │
│                                                         │
│  ✅ All communicate via Docker network (fast!)         │
│  ✅ No SSH tunnels (simpler, more secure)              │
│  ✅ Production-ready architecture                       │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Find Your Wazuh Network Name

```bash
# List Docker networks
docker network ls

# Common Wazuh network names:
# - wazuh
# - wazuh-docker_default
# - wazuh_default
# - wazuh-network
```

### 2. Update Configuration (If Needed)

If your Wazuh network has a different name, update `docker-compose.yml`:

```yaml
networks:
  wazuh-docker_default:  # Change to match your network name
    external: true
```

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

Update these values:
```bash
# Use Docker service names (not localhost!)
WAZUH_API_HOST=https://wazuh.manager
OPENSEARCH_HOST=https://wazuh.indexer:9200

# Add your credentials
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=your-password
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-password
OPENAI_API_KEY=sk-proj-your-key
```

### 4. Deploy

```bash
./scripts/docker-deploy.sh
```

This will:
- ✅ Check for Wazuh network
- ✅ Create network if needed
- ✅ Build Docker images
- ✅ Start containers
- ✅ Test connectivity
- ✅ Display access URLs

### 5. Access

- **Wazuh Dashboard**: https://localhost (port 443)
- **MCP Frontend**: https://localhost:8443 (port 8443)
- **MCP API**: http://localhost:8000 (port 8000)

---

## 🔍 Verification

### Check Network Connectivity

```bash
# List all containers on Wazuh network
docker network inspect wazuh

# Should show:
# - wazuh.manager
# - wazuh.indexer
# - wazuh.dashboard
# - wazuh-mcp-server     ✅
# - wazuh-mcp-frontend   ✅
```

### Test Container-to-Container Communication

```bash
# From MCP server, ping Wazuh Manager
docker exec wazuh-mcp-server ping -c 3 wazuh.manager

# Test Wazuh API connectivity
docker exec wazuh-mcp-server curl -k https://wazuh.manager:55000

# Test Indexer connectivity
docker exec wazuh-mcp-server curl -k https://wazuh.indexer:9200
```

### View Container Status

```bash
docker-compose ps

# All containers should be "Up" and "healthy"
```

---

## 🐛 Troubleshooting

### Cannot Connect to Wazuh Services

**Problem**: MCP server can't reach `wazuh.manager` or `wazuh.indexer`

**Solutions**:

1. **Check if containers are on the same network**:
   ```bash
   docker network inspect wazuh
   # Verify both MCP and Wazuh containers are listed
   ```

2. **Verify Wazuh services are running**:
   ```bash
   docker ps | grep wazuh
   # Should show wazuh.manager, wazuh.indexer, wazuh.dashboard
   ```

3. **Check service names**:
   ```bash
   # Your Wazuh might use different service names
   docker ps --format "table {{.Names}}\t{{.Networks}}"
   
   # Update .env with actual service names
   ```

4. **Test DNS resolution**:
   ```bash
   docker exec wazuh-mcp-server nslookup wazuh.manager
   # Should resolve to internal Docker IP
   ```

### Network Not Found

**Problem**: `ERROR: Network wazuh declared as external, but could not be found`

**Solution**:
```bash
# Option 1: Create the network
docker network create wazuh

# Option 2: Use your existing Wazuh network name
docker network ls
# Update docker-compose.yml with the correct name
```

### Port Already in Use

**Problem**: Port 8000 or 8443 already in use

**Solution**:
```bash
# Find what's using the port
lsof -i :8000
lsof -i :8443

# Option 1: Stop the service
docker-compose down

# Option 2: Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different external port
```

### Authentication Failed

**Problem**: 401 Unauthorized when accessing Wazuh

**Solution**:
```bash
# Verify credentials in .env
cat .env | grep WAZUH

# Test Wazuh API manually
docker exec wazuh-mcp-server curl -k -u wazuh-wui:password \
  https://wazuh.manager:55000/security/user/authenticate

# Check Wazuh logs
docker logs wazuh.manager
```

---

## 📊 Network Architecture Details

### Service Discovery

Docker's internal DNS automatically resolves service names:

| Service Name | Resolves To | Port |
|--------------|-------------|------|
| `wazuh.manager` | Internal Docker IP | 55000 |
| `wazuh.indexer` | Internal Docker IP | 9200 |
| `wazuh.dashboard` | Internal Docker IP | 443 |
| `mcp-server` | Internal Docker IP | 8000 |
| `mcp-frontend` | Internal Docker IP | 443 (internal) |

### Communication Flow

```
Frontend (Browser)
    ↓ HTTPS (8443)
mcp-frontend (Nginx)
    ↓ HTTP (internal Docker network)
mcp-server (FastAPI)
    ↓ HTTPS (internal Docker network)
    ├→ wazuh.manager:55000 (Wazuh API)
    └→ wazuh.indexer:9200 (OpenSearch)
```

### Security Benefits

✅ **No exposed tunnels** - All communication internal  
✅ **Network isolation** - Docker network segmentation  
✅ **Fast communication** - No SSH overhead  
✅ **Automatic DNS** - No IP address management  
✅ **Health checks** - Auto-restart on failure  

---

## 🔧 Advanced Configuration

### Using Different Network

If your Wazuh uses a different network name:

```yaml
# docker-compose.yml
networks:
  my-custom-wazuh-network:
    external: true
```

Update services:
```yaml
services:
  mcp-server:
    networks:
      - my-custom-wazuh-network
```

### Custom Service Names

If your Wazuh services have different names:

```bash
# Find actual service names
docker ps --format "{{.Names}}"

# Update .env
WAZUH_API_HOST=https://your-actual-wazuh-manager-name
OPENSEARCH_HOST=https://your-actual-indexer-name:9200
```

### Adding to Existing docker-compose

Instead of separate docker-compose.yml, you can add to your Wazuh compose file:

```yaml
# In your existing wazuh docker-compose.yml
services:
  # ... existing wazuh services ...
  
  mcp-server:
    build: ./mcp_server_wazuh_2025
    # ... rest of MCP config ...
  
  mcp-frontend:
    build: ./mcp_server_wazuh_2025/frontend
    # ... rest of frontend config ...
```

---

## 📚 Additional Resources

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)
- [Quick Reference](DOCKER_QUICK_REF.txt)
- [Main Documentation](DOCUMENTATION.md)

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] `docker network inspect wazuh` shows all containers
- [ ] `docker-compose ps` shows all containers as "healthy"
- [ ] `curl http://localhost:8000/health` returns healthy status
- [ ] `docker exec wazuh-mcp-server curl -k https://wazuh.manager:55000` succeeds
- [ ] Frontend accessible at https://localhost:8443
- [ ] Can query "Show me all agents" successfully
- [ ] No SSH tunnel scripts needed!

---

**🎉 Congratulations!** You're running a production-ready MCP server using Docker networking - no SSH tunnels required!
