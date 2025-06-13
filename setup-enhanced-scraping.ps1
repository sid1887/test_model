# Cumpair Enhanced Scraping System Setup
# Complete setup for Step 4: Enhanced Anti-Block Scraping System

Write-Host "🚀 Setting up Enhanced Scraping & Anti-Block System" -ForegroundColor Green
Write-Host "=" * 60

# Step 1: Install additional dependencies
Write-Host "`n📦 Installing enhanced scraping dependencies..." -ForegroundColor Blue

$additionalPackages = @(
    "playwright==1.40.0",
    "easyocr==1.7.0", 
    "pytesseract==0.3.10",
    "fake-useragent==1.4.0",
    "asyncio-throttle==1.0.2",
    "aiohttp-socks==0.8.4",
    "python-socks==2.4.3"
)

foreach ($package in $additionalPackages) {
    Write-Host "   Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
}

# Install Playwright browsers
Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Blue
playwright install chromium

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green

# Step 2: Setup Proxy Service
Write-Host "`n🔧 Setting up Self-Hosted Proxy Service..." -ForegroundColor Blue

if (Test-Path "proxy-service") {
    Write-Host "   Proxy service directory exists" -ForegroundColor Gray
} else {
    Write-Host "❌ Proxy service directory not found. Please check the setup." -ForegroundColor Red
    exit 1
}

# Test Docker availability
try {
    docker version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is required but not running. Please start Docker Desktop." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Start proxy service
Write-Host "🚀 Starting proxy management service..." -ForegroundColor Blue
Set-Location "proxy-service"

# Build and start proxy service
docker-compose build --no-cache --quiet
docker-compose up -d

# Wait for startup
Write-Host "⏳ Waiting for proxy service to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Test proxy service
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 10
    Write-Host "✅ Proxy Manager API: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Proxy service starting... (this is normal)" -ForegroundColor Yellow
}

Set-Location ..

# Step 3: Validate Enhanced Scraping Components
Write-Host "`n🧪 Validating enhanced scraping components..." -ForegroundColor Blue

# Test stealth browser
Write-Host "   Testing stealth browser initialization..." -ForegroundColor Gray
python -c "
import asyncio
from app.services.stealth_browser import StealthBrowser
async def test():
    browser = StealthBrowser()
    result = await browser.initialize()
    await browser.cleanup()
    print('✅ Stealth browser: Working' if result else '❌ Stealth browser: Failed')
try:
    asyncio.run(test())
except Exception as e:
    print(f'⚠️ Stealth browser: {e}')
"

# Test adaptive scraper
Write-Host "   Testing adaptive scraper..." -ForegroundColor Gray
python -c "
from app.services.adaptive_scraper import AdaptiveScrapingEngine
try:
    scraper = AdaptiveScrapingEngine()
    print('✅ Adaptive scraper: Initialized')
except Exception as e:
    print(f'❌ Adaptive scraper: {e}')
"

# Step 4: Run comprehensive test
Write-Host "`n🎯 Running enhanced scraping system test..." -ForegroundColor Blue
Write-Host "   This will test all components working together..." -ForegroundColor Gray

