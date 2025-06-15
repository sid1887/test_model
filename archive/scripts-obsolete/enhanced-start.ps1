# Enhanced Startup Script for Cumpair AI System
# Integrates pre-flight dependency checks with your existing workflow

param(
    [switch]$DevMode,
    [switch]$SkipPreFlight,
    [switch]$QuickCheck,
    [switch]$ForceReinstall,
    [switch]$DockerMode,
    [switch]$ShowHelp
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green" 
        "Yellow" = "Yellow"
        "Blue" = "Blue"
        "Cyan" = "Cyan"
        "Magenta" = "Magenta"
        "White" = "White"
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

function Show-Help {
    Write-ColorOutput "🚀 Cumpair Enhanced Startup Script" "Cyan"
    Write-ColorOutput "=" * 50 "Blue"
    Write-ColorOutput ""
    Write-ColorOutput "This script runs pre-flight checks and starts your Cumpair application safely." "White"
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" "Yellow"
    Write-ColorOutput "  .\enhanced-start.ps1 [options]" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "Yellow"
    Write-ColorOutput "  -DevMode          Start in development mode with auto-reload" "White"
    Write-ColorOutput "  -SkipPreFlight    Skip pre-flight dependency check (not recommended)" "White"
    Write-ColorOutput "  -QuickCheck       Run only critical package checks (faster)" "White"
    Write-ColorOutput "  -ForceReinstall   Force reinstall packages during pre-flight" "White"
    Write-ColorOutput "  -DockerMode       Use Docker containers instead of local Python" "White"
    Write-ColorOutput "  -ShowHelp         Show this help message" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" "Yellow"
    Write-ColorOutput "  .\enhanced-start.ps1                    # Standard startup with full checks" "White"
    Write-ColorOutput "  .\enhanced-start.ps1 -DevMode           # Development mode" "White"
    Write-ColorOutput "  .\enhanced-start.ps1 -QuickCheck        # Fast startup" "White"
    Write-ColorOutput "  .\enhanced-start.ps1 -DockerMode        # Use Docker" "White"
}

function Test-Prerequisites {
    Write-ColorOutput "🔧 Checking prerequisites..." "Cyan"
    
    $allGood = $true
    
    if ($DockerMode) {
        # Check Docker
        try {
            $dockerVersion = docker --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Docker is available: $dockerVersion" "Green"
            } else {
                Write-ColorOutput "❌ Docker is not available" "Red"
                $allGood = $false
            }
        } catch {
            Write-ColorOutput "❌ Docker is not available" "Red"
            $allGood = $false
        }
        
        # Check if docker-compose.yml exists
        if (Test-Path "docker-compose.yml") {
            Write-ColorOutput "✅ docker-compose.yml found" "Green"
        } else {
            Write-ColorOutput "❌ docker-compose.yml not found" "Red"
            $allGood = $false
        }
    } else {
        # Check Python
        try {
            $pythonVersion = python --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Python is available: $pythonVersion" "Green"
            } else {
                Write-ColorOutput "❌ Python is not available" "Red"
                $allGood = $false
            }
        } catch {
            Write-ColorOutput "❌ Python is not available" "Red"
            $allGood = $false
        }
        
        # Check main.py
        if (Test-Path "main.py") {
            Write-ColorOutput "✅ main.py found" "Green"
        } else {
            Write-ColorOutput "❌ main.py not found" "Red"
            $allGood = $false
        }
    }
    
    return $allGood
}

function Start-PreFlightCheck {
    if ($SkipPreFlight) {
        Write-ColorOutput "⚠️ Skipping pre-flight check (not recommended)" "Yellow"
        return $true
    }
    
    Write-ColorOutput "🔍 Running pre-flight dependency check..." "Cyan"
    
    $arguments = @()
    
    if ($QuickCheck) {
        $arguments += "--quick"
    }
    
    if ($ForceReinstall) {
        $arguments += "--force"
    }
    
    if ($DockerMode) {
        $arguments += "--docker"
    }
    
    try {
        if ($DockerMode -and (Get-Command docker -ErrorAction SilentlyContinue)) {
            # Check if container is running
            $containerStatus = docker ps --filter "name=compair_web" --format "{{.Status}}" 2>$null
            if ($containerStatus) {
                Write-ColorOutput "🐳 Running pre-flight check in Docker container..." "Cyan"
                docker exec compair_web python pre_flight_check.py $arguments
                $exitCode = $LASTEXITCODE
            } else {
                Write-ColorOutput "⚠️ Container not running, running pre-flight check locally..." "Yellow"
                python pre_flight_check.py $arguments
                $exitCode = $LASTEXITCODE
            }
        } else {
            # Run locally
            python pre_flight_check.py $arguments
            $exitCode = $LASTEXITCODE
        }
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "✅ Pre-flight check passed!" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Pre-flight check failed!" "Red"
            Write-ColorOutput "💡 Check the emergency_requirements.txt file for packages that need manual installation" "Yellow"
            return $false
        }
        
    } catch {
        Write-ColorOutput "💥 Error during pre-flight check: $_" "Red"
        return $false
    }
}

