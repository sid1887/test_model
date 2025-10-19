# Quick Docker Fix Script for Windows PowerShell
# This script addresses all Docker issues immediately

Write-Host "🚀 Quick Docker Fix Script Starting..." -ForegroundColor Green

# Step 1: Stop and remove existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Step 2: Remove old images to force rebuild
Write-Host "🗑️ Removing old images..." -ForegroundColor Yellow
docker-compose down --rmi all

# Step 3: Build with no cache to ensure fresh build
Write-Host "🏗️ Building fresh containers..." -ForegroundColor Yellow
docker-compose build --no-cache

# Step 4: Start services
Write-Host "🚀 Starting services..." -ForegroundColor Green
docker-compose up -d postgres redis

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 5: Run the web service with fixes
Write-Host "🌐 Starting web service..." -ForegroundColor Green
docker-compose run --rm web bash -c "
    echo '🔧 Applying fixes...'
    python /app/fix_all_issues.py
    echo '🏥 Running health check...'
    python /app/simple_health_check.py
    echo '🚀 Starting application...'
    python main.py
"

Write-Host "✅ Docker fix complete!" -ForegroundColor Green