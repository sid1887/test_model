#Requires -Version 5.1
<#
.SYNOPSIS
    Enhanced Docker Security Setup Script
    Generates secure secrets and sets up Docker environment following security best practices

.DESCRIPTION
    This script creates a secure Docker environment with:
    - Cryptographically secure secret generation using modern APIs
    - Proper file permissions and access controls
    - Docker security hardening
    - Production-ready configurations
    - Comprehensive validation and error handling

.PARAMETER Force
    Force regeneration of existing secrets

.PARAMETER Environment
    Target environment (Development, Staging, Production)

.EXAMPLE
    .\docker-security-setup.ps1
    .\docker-security-setup.ps1 -Force -Environment Production
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage = "Force regeneration of existing secrets")]
    [switch]$Force,
    
    [Parameter(HelpMessage = "Target environment")]
    [ValidateSet("Development", "Staging", "Production")]
    [string]$Environment = "Development"
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Constants
$SCRIPT_VERSION = "2.1.0"
$MIN_POWERSHELL_VERSION = [Version]"5.1"
$SECRETS_DIR = "secrets"
$SCRIPTS_DIR = "scripts"
$NGINX_DIR = "nginx"
$BACKUP_DIR = "backup"

# Security configuration
$SecurityConfig = @{
    DatabasePassword = @{ Length = 32; Complexity = "High" }
    SecretKey = @{ Length = 64; Complexity = "High" }
    RedisPassword = @{ Length = 24; Complexity = "High" }
    GrafanaPassword = @{ Length = 20; Complexity = "High" }
    JWTSecret = @{ Length = 44; Complexity = "High" }
    EncryptionKey = @{ Length = 32; Complexity = "High" }
}

# Color scheme
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Blue"
    Highlight = "Cyan"
    Gray = "Gray"
    White = "White"
}

#region Helper Functions

function Write-StatusMessage {
    param(
        [string]$Message,
        [string]$Type = "Info",
        [int]$Indent = 0
    )
    
    $prefix = switch ($Type) {
        "Success" { "✅" }
        "Warning" { "⚠️" }
        "Error" { "❌" }
        "Info" { "ℹ️" }
        default { "•" }
    }
    
    $indentText = "   " * $Indent
    Write-Host "$indentText$prefix $Message" -ForegroundColor $Colors[$Type]
}

function Test-Prerequisites {
    Write-Host "`n🔍 Checking Prerequisites..." -ForegroundColor $Colors.Info
    
    # Check PowerShell version
    if ($PSVersionTable.PSVersion -lt $MIN_POWERSHELL_VERSION) {
        Write-StatusMessage "PowerShell version $($PSVersionTable.PSVersion) is below minimum required version $MIN_POWERSHELL_VERSION" "Error"
        throw "Insufficient PowerShell version"
    }
    Write-StatusMessage "PowerShell version $($PSVersionTable.PSVersion) meets requirements"
    
    # Check if running as administrator for better file permissions
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin -and $Environment -eq "Production") {
        Write-StatusMessage "Running as administrator is recommended for production environments" "Warning"
    }
    
    # Check Docker availability
    try {
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        if ($dockerVersion) {
            Write-StatusMessage "Docker Engine version: $dockerVersion"
        } else {
            Write-StatusMessage "Docker Engine not accessible" "Warning"
        }
    } catch {
        Write-StatusMessage "Docker is not available - install Docker Desktop" "Warning"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose version --short 2>$null
        if ($composeVersion) {
            Write-StatusMessage "Docker Compose version: $composeVersion"
        }
    } catch {
        Write-StatusMessage "Docker Compose not available" "Warning"
    }
}

