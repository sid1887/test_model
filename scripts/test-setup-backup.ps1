# Main execution function with comprehensive error handling
function Main {
    try {
        Write-Host "🚀 Make + Docker-Compose Profiles Integration Test" -ForegroundColor Magenta
        Write-Host "=================================================" -ForegroundColor Magenta
        Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
        
        # Check prerequisites first
        if (-not (Test-Prerequisites)) {
            Write-Error "Prerequisites check failed - cannot continue"
            Write-TestReport
            exit 1
        }
        
        # Run all tests in sequence
        $testResults = @{
            ShellScripts = Test-ShellScripts
            MakeCommands = Test-MakeCommands
            Profiles = Test-Profiles
            ServiceStart = if (-not $SkipServiceTest) { Test-MinimalStart } else { $true }
        }
        
        # Generate comprehensive report
        Write-TestReport
        
        # Determine overall result
        $failedTests = ($testResults.Values | Where-Object { $_ -eq $false } | Measure-Object).Count
        $allTestsPassed = $failedTests -eq 0
        
        Write-Host ""
        if ($allTestsPassed) {
            Write-Host "🎉 All tests passed! Your setup is working correctly." -ForegroundColor Green
            Write-Host ""
            Write-Info "💡 Next steps:"
            Write-Host "   make start-minimal    # Start core services" -ForegroundColor White
            Write-Host "   make start           # Start all services" -ForegroundColor White
            Write-Host "   make logs            # View service logs" -ForegroundColor White
            Write-Host "   make stop            # Stop all services" -ForegroundColor White
            Write-Host ""
            Write-Info "💡 PowerShell alternatives:"
            Write-Host "   .\scripts\start-all.ps1 -Minimal" -ForegroundColor White
            Write-Host "   .\scripts\start-all.ps1" -ForegroundColor White
            Write-Host "   docker-compose down" -ForegroundColor White
            Write-Host ""
            Write-Info "💡 Available profiles for testing:"
            Write-Host "   --profile core      # Essential services (postgres, redis, web)" -ForegroundColor White
            Write-Host "   --profile worker    # Background processing (celery, flower)" -ForegroundColor White
            Write-Host "   --profile scraper   # Data collection service" -ForegroundColor White
            Write-Host "   --profile monitor   # Monitoring stack (prometheus, grafana)" -ForegroundColor White
            
            exit 0
        } else {
            Write-Host "❌ $failedTests test(s) failed. Please review the output above." -ForegroundColor Red
            Write-Host ""
            Write-Info "💡 Common issues and solutions:"
            Write-Host "   - Ensure Docker Desktop is running and accessible" -ForegroundColor White
            Write-Host "   - Check that docker-compose.yml exists and is valid" -ForegroundColor White
            Write-Host "   - Verify Makefile exists with required targets" -ForegroundColor White
            Write-Host "   - Ensure all required files are in the correct locations" -ForegroundColor White
            Write-Host ""
            Write-Info "💡 For detailed help:"
            Write-Host "   Re-run with -VerboseOutput switch for more information" -ForegroundColor White
            
            exit 1
        }
        
    } catch {
        Write-Host ""
        Write-Host "💥 Test execution failed with an unexpected error:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        
        if ($VerboseOutput) {
            Write-Host ""
            Write-Host "Stack trace:" -ForegroundColor Red
            Write-Host $_.ScriptStackTrace -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Info "💡 Troubleshooting:"
        Write-Host "   - Try running with -VerboseOutput for more details" -ForegroundColor White
        Write-Host "   - Check that all prerequisites are properly installed" -ForegroundColor White
        Write-Host "   - Ensure you're running from the correct directory" -ForegroundColor White
        
        exit 1
    }
}#Requires -Version 5.1
<#
.SYNOPSIS
    Integration test script to verify the Make + Docker-Compose Profiles setup
    
.DESCRIPTION
    This PowerShell script tests Docker Compose profiles, Make commands, and service availability.
    It provides comprehensive validation of the development environment setup.
    
.PARAMETER SkipServiceTest
    Skip the actual service startup test (useful for CI/CD environments)
    
.PARAMETER Timeout
    Timeout in seconds for HTTP requests (default: 10)
    
.PARAMETER Verbose
    Enable verbose output for detailed logging
    
.EXAMPLE
    .\test-integration.ps1
    
.EXAMPLE
    .\test-integration.ps1 -SkipServiceTest -Verbose
#>

[CmdletBinding()]
param(
    [switch]$SkipServiceTest,
    [int]$Timeout = 10,
    [switch]$VerboseOutput
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Global variables
$Script:TestResults = @()
$Script:StartTime = Get-Date

# Enhanced color functions with proper error handling
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
    if ($VerboseOutput) { Write-Verbose $Message }
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
    $Script:TestResults += @{ Status = 'PASS'; Message = $Message; Timestamp = Get-Date }
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
    $Script:TestResults += @{ Status = 'WARN'; Message = $Message; Timestamp = Get-Date }
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
    $Script:TestResults += @{ Status = 'FAIL'; Message = $Message; Timestamp = Get-Date }
}

function Write-TestHeader {
    param([string]$TestName)
    Write-Host ""
    Write-Host "🔍 $TestName" -ForegroundColor Cyan
    Write-Host ("=" * ($TestName.Length + 3)) -ForegroundColor Cyan
}

# Enhanced endpoint testing with retry logic
function Test-Endpoint {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        [Parameter(Mandatory)]
        [string]$Name,
        [int]$TimeoutSeconds = $Timeout,
        [int]$RetryCount = 3,
        [int]$RetryDelaySeconds = 2
    )
    
    for ($i = 1; $i -le $RetryCount; $i++) {
        try {
            if ($VerboseOutput) {
                Write-Info "Attempt $i/$RetryCount: Testing $Name at $Url"
            }
            
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                Write-Success "$Name is responding (HTTP $($response.StatusCode))"
                return $true
            } else {
                Write-Warning "$Name responded with HTTP $($response.StatusCode)"
            }
        } catch [System.Net.WebException] {
            if ($i -eq $RetryCount) {
                Write-Error "$Name is not responding after $RetryCount attempts: $($_.Exception.Message)"
                return $false
            } else {
                Write-Warning "$Name not responding (attempt $i/$RetryCount), retrying in $RetryDelaySeconds seconds..."
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        } catch {
            Write-Error "$Name test failed with unexpected error: $($_.Exception.Message)"
            return $false
        }
    }
    
    return $false
}

