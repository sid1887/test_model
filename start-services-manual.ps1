# CUMPAIR MANUAL SERVICES STARTUP GUIDE
# Start all services locally for testing before Docker deployment

Write-Host "CUMPAIR - Starting All Services Manually" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (!(Test-Path "main.py")) {
    Write-Host "ERROR: Please run this script from the Cumpair root directory (d:\dev_packages\test_model)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SERVICE STARTUP ORDER:" -ForegroundColor Yellow
Write-Host "1. PostgreSQL (Port 5432)" -ForegroundColor White
Write-Host "2. Redis (Port 6379)" -ForegroundColor White
Write-Host "3. FastAPI Backend (Port 8000)" -ForegroundColor White
Write-Host "4. Node.js Scraper (Port 3001)" -ForegroundColor White
Write-Host "5. Frontend Dev Server (Port 8080)" -ForegroundColor White
Write-Host "6. Optional: CAPTCHA Service (Port 9001)" -ForegroundColor Gray
Write-Host "7. Optional: Proxy Service (Port 8001)" -ForegroundColor Gray
Write-Host "8. Optional: Celery Worker & Flower (Port 5555)" -ForegroundColor Gray
Write-Host ""

Write-Host "PREREQUISITES CHECK:" -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "OK Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "OK Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
try {
    $pgVersion = psql --version 2>&1
    Write-Host "OK PostgreSQL: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING PostgreSQL CLI not found. Make sure PostgreSQL is installed and running" -ForegroundColor Yellow
}

# Check Redis
try {
    $redisResult = redis-cli ping 2>&1
    if ($redisResult -eq "PONG") {
        Write-Host "OK Redis: Running and responding" -ForegroundColor Green
    } else {
        Write-Host "WARNING Redis: Not responding ($redisResult)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING Redis CLI not found. Make sure Redis is installed and running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "MANUAL STARTUP INSTRUCTIONS:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "1. START INFRASTRUCTURE SERVICES" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow

Write-Host ""
Write-Host "PostgreSQL (Port 5432):" -ForegroundColor White
Write-Host "  Windows: " -NoNewline -ForegroundColor Gray
Write-Host "net start postgresql-x64-15" -ForegroundColor Cyan
Write-Host "  OR manually start PostgreSQL service from Services.msc" -ForegroundColor Gray
Write-Host "  Database: compair, User: compair, Password: compair123" -ForegroundColor Gray

Write-Host ""
Write-Host "Redis (Port 6379):" -ForegroundColor White
Write-Host "  Command: " -NoNewline -ForegroundColor Gray
Write-Host "redis-server" -ForegroundColor Cyan
Write-Host "  OR start Redis Windows service" -ForegroundColor Gray

Write-Host ""
Write-Host "2. START MAIN SERVICES" -ForegroundColor Yellow
Write-Host "-------------------------" -ForegroundColor Yellow

Write-Host ""
Write-Host "FastAPI Backend (Port 8000):" -ForegroundColor White
Write-Host "  Terminal 1:" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model" -ForegroundColor Cyan
Write-Host "  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Cyan
Write-Host "  Test: http://localhost:8000/docs" -ForegroundColor Gray

Write-Host ""
Write-Host "Node.js Scraper (Port 3001):" -ForegroundColor White
Write-Host "  Terminal 2:" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model\scraper" -ForegroundColor Cyan
Write-Host "  npm install  # if not done" -ForegroundColor Cyan
Write-Host "  npm start    # or: node server.js" -ForegroundColor Cyan
Write-Host "  Test: http://localhost:3001/health" -ForegroundColor Gray

Write-Host ""
Write-Host "Frontend Dev Server (Port 8080):" -ForegroundColor White
Write-Host "  Terminal 3:" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model\frontend" -ForegroundColor Cyan
Write-Host "  npm install  # if not done" -ForegroundColor Cyan
Write-Host "  npm run dev  # Vite development server" -ForegroundColor Cyan
Write-Host "  Access: http://localhost:8080" -ForegroundColor Gray

Write-Host ""
Write-Host "3. OPTIONAL SERVICES" -ForegroundColor Yellow
Write-Host "-----------------------" -ForegroundColor Yellow

Write-Host ""
Write-Host "CAPTCHA Service (Port 9001):" -ForegroundColor White
Write-Host "  Terminal 4:" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model\captcha-service" -ForegroundColor Cyan
Write-Host "  pip install -r requirements.txt  # if not done" -ForegroundColor Cyan
Write-Host "  python app.py" -ForegroundColor Cyan
Write-Host "  Test: http://localhost:9001/health" -ForegroundColor Gray

Write-Host ""
Write-Host "Proxy Service (Port 8001):" -ForegroundColor White
Write-Host "  Terminal 5:" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model\proxy-service" -ForegroundColor Cyan
Write-Host "  pip install -r requirements.txt  # if not done" -ForegroundColor Cyan
Write-Host "  python proxy_manager.py" -ForegroundColor Cyan
Write-Host "  Test: http://localhost:8001/health" -ForegroundColor Gray

Write-Host ""
Write-Host "Celery Worker & Flower:" -ForegroundColor White
Write-Host "  Terminal 6 (Worker):" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model" -ForegroundColor Cyan
Write-Host "  celery -A app.worker worker --loglevel=info" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 7 (Flower - Port 5555):" -ForegroundColor Gray
Write-Host "  cd d:\dev_packages\test_model" -ForegroundColor Cyan
Write-Host "  celery -A app.worker flower --port=5555" -ForegroundColor Cyan
Write-Host "  Access: http://localhost:5555" -ForegroundColor Gray

Write-Host ""
Write-Host "4. MONITORING (Optional)" -ForegroundColor Yellow
Write-Host "---------------------------" -ForegroundColor Yellow

Write-Host ""
Write-Host "Prometheus (Port 9090):" -ForegroundColor White
Write-Host "  Follow Prometheus installation guide" -ForegroundColor Gray
Write-Host "  Config: ./monitoring/prometheus.yml" -ForegroundColor Gray

Write-Host ""
Write-Host "Grafana (Port 3002):" -ForegroundColor White
Write-Host "  Follow Grafana installation guide" -ForegroundColor Gray
Write-Host "  Access: http://localhost:3002 (admin/admin)" -ForegroundColor Gray

Write-Host ""
Write-Host "5. VERIFICATION COMMANDS" -ForegroundColor Yellow
Write-Host "---------------------------" -ForegroundColor Yellow

Write-Host ""
Write-Host "Health Checks:" -ForegroundColor White
Write-Host "curl http://localhost:8000/api/v1/health   # Backend API" -ForegroundColor Cyan
Write-Host "curl http://localhost:3000/health          # Scraper Service" -ForegroundColor Cyan
Write-Host "curl http://localhost:9001/health          # CAPTCHA Service" -ForegroundColor Cyan
Write-Host "curl http://localhost:8001/health          # Proxy Service" -ForegroundColor Cyan

Write-Host ""
Write-Host "Web Interfaces:" -ForegroundColor White
Write-Host "http://localhost:8080                      # Frontend App" -ForegroundColor Cyan
Write-Host "http://localhost:8000/docs                 # API Documentation" -ForegroundColor Cyan
Write-Host "http://localhost:5555                      # Celery Flower" -ForegroundColor Cyan

Write-Host ""
Write-Host "6. STARTUP CHECKLIST" -ForegroundColor Yellow
Write-Host "-----------------------" -ForegroundColor Yellow

Write-Host "[ ] PostgreSQL running on port 5432" -ForegroundColor White
Write-Host "[ ] Redis running on port 6379" -ForegroundColor White
Write-Host "[ ] FastAPI backend on port 8000" -ForegroundColor White
Write-Host "[ ] Node.js scraper on port 3001" -ForegroundColor White
Write-Host "[ ] Frontend dev server on port 8080" -ForegroundColor White
Write-Host "[ ] All health checks passing" -ForegroundColor White
Write-Host "[ ] Can upload and analyze images" -ForegroundColor White
Write-Host "[ ] Price comparison working" -ForegroundColor White

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Green
Write-Host "1. Start infrastructure services (PostgreSQL, Redis)" -ForegroundColor White
Write-Host "2. Start core services (Backend, Scraper, Frontend)" -ForegroundColor White
Write-Host "3. Test the complete workflow" -ForegroundColor White
Write-Host "4. Add optional services as needed" -ForegroundColor White

Write-Host ""
Write-Host "NOTE: Open each service in a separate terminal window for easier monitoring" -ForegroundColor Yellow
Write-Host "Ready to start? Follow the commands above in order!" -ForegroundColor Green
