#!/bin/bash
set -e

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - STARTUP: $1"
}

log "Starting intelligent service detection and initialization..."

# Function to check if a Python module can be imported
check_module() {
    python -c "import $1" 2>/dev/null && echo "✓ $1 available" || echo "⚠ $1 not available"
}

# Run automatic package installation
if [ -f "/app/auto_install_packages.py" ]; then
    log "Running automatic package installer..."
    python /app/auto_install_packages.py
    log "Package installation completed"
fi

# Verify critical modules
log "Checking critical modules..."
check_module fastapi
check_module uvicorn
check_module pydantic
check_module sqlalchemy
check_module celery
check_module redis

# Check environment variables and set defaults
if [ -z "$PORT" ]; then
    export PORT=8000
    log "Setting default PORT to $PORT"
fi

if [ -z "$WORKERS" ]; then
    export WORKERS=1
    log "Setting default WORKERS to $WORKERS"
fi

# Detect service type from environment variable
if [ ! -z "$SERVICE_TYPE" ]; then
    log "Service type explicitly set to: $SERVICE_TYPE"
    
    case "$SERVICE_TYPE" in
        "web")
            log "Starting web service..."
            exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS
            ;;
        "worker")
            log "Starting Celery worker..."
            exec celery -A app.worker worker --loglevel=info
            ;;
        "flower")
            log "Starting Celery flower..."
            exec celery -A app.worker flower --port=5555
            ;;
        "scraper")
            log "Starting scraper service..."
            if [ -f "scraper.py" ]; then
                exec python scraper.py
            elif [ -f "app.js" ]; then
                exec node app.js
            else
                log "ERROR: No scraper entrypoint found!"
                exit 1
            fi
            ;;
        *)
            log "Unknown service type: $SERVICE_TYPE, falling back to auto-detection"
            ;;
    esac
fi

# Auto-detect service type based on available files and modules
log "Auto-detecting service type..."

if [ -f "main.py" ] && python -c "import fastapi" 2>/dev/null; then
    log "Detected FastAPI application"
    log "Starting with uvicorn..."
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS
elif [ -f "app.py" ] && python -c "import flask" 2>/dev/null; then
    log "Detected Flask application"
    log "Starting with gunicorn..."
    exec gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS app:app
elif [ -f "manage.py" ]; then
    log "Detected Django application"
    exec python manage.py runserver 0.0.0.0:$PORT
elif python -c "import celery" 2>/dev/null && [ -d "app" ] && [ -f "app/worker.py" ]; then
    log "Detected Celery worker"
    exec celery -A app.worker worker --loglevel=info
elif [ -f "app.js" ] || [ -f "index.js" ]; then
    log "Detected Node.js application"
    npm_package=$(find . -maxdepth 1 -name "package.json" | wc -l)
    if [ "$npm_package" -gt 0 ]; then
        log "Installing Node.js dependencies..."
        npm install --production
    fi
    if [ -f "app.js" ]; then
        exec node app.js
    else
        exec node index.js
    fi
else
    log "No specific framework detected, trying generic startup..."
    if [ -f "main.py" ]; then
        exec python main.py
    elif [ -f "app.py" ]; then
        exec python app.py
    else
        log "No application entry point found, starting shell"
        exec /bin/bash
    fi
fi