# Enhanced Docker Compose profile testing
function Test-Profiles {
    Write-TestHeader "Docker Compose Profiles"
    
    $profiles = @('core', 'worker', 'scraper', 'monitor')
    $allProfilesValid = $true
    
    foreach ($profile in $profiles) {
        Write-Info "Validating '$profile' profile configuration..."
        try {
            $output = docker-compose --profile $profile config 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$profile profile configuration is valid"
                
                # Check if profile actually defines services
                $serviceCount = ($output | Select-String "services:" | Measure-Object).Count
                if ($serviceCount -gt 0) {
                    Write-Info "$profile profile defines services"
                } else {
                    Write-Warning "$profile profile may not define any services"
                }
            } else {
                Write-Error "$profile profile configuration failed: $output"
                $allProfilesValid = $false
            }
        } catch {
            Write-Error "$profile profile test failed: $($_.Exception.Message)"
            $allProfilesValid = $false
        }
    }
    
    # Test multiple profiles combination
    Write-Info "Testing multiple profiles combination..."
    try {
        $combinedProfiles = $profiles -join ' --profile '
        $output = Invoke-Expression "docker-compose --profile $combinedProfiles config" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Multiple profiles configuration is valid"
        } else {
            Write-Error "Multiple profiles configuration failed: $output"
            $allProfilesValid = $false
        }
    } catch {
        Write-Error "Multiple profiles test failed: $($_.Exception.Message)"
        $allProfilesValid = $false
    }
    
    # Test profile-specific service filtering
    Write-Info "Testing profile service filtering..."
    try {
        $coreServices = docker-compose --profile core config --services 2>&1
        $allServices = docker-compose config --services 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $coreCount = ($coreServices | Measure-Object -Line).Lines
            $totalCount = ($allServices | Measure-Object -Line).Lines
            Write-Success "Profile filtering works: core has $coreCount services, total has $totalCount services"
        }
    } catch {
        Write-Warning "Could not test service filtering: $($_.Exception.Message)"
    }
    
    return $allProfilesValid
}

