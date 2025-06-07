#!/usr/bin/env pwsh
# Cumpair - All-in-One Service Launcher
# Starts all required services with a single command

param(
    [switch]$Full,      # Start all services (default)
    [switch]$Minimal,   # Start only core services
    [switch]$Stop,      # Stop all services
    [switch]$Status,    # Show service status
    [switch]$Help       # Show help
)

# Color functions for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    🔍 CUMPAIR SYSTEM LAUNCHER" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Help
function Show-Help {
    Show-Banner
    Write-Host "Usage: .\start-all.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Full        Start all services (PostgreSQL, Redis, Scraper, Celery, FastAPI)"
    Write-Host "  -Minimal     Start core services only (PostgreSQL, Redis, FastAPI)"
    Write-Host "  -Stop        Stop all running services"
    Write-Host "  -Status      Show current service status"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\start-all.ps1 -Full      # Start everything (recommended)"
    Write-Host "  .\start-all.ps1 -Minimal   # Quick start"
    Write-Host "  .\start-all.ps1 -Status    # Check what's running"
    Write-Host "  .\start-all.ps1 -Stop      # Stop all services"
    Write-Host ""
}

# Check if port is in use
function Test-PortInUse {
    param([int]$Port)
    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        return $listener | Where-Object { $_.Port -eq $Port }
    } catch {
        return $false
    }
}

# Stop all services
function Stop-AllServices {
    Write-Info "🛑 Stopping all Cumpair services..."
    
    # Stop Docker services
    Write-Info "Stopping Docker services..."
    docker-compose down 2>$null
    
    # Stop Node.js processes
    Write-Info "Stopping Node.js scraper..."
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*scraper*" } | Stop-Process -Force
    
    # Stop Python processes
    Write-Info "Stopping Python services..."
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*celery*" } | Stop-Process -Force
    
    Write-Success "✅ All services stopped!"
}

# Get service status
function Get-ServicesStatus {
    Write-Info "📊 Cumpair Services Status:"
    Write-Host ""
    
    # Docker services
    if (Test-PortInUse 5432) {
        Write-Success "✅ PostgreSQL (Port 5432)"
    } else {
        Write-Warning "❌ PostgreSQL not running"
    }
    
    if (Test-PortInUse 6379) {
        Write-Success "✅ Redis (Port 6379)"
    } else {
        Write-Warning "❌ Redis not running"
    }
    
    # Main application
    if (Test-PortInUse 8000) {
        Write-Success "✅ FastAPI App (Port 8000)"
        Write-Success "   🌐 http://localhost:8000"
    } else {
        Write-Warning "❌ FastAPI App not running"
    }
    
    # Scraper service
    if (Test-PortInUse 3000) {
        Write-Success "✅ Node.js Scraper (Port 3000)"
    } else {
        Write-Warning "❌ Node.js Scraper not running"
    }
    
    # Celery Flower
    if (Test-PortInUse 5555) {
        Write-Success "✅ Celery Flower (Port 5555)"
        Write-Success "   📊 http://localhost:5555"
    } else {
        Write-Warning "❌ Celery Flower not running"
    }
    
    Write-Host ""
}

# Start core services (Docker)
function Start-CoreServices {
    Write-Info "🐳 Starting core services (PostgreSQL + Redis)..."
    
    # Start Docker services
    docker-compose up postgres redis -d
    
    # Wait for services to be ready
    Write-Info "Waiting for services to be ready..."
    $timeout = 30
    $elapsed = 0
    
    do {
        Start-Sleep 2
        $elapsed += 2
        $pgReady = Test-PortInUse 5432
        $redisReady = Test-PortInUse 6379
    } while ((-not $pgReady -or -not $redisReady) -and $elapsed -lt $timeout)
    
    if ($pgReady -and $redisReady) {
        Write-Success "✅ Core services started!"
        
        # Run database migrations
        Write-Info "Running database migrations..."
        try {
            alembic upgrade head
            Write-Success "✅ Database migrations completed!"
        } catch {
            Write-Warning "⚠️ Database migrations may have failed"
        }
    } else {
        Write-Error "❌ Core services failed to start within $timeout seconds"
        exit 1
    }
}

