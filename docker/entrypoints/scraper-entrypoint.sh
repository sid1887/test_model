#!/bin/sh
set -e

echo "🕷️  Starting Scraper Service..."

# Get environment variables with defaults
export PORT=${PORT:-3001}
export NODE_ENV=${NODE_ENV:-production}

echo "📝 Configuration:"
echo "   - Port: $PORT"
echo "   - Node Environment: $NODE_ENV"

# Wait for Redis
if [ -n "$REDIS_URL" ] || [ -n "$REDIS_HOST" ]; then
    REDIS_HOST=${REDIS_HOST:-redis}
    echo "⏳ Waiting for Redis at $REDIS_HOST..."
    timeout 30 sh -c "until nc -z $REDIS_HOST 6379 2>/dev/null; do sleep 1; done" || echo "⚠️  Redis not ready, continuing anyway"
fi

# Start the scraper service
echo "✅ Starting Node.js scraper service on port $PORT..."
cd /app
exec node /app/server.js
