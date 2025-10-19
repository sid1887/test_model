# Enhanced Docker Rebuild Script with Advanced Features
# Requires PowerShell 5.1 or higher

[CmdletBinding()]
param(
    [string]$ComposeFile = "docker-compose.complete.yml",
    [switch]$SkipCleanup,
    [switch]$SkipHealthCheck,
    [string[]]$Services = @(),
    [switch]$BuildOnly,
    [int]$HealthCheckTimeout = 300
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Console colors using ANSI escape sequences
$Script:Colors = @{
    Reset = "`e[0m"
    Red = "`e[31m"
    Green = "`e[32m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Magenta = "`e[35m"
    Cyan = "`e[36m"
    Bold = "`e[1m"
}

# Configuration
$Script:Config = @{
    MinMemoryGB = 2
    MinDiskSpaceGB = 5
    MaxLogLines = 50
    DefaultServices = @("web", "worker", "flower", "scraper")
    InfrastructureServices = @("redis", "postgres", "database")
    CriticalPythonPackages = @('fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'redis', 'celery', 'requests', 'psycopg2')
    CriticalNodePackages = @('express', 'axios', 'lodash')
    SecurityPatterns = @{
        "FROM.*python:3\.[0-9]+-slim" = "Consider using python:3.12-slim-bullseye or distroless images for better security"
        "FROM.*node:1[0-7]" = "Node.js version may be outdated. Consider upgrading to Node.js 18+ LTS"
        "FROM.*ubuntu:18\.04|FROM.*ubuntu:16\.04" = "Ubuntu version is outdated and may contain security vulnerabilities"
        "RUN.*apt-get.*install.*--no-install-recommends" = @"
Missing --no-install-recommends flag increases image size and attack surface.
Consider: RUN apt-get update && apt-get install -y --no-install-recommends package-name && rm -rf /var/lib/apt/lists/*
"@
        "USER\s+root|^(?!.*USER)" = "Running as root user increases security risk. Consider adding USER directive"
    }
}

# Enhanced logging with structured output
function Write-LogMessage {
    param (
        [ValidateSet("info", "success", "warning", "error", "debug")]
        [string]$Type = "info",
        [string]$Message,
        [string]$Component = "MAIN"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $colors = $Script:Colors
    
    $colorMap = @{
        "info" = $colors.Blue
        "success" = $colors.Green
        "warning" = $colors.Yellow
        "error" = $colors.Red
        "debug" = $colors.Magenta
    }
    
    $color = $colorMap[$Type]
    $prefix = "[$($Type.ToUpper())]".PadRight(9)
    
    if ($Type -eq "debug" -and $VerbosePreference -eq 'SilentlyContinue') { return }
    
    Write-Host "${color}${prefix}$($Script:Colors.Reset) ${timestamp} [${Component}] - $Message"
      # Also log to file for debugging
    $logEntry = "${timestamp} [$($Type.ToUpper())] [${Component}] - $Message"
    Add-Content -Path "docker-rebuild.log" -Value $logEntry -ErrorAction SilentlyContinue
}

# Enhanced command existence check with version info
function Test-CommandExists {
    param (
        [string]$Command,
        [string]$MinVersion = $null
    )
    
    try {
        $cmd = Get-Command $Command -ErrorAction Stop
        Write-LogMessage "debug" "Found command: $Command at $($cmd.Source)" "DEPS"
        
        if ($MinVersion) {
            $version = & $Command --version 2>$null | Select-Object -First 1
            Write-LogMessage "debug" "Version output: $version" "DEPS"
        }
        
        return $true
    }
    catch {
        Write-LogMessage "debug" "Command not found: $Command" "DEPS"
        return $false
    }
}

# Comprehensive Docker environment check
function Test-DockerEnvironment {
    Write-LogMessage "info" "Checking Docker environment..." "DOCKER"
    
    # Check Docker installation
    if (-not (Test-CommandExists "docker")) {
        Write-LogMessage "error" "Docker is not installed or not in PATH" "DOCKER"
        throw "Docker installation required"
    }
    
    # Check Docker daemon
    try {
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        Write-LogMessage "success" "Docker daemon running (version: $dockerVersion)" "DOCKER"
    }
    catch {
        Write-LogMessage "error" "Docker daemon is not running. Please start Docker Desktop or Docker service" "DOCKER"
        throw "Docker daemon not accessible"
    }
    
    # Check Docker Compose
    $composeAvailable = $false
    if (Test-CommandExists "docker-compose") {
        $composeVersion = docker-compose version --short 2>$null
        Write-LogMessage "success" "Docker Compose V1 available (version: $composeVersion)" "DOCKER"
        $Script:ComposeCommand = "docker-compose"
        $composeAvailable = $true
    }
    elseif (docker compose version 2>$null) {
        $composeVersion = docker compose version --short 2>$null
        Write-LogMessage "success" "Docker Compose V2 available (version: $composeVersion)" "DOCKER"
        $Script:ComposeCommand = "docker compose"
        $composeAvailable = $true
    }
    
    if (-not $composeAvailable) {
        Write-LogMessage "error" "Docker Compose is not available" "DOCKER"
        throw "Docker Compose installation required"
    }
    
    # Verify compose file exists
    if (-not (Test-Path $ComposeFile)) {
        Write-LogMessage "error" "Docker Compose file not found: $ComposeFile" "DOCKER"
        throw "Compose file missing"
    }
    
    Write-LogMessage "success" "Docker environment check completed" "DOCKER"
}

# Enhanced system resource monitoring
function Get-SystemResources {
    Write-LogMessage "info" "Analyzing system resources..." "SYSTEM"
    
    try {
        # Memory information
        $memory = Get-CimInstance Win32_OperatingSystem
        $totalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
        $availableMemoryGB = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
        $memoryUsagePercent = [math]::Round((($totalMemoryGB - $availableMemoryGB) / $totalMemoryGB) * 100, 1)
        
        # CPU information
        $cpu = Get-CimInstance Win32_ComputerSystem
        $cpuCount = $cpu.NumberOfLogicalProcessors
        
        # Disk information
        $disk = Get-PSDrive -Name C -ErrorAction SilentlyContinue
        $diskFreeGB = if ($disk) { [math]::Round($disk.Free / 1GB, 2) } else { 0 }
        $diskTotalGB = if ($disk) { [math]::Round(($disk.Free + $disk.Used) / 1GB, 2) } else { 0 }
        $diskUsagePercent = if ($diskTotalGB -gt 0) { [math]::Round((($diskTotalGB - $diskFreeGB) / $diskTotalGB) * 100, 1) } else { 0 }
        
        # Docker space usage
        $dockerSystemInfo = docker system df --format "table {{.Type}}\t{{.Size}}" 2>$null | Select-Object -Skip 1
        
        $resources = @{
            Memory = @{
                Total = $totalMemoryGB
                Available = $availableMemoryGB
                UsagePercent = $memoryUsagePercent
            }
            CPU = @{
                Cores = $cpuCount
            }
            Disk = @{
                Free = $diskFreeGB
                Total = $diskTotalGB
                UsagePercent = $diskUsagePercent
            }
            Docker = $dockerSystemInfo
        }
        
        Write-LogMessage "info" "System Resources:" "SYSTEM"
        Write-LogMessage "info" "  Memory: ${availableMemoryGB}GB available / ${totalMemoryGB}GB total (${memoryUsagePercent}% used)" "SYSTEM"
        Write-LogMessage "info" "  CPU: $cpuCount logical cores" "SYSTEM"
        Write-LogMessage "info" "  Disk: ${diskFreeGB}GB free / ${diskTotalGB}GB total (${diskUsagePercent}% used)" "SYSTEM"
        
        # Resource warnings
        if ($availableMemoryGB -lt $Script:Config.MinMemoryGB) {
            Write-LogMessage "warning" "Low memory available (${availableMemoryGB}GB < $($Script:Config.MinMemoryGB)GB). Docker builds may be slow or fail" "SYSTEM"
        }
        
        if ($diskFreeGB -lt $Script:Config.MinDiskSpaceGB) {
            Write-LogMessage "warning" "Low disk space (${diskFreeGB}GB < $($Script:Config.MinDiskSpaceGB)GB). Docker builds may fail" "SYSTEM"
        }
        
        if ($memoryUsagePercent -gt 85) {
            Write-LogMessage "warning" "High memory usage (${memoryUsagePercent}%). Consider closing other applications" "SYSTEM"
        }
        
        return $resources
    }
    catch {
        Write-LogMessage "warning" "Could not retrieve complete system information: $_" "SYSTEM"
        return @{}
    }
}

# Enhanced security scanning with detailed recommendations
function Invoke-SecurityScan {
    param ([string[]]$DockerfilePaths)
    
    Write-LogMessage "info" "Performing comprehensive security scan..." "SECURITY"
    $vulnerabilitiesFound = 0
    
    foreach ($dockerfilePath in $DockerfilePaths) {
        if (-not (Test-Path $dockerfilePath)) { continue }
        
        Write-LogMessage "info" "Scanning: $dockerfilePath" "SECURITY"
        $content = Get-Content $dockerfilePath -Raw
        
        foreach ($pattern in $Script:Config.SecurityPatterns.Keys) {
            if ($content -match $pattern) {
                $recommendation = $Script:Config.SecurityPatterns[$pattern]
                Write-LogMessage "warning" "Security issue in ${dockerfilePath}:" "SECURITY"
                Write-LogMessage "warning" "  $recommendation" "SECURITY"
                $vulnerabilitiesFound++
            }
        }        # Check for secrets in Dockerfiles
        $secretPatterns = @(
            'password\s*=\s*["''][^"'']+["'']',
            'api[_-]?key\s*=\s*["''][^"'']+["'']',
            'token\s*=\s*["''][^"'']+["'']',
            'secret\s*=\s*["''][^"'']+["'']'
        )
        
        foreach ($secretPattern in $secretPatterns) {
            if ($content -match $secretPattern) {
                Write-LogMessage "error" "Potential secret detected in ${dockerfilePath}. Avoid hardcoding credentials!" "SECURITY"
                $vulnerabilitiesFound++
            }
        }
    }
    
    if ($vulnerabilitiesFound -eq 0) {
        Write-LogMessage "success" "No security issues detected in Dockerfiles" "SECURITY"
    } else {
        Write-LogMessage "warning" "Found $vulnerabilitiesFound potential security issues" "SECURITY"
    }
}

# Intelligent service cleanup with dependency awareness
function Stop-DockerServices {
    Write-LogMessage "info" "Stopping Docker services gracefully..." "CLEANUP"
    
    try {
        # First try graceful shutdown
        $stopResult = & $Script:ComposeCommand -f $ComposeFile down --remove-orphans --timeout 30 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-LogMessage "success" "Services stopped gracefully" "CLEANUP"
            return
        } else {
            Write-LogMessage "warning" "Graceful shutdown failed: $stopResult" "CLEANUP"
        }
    }
    catch {
        Write-LogMessage "warning" "Docker Compose down failed: $_" "CLEANUP"
    }
    
    # Fallback: Stop containers individually
    Write-LogMessage "info" "Attempting individual container shutdown..." "CLEANUP"
    $runningContainers = docker ps -q --filter "label=com.docker.compose.project"
    
    if ($runningContainers) {
        foreach ($container in $runningContainers) {
            try {
                $containerName = docker inspect --format "{{.Name}}" $container
                Write-LogMessage "info" "Stopping container: $containerName" "CLEANUP"
                docker stop $container --time 10
                docker rm $container -f
            }
            catch {
                Write-LogMessage "warning" "Failed to stop container $container`: $_" "CLEANUP"
            }
        }
    }
}

# Enhanced Docker cleanup with size reporting
function Invoke-DockerCleanup {
    if ($SkipCleanup) {
        Write-LogMessage "info" "Skipping cleanup as requested" "CLEANUP"
        return
    }
    
    Write-LogMessage "info" "Performing Docker cleanup..." "CLEANUP"
    
    # Get sizes before cleanup
    $beforeSize = docker system df --format "{{.Size}}" | Select-Object -First 1
    
    try {
        # Remove project-specific containers
        $projectName = (Get-Item -Path .).Name.ToLower()
        Write-LogMessage "info" "Cleaning up project containers for: $projectName" "CLEANUP"
        
        $projectContainers = docker ps -a --filter "label=com.docker.compose.project=$projectName" -q
        if ($projectContainers) {
            docker rm -f $projectContainers
            Write-LogMessage "success" "Removed project containers" "CLEANUP"
        }
        
        # Clean up volumes (with confirmation for named volumes)
        Write-LogMessage "info" "Cleaning up Docker volumes..." "CLEANUP"
        $unusedVolumes = docker volume ls -f dangling=true -q
        if ($unusedVolumes) {
            docker volume rm $unusedVolumes
            Write-LogMessage "success" "Removed unused volumes" "CLEANUP"
        }
        
        # Clean up networks
        Write-LogMessage "info" "Cleaning up Docker networks..." "CLEANUP"
        docker network prune -f | Out-Null
        
        # Clean up build cache (partial - keep recent layers)
        Write-LogMessage "info" "Cleaning up build cache..." "CLEANUP"
        docker builder prune -f --filter "until=24h" | Out-Null
        
        # Report space savings
        $afterSize = docker system df --format "{{.Size}}" | Select-Object -First 1
        Write-LogMessage "success" "Cleanup completed. Space usage: $beforeSize → $afterSize" "CLEANUP"
    }
    catch {
        Write-LogMessage "warning" "Cleanup encountered issues: $_" "CLEANUP"
    }
}

# Smart build strategy with dependency caching
function Invoke-DockerBuild {
    param ([string[]]$ServicesToBuild)
    
    Write-LogMessage "info" "Starting intelligent Docker build process..." "BUILD"
    
    if (-not $ServicesToBuild -or $ServicesToBuild.Count -eq 0) {
        $ServicesToBuild = $Script:Config.DefaultServices
    }
    
    # Check which services actually need rebuilding
    $servicesNeedingRebuild = @()
    foreach ($service in $ServicesToBuild) {
        $imageExists = docker images --filter "reference=*${service}*" -q
        if (-not $imageExists) {
            $servicesNeedingRebuild += $service
            Write-LogMessage "info" "Service '$service' needs rebuilding (no image found)" "BUILD"
        }
    }
    
    if ($servicesNeedingRebuild.Count -eq 0) {
        Write-LogMessage "info" "Rebuilding all services to ensure latest versions..." "BUILD"
        $servicesNeedingRebuild = $ServicesToBuild
    }
    
    # Build with parallel processing where possible
    $buildArgs = @("build", "--pull")
    if ($VerbosePreference -eq 'SilentlyContinue') { $buildArgs += "--quiet" }
    
    # Try building all services together first
    try {
        Write-LogMessage "info" "Building services: $($servicesNeedingRebuild -join ', ')" "BUILD"
        $buildCommand = $Script:ComposeCommand, "-f", $ComposeFile + $buildArgs + $servicesNeedingRebuild
        
        $buildOutput = & $buildCommand[0] $buildCommand[1..($buildCommand.Length-1)] 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogMessage "success" "All services built successfully" "BUILD"
            return $true
        } else {
            Write-LogMessage "warning" "Batch build failed, trying individual builds..." "BUILD"
            if ($VerbosePreference -ne 'SilentlyContinue') { Write-LogMessage "debug" "Build output: $buildOutput" "BUILD" }
        }
    }
    catch {
        Write-LogMessage "warning" "Batch build failed with exception: $_" "BUILD"
    }
    
    # Fallback: Build services individually
    $successCount = 0
    foreach ($service in $servicesNeedingRebuild) {
        try {
            Write-LogMessage "info" "Building service individually: $service" "BUILD"
            $buildCommand = $Script:ComposeCommand, "-f", $ComposeFile + $buildArgs + $service
            
            $serviceOutput = & $buildCommand[0] $buildCommand[1..($buildCommand.Length-1)] 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-LogMessage "success" "Service '$service' built successfully" "BUILD"
                $successCount++
            } else {
                Write-LogMessage "error" "Failed to build service '$service'" "BUILD"
                if ($VerbosePreference -ne 'SilentlyContinue') { Write-LogMessage "debug" "Build output: $serviceOutput" "BUILD" }
            }
        }
        catch {
            Write-LogMessage "error" "Service '$service' build failed with exception: $_" "BUILD"
        }
    }
    
    $failedCount = $servicesNeedingRebuild.Count - $successCount
    if ($failedCount -gt 0) {
        Write-LogMessage "warning" "$failedCount out of $($servicesNeedingRebuild.Count) services failed to build" "BUILD"
        return $false
    }
    
    return $true
}

# Intelligent service startup with dependency ordering
function Start-DockerServices {
    param ([string[]]$ServicesToStart)
    
    if ($BuildOnly) {
        Write-LogMessage "info" "Build-only mode, skipping service startup" "STARTUP"
        return $true
    }
    
    Write-LogMessage "info" "Starting Docker services with dependency awareness..." "STARTUP"
    
    # Start infrastructure services first
    $infraServices = $Script:Config.InfrastructureServices | Where-Object { 
        (& $Script:ComposeCommand -f $ComposeFile config --services) -contains $_ 
    }
    
    if ($infraServices) {
        try {
            Write-LogMessage "info" "Starting infrastructure services: $($infraServices -join ', ')" "STARTUP"
            & $Script:ComposeCommand -f $ComposeFile up -d $infraServices
            
            if ($LASTEXITCODE -eq 0) {
                Write-LogMessage "success" "Infrastructure services started" "STARTUP"
                Write-LogMessage "info" "Waiting 15 seconds for infrastructure to initialize..." "STARTUP"
                Start-Sleep -Seconds 15
            }
        }
        catch {
            Write-LogMessage "warning" "Infrastructure startup issues: $_" "STARTUP"
        }
    }
    
    # Start remaining services
    try {
        if ($ServicesToStart -and $ServicesToStart.Count -gt 0) {
            Write-LogMessage "info" "Starting specified services: $($ServicesToStart -join ', ')" "STARTUP"
            & $Script:ComposeCommand -f $ComposeFile up -d $ServicesToStart
        } else {
            Write-LogMessage "info" "Starting all services..." "STARTUP"
            & $Script:ComposeCommand -f $ComposeFile up -d
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogMessage "success" "All services started successfully" "STARTUP"
            return $true
        } else {
            Write-LogMessage "error" "Service startup failed" "STARTUP"
            return $false
        }
    }
    catch {
        Write-LogMessage "error" "Service startup failed with exception: $_" "STARTUP"
        return $false
    }
}

# Comprehensive health checking with timeout
function Test-ServiceHealth {
    if ($SkipHealthCheck) {
        Write-LogMessage "info" "Skipping health checks as requested" "HEALTH"
        return $true
    }
    
    Write-LogMessage "info" "Performing comprehensive health checks..." "HEALTH"
    Start-Sleep -Seconds 10
    
    $containers = & $Script:ComposeCommand -f $ComposeFile ps -q
    $healthyCount = 0
    $totalCount = 0
    
    foreach ($container in $containers) {
        if (-not $container) { continue }
        $totalCount++
        
        try {
            $containerInfo = docker inspect $container | ConvertFrom-Json
            $containerName = $containerInfo.Name -replace '^/', ''
            $state = $containerInfo.State
            
            Write-LogMessage "debug" "Checking container: $containerName" "HEALTH"
            
            # Check if container is running
            if (-not $state.Running) {
                Write-LogMessage "error" "Container $containerName is not running (Status: $($state.Status))" "HEALTH"
                $logs = docker logs --tail $Script:Config.MaxLogLines $container 2>&1
                Write-LogMessage "info" "Recent logs from $containerName`:" "HEALTH"
                $logs | ForEach-Object { Write-LogMessage "debug" "  $_" "HEALTH" }
                continue
            }
            
            # Check health status if available
            if ($state.Health) {
                $healthStatus = $state.Health.Status
                $failingStreak = $state.Health.FailingStreak
                
                switch ($healthStatus) {
                    "healthy" {
                        Write-LogMessage "success" "Container $containerName is healthy" "HEALTH"
                        $healthyCount++
                    }
                    "starting" {
                        Write-LogMessage "warning" "Container $containerName is still starting (be patient...)" "HEALTH"
                    }
                    "unhealthy" {
                        Write-LogMessage "error" "Container $containerName is unhealthy (failing streak: $failingStreak)" "HEALTH"
                        
                        # Show recent health check logs
                        if ($state.Health.Log) {
                            $recentCheck = $state.Health.Log | Select-Object -Last 1
                            Write-LogMessage "error" "Last health check: $($recentCheck.Output)" "HEALTH"
                        }
                    }
                }
            } else {
                # No health check defined, assume healthy if running
                Write-LogMessage "info" "Container $containerName is running (no health check defined)" "HEALTH"
                $healthyCount++
            }
        }
        catch {
            Write-LogMessage "error" "Failed to check health for container $container`: $_" "HEALTH"
        }
    }
    
    $healthPercentage = if ($totalCount -gt 0) { [math]::Round(($healthyCount / $totalCount) * 100, 1) } else { 0 }
    Write-LogMessage "info" "Health check summary: $healthyCount/$totalCount containers healthy (${healthPercentage}%)" "HEALTH"
    
    return $healthyCount -eq $totalCount
}

# Enhanced dependency verification with package-specific checks
function Test-ContainerDependencies {
    Write-LogMessage "info" "Verifying critical dependencies in containers..." "DEPS"
    
    $containers = & $Script:ComposeCommand -f $ComposeFile ps -q
    $verificationResults = @{}
    
    foreach ($container in $containers) {
        if (-not $container) { continue }
        
        try {
            $containerInfo = docker inspect $container | ConvertFrom-Json
            $containerName = $containerInfo.Name -replace '^/', ''
            
            Write-LogMessage "info" "Verifying dependencies in: $containerName" "DEPS"
              # Detect container type and verify appropriate dependencies
            $pythonAvailable = (docker exec $container which python 2>$null) -or (docker exec $container which python3 2>$null)
            $nodeAvailable = docker exec $container which node 2>$null
            
            if ($pythonAvailable) {
                $verificationResults[$containerName] = Test-PythonDependencies -Container $container -ContainerName $containerName
            }
            elseif ($nodeAvailable) {
                $verificationResults[$containerName] = Test-NodeDependencies -Container $container -ContainerName $containerName
            }
            else {
                Write-LogMessage "info" "Container $containerName`: No Python or Node.js runtime detected" "DEPS"
                $verificationResults[$containerName] = @{ Status = "Skipped"; Reason = "No supported runtime" }
            }
        }
        catch {
            Write-LogMessage "error" "Failed to verify dependencies for container $container`: $_" "DEPS"
            $verificationResults[$container] = @{ Status = "Error"; Error = $_.Exception.Message }
        }
    }    # Summary
    $successCount = 0
    $totalCount = 0
    
    if ($verificationResults -and $verificationResults -is [hashtable] -and $verificationResults.Count -gt 0) {
        $successfulResults = $verificationResults.Values | Where-Object { $_.Status -eq "Success" }
        $successCount = if ($successfulResults) { ($successfulResults | Measure-Object).Count } else { 0 }
        $totalCount = $verificationResults.Count
    }
    
    Write-LogMessage "info" "Dependency verification summary: $successCount/$totalCount containers verified successfully" "DEPS"
    
    return $verificationResults
}

function Test-PythonDependencies {
    param (
        [string]$Container,
        [string]$ContainerName
    )
    
    $pythonScript = @'
import sys
import importlib.util
import json

critical_packages = %PACKAGES%
results = {
    "installed": [],
    "missing": [],
    "versions": {}
}

for package in critical_packages:
    try:
        spec = importlib.util.find_spec(package)
        if spec is not None:
            results["installed"].append(package)
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                results["versions"][package] = version
            except:
                results["versions"][package] = 'unknown'
        else:
            results["missing"].append(package)
    except Exception as e:
        results["missing"].append(package)

print(json.dumps(results))
'@ -replace '%PACKAGES%', ($Script:Config.CriticalPythonPackages | ConvertTo-Json)
    
    try {
        $tempScript = "check_python_deps_$(Get-Random).py"
        $pythonScript | Out-File -FilePath $tempScript -Encoding utf8
        
        docker cp $tempScript "${Container}:/tmp/$tempScript"
        $output = docker exec $Container python "/tmp/$tempScript" 2>&1
          if ($LASTEXITCODE -eq 0) {
            $results = $output | ConvertFrom-Json
            
            foreach ($pkg in $results.installed) {
                $version = $results.versions[$pkg]
                Write-LogMessage "success" "[OK] $pkg ($version) installed in $containerName" "DEPS"
            }
            
            foreach ($pkg in $results.missing) {
                Write-LogMessage "error" "[FAIL] $pkg missing in $containerName" "DEPS"
            }
            
            $status = if ($results.missing.Count -eq 0) { "Success" } else { "Partial" }
            return @{
                Status = $status
                Installed = $results.installed
                Missing = $results.missing
                Versions = $results.versions
            }
        } else {
            Write-LogMessage "error" "Python dependency check failed in $containerName`: $output" "DEPS"
            return @{ Status = "Error"; Error = $output }
        }
    }    catch {
        Write-LogMessage "error" "Failed to run Python dependency check: $_" "DEPS"
        return @{ Status = "Error"; Error = $_.Exception.Message }
    }
    finally {
        Remove-Item -Path $tempScript -ErrorAction SilentlyContinue
        docker exec $Container rm -f "/tmp/$tempScript" 2>$null
    }
}

function Test-NodeDependencies {
    param (
        [string]$Container,
        [string]$ContainerName
    )
    
    $nodeScript = @'
const fs = require('fs');
const path = require('path');

const criticalPackages = %PACKAGES%;
const results = {
    installed: [],
    missing: [],
    versions: {}
};

criticalPackages.forEach(pkg => {
    try {
        const packagePath = require.resolve(pkg);
        const packageJson = require(path.join(packagePath, '../../package.json'));
        results.installed.push(pkg);
        results.versions[pkg] = packageJson.version || 'unknown';
    } catch (e) {
        results.missing.push(pkg);
    }
});

console.log(JSON.stringify(results));
'@ -replace '%PACKAGES%', ($Script:Config.CriticalNodePackages | ConvertTo-Json)
    
    try {
        $tempScript = "check_node_deps_$(Get-Random).js"
        $nodeScript | Out-File -FilePath $tempScript -Encoding utf8
        
        docker cp $tempScript "${Container}:/tmp/$tempScript"
        $output = docker exec $Container node "/tmp/$tempScript" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $results = $output | ConvertFrom-Json
            
            foreach ($pkg in $results.installed) {
                $version = $results.versions[$pkg]
                Write-LogMessage "success" "[OK] $pkg ($version) installed in $containerName" "DEPS"
            }
            
            foreach ($pkg in $results.missing) {
                Write-LogMessage "error" "[FAIL] $pkg missing in $containerName" "DEPS"
            }
            
            $status = if ($results.missing.Count -eq 0) { "Success" } else { "Partial" }
            return @{
                Status = $status
                Installed = $results.installed
                Missing = $results.missing
                Versions = $results.versions
            }
        } else {
            Write-LogMessage "error" "Node.js dependency check failed in ${containerName}: $output" "DEPS"
            return @{ Status = "Error"; Error = $output }
        }
    }
    catch {
        Write-LogMessage "error" "Failed to run Node.js dependency check: $_" "DEPS"
        return @{ Status = "Error"; Error = $_.Exception.Message }
    }
    finally {
        Remove-Item -Path $tempScript -ErrorAction SilentlyContinue
        docker exec $Container rm -f "/tmp/$tempScript" 2>$null
    }
}

# Generate comprehensive report
function New-BuildReport {
    param (
        [hashtable]$SystemResources,
        [hashtable]$DependencyResults,
        [bool]$BuildSuccess,
        [bool]$HealthCheckSuccess,
        [datetime]$StartTime
    )
      $endTime = Get-Date
    $duration = $endTime - $StartTime
    
    $report = @"
# Docker Rebuild Report
Generated: $($endTime.ToString("yyyy-MM-dd HH:mm:ss"))
Duration: $($duration.ToString("mm\:ss"))
Success: $(if ($BuildSuccess -and $HealthCheckSuccess) { "[OK] Yes" } else { "[FAIL] No" })

System Resources:
  Memory: $($SystemResources.Memory.Available)GB available / $($SystemResources.Memory.Total)GB total
  CPU: $($SystemResources.CPU.Cores) cores
  Disk: $($SystemResources.Disk.Free)GB free / $($SystemResources.Disk.Total)GB total

Build Results:
  Build Status: $(if ($BuildSuccess) { "[OK] Success" } else { "[FAIL] Failed" })
  Health Check: $(if ($HealthCheckSuccess) { "[OK] Passed" } else { "[FAIL] Failed" })

Dependency Verification:
"@
    
    foreach ($container in $DependencyResults.Keys) {
        $result = $DependencyResults[$container]
        $status = switch ($result.Status) {
            "Success" { "[OK]" }
            "Partial" { "[WARN]" }
            "Error" { "[FAIL]" }
            "Skipped" { "[SKIP]" }
        }
        $report += "`n  $container`: $status $($result.Status)"
        
        if ($result.Missing -and $result.Missing.Count -gt 0) {
            $report += " (Missing: $($result.Missing -join ', '))"        }
    }
    
    $nextSteps = "`nNext Steps:"
    if (-not $BuildSuccess) { $nextSteps += "`n  Review build logs for failed services" }
    if (-not $HealthCheckSuccess) { $nextSteps += "`n  Check service health and logs" }
    $nextSteps += "`n  Run docker-compose logs -f to monitor services"
    $nextSteps += "`n  Run docker-compose ps to check service status"
    $nextSteps += "`n  Run docker-compose down to stop services"
    $nextSteps += "`n`nReport saved to: docker-rebuild-report.md"
    
    $report += $nextSteps
    
    $report | Out-File -FilePath "docker-rebuild-report.md" -Encoding utf8
    Write-LogMessage "info" "Build report saved to: docker-rebuild-report.md" "REPORT"
    
    return $report
}

# Main execution function
function Invoke-DockerRebuild {
    $startTime = Get-Date
    Write-LogMessage "info" "=== Docker Rebuild Process Started ===" "MAIN"
    Write-LogMessage "info" "PowerShell Version: $($PSVersionTable.PSVersion)" "MAIN"
    Write-LogMessage "info" "Compose File: $ComposeFile" "MAIN"
    
    try {
        # Initialize log file
        "Docker Rebuild Log - Started at $startTime" | Out-File -FilePath "docker-rebuild.log" -Encoding utf8
        
        # Step 1: Environment validation
        Test-DockerEnvironment
        
        # Step 2: System resource analysis
        $systemResources = Get-SystemResources
        
        # Step 3: Security scanning
        $dockerfiles = @(
            ".\Dockerfile",
            ".\scraper\Dockerfile",
            ".\captcha-service\Dockerfile",
            ".\proxy-service\Dockerfile",
            ".\frontend\Dockerfile",
            ".\api\Dockerfile",
            ".\worker\Dockerfile"
        ) | Where-Object { Test-Path $_ }
        
        if ($dockerfiles.Count -gt 0) {
            Invoke-SecurityScan -DockerfilePaths $dockerfiles
        }
        
        # Step 4: Stop existing services
        Stop-DockerServices
        
        # Step 5: Cleanup resources
        Invoke-DockerCleanup
        
        # Step 6: Build services
        $servicesToBuild = if ($Services.Count -gt 0) { $Services } else { @() }
        $buildSuccess = Invoke-DockerBuild -ServicesToBuild $servicesToBuild
        
        if (-not $buildSuccess) {
            Write-LogMessage "error" "Build process failed. Check logs for details." "MAIN"
        }
        
        # Step 7: Start services (unless build-only mode)
        $startupSuccess = $true
        if (-not $BuildOnly) {
            $startupSuccess = Start-DockerServices -ServicesToStart $servicesToBuild
        }
        
        # Step 8: Health checks
        $healthSuccess = $true
        if (-not $BuildOnly -and $startupSuccess) {
            $healthSuccess = Test-ServiceHealth
        }
        
        # Step 9: Dependency verification
        $dependencyResults = @{}
        if (-not $BuildOnly -and $startupSuccess) {
            $dependencyResults = Test-ContainerDependencies
        }
        
        # Step 10: Generate report
        $report = New-BuildReport -SystemResources $systemResources -DependencyResults $dependencyResults -BuildSuccess $buildSuccess -HealthCheckSuccess $healthSuccess -StartTime $startTime
        
        # Final status
        $overallSuccess = $buildSuccess -and $startupSuccess -and $healthSuccess
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        if ($overallSuccess) {
            Write-LogMessage "success" "=== Docker Rebuild Completed Successfully in $($duration.ToString("mm\:ss")) ===" "MAIN"
        } else {
            Write-LogMessage "warning" "=== Docker Rebuild Completed with Issues in $($duration.ToString("mm\:ss")) ===" "MAIN"
        }
        
        # Useful commands for user
        Write-LogMessage "info" "Useful commands:" "MAIN"
        Write-LogMessage "info" "  View logs: $($Script:ComposeCommand) -f $ComposeFile logs -f" "MAIN"
        Write-LogMessage "info" "  Check status: $($Script:ComposeCommand) -f $ComposeFile ps" "MAIN"
        Write-LogMessage "info" "  Stop services: $($Script:ComposeCommand) -f $ComposeFile down" "MAIN"
        Write-LogMessage "info" "  View report: Get-Content docker-rebuild-report.md" "MAIN"
        
        return $overallSuccess
    }
    catch {
        Write-LogMessage "error" "Critical error during rebuild process: $_" "MAIN"
        Write-LogMessage "error" "Stack trace: $($_.ScriptStackTrace)" "MAIN"
        return $false
    }
}

# Script entry point
try {
    $success = Invoke-DockerRebuild
    exit $(if ($success) { 0 } else { 1 })
}
catch {
    Write-LogMessage "error" "Unhandled exception: $_" "MAIN"    exit 1
}