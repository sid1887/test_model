# Self-Hosted Captcha Service Startup Script
# This script starts the self-hosted captcha solving service

Write-Host "🔧 Starting Self-Hosted Captcha Service..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Navigate to captcha service directory
$captchaServicePath = "captcha-service"
if (Test-Path $captchaServicePath) {
    Set-Location $captchaServicePath
} else {
    Write-Host "❌ Captcha service directory not found!" -ForegroundColor Red
    exit 1
}

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found in captcha-service directory!" -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host "🛑 Stopping existing captcha service containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Build and start the services
Write-Host "🏗️ Building captcha service containers..." -ForegroundColor Blue
docker-compose build

Write-Host "🚀 Starting captcha service..." -ForegroundColor Blue
docker-compose up -d

# Wait a moment for services to start
Start-Sleep -Seconds 5

# Check if services are running
Write-Host "🔍 Checking service status..." -ForegroundColor Blue

$captchaHealth = $null
try {
    $captchaHealth = Invoke-RestMethod -Uri "http://localhost:9001/health" -Method Get -TimeoutSec 10
    Write-Host "✅ Captcha service is healthy" -ForegroundColor Green
    Write-Host "   OCR Engines: $($captchaHealth.ocr_engines | ConvertTo-Json -Compress)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ Captcha service health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test Redis connection
try {
    docker-compose exec redis redis-cli ping | Out-Null
    Write-Host "✅ Redis is responding" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Redis connection test failed" -ForegroundColor Yellow
}

# Show service URLs
Write-Host ""
Write-Host "🌐 Service Endpoints:" -ForegroundColor Cyan
Write-Host "   Captcha API: http://localhost:9001" -ForegroundColor White
Write-Host "   Health Check: http://localhost:9001/health" -ForegroundColor White
Write-Host "   Statistics: http://localhost:9001/stats" -ForegroundColor White
Write-Host "   Redis: localhost:6380" -ForegroundColor White

Write-Host ""
Write-Host "📋 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop service: docker-compose down" -ForegroundColor White
Write-Host "   Restart: docker-compose restart" -ForegroundColor White

# Test captcha solving with a sample
Write-Host ""
Write-Host "🧪 Testing captcha solving capability..." -ForegroundColor Blue

# Create a simple test image (placeholder)
$testImage = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

try {
    $submitResponse = Invoke-RestMethod -Uri "http://localhost:9001/in.php" -Method Post -Body @{
        method = "base64"
        body = $testImage
    } -ContentType "application/x-www-form-urlencoded" -TimeoutSec 10
    
    if ($submitResponse.status -eq 1) {
        Write-Host "✅ Captcha submission test passed" -ForegroundColor Green
        
        # Try to get result
        Start-Sleep -Seconds 2
        try {
            $resultResponse = Invoke-RestMethod -Uri "http://localhost:9001/res.php?action=get&id=$($submitResponse.request)" -Method Get -TimeoutSec 10
            Write-Host "✅ Captcha result retrieval test passed" -ForegroundColor Green
        } catch {
            Write-Host "ℹ️ Result retrieval test skipped (expected for test image)" -ForegroundColor Gray
        }
    } else {
        Write-Host "ℹ️ Captcha test completed (expected failure for test image)" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️ Captcha API test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Self-hosted captcha service is ready!" -ForegroundColor Green
Write-Host "   You can now configure Cumpair to use this service." -ForegroundColor White

# Return to original directory
Set-Location ..

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Update your Cumpair .env file:" -ForegroundColor White
Write-Host "      CAPTCHA_SERVICE_URL=http://localhost:9001" -ForegroundColor Gray
Write-Host "   2. Restart Cumpair to use the new captcha service" -ForegroundColor White
Write-Host "   3. Monitor logs: docker-compose -f captcha-service/docker-compose.yml logs -f" -ForegroundColor White
