#!/bin/bash
# Enhanced healthcheck script that adapts to different services

# Log message
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - HEALTHCHECK: $1"
}

# Retry mechanism
retry() {
    local retries=$1
    local delay=$2
    shift 2
    local count=0
    until "$@"; do
        exit_code=$?
        count=$((count + 1))
        if [ $count -lt $retries ]; then
            log "Command failed. Attempt $count/$retries. Retrying in ${delay}s..."
            sleep $delay
        else
            log "Command failed after $count attempts."
            return $exit_code
        fi
    done
    return 0
}

# Check FastAPI/web endpoints
check_web_endpoints() {
    # Try health endpoint
    if curl -f -s http://localhost:8000/api/v1/health 2>/dev/null; then
        log "Health endpoint is available"
        return 0
    fi
    
    # Try docs endpoint
    if curl -f -s http://localhost:8000/docs 2>/dev/null; then
        log "Docs endpoint is available"
        return 0
    fi
    
    # Try root endpoint
    if curl -f -s http://localhost:8000/ 2>/dev/null; then
        log "Root endpoint is available"
        return 0
    fi
    
    log "All HTTP endpoints failed"
    return 1
}

# Check if critical processes are running
check_processes() {
    if pgrep -f "uvicorn\|gunicorn\|fastapi" > /dev/null; then
        log "Web server process is running"
        return 0
    elif pgrep -f "celery worker" > /dev/null; then
        log "Celery worker process is running"
        return 0
    elif pgrep -f "celery flower" > /dev/null; then
        log "Celery flower process is running"
        return 0
    elif pgrep -f "python" > /dev/null; then
        log "Python process is running"
        return 0
    else
        log "No critical processes found running"
        return 1
    fi
}

# Execute the healthcheck with retries
log "Starting healthcheck..."

# First try HTTP endpoints
if retry 3 2 check_web_endpoints; then
    exit 0
fi

# If HTTP fails, check processes
if retry 2 1 check_processes; then
    log "Process check succeeded, but HTTP check failed"
    exit 0
else
    log "Service is unhealthy - both HTTP and process checks failed"
    exit 1
fi
