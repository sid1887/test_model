#!/usr/bin/env pwsh

# 🚀 COMPREHENSIVE DOCKER FIX SCRIPT - CORRECTED VERSION
# This script fixes Docker deployment issues with proper error handling and validation

[CmdletBinding()]
param(
    [switch]$SkipCleanup,
    [switch]$SkipHealthCheck,
    [int]$Timeout = 300
)

# Error handling
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-StatusMessage {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerInstalled {
    try {
        docker --version | Out-Null
        docker-compose --version | Out-Null
        return $true
    } catch {
        Write-StatusMessage "❌ Docker or Docker Compose not installed!" "Red"
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$HealthCommand,
        [int]$MaxWaitSeconds = 60
    )
    
    Write-StatusMessage "⏳ Waiting for $ServiceName to be ready..." "Yellow"
    $elapsed = 0
    $interval = 5
    
    while ($elapsed -lt $MaxWaitSeconds) {
        try {
            Invoke-Expression $HealthCommand | Out-Null
            Write-StatusMessage "✅ $ServiceName is ready!" "Green"
            return $true
        } catch {
            Start-Sleep -Seconds $interval
            $elapsed += $interval
            Write-StatusMessage "⏳ $ServiceName not ready yet... ($elapsed/$MaxWaitSeconds)" "Gray"
        }
    }
    
    Write-StatusMessage "❌ $ServiceName failed to become ready within $MaxWaitSeconds seconds" "Red"
    return $false
}

function Test-ServiceHealth {
    param([string]$Url, [int]$TimeoutSeconds = 10)
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec $TimeoutSeconds
        return $true
    } catch {
        return $false
    }
}

Write-StatusMessage "COMPREHENSIVE DOCKER FIX STARTING..." "Cyan"
Write-StatusMessage "=================================" "Cyan"

# Validate prerequisites
if (-not (Test-DockerInstalled)) {
    Write-StatusMessage "Please install Docker and Docker Compose first." "Red"
    exit 1
}

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml") -and -not (Test-Path "docker-compose.complete.yml")) {
    Write-StatusMessage "❌ No docker-compose.yml file found in current directory!" "Red"
    exit 1
}

$ComposeFile = if (Test-Path "docker-compose.complete.yml") { "docker-compose.complete.yml" } else { "docker-compose.yml" }

# Step 1: Environment Cleanup (Optional)
if (-not $SkipCleanup) {
    Write-StatusMessage "STEP 1: Environment Cleanup..." "Yellow"
    
    Write-StatusMessage "Stopping containers..." "Gray"
    try {
        docker-compose -f $ComposeFile down --remove-orphans --volumes 2>$null
    } catch {
        Write-StatusMessage "Warning: Some containers may not have stopped cleanly" "Yellow"
    }
    
    Write-StatusMessage "Cleaning unused Docker resources..." "Gray"
    try {
        docker system prune -f 2>$null
        docker volume prune -f 2>$null
    } catch {
        Write-StatusMessage "Warning: Docker cleanup had issues" "Yellow"
    }
    
    Write-StatusMessage "Environment cleanup complete!" "Green"
}

# Step 2: Create Directory Structure
Write-StatusMessage "STEP 2: Creating Directory Structure..." "Yellow"

$directories = @("secrets", "uploads", "logs", "models", "data/postgres", "data/redis")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        try {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-StatusMessage "Created directory: $dir" "Gray"
        } catch {
            Write-StatusMessage "❌ Failed to create directory: $dir" "Red"
            exit 1
        }
    }
}

Write-StatusMessage "Directory structure created!" "Green"

# Step 3: Create Secret Files with Secure Passwords
Write-StatusMessage "STEP 3: Creating Secret Files..." "Yellow"

$secrets = @{
    "postgres_password.txt" = "$(New-Guid)_pg_2024"
    "db_password.txt" = "$(New-Guid)_db_2024" 
    "grafana_password.txt" = "$(New-Guid)_grafana_2024"
    "redis_password.txt" = "$(New-Guid)_redis_2024"
    "secret_key.txt" = "$(New-Guid)_$(Get-Date -Format 'yyyyMMdd')_ultra_secure"
}