# Start Node.js scraper service
function Start-ScraperService {
    Write-Info "🌐 Starting Node.js Scraper Service..."
    
    if (Test-Path "scraper/package.json") {
        Push-Location "scraper"
        
        # Install dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Info "Installing Node.js dependencies..."
            npm install
        }
        
        # Start scraper service in background
        Start-Process -FilePath "npm" -ArgumentList "start" -WindowStyle Hidden
        Pop-Location
        
        # Wait for service to start
        Start-Sleep 5
        if (Test-PortInUse 3000) {
            Write-Success "✅ Node.js Scraper started (Port 3000)"
        } else {
            Write-Warning "⚠️ Node.js Scraper may not have started properly"
        }
    } else {
        Write-Warning "⚠️ Scraper service not found (optional)"
    }
}

# Start Celery services
function Start-CeleryServices {
    Write-Info "⚙️ Starting Celery Services..."
    
    # Start Celery worker
    Write-Info "Starting Celery worker..."
    Start-Process -FilePath "celery" -ArgumentList "-A", "app.worker", "worker", "--loglevel=info" -WindowStyle Hidden
    
    # Start Celery Flower (monitoring)
    Write-Info "Starting Celery Flower..."
    Start-Process -FilePath "celery" -ArgumentList "-A", "app.worker", "flower" -WindowStyle Hidden
    
    # Wait for Flower to start
    Start-Sleep 3
    if (Test-PortInUse 5555) {
        Write-Success "✅ Celery services started!"
        Write-Success "   📊 Task Monitor: http://localhost:5555"
    } else {
        Write-Warning "⚠️ Celery Flower may not have started properly"
    }
}

# Start main FastAPI application
function Start-MainApplication {
    Write-Info "🚀 Starting Main FastAPI Application..."
    
    # Start FastAPI
    Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WindowStyle Hidden
    
    # Wait for application to be ready
    $timeout = 30
    $elapsed = 0
    do {
        Start-Sleep 2
        $elapsed += 2
        $appReady = Test-PortInUse 8000
    } while (-not $appReady -and $elapsed -lt $timeout)
    
    if ($appReady) {
        Write-Success "✅ Cumpair application started successfully!"
        Write-Success "   🌐 Main App: http://localhost:8000"
        Write-Success "   📚 API Docs: http://localhost:8000/docs"
    } else {
        Write-Error "❌ Main application failed to start within $timeout seconds"
        exit 1
    }
}

# Main execution logic
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    if ($Stop) {
        Stop-AllServices
        return
    }
    
    if ($Status) {
        Get-ServicesStatus
        return
    }
    
    Show-Banner
    
    if ($Minimal) {
        Write-Info "🎯 Starting Minimal Configuration..."
        Start-CoreServices
        Start-MainApplication
        
        Write-Host ""
        Write-Success "🎉 Cumpair (Minimal) is ready!"
        Write-Success "   🌐 Access: http://localhost:8000"
        Write-Success "   📚 API Docs: http://localhost:8000/docs"
        Write-Host ""
        Write-Info "To start additional services later:"
        Write-Info "   .\start-all.ps1 -Full"
        
    } elseif ($Full -or (-not $Minimal -and -not $Stop -and -not $Status)) {
        Write-Info "🎯 Starting Full Configuration..."
        Start-CoreServices
        Start-ScraperService
        Start-CeleryServices
        Start-MainApplication
        
        Write-Host ""
        Write-Success "🎉 Cumpair (Full) is ready!"
        Write-Success "   🌐 Main App: http://localhost:8000"
        Write-Success "   📚 API Docs: http://localhost:8000/docs"
        if (Test-PortInUse 5555) {
            Write-Success "   📊 Task Monitor: http://localhost:5555"
        }
        Write-Host ""
        Write-Info "All services are running in the background."
        Write-Info "Use '.\start-all.ps1 -Status' to check service status."
        Write-Info "Use '.\start-all.ps1 -Stop' to stop all services."
    }
}

# Run main function
Main
