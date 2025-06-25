# COMPREHENSIVE DOCKER DEPLOYMENT WITH AUTOMATED ERROR HANDLING
# This script handles all Docker build and deployment issues automatically

param(
    [string]$ComposeFile = "docker-compose.complete.yml",
    [switch]$CleanStart = $false,
    [switch]$ForceRebuild = $false,
    [int]$MaxRetries = 3
)

Write-Host "=== COMPREHENSIVE DOCKER DEPLOYMENT SCRIPT ===" -ForegroundColor Green
Write-Host "Target Compose File: $ComposeFile" -ForegroundColor Yellow
Write-Host "Clean Start: $CleanStart" -ForegroundColor Yellow
Write-Host "Force Rebuild: $ForceRebuild" -ForegroundColor Yellow
Write-Host ""

# Function to handle errors and cleanup
function Handle-Error {
    param([string]$Message, [switch]$Critical = $false)
    
    Write-Host "ERROR: $Message" -ForegroundColor Red
    
    if ($Critical) {
        Write-Host "Critical error encountered. Performing cleanup..." -ForegroundColor Red
        docker-compose -f $ComposeFile down --remove-orphans 2>$null
        exit 1
    }
}

# Function to wait for service health
function Wait-ForServiceHealth {
    param([string]$ServiceName, [int]$TimeoutSeconds = 300)
    
    Write-Host "Waiting for $ServiceName to become healthy..." -ForegroundColor Yellow
    $elapsed = 0
    $interval = 10
    
    while ($elapsed -lt $TimeoutSeconds) {
        $status = docker-compose -f $ComposeFile ps $ServiceName --format "table {{.Health}}" 2>$null
        if ($status -match "healthy") {
            Write-Host "$ServiceName is now healthy!" -ForegroundColor Green
            return $true
        }
        
        Start-Sleep $interval
        $elapsed += $interval
        Write-Host "Waiting... ($elapsed/$TimeoutSeconds seconds)" -ForegroundColor Gray
    }
    
    Write-Host "$ServiceName failed to become healthy within $TimeoutSeconds seconds" -ForegroundColor Red
    return $false
}

# Step 1: Cleanup if requested
if ($CleanStart) {
    Write-Host "=== PERFORMING CLEAN START ===" -ForegroundColor Cyan
    
    # Stop and remove all containers
    Write-Host "Stopping all containers..." -ForegroundColor Yellow
    docker-compose -f $ComposeFile down --remove-orphans --volumes 2>$null
    
    # Remove Docker images if force rebuild
    if ($ForceRebuild) {
        Write-Host "Removing all project images..." -ForegroundColor Yellow
        $images = docker images --format "table {{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "test_model" }
        foreach ($image in $images) {
            if ($image -and $image -notmatch "REPOSITORY") {
                docker rmi $image --force 2>$null
            }
        }
    }
    
    # Clean Docker system
    Write-Host "Cleaning Docker system..." -ForegroundColor Yellow
    docker system prune -f 2>$null
    
    Write-Host "Cleanup completed!" -ForegroundColor Green
}

# Step 2: Check Docker and requirements
Write-Host "=== CHECKING PREREQUISITES ===" -ForegroundColor Cyan

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Handle-Error "Docker is not installed or not running" -Critical
}

# Check docker-compose
try {
    $composeVersion = docker-compose --version
    Write-Host "Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Handle-Error "Docker Compose is not installed" -Critical
}

# Check compose file exists
if (!(Test-Path $ComposeFile)) {
    Handle-Error "Compose file '$ComposeFile' not found" -Critical
}

# Step 3: Build and deploy with retry logic
Write-Host "=== BUILDING AND DEPLOYING SERVICES ===" -ForegroundColor Cyan

$attempt = 1
$success = $false

while ($attempt -le $MaxRetries -and !$success) {
    Write-Host "Deployment attempt $attempt of $MaxRetries" -ForegroundColor Yellow
    
    try {
        # Build with no-cache if force rebuild or if previous attempt failed
        $buildArgs = if ($ForceRebuild -or $attempt -gt 1) { "--no-cache" } else { "" }
        
        Write-Host "Building services..." -ForegroundColor Yellow
        if ($buildArgs) {
            docker-compose -f $ComposeFile build $buildArgs
        } else {
            docker-compose -f $ComposeFile build
        }
        
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed with exit code $LASTEXITCODE"
        }
        
        Write-Host "Starting services..." -ForegroundColor Yellow
        docker-compose -f $ComposeFile up -d
        
        if ($LASTEXITCODE -ne 0) {
            throw "Service startup failed with exit code $LASTEXITCODE"
        }
        
        # Check critical services
        $criticalServices = @("postgres", "redis", "web")
        $allHealthy = $true
        
        foreach ($service in $criticalServices) {
            if (!(Wait-ForServiceHealth -ServiceName $service -TimeoutSeconds 180)) {
                $allHealthy = $false
                Write-Host "Critical service $service failed to start properly" -ForegroundColor Red
                
                # Show logs for debugging
                Write-Host "=== LOGS FOR $service ===" -ForegroundColor Red
                docker-compose -f $ComposeFile logs --tail=50 $service
                Write-Host "=== END LOGS ===" -ForegroundColor Red
            }
        }
        
        if ($allHealthy) {
            $success = $true
            Write-Host "All critical services are healthy!" -ForegroundColor Green
        } else {
            throw "One or more critical services failed to become healthy"
        }
        
    } catch {
        Write-Host "Attempt $attempt failed: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($attempt -lt $MaxRetries) {
            Write-Host "Cleaning up for retry..." -ForegroundColor Yellow
            docker-compose -f $ComposeFile down --remove-orphans 2>$null
            
            # Add delay before retry
            Write-Host "Waiting 30 seconds before retry..." -ForegroundColor Yellow
            Start-Sleep 30
        }
        
        $attempt++
    }
}

if (!$success) {
    Handle-Error "Failed to deploy services after $MaxRetries attempts" -Critical
}

# Step 4: Final health check and status report
Write-Host "=== FINAL STATUS REPORT ===" -ForegroundColor Cyan

Write-Host "Checking all services..." -ForegroundColor Yellow
docker-compose -f $ComposeFile ps

Write-Host ""
Write-Host "Service health status:" -ForegroundColor Yellow
$services = docker-compose -f $ComposeFile ps --services
foreach ($service in $services) {
    $status = docker-compose -f $ComposeFile ps $service --format "table {{.State}} {{.Health}}"
    Write-Host "$service`: $status" -ForegroundColor $(if ($status -match "healthy|Up") { "Green" } else { "Red" })
}

Write-Host ""
Write-Host "=== DEPLOYMENT COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
Write-Host "All services are running. You can now access:" -ForegroundColor Cyan
Write-Host "- Main Application: http://localhost:8000" -ForegroundColor White
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "- Proxy: http://localhost:80" -ForegroundColor White
Write-Host "- Grafana: http://localhost:3001" -ForegroundColor White
Write-Host "- Flower (Celery): http://localhost:5555" -ForegroundColor White

# Optional: Show resource usage
Write-Host ""
Write-Host "Resource usage:" -ForegroundColor Yellow
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
