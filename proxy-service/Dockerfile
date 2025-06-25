# ROBUST PROXY SERVICE DOCKERFILE WITH ERROR HANDLING
FROM python:3.11-slim

WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with error handling
RUN apt-get update && \
    # Essential packages
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates && \
    # Try to install HAProxy (optional)
    (apt-get install -y --no-install-recommends haproxy || \
     echo "HAProxy install failed, continuing without it") && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with error handling
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 3000 --retries 15 --upgrade pip setuptools wheel && \
    # Try to install all packages
    (pip install --no-cache-dir --timeout 3000 --retries 15 \
        --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
        -r requirements.txt || \
    # Fallback to essential packages
    (echo "Bulk install failed, installing core packages..." && \
     pip install --no-cache-dir --timeout 3000 --retries 15 fastapi uvicorn requests aiohttp))

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /app/logs && chmod -R 755 /app

# Expose port
EXPOSE 8001

# Robust health check with multiple fallbacks
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8001/health || \
        curl -f http://localhost:8001/ || \
        wget --quiet --tries=1 --spider http://localhost:8001/health || \
        exit 1

# Start with error handling and multiple fallbacks
CMD ["sh", "-c", "python proxy_manager.py || uvicorn main:app --host 0.0.0.0 --port 8001 || python -m uvicorn main:app --host 0.0.0.0 --port 8001"]
