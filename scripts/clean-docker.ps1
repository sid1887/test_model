#!/usr/bin/env pwsh
# Clean Docker completely and start fresh

Write-Host "🧹 Cleaning up Docker completely..." -ForegroundColor Yellow

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Cyan
docker-compose down -v --remove-orphans

# Remove all containers
Write-Host "Removing all containers..." -ForegroundColor Cyan
docker container prune -f

# Remove all images for this project
Write-Host "Removing project images..." -ForegroundColor Cyan
docker image rm test_model-web test_model-scraper test_model-frontend 2>$null
docker image rm test_model_web test_model_scraper test_model_frontend 2>$null

# Remove all volumes
Write-Host "Removing all volumes..." -ForegroundColor Cyan
docker volume prune -f

# Remove all networks
Write-Host "Removing unused networks..." -ForegroundColor Cyan
docker network prune -f

# Remove build cache
Write-Host "Removing build cache..." -ForegroundColor Cyan
docker builder prune -f

Write-Host "✅ Docker cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Now you can run:" -ForegroundColor Yellow
Write-Host "cd 'd:\dev_packages\test_model'; docker-compose up -d" -ForegroundColor White