# Enhanced service startup testing
function Test-MinimalStart {
    Write-TestHeader "Minimal Service Startup"
    
    if ($SkipServiceTest) {
        Write-Warning "Skipping service startup test as requested"
        return $true
    }
    
    try {
        # Cleanup any existing services
        Write-Info "Cleaning up any existing services..."
        docker-compose down --remove-orphans 2>&1 | Out-Null
        
        # Start minimal services
        Write-Info "Starting minimal services..."
        $startOutput = make start-minimal 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start minimal services: $startOutput"
            return $false
        }
        
        Write-Success "Services started successfully"
        
        # Wait for services to be ready
        Write-Info "Waiting for services to be ready..."
        Start-Sleep -Seconds 15
        
        # Test core endpoints
        $endpointTests = @(
            @{ Url = "http://localhost:8000/health"; Name = "Health Check" },
            @{ Url = "http://localhost:8000/api/v1/health"; Name = "API Health" },
            @{ Url = "http://localhost:8000/docs"; Name = "API Documentation" }
        )
        
        $allEndpointsHealthy = $true
        foreach ($test in $endpointTests) {
            if (-not (Test-Endpoint -Url $test.Url -Name $test.Name)) {
                $allEndpointsHealthy = $false
            }
        }
        
        # Test Docker service status
        Write-Info "Checking Docker service status..."
        $runningServices = docker-compose ps --services --filter "status=running" 2>&1
        if ($runningServices) {
            Write-Success "Running services: $($runningServices -join ', ')"
        } else {
            Write-Warning "No services appear to be running"
        }
        
        return $allEndpointsHealthy
        
    } catch {
        Write-Error "Service startup test failed: $($_.Exception.Message)"
        return $false
    } finally {
        # Always cleanup
        Write-Info "Cleaning up test services..."
        try {
            make stop 2>&1 | Out-Null
            Write-Info "Services stopped successfully"
        } catch {
            Write-Warning "Could not stop services cleanly: $($_.Exception.Message)"
        }
    }
}

# Enhanced Make command testing
function Test-MakeCommands {
    Write-TestHeader "Make Commands"
    
    # Check if Makefile exists
    if (-not (Test-Path "Makefile")) {
        Write-Error "Makefile not found in current directory"
        return $false
    }
    
    $makefileContent = Get-Content Makefile -Raw -ErrorAction SilentlyContinue
    if (-not $makefileContent) {
        Write-Error "Could not read Makefile content"
        return $false
    }
    
    # Test help command
    Write-Info "Testing 'make help' command..."
    try {
        $helpOutput = make help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "make help works"
            if ($VerboseOutput) {
                Write-Info "Help output preview: $($helpOutput[0..2] -join '; ')"
            }
        } else {
            Write-Error "make help failed: $helpOutput"
            return $false
        }
    } catch {
        Write-Error "make help failed: $($_.Exception.Message)"
        return $false
    }
    
    # Test status command
    Write-Info "Testing 'make status' command..."
    try {
        $statusOutput = make status 2>&1
        Write-Success "make status works"
        if ($VerboseOutput) {
            Write-Info "Status: $statusOutput"
        }
    } catch {
        Write-Warning "make status failed (this may be normal if no services are running)"
    }
    
    # Check for required targets in Makefile
    $requiredTargets = @('start', 'stop', 'logs', 'start-minimal')
    $missingTargets = @()
    
    foreach ($target in $requiredTargets) {
        if ($makefileContent -match "^$target\s*:") {
            Write-Success "make $target target exists"
        } else {
            Write-Error "make $target target not found"
            $missingTargets += $target
        }
    }
    
    # Check for optional but recommended targets
    $optionalTargets = @('clean', 'build', 'test', 'restart')
    foreach ($target in $optionalTargets) {
        if ($makefileContent -match "^$target\s*:") {
            Write-Success "make $target target exists (optional)"
        } else {
            Write-Info "make $target target not found (optional)"
        }
    }
    
    return $missingTargets.Count -eq 0
}

