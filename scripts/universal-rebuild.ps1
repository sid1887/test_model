# Universal Package Installer - Docker Rebuild Script
Write-Host "UNIVERSAL PACKAGE INSTALLER - REBUILDING ALL SERVICES" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Stop all services
Write-Host "Stopping all services..." -ForegroundColor Yellow
docker compose down

# Clean up containers and images for fresh rebuild
Write-Host "Cleaning up containers..." -ForegroundColor Yellow
docker system prune -f

# Copy the universal requirements if available
if (Test-Path "requirements_universal.txt") {
    Write-Host "Using enhanced requirements file..." -ForegroundColor Green
    Copy-Item "requirements_universal.txt" "requirements.txt" -Force
}

# Build all services with no cache for clean start
Write-Host "Building all services with Universal Package Installer..." -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.override.yml build --no-cache

# Start services with universal installer
Write-Host "Starting services with Universal Package Installer..." -ForegroundColor Green
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Wait a moment for services to initialize
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep 30

# Check service status
Write-Host "Checking service status..." -ForegroundColor Cyan
docker compose ps

Write-Host "Universal Package Installer deployment complete!" -ForegroundColor Green
Write-Host "All services now have automatic package installation capabilities." -ForegroundColor Green
Write-Host "Check logs with: docker compose logs -f [service_name]" -ForegroundColor Yellow
