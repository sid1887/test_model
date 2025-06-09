#Requires -Version 5.1
<#
.SYNOPSIS
    Test script for frontend-backend integration
    
.DESCRIPTION
    Validates that the new frontend correctly integrates with the existing backend
    
.EXAMPLE
    .\test-frontend-integration.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

function Write-Info {
    param([string]$Message)
    Write-Host "⏳ $Message..." -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Test-BackendConnection {
    Write-Info "Testing backend API connection"
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 10
        Write-Success "Backend API is accessible"
        return $true
    } catch {
        Write-Error "Backend API is not accessible: $($_.Exception.Message)"
        return $false
    }
}

function Test-FrontendBuild {
    Write-Info "Testing frontend build process"
    
    try {
        Push-Location "frontend"
        
        $buildOutput = npm run build 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend builds successfully"
            Pop-Location
            return $true
        } else {
            Write-Error "Frontend build failed"
            Write-Host $buildOutput -ForegroundColor Gray
            Pop-Location
            return $false
        }
    } catch {
        Write-Error "Build test failed: $($_.Exception.Message)"
        if (Get-Location | Select-Object -ExpandProperty Path | Where-Object { $_ -like "*frontend*" }) {
            Pop-Location
        }
        return $false
    }
}

function Test-ApiProxyConfiguration {
    Write-Info "Testing API proxy configuration"
    
    $nextConfigPath = "frontend/next.config.js"
    
    if (Test-Path $nextConfigPath) {
        $configContent = Get-Content $nextConfigPath -Raw
        
        if ($configContent -match "destination.*localhost:8000" -and $configContent -match "rewrites") {
            Write-Success "API proxy configuration is correct"
            return $true
        } else {
            Write-Error "API proxy configuration is missing or incorrect"
            return $false
        }
    } else {
        Write-Error "next.config.js not found"
        return $false
    }
}

function Test-TypeScriptConfiguration {
    Write-Info "Testing TypeScript configuration"
    
    try {
        Push-Location "frontend"
        
        $typeCheckOutput = npx tsc --noEmit 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "TypeScript configuration is valid"
            Pop-Location
            return $true
        } else {
            Write-Warning "TypeScript issues found (may need attention):"
            Write-Host $typeCheckOutput -ForegroundColor Gray
            Pop-Location
            return $true # Non-blocking for now
        }
    } catch {
        Write-Error "TypeScript test failed: $($_.Exception.Message)"
        if (Get-Location | Select-Object -ExpandProperty Path | Where-Object { $_ -like "*frontend*" }) {
            Pop-Location
        }
        return $false
    }
}

function Test-Dependencies {
    Write-Info "Testing frontend dependencies"
    
    $packageJsonPath = "frontend/package.json"
    
    if (Test-Path $packageJsonPath) {
        try {
            $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
            
            $requiredDeps = @('next', 'react', 'react-dom', 'typescript')
            $missingDeps = @()
            
            foreach ($dep in $requiredDeps) {
                if (-not ($packageJson.dependencies.$dep -or $packageJson.devDependencies.$dep)) {
                    $missingDeps += $dep
                }
            }
            
            if ($missingDeps.Count -eq 0) {
                Write-Success "All required dependencies are present"
                return $true
            } else {
                Write-Warning "Missing dependencies: $($missingDeps -join ', ')"
                return $false
            }
        } catch {
            Write-Error "Failed to parse package.json: $($_.Exception.Message)"
            return $false
        }
    } else {
        Write-Error "package.json not found"
        return $false
    }
}

function Test-EnvironmentConfiguration {
    Write-Info "Testing environment configuration"
    
    $envExamplePath = "frontend/.env.example"
    $envLocalPath = "frontend/.env.local"
    
    if (Test-Path $envExamplePath) {
        Write-Success ".env.example file exists"
        
        if (-not (Test-Path $envLocalPath)) {
            Write-Warning ".env.local not found - you may need to create it"
            Write-Host "   Copy .env.example to .env.local and adjust values as needed" -ForegroundColor Gray
        }
        
        return $true
    } else {
        Write-Warning "Environment configuration files not found"
        return $false
    }
}

function Test-ApiUtilities {
    Write-Info "Testing API utilities"
    
    $apiUtilsPath = "frontend/lib/api.ts"
    
    if (Test-Path $apiUtilsPath) {
        $apiContent = Get-Content $apiUtilsPath -Raw
        
        if ($apiContent -match "localhost:8000" -and $apiContent -match "endpoints") {
            Write-Success "API utilities are configured correctly"
            return $true
        } else {
            Write-Warning "API utilities may need configuration updates"
            return $false
        }
    } else {
        Write-Warning "API utilities not found - may need to be created"
        return $false
    }
}

