# Cumpair Enhanced Proxy Service Startup Script
# Starts the self-hosted proxy management service with HAProxy

Write-Host "🚀 Starting Cumpair Proxy Management Service..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Change to proxy service directory
Set-Location "proxy-service"

# Check if services are already running
$existingServices = docker-compose ps -q
if ($existingServices) {
    Write-Host "⚠️ Proxy services are already running. Stopping them first..." -ForegroundColor Yellow
    docker-compose down
    Start-Sleep -Seconds 3
}

# Build and start the services
Write-Host "🔨 Building proxy management services..." -ForegroundColor Blue
docker-compose build --no-cache

Write-Host "🚀 Starting proxy management services..." -ForegroundColor Blue
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "`n🔍 Checking service health..." -ForegroundColor Blue

try {
    # Check proxy manager API
    $apiResponse = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5
    Write-Host "✅ Proxy Manager API: $($apiResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Proxy Manager API: Not responding" -ForegroundColor Red
}

try {
    # Check HAProxy stats
    $haproxyResponse = Invoke-WebRequest -Uri "http://localhost:8081/stats" -TimeoutSec 5
    if ($haproxyResponse.StatusCode -eq 200) {
        Write-Host "✅ HAProxy Stats: Available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ HAProxy Stats: Not responding" -ForegroundColor Red
}

try {
    # Check Redis
    $redisTest = docker exec -it cumpair-proxy-redis redis-cli ping
    if ($redisTest -like "*PONG*") {
        Write-Host "✅ Redis: Connected" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Redis: Connection failed" -ForegroundColor Red
}

Write-Host "`n📊 Service URLs:" -ForegroundColor Cyan
Write-Host "   • Proxy Manager API: http://localhost:8001" -ForegroundColor White
Write-Host "   • HAProxy Stats: http://localhost:8081/stats" -ForegroundColor White
Write-Host "   • Redis: localhost:6380" -ForegroundColor White

Write-Host "`n🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "   • View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   • Stop services: docker-compose down" -ForegroundColor White
Write-Host "   • Restart services: docker-compose restart" -ForegroundColor White

# Test proxy fetching
Write-Host "`n🧪 Testing proxy functionality..." -ForegroundColor Blue
try {
    Start-Sleep -Seconds 5  # Give more time for initialization
    $proxiesResponse = Invoke-RestMethod -Uri "http://localhost:8001/proxies" -TimeoutSec 10
    $proxyCount = $proxiesResponse.Count
    Write-Host "✅ Proxy pool initialized with $proxyCount proxies" -ForegroundColor Green
    
    # Trigger free proxy refresh
    $refreshResponse = Invoke-RestMethod -Uri "http://localhost:8001/proxies/refresh" -Method Post -TimeoutSec 10
    Write-Host "✅ Free proxy refresh initiated" -ForegroundColor Green
    
} catch {
    Write-Host "⚠️ Proxy functionality test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   This is normal on first startup. Proxies will be loaded in the background." -ForegroundColor Gray
}

Write-Host "`n🎉 Proxy Management Service startup complete!" -ForegroundColor Green
Write-Host "   The service will continue to discover and health-check proxies automatically." -ForegroundColor Gray

# Return to original directory
Set-Location ..

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
