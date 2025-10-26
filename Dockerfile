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
    build-essential \
    curl \
    wget \
    procps \
    ca-certificates \
    gnupg \
    git \
    # Runtime libs for OpenCV/EasyOCR/Matplotlib
    libgl1 \
    libglib2.0-0 \
    # Tesseract OCR engine and English language data
    tesseract-ocr \
    tesseract-ocr-eng \
    libleptonica-dev \
    libtesseract-dev \
    # Math/BLAS/LAPACK
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    gfortran \
    # GEOS/PROJ/GDAL for Shapely/GIS
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    # Audio/Media
    ffmpeg \
    libsndfile1 \
    sox \
    swig \
    pkg-config \
    # Playwright dependencies (Chromium)
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libasound2 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    fonts-liberation \
    # Node for Playwright and build tooling
    nodejs \
    npm \
    # Additional libs for Python packages
    libmagic1 \
    libgomp1 \
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

# Copy and make scripts executable (updated paths after workspace organization)
COPY scripts/start.sh /app/start.sh
COPY scripts/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/start.sh /app/healthcheck.sh && \
    sed -i 's/\r$//' /app/start.sh /app/healthcheck.sh

# Default environment variables
ENV PORT=8000
ENV WORKERS=4
ENV SERVICE_TYPE=web
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV METRIC_PREFIX=cumpair_

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /app/models /tmp/prometheus_multiproc && \
    chmod -R 755 /app/logs /app/uploads /app/models && \
    chmod 777 /tmp/prometheus_multiproc

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

# Ensure Playwright browsers are installed (Chromium) for scraping
RUN python -m playwright install --with-deps chromium || true
