#!/bin/bash

echo "🔄 Restarting Discord Bot..."

# Stop the current containers
echo "⏹️  Stopping containers..."
docker-compose down

# Remove the container to force a rebuild
echo "🗑️  Removing old container..."
docker-compose rm -f rewards-platform

# Rebuild and start
echo "🔨 Rebuilding and starting..."
docker-compose up --build -d

echo "✅ Bot restart complete!"
echo "📋 Check the logs with: docker-compose logs -f rewards-platform"