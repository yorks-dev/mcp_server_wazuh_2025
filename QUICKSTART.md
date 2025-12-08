# Quick Start Guide

## Installation & Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start the server:**
```bash
python start_server.py
```

Or manually:
```bash
cd mcp_server_wazuh_2025-main
python -m app.main
```

## Testing

Server runs on: `http://localhost:8000`

**Test commands:**
```powershell
# Status check
(Invoke-WebRequest "http://localhost:8000/").Content

# Wazuh connection test (shows agents)
(Invoke-WebRequest "http://localhost:8000/test").Content

# Get all agents
(Invoke-WebRequest "http://localhost:8000/agents").Content
```

## Authentication Fix Applied ✅

The Wazuh API authentication has been fixed. See `AUTH_FIX_README.md` for details.

**Credentials configured:**
- Wazuh API: `wazuh` user at `https://10.21.236.157:55000`
- Auto-authenticates on startup with bearer token
- Token auto-refresh implemented

## Files Modified

- `app/wazuh_client.py` - Fixed HTTP Basic Auth
- `app/config.py` - Updated credentials
- `app/main.py` - Added startup auth & endpoints
- `start_server.py` - Convenience startup script
