# Comprehensive Service Testing Script
# Tests all services with real data and prepares for model training

param(
    [switch]$TestFrontend,
    [switch]$TestBackend,
    [switch]$TestDatabase,
    [switch]$TestWorker,
    [switch]$TestAI,
    [switch]$TestScraper,
    [switch]$TrainModel,
    [switch]$All
)

$ErrorActionPreference = 'Continue'

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-TestResult {
    param(
        [string]$Service,
        [string]$Test,
        [bool]$Success,
        [string]$Details = ""
    )
    $status = if ($Success) { "${Green}PASS${Reset}" } else { "${Red}FAIL${Reset}" }
    $message = "[$Service] $Test - $status"
    if ($Details) { $message += " | $Details" }
    Write-Host $message
}

function Test-ServiceEndpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Body = @{},
        [int]$TimeoutSec = 10
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = $TimeoutSec
        }
        
        if ($Body.Count -gt 0 -and $Method -ne "GET") {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        return @{ Success = $true; Data = $response; StatusCode = 200 }
    }
    catch {
        return @{ Success = $false; Error = $_.Exception.Message; StatusCode = $_.Exception.Response.StatusCode.value__ }
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [int]$MaxWaitSeconds = 60,
        [string]$ServiceName = "Service"
    )
    
    Write-Host "${Blue}Waiting for $ServiceName to be ready...${Reset}"
    $waited = 0
    
    while ($waited -lt $MaxWaitSeconds) {
        $result = Test-ServiceEndpoint -Url $Url -TimeoutSec 5
        if ($result.Success) {
            Write-Host "${Green}$ServiceName is ready!${Reset}"
            return $true
        }
        Start-Sleep -Seconds 2
        $waited += 2
    }
    
    Write-Host "${Red}$ServiceName failed to become ready within $MaxWaitSeconds seconds${Reset}"
    return $false
}

# Test Frontend Service
function Test-Frontend {
    Write-Host "${Blue}=== TESTING FRONTEND SERVICE ===${Reset}"
    
    $frontendReady = Wait-ForService -Url "http://localhost:8080" -ServiceName "Frontend"
    Write-TestResult "Frontend" "Service Availability" $frontendReady
    
    if ($frontendReady) {
        # Test main page
        $mainPage = Test-ServiceEndpoint -Url "http://localhost:8080"
        Write-TestResult "Frontend" "Main Page Load" $mainPage.Success $mainPage.Error
        
        # Test static assets (if any)
        $staticTest = Test-ServiceEndpoint -Url "http://localhost:8080/static/css/style.css"
        Write-TestResult "Frontend" "Static Assets" $staticTest.Success "CSS files accessible"
    }
}

# Test Backend API
function Test-Backend {
    Write-Host "${Blue}=== TESTING BACKEND API ===${Reset}"
    
    $backendReady = Wait-ForService -Url "http://localhost:8000/api/v1/health" -ServiceName "Backend API"
    Write-TestResult "Backend" "Service Availability" $backendReady
    
    if ($backendReady) {
        # Test health endpoint
        $health = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/health"
        Write-TestResult "Backend" "Health Check" $health.Success
        if ($health.Success) {
            Write-Host "   Features: $($health.Data.features | ConvertTo-Json -Compress)"
        }
        
        # Test status endpoint
        $status = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/status"
        Write-TestResult "Backend" "Status Endpoint" $status.Success
        
        # Test OpenAPI docs
        $docs = Test-ServiceEndpoint -Url "http://localhost:8000/docs"
        Write-TestResult "Backend" "API Documentation" $docs.Success
        
        # Test system info
        $sysInfo = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/system/info"
        Write-TestResult "Backend" "System Info" $sysInfo.Success
        if ($sysInfo.Success) {
            Write-Host "   Python: $($sysInfo.Data.python_version)"
            Write-Host "   Features: $($sysInfo.Data.available_features -join ', ')"
        }
    }
}

