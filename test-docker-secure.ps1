# Simple Docker Secure Test Script
param([string]$Profile = "basic")

Write-Host "Testing Docker Secure Setup..." -ForegroundColor Green

# Check if secrets exist
$requiredSecrets = @("db_password.txt", "secret_key.txt", "redis_password.txt")
foreach ($secret in $requiredSecrets) {
    if (Test-Path "secrets\$secret") {
        Write-Host "✅ Secret found: $secret" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing secret: $secret" -ForegroundColor Red
        Write-Host "Run: .\setup-docker-security.ps1" -ForegroundColor Yellow
        exit 1
    }
}

# Check Docker availability
try {
    docker version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not available" -ForegroundColor Red
    exit 1
}

try {
    docker-compose version | Out-Null
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not available" -ForegroundColor Red
    exit 1
}

# Check if compose file exists
if (Test-Path "docker-compose.secure.yml") {
    Write-Host "✅ Secure compose file found" -ForegroundColor Green
} else {
    Write-Host "❌ docker-compose.secure.yml not found" -ForegroundColor Red
    exit 1
}

# Validate compose configuration
Write-Host "Validating Docker Compose configuration..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.secure.yml config | Out-Null
    Write-Host "✅ Docker Compose configuration is valid" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose configuration has errors" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 All prerequisites passed!" -ForegroundColor Green
Write-Host "You can now start the secure Docker setup." -ForegroundColor White
