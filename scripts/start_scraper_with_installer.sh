#!/bin/bash
set -e

echo "Starting Scraper Service (Node.js)"

# Check if package.json exists and install npm packages if needed
if [ -f "/app/package.json" ]; then
    echo "Installing npm packages..."
    cd /app
    npm install --production
fi

# Set environment variables
export NODE_ENV=production
export PORT=3001
export REDIS_HOST=redis
export REDIS_PORT=6379

echo "Starting scraper service..."
cd /app
exec npm start