foreach ($secret in $secrets.GetEnumerator()) {
    try {
        $secret.Value | Out-File -FilePath "secrets/$($secret.Key)" -Encoding UTF8 -NoNewline
        Write-StatusMessage "Created secret: $($secret.Key)" "Gray"
    } catch {
        Write-StatusMessage "❌ Failed to create secret: $($secret.Key)" "Red"
        exit 1
    }
}

Write-StatusMessage "Secret files created!" "Green"

# Step 4: Create Environment File
Write-StatusMessage "STEP 4: Creating Environment File..." "Yellow"

# Read secrets for environment file
$postgresPassword = Get-Content "secrets/postgres_password.txt" -Raw
$redisPassword = Get-Content "secrets/redis_password.txt" -Raw  
$secretKey = Get-Content "secrets/secret_key.txt" -Raw

# Create environment content with proper escaping
$envLines = @(
    "# Database Configuration",
    "DATABASE_URL=postgresql://compair:$postgresPassword@postgres:5432/compair",
    "POSTGRES_DB=compair",
    "POSTGRES_USER=compair", 
    "POSTGRES_PASSWORD=$postgresPassword",
    "",
    "# Redis Configuration",
    "REDIS_URL=redis://:$redisPassword@redis:6379",
    "REDIS_HOST=redis",
    "REDIS_PORT=6379",
    "REDIS_PASSWORD=$redisPassword",
    "",
    "# Celery Configuration", 
    "CELERY_BROKER_URL=redis://:$redisPassword@redis:6379/0",
    "CELERY_RESULT_BACKEND=redis://:$redisPassword@redis:6379/0",
    "",
    "# Service URLs",
    "SCRAPER_SERVICE_URL=http://scraper:3001",
    "CAPTCHA_SERVICE_URL=http://captcha:9001", 
    "PROXY_SERVICE_URL=http://proxy:8001",
    "",
    "# Application Settings",
    "SECRET_KEY=$secretKey",
    "PYTHONUNBUFFERED=1",
    "COMPOSE_HTTP_TIMEOUT=1800",
    "DOCKER_CLIENT_TIMEOUT=1800", 
    "",
    "# Node.js Settings",
    "NODE_ENV=production",
    "NODE_OPTIONS=--max_old_space_size=2048",
    "",
    "# Docker Settings", 
    "BUILDKIT_INLINE_CACHE=1",
    "PIP_TIMEOUT=2000",
    "PIP_RETRIES=10",
    "",
    "# Security Settings",
    'CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost:8080"]',
    'ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]',
    "",
    "# Monitoring",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc"
)

try {
    $envLines | Out-File -FilePath ".env" -Encoding UTF8
    Write-StatusMessage "Environment file created!" "Green"
} catch {
    Write-StatusMessage "Failed to create environment file!" "Red"
    exit 1
}

# Step 5: Create Production-Ready Dockerfile
Write-StatusMessage "STEP 5: Creating Production Dockerfile..." "Yellow"

$dockerfileLines = @(
    "FROM python:3.11-slim",
    "",
    "# Set environment variables",
    "ENV PYTHONDONTWRITEBYTECODE=1",
    "ENV PYTHONUNBUFFERED=1", 
    "ENV PIP_NO_CACHE_DIR=1",
    "ENV PIP_DISABLE_PIP_VERSION_CHECK=1",
    "",
    "# Install system dependencies",
    "RUN apt-get update && apt-get install -y --no-install-recommends \",
    "    curl \",
    "    gcc \",
    "    g++ \",
    "    make \",
    "    git \",
    "    libpq-dev \",
    "    postgresql-client \",
    "    && rm -rf /var/lib/apt/lists/* \",
    "    && apt-get clean",
    "",
    "# Create non-root user", 
    "RUN groupadd -r appuser && useradd -r -g appuser appuser",
    "",
    "# Set working directory",
    "WORKDIR /app",
    "",
    "# Copy requirements first (for better caching)",
    "COPY requirements.txt ./",
    "COPY requirements.minimal.txt ./", 
    "",
    "# Install Python dependencies with proper error handling",
    "RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \",
    "    pip install --no-cache-dir --timeout=2000 --retries=10 -r requirements.txt || \",
    "    pip install --no-cache-dir --timeout=2000 --retries=10 -r requirements.minimal.txt",
    "",
    "# Copy application code",
    "COPY --chown=appuser:appuser . .",
    "",
    "# Create necessary directories with proper permissions", 
    "RUN mkdir -p /app/logs /app/uploads /app/models /app/.cache /tmp/prometheus_multiproc && \",
    "    chown -R appuser:appuser /app /tmp/prometheus_multiproc && \",
    "    chmod -R 755 /app",
    "",
    "# Switch to non-root user",
    "USER appuser",
    "",
    "# Expose port",
    "EXPOSE 8000",
    "",
    "# Health check with proper timeout",
    "HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \",
    "    CMD curl -f http://localhost:8000/health || curl -f http://localhost:8000/api/v1/health || exit 1",
    "",
    "# Default command with proper signal handling", 
    'CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]'
)

try {
    $dockerfileLines | Out-File -FilePath "Dockerfile.fixed" -Encoding UTF8
    Write-StatusMessage "Production Dockerfile created!" "Green"
} catch {
    Write-StatusMessage "Failed to create Dockerfile!" "Red"
    exit 1
}

# Step 6: Create Minimal Requirements
Write-StatusMessage "STEP 6: Creating Minimal Requirements..." "Yellow"

$requirementsLines = @(
    "# Core FastAPI Dependencies",
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0", 
    "gunicorn==21.2.0",
    "",
    "# Database Dependencies",
    "asyncpg==0.29.0",
    "psycopg2-binary==2.9.9",
    "sqlalchemy==2.0.23",
    "alembic==1.13.1",
    "",
    "# Redis Dependencies",
    "redis==5.0.1", 
    "aioredis==2.0.1",
    "",
    "# Celery Dependencies",
    "celery==5.3.6",
    "flower==2.0.1",
    "",
    "# Core Dependencies",
    "aiofiles==23.2.1",
    "python-multipart==0.0.6",
    "httpx==0.27.0",
    "requests==2.31.0",
    "pydantic==2.5.2",
    "pydantic-settings==2.1.0", 
    "prometheus-client==0.19.0",
    "structlog==23.2.0",
    "Pillow==10.2.0",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-dotenv==1.0.0",
    "click==8.1.7",
    "tenacity==8.2.3"
)

try {
    $requirementsLines | Out-File -FilePath "requirements.minimal.txt" -Encoding UTF8
    Write-StatusMessage "Minimal requirements created!" "Green"
} catch {
    Write-StatusMessage "Failed to create requirements file!" "Red"
    exit 1
}

# Step 7: Build Services with Error Handling  
Write-StatusMessage "STEP 7: Building Services..." "Yellow"

Write-StatusMessage "Building services..." "Gray"
try {
    docker-compose -f $ComposeFile build --no-cache --parallel
    Write-StatusMessage "Services built successfully!" "Green"
} catch {
    Write-StatusMessage "Failed to build services!" "Red"
    Write-StatusMessage "Trying to build core services only..." "Yellow"
    
    try {
        docker-compose -f $ComposeFile build --no-cache postgres redis
        Write-StatusMessage "Core services built!" "Green"
    } catch {
        Write-StatusMessage "Failed to build core services!" "Red"
        exit 1
    }
}

# Step 8: Start Services with Proper Ordering
Write-StatusMessage "STEP 8: Starting Services..." "Yellow"

# Start PostgreSQL first
Write-StatusMessage "Starting PostgreSQL..." "Gray"
try {
    docker-compose -f $ComposeFile up -d postgres
    
    # Wait for PostgreSQL
    if (-not (Wait-ForService "PostgreSQL" "docker-compose -f $ComposeFile exec postgres pg_isready -U compair -d compair" 60)) {
        Write-StatusMessage "PostgreSQL failed to start!" "Red"
        exit 1
    }
} catch {
    Write-StatusMessage "Failed to start PostgreSQL!" "Red"
    exit 1
}

# Start Redis  
Write-StatusMessage "Starting Redis..." "Gray"
try {
    docker-compose -f $ComposeFile up -d redis
    
    # Wait for Redis
    $redisPassword = Get-Content "secrets/redis_password.txt" -Raw
    if (-not (Wait-ForService "Redis" "docker-compose -f $ComposeFile exec redis redis-cli --no-auth-warning -a $redisPassword ping" 30)) {
        Write-StatusMessage "Redis failed to start!" "Red"
        exit 1
    }
} catch {
    Write-StatusMessage "Failed to start Redis!" "Red"
    exit 1
}

# Start Web Service
Write-StatusMessage "Starting Web Service..." "Gray"
try {
    docker-compose -f $ComposeFile up -d web
    
    # Wait for Web Service
    if (-not (Wait-ForService "Web Service" "docker-compose -f $ComposeFile exec web curl -f http://localhost:8000/health" 90)) {
        Write-StatusMessage "Web service may not be fully ready, but continuing..." "Yellow"
    }
} catch {
    Write-StatusMessage "Failed to start Web Service!" "Red"
    Write-StatusMessage "Check logs: docker-compose -f $ComposeFile logs web" "Yellow"
}

# Step 9: Start Additional Services
Write-StatusMessage "STEP 9: Starting Additional Services..." "Yellow"

$additionalServices = @("worker", "scraper", "captcha", "proxy")
foreach ($service in $additionalServices) {
    Write-StatusMessage "Starting $service..." "Gray"
    try {
        docker-compose -f $ComposeFile up -d $service 2>$null
        Write-StatusMessage "$service started!" "Green"
    } catch {
        Write-StatusMessage "$service may not be configured, skipping..." "Yellow"
    }
}

# Step 10: Health Check and Status
if (-not $SkipHealthCheck) {
    Write-StatusMessage "STEP 10: Health Check..." "Yellow"
    
    # Check service status
    Write-StatusMessage "Checking service health..." "Gray"
    
    $services = @{
        "PostgreSQL" = "docker-compose -f $ComposeFile exec postgres pg_isready -U compair -d compair"
        "Redis" = "docker-compose -f $ComposeFile exec redis redis-cli --no-auth-warning -a $(Get-Content 'secrets/redis_password.txt' -Raw) ping"
        "Web API" = "curl -f http://localhost:8000/health -m 5"
    }
    
    foreach ($service in $services.GetEnumerator()) {
        try {
            Invoke-Expression $service.Value | Out-Null
            Write-StatusMessage "$($service.Key): HEALTHY" "Green"
        } catch {
            Write-StatusMessage "$($service.Key): UNHEALTHY" "Red"
        }
    }
}

# Final Status Report
Write-StatusMessage "FINAL STATUS REPORT" "Cyan"
Write-StatusMessage "=================================" "Cyan"

Write-StatusMessage "Running containers:" "Yellow"
try {
    docker-compose -f $ComposeFile ps
} catch {
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

Write-StatusMessage ""
Write-StatusMessage "DOCKER SETUP COMPLETE!" "Green"
Write-StatusMessage "=================================" "Green"
Write-StatusMessage "Access Points:" "Cyan"
Write-StatusMessage "   - API: http://localhost:8000" "Cyan"
Write-StatusMessage "   - API Docs: http://localhost:8000/docs" "Cyan"
Write-StatusMessage "   - Health Check: http://localhost:8000/health" "Cyan"
Write-StatusMessage ""
Write-StatusMessage "Management Commands:" "Yellow"
Write-StatusMessage "   - View logs: docker-compose -f $ComposeFile logs -f" "Yellow"
Write-StatusMessage "   - Restart: docker-compose -f $ComposeFile restart" "Yellow"
Write-StatusMessage "   - Stop all: docker-compose -f $ComposeFile down" "Yellow"
Write-StatusMessage "   - Status: docker-compose -f $ComposeFile ps" "Yellow"