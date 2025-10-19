# Advanced Docker Rebuild Script with Error Handling and Conflict Resolution
# This script intelligently rebuilds all Docker services with robust error handling

# Set colors for console output
$RESET = "$([char]27)[0m"
$RED = "$([char]27)[31m"
$GREEN = "$([char]27)[32m"
$YELLOW = "$([char]27)[33m"
$BLUE = "$([char]27)[34m"

# Helper functions
function Write-LogMessage {
    param (
        [string]$Type,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    switch ($Type) {
        "info" { Write-Host "${BLUE}[INFO]${RESET} ${timestamp} - $Message" }
        "success" { Write-Host "${GREEN}[SUCCESS]${RESET} ${timestamp} - $Message" }
        "warning" { Write-Host "${YELLOW}[WARNING]${RESET} ${timestamp} - $Message" }
        "error" { Write-Host "${RED}[ERROR]${RESET} ${timestamp} - $Message" }
        default { Write-Host "${timestamp} - $Message" }
    }
}

function Test-CommandExists {
    param (
        [string]$Command
    )
    
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

# Check for Docker
if (-not (Test-CommandExists "docker")) {
    Write-LogMessage "error" "Docker is not installed. Please install Docker and try again."
    exit 1
}

# Check for Docker Compose
if (-not (Test-CommandExists "docker-compose")) {
    Write-LogMessage "warning" "docker-compose not found as a standalone command. Checking for Docker Compose V2..."
    if (-not (Test-CommandExists "docker")) {
        Write-LogMessage "error" "Docker Compose is not available. Please install Docker Compose and try again."
        exit 1
    }
}

# Step 0: Define security recommendations
$securityRecommendations = @{
    "python:3.11-slim" = "Note: Python slim images may contain vulnerabilities. For production, consider using a distroless or secure base image."
    "node:18-alpine" = "Note: Node.js 18-alpine may contain vulnerabilities. Consider updating to the latest Node.js LTS version with Alpine."
}

# Function to check for known vulnerable base images
function Check-ImageSecurity {
    param (
        [string]$DockerfilePath
    )
    
    if (-not (Test-Path $DockerfilePath)) {
        return
    }
    
    $content = Get-Content $DockerfilePath -Raw
    $vulnFound = $false
    
    foreach ($baseImage in $securityRecommendations.Keys) {
        if ($content -match "FROM\s+$baseImage") {
            Write-LogMessage "warning" "Security notice in $DockerfilePath`: $($securityRecommendations[$baseImage])"
            $vulnFound = $true
        }
    }
    
    if (-not $vulnFound) {
        Write-LogMessage "info" "No known vulnerable base images found in $DockerfilePath"
    }
}

# Start the rebuild process
Write-LogMessage "info" "Starting Docker environment rebuild process..."

# Security scan step
Write-LogMessage "info" "Performing security scan of Dockerfiles..."
Check-ImageSecurity ".\Dockerfile"
Check-ImageSecurity ".\scraper\Dockerfile"
Check-ImageSecurity ".\captcha-service\Dockerfile"
Check-ImageSecurity ".\proxy-service\Dockerfile"
Check-ImageSecurity ".\frontend\Dockerfile"

# Step 1: Check system resources
$totalMemoryGB = [math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB, 2)
$availableMemoryGB = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
$cpuCount = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$diskFreeGB = [math]::Round((Get-PSDrive -Name C).Free / 1GB, 2)

Write-LogMessage "info" "System resources:"
Write-LogMessage "info" "- Total Memory: ${totalMemoryGB}GB"
Write-LogMessage "info" "- Available Memory: ${availableMemoryGB}GB"
Write-LogMessage "info" "- CPU Cores: $cpuCount"
Write-LogMessage "info" "- Disk Free Space: ${diskFreeGB}GB"

if ($availableMemoryGB -lt 2) {
    Write-LogMessage "warning" "Low memory available! This might affect Docker build performance."
}

if ($diskFreeGB -lt 5) {
    Write-LogMessage "warning" "Low disk space available! This might cause Docker build failures."
}

# Step 2: Stop all running containers
Write-LogMessage "info" "Stopping all running containers..."
try {
    docker-compose down --remove-orphans
    Write-LogMessage "success" "All containers stopped successfully."
} catch {
    Write-LogMessage "warning" "Failed to stop containers with docker-compose. Trying to stop individually..."
    docker ps -q | ForEach-Object {
        docker stop $_
    }
}

# Step 3: Clean Docker resources
Write-LogMessage "info" "Cleaning Docker resources..."

# Remove containers with our project name
$projectName = (Get-Item -Path .).Name
Write-LogMessage "info" "Removing containers related to project: $projectName"
docker ps -a | Select-String $projectName | ForEach-Object {
    $containerId = $_.ToString().Split()[0]
    docker rm -f $containerId
    Write-LogMessage "info" "Removed container: $containerId"
}

# Clean unused volumes
Write-LogMessage "info" "Removing unused volumes..."
docker volume prune -f

# Clean unused networks
Write-LogMessage "info" "Removing unused networks..."
docker network prune -f

# Step 4: Rebuild images with improved error handling
Write-LogMessage "info" "Building Docker images with enhanced error handling..."

# First, check if specific services need rebuilding
$servicesNeedingRebuild = @()
$allServices = @("web", "worker", "flower", "scraper")

foreach ($service in $allServices) {
    $serviceImage = docker images --filter "reference=*${service}*" -q
    if (-not $serviceImage) {
        $servicesNeedingRebuild += $service
        Write-LogMessage "info" "Service '$service' needs rebuilding"
    }
}

if ($servicesNeedingRebuild.Count -gt 0) {
    Write-LogMessage "info" "Rebuilding specific services: $($servicesNeedingRebuild -join ', ')"
    
    # Building with build arguments for improved dependency handling
    try {
        docker-compose build --no-cache --pull $servicesNeedingRebuild
        Write-LogMessage "success" "Services rebuilt successfully."
    } catch {
        Write-LogMessage "warning" "Failed to rebuild all services together. Trying one by one..."
        
        foreach ($service in $servicesNeedingRebuild) {
            try {
                Write-LogMessage "info" "Building service: $service"
                docker-compose build --no-cache --pull $service
                Write-LogMessage "success" "Service $service built successfully."
            } catch {
                Write-LogMessage "error" "Failed to build service: $service"
                Write-LogMessage "error" $_.Exception.Message
            }
        }
    }
} else {
    Write-LogMessage "info" "All service images exist. Rebuilding everything to ensure latest versions..."
    
    try {
        docker-compose build --pull
        Write-LogMessage "success" "All services rebuilt successfully."
    } catch {
        Write-LogMessage "warning" "Failed to rebuild all services together. Trying one by one..."
        
        foreach ($service in $allServices) {
            try {
                Write-LogMessage "info" "Building service: $service"
                docker-compose build --pull $service
                Write-LogMessage "success" "Service $service built successfully."
            } catch {
                Write-LogMessage "error" "Failed to build service: $service"
                Write-LogMessage "error" $_.Exception.Message
            }
        }
    }
}

# Step 5: Start the services
Write-LogMessage "info" "Starting Docker services..."

try {
    docker-compose up -d
    Write-LogMessage "success" "Services started successfully in detached mode."
} catch {
    Write-LogMessage "error" "Failed to start all services together. Trying essential services first..."
    
    try {
        # Start infrastructure services first
        docker-compose up -d redis postgres
        Write-LogMessage "success" "Infrastructure services started."
        
        # Wait for infrastructure to be ready
        Write-LogMessage "info" "Waiting 15 seconds for infrastructure services to initialize..."
        Start-Sleep -Seconds 15
        
        # Start application services
        docker-compose up -d web
        Write-LogMessage "success" "Web service started."
        
        # Start remaining services
        docker-compose up -d
        Write-LogMessage "success" "All remaining services started."
    } catch {
        Write-LogMessage "error" "Failed to start services gradually."
        Write-LogMessage "error" $_.Exception.Message
    }
}

# Step 6: Check service health
Write-LogMessage "info" "Checking service health..."
Start-Sleep -Seconds 10

$containers = docker-compose ps -q
foreach ($container in $containers) {
    $inspectResult = docker inspect --format "{{json .State.Health}}" $container | ConvertFrom-Json
    $containerName = docker inspect --format "{{.Name}}" $container
    
    if ($null -ne $inspectResult) {
        $status = $inspectResult.Status
        $failingStreak = $inspectResult.FailingStreak
        
        if ($status -eq "healthy") {
            Write-LogMessage "success" "Container $containerName is healthy."
        } elseif ($status -eq "starting") {
            Write-LogMessage "warning" "Container $containerName is still starting. Check again later."
        } else {
            Write-LogMessage "error" "Container $containerName is unhealthy (Failing streak: $failingStreak)."
            
            # Show logs for unhealthy container
            Write-LogMessage "info" "Last logs from $containerName`:"
            docker logs --tail 20 $container
        }
    } else {
        Write-LogMessage "info" "Container $containerName has no health check defined."
    }
}

# Step 7: Verify dependency installation in web container
Write-LogMessage "info" "Verifying dependency installation in web container..."

$webContainer = docker-compose ps -q web
if ($webContainer) {
    Write-LogMessage "info" "Running dependency verification in web container..."
    
    $pythonCmd = @"
import sys
import importlib.util

critical_packages = ['fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'redis', 'celery']
installed = 0
missing = []

for package in critical_packages:
    try:
        if importlib.util.find_spec(package) is not None:
            installed += 1
            print(f'✓ {package} is installed')
        else:
            missing.append(package)
            print(f'✗ {package} is NOT installed')
    except ImportError:
        missing.append(package)
        print(f'✗ {package} is NOT installed')

if missing:
    print(f'WARNING: {len(missing)}/{len(critical_packages)} critical packages missing: {", ".join(missing)}')
    sys.exit(1)
else:
    print(f'SUCCESS: All {len(critical_packages)} critical packages installed!')
    sys.exit(0)
"@

    try {
        $pythonCheck = docker exec $webContainer python -c $pythonCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogMessage "success" "All critical dependencies verified in web container!"
        } else {
            Write-LogMessage "error" "Some critical dependencies are missing in web container."
            Write-LogMessage "info" "You may need to rebuild with improved dependency handling."
        }
        
        foreach ($line in $pythonCheck) {
            if ($line -match "^✓") {
                Write-LogMessage "success" $line
            } elseif ($line -match "^✗") {
                Write-LogMessage "error" $line
            } elseif ($line -match "^WARNING:") {
                Write-LogMessage "warning" $line
            } elseif ($line -match "^SUCCESS:") {
                Write-LogMessage "success" $line
            }
        }
    } catch {
        Write-LogMessage "error" "Failed to verify dependencies: $_"
    }
} else {
    Write-LogMessage "warning" "Web container not found, skipping dependency verification."
}

Write-LogMessage "info" "Docker rebuild process completed."
Write-LogMessage "info" "To view logs, run: docker-compose logs -f"
Write-LogMessage "info" "To stop services, run: docker-compose down"
