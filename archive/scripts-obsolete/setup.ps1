# Compair Project Setup Script
# Run this script to set up the development environment

Write-Host "🔍 Setting up Compair - AI-Powered Price Comparison System" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Blue

# Check if Python is installed
Write-Host "`n📋 Checking Prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Docker not found. You can still run without Docker but some features may be limited." -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "`n📁 Creating project directories..." -ForegroundColor Yellow
$directories = @("uploads", "models", "models/clip_cache", "logs", "config")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "✅ Directory exists: $dir" -ForegroundColor Green
    }
}

# Install Python dependencies
Write-Host "`n🐍 Installing Python dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    Write-Host "Try running: pip install -r requirements.txt" -ForegroundColor Yellow
}

# Install Node.js dependencies for scraper
Write-Host "`n📦 Installing Node.js scraper dependencies..." -ForegroundColor Yellow
Set-Location scraper
try {
    npm install
    Write-Host "✅ Node.js dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
    Write-Host "Try running: cd scraper && npm install" -ForegroundColor Yellow
}
Set-Location ..

# Download YOLOv8 model
Write-Host "`n🤖 Downloading AI models..." -ForegroundColor Yellow
if (!(Test-Path "models/yolov8n.pt")) {
    Write-Host "Downloading YOLOv8 nano model..." -ForegroundColor Cyan
    try {
        python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); model.save('models/yolov8n.pt')"
        Write-Host "✅ YOLOv8 model downloaded" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Could not download YOLOv8 model automatically" -ForegroundColor Yellow
        Write-Host "It will be downloaded on first use" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ YOLOv8 model already exists" -ForegroundColor Green
}

# Initialize CLIP model cache
Write-Host "`n🔗 Initializing CLIP model..." -ForegroundColor Yellow
try {
    python -c "import clip; clip.load('ViT-B/32')"
    Write-Host "✅ CLIP model initialized" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not initialize CLIP model" -ForegroundColor Yellow
    Write-Host "It will be downloaded on first use" -ForegroundColor Yellow
}

# Create environment file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "`n⚙️ Creating environment configuration..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    Write-Host "✅ Environment file created. Please review .env file." -ForegroundColor Green
} else {
    Write-Host "✅ Environment file already exists" -ForegroundColor Green
}

# Database setup instructions
Write-Host "`n🗄️ Database Setup Required:" -ForegroundColor Yellow
Write-Host "Option 1 - Docker (Recommended):" -ForegroundColor Cyan
Write-Host "  docker-compose up -d postgres redis rota" -ForegroundColor White
Write-Host "Option 2 - Local Installation:" -ForegroundColor Cyan
Write-Host "  Install PostgreSQL and Redis locally" -ForegroundColor White
Write-Host "  Update DATABASE_URL and REDIS_URL in .env" -ForegroundColor White

Write-Host "`n🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Start the services:" -ForegroundColor Cyan
Write-Host "   docker-compose up -d  # Start all services" -ForegroundColor White
Write-Host "   # OR" -ForegroundColor Gray
Write-Host "   Start PostgreSQL and Redis manually" -ForegroundColor White
Write-Host ""
Write-Host "2. Start the scraper service:" -ForegroundColor Cyan
Write-Host "   cd scraper" -ForegroundColor White
Write-Host "   npm start" -ForegroundColor White
Write-Host ""
Write-Host "3. Start the main application:" -ForegroundColor Cyan
Write-Host "   python main.py" -ForegroundColor White
Write-Host ""
Write-Host "4. Access the application:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000" -ForegroundColor White
Write-Host "   http://localhost:8000/docs (API Documentation)" -ForegroundColor White

Write-Host "`n✨ Setup completed! Ready to start Compair." -ForegroundColor Green
Write-Host "For issues, check the README.md or logs/" -ForegroundColor Yellow
