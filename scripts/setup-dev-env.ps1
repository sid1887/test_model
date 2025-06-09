#Requires -Version 5.1
<#
.SYNOPSIS
    Development environment setup script for Windows
    
.DESCRIPTION
    Installs and configures all necessary tools for code quality
    
.EXAMPLE
    .\setup-dev-env.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

function Invoke-Command {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Info $Description
    try {
        $output = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$Description completed successfully"
            return $true
        } else {
            Write-Error "$Description failed with exit code $LASTEXITCODE"
            if ($output) {
                Write-Host "   Output: $output" -ForegroundColor Gray
            }
            return $false
        }
    } catch {
        Write-Error "$Description failed: $($_.Exception.Message)"
        return $false
    }
}

function Main {
    Write-Host "🚀 Setting up development environment for code quality..." -ForegroundColor Magenta
    Write-Host "=================================================" -ForegroundColor Magenta
    
    # Check if we're in the right directory
    if (-not (Test-Path "pyproject.toml")) {
        Write-Error "Please run this script from the project root directory"
        exit 1
    }
    
    # Install Python development dependencies
    $pythonDeps = @("black", "flake8", "isort", "pre-commit", "mypy")
    
    foreach ($dep in $pythonDeps) {
        if (-not (Invoke-Command "pip install $dep" "Installing $dep")) {
            Write-Warning "Failed to install $dep, continuing..."
        }
    }
    
    # Install pre-commit hooks
    if (-not (Invoke-Command "pre-commit install" "Installing pre-commit hooks")) {
        Write-Warning "Failed to install pre-commit hooks"
    }
    
    # Check if Node.js dependencies are installed in frontend
    if (Test-Path "frontend/package.json") {
        Push-Location "frontend"
        if (-not (Invoke-Command "npm install" "Installing frontend dependencies")) {
            Write-Warning "Failed to install frontend dependencies"
        }
        Pop-Location
    }
    
    # Check if Node.js dependencies are installed in scraper
    if (Test-Path "scraper/package.json") {
        Push-Location "scraper"
        if (-not (Invoke-Command "npm install" "Installing scraper dependencies")) {
            Write-Warning "Failed to install scraper dependencies"
        }
        Pop-Location
    }
    
    Write-Host ""
    Write-Host "🎉 Development environment setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Configure your IDE to use the .editorconfig file" -ForegroundColor White
    Write-Host "   2. Enable format-on-save in your editor" -ForegroundColor White
    Write-Host "   3. Run 'pre-commit run --all-files' to check all files" -ForegroundColor White
    Write-Host "   4. The pre-commit hooks will now run automatically on each commit" -ForegroundColor White
    
    Write-Host ""
    Write-Host "💡 Available commands:" -ForegroundColor Cyan
    Write-Host "   black .                    # Format Python code" -ForegroundColor White
    Write-Host "   flake8 .                   # Lint Python code" -ForegroundColor White
    Write-Host "   npx eslint . --fix         # Fix JavaScript/TypeScript issues" -ForegroundColor White
    Write-Host "   npx prettier . --write     # Format frontend code" -ForegroundColor White
    Write-Host "   pre-commit run --all-files # Run all quality checks" -ForegroundColor White
}

try {
    Main
} catch {
    Write-Error "Setup failed with an unexpected error: $($_.Exception.Message)"
    exit 1
}
