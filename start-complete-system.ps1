# 🚀 Complete System Startup Script
# Starts backend + frontend together

Write-Host "`n🔥 Starting Cumpair Complete System..." -ForegroundColor Yellow

# Step 1: Start Backend Services
Write-Host "`n📦 Starting backend services..." -ForegroundColor Cyan
docker-compose -f docker-compose.secure.yml up -d

# Step 2: Wait for services
Write-Host "`n⏳ Waiting for services to be ready (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# Step 3: Start Workers
Write-Host "`n👷 Starting event workers..." -ForegroundColor Cyan
docker exec -d test_model-web-1 python -m app.workers.manager

# Step 4: Check Health
Write-Host "`n🏥 Checking service health..." -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "http://localhost:8000/health/services" -ErrorAction SilentlyContinue

if ($health) {
    Write-Host "✅ Backend is healthy!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Backend health check failed" -ForegroundColor Yellow
}

# Step 5: Start Frontend
Write-Host "`n🎨 Starting frontend development server..." -ForegroundColor Cyan
Write-Host "   Navigate to frontend directory and run: npm run dev" -ForegroundColor White
Write-Host "   Or open: http://localhost:5173/search" -ForegroundColor White

Write-Host "`n✨ System startup complete!" -ForegroundColor Green
Write-Host "`n📍 URLs:" -ForegroundColor Yellow
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173 (after npm run dev)" -ForegroundColor White
Write-Host "   Search Page: http://localhost:5173/search" -ForegroundColor White
Write-Host "   Health: http://localhost:8000/health/services" -ForegroundColor White
Write-Host "   Metrics: http://localhost:8000/metrics" -ForegroundColor White

Write-Host "`n🎯 Quick Tests:" -ForegroundColor Yellow
Write-Host "   1. Open http://localhost:5173/search" -ForegroundColor White
Write-Host "   2. Search for 'iPhone 15'" -ForegroundColor White
Write-Host "   3. Upload a product image" -ForegroundColor White
Write-Host "   4. Check AI analysis results" -ForegroundColor White

Write-Host "`n"
