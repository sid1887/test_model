# Enhanced Startup Script for Cumpair AI System
param(
    [switch]$DevMode,
    [switch]$SkipPreFlight,
    [switch]$QuickCheck,
    [switch]$DockerMode,
    [switch]$ShowHelp
)

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{"Red"="Red"; "Green"="Green"; "Yellow"="Yellow"; "Blue"="Blue"; "Cyan"="Cyan"; "White"="White"}
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Show-Help {
    Write-ColorOutput "🚀 Cumpair Enhanced Startup Script" "Cyan"
    Write-ColorOutput "=================================================="
    Write-ColorOutput ""
    Write-ColorOutput "This script runs pre-flight checks and starts Cumpair safely." "White"
    Write-ColorOutput ""
    Write-ColorOutput "Usage: .\enhanced-start.ps1 [options]" "Yellow"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "Yellow"
    Write-ColorOutput "  -DevMode       Start in development mode" "White"
    Write-ColorOutput "  -SkipPreFlight Skip dependency check" "White"
    Write-ColorOutput "  -QuickCheck    Quick check only" "White"
    Write-ColorOutput "  -DockerMode    Use Docker containers" "White"
    Write-ColorOutput "  -ShowHelp      Show this help" "White"
}

function Test-Prerequisites {
    Write-ColorOutput "🔧 Checking prerequisites..." "Cyan"
    
    if ($DockerMode) {
        try {
            $null = docker --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Docker is available" "Green"
                return $true
            }
        } catch {
            Write-ColorOutput "❌ Docker not available" "Red"
            return $false
        }
    } else {
        try {
            $null = python --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Python is available" "Green"
                return $true
            }
        } catch {
            Write-ColorOutput "❌ Python not available" "Red"
            return $false
        }
    }
    return $false
}

function Start-PreFlightCheck {
    if ($SkipPreFlight) {
        Write-ColorOutput "⚠️ Skipping pre-flight check" "Yellow"
        return $true
    }
    
    Write-ColorOutput "🔍 Running pre-flight check..." "Cyan"
    
    $arguments = @()
    if ($QuickCheck) { $arguments += "--quick" }
    if ($DockerMode) { $arguments += "--docker" }
    
    try {
        python pre_flight_check.py $arguments
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Pre-flight check passed!" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Pre-flight check failed!" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "💥 Pre-flight check error: $_" "Red"
        return $false
    }
}

function Start-Application {
    Write-ColorOutput "🚀 Starting Cumpair..." "Cyan"
    
    if ($DockerMode) {
        Write-ColorOutput "🐳 Using Docker..." "Blue"
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker containers started!" "Green"
            Write-ColorOutput "🌐 App: http://localhost:8000" "White"
            Write-ColorOutput "📚 Docs: http://localhost:8000/docs" "White"
            return $true
        } else {
            Write-ColorOutput "❌ Docker startup failed" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "🐍 Using local Python..." "Blue"
        if ($DevMode) {
            Write-ColorOutput "🛠️ Development mode" "Yellow"
            python safe_start.py --dev --quick-check
        } else {
            python safe_start.py --quick-check
        }
        return $true
    }
}

# Main execution
if ($ShowHelp) {
    Show-Help
    exit 0
}

Write-ColorOutput "🚀 Cumpair Enhanced Startup" "Cyan"
Write-ColorOutput "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
Write-ColorOutput ""

if (-not (Test-Prerequisites)) {
    Write-ColorOutput "❌ Prerequisites failed!" "Red"
    exit 1
}

if (-not (Start-PreFlightCheck)) {
    Write-ColorOutput "❌ Pre-flight check failed!" "Red"
    exit 1
}

if (-not (Start-Application)) {
    Write-ColorOutput "❌ Application startup failed!" "Red"
    exit 1
}

Write-ColorOutput ""
Write-ColorOutput "🎉 Cumpair is running!" "Green"
Write-ColorOutput "📱 Main: http://localhost:8000" "White"
Write-ColorOutput "📚 Docs: http://localhost:8000/docs" "White"
