# Secure Docker Startup Script
# Starts Cumpair with production-grade security following testdriven.io best practices

param(
    [string]$Profile = "basic",  # basic, worker, scraping, monitoring, production
    [switch]$Build = $false,
    [switch]$Fresh = $false,
    [switch]$Logs = $false
)

Write-Host "🚀 Starting Cumpair with Docker Security" -ForegroundColor Green
Write-Host "=" * 60

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "`n🔍 Checking prerequisites..." -ForegroundColor Blue
    
    # Check Docker
    try {
        $dockerVersion = docker version --format "{{.Server.Version}}"
        Write-Host "   ✅ Docker: v$dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Docker not available" -ForegroundColor Red
        Write-Host "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose version --short
        Write-Host "   ✅ Docker Compose: v$composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Docker Compose not available" -ForegroundColor Red
        exit 1
    }
    
    # Check secrets
    $requiredSecrets = @("db_password.txt", "secret_key.txt", "redis_password.txt")
    $missingSecrets = @()
    
    foreach ($secret in $requiredSecrets) {
        if (-not (Test-Path "secrets\$secret")) {
            $missingSecrets += $secret
        }
    }
    
    if ($missingSecrets.Count -gt 0) {
        Write-Host "   ❌ Missing secrets: $($missingSecrets -join ', ')" -ForegroundColor Red
        Write-Host "   Run: .\setup-docker-security.ps1" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "   ✅ All secrets present" -ForegroundColor Green
    
    # Check .env file
    if (-not (Test-Path ".env")) {
        Write-Host "   ⚠️ .env file not found, using defaults" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ Environment configuration found" -ForegroundColor Green
    }
}

# Function to select appropriate compose file and profiles
function Get-ComposeConfiguration {
    param([string]$ProfileName)
    
    $composeFile = "docker-compose.secure.yml"
    $profiles = @()
    
    switch ($ProfileName.ToLower()) {
        "basic" {
            $profiles = @()
            Write-Host "   📦 Basic setup: Web + Database + Redis" -ForegroundColor Cyan
        }
        "worker" {
            $profiles = @("worker")
            Write-Host "   🔧 Worker setup: Basic + Celery Workers + Flower" -ForegroundColor Cyan
        }
        "scraping" {
            $profiles = @("scraping")
            Write-Host "   🕷️ Scraping setup: Basic + Proxy + CAPTCHA services" -ForegroundColor Cyan
        }
        "monitoring" {
            $profiles = @("monitoring")
            Write-Host "   📊 Monitoring setup: Basic + Prometheus + Grafana" -ForegroundColor Cyan
        }
        "production" {
            $profiles = @("worker", "scraping", "monitoring", "production")
            Write-Host "   🏭 Production setup: All services + Nginx + Full monitoring" -ForegroundColor Cyan
        }
        "all" {
            $profiles = @("worker", "scraping", "monitoring", "production")
            Write-Host "   🌟 Complete setup: All available services" -ForegroundColor Cyan
        }
        default {
            Write-Host "   ❌ Unknown profile: $ProfileName" -ForegroundColor Red
            Write-Host "   Available profiles: basic, worker, scraping, monitoring, production, all" -ForegroundColor Yellow
            exit 1
        }
    }
    
    return @{
        "ComposeFile" = $composeFile
        "Profiles" = $profiles
    }
}

# Function to clean up if fresh start requested
function Start-FreshEnvironment {
    Write-Host "`n🧹 Cleaning up existing environment..." -ForegroundColor Blue
    
    try {
        # Stop and remove containers
        docker-compose -f docker-compose.secure.yml down --remove-orphans 2>$null
        
        # Remove volumes (careful - this deletes data!)
        $confirmation = Read-Host "   ⚠️ This will DELETE ALL DATA. Type 'YES' to confirm"
        if ($confirmation -eq "YES") {
            docker-compose -f docker-compose.secure.yml down -v 2>$null
            Write-Host "   ✅ Volumes removed" -ForegroundColor Green
        }
        
        # Prune unused images (optional)
        docker image prune -f 2>$null
        Write-Host "   ✅ Environment cleaned" -ForegroundColor Green
        
    } catch {
        Write-Host "   ⚠️ Cleanup had some issues (this is often normal)" -ForegroundColor Yellow
    }
}

