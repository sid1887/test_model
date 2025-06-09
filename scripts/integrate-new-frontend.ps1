#Requires -Version 5.1
<#
.SYNOPSIS
    Integration script for new Lovable UI frontend
    
.DESCRIPTION
    This script helps integrate the new frontend from the PR and connects it with the existing backend
    
.PARAMETER SourcePath
    Path to the new frontend folder (from PR)
    
.PARAMETER BackupCurrent
    Whether to backup the current frontend before replacement
    
.EXAMPLE
    .\integrate-new-frontend.ps1 -SourcePath ".\new-frontend" -BackupCurrent
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    
    [switch]$BackupCurrent = $true
)

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

function Backup-CurrentFrontend {
    $backupPath = "frontend_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    Write-Info "Creating backup of current frontend"
    try {
        if (Test-Path "frontend") {
            Copy-Item -Path "frontend" -Destination $backupPath -Recurse -Force
            Write-Success "Current frontend backed up to $backupPath"
            return $backupPath
        } else {
            Write-Warning "No existing frontend folder found"
            return $null
        }
    } catch {
        Write-Error "Failed to backup current frontend: $($_.Exception.Message)"
        throw
    }
}

function Copy-NewFrontend {
    param([string]$Source)
    
    Write-Info "Copying new frontend from $Source"
    try {
        if (-not (Test-Path $Source)) {
            throw "Source path $Source does not exist"
        }
        
        # Remove existing frontend if it exists
        if (Test-Path "frontend") {
            Remove-Item -Path "frontend" -Recurse -Force
        }
        
        # Copy new frontend
        Copy-Item -Path $Source -Destination "frontend" -Recurse -Force
        Write-Success "New frontend copied successfully"
    } catch {
        Write-Error "Failed to copy new frontend: $($_.Exception.Message)"
        throw
    }
}

