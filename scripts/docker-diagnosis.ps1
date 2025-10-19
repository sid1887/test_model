#!/usr/bin/env pwsh

# 🔍 DOCKER DIAGNOSIS SCRIPT
# Comprehensive analysis of Docker environment and issues

Write-Host "🔍 DOCKER DIAGNOSIS STARTING..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Function to check service status
function Check-Service {
    param($serviceName, $port)
    
    Write-Host "🔍 Checking $serviceName..." -ForegroundColor Yellow
    
    # Check if container is running
    $container = docker ps -q -f "name=$serviceName"
    if ($container) {
        Write-Host "   ✅ Container is running: $container" -ForegroundColor Green
        
        # Check port
        if ($port) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$port" -Method GET -TimeoutSec 5 -UseBasicParsing
                Write-Host "   ✅ Port $port is responding" -ForegroundColor Green
            } catch {
                Write-Host "   ❌ Port $port is not responding: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # Check logs for errors
        $logs = docker logs $container --tail 10 2>&1
        $errors = $logs | Select-String -Pattern "ERROR|FATAL|failed|Failed"
        if ($errors) {
            Write-Host "   ⚠️  Recent errors found:" -ForegroundColor Yellow
            $errors | ForEach-Object { Write-Host "      $($_.Line)" -ForegroundColor Red }
        } else {
            Write-Host "   ✅ No recent errors in logs" -ForegroundColor Green
        }
    } else {
        Write-Host "   ❌ Container is not running" -ForegroundColor Red
        
        # Check if container exists but is stopped
        $stoppedContainer = docker ps -aq -f "name=$serviceName"
        if ($stoppedContainer) {
            Write-Host "   ℹ️  Container exists but is stopped: $stoppedContainer" -ForegroundColor Yellow
            
            # Show exit code
            $exitCode = docker inspect $stoppedContainer --format='{{.State.ExitCode}}'
            Write-Host "   ℹ️  Exit code: $exitCode" -ForegroundColor Yellow
            
            # Show last logs
            Write-Host "   📋 Last logs:" -ForegroundColor Yellow
            docker logs $stoppedContainer --tail 5 2>&1 | ForEach-Object { Write-Host "      $($_)" -ForegroundColor Gray }
        } else {
            Write-Host "   ❌ Container does not exist" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# System Information
Write-Host "🖥️  SYSTEM INFORMATION" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Docker version
Write-Host "Docker Version:" -ForegroundColor Yellow
docker --version

# Docker Compose version
Write-Host "Docker Compose Version:" -ForegroundColor Yellow
docker-compose --version

# System resources
Write-Host "System Resources:" -ForegroundColor Yellow
$memory = Get-WmiObject -Class Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory
$totalGB = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
$freeGB = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
Write-Host "   Total RAM: $totalGB GB" -ForegroundColor Gray
Write-Host "   Free RAM: $freeGB GB" -ForegroundColor Gray

# Disk space
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$totalDiskGB = [math]::Round($disk.Size / 1GB, 2)
$freeDiskGB = [math]::Round($disk.FreeSpace / 1GB, 2)
Write-Host "   Total Disk: $totalDiskGB GB" -ForegroundColor Gray
Write-Host "   Free Disk: $freeDiskGB GB" -ForegroundColor Gray

Write-Host ""

# Docker System Information
Write-Host "🐳 DOCKER SYSTEM INFORMATION" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Docker system df
Write-Host "Docker System Usage:" -ForegroundColor Yellow
docker system df

# Docker info
Write-Host "Docker Info (Key Metrics):" -ForegroundColor Yellow
$dockerInfo = docker info --format="json" | ConvertFrom-Json
Write-Host "   Containers: $($dockerInfo.Containers)" -ForegroundColor Gray
Write-Host "   Images: $($dockerInfo.Images)" -ForegroundColor Gray
Write-Host "   Driver: $($dockerInfo.Driver)" -ForegroundColor Gray

Write-Host ""

# Current Container Status
Write-Host "📦 CURRENT CONTAINER STATUS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# All containers
Write-Host "All Containers:" -ForegroundColor Yellow
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"

Write-Host ""

# Service-Specific Checks
Write-Host "🔍 SERVICE-SPECIFIC DIAGNOSIS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Check-Service "postgres" 5432
Check-Service "redis" 6379
Check-Service "web" 8000
Check-Service "scraper" 3001
Check-Service "worker" $null
Check-Service "flower" 5555
Check-Service "frontend" 8080
Check-Service "captcha" 9001
Check-Service "proxy" 8001

# Network Analysis
Write-Host "🌐 NETWORK ANALYSIS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Docker networks
Write-Host "Docker Networks:" -ForegroundColor Yellow
docker network ls

# Port usage
Write-Host "Port Usage Check:" -ForegroundColor Yellow
$ports = @(5432, 6379, 8000, 3001, 5555, 8080, 9001, 8001, 3002, 9090)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "   Port $port`: IN USE by PID $($connection.OwningProcess)" -ForegroundColor Red
    } else {
        Write-Host "   Port $port`: AVAILABLE" -ForegroundColor Green
    }
}

Write-Host ""

# File System Analysis
Write-Host "📁 FILE SYSTEM ANALYSIS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check critical files
$criticalFiles = @(
    "docker-compose.complete.yml",
    "Dockerfile",
    ".env",
    "requirements.txt",
    "main.py"
)

Write-Host "Critical Files:" -ForegroundColor Yellow
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "   ✅ $file (${size} bytes)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file MISSING" -ForegroundColor Red
    }
}

