#!/bin/bash

echo "🔄 Rebuilding Docker images..."

# Rebuild specific service or all
if [ -z "$1" ]; then
    docker-compose build --no-cache
else
    docker-compose build --no-cache "$1"
fi

echo ""
echo "✅ Rebuild complete"
echo ""
echo "Restart services:"
echo "  docker-compose up -d"
