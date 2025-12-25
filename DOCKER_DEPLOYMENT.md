# Docker Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Wazuh already running on localhost (ports 443, 55000, 9200)
- OpenAI API key

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required configuration:
```bash
# Wazuh credentials (from your Wazuh setup)
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=your-password

# OpenSearch credentials (from your Wazuh setup)
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-password

# OpenAI API key
OPENAI_API_KEY=sk-proj-your-key-here
```

### 2. Deploy

```bash
# Make scripts executable
chmod +x scripts/docker-*.sh

# Deploy with one command
./scripts/docker-deploy.sh
```

### 3. Access

- **Wazuh Dashboard**: https://localhost (existing)
- **MCP Frontend**: https://localhost:8443 (new)
- **MCP API**: http://localhost:8000 (new)
- **API Docs**: http://localhost:8000/docs

---

## 📊 Port Configuration

### Wazuh Services (Already Running)
- `443` - Wazuh Dashboard (HTTPS)
- `80` - Wazuh Dashboard (HTTP)
- `55000` - Wazuh Manager API
- `9200` - Wazuh Indexer (OpenSearch)
- `1514` - Wazuh Agent communication
- `1515` - Wazuh Agent enrollment

### MCP Services (New)
- `8000` - MCP API (HTTP)
- `8080` - MCP Frontend (HTTP - redirects to 8443)
- `8443` - MCP Frontend (HTTPS) ⭐

**No port conflicts!** All services run side by side.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                         │
│                                                         │
│  Port 443  → Wazuh Dashboard                           │
│  Port 55000 → Wazuh Manager API                        │
│  Port 9200  → Wazuh Indexer                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Docker: mcp-server (network_mode: host)         │  │
│  │   → Accesses localhost:55000 (Wazuh API)        │  │
│  │   → Accesses localhost:9200 (Indexer)           │  │
│  │   → Exposes port 8000 (API)                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Docker: mcp-frontend (Nginx + SSL)              │  │
│  │   → Port 8080 (HTTP)                            │  │
│  │   → Port 8443 (HTTPS) ⭐                        │  │
│  │   → Proxies /api/ to localhost:8000             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Management Commands

### View Logs
```bash
# All services
./scripts/docker-logs.sh

# Specific service
./scripts/docker-logs.sh mcp-server
./scripts/docker-logs.sh mcp-frontend

# Or directly
docker-compose logs -f
docker-compose logs -f mcp-server
```

### Stop Services
```bash
./scripts/docker-stop.sh

# Or directly
docker-compose down
```

### Restart Services
```bash
docker-compose restart

# Restart specific service
docker-compose restart mcp-server
docker-compose restart mcp-frontend
```

### Rebuild After Code Changes
```bash
./scripts/docker-rebuild.sh

# Or rebuild and restart
docker-compose build && docker-compose up -d
```

### Check Status
```bash
docker-compose ps

# Detailed container info
docker-compose ps -a
```

---

## 🔒 SSL Certificates

### Development (Default)
Self-signed certificates are automatically generated. Browser will show security warning - this is expected.

**To access**:
1. Go to https://localhost:8443
2. Click "Advanced" or "Show Details"
3. Click "Proceed to localhost" or "Accept Risk"

### Production

Place real SSL certificates in `ssl/` directory:

```bash
# Create SSL directory
mkdir -p ssl

# Option 1: Let's Encrypt
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/cert.key

# Option 2: Manual certificates
# Copy your certificates to:
# - ssl/cert.crt (certificate + chain)
# - ssl/cert.key (private key)

# Set permissions
chmod 644 ssl/cert.crt
chmod 600 ssl/cert.key

# Restart frontend to use new certificates
docker-compose restart mcp-frontend
```

---

## 🧪 Testing

### Test API Health
```bash
curl http://localhost:8000/health
```

### Test Frontend
```bash
# HTTP (should redirect)
curl -I http://localhost:8080/

# HTTPS
curl -k -I https://localhost:8443/
```

### Test API Through Frontend Proxy
```bash
curl -k https://localhost:8443/api/health
```

### Test Natural Language Query
```bash
curl -X POST http://localhost:8000/query/nl \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all agents"}'
```

---

## 🔍 Troubleshooting

### Port Already in Use

**Problem**: Port 8000 or 8443 already in use

**Solution**:
```bash
# Find what's using the port
lsof -i :8000
lsof -i :8443

# Stop the process or change port in docker-compose.yml
```

### Container Won't Start

**Check logs**:
```bash
docker-compose logs mcp-server
docker-compose logs mcp-frontend
```

**Common issues**:
1. Missing `.env` file → Copy from `.env.example`
2. Wrong credentials → Check Wazuh passwords
3. Port conflicts → See above

### API Can't Connect to Wazuh

**Problem**: 401 Unauthorized or Connection Refused

**Solution**:
```bash
# Test Wazuh API from host
curl -k -u wazuh-wui:password https://localhost:55000/

# Check if Wazuh is running
docker ps | grep wazuh

# Verify credentials in .env
cat .env | grep WAZUH
```

### Frontend Shows 502 Bad Gateway

**Problem**: Frontend can't reach backend API

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs mcp-frontend

# Restart services
docker-compose restart
```

### SSL Certificate Warning

This is **expected** with self-signed certificates in development.

**To fix permanently**:
1. Get real SSL certificate (Let's Encrypt)
2. Place in `ssl/` directory
3. Restart frontend container

---

## 📝 Environment Variables

All configuration in `.env` file:

```bash
# Wazuh API (localhost since Wazuh is on same machine)
WAZUH_API_HOST=https://localhost
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=your-password

# Wazuh Indexer (localhost)
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASS=your-password

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# Optional
LOG_LEVEL=INFO
```

---

## 🔄 Updates

### Update MCP Server Code
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build mcp-server
docker-compose up -d mcp-server
```

### Update Frontend
```bash
# Make frontend changes
# Then rebuild
docker-compose build mcp-frontend
docker-compose up -d mcp-frontend
```

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Use real SSL certificates (not self-signed)
- [ ] Change default passwords in `.env`
- [ ] Set `LOG_LEVEL=WARNING` in production
- [ ] Configure proper CORS origins in `app/main.py`
- [ ] Enable firewall rules for ports 8000, 8443
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Monitor container health
- [ ] Set up alerting for service failures

---

## 📚 Additional Resources

- [Main Documentation](DOCUMENTATION.md)
- [Quick Start Guide](QUICK_START.md)
- [Project Summary](PROJECT_SUMMARY.txt)
- [API Documentation](http://localhost:8000/docs)

---

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify configuration: `cat .env`
3. Test connectivity: `curl http://localhost:8000/health`
4. Check Wazuh status: `docker ps | grep wazuh`

---

**Ready to deploy!** 🚀

Run: `./scripts/docker-deploy.sh`