# Enhanced shell script testing
function Test-ShellScripts {
    Write-TestHeader "Shell Scripts"
    
    $scriptTests = @(
        @{ Path = "scripts/start-all.sh"; Type = "Bash"; Required = $false },
        @{ Path = "scripts/start-all.ps1"; Type = "PowerShell"; Required = $false },
        @{ Path = "scripts/setup.sh"; Type = "Bash"; Required = $false },
        @{ Path = "scripts/cleanup.ps1"; Type = "PowerShell"; Required = $false }
    )
    
    $allScriptsValid = $true
    
    foreach ($script in $scriptTests) {
        if (Test-Path $script.Path) {
            Write-Success "$($script.Path) exists"
            
            if ($script.Type -eq "PowerShell") {
                try {
                    $scriptContent = Get-Content $script.Path -Raw
                    $null = [System.Management.Automation.PSParser]::Tokenize($scriptContent, [ref]$null)
                    Write-Success "$($script.Path) syntax is valid"
                } catch {
                    Write-Error "$($script.Path) syntax error: $($_.Exception.Message)"
                    if ($script.Required) { $allScriptsValid = $false }
                }
            } elseif ($script.Type -eq "Bash") {
                # Basic bash syntax check (if bash is available)
                try {
                    if (Get-Command bash -ErrorAction SilentlyContinue) {
                        $bashCheck = bash -n $script.Path 2>&1
                        if ($LASTEXITCODE -eq 0) {
                            Write-Success "$($script.Path) syntax is valid"
                        } else {
                            Write-Warning "$($script.Path) may have syntax issues: $bashCheck"
                        }
                    } else {
                        Write-Info "$($script.Path) exists (bash not available for syntax check)"
                    }
                } catch {
                    Write-Warning "Could not validate $($script.Path): $($_.Exception.Message)"
                }
            }
        } else {
            if ($script.Required) {
                Write-Error "$($script.Path) not found (required)"
                $allScriptsValid = $false
            } else {
                Write-Info "$($script.Path) not found (optional)"
            }
        }
    }
    
    return $allScriptsValid
}

# Enhanced prerequisites checking
function Test-Prerequisites {
    Write-TestHeader "Prerequisites"
    
    $prerequisites = @(
        @{ Command = "docker"; Name = "Docker"; Required = $true; VersionFlag = "--version" },
        @{ Command = "docker-compose"; Name = "Docker Compose"; Required = $true; VersionFlag = "--version" },
        @{ Command = "make"; Name = "Make"; Required = $true; VersionFlag = "--version" },
        @{ Command = "git"; Name = "Git"; Required = $false; VersionFlag = "--version" },
        @{ Command = "curl"; Name = "cURL"; Required = $false; VersionFlag = "--version" }
    )
    
    $allPrerequisitesMet = $true
    
    foreach ($prereq in $prerequisites) {
        try {
            $versionOutput = & $prereq.Command $prereq.VersionFlag 2>&1
            if ($LASTEXITCODE -eq 0) {
                $version = ($versionOutput | Select-Object -First 1) -replace '.*?(\d+\.\d+[\.\d+]*)', '$1'
                Write-Success "$($prereq.Name) is available (version: $version)"
            } else {
                throw "Command failed with exit code $LASTEXITCODE"
            }
        } catch {
            if ($prereq.Required) {
                Write-Error "$($prereq.Name) is not installed or not in PATH"
                
                # Provide installation hints
                switch ($prereq.Command) {
                    "docker" { Write-Info "Install from: https://docs.docker.com/desktop/windows/" }
                    "docker-compose" { Write-Info "Usually included with Docker Desktop" }
                    "make" { Write-Info "Install via: choco install make OR winget install GnuWin32.Make" }
                }
                
                $allPrerequisitesMet = $false
            } else {
                Write-Info "$($prereq.Name) is not available (optional)"
            }
        }
    }
    
    # Check Docker daemon status
    try {
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker daemon is running"
        } else {
            Write-Error "Docker daemon is not running"
            $allPrerequisitesMet = $false
        }
    } catch {
        Write-Error "Could not connect to Docker daemon"
        $allPrerequisitesMet = $false
    }
    
    return $allPrerequisitesMet
}