# Function to build images
function Build-Images {
    param([string]$ComposeFile, [array]$Profiles)
    
    Write-Host "`n🔨 Building Docker images..." -ForegroundColor Blue
    
    $buildArgs = @("docker-compose", "-f", $ComposeFile, "build", "--no-cache")
    
    if ($Profiles.Count -gt 0) {
        foreach ($profile in $Profiles) {
            $buildArgs += "--profile"
            $buildArgs += $profile
        }
    }
    
    try {
        & $buildArgs[0] $buildArgs[1..($buildArgs.Length-1)]
        Write-Host "   ✅ Images built successfully" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Build failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Function to start services
function Start-Services {
    param([string]$ComposeFile, [array]$Profiles)
    
    Write-Host "`n🚀 Starting services..." -ForegroundColor Blue
    
    $upArgs = @("docker-compose", "-f", $ComposeFile, "up", "-d")
    
    if ($Profiles.Count -gt 0) {
        foreach ($profile in $Profiles) {
            $upArgs += "--profile"
            $upArgs += $profile
        }
    }
    
    try {
        & $upArgs[0] $upArgs[1..($upArgs.Length-1)]
        Write-Host "   ✅ Services started successfully" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Startup failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Function to wait for services to be healthy
function Wait-ForServices {
    param([string]$ComposeFile)
    
    Write-Host "`n⏳ Waiting for services to be healthy..." -ForegroundColor Blue
    
    $maxWait = 120  # 2 minutes
    $waited = 0
    $interval = 5
    
    while ($waited -lt $maxWait) {
        try {
            $healthyServices = docker-compose -f $ComposeFile ps --filter "health=healthy" --format "{{.Service}}" 2>$null
            $runningServices = docker-compose -f $ComposeFile ps --filter "status=running" --format "{{.Service}}" 2>$null
            
            if ($healthyServices -and $runningServices) {
                $healthyCount = ($healthyServices | Measure-Object).Count
                $runningCount = ($runningServices | Measure-Object).Count
                
                Write-Host "   🏥 Healthy: $healthyCount, Running: $runningCount" -ForegroundColor Gray
                
                # Check key services
                $keyServices = @("redis", "postgres", "web")
                $allHealthy = $true
                
                foreach ($service in $keyServices) {
                    $serviceStatus = docker-compose -f $ComposeFile ps $service --format "{{.Status}}" 2>$null
                    if ($serviceStatus -notlike "*healthy*") {
                        $allHealthy = $false
                        break
                    }
                }
                
                if ($allHealthy) {
                    Write-Host "   ✅ Core services are healthy" -ForegroundColor Green
                    break
                }
            }
        } catch {
            # Ignore errors during health checking
        }
        
        Start-Sleep $interval
        $waited += $interval
        
        if ($waited % 15 -eq 0) {
            Write-Host "   ⏳ Still waiting... ($waited/$maxWait seconds)" -ForegroundColor Yellow
        }
    }
    
    if ($waited -ge $maxWait) {
        Write-Host "   ⚠️ Timeout waiting for services. They may still be starting..." -ForegroundColor Yellow
    }
}

# Function to show service status
function Show-ServiceStatus {
    param([string]$ComposeFile, [array]$Profiles)
    
    Write-Host "`n📊 SERVICE STATUS" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    try {
        $services = docker-compose -f $ComposeFile ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>$null
        
        if ($services) {
            $services | ForEach-Object {
                if ($_ -like "*healthy*") {
                    Write-Host $_ -ForegroundColor Green
                } elseif ($_ -like "*starting*" -or $_ -like "*running*") {
                    Write-Host $_ -ForegroundColor Yellow
                } elseif ($_ -like "*Service*") {
                    Write-Host $_ -ForegroundColor Cyan
                } else {
                    Write-Host $_
                }
            }
        } else {
            Write-Host "No services found or services are still starting..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not retrieve service status" -ForegroundColor Red
    }
}

# Function to show application URLs
function Show-ApplicationURLs {
    param([array]$Profiles)
    
    Write-Host "`n🌐 APPLICATION URLS" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    # Core application
    Write-Host "🏠 Main Application:" -ForegroundColor White
    Write-Host "   • Web Interface: http://localhost:8000" -ForegroundColor Gray
    Write-Host "   • API Documentation: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "   • Health Check: http://localhost:8000/api/v1/health" -ForegroundColor Gray
    
    # Profile-specific URLs
    if ($Profiles -contains "worker") {
        Write-Host "`n🔧 Worker Services:" -ForegroundColor White
        Write-Host "   • Flower (Celery Monitor): http://localhost:5555" -ForegroundColor Gray
    }
    
    if ($Profiles -contains "scraping") {
        Write-Host "`n🕷️ Scraping Services:" -ForegroundColor White
        Write-Host "   • Proxy Manager: http://localhost:8001" -ForegroundColor Gray
        Write-Host "   • HAProxy Stats: http://localhost:8081/stats" -ForegroundColor Gray
        Write-Host "   • CAPTCHA Service: http://localhost:9001" -ForegroundColor Gray
    }
    
    if ($Profiles -contains "monitoring") {
        Write-Host "`n📊 Monitoring:" -ForegroundColor White
        Write-Host "   • Prometheus: http://localhost:9090" -ForegroundColor Gray
        Write-Host "   • Grafana: http://localhost:3000 (admin/[check secrets])" -ForegroundColor Gray
    }
    
    if ($Profiles -contains "production") {
        Write-Host "`n🏭 Production:" -ForegroundColor White
        Write-Host "   • Nginx Frontend: http://localhost:80" -ForegroundColor Gray
    }
}

# Function to show management commands
function Show-ManagementCommands {
    param([string]$ComposeFile, [array]$Profiles)
    
    Write-Host "`n🛠️ MANAGEMENT COMMANDS" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    Write-Host "🔧 Service Management:" -ForegroundColor White
    Write-Host "   • View logs: docker-compose -f $ComposeFile logs -f [service]" -ForegroundColor Gray
    Write-Host "   • Stop services: docker-compose -f $ComposeFile down" -ForegroundColor Gray
    Write-Host "   • Restart service: docker-compose -f $ComposeFile restart [service]" -ForegroundColor Gray
    Write-Host "   • Shell access: docker-compose -f $ComposeFile exec web bash" -ForegroundColor Gray
    
    Write-Host "`n📊 Monitoring:" -ForegroundColor White
    Write-Host "   • Service status: docker-compose -f $ComposeFile ps" -ForegroundColor Gray
    Write-Host "   • Resource usage: docker stats" -ForegroundColor Gray
    Write-Host "   • Disk usage: docker system df" -ForegroundColor Gray
    
    Write-Host "`n🗄️ Database:" -ForegroundColor White
    Write-Host "   • Database shell: docker-compose -f $ComposeFile exec postgres psql -U compair" -ForegroundColor Gray
    Write-Host "   • Redis CLI: docker-compose -f $ComposeFile exec redis redis-cli" -ForegroundColor Gray
    
    Write-Host "`n🧹 Cleanup:" -ForegroundColor White
    Write-Host "   • Full cleanup: .\docker-start-secure.ps1 -Profile $Profile -Fresh" -ForegroundColor Gray
    Write-Host "   • Remove images: docker image prune -a" -ForegroundColor Gray
}

# Main execution
try {
    Write-Host "Profile: $Profile" -ForegroundColor Gray
    Write-Host "Build: $Build" -ForegroundColor Gray
    Write-Host "Fresh: $Fresh" -ForegroundColor Gray
    
    # Step 1: Check prerequisites
    Test-Prerequisites
    
    # Step 2: Get configuration
    $config = Get-ComposeConfiguration -ProfileName $Profile
    $composeFile = $config.ComposeFile
    $profiles = $config.Profiles
    
    # Step 3: Fresh start if requested
    if ($Fresh) {
        Start-FreshEnvironment
    }
    
    # Step 4: Build if requested
    if ($Build) {
        Build-Images -ComposeFile $composeFile -Profiles $profiles
    }
    
    # Step 5: Start services
    Start-Services -ComposeFile $composeFile -Profiles $profiles
    
    # Step 6: Wait for health
    Wait-ForServices -ComposeFile $composeFile
    
    # Step 7: Show status
    Show-ServiceStatus -ComposeFile $composeFile -Profiles $profiles
    
    # Step 8: Show URLs and commands
    Show-ApplicationURLs -Profiles $profiles
    Show-ManagementCommands -ComposeFile $composeFile -Profiles $profiles
    
    Write-Host "`n🎉 Cumpair started successfully!" -ForegroundColor Green
    Write-Host "All services are running with production-grade security." -ForegroundColor White
    
    # Step 9: Show logs if requested
    if ($Logs) {
        Write-Host "`n📋 Following logs (Ctrl+C to exit)..." -ForegroundColor Blue
        docker-compose -f $composeFile logs -f
    }
    
} catch {
    Write-Host "`n❌ Startup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
