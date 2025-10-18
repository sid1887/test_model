#!/bin/bash
set -e

echo "🚀 Starting Cumpair Web Service..."

# Get environment variables with defaults
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export HOST=${HOST:-0.0.0.0}

echo "📝 Configuration:"
echo "   - Port: $PORT"
echo "   - Workers: $WORKERS"
echo "   - Host: $HOST"

# Wait for database
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Waiting for database..."
    timeout 30 bash -c 'until pg_isready -h postgres -p 5432; do sleep 1; done' || echo "⚠️  Database not ready, continuing anyway"
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    echo "⏳ Waiting for Redis..."
    timeout 30 bash -c 'until redis-cli -h redis ping 2>/dev/null; do sleep 1; done' || echo "⚠️  Redis not ready, continuing anyway"
fi

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migrations failed or not configured"
fi

# Start the application
echo "✅ Starting Uvicorn server on $HOST:$PORT with $WORKERS workers..."
exec uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info \
    --access-log \
    --use-colors