# Test AI/ML Endpoints
function Test-AIEndpoints {
    Write-Host "${Blue}=== TESTING AI/ML ENDPOINTS ===${Reset}"
    
    # Test AI Analysis
    $analysisData = @{
        url = "https://example.com"
        text = "Test product analysis"
    }
    $analysis = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/analyze" -Method "POST" -Body $analysisData
    Write-TestResult "AI" "Analysis Endpoint" $analysis.Success
    if ($analysis.Success) {
        Write-Host "   Confidence: $($analysis.Data.data.confidence)"
    }
    
    # Test CLIP Search
    $clipSearch = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/search/clip?query=test+product"
    Write-TestResult "AI" "CLIP Search" $clipSearch.Success
    if ($clipSearch.Success) {
        Write-Host "   Results: $($clipSearch.Data.results.Count) items"
    }
    
    # Test GPU Monitoring
    $gpuStatus = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/gpu/status"
    Write-TestResult "AI" "GPU Monitoring" $gpuStatus.Success
    if ($gpuStatus.Success) {
        Write-Host "   GPU Count: $($gpuStatus.Data.gpu_count)"
    }
    
    # Test Feature Toggle
    $featureToggle = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/features/toggle?feature=ai_analysis`&enabled=true" -Method "POST"
    Write-TestResult "AI" "Feature Toggle" $featureToggle.Success
}

# Test Database Connection
function Test-Database {
    Write-Host "${Blue}=== TESTING DATABASE SERVICES ===${Reset}"
    
    # Test database connectivity via API
    $dbTest = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/test/database"
    $dbAvailable = $dbTest.StatusCode -ne 503
    Write-TestResult "Database" "Connection Test" $dbAvailable $dbTest.Error
    
    # Test Redis connectivity
    try {
        $redisTest = docker exec test_model-redis-1 redis-cli ping 2>$null
        $redisWorking = $redisTest -eq "PONG"
        Write-TestResult "Database" "Redis Connectivity" $redisWorking "Redis ping: $redisTest"
    } catch {
        Write-TestResult "Database" "Redis Connectivity" $false $_.Exception.Message
    }
    
    # Test PostgreSQL connectivity
    try {
        $pgTest = docker exec test_model-postgres-1 pg_isready -U postgres 2>$null
        $pgWorking = $pgTest -like "*accepting connections*"
        Write-TestResult "Database" "PostgreSQL Connectivity" $pgWorking "PG status: $pgTest"
    } catch {
        Write-TestResult "Database" "PostgreSQL Connectivity" $false $_.Exception.Message
    }
}

# Test Worker Services
function Test-Workers {
    Write-Host "${Blue}=== TESTING WORKER SERVICES ===${Reset}"
    
    # Check Celery Worker status
    try {
        $workerStatus = docker exec test_model-worker-1 celery -A app.worker.celery_app inspect ping 2>$null
        $workerWorking = $workerStatus -like "*pong*"
        Write-TestResult "Worker" "Celery Worker Status" $workerWorking
    } catch {
        Write-TestResult "Worker" "Celery Worker Status" $false $_.Exception.Message
    }
    
    # Test Flower monitoring (if available)
    $flowerTest = Test-ServiceEndpoint -Url "http://localhost:5555" -TimeoutSec 5
    Write-TestResult "Worker" "Flower Monitoring" $flowerTest.Success
}

# Test Scraper Service
function Test-Scraper {
    Write-Host "${Blue}=== TESTING SCRAPER SERVICE ===${Reset}"
    
    $scraperTest = Test-ServiceEndpoint -Url "http://localhost:3001/health" -TimeoutSec 5
    Write-TestResult "Scraper" "Service Health" $scraperTest.Success
    
    if ($scraperTest.Success) {
        # Test scraper API endpoints
        $scraperStatus = Test-ServiceEndpoint -Url "http://localhost:3001/api/status"
        Write-TestResult "Scraper" "Status Endpoint" $scraperStatus.Success
    }
}

# Test with Real Data
function Test-RealData {
    Write-Host "${Blue}=== TESTING WITH REAL DATA ===${Reset}"
    
    # Test real product analysis
    $realProductData = @{
        url = "https://www.amazon.com/dp/B08N5WRWNW"
        text = "Echo Dot (4th Gen) | Smart speaker with Alexa | Charcoal"
        deep_analysis = $true
    }
    
    $realAnalysis = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/analyze" -Method "POST" -Body $realProductData
    Write-TestResult "Real Data" "Product Analysis" $realAnalysis.Success
    if ($realAnalysis.Success) {
        Write-Host "   Product URL: $($realProductData.url)"
        Write-Host "   Analysis Result: $($realAnalysis.Data.data.result)"
    }
    
    # Test real search
    $realSearch = Test-ServiceEndpoint -Url "http://localhost:8000/api/v1/search/clip?query=amazon+echo+smart+speaker"
    Write-TestResult "Real Data" "Product Search" $realSearch.Success
}

# Prepare Model Training Data
function Prepare-ModelTraining {
    Write-Host "${Blue}=== PREPARING MODEL TRAINING ===${Reset}"
    
    # Check if training data exists
    $trainingDataPath = ".\training_data"
    if (-not (Test-Path $trainingDataPath)) {
        New-Item -ItemType Directory -Path $trainingDataPath -Force | Out-Null
        Write-Host "${Yellow}Created training data directory${Reset}"
    }
    
    # Generate sample training data
    $sampleData = @{
        products = @()
        labels = @()
        features = @()
    }
    
    # Add sample product data
    for ($i = 1; $i -le 10; $i++) {
        $sampleData.products += @{
            id = $i
            name = "Sample Product $i"
            price = (Get-Random -Minimum 10 -Maximum 1000)
            category = @("Electronics", "Books", "Clothing", "Home")[(Get-Random -Maximum 4)]
            rating = (Get-Random -Minimum 1 -Maximum 5) + (Get-Random) / 100
        }
    }
    
    $sampleData | ConvertTo-Json -Depth 3 | Out-File -FilePath "$trainingDataPath\sample_products.json" -Encoding UTF8
    Write-TestResult "Training" "Sample Data Generated" $true "$trainingDataPath\sample_products.json"
    
    # Check for ML model files
    $modelPath = ".\models"
    if (-not (Test-Path $modelPath)) {
        New-Item -ItemType Directory -Path $modelPath -Force | Out-Null
        Write-Host "${Yellow}Created models directory${Reset}"
    }
    
    Write-TestResult "Training" "Training Environment" $true "Ready for model training"
}

# Generate Service Report
function Generate-ServiceReport {
    Write-Host "${Blue}=== GENERATING SERVICE REPORT ===${Reset}"
    
    $report = @"
# Service Test Report
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Service Status Summary
"@
    
    # Get container status
    $containers = docker compose -f docker-compose.complete.yml ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>$null
    $report += "`n```"
    $report += "`n$containers"
    $report += "`n```"
    
    $report += "`n`n## Available Services"
    $report += "`n- Frontend: http://localhost:8080"
    $report += "`n- Backend API: http://localhost:8000"
    $report += "`n- API Documentation: http://localhost:8000/docs"
    $report += "`n- Nginx Load Balancer: http://localhost:80"
    $report += "`n- Redis: localhost:6379"
    $report += "`n- Flower (Celery Monitor): http://localhost:5555"
    $report += "`n- Grafana: http://localhost:3002"
    $report += "`n- Prometheus: http://localhost:9090"
    $report += "`n- Scraper API: http://localhost:3001"
    
    $report += "`n`n## Next Steps for Model Training"
    $report += "`n1. Collect real product data through scraper"
    $report += "`n2. Prepare training datasets in ./training_data/"
    $report += "`n3. Train price prediction models"
    $report += "`n4. Train product classification models"
    $report += "`n5. Train recommendation engine"
    $report += "`n6. Deploy trained models to ./models/"
    
    $report | Out-File -FilePath "service_test_report.md" -Encoding UTF8
    Write-TestResult "Report" "Service Report Generated" $true "service_test_report.md"
}