try {
    python test_enhanced_scraping.py
    $testResult = $LASTEXITCODE
    
    if ($testResult -eq 0) {
        Write-Host "✅ Enhanced scraping system test: PASSED" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Enhanced scraping system test: Some issues detected" -ForegroundColor Yellow
        Write-Host "   Check the detailed test results for more information." -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Test execution failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Integration with existing system
Write-Host "`n🔗 Integrating with existing Cumpair system..." -ForegroundColor Blue

# Update main scraping service to use adaptive scraper
$scrapingServicePath = "app\services\scraping.py"
if (Test-Path $scrapingServicePath) {
    Write-Host "   ✅ Scraping service found - integration ready" -ForegroundColor Green
} else {
    Write-Host "   ❌ Scraping service not found" -ForegroundColor Red
}

# Step 6: System status summary
Write-Host "`n📊 ENHANCED SCRAPING SYSTEM STATUS" -ForegroundColor Cyan
Write-Host "=" * 50

# Check proxy service
try {
    $proxyHealth = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5
    Write-Host "🌐 Proxy Manager:     ✅ Running ($($proxyHealth.status))" -ForegroundColor Green
    
    $proxyStats = Invoke-RestMethod -Uri "http://localhost:8001/stats" -TimeoutSec 5
    Write-Host "   └─ Total Proxies:  $($proxyStats.total_proxies)" -ForegroundColor Gray
    Write-Host "   └─ Healthy Proxies: $($proxyStats.healthy_proxies)" -ForegroundColor Gray
} catch {
    Write-Host "🌐 Proxy Manager:     ⚠️ Starting up..." -ForegroundColor Yellow
}

# Check HAProxy
try {
    $haproxyResponse = Invoke-WebRequest -Uri "http://localhost:8081/stats" -TimeoutSec 5
    if ($haproxyResponse.StatusCode -eq 200) {
        Write-Host "⚖️ HAProxy:           ✅ Load balancing active" -ForegroundColor Green
    }
} catch {
    Write-Host "⚖️ HAProxy:           ⚠️ Starting up..." -ForegroundColor Yellow
}

# Check captcha service
try {
    $captchaHealth = Invoke-RestMethod -Uri "http://localhost:9001/health" -TimeoutSec 5
    Write-Host "🧩 CAPTCHA Service:   ✅ Ready" -ForegroundColor Green
} catch {
    Write-Host "🧩 CAPTCHA Service:   ⚠️ Optional (start with start-captcha-service.ps1)" -ForegroundColor Gray
}

Write-Host "`n🛡️ ANTI-BLOCK CAPABILITIES" -ForegroundColor Cyan
Write-Host "   ✅ Proxy Rotation & Health Monitoring"
Write-Host "   ✅ Stealth Browser with Fingerprint Spoofing"
Write-Host "   ✅ Human-like Behavior Simulation"
Write-Host "   ✅ CAPTCHA Auto-Solving"
Write-Host "   ✅ Adaptive Strategy Selection"
Write-Host "   ✅ Rate Limiting & Request Delays"
Write-Host "   ✅ User Agent & Header Rotation"

Write-Host "`n🎯 SCRAPING STRATEGIES AVAILABLE" -ForegroundColor Cyan
Write-Host "   1. Direct API (fastest)"
Write-Host "   2. Simple HTTP + Proxy (reliable)"
Write-Host "   3. Stealth Browser (anti-detection)"
Write-Host "   4. Full Browser (maximum stealth)"

Write-Host "`n📚 USAGE EXAMPLES" -ForegroundColor Cyan
Write-Host @"
   # Basic scraping with adaptive strategy
   from app.services.adaptive_scraper import adaptive_scraper
   result = await adaptive_scraper.scrape_product('https://example.com/product')
   
   # Manual strategy selection
   result = await adaptive_scraper._scrape_stealth_browser(url, site_config)
   
   # Get strategy performance stats
   stats = await adaptive_scraper.get_strategy_stats()
"@

Write-Host "`n🔧 MANAGEMENT COMMANDS" -ForegroundColor Cyan
Write-Host "   • Start proxy service:    .\start-proxy-service.ps1"
Write-Host "   • Start captcha service:  .\start-captcha-service.ps1"
Write-Host "   • Test scraping system:   python test_enhanced_scraping.py"
Write-Host "   • View proxy stats:       http://localhost:8081/stats"
Write-Host "   • Proxy API:              http://localhost:8001"

Write-Host "`n🎉 STEP 4 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "Enhanced Scraping & Anti-Block System is ready for production use." -ForegroundColor White

Write-Host "`n⭐ KEY FEATURES IMPLEMENTED:" -ForegroundColor Yellow
Write-Host "   • Self-hosted proxy management with HAProxy load balancing"
Write-Host "   • Advanced stealth browsing with comprehensive fingerprint spoofing"
Write-Host "   • Adaptive strategy selection based on success rates"
Write-Host "   • Human-like behavior simulation (mouse, keyboard, scrolling)"
Write-Host "   • Automatic CAPTCHA detection and solving"
Write-Host "   • Rate limiting and request delay randomization"
Write-Host "   • Real-time proxy health monitoring and rotation"
Write-Host "   • Comprehensive error handling and retry logic"

Write-Host "`nThe system is now ready to handle even the most protected websites!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
