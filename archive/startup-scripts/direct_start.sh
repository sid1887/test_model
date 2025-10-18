#!/bin/bash
set -e

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - STARTUP: $1"
}

log "Starting direct package installation and web service..."

# Directly install critical packages
log "Installing critical packages..."
python -m pip install asyncpg==0.29.0 aiofiles==23.2.0 python-dotenv==1.0.0

# Check environment variables and set defaults
if [ -z "$PORT" ]; then
    export PORT=8000
    log "Setting default PORT to $PORT"
fi

if [ -z "$WORKERS" ]; then
    export WORKERS=1
    log "Setting default WORKERS to $WORKERS"
fi

# Start the web service directly
log "Starting web service..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS
