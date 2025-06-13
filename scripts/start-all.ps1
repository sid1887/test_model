# Cumpair Service Management PowerShell Script
# Windows version of start-all.sh

param(
    [switch]$NoScraper,
    [switch]$NoMonitor, 
    [switch]$NoFrontend,
    [switch]$NoWorker,
    [switch]$Minimal,
    [switch]$Full
)

# Colors for PowerShell output
function Write-Info($message) {
    Write-Host "▶️  $message" -ForegroundColor Blue
}

function Write-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "❌ $message" -ForegroundColor Red
}

# Set defaults
$INCLUDE_SCRAPER = -not $NoScraper
$INCLUDE_MONITOR = -not $NoMonitor
$INCLUDE_FRONTEND = -not $NoFrontend
$INCLUDE_WORKER = -not $NoWorker

# Handle presets
if ($Minimal) {
    $INCLUDE_SCRAPER = $false
    $INCLUDE_MONITOR = $false
    $INCLUDE_FRONTEND = $false
    $INCLUDE_WORKER = $false
}

if ($Full) {
    $INCLUDE_SCRAPER = $true
    $INCLUDE_MONITOR = $true
    $INCLUDE_FRONTEND = $true
    $INCLUDE_WORKER = $true
}

# Build list of profiles
$PROFILES = @("core")
if ($INCLUDE_WORKER) { $PROFILES += "worker" }
if ($INCLUDE_SCRAPER) { $PROFILES += "scraper" }
if ($INCLUDE_FRONTEND) { $PROFILES += "frontend" }
if ($INCLUDE_MONITOR) { $PROFILES += "monitor" }

Write-Info "Starting Cumpair services with profiles: $($PROFILES -join ', ')"

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker first."
    exit 1
}

# Build profile arguments for docker-compose
$profileArgs = @()
foreach ($profile in $PROFILES) {
    $profileArgs += "--profile"
    $profileArgs += $profile
}

# Run compose with selected profiles
Write-Info "Building and starting containers..."
$startArgs = $profileArgs + @("up", "-d", "--build")
& docker-compose @startArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker services"
    exit 1
}

# Wait for core services to be healthy
Write-Info "Waiting for core services to be ready..."

# Wait for PostgreSQL
Write-Host "⏳ PostgreSQL: " -NoNewline
$maxAttempts = 30
$attempt = 0
do {
    Start-Sleep 2
    $attempt++
    try {
        docker exec compair_postgres pg_isready -U compair 2>&1 | Out-Null
        $pgReady = $true
    } catch {
        $pgReady = $false
        Write-Host "." -NoNewline
    }
} while (-not $pgReady -and $attempt -lt $maxAttempts)

if ($pgReady) {
    Write-Success "PostgreSQL is ready!"
} else {
    Write-Error "PostgreSQL failed to start within $($maxAttempts * 2) seconds"
    exit 1
}

# Wait for Redis
Write-Host "⏳ Redis: " -NoNewline
$attempt = 0
do {
    Start-Sleep 2
    $attempt++
    try {
        docker exec compair_redis redis-cli ping 2>&1 | Out-Null
        $redisReady = $true
    } catch {
        $redisReady = $false
        Write-Host "." -NoNewline
    }
} while (-not $redisReady -and $attempt -lt $maxAttempts)

if ($redisReady) {
    Write-Success "Redis is ready!"
} else {
    Write-Error "Redis failed to start within $($maxAttempts * 2) seconds"
    exit 1
}

# Wait for main web service
$webRunning = docker-compose ps | Select-String "compair_web"
if ($webRunning) {
    Write-Host "⏳ FastAPI Web Service: " -NoNewline
    $attempt = 0
    do {
        Start-Sleep 3
        $attempt++
        try {
            docker exec compair_web curl -f http://localhost:8000/api/v1/health 2>&1 | Out-Null
            $webReady = $true
        } catch {
            $webReady = $false
            Write-Host "." -NoNewline
        }
    } while (-not $webReady -and $attempt -lt $maxAttempts)
    
    if ($webReady) {
        Write-Success "FastAPI web service is ready!"
    } else {
        Write-Warning "FastAPI web service health check failed - continuing anyway"
    }
}

# Run database migrations
Write-Info "Applying database migrations..."
try {
    docker exec compair_web alembic upgrade head
    Write-Success "Database migrations completed!"
} catch {
    Write-Warning "Database migrations may have failed - check logs"
}

# Check scraper service
if ($INCLUDE_SCRAPER) {
    $scraperRunning = docker-compose ps | Select-String "compair_scraper"
    if ($scraperRunning) {
        Write-Host "⏳ Scraper Service: " -NoNewline
        $attempt = 0
        do {
            Start-Sleep 2
            $attempt++
            try {
                docker exec compair_scraper curl -f http://localhost:3001/health 2>&1 | Out-Null
                $scraperReady = $true
            } catch {
                $scraperReady = $false
                Write-Host "." -NoNewline
            }
        } while (-not $scraperReady -and $attempt -lt 15)
        
        if ($scraperReady) {
            Write-Success "Scraper service is ready!"
        } else {
            Write-Warning "Scraper service health check failed"
        }
    }
}

# Display service status
Write-Host ""
Write-Success "🎉 Cumpair services are up and running!"
Write-Host ""
Write-Info "📋 Service Status:"

# Core services
Write-Host "🔗 Core Services:"
Write-Host "   🗄️  PostgreSQL: http://localhost:5432"
Write-Host "   📦 Redis: http://localhost:6379"
Write-Host "   🌐 FastAPI Web: http://localhost:8000"
Write-Host "   📚 API Docs: http://localhost:8000/docs"

# Optional services
if ($INCLUDE_WORKER) {
    Write-Host "⚙️  Background Services:"
    Write-Host "   🔄 Celery Worker: Running"
    $flowerRunning = docker-compose ps | Select-String "compair_flower"
    if ($flowerRunning) {
        Write-Host "   📊 Flower Monitor: http://localhost:5555"
    }
}

if ($INCLUDE_SCRAPER) {
    Write-Host "🕷️  Scraping Services:"
    Write-Host "   🌐 Node.js Scraper: http://localhost:3001"
}

if ($INCLUDE_FRONTEND) {
    Write-Host "🎨 Frontend Services:"
    Write-Host "   💻 Next.js App: http://localhost:3002"
}

if ($INCLUDE_MONITOR) {
    Write-Host "📊 Monitoring Services:"
    Write-Host "   📈 Prometheus: http://localhost:9090"
    Write-Host "   📉 Grafana: http://localhost:3003 (admin/admin)"
}

Write-Host ""
Write-Info "💡 Usage Tips:"
Write-Host "   make logs     - View all service logs"
Write-Host "   make stop     - Stop all services"
Write-Host "   make restart  - Restart all services"
Write-Host ""
Write-Info "🚀 Ready to use! Visit http://localhost:8000 to get started."
