# Quick Start Script for Cumpair Development Environment
# Usage: .\quickstart.ps1

Write-Host "🚀 Starting Cumpair Development Environment" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (!(Test-Path .env)) {
    Write-Host "📝 Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env with your configuration" -ForegroundColor Yellow
    Write-Host ""
}

# Check Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Build images
Write-Host ""
Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
docker-compose -f docker-compose.dev.yml build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Start services
Write-Host ""
Write-Host "🚢 Starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.dev.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services!" -ForegroundColor Red
    exit 1
}

# Wait for services to be healthy
Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.dev.yml ps

# Run migrations
Write-Host ""
Write-Host "🔄 Running database migrations..." -ForegroundColor Cyan
docker-compose -f docker-compose.dev.yml exec -T web alembic upgrade head 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Migrations not configured or failed (this is OK for first run)" -ForegroundColor Yellow
}

# Show access URLs
Write-Host ""
Write-Host "✅ Cumpair is ready!" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
Write-Host "📍 Access points:" -ForegroundColor Cyan
Write-Host "   - API: http://localhost:8000" -ForegroundColor White
Write-Host "   - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   - Health Check: http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host "   - Scraper: http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   - View logs: docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor White
Write-Host "   - Stop services: docker-compose -f docker-compose.dev.yml down" -ForegroundColor White
Write-Host "   - Restart service: docker-compose -f docker-compose.dev.yml restart [service]" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Happy coding!" -ForegroundColor Green
