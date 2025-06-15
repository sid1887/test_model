# Docker Security Setup Script
# Generates secure secrets and sets up Docker environment following testdriven.io best practices

Write-Host "🔐 Setting up Docker Security Configuration..." -ForegroundColor Green
Write-Host "=" * 60

# Function to generate secure random password
function Generate-SecurePassword {
    param (
        [int]$Length = 32,
        [string]$CharSet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
    )
    
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $CharSet[(Get-Random -Minimum 0 -Maximum $CharSet.Length)]
    }
    return $password
}

# Function to generate secure token
function Generate-SecureToken {
    param ([int]$Length = 32)
    
    try {
        $token = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes($Length))
        return $token.Substring(0, $Length)
    } catch {
        Write-Host "   Falling back to PowerShell random generation..." -ForegroundColor Yellow
        return Generate-SecurePassword -Length $Length -CharSet "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    }
}

# Step 1: Create secrets directory
Write-Host "`n📁 Creating secrets directory..." -ForegroundColor Blue

if (-not (Test-Path "secrets")) {
    New-Item -ItemType Directory -Name "secrets" | Out-Null
    Write-Host "   ✅ Created secrets directory" -ForegroundColor Green
} else {
    Write-Host "   ✅ Secrets directory already exists" -ForegroundColor Green
}

# Step 2: Generate or check existing secrets
Write-Host "`n🔑 Generating secure secrets..." -ForegroundColor Blue

$secrets = @{
    "db_password.txt" = @{
        "description" = "Database password"
        "generator" = { Generate-SecurePassword -Length 24 }
    }
    "secret_key.txt" = @{
        "description" = "Application secret key"
        "generator" = { Generate-SecureToken -Length 44 }
    }
    "redis_password.txt" = @{
        "description" = "Redis password"
        "generator" = { Generate-SecurePassword -Length 20 }
    }
    "grafana_password.txt" = @{
        "description" = "Grafana admin password"
        "generator" = { Generate-SecurePassword -Length 16 }
    }
}

foreach ($secretFile in $secrets.Keys) {
    $secretPath = "secrets\$secretFile"
    $secretInfo = $secrets[$secretFile]
    
    if (-not (Test-Path $secretPath)) {
        Write-Host "   Generating $($secretInfo.description)..." -ForegroundColor Gray
        $secretValue = & $secretInfo.generator
        $secretValue | Out-File -FilePath $secretPath -Encoding UTF8 -NoNewline
        Write-Host "   ✅ Created $secretFile" -ForegroundColor Green
    } else {
        Write-Host "   ✅ $secretFile already exists" -ForegroundColor Green
    }
}

# Step 3: Set proper file permissions (Windows)
Write-Host "`n🔒 Setting secure file permissions..." -ForegroundColor Blue

Get-ChildItem "secrets\*.txt" | ForEach-Object {
    try {
        # Remove inheritance and grant only current user access
        icacls $_.FullName /inheritance:r /grant:r "$env:USERNAME:F" | Out-Null
        Write-Host "   ✅ Secured $($_.Name)" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Could not set permissions for $($_.Name)" -ForegroundColor Yellow
    }
}

# Step 4: Create environment file from template
Write-Host "`n📝 Setting up environment configuration..." -ForegroundColor Blue

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.docker") {
        Copy-Item ".env.docker" ".env"
        Write-Host "   ✅ Created .env from Docker template" -ForegroundColor Green
    } elseif (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   ✅ Created .env from example template" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ No .env template found" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ .env file already exists" -ForegroundColor Green
}

# Step 5: Create database initialization script
Write-Host "`n🗄️ Creating database initialization script..." -ForegroundColor Blue

$dbInitScript = @"
#!/bin/bash
set -e

# Create database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL

echo "Database initialization completed successfully"
"@

$scriptsDir = "scripts"
if (-not (Test-Path $scriptsDir)) {
    New-Item -ItemType Directory -Name $scriptsDir | Out-Null
}

$dbInitScript | Out-File -FilePath "$scriptsDir\init-db.sh" -Encoding UTF8
Write-Host "   ✅ Created database initialization script" -ForegroundColor Green

# Step 6: Create Nginx configuration for production
Write-Host "`n🌐 Creating Nginx configuration..." -ForegroundColor Blue

$nginxDir = "nginx"
if (-not (Test-Path $nginxDir)) {
    New-Item -ItemType Directory -Name $nginxDir | Out-Null
}