# Check directories
$criticalDirs = @(
    "app",
    "scraper",
    "frontend",
    "secrets",
    "logs",
    "uploads"
)

Write-Host "Critical Directories:" -ForegroundColor Yellow
foreach ($dir in $criticalDirs) {
    if (Test-Path $dir) {
        $items = (Get-ChildItem $dir -ErrorAction SilentlyContinue).Count
        Write-Host "   ✅ $dir/ ($items items)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir/ MISSING" -ForegroundColor Red
    }
}

Write-Host ""

# Recent Docker Events
Write-Host "📊 RECENT DOCKER EVENTS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "Recent Docker Events (last 10):" -ForegroundColor Yellow
docker events --since="10m" --until="now" --format="table {{.Time}}\t{{.Action}}\t{{.Type}}\t{{.Actor.Attributes.name}}" | Select-Object -First 10

Write-Host ""

# Recommendations
Write-Host "💡 RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check for common issues
$recommendations = @()

# Check available memory
if ($freeGB -lt 2) {
    $recommendations += "⚠️  Low memory: $freeGB GB free. Consider freeing up RAM or reducing container memory limits."
}

# Check available disk space
if ($freeDiskGB -lt 5) {
    $recommendations += "⚠️  Low disk space: $freeDiskGB GB free. Consider cleaning up Docker images and volumes."
}

# Check for port conflicts
$portsInUse = @()
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $portsInUse += $port
    }
}

if ($portsInUse.Count -gt 0) {
    $recommendations += "⚠️  Port conflicts detected on ports: $($portsInUse -join ', '). Stop conflicting services or change port mappings."
}

# Check for missing services
$runningContainers = docker ps --format "{{.Names}}"
$requiredServices = @("postgres", "redis", "web")
$missingServices = $requiredServices | Where-Object { $runningContainers -notcontains $_ }

if ($missingServices.Count -gt 0) {
    $recommendations += "❌ Critical services not running: $($missingServices -join ', '). Run the comprehensive fix script."
}

# Display recommendations
if ($recommendations.Count -gt 0) {
    foreach ($rec in $recommendations) {
        Write-Host $rec -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ No critical issues detected!" -ForegroundColor Green
}

Write-Host ""

# Quick Fix Commands
Write-Host "🛠️  QUICK FIX COMMANDS" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "If you need to fix issues:" -ForegroundColor Yellow
Write-Host "   1. Run comprehensive fix: .\docker-complete-fix.ps1" -ForegroundColor Gray
Write-Host "   2. Run emergency fix: .\docker-emergency-fix.ps1" -ForegroundColor Gray
Write-Host "   3. Check logs: docker-compose -f docker-compose.complete.yml logs -f" -ForegroundColor Gray
Write-Host "   4. Restart services: docker-compose -f docker-compose.complete.yml restart" -ForegroundColor Gray
Write-Host "   5. Complete reset: docker-compose -f docker-compose.complete.yml down --volumes && docker system prune -a -f" -ForegroundColor Gray

Write-Host ""
Write-Host "🎯 DIAGNOSIS COMPLETE!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green