function New-CryptographicPassword {
    param(
        [int]$Length = 32,
        [string]$Complexity = "High"
    )
    
    try {
        # Use modern cryptographically secure random number generator
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        
        # Define character sets based on complexity
        $charSets = switch ($Complexity) {
            "High" { 
                @{
                    Lower = "abcdefghijklmnopqrstuvwxyz"
                    Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" 
                    Digits = "0123456789"
                    Symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
                }
            }
            "Medium" {
                @{
                    Lower = "abcdefghijklmnopqrstuvwxyz"
                    Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    Digits = "0123456789"
                    Symbols = "!@#$%^&*"
                }
            }
            default {
                @{
                    Lower = "abcdefghijklmnopqrstuvwxyz"
                    Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    Digits = "0123456789"
                }
            }
        }
        
        # Combine all character sets
        $allChars = ($charSets.Values -join "").ToCharArray()
        
        # Generate password ensuring at least one character from each set
        $password = ""
        $usedSets = @()
        
        # First, add one character from each required set
        foreach ($setName in $charSets.Keys) {
            $setChars = $charSets[$setName].ToCharArray()
            $bytes = [byte[]]::new(4)
            $rng.GetBytes($bytes)
            $randomIndex = [Math]::Abs([BitConverter]::ToInt32($bytes, 0)) % $setChars.Length
            $password += $setChars[$randomIndex]
            $usedSets += $setName
        }
        
        # Fill remaining length with random characters
        for ($i = $password.Length; $i -lt $Length; $i++) {
            $bytes = [byte[]]::new(4)
            $rng.GetBytes($bytes)
            $randomIndex = [Math]::Abs([BitConverter]::ToInt32($bytes, 0)) % $allChars.Length
            $password += $allChars[$randomIndex]
        }
        
        # Shuffle the password to avoid predictable patterns
        $passwordArray = $password.ToCharArray()
        for ($i = $passwordArray.Length - 1; $i -gt 0; $i--) {
            $bytes = [byte[]]::new(4)
            $rng.GetBytes($bytes)
            $j = [Math]::Abs([BitConverter]::ToInt32($bytes, 0)) % ($i + 1)
            $temp = $passwordArray[$i]
            $passwordArray[$i] = $passwordArray[$j]
            $passwordArray[$j] = $temp
        }
        
        $rng.Dispose()
        return -join $passwordArray
        
    } catch {
        Write-StatusMessage "Failed to generate cryptographic password, using fallback method" "Warning"
        
        # Fallback to simpler method
        $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        $password = ""
        for ($i = 0; $i -lt $Length; $i++) {
            $password += $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)]
        }
        return $password
    }
}

function New-CryptographicToken {
    param([int]$Length = 44)
    
    try {
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $bytes = [byte[]]::new([Math]::Ceiling($Length * 3 / 4))
        $rng.GetBytes($bytes)
        $token = [Convert]::ToBase64String($bytes)
        $rng.Dispose()
        
        # Clean up base64 for URL safety and trim to length
        $cleanToken = $token.Replace('+', '-').Replace('/', '_').Replace('=', '')
        return $cleanToken.Substring(0, [Math]::Min($Length, $cleanToken.Length))
        
    } catch {
        Write-StatusMessage "Failed to generate cryptographic token, using fallback" "Warning"
        return New-CryptographicPassword -Length $Length -Complexity "High"
    }
}

function Set-SecureFilePermissions {
    param([string]$Path)
    
    try {
        if (Test-Path $Path) {
            # Get current user
            $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            
            # Create new ACL
            $acl = New-Object System.Security.AccessControl.DirectorySecurity
            
            # Add full control for current user only
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $currentUser,
                [System.Security.AccessControl.FileSystemRights]::FullControl,
                [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit,
                [System.Security.AccessControl.PropagationFlags]::None,
                [System.Security.AccessControl.AccessControlType]::Allow
            )
            
            $acl.SetAccessRule($accessRule)
            
            # Disable inheritance and remove inherited permissions
            $acl.SetAccessRuleProtection($true, $false)
            
            # Apply the ACL
            Set-Acl -Path $Path -AclObject $acl
            
            Write-StatusMessage "Secure file permissions applied to $Path"
            return $true
        }
    } catch {
        Write-StatusMessage "Could not set secure permissions on $Path`: $($_.Exception.Message)" "Warning"
        return $false
    }
    
    return $false
}