# Generate test report
function Write-TestReport {
    Write-TestHeader "Test Report"
    
    $passCount = ($Script:TestResults | Where-Object { $_.Status -eq 'PASS' } | Measure-Object).Count
    $failCount = ($Script:TestResults | Where-Object { $_.Status -eq 'FAIL' } | Measure-Object).Count
    $warnCount = ($Script:TestResults | Where-Object { $_.Status -eq 'WARN' } | Measure-Object).Count
    $totalCount = $Script:TestResults.Count
    $duration = (Get-Date) - $Script:StartTime
    
    Write-Host ""
    Write-Host "📊 Test Summary:" -ForegroundColor Cyan
    Write-Host "   ✅ Passed: $passCount" -ForegroundColor Green
    Write-Host "   ❌ Failed: $failCount" -ForegroundColor Red
    Write-Host "   ⚠️  Warnings: $warnCount" -ForegroundColor Yellow
    Write-Host "   📋 Total: $totalCount" -ForegroundColor White
    Write-Host "   ⏱️  Duration: $($duration.TotalSeconds.ToString('F2')) seconds" -ForegroundColor White
    
    if ($VerboseOutput -and $Script:TestResults.Count -gt 0) {
        Write-Host ""
        Write-Host "📝 Detailed Results:" -ForegroundColor Cyan
        $Script:TestResults | ForEach-Object {
            $icon = switch ($_.Status) {
                'PASS' { '✅' }
                'FAIL' { '❌' }
                'WARN' { '⚠️' }
                default { 'ℹ️' }
            }
            Write-Host "   $icon $($_.Message)" -ForegroundColor White
        }
    }
}

# Main execution function with comprehensive error handling
function Main {
    try {
        Write-Host "🚀 Make + Docker-Compose Profiles Integration Test" -ForegroundColor Magenta
        Write-Host "=================================================" -ForegroundColor Magenta
        Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
        
        # Run all tests
        $testResults = @{
            Prerequisites = Test-Prerequisites
            ShellScripts = Test-ShellScripts
            MakeCommands = Test-MakeCommands
            Profiles = Test-Profiles
            ServiceStart = if (-not $SkipServiceTest) { Test-MinimalStart } else { $true }
        }
        
        # Generate report
        Write-TestReport
        
        # Determine overall result
        $allTestsPassed = ($testResults.Values | Where-Object { $_ -eq $false } | Measure-Object).Count -eq 0
        
        Write-Host ""
        if ($allTestsPassed) {
            Write-Host "🎉 All tests passed! Your setup is working correctly." -ForegroundColor Green
            Write-Host ""
            Write-Info "💡 Next steps:"
            Write-Host "   make start-minimal    # Start core services"
            Write-Host "   make start           # Start all services"
            Write-Host "   make logs            # View service logs"
            Write-Host "   make stop            # Stop all services"
            Write-Host ""
            Write-Info "💡 PowerShell alternatives:"
            Write-Host "   .\scripts\start-all.ps1 -Minimal"
            Write-Host "   .\scripts\start-all.ps1"
            Write-Host "   docker-compose down"
            
            exit 0
        } else {
            Write-Host "❌ Some tests failed. Please review the output above." -ForegroundColor Red
            Write-Host ""
            Write-Info "💡 Common issues:"
            Write-Host "   - Ensure Docker Desktop is running"
            Write-Host "   - Check that all required files exist"
            Write-Host "   - Verify Makefile syntax"
            Write-Host "   - Ensure docker-compose.yml is valid"
            
            exit 1
        }
        
    } catch {
        Write-Error "Test execution failed: $($_.Exception.Message)"
        Write-Host "Stack trace:" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
        exit 1
    }
}

# Execute main function
Main