function Update-NextConfig {
    $nextConfigPath = "frontend/next.config.js"
    
    Write-Info "Updating Next.js configuration for backend integration"
    
    $nextConfigContent = @"
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: true,
  },
  images: {
    domains: ['localhost', '127.0.0.1'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/**',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
"@

    try {
        Set-Content -Path $nextConfigPath -Value $nextConfigContent -Encoding UTF8
        Write-Success "Next.js configuration updated"
    } catch {
        Write-Error "Failed to update Next.js configuration: $($_.Exception.Message)"
        throw
    }
}

function Update-PackageJson {
    $packageJsonPath = "frontend/package.json"
    
    Write-Info "Updating package.json for project integration"
    
    try {
        if (Test-Path $packageJsonPath) {
            $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
            
            # Update project details
            $packageJson.name = "cumpair-frontend-lovable"
            $packageJson.description = "Cumpair Price Comparison Frontend - Lovable UI Framework"
            $packageJson.version = "2.0.0"
            
            # Ensure required scripts exist
            if (-not $packageJson.scripts) {
                $packageJson.scripts = @{}
            }
            
            $packageJson.scripts.dev = "next dev"
            $packageJson.scripts.build = "next build"
            $packageJson.scripts.start = "next start"
            $packageJson.scripts.lint = "next lint"
            $packageJson.scripts."type-check" = "tsc --noEmit"
            
            # Convert back to JSON and save
            $packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath -Encoding UTF8
            Write-Success "package.json updated"
        } else {
            Write-Warning "package.json not found in new frontend"
        }
    } catch {
        Write-Error "Failed to update package.json: $($_.Exception.Message)"
        throw
    }
}

function Create-ApiUtils {
    $apiUtilsPath = "frontend/lib/api.ts"
    $libDir = "frontend/lib"
    
    Write-Info "Creating API utility functions"
    
    # Ensure lib directory exists
    if (-not (Test-Path $libDir)) {
        New-Item -Path $libDir -ItemType Directory -Force | Out-Null
    }
    
    $apiUtilsContent = @"
// API utilities for connecting to Cumpair backend
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Product search
  searchProducts: '/api/products/search',
  uploadProduct: '/api/products/upload',
  getProduct: (id: string) => `/api/products/${id}`,
  
  // Price comparison
  comparePrice: '/api/comparison/search',
  refreshPrices: (id: string) => `/api/comparison/${id}/refresh`,
  
  // Analysis
  analyzeProduct: '/api/analysis/create',
  getAnalysis: (id: string) => `/api/analysis/${id}`,
  
  // Health check
  health: '/api/health',
};

// Helper functions
export const searchProducts = async (query: string, file?: File) => {
  const formData = new FormData();
  formData.append('query', query);
  if (file) {
    formData.append('image', file);
  }
  
  return api.post(endpoints.searchProducts, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const comparePrices = async (productId: string, sites: string[] = ['amazon', 'walmart', 'ebay']) => {
  return api.post(endpoints.comparePrice, {
    product_id: productId,
    sites,
  });
};

export const uploadProductImage = async (file: File) => {
  const formData = new FormData();
  formData.append('image', file);
  
  return api.post(endpoints.uploadProduct, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};
"@

    try {
        Set-Content -Path $apiUtilsPath -Value $apiUtilsContent -Encoding UTF8
        Write-Success "API utilities created"
    } catch {
        Write-Error "Failed to create API utilities: $($_.Exception.Message)"
        throw
    }
}

function Install-Dependencies {
    Write-Info "Installing frontend dependencies"
    
    try {
        Push-Location "frontend"
        
        # Install dependencies
        $installOutput = npm install 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencies installed successfully"
        } else {
            Write-Warning "Some issues during dependency installation"
            Write-Host $installOutput -ForegroundColor Gray
        }
        
        Pop-Location
    } catch {
        Write-Error "Failed to install dependencies: $($_.Exception.Message)"
        if (Get-Location | Select-Object -ExpandProperty Path | Where-Object { $_ -like "*frontend*" }) {
            Pop-Location
        }
        throw
    }
}

function Test-Integration {
    Write-Info "Testing frontend integration"
    
    try {
        Push-Location "frontend"
        
        # Type check
        Write-Info "Running TypeScript type check"
        $typeCheckOutput = npx tsc --noEmit 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "TypeScript type check passed"
        } else {
            Write-Warning "TypeScript issues found:"
            Write-Host $typeCheckOutput -ForegroundColor Gray
        }
        
        # Try to build
        Write-Info "Testing build process"
        $buildOutput = npm run build 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Build test successful"
        } else {
            Write-Warning "Build issues found:"
            Write-Host $buildOutput -ForegroundColor Gray
        }
        
        Pop-Location
    } catch {
        Write-Error "Integration test failed: $($_.Exception.Message)"
        if (Get-Location | Select-Object -ExpandProperty Path | Where-Object { $_ -like "*frontend*" }) {
            Pop-Location
        }
        throw
    }
}

function Main {
    Write-Host "🚀 Cumpair Frontend Integration" -ForegroundColor Magenta
    Write-Host "=================================" -ForegroundColor Magenta
    Write-Host "Integrating Lovable UI Frontend with Cumpair Backend" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if we're in the right directory
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Error "Please run this script from the project root directory"
        exit 1
    }
    
    $backupPath = $null
    
    try {
        # Step 1: Backup current frontend
        if ($BackupCurrent) {
            $backupPath = Backup-CurrentFrontend
        }
        
        # Step 2: Copy new frontend
        Copy-NewFrontend -Source $SourcePath
        
        # Step 3: Update configuration files
        Update-NextConfig
        Update-PackageJson
        
        # Step 4: Create API utilities
        Create-ApiUtils
        
        # Step 5: Install dependencies
        Install-Dependencies
        
        # Step 6: Test integration
        Test-Integration
        
        Write-Host ""
        Write-Host "🎉 Frontend integration completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Review the integrated frontend code" -ForegroundColor White
        Write-Host "   2. Test the application: cd frontend && npm run dev" -ForegroundColor White
        Write-Host "   3. Verify API connectivity with backend" -ForegroundColor White
        Write-Host "   4. Update any custom components as needed" -ForegroundColor White
        Write-Host "   5. Run full integration tests" -ForegroundColor White
        
        if ($backupPath) {
            Write-Host ""
            Write-Host "💾 Backup location: $backupPath" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host ""
        Write-Host "💥 Integration failed: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($backupPath -and (Test-Path $backupPath)) {
            Write-Host ""
            Write-Host "🔄 Restoring from backup..." -ForegroundColor Yellow
            try {
                if (Test-Path "frontend") {
                    Remove-Item -Path "frontend" -Recurse -Force
                }
                Copy-Item -Path $backupPath -Destination "frontend" -Recurse -Force
                Write-Success "Frontend restored from backup"
            } catch {
                Write-Error "Failed to restore backup: $($_.Exception.Message)"
                Write-Warning "Please manually restore from: $backupPath"
            }
        }
        
        exit 1
    }
}

try {
    Main
} catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    exit 1
}
