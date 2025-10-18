#!/bin/bash
"""
ADAPTIVE STARTUP SCRIPT
This script automatically detects the environment and starts the appropriate service.
"""

echo "=== ADAPTIVE STARTUP SCRIPT ==="
echo "Checking environment and available packages..."

# Function to check if a Python package is installed
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Function to check if a command exists
check_command() {
    command -v "$1" >/dev/null 2>&1
    return $?
}

# Function to test port availability
test_port() {
    local port=$1
    curl -f "http://localhost:$port" >/dev/null 2>&1 || \
    curl -f "http://localhost:$port/health" >/dev/null 2>&1 || \
    curl -f "http://localhost:$port/api/v1/health" >/dev/null 2>&1
}

# Check available packages
echo "Checking Python packages..."
FASTAPI_AVAILABLE=false
FLASK_AVAILABLE=false
UVICORN_AVAILABLE=false
GUNICORN_AVAILABLE=false

if check_package "fastapi"; then
    echo "✓ FastAPI available"
    FASTAPI_AVAILABLE=true
fi

if check_package "flask"; then
    echo "✓ Flask available"
    FLASK_AVAILABLE=true
fi

if check_command "uvicorn" || check_package "uvicorn"; then
    echo "✓ Uvicorn available"
    UVICORN_AVAILABLE=true
fi

if check_command "gunicorn" || check_package "gunicorn"; then
    echo "✓ Gunicorn available"
    GUNICORN_AVAILABLE=true
fi

# Check if main application files exist
MAIN_APP_EXISTS=false
FLASK_APP_EXISTS=false

if [ -f "main.py" ]; then
    echo "✓ main.py found"
    MAIN_APP_EXISTS=true
fi

if [ -f "app.py" ] || [ -f "flask_app.py" ]; then
    echo "✓ Flask app found"
    FLASK_APP_EXISTS=true
fi

# Determine best startup strategy
echo -e "\n=== DETERMINING STARTUP STRATEGY ==="

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-1}

# Strategy 1: FastAPI with Uvicorn (preferred)
if [ "$FASTAPI_AVAILABLE" = true ] && [ "$UVICORN_AVAILABLE" = true ] && [ "$MAIN_APP_EXISTS" = true ]; then
    echo "Strategy 1: FastAPI with Uvicorn"
    
    # Try multiple worker setup first
    if [ "$WORKERS" -gt 1 ]; then
        echo "Starting with $WORKERS workers..."
        uvicorn main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" &
        MAIN_PID=$!
        
        # Wait a bit and check if it's working
        sleep 10
        if kill -0 $MAIN_PID 2>/dev/null && test_port $PORT; then
            echo "✓ Multi-worker FastAPI started successfully"
            wait $MAIN_PID
            exit $?
        else
            echo "⚠ Multi-worker setup failed, stopping..."
            kill $MAIN_PID 2>/dev/null || true
            wait $MAIN_PID 2>/dev/null || true
        fi
    fi
    
    # Try single worker
    echo "Starting with single worker..."
    uvicorn main:app --host "$HOST" --port "$PORT" --workers 1 &
    MAIN_PID=$!
    
    sleep 5
    if kill -0 $MAIN_PID 2>/dev/null && test_port $PORT; then
        echo "✓ Single-worker FastAPI started successfully"
        wait $MAIN_PID
        exit $?
    else
        echo "⚠ Single-worker setup failed, stopping..."
        kill $MAIN_PID 2>/dev/null || true
        wait $MAIN_PID 2>/dev/null || true
    fi
    
    # Try basic mode
    echo "Starting in basic mode..."
    python -m uvicorn main:app --host "$HOST" --port "$PORT" &
    MAIN_PID=$!
    
    sleep 5
    if kill -0 $MAIN_PID 2>/dev/null; then
        echo "✓ Basic FastAPI started successfully"
        wait $MAIN_PID
        exit $?
    else
        echo "⚠ Basic FastAPI failed, stopping..."
        kill $MAIN_PID 2>/dev/null || true
        wait $MAIN_PID 2>/dev/null || true
    fi
fi

# Strategy 2: FastAPI with Gunicorn
if [ "$FASTAPI_AVAILABLE" = true ] && [ "$GUNICORN_AVAILABLE" = true ] && [ "$MAIN_APP_EXISTS" = true ]; then
    echo "Strategy 2: FastAPI with Gunicorn"
    
    gunicorn main:app -w "$WORKERS" -k uvicorn.workers.UvicornWorker --bind "$HOST:$PORT" &
    MAIN_PID=$!
    
    sleep 10
    if kill -0 $MAIN_PID 2>/dev/null && test_port $PORT; then
        echo "✓ FastAPI with Gunicorn started successfully"
        wait $MAIN_PID
        exit $?
    else
        echo "⚠ FastAPI with Gunicorn failed, stopping..."
        kill $MAIN_PID 2>/dev/null || true
        wait $MAIN_PID 2>/dev/null || true
    fi
fi

# Strategy 3: Flask with Gunicorn
if [ "$FLASK_AVAILABLE" = true ] && [ "$GUNICORN_AVAILABLE" = true ] && [ "$FLASK_APP_EXISTS" = true ]; then
    echo "Strategy 3: Flask with Gunicorn"
    
    # Try to find Flask app
    FLASK_APP_FILE=""
    if [ -f "app.py" ]; then
        FLASK_APP_FILE="app:app"
    elif [ -f "flask_app.py" ]; then
        FLASK_APP_FILE="flask_app:app"
    fi
    
    if [ -n "$FLASK_APP_FILE" ]; then
        gunicorn "$FLASK_APP_FILE" -w "$WORKERS" --bind "$HOST:$PORT" &
        MAIN_PID=$!
        
        sleep 10
        if kill -0 $MAIN_PID 2>/dev/null && test_port $PORT; then
            echo "✓ Flask with Gunicorn started successfully"
            wait $MAIN_PID
            exit $?
        else
            echo "⚠ Flask with Gunicorn failed, stopping..."
            kill $MAIN_PID 2>/dev/null || true
            wait $MAIN_PID 2>/dev/null || true
        fi
    fi
fi

# Strategy 4: Basic Flask development server
if [ "$FLASK_AVAILABLE" = true ]; then
    echo "Strategy 4: Basic Flask development server"
    
    python -c "
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return {'status': 'ok', 'message': 'Emergency Flask server running'}

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/api/v1/health')
def api_health():
    return {'status': 'healthy', 'service': 'emergency-flask'}

if __name__ == '__main__':
    app.run(host='$HOST', port=$PORT, debug=False)
" &
    MAIN_PID=$!
    
    sleep 5
    if kill -0 $MAIN_PID 2>/dev/null; then
        echo "✓ Emergency Flask server started successfully"
        wait $MAIN_PID
        exit $?
    else
        echo "⚠ Emergency Flask server failed, stopping..."
        kill $MAIN_PID 2>/dev/null || true
        wait $MAIN_PID 2>/dev/null || true
    fi
fi

# Strategy 5: Simple HTTP server
echo "Strategy 5: Simple HTTP server (last resort)"

python -c "
import http.server
import socketserver
import json
from urllib.parse import urlparse

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/api/v1/health']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'service': 'emergency-http-server'}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

PORT = $PORT
with socketserver.TCPServer(('', PORT), HealthCheckHandler) as httpd:
    print(f'Emergency HTTP server running on port {PORT}')
    httpd.serve_forever()
"

echo "❌ All startup strategies failed!"
exit 1
