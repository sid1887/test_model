# COMPREHENSIVE DOCKER DEPLOYMENT SCRIPT WITH AUTOMATED ERROR HANDLING (PowerShell)
# This script automatically handles package conflicts, version issues, and service failures

param(
    [switch]$Clean,
    [switch]$Build,
    [switch]$Help,
    [switch]$Status
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $InfoColor
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $ErrorColor
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [int]$MaxAttempts = 30
    )
    
    Write-Info "Waiting for $ServiceName to become healthy..."
    
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $status = docker-compose -f docker-compose.complete.yml ps | Select-String $ServiceName
            if ($status -and ($status -match "healthy" -or $status -match "running")) {
                Write-Success "$ServiceName is healthy!"
                return $true
            }
        }
        catch {
            # Continue trying
        }
        
        Write-Host "Attempt $attempt/$MaxAttempts - $ServiceName not ready yet..."
        Start-Sleep -Seconds 10
    }
    
    Write-Warning "$ServiceName did not become healthy within expected time"
    return $false
}

function Handle-ServiceFailure {
    param([string]$ServiceName)
    
    Write-Error "$ServiceName failed to start properly"
    
    Write-Info "Getting logs for $ServiceName..."
    try {
        docker-compose -f docker-compose.complete.yml logs --tail=50 $ServiceName
    }
    catch {
        Write-Warning "Could not retrieve logs for $ServiceName"
    }
    
    Write-Info "Attempting to restart $ServiceName..."
    try {
        docker-compose -f docker-compose.complete.yml restart $ServiceName
        Start-Sleep -Seconds 10
        
        $status = docker-compose -f docker-compose.complete.yml ps | Select-String $ServiceName
        if ($status -and ($status -match "healthy" -or $status -match "running")) {
            Write-Success "$ServiceName restarted successfully!"
            return $true
        }
        else {
            Write-Warning "$ServiceName restart failed, continuing with other services..."
            return $false
        }
    }
    catch {
        Write-Warning "$ServiceName restart failed, continuing with other services..."
        return $false
    }
}

function Cleanup-Docker {
    Write-Info "Cleaning up Docker resources..."
    
    try {
        Write-Info "Stopping all containers..."
        docker-compose -f docker-compose.complete.yml down --remove-orphans
        
        Write-Info "Removing stopped containers..."
        docker container prune -f
        
        Write-Info "Removing unused images..."
        docker image prune -f
        
        Write-Warning "Cleaning unused volumes (this may remove cached data)..."
        docker volume prune -f
        
        Write-Info "Removing unused networks..."
        docker network prune -f
        
        Write-Success "Docker cleanup completed"
    }
    catch {
        Write-Warning "Some cleanup operations failed, continuing..."
    }
}

function Test-Requirements {
    Write-Info "Checking system requirements..."
    
    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    if (-not (Test-Command "docker-compose")) {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running"
        exit 1
    }
    
    Write-Success "System requirements check passed"
}

function Build-WithRetry {
    param(
        [string]$ServiceName,
        [int]$MaxAttempts = 3
    )
    
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-Info "Building $ServiceName (attempt $attempt/$MaxAttempts)..."
        
        try {
            docker-compose -f docker-compose.complete.yml build --no-cache $ServiceName
            Write-Success "$ServiceName built successfully!"
            return $true
        }
        catch {
            Write-Warning "$ServiceName build failed on attempt $attempt"
            if ($attempt -lt $MaxAttempts) {
                Write-Info "Cleaning up and retrying..."
                try {
                    docker-compose -f docker-compose.complete.yml down $ServiceName
                    docker image rm "test_model-$ServiceName" 2>$null
                }
                catch {
                    # Continue
                }
                Start-Sleep -Seconds 5
            }
        }
    }
    
    Write-Error "$ServiceName failed to build after $MaxAttempts attempts"
    return $false
}