function Start-Application {
    Write-ColorOutput "🚀 Starting Cumpair application..." "Cyan"
    
    if ($DockerMode) {
        Write-ColorOutput "🐳 Starting with Docker..." "Blue"
        
        # Check if containers are already running
        $runningContainers = docker ps --filter "name=compair" --format "{{.Names}}" 2>$null
        
        if ($runningContainers) {
            Write-ColorOutput "ℹ️ Containers already running:" "Blue"
            foreach ($container in $runningContainers) {
                Write-ColorOutput "   📦 $container" "White"
            }
            Write-ColorOutput "💡 Use 'docker-compose restart' to restart or 'docker-compose down' to stop" "Yellow"
        } else {
            Write-ColorOutput "🔄 Starting Docker containers..." "Blue"
            docker-compose up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Docker containers started successfully!" "Green"
                Write-ColorOutput ""
                Write-ColorOutput "🌐 Application URLs:" "Cyan"
                Write-ColorOutput "   Main App:     http://localhost:8000" "White"
                Write-ColorOutput "   API Docs:     http://localhost:8000/docs" "White"
                Write-ColorOutput "   Health Check: http://localhost:8000/api/v1/health" "White"
                
                # Wait a moment for services to start
                Start-Sleep -Seconds 3
                
                # Test if the application is responding
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 10 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        Write-ColorOutput "✅ Application is responding!" "Green"
                    }
                } catch {
                    Write-ColorOutput "⚠️ Application may still be starting up..." "Yellow"
                    Write-ColorOutput "💡 Check logs with: docker-compose logs -f" "Blue"
                }
            } else {
                Write-ColorOutput "❌ Failed to start Docker containers" "Red"
                return $false
            }
        }
    } else {
        Write-ColorOutput "🐍 Starting with local Python..." "Blue"
        
        if ($DevMode) {
            Write-ColorOutput "🛠️ Development mode with auto-reload enabled" "Yellow"
            python safe_start.py --dev --quick-check
        } else {
            Write-ColorOutput "🏭 Production mode" "Blue"
            python safe_start.py --quick-check
        }
    }
    
    return $true
}

function Show-PostStartupInfo {
    Write-ColorOutput ""
    Write-ColorOutput "🎉 Cumpair is now running!" "Green"
    Write-ColorOutput "=" * 40 "Green"
    Write-ColorOutput ""
    Write-ColorOutput "🌐 Key URLs:" "Cyan"
    Write-ColorOutput "   📱 Main Application: http://localhost:8000" "White"
    Write-ColorOutput "   📚 API Documentation: http://localhost:8000/docs" "White"
    Write-ColorOutput "   💚 Health Check: http://localhost:8000/api/v1/health" "White"
    Write-ColorOutput ""
    Write-ColorOutput "🔧 Useful Commands:" "Yellow"
    
    if ($DockerMode) {
        Write-ColorOutput "   View logs:        docker-compose logs -f" "White"
        Write-ColorOutput "   Stop services:    docker-compose down" "White"
        Write-ColorOutput "   Restart:          docker-compose restart" "White"
        Write-ColorOutput "   Shell access:     docker exec -it compair_web bash" "White"
    } else {
        Write-ColorOutput "   Stop application: Ctrl+C" "White"
        Write-ColorOutput "   View logs:        Check console output" "White"
        Write-ColorOutput "   Restart:          Run this script again" "White"
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "📊 Next Steps:" "Cyan"
    Write-ColorOutput "   1. Open http://localhost:8000 in your browser" "White"
    Write-ColorOutput "   2. Try uploading an image for AI analysis" "White"
    Write-ColorOutput "   3. Test the price comparison features" "White"
    Write-ColorOutput "   4. Check the API docs for programmatic access" "White"
    Write-ColorOutput ""
    Write-ColorOutput "❓ Need help? Check the documentation or run with -ShowHelp" "Blue"
}

function Main {
    if ($ShowHelp) {
        Show-Help
        return
    }
    
    Write-ColorOutput "🚀 Cumpair Enhanced Startup" "Cyan"
    Write-ColorOutput "=" * 50 "Blue"
    Write-ColorOutput "Current Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
    Write-ColorOutput ""
    
    # Step 1: Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-ColorOutput ""
        Write-ColorOutput "❌ Prerequisites check failed!" "Red"
        Write-ColorOutput "Please resolve the issues above before continuing." "Yellow"
        exit 1
    }
    
    # Step 2: Run pre-flight check
    if (-not (Start-PreFlightCheck)) {
        Write-ColorOutput ""
        Write-ColorOutput "❌ Pre-flight check failed!" "Red"
        Write-ColorOutput "Critical dependencies are missing. Please resolve before continuing." "Yellow"
        exit 1
    }
    
    # Step 3: Start the application
    if (-not (Start-Application)) {
        Write-ColorOutput ""
        Write-ColorOutput "❌ Application startup failed!" "Red"
        exit 1
    }
    
    # Step 4: Show post-startup information
    Show-PostStartupInfo
}

# Run main function
Main