function Backup-ExistingSecrets {
    if (Test-Path $SECRETS_DIR) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = Join-Path $BACKUP_DIR "secrets_backup_$timestamp"
        
        if (-not (Test-Path $BACKUP_DIR)) {
            New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
        }
        
        try {
            Copy-Item -Path $SECRETS_DIR -Destination $backupPath -Recurse -Force
            Write-StatusMessage "Existing secrets backed up to: $backupPath"
            return $true
        } catch {
            Write-StatusMessage "Failed to backup existing secrets: $($_.Exception.Message)" "Warning"
            return $false
        }
    }
    return $true
}

function New-SecretFile {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description = ""
    )
    
    $filePath = Join-Path $SECRETS_DIR "$Name.txt"
    
    try {
        # Write secret to file with UTF8 encoding (no BOM)
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($filePath, $Value, $utf8NoBom)
        
        # Set secure permissions on individual file
        if (Test-Path $filePath) {
            $acl = Get-Acl $filePath
            $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            
            # Remove all access rules
            $acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }
            
            # Add current user with full control
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $currentUser,
                [System.Security.AccessControl.FileSystemRights]::FullControl,
                [System.Security.AccessControl.AccessControlType]::Allow
            )
            $acl.SetAccessRule($accessRule)
            $acl.SetAccessRuleProtection($true, $false)
            
            Set-Acl -Path $filePath -AclObject $acl
        }
        
        Write-StatusMessage "$Name secret generated ($($Value.Length) characters)" "Success" 1
        
        # Optional: Create description file
        if ($Description) {
            $descPath = Join-Path $SECRETS_DIR "$Name.desc"
            $Description | Out-File -FilePath $descPath -Encoding UTF8
        }
        
        return $true
        
    } catch {
        Write-StatusMessage "Failed to create secret file $Name`: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Test-SecretStrength {
    param([string]$Secret)
    
    $checks = @{
        Length = $Secret.Length -ge 16
        HasLower = $Secret -cmatch "[a-z]"
        HasUpper = $Secret -cmatch "[A-Z]"
        HasDigit = $Secret -match "\d"
        HasSymbol = $Secret -match "[^a-zA-Z0-9]"
        NoRepeating = -not ($Secret -match "(.)\1{2,}")
        NoSequential = -not ($Secret -match "(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)")
    }
    
    $score = ($checks.Values | Where-Object { $_ }).Count
    $maxScore = $checks.Count
    
    return @{
        Score = $score
        MaxScore = $maxScore
        Percentage = [math]::Round(($score / $maxScore) * 100, 1)
        Checks = $checks
    }
}

#endregion

#region Main Script

