# Pre-flight Dependency Check for Cumpair AI System
# PowerShell wrapper for the Python pre-flight check

param(
    [switch]$Force,
    [switch]$SkipOptional,
    [switch]$DockerMode,
    [switch]$Verbose
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

function Test-PythonAvailable {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Python is available: $pythonVersion" "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Python is not available in PATH" "Red"
        return $false
    }
    return $false
}

function Test-DockerAvailable {
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker is available: $dockerVersion" "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Docker is not available in PATH" "Red"
        return $false
    }
    return $false
}

function Install-PreFlightScript {
    $scriptPath = "pre_flight_check.py"
    
    if (-not (Test-Path $scriptPath)) {
        Write-ColorOutput "❌ Pre-flight check script not found: $scriptPath" "Red"
        Write-ColorOutput "Please ensure pre_flight_check.py is in the current directory" "Yellow"
        return $false
    }
    
    return $true
}

function Start-PreFlightCheck {
    param(
        [bool]$InDocker = $false
    )
    
    $arguments = @()
    
    if ($Verbose) {
        $arguments += "--verbose"
    }
    
    if ($SkipOptional) {
        $arguments += "--skip-optional"
    }
    
    if ($Force) {
        $arguments += "--force"
    }
    
    try {
        if ($InDocker) {
            Write-ColorOutput "🐳 Running pre-flight check in Docker container..." "Cyan"
            
            # Run the pre-flight check inside the existing container
            $result = docker exec compair_web python pre_flight_check.py $arguments
            $exitCode = $LASTEXITCODE
        } else {
            Write-ColorOutput "🚀 Running pre-flight check locally..." "Cyan"
            
            # Run locally
            python pre_flight_check.py $arguments
            $exitCode = $LASTEXITCODE
        }
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "✅ Pre-flight check completed successfully!" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Pre-flight check failed!" "Red"
            return $false
        }
        
    } catch {
        Write-ColorOutput "💥 Error running pre-flight check: $_" "Red"
        return $false
    }
}

function Show-Help {
    Write-ColorOutput "🔍 Cumpair Pre-flight Dependency Check" "Cyan"
    Write-ColorOutput "=" * 50 "Blue"
    Write-ColorOutput ""
    Write-ColorOutput "This script checks and installs missing Python packages before starting the application." "White"
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" "Yellow"
    Write-ColorOutput "  .\pre-flight-check.ps1 [-Force] [-SkipOptional] [-DockerMode] [-Verbose]" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Parameters:" "Yellow"
    Write-ColorOutput "  -Force        Force reinstallation of packages" "White"
    Write-ColorOutput "  -SkipOptional Skip optional packages" "White"
    Write-ColorOutput "  -DockerMode   Run check inside Docker container" "White"
    Write-ColorOutput "  -Verbose      Enable verbose output" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" "Yellow"
    Write-ColorOutput "  .\pre-flight-check.ps1                    # Basic check" "White"
    Write-ColorOutput "  .\pre-flight-check.ps1 -DockerMode        # Check in Docker" "White"
    Write-ColorOutput "  .\pre-flight-check.ps1 -Force -Verbose    # Force reinstall with verbose output" "White"
}

function Main {
    Write-ColorOutput "🔍 Cumpair Pre-flight Dependency Check" "Cyan"
    Write-ColorOutput "=" * 50 "Blue"
    
    # Check if help is requested
    if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "help") {
        Show-Help
        return
    }
    
    # Verify pre-flight script exists
    if (-not (Install-PreFlightScript)) {
        exit 1
    }
    
    # Determine execution mode
    if ($DockerMode) {
        if (-not (Test-DockerAvailable)) {
            Write-ColorOutput "❌ Docker mode requested but Docker is not available" "Red"
            exit 1
        }
        
        # Check if container is running
        $containerStatus = docker ps --filter "name=compair_web" --format "{{.Status}}" 2>$null
        if (-not $containerStatus) {
            Write-ColorOutput "❌ Cumpair container is not running. Please start it first with:" "Red"
            Write-ColorOutput "   docker-compose up -d" "Yellow"
            exit 1
        }
        
        $success = Start-PreFlightCheck -InDocker $true
    } else {
        if (-not (Test-PythonAvailable)) {
            Write-ColorOutput "❌ Python is not available. Please install Python 3.8+ or use Docker mode" "Red"
            exit 1
        }
        
        $success = Start-PreFlightCheck -InDocker $false
    }
    
    if ($success) {
        Write-ColorOutput ""
        Write-ColorOutput "🎉 Ready to start Cumpair! You can now run:" "Green"
        if ($DockerMode) {
            Write-ColorOutput "   docker-compose up" "Cyan"
        } else {
            Write-ColorOutput "   python main.py" "Cyan"
            Write-ColorOutput "   or" "White"
            Write-ColorOutput "   uvicorn main:app --host 0.0.0.0 --port 8000" "Cyan"
        }
        exit 0
    } else {
        Write-ColorOutput ""
        Write-ColorOutput "❌ Please resolve the dependency issues before starting the application." "Red"
        Write-ColorOutput "Check the error messages above and the emergency_requirements.txt file if created." "Yellow"
        exit 1
    }
}

# Run main function
Main
