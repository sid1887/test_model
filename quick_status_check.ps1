#!/usr/bin/env pwsh

Write-Host "=== DOCKER COMPOSE SERVICE STATUS CHECK ===" -ForegroundColor Green
Write-Host ""

# Check container status
Write-Host "Container Status:" -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "=== ENDPOINT HEALTH CHECKS ===" -ForegroundColor Green

# Test endpoints
$endpoints = @(
    @{ Name = "Web API Health"; Url = "http://localhost:8000/api/v1/health" }
    @{ Name = "Flower Dashboard"; Url = "http://localhost:5555" }
    @{ Name = "Frontend"; Url = "http://localhost:8080" }
    @{ Name = "Grafana"; Url = "http://localhost:3002" }
    @{ Name = "Prometheus"; Url = "http://localhost:9090" }
)

foreach ($endpoint in $endpoints) {
    Write-Host "Testing $($endpoint.Name)..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $endpoint.Url -Method Get -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✅ SUCCESS - Status: $($response.StatusCode)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== RECENT LOGS (Last 5 lines) ===" -ForegroundColor Green
$services = @("web", "worker", "flower", "scraper")

foreach ($service in $services) {
    Write-Host "--- $service logs ---" -ForegroundColor Yellow
    docker compose logs $service --tail 5
    Write-Host ""
}