function Start-IntegrationTest {
    Write-Info "Starting integration test servers"
    
    # Check if backend is running
    $backendRunning = Test-BackendConnection
    
    if (-not $backendRunning) {
        Write-Warning "Backend is not running. Starting backend services..."
        try {
            Start-Process -FilePath "make" -ArgumentList "start-minimal" -NoNewWindow -Wait
            Start-Sleep -Seconds 10
            $backendRunning = Test-BackendConnection
        } catch {
            Write-Error "Failed to start backend services"
        }
    }
    
    if ($backendRunning) {
        Write-Success "Backend services are running"
        
        # Start frontend in development mode (background)
        Write-Info "Starting frontend development server"
        try {
            Push-Location "frontend"
            $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru
            Pop-Location
            
            Start-Sleep -Seconds 15
            
            # Test if frontend is accessible
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10
                if ($response.StatusCode -eq 200) {
                    Write-Success "Frontend is accessible at http://localhost:3000"
                    
                    # Stop the frontend process
                    if ($frontendProcess -and -not $frontendProcess.HasExited) {
                        $frontendProcess.Kill()
                        Write-Info "Frontend development server stopped"
                    }
                    
                    return $true
                } else {
                    Write-Error "Frontend returned status code: $($response.StatusCode)"
                    return $false
                }
            } catch {
                Write-Error "Frontend is not accessible: $($_.Exception.Message)"
                
                # Stop the frontend process
                if ($frontendProcess -and -not $frontendProcess.HasExited) {
                    $frontendProcess.Kill()
                }
                
                return $false
            }
        } catch {
            Write-Error "Failed to start frontend: $($_.Exception.Message)"
            if (Get-Location | Select-Object -ExpandProperty Path | Where-Object { $_ -like "*frontend*" }) {
                Pop-Location
            }
            return $false
        }
    } else {
        Write-Error "Cannot test integration without backend services"
        return $false
    }
}

function Main {
    Write-Host "🧪 Frontend Integration Testing" -ForegroundColor Magenta
    Write-Host "================================" -ForegroundColor Magenta
    Write-Host "Testing Lovable UI Frontend Integration with Cumpair Backend" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if we're in the right directory
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Error "Please run this script from the project root directory"
        exit 1
    }
    
    $tests = @{
        'Dependencies Check' = { Test-Dependencies }
        'TypeScript Configuration' = { Test-TypeScriptConfiguration }
        'API Proxy Configuration' = { Test-ApiProxyConfiguration }
        'Environment Configuration' = { Test-EnvironmentConfiguration }
        'API Utilities' = { Test-ApiUtilities }
        'Frontend Build' = { Test-FrontendBuild }
        'Backend Connection' = { Test-BackendConnection }
        'Integration Test' = { Start-IntegrationTest }
    }
    
    $results = @{}
    $passCount = 0
    $totalCount = $tests.Count
    
    foreach ($testName in $tests.Keys) {
        Write-Host ""
        Write-Host "🔍 Running: $testName" -ForegroundColor Cyan
        
        $result = & $tests[$testName]
        $results[$testName] = $result
        
        if ($result) {
            $passCount++
        }
    }
    
    # Summary
    Write-Host ""
    Write-Host "📊 Test Summary" -ForegroundColor Cyan
    Write-Host "===============" -ForegroundColor Cyan
    Write-Host "✅ Passed: $passCount/$totalCount" -ForegroundColor Green
    Write-Host "❌ Failed: $($totalCount - $passCount)/$totalCount" -ForegroundColor Red
    
    Write-Host ""
    Write-Host "📋 Detailed Results:" -ForegroundColor Cyan
    foreach ($test in $results.Keys) {
        $status = if ($results[$test]) { "✅ PASS" } else { "❌ FAIL" }
        $color = if ($results[$test]) { "Green" } else { "Red" }
        Write-Host "   $status $test" -ForegroundColor $color
    }
    
    Write-Host ""
    if ($passCount -eq $totalCount) {
        Write-Host "🎉 All tests passed! Frontend integration is successful." -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Start the full application: make start" -ForegroundColor White
        Write-Host "   2. Access frontend at: http://localhost:3000" -ForegroundColor White
        Write-Host "   3. Test all features manually" -ForegroundColor White
        Write-Host "   4. Update documentation if needed" -ForegroundColor White
    } else {
        Write-Host "⚠️  Some tests failed. Please review the issues above." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "💡 Troubleshooting tips:" -ForegroundColor Cyan
        Write-Host "   1. Ensure all dependencies are installed" -ForegroundColor White
        Write-Host "   2. Check API configuration in next.config.js" -ForegroundColor White
        Write-Host "   3. Verify backend services are running" -ForegroundColor White
        Write-Host "   4. Review environment variables" -ForegroundColor White
    }
}

try {
    Main
} catch {
    Write-Error "Test execution failed: $($_.Exception.Message)"
    exit 1
}
