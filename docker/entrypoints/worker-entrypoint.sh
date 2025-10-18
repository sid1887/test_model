#!/bin/bash
set -e

echo "👷 Starting Celery Worker..."

# Get environment variables with defaults
export CONCURRENCY=${CELERY_CONCURRENCY:-2}
export LOG_LEVEL=${CELERY_LOG_LEVEL:-info}

echo "📝 Configuration:"
echo "   - Concurrency: $CONCURRENCY"
echo "   - Log Level: $LOG_LEVEL"

# Wait for Redis (Celery broker)
if [ -n "$REDIS_URL" ]; then
    echo "⏳ Waiting for Redis..."
    timeout 30 bash -c 'until redis-cli -h redis ping 2>/dev/null; do sleep 1; done' || echo "⚠️  Redis not ready, continuing anyway"
fi

# Start Celery worker
echo "✅ Starting Celery worker..."
exec celery -A app.worker worker \
    --loglevel="$LOG_LEVEL" \
    --concurrency="$CONCURRENCY" \
    --max-tasks-per-child=100 \
    --time-limit=300 \
    --soft-time-limit=240
