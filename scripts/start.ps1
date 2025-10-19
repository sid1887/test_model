# Quick Start Script for Cumpair
# This script starts all necessary services

Write-Host "🔍 Starting Cumpair Services" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Blue

# Function to check if a service is running
function Test-ServiceRunning {
    param($url, $name)
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ $name is running" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ $name is not responding at $url" -ForegroundColor Red
        return $false
    }
}

# Check prerequisites
Write-Host "`n📋 Checking services..." -ForegroundColor Yellow

# Start Docker services if Docker is available
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "🐳 Starting Docker services..." -ForegroundColor Cyan
    try {
        docker-compose up -d postgres redis rota
        Start-Sleep 10  # Wait for services to start
        Write-Host "✅ Docker services started" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Could not start Docker services" -ForegroundColor Yellow
    }
}

# Start Node.js scraper service
Write-Host "`n📦 Starting scraper service..." -ForegroundColor Cyan
if (Test-Path "scraper/server.js") {
    Start-Process -FilePath "cmd" -ArgumentList "/c", "cd scraper && npm start" -WindowStyle Minimized
    Start-Sleep 5
    
    # Check if scraper is running
    if (Test-ServiceRunning "http://localhost:3001/health" "Scraper Service") {
        Write-Host "✅ Scraper service started on port 3001" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Scraper service may not be running. Check scraper/server.js" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Scraper service files not found" -ForegroundColor Red
}

# Check database connection
Write-Host "`n🗄️ Checking database..." -ForegroundColor Yellow
if (Test-ServiceRunning "http://localhost:5432" "PostgreSQL" -ErrorAction SilentlyContinue) {
    Write-Host "✅ PostgreSQL is accessible" -ForegroundColor Green
} else {
    Write-Host "⚠️ PostgreSQL may not be running on port 5432" -ForegroundColor Yellow
}

# Check Redis connection
if (Test-ServiceRunning "http://localhost:6379" "Redis" -ErrorAction SilentlyContinue) {
    Write-Host "✅ Redis is accessible" -ForegroundColor Green
} else {
    Write-Host "⚠️ Redis may not be running on port 6379" -ForegroundColor Yellow
}

# Start main application
Write-Host "`n🚀 Starting main application..." -ForegroundColor Cyan
Write-Host "This will start the FastAPI server..." -ForegroundColor Yellow

# Set environment variables
$env:PYTHONPATH = Get-Location

# Start the application
try {
    python main.py
} catch {
    Write-Host "❌ Failed to start main application" -ForegroundColor Red
    Write-Host "Make sure all dependencies are installed: pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host "`n📝 Access Points:" -ForegroundColor Yellow
Write-Host "Main App: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Scraper: http://localhost:3001/health" -ForegroundColor Cyan