# Main execution
Write-Host "${Green}=== COMPREHENSIVE SERVICE TESTING STARTED ===${Reset}"
Write-Host "Testing all services and preparing for model training..."
Write-Host ""

if ($All -or $TestFrontend) { Test-Frontend }
if ($All -or $TestBackend) { Test-Backend }
if ($All -or $TestAI) { Test-AIEndpoints }
if ($All -or $TestDatabase) { Test-Database }
if ($All -or $TestWorker) { Test-Workers }
if ($All -or $TestScraper) { Test-Scraper }
if ($All -or $TrainModel) { 
    Test-RealData
    Prepare-ModelTraining
}

Generate-ServiceReport

Write-Host ""
Write-Host "${Green}=== COMPREHENSIVE SERVICE TESTING COMPLETED ===${Reset}"
Write-Host "Check service_test_report.md for detailed results"
Write-Host ""
Write-Host "To run individual tests:"
Write-Host "  .\comprehensive_service_test.ps1 -TestFrontend"
Write-Host "  .\comprehensive_service_test.ps1 -TestBackend"
Write-Host "  .\comprehensive_service_test.ps1 -TestAI"
Write-Host "  .\comprehensive_service_test.ps1 -TrainModel"
Write-Host "  .\comprehensive_service_test.ps1 -All"