function Main {
    # Display header
    Write-Host "🔐 Enhanced Docker Security Setup Script v$SCRIPT_VERSION" -ForegroundColor $Colors.Highlight
    Write-Host "Environment: $Environment" -ForegroundColor $Colors.Info
    Write-Host "=" * 70

    try {
        # Step 1: Prerequisites check
        Test-Prerequisites

        # Step 2: Backup existing secrets if requested
        if (Test-Path $SECRETS_DIR) {
            if ($Force) {
                Write-Host "`n💾 Backing up existing secrets..." -ForegroundColor $Colors.Info
                Backup-ExistingSecrets | Out-Null
            } else {
                Write-Host "`n⚠️ Secrets directory already exists. Use -Force to regenerate." -ForegroundColor $Colors.Warning
                Write-Host "Current secrets will be preserved." -ForegroundColor $Colors.Gray
            }
        }

        # Step 3: Create directory structure
        Write-Host "`n📁 Creating directory structure..." -ForegroundColor $Colors.Info
        
        @($SECRETS_DIR, $SCRIPTS_DIR, $NGINX_DIR, $BACKUP_DIR) | ForEach-Object {
            if (-not (Test-Path $_)) {
                New-Item -ItemType Directory -Path $_ -Force | Out-Null
                Write-StatusMessage "Created directory: $_"
            } else {
                Write-StatusMessage "Directory exists: $_"
            }
        }

        # Step 4: Generate secrets
        Write-Host "`n🔑 Generating cryptographically secure secrets..." -ForegroundColor $Colors.Info
        
        $secretsGenerated = 0
        foreach ($secretName in $SecurityConfig.Keys) {
            $config = $SecurityConfig[$secretName]
            $fileName = ($secretName -creplace '([A-Z])', '_$1').ToLower().TrimStart('_')
            $filePath = Join-Path $SECRETS_DIR "$fileName.txt"
            
            # Skip if file exists and not forcing regeneration
            if ((Test-Path $filePath) -and -not $Force) {
                Write-StatusMessage "$secretName already exists (skipping)" "Info" 1
                continue
            }
            
            # Generate secret based on type
            $secret = if ($secretName -like "*Key" -or $secretName -like "*Secret") {
                New-CryptographicToken -Length $config.Length
            } else {
                New-CryptographicPassword -Length $config.Length -Complexity $config.Complexity
            }
            
            # Test secret strength
            $strength = Test-SecretStrength -Secret $secret
            
            # Create secret file with description
            $description = switch ($secretName) {
                "DatabasePassword" { "PostgreSQL database password for application user" }
                "SecretKey" { "Application secret key for session management and CSRF protection" }
                "RedisPassword" { "Redis server authentication password" }
                "GrafanaPassword" { "Grafana admin user password for monitoring dashboard" }
                "JWTSecret" { "JWT token signing secret for authentication" }
                "EncryptionKey" { "Data encryption key for sensitive information" }
                default { "Generated secret for $secretName" }
            }
            
            if (New-SecretFile -Name $fileName -Value $secret -Description $description) {
                Write-StatusMessage "Strength: $($strength.Percentage)% ($($strength.Score)/$($strength.MaxScore) checks passed)" "Info" 2
                $secretsGenerated++
            }
        }

        # Step 5: Set directory permissions
        Write-Host "`n🛡️ Securing file permissions..." -ForegroundColor $Colors.Info
        Set-SecureFilePermissions -Path $SECRETS_DIR | Out-Null

        # Step 6: Create enhanced environment configuration
        Write-Host "`n📄 Creating environment configuration..." -ForegroundColor $Colors.Info
        
        $envTemplate = @"
# Docker Environment Configuration
# Generated by Enhanced Docker Security Setup Script v$SCRIPT_VERSION
# Environment: $Environment
# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')

# Application Settings
NODE_ENV=$($Environment.ToLower())
DEBUG=false
LOG_LEVEL=info

# Security Settings
SECURE_COOKIES=true
CSRF_PROTECTION=true
RATE_LIMIT_ENABLED=true
CORS_ENABLED=true

# Database Configuration
POSTGRES_DB=app_db
POSTGRES_USER=app_user
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis Configuration  
REDIS_HOST=redis
REDIS_PORT=6379

# Monitoring
GRAFANA_USER=admin
PROMETHEUS_RETENTION=15d

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30

# Security Headers
HSTS_MAX_AGE=31536000
CONTENT_SECURITY_POLICY=default-src 'self'
"@

        if (-not (Test-Path ".env") -or $Force) {
            $envTemplate | Out-File -FilePath ".env" -Encoding UTF8
            Write-StatusMessage "Environment configuration created"
        } else {
            Write-StatusMessage "Environment file already exists (skipping)"
        }

        # Step 7: Create enhanced Docker Compose configurations
        Write-Host "`n🐳 Creating Docker Compose configurations..." -ForegroundColor $Colors.Info
        
        # Production Docker Compose with security hardening
        $dockerComposeSecure = @'
version: '3.8'

secrets:
  db_password:
    file: ./secrets/database_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
  redis_password:
    file: ./secrets/redis_password.txt
  grafana_password:
    file: ./secrets/grafana_password.txt

services:
  web:
    build: 
      context: .
      dockerfile: Dockerfile
      target: production
    secrets:
      - db_password
      - secret_key
    environment:
      - DATABASE_URL=postgresql://app_user:$(cat /run/secrets/db_password)@db:5432/app_db
      - SECRET_KEY_FILE=/run/secrets/secret_key
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  db:
    image: postgres:15-alpine
    secrets:
      - db_password
    environment:
      - POSTGRES_DB=app_db
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d app_db"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    secrets:
      - redis_password
    command: >
      redis-server
      --requirepass "$(cat /run/secrets/redis_password)"
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    volumes:
      - redis_data:/data:Z
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 32M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Monitoring stack (optional profile)
  prometheus:
    image: prom/prometheus:latest
    profiles: ["monitoring"]
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus:Z
    security_opt:
      - no-new-privileges:true

  grafana:
    image: grafana/grafana:latest
    profiles: ["monitoring"]
    secrets:
      - grafana_password
    environment:
      - GF_SECURITY_ADMIN_PASSWORD_FILE=/run/secrets/grafana_password
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_DISABLE_GRAVATAR=true
    volumes:
      - grafana_data:/var/lib/grafana:Z
    depends_on:
      - prometheus
    security_opt:
      - no-new-privileges:true

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
'@

        $dockerComposeSecure | Out-File -FilePath "docker-compose.secure.yml" -Encoding UTF8
        Write-StatusMessage "Secure Docker Compose configuration created"

        # Step 8: Create enhanced Nginx configuration
        $nginxSecureConfig = @'
# Enhanced Nginx Configuration for Production
# Security-hardened reverse proxy with modern best practices

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# Optimize worker connections
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Security settings
    server_tokens off;
    more_clear_headers Server;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/javascript
        application/json
        application/xml
        text/css
        text/javascript
        text/plain
        text/xml;
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    
    # Upstream configuration
    upstream web_backend {
        least_conn;
        server web:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    # Security headers map
    map $sent_http_content_type $csp_header {
        default "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self';";
        ~image/ "";
    }
    
    # Main server block
    server {
        listen 80;
        listen [::]:80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy $csp_header always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_conn conn_limit_per_ip 10;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Static files with caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API endpoints with stricter rate limiting
        location /api/ {
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            
            # Timeout settings
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 30s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # Login endpoints with strict rate limiting
        location ~ ^/(login|auth)/ {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Default location for all other requests
        location / {
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            
            # Connection settings
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeout settings
            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Block access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        location ~ \.(env|config|key|pem|crt)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
    
    # SSL/TLS configuration (uncomment when certificates are available)
    # server {
    #     listen 443 ssl http2;
    #     listen [::]:443 ssl http2;
    #     server_name localhost;
    #     
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    #     ssl_prefer_server_ciphers off;
    #     ssl_session_cache shared:SSL:10m;
    #     ssl_session_timeout 10m;
    #     
    #     # All the same location blocks as above...
    # }
}
'@

        $nginxSecureConfig | Out-File -FilePath (Join-Path $NGINX_DIR "nginx.conf") -Encoding UTF8
        Write-StatusMessage "Enhanced Nginx configuration created"

        # Step 9: Create database initialization script
        Write-Host "`n🗄️ Creating database initialization scripts..." -ForegroundColor $Colors.Info
        
        $dbInitScript = @'
#!/bin/bash
set -e

echo "🗄️ Initializing PostgreSQL database..."

# Read password from Docker secret
if [ -f /run/secrets/db_password ]; then
    export POSTGRES_PASSWORD=$(cat /run/secrets/db_password)
fi

# Create database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Create application schema
    CREATE SCHEMA IF NOT EXISTS app;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON SCHEMA app TO $POSTGRES_USER;
    
    -- Create audit table for security monitoring
    CREATE TABLE IF NOT EXISTS app.audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        table_name VARCHAR(255),
        operation VARCHAR(10),
        old_data JSONB,
        new_data JSONB,
        user_id VARCHAR(255),
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        ip_address INET
    );
    
    -- Create index for performance
    CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON app.audit_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON app.audit_log(user_id);
    
    -- Security configurations
    ALTER SYSTEM SET log_statement = 'mod';
    ALTER SYSTEM SET log_min_duration_statement = 1000;
    ALTER SYSTEM SET log_connections = on;
    ALTER SYSTEM SET log_disconnections = on;
    ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
    
    SELECT pg_reload_conf();
EOSQL

echo "✅ Database initialization completed successfully"
'@

        $dbInitScript | Out-File -FilePath (Join-Path $SCRIPTS_DIR "init-db.sh") -Encoding UTF8
        Write-StatusMessage "Database initialization script created"

        # Create health check script
        $healthCheckScript = @'
#!/bin/bash
# Health check script for Docker containers

check_database() {
    echo "Checking database connection..."
    if pg_isready -h db -p 5432 -U app_user; then
        echo "✅ Database is healthy"
        return 0
    else
        echo "❌ Database is not responding"
        return 1
    }
}

check_redis() {
    echo "Checking Redis connection..."
    if redis-cli -h redis -p 6379 ping | grep -q PONG; then
        echo "✅ Redis is healthy"
        return 0
    else
        echo "❌ Redis is not responding"
        return 1
    }
}

check_web_app() {
    echo "Checking web application..."
    if curl -f -s http://web:8000/health > /dev/null; then
        echo "✅ Web application is healthy"
        return 0
    else
        echo "❌ Web application is not responding"
        return 1
    }
}

# Main health check
main() {
    echo "🏥 Docker Environment Health Check"
    echo "=================================="
    
    local exit_code=0
    
    check_database || exit_code=1
    check_redis || exit_code=1
    check_web_app || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ All services are healthy"
    else
        echo "❌ Some services are unhealthy"
    fi
    
    exit $exit_code
}

main "$@"
'@

        $healthCheckScript | Out-File -FilePath (Join-Path $SCRIPTS_DIR "health-check.sh") -Encoding UTF8
        Write-StatusMessage "Health check script created"

        # Step 10: Create monitoring configuration
        Write-Host "`n📊 Creating monitoring configuration..." -ForegroundColor $Colors.Info
        
        $monitoringDir = "monitoring"
        if (-not (Test-Path $monitoringDir)) {
            New-Item -ItemType Directory -Path $monitoringDir -Force | Out-Null
        }
        
        $prometheusConfig = @'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
      
  - job_name: 'web-app'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
'@

        $prometheusConfig | Out-File -FilePath (Join-Path $monitoringDir "prometheus.yml") -Encoding UTF8
        Write-StatusMessage "Prometheus configuration created"

        # Step 11: Create security documentation
        Write-Host "`n📝 Creating security documentation..." -ForegroundColor $Colors.Info
        
        $securityDoc = @"
# Docker Security Configuration

## Overview
This document outlines the security measures implemented in the Docker environment.

## Generated Secrets
- **Database Password**: 32-character cryptographically secure password
- **Application Secret Key**: 64-character base64-encoded token
- **Redis Password**: 24-character secure password
- **Grafana Password**: 20-character secure password
- **JWT Secret**: 44-character base64-encoded token
- **Encryption Key**: 32-character cryptographically secure key

## Security Features

### Container Security
- **No-new-privileges**: Prevents privilege escalation
- **Capability dropping**: Removes unnecessary Linux capabilities
- **Resource limits**: CPU and memory constraints
- **Security contexts**: Non-root user execution where possible
- **Tmpfs mounts**: Secure temporary storage

### Network Security
- **Rate limiting**: API and login endpoint protection
- **CORS configuration**: Cross-origin resource sharing controls
- **Security headers**: Comprehensive HTTP security headers
- **SSL/TLS ready**: HTTPS configuration template provided

### Data Security
- **Encrypted secrets**: Docker secrets for sensitive data
- **Secure file permissions**: Restricted access to secret files
- **Database encryption**: PostgreSQL with SCRAM-SHA-256
- **Audit logging**: Database operation tracking

### Monitoring & Alerting
- **Health checks**: Automated service health monitoring
- **Prometheus metrics**: Performance and security metrics
- **Grafana dashboards**: Visual monitoring interface
- **Log aggregation**: Centralized logging for security events

## Deployment Instructions

### Development
``````bash
docker-compose up -d