#!/bin/bash

echo "Stopping SSH tunnel..."

if [ -f .ssh_tunnel.pid ]; then
    TUNNEL_PID=$(cat .ssh_tunnel.pid)
    if ps -p $TUNNEL_PID > /dev/null 2>&1; then
        kill $TUNNEL_PID
        echo "✓ SSH tunnel stopped (PID: $TUNNEL_PID)"
    else
        echo "⚠ Tunnel process not found"
    fi
    rm .ssh_tunnel.pid
else
    # Try to find and kill any ssh tunnel on port 9200
    TUNNEL_PID=$(lsof -ti:9200)
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID
        echo "✓ SSH tunnel stopped (PID: $TUNNEL_PID)"
    else
        echo "⚠ No tunnel found"
    fi
fi

# Restore original .env if backup exists
if [ -f .env.backup ]; then
    echo "Do you want to restore original .env? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        mv .env.backup .env
        echo "✓ Original .env restored"
    fi
fi

echo "Done!"
