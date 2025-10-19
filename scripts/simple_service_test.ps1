# Simple Service Testing Script
param(
    [switch]$All = $true
)

$ErrorActionPreference = 'Continue'

function Test-Endpoint {
    param([string]$Url, [string]$Name)
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
        Write-Host "[$Name] PASS - $Url" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$Name] FAIL - $Url | $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-WebPage {
    param([string]$Url, [string]$Name)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10
        Write-Host "[$Name] PASS - Status: $($response.StatusCode)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$Name] FAIL - $Url | $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host "=== COMPREHENSIVE SERVICE TESTING ===" -ForegroundColor Cyan
Write-Host ""

# Test Frontend
Write-Host "Testing Frontend Services..." -ForegroundColor Yellow
Test-WebPage "http://localhost:8080" "Frontend Main Page"
Test-WebPage "http://localhost:80" "Nginx Load Balancer"

# Test Backend API
Write-Host "`nTesting Backend API..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # Wait for services to stabilize

$healthTest = Test-Endpoint "http://localhost:8000/api/v1/health" "Backend Health"
if ($healthTest) {
    Test-Endpoint "http://localhost:8000/api/v1/status" "Backend Status"
    Test-Endpoint "http://localhost:8000/api/v1/system/info" "System Info"
    Test-WebPage "http://localhost:8000/docs" "API Documentation"
}

# Test AI Endpoints
Write-Host "`nTesting AI/ML Endpoints..." -ForegroundColor Yellow
if ($healthTest) {
    # Test with POST data for analysis
    try {
        $analysisData = @{
            url = "https://example.com"
            text = "Test analysis"
        } | ConvertTo-Json
        
        $analysis = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method POST -Body $analysisData -ContentType "application/json" -TimeoutSec 10
        Write-Host "[AI Analysis] PASS - Confidence: $($analysis.data.confidence)" -ForegroundColor Green
    }
    catch {
        Write-Host "[AI Analysis] FAIL - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Test-Endpoint "http://localhost:8000/api/v1/search/clip?query=test" "CLIP Search"
    Test-Endpoint "http://localhost:8000/api/v1/gpu/status" "GPU Monitoring"
}

# Test Database Services
Write-Host "`nTesting Database Services..." -ForegroundColor Yellow
try {
    $redisTest = docker exec test_model-redis-1 redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "[Redis] PASS - Redis is responding" -ForegroundColor Green
    } else {
        Write-Host "[Redis] FAIL - No response" -ForegroundColor Red
    }
}
catch {
    Write-Host "[Redis] FAIL - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $pgTest = docker exec test_model-postgres-1 pg_isready -U postgres 2>$null
    if ($pgTest -like "*accepting connections*") {
        Write-Host "[PostgreSQL] PASS - Database accepting connections" -ForegroundColor Green
    } else {
        Write-Host "[PostgreSQL] FAIL - Not accepting connections" -ForegroundColor Red
    }
}
catch {
    Write-Host "[PostgreSQL] FAIL - $($_.Exception.Message)" -ForegroundColor Red
}

# Test Other Services
Write-Host "`nTesting Other Services..." -ForegroundColor Yellow
Test-WebPage "http://localhost:3002" "Grafana Monitoring"
Test-WebPage "http://localhost:9090" "Prometheus Metrics"
Test-Endpoint "http://localhost:3001/health" "Scraper Service"

# Test with Real Data
Write-Host "`nTesting with Real Product Data..." -ForegroundColor Yellow
if ($healthTest) {
    try {
        $realProductData = @{
            url = "https://www.amazon.com/dp/B08N5WRWNW"
            text = "Amazon Echo Dot (4th Gen) | Smart speaker with Alexa | Charcoal"
            deep_analysis = $true
        } | ConvertTo-Json
        
        $realAnalysis = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method POST -Body $realProductData -ContentType "application/json" -TimeoutSec 15
        Write-Host "[Real Data Test] PASS - Analyzed real product: $($realAnalysis.data.result)" -ForegroundColor Green
    }
    catch {
        Write-Host "[Real Data Test] FAIL - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Container Status Summary
Write-Host "`nContainer Status Summary:" -ForegroundColor Yellow
try {
    docker compose -f docker-compose.complete.yml ps
}
catch {
    Write-Host "Failed to get container status" -ForegroundColor Red
}

# Generate URLs for manual testing
Write-Host "`n=== MANUAL TESTING URLS ===" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:8080" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White  
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Grafana: http://localhost:3002 (admin/admin)" -ForegroundColor White
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "Flower (Celery): http://localhost:5555" -ForegroundColor White

Write-Host "`n=== NEXT STEPS FOR MODEL TRAINING ===" -ForegroundColor Cyan
Write-Host "1. Collect real product data through scraper service" -ForegroundColor White
Write-Host "2. Prepare training datasets in ./training_data/ directory" -ForegroundColor White
Write-Host "3. Train price prediction models using collected data" -ForegroundColor White
Write-Host "4. Train product classification and recommendation models" -ForegroundColor White
Write-Host "5. Deploy trained models to ./models/ directory" -ForegroundColor White

Write-Host "`nTesting completed! Check the manual URLs above." -ForegroundColor Green
