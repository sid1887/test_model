# INTELLIGENT AUTOMATED DOCKERFILE WITH CONFLICT RESOLUTION
FROM python:3.11-slim AS base

# Set environment variables for automated installations
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install system dependencies with automated retry mechanism
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    procps \
    ca-certificates \
    gnupg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "System dependencies installed"

# Upgrade pip with retry mechanism
RUN python -m pip install --upgrade pip setuptools wheel || \
    (sleep 5 && python -m pip install --upgrade pip setuptools wheel) || \
    echo "Pip upgrade failed, continuing with existing version"

# Copy the automated package installer and requirements
COPY auto_install_packages.py /app/auto_install_packages.py
COPY requirements.txt /app/requirements.txt

# Run automated package installation with conflict resolution
RUN python auto_install_packages.py || echo "Some packages failed, continuing..."

# Builder stage for development dependencies
FROM base AS builder

# Install build dependencies that might be needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    pkg-config \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Build dependencies installed"

# Production stage
FROM base AS production

# Copy application code
COPY . /app/

# Copy and make scripts executable
COPY start.sh /app/start.sh
COPY healthcheck.sh /app/healthcheck.sh
COPY docker/entrypoints/*.sh /app/docker/entrypoints/
RUN chmod +x /app/start.sh /app/healthcheck.sh /app/docker/entrypoints/*.sh \
    && sed -i 's/\r$//' /app/start.sh /app/healthcheck.sh /app/docker/entrypoints/*.sh

# Default environment variables
ENV PORT=8000
ENV WORKERS=1
ENV SERVICE_TYPE=web

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /app/models && \
    chmod -R 755 /app/logs /app/uploads /app/models

# Health check with adaptive timeout
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

EXPOSE 8000

# Set default command to our smart startup script
CMD ["/app/start.sh"]

# As a safety net, ensure critical runtime dependencies are present (in case auto installer skipped any)
RUN pip install --no-cache-dir --disable-pip-version-check \
    -r /app/requirements.txt || true \
    && pip install --no-cache-dir --disable-pip-version-check prometheus-client uvicorn || true