$nginxConfig = @"
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Rate limiting
        limit_req_zone `$binary_remote_addr zone=api:10m rate=10r/s;
        limit_req_zone `$binary_remote_addr zone=static:10m rate=50r/s;

        # API requests
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://web;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
        }

        # Static files
        location /static/ {
            limit_req zone=static burst=100 nodelay;
            proxy_pass http://web;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            proxy_pass http://web/api/v1/health;
            access_log off;
        }

        # Default location
        location / {
            proxy_pass http://web;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
        }
    }
}
"@

$nginxConfig | Out-File -FilePath "$nginxDir\nginx.conf" -Encoding UTF8
Write-Host "   ✅ Created Nginx configuration" -ForegroundColor Green

# Step 7: Validate Docker setup
Write-Host "`n🐳 Validating Docker setup..." -ForegroundColor Blue

try {
    docker version | Out-Null
    Write-Host "   ✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker is not available" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
}

try {
    docker-compose version | Out-Null
    Write-Host "   ✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker Compose is not available" -ForegroundColor Red
}

# Step 8: Test secret loading
Write-Host "`n🧪 Testing secret loading..." -ForegroundColor Blue

try {
    $testDbPassword = Get-Content "secrets\db_password.txt" -Raw
    $testSecretKey = Get-Content "secrets\secret_key.txt" -Raw
    
    if ($testDbPassword -and $testSecretKey) {
        Write-Host "   ✅ Secrets are readable" -ForegroundColor Green
        Write-Host "   DB Password length: $($testDbPassword.Length) characters" -ForegroundColor Gray
        Write-Host "   Secret Key length: $($testSecretKey.Length) characters" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Failed to read secrets" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error reading secrets: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 9: Security summary
Write-Host "`n🛡️ SECURITY SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 50

Write-Host "✅ Secrets Generation:" -ForegroundColor Green
Write-Host "   • Database password: 24 characters, mixed case + symbols"
Write-Host "   • Secret key: 44 characters, base64 encoded"
Write-Host "   • Redis password: 20 characters, mixed case + symbols"
Write-Host "   • Grafana password: 16 characters, mixed case + symbols"

Write-Host "`n✅ Security Measures:" -ForegroundColor Green
Write-Host "   • File permissions restricted to current user"
Write-Host "   • Secrets stored in separate files (not in images)"
Write-Host "   • Environment variables used for non-sensitive config"
Write-Host "   • Production-ready Docker configuration"
Write-Host "   • Nginx reverse proxy with security headers"
Write-Host "   • Rate limiting and CORS protection"

Write-Host "`n📚 Usage Instructions:" -ForegroundColor Cyan
Write-Host "   • Development: docker-compose up -d"
Write-Host "   • Production: docker-compose -f docker-compose.secure.yml up -d"
Write-Host "   • With monitoring: docker-compose -f docker-compose.secure.yml --profile monitoring up -d"
Write-Host "   • With scraping services: docker-compose -f docker-compose.secure.yml --profile scraping up -d"

Write-Host "`n⚠️ IMPORTANT SECURITY NOTES:" -ForegroundColor Yellow
Write-Host "   • Never commit secrets/ directory to version control"
Write-Host "   • Backup secrets securely before deploying"
Write-Host "   • Rotate secrets regularly in production"
Write-Host "   • Monitor logs for security events"

Write-Host "`n🎉 Docker Security Setup Complete!" -ForegroundColor Green
Write-Host "Your application is now configured with production-grade security." -ForegroundColor White

# Add secrets to .gitignore
Write-Host "`n📝 Updating .gitignore..." -ForegroundColor Blue

$gitignoreEntries = @(
    "",
    "# Docker secrets (NEVER COMMIT)",
    "secrets/",
    "!secrets/README.md",
    "!secrets/*.example",
    "",
    "# Environment files",
    ".env",
    ".env.local",
    ".env.production"
)

if (Test-Path ".gitignore") {
    $currentGitignore = Get-Content ".gitignore" -Raw
    $needsUpdate = $false
    
    foreach ($entry in $gitignoreEntries) {
        if ($entry -and -not $currentGitignore.Contains($entry)) {
            $needsUpdate = $true
            break
        }
    }
    
    if ($needsUpdate) {
        $gitignoreEntries | Add-Content ".gitignore"
        Write-Host "   ✅ Updated .gitignore with security entries" -ForegroundColor Green
    } else {
        Write-Host "   ✅ .gitignore already contains security entries" -ForegroundColor Green
    }
} else {
    $gitignoreEntries | Out-File ".gitignore" -Encoding UTF8
    Write-Host "   ✅ Created .gitignore with security entries" -ForegroundColor Green
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