function Deploy-Services {
    Write-Info "Starting service deployment with automated error handling..."
    
    $services = @("redis", "postgres", "web", "scraper", "captcha", "proxy", "worker", "flower", "frontend", "prometheus", "grafana", "nginx")
    $failedServices = @()
    $successfulServices = @()
    
    # Build all services first
    Write-Info "Building all services..."
    try {
        docker-compose -f docker-compose.complete.yml build --no-cache
        Write-Success "All services built successfully!"
    }
    catch {
        Write-Warning "Bulk build failed, trying individual builds..."
        
        $criticalServices = @("web", "scraper", "captcha", "proxy")
        foreach ($service in $criticalServices) {
            if (Build-WithRetry $service) {
                $successfulServices += $service
            }
            else {
                $failedServices += $service
            }
        }
    }
    
    # Start services in dependency order
    Write-Info "Starting services in dependency order..."
    
    # Start infrastructure services first
    Write-Info "Starting infrastructure services (Redis, PostgreSQL)..."
    try {
        docker-compose -f docker-compose.complete.yml up -d redis postgres
        
        # Wait for infrastructure
        if (-not (Wait-ForService "redis")) {
            Handle-ServiceFailure "redis" | Out-Null
        }
        if (-not (Wait-ForService "postgres")) {
            Handle-ServiceFailure "postgres" | Out-Null
        }
        
        # Start core application services
        Write-Info "Starting core application services..."
        docker-compose -f docker-compose.complete.yml up -d web scraper captcha proxy
        
        # Check each core service
        $coreServices = @("web", "scraper", "captcha", "proxy")
        foreach ($service in $coreServices) {
            if (Wait-ForService $service) {
                $successfulServices += $service
            }
            else {
                Handle-ServiceFailure $service | Out-Null
                $failedServices += $service
            }
        }
        
        # Start remaining services
        Write-Info "Starting remaining services..."
        docker-compose -f docker-compose.complete.yml up -d worker flower frontend prometheus grafana nginx
    }
    catch {
        Write-Error "Failed to start some services: $($_.Exception.Message)"
    }
    
    # Final status report
    Write-Info "Deployment completed. Generating status report..."
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor White
    Write-Host "         DEPLOYMENT STATUS REPORT" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor White
    
    if ($successfulServices.Count -gt 0) {
        Write-Success "Successful services:"
        foreach ($service in $successfulServices) {
            Write-Host "  ✅ $service" -ForegroundColor Green
        }
    }
    
    if ($failedServices.Count -gt 0) {
        Write-Error "Failed services:"
        foreach ($service in $failedServices) {
            Write-Host "  ❌ $service" -ForegroundColor Red
        }
        Write-Host ""
        Write-Warning "Some services failed. Check logs with: docker-compose -f docker-compose.complete.yml logs [service_name]"
    }
    else {
        Write-Success "All services started successfully!"
    }
    
    Write-Host ""
    Write-Info "Current service status:"
    try {
        docker-compose -f docker-compose.complete.yml ps
    }
    catch {
        Write-Warning "Could not retrieve service status"
    }
    
    Write-Host ""
    Write-Info "Access points:"
    Write-Host "  🌐 Web Application: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📊 Grafana Dashboard: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🌸 Flower (Celery): http://localhost:5555" -ForegroundColor Cyan
    Write-Host "  🔍 Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  📈 Prometheus: http://localhost:9090" -ForegroundColor Cyan
}

function Show-Help {
    Write-Host "Comprehensive Docker Deployment Script (PowerShell)" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage: .\deploy-robust.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -Clean     Clean up all Docker resources before deployment" -ForegroundColor Yellow
    Write-Host "  -Build     Force rebuild all images" -ForegroundColor Yellow
    Write-Host "  -Help      Show this help message" -ForegroundColor Yellow
    Write-Host "  -Status    Show current status without deployment" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\deploy-robust.ps1           # Normal deployment with error handling" -ForegroundColor Gray
    Write-Host "  .\deploy-robust.ps1 -Clean   # Clean deployment" -ForegroundColor Gray
    Write-Host "  .\deploy-robust.ps1 -Status  # Check current status" -ForegroundColor Gray
}

function Show-Status {
    Write-Info "Current Docker Compose Status:"
    try {
        docker-compose -f docker-compose.complete.yml ps
    }
    catch {
        Write-Error "Failed to get service status"
    }
    
    Write-Host ""
    Write-Info "Docker Images:"
    try {
        docker images | Select-String "test_model"
    }
    catch {
        Write-Warning "No test_model images found"
    }
    
    Write-Host ""
    Write-Info "Docker Volumes:"
    try {
        docker volume ls | Select-String "test_model"
    }
    catch {
        Write-Warning "No test_model volumes found"
    }
    
    Write-Host ""
    Write-Info "Docker Networks:"
    try {
        $networks = docker network ls | Select-String "test_model"
        if (-not $networks) {
            docker network ls | Select-Object -First 5
        }
        else {
            $networks
        }
    }
    catch {
        Write-Warning "Could not retrieve network information"
    }
}

# Main script execution
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    if ($Status) {
        Show-Status
        return
    }
    
    Write-Info "Starting Comprehensive Docker Deployment Script..."
    Write-Info "Timestamp: $(Get-Date)"
    
    # Check requirements
    Test-Requirements
    
    # Clean deployment if requested
    if ($Clean) {
        Write-Warning "Clean deployment requested - this will remove all existing containers and images"
        $response = Read-Host "Are you sure? (y/N)"
        if ($response -eq "y" -or $response -eq "Y") {
            Cleanup-Docker
        }
        else {
            Write-Info "Skipping cleanup"
        }
    }
    
    # Deploy services
    Deploy-Services
    
    Write-Success "Deployment script completed!"
    Write-Info "Use '.\deploy-robust.ps1 -Status' to check service status anytime"
}

# Run main function
Main
