#!/usr/bin/env pwsh

# Cumpair Docker Startup Script
# This script helps you start the application with different service combinations

param(
    [string]$Profile = "basic",
    [switch]$Build,
    [switch]$Clean,
    [switch]$Logs,
    [switch]$Stop,
    [switch]$Help
)

function Show-Help {
    Write-Host "Cumpair Docker Management Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: ./docker-start.ps1 [OPTIONS]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Profiles:" -ForegroundColor Cyan
    Write-Host "  basic     - Core services (web, postgres, redis)" -ForegroundColor White
    Write-Host "  worker    - Basic + Celery worker and Flower" -ForegroundColor White
    Write-Host "  scraper   - Basic + Node.js scraper service" -ForegroundColor White
    Write-Host "  frontend  - Basic + React frontend" -ForegroundColor White
    Write-Host "  monitor   - Basic + Prometheus and Grafana" -ForegroundColor White
    Write-Host "  full      - All services" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Build    - Force rebuild of images" -ForegroundColor White
    Write-Host "  -Clean    - Clean up containers and volumes first" -ForegroundColor White
    Write-Host "  -Logs     - Show logs after starting" -ForegroundColor White
    Write-Host "  -Stop     - Stop all services" -ForegroundColor White
    Write-Host "  -Help     - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  ./docker-start.ps1 -Profile basic -Build" -ForegroundColor White
    Write-Host "  ./docker-start.ps1 -Profile full -Clean -Logs" -ForegroundColor White
    Write-Host "  ./docker-start.ps1 -Stop" -ForegroundColor White
}

if ($Help) {
    Show-Help
    exit 0
}

if ($Stop) {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    docker-compose down
    exit 0
}

if ($Clean) {
    Write-Host "Cleaning up containers and volumes..." -ForegroundColor Yellow
    docker-compose down -v
    docker system prune -f
}

# Define profile configurations
$profiles = @{
    "basic" = @()
    "worker" = @("--profile", "worker")
    "scraper" = @("--profile", "scraper")
    "frontend" = @("--profile", "frontend")
    "monitor" = @("--profile", "monitor")
    "full" = @("--profile", "worker", "--profile", "scraper", "--profile", "frontend", "--profile", "monitor")
}

if (-not $profiles.ContainsKey($Profile)) {
    Write-Host "Error: Unknown profile '$Profile'" -ForegroundColor Red
    Write-Host "Available profiles: $($profiles.Keys -join ', ')" -ForegroundColor Yellow
    exit 1
}

$profileArgs = $profiles[$Profile]

# Build command
$buildArgs = @()
if ($Build) {
    $buildArgs = @("--build")
}

Write-Host "Starting Cumpair with profile: $Profile" -ForegroundColor Green

# Start services
$command = @("docker-compose", "up", "-d") + $buildArgs + $profileArgs
Write-Host "Running: $($command -join ' ')" -ForegroundColor Cyan
& $command[0] $command[1..($command.Length-1)]

if ($LASTEXITCODE -eq 0) {
    Write-Host "Services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available endpoints:" -ForegroundColor Cyan
    Write-Host "  🌐 Main API: http://localhost:8000" -ForegroundColor White
    Write-Host "  📚 API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  💚 Health: http://localhost:8000/api/v1/health" -ForegroundColor White
    
    if ($Profile -eq "frontend" -or $Profile -eq "full") {
        Write-Host "  🎨 Frontend: http://localhost:3001" -ForegroundColor White
    }
    
    if ($Profile -eq "scraper" -or $Profile -eq "full") {
        Write-Host "  🕷️ Scraper: http://localhost:3001" -ForegroundColor White
    }
    
    if ($Profile -eq "worker" -or $Profile -eq "full") {
        Write-Host "  🌸 Flower: http://localhost:5555" -ForegroundColor White
    }
    
    if ($Profile -eq "monitor" -or $Profile -eq "full") {
        Write-Host "  📊 Prometheus: http://localhost:9090" -ForegroundColor White
        Write-Host "  📈 Grafana: http://localhost:3002 (admin/admin)" -ForegroundColor White
    }
    
    Write-Host ""
    
    if ($Logs) {
        Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
        docker-compose logs -f
    } else {
        Write-Host "Use 'docker-compose logs -f' to view logs" -ForegroundColor Yellow
        Write-Host "Use './docker-start.ps1 -Stop' to stop all services" -ForegroundColor Yellow
    }
} else {
    Write-Host "Failed to start services!" -ForegroundColor Red
    exit 1
}