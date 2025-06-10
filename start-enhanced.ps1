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
    Write-ColorOutput "Cumpair Enhanced Startup Script" "Cyan"
    Write-ColorOutput "==============================="
    Write-ColorOutput ""
    Write-ColorOutput "This script runs pre-flight checks and starts Cumpair safely." "White"
    Write-ColorOutput ""
    Write-ColorOutput "Usage: .\start-enhanced.ps1 [options]" "Yellow"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "Yellow"
    Write-ColorOutput "  -DevMode       Start in development mode with auto-reload" "White"
    Write-ColorOutput "  -SkipPreFlight Skip dependency check (not recommended)" "White"
    Write-ColorOutput "  -QuickCheck    Quick check of critical packages only" "White"
    Write-ColorOutput "  -DockerMode    Use Docker containers" "White"
    Write-ColorOutput "  -ShowHelp      Show this help message" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" "Yellow"
    Write-ColorOutput "  .\start-enhanced.ps1                # Standard startup" "White"
    Write-ColorOutput "  .\start-enhanced.ps1 -DevMode       # Development mode" "White"
    Write-ColorOutput "  .\start-enhanced.ps1 -QuickCheck    # Fast startup" "White"
    Write-ColorOutput "  .\start-enhanced.ps1 -DockerMode    # Use Docker" "White"
}

function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." "Cyan"
    
    if ($DockerMode) {
        try {
            $dockerVersion = docker --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "SUCCESS: Docker is available - $dockerVersion" "Green"
                return $true
            } else {
                Write-ColorOutput "ERROR: Docker not available" "Red"
                return $false
            }
        } catch {
            Write-ColorOutput "ERROR: Docker not found" "Red"
            return $false
        }
    } else {
        try {
            $pythonVersion = python --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "SUCCESS: Python is available - $pythonVersion" "Green"
                
                if (Test-Path "main.py") {
                    Write-ColorOutput "SUCCESS: main.py found" "Green"
                    return $true
                } else {
                    Write-ColorOutput "ERROR: main.py not found" "Red"
                    return $false
                }
            } else {
                Write-ColorOutput "ERROR: Python not available" "Red"
                return $false
            }
        } catch {
            Write-ColorOutput "ERROR: Python not found" "Red"
            return $false
        }
    }
}

function Start-PreFlightCheck {
    if ($SkipPreFlight) {
        Write-ColorOutput "WARNING: Skipping pre-flight check (not recommended)" "Yellow"
        return $true
    }
    
    Write-ColorOutput "Running pre-flight dependency check..." "Cyan"
    
    $arguments = @()
    if ($QuickCheck) { $arguments += "--quick" }
    if ($DockerMode) { $arguments += "--docker" }
    
    try {
        python pre_flight_check.py $arguments
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "SUCCESS: Pre-flight check passed!" "Green"
            return $true
        } else {
            Write-ColorOutput "ERROR: Pre-flight check failed!" "Red"
            Write-ColorOutput "TIP: Check emergency_requirements.txt for manual installation" "Yellow"
            return $false
        }
    } catch {
        Write-ColorOutput "ERROR: Pre-flight check failed: $_" "Red"
        return $false
    }
}

function Start-Application {
    Write-ColorOutput "Starting Cumpair application..." "Cyan"
    
    if ($DockerMode) {
        Write-ColorOutput "Using Docker containers..." "Blue"
        
        # Check if containers are already running
        $runningContainers = docker ps --filter "name=compair" --format "{{.Names}}" 2>$null
        
        if ($runningContainers) {
            Write-ColorOutput "INFO: Containers already running: $($runningContainers -join ', ')" "Blue"
            Write-ColorOutput "TIP: Use 'docker-compose restart' to restart" "Yellow"
        } else {
            Write-ColorOutput "Starting Docker containers..." "Blue"
            docker-compose up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "SUCCESS: Docker containers started!" "Green"
                
                # Wait a moment for services to start
                Start-Sleep -Seconds 5
                
                # Test health endpoint
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 15 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        Write-ColorOutput "SUCCESS: Application is responding!" "Green"
                    }
                } catch {
                    Write-ColorOutput "WARNING: Application may still be starting..." "Yellow"
                    Write-ColorOutput "TIP: Check logs with 'docker-compose logs -f'" "Blue"
                }
            } else {
                Write-ColorOutput "ERROR: Failed to start Docker containers" "Red"
                return $false
            }
        }
    } else {
        Write-ColorOutput "Using local Python..." "Blue"
        
        if ($DevMode) {
            Write-ColorOutput "Development mode with auto-reload enabled" "Yellow"
            python safe_start.py --dev --quick-check
        } else {
            Write-ColorOutput "Production mode" "Blue"
            python safe_start.py --quick-check
        }
    }
    
    return $true
}

function Show-PostStartupInfo {
    Write-ColorOutput ""
    Write-ColorOutput "SUCCESS: Cumpair is now running!" "Green"
    Write-ColorOutput "================================"
    Write-ColorOutput ""
    Write-ColorOutput "Key URLs:" "Cyan"
    Write-ColorOutput "  Main Application: http://localhost:8000" "White"
    Write-ColorOutput "  API Documentation: http://localhost:8000/docs" "White"
    Write-ColorOutput "  Health Check: http://localhost:8000/api/v1/health" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Useful Commands:" "Yellow"
    
    if ($DockerMode) {
        Write-ColorOutput "  View logs:      docker-compose logs -f" "White"
        Write-ColorOutput "  Stop services:  docker-compose down" "White"
        Write-ColorOutput "  Restart:        docker-compose restart" "White"
    } else {
        Write-ColorOutput "  Stop app:       Ctrl+C" "White"
        Write-ColorOutput "  Restart:        Run this script again" "White"
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "Next Steps:" "Cyan"
    Write-ColorOutput "  1. Open http://localhost:8000 in your browser" "White"
    Write-ColorOutput "  2. Try uploading an image for AI analysis" "White"
    Write-ColorOutput "  3. Test the price comparison features" "White"
    Write-ColorOutput "  4. Check the API docs for programmatic access" "White"
}

# Main execution
if ($ShowHelp) {
    Show-Help
    exit 0
}

Write-ColorOutput "Cumpair Enhanced Startup" "Cyan"
Write-ColorOutput "Current Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
Write-ColorOutput ""

# Step 1: Check prerequisites
if (-not (Test-Prerequisites)) {
    Write-ColorOutput ""
    Write-ColorOutput "ERROR: Prerequisites check failed!" "Red"
    Write-ColorOutput "Please resolve the issues above before continuing." "Yellow"
    exit 1
}

# Step 2: Run pre-flight check
if (-not (Start-PreFlightCheck)) {
    Write-ColorOutput ""
    Write-ColorOutput "ERROR: Pre-flight check failed!" "Red"
    Write-ColorOutput "Critical dependencies are missing. Please resolve before continuing." "Yellow"
    exit 1
}

# Step 3: Start the application
if (-not (Start-Application)) {
    Write-ColorOutput ""
    Write-ColorOutput "ERROR: Application startup failed!" "Red"
    exit 1
}

# Step 4: Show post-startup information
Show-PostStartupInfo
