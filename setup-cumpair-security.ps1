#Requires -Version 5.1
<#
.SYNOPSIS
    Cumpair Docker Security Setup Script
    Generates secure secrets and configures Docker environment for Cumpair AI Product Analysis system

.DESCRIPTION
    This script creates a secure Docker environment for Cumpair with:
    - Cryptographically secure secret generation
    - Proper file permissions and access controls
    - Docker security hardening for AI/ML workloads
    - Production-ready configurations
    - Cumpair-specific service configurations

.PARAMETER Force
    Force regeneration of existing secrets

.PARAMETER Environment
    Target environment (Development, Staging, Production)

.PARAMETER SkipValidation
    Skip Docker and system validation checks

.EXAMPLE
    .\setup-cumpair-security.ps1
    .\setup-cumpair-security.ps1 -Force -Environment Production
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage = "Force regeneration of existing secrets")]
    [switch]$Force,
    
    [Parameter(HelpMessage = "Target environment")]
    [ValidateSet("Development", "Staging", "Production")]
    [string]$Environment = "Development",
    
    [Parameter(HelpMessage = "Skip Docker validation checks")]
    [switch]$SkipValidation
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Constants for Cumpair project
$SCRIPT_VERSION = "1.0.0"
$PROJECT_NAME = "Cumpair"
$MIN_POWERSHELL_VERSION = [Version]"5.1"
$SECRETS_DIR = "secrets"
$SCRIPTS_DIR = "scripts"
$NGINX_DIR = "nginx"
$BACKUP_DIR = "backup"

# Cumpair-specific security configuration
$CumpairSecrets = @{
    DatabasePassword = @{ Length = 24; Complexity = "High"; Description = "PostgreSQL password for Cumpair database (compair user)" }
    SecretKey = @{ Length = 44; Complexity = "High"; Description = "FastAPI secret key for JWT tokens and sessions" }
    RedisPassword = @{ Length = 20; Complexity = "High"; Description = "Redis password for Celery task queue and caching" }
    GrafanaPassword = @{ Length = 16; Complexity = "Medium"; Description = "Grafana admin password for monitoring dashboard" }
    ProxyApiKey = @{ Length = 32; Complexity = "High"; Description = "API key for proxy service authentication" }
    CaptchaSecret = @{ Length = 24; Complexity = "High"; Description = "CAPTCHA service secret key" }
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

function Write-CumpairMessage {
    param(
        [string]$Message,
        [string]$Type = "Info",
        [int]$Indent = 0
    )
    
    $prefix = switch ($Type) {
        "Success" { "[SUCCESS]" }
        "Warning" { "[WARNING]" }
        "Error" { "[ERROR]" }
        "Info" { "[INFO]" }
        "Highlight" { "[CONFIG]" }
        default { "*" }
    }
    
    $indentText = "   " * $Indent
    Write-Host "$indentText$prefix $Message" -ForegroundColor $Colors[$Type]
}

function Test-CumpairPrerequisites {
    Write-Host "`n[CHECK] Checking Cumpair Prerequisites..." -ForegroundColor $Colors.Info
    
    # Check PowerShell version
    if ($PSVersionTable.PSVersion -lt $MIN_POWERSHELL_VERSION) {
        Write-CumpairMessage "PowerShell version $($PSVersionTable.PSVersion) is below minimum required version $MIN_POWERSHELL_VERSION" "Error"
        throw "Insufficient PowerShell version"
    }
    Write-CumpairMessage "PowerShell version $($PSVersionTable.PSVersion) meets requirements"
    
    # Check if we're in the correct directory
    if (-not (Test-Path "main.py") -or -not (Test-Path "app")) {
        Write-CumpairMessage "This doesn't appear to be the Cumpair project root directory" "Error"
        Write-CumpairMessage "Please run this script from the directory containing main.py and app/" "Error"
        throw "Incorrect directory"
    }
    Write-CumpairMessage "Cumpair project structure verified"
    
    if (-not $SkipValidation) {
        # Check Docker availability
        try {
            $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
            if ($dockerVersion) {
                Write-CumpairMessage "Docker Engine version: $dockerVersion"
            } else {
                Write-CumpairMessage "Docker Engine not accessible" "Warning"
                Write-CumpairMessage "Install Docker Desktop: https://www.docker.com/products/docker-desktop" "Info"
            }
        } catch {
            Write-CumpairMessage "Docker is not available - install Docker Desktop" "Warning"
        }
        
        # Check Docker Compose
        try {
            $composeVersion = docker-compose version --short 2>$null
            if ($composeVersion) {
                Write-CumpairMessage "Docker Compose version: $composeVersion"
            }
        } catch {
            Write-CumpairMessage "Docker Compose not available" "Warning"
        }
    }
    
    # Check if required compose file exists
    if (Test-Path "docker-compose.secure.yml") {
        Write-CumpairMessage "Secure Docker Compose file found"
    } else {
        Write-CumpairMessage "docker-compose.secure.yml not found - will be created" "Warning"
    }
}

function New-SecurePassword {
    param(
        [int]$Length = 24,
        [string]$Complexity = "High"
    )
    
    try {
        # Use cryptographically secure random number generator
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        
        # Character sets based on complexity
        $charSets = switch ($Complexity) {
            "High" { 
                @{
                    Lower = "abcdefghijklmnopqrstuvwxyz"
                    Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" 
                    Digits = "0123456789"
                    Symbols = "!@#$%^&*-_=+"
                }
            }
            "Medium" {
                @{
                    Lower = "abcdefghijklmnopqrstuvwxyz"
                    Upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    Digits = "0123456789"
                    Symbols = "!@#$"
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
        
        # First, add one character from each required set
        foreach ($setName in $charSets.Keys) {
            $setChars = $charSets[$setName].ToCharArray()
            $bytes = [byte[]]::new(4)
            $rng.GetBytes($bytes)
            $randomIndex = [Math]::Abs([BitConverter]::ToInt32($bytes, 0)) % $setChars.Length
            $password += $setChars[$randomIndex]
        }
        
        # Fill remaining length with random characters
        for ($i = $password.Length; $i -lt $Length; $i++) {
            $bytes = [byte[]]::new(4)
            $rng.GetBytes($bytes)
            $randomIndex = [Math]::Abs([BitConverter]::ToInt32($bytes, 0)) % $allChars.Length
            $password += $allChars[$randomIndex]
        }
        
        # Shuffle the password
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
        Write-CumpairMessage "Failed to generate cryptographic password, using fallback method" "Warning"
        
        # Fallback method
        $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        $password = ""
        for ($i = 0; $i -lt $Length; $i++) {
            $password += $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)]
        }
        return $password
    }
}

function New-SecureToken {
    param([int]$Length = 44)
    
    try {
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $bytes = [byte[]]::new([Math]::Ceiling($Length * 3 / 4))
        $rng.GetBytes($bytes)
        $token = [Convert]::ToBase64String($bytes)
        $rng.Dispose()
        
        # Clean up base64 for URL safety
        $cleanToken = $token.Replace('+', '-').Replace('/', '_').Replace('=', '')
        return $cleanToken.Substring(0, [Math]::Min($Length, $cleanToken.Length))
        
    } catch {
        Write-CumpairMessage "Failed to generate cryptographic token, using fallback" "Warning"
        return New-SecurePassword -Length $Length -Complexity "High"
    }
}

function Set-SecureFilePermissions {
    param([string]$Path)
    
    try {
        if (Test-Path $Path) {
            # Get current user
            $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            
            # Set restrictive permissions
            $acl = Get-Acl $Path
            $acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }
            
            # Add current user with full control
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $currentUser,
                [System.Security.AccessControl.FileSystemRights]::FullControl,
                [System.Security.AccessControl.AccessControlType]::Allow
            )
            $acl.SetAccessRule($accessRule)
            $acl.SetAccessRuleProtection($true, $false)
            
            Set-Acl -Path $Path -AclObject $acl
            Write-CumpairMessage "Secure permissions applied to $Path" "Success" 2
            return $true
        }
    } catch {
        Write-CumpairMessage "Could not set secure permissions on $Path" "Warning"
        return $false
    }
    
    return $false
}

function New-CumpairSecretFile {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description = ""
    )
    
    $filePath = Join-Path $SECRETS_DIR "$Name.txt"
    
    try {
        # Write secret to file
        $Value | Out-File -FilePath $filePath -Encoding UTF8 -NoNewline
        
        # Set secure permissions
        Set-SecureFilePermissions -Path $filePath | Out-Null
        
        Write-CumpairMessage "$Name secret generated ($($Value.Length) characters)" "Success" 1
        
        return $true
        
    } catch {
        Write-CumpairMessage "Failed to create secret file $Name" "Error"
        return $false
    }
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
            Write-CumpairMessage "Existing secrets backed up to: $backupPath"
            return $true
        } catch {
            Write-CumpairMessage "Failed to backup existing secrets" "Warning"
            return $false
        }
    }
    return $true
}

#endregion

#region Main Script

function Main {
    # Display header
    Write-Host "[SECURE] $PROJECT_NAME Docker Security Setup Script v$SCRIPT_VERSION" -ForegroundColor $Colors.Highlight
    Write-Host "Environment: $Environment" -ForegroundColor $Colors.Info
    Write-Host "=" * 70

    try {
        # Step 1: Prerequisites check
        Test-CumpairPrerequisites

        # Step 2: Backup existing secrets if forced
        if (Test-Path $SECRETS_DIR) {
            if ($Force) {
                Write-Host "`n[BACKUP] Backing up existing secrets..." -ForegroundColor $Colors.Info
                Backup-ExistingSecrets | Out-Null
            } else {
                Write-Host "`n[WARNING] Secrets directory already exists. Use -Force to regenerate." -ForegroundColor $Colors.Warning
                Write-Host "Checking existing secrets..." -ForegroundColor $Colors.Gray
                
                # Check if all required secrets exist
                $missingSecrets = @()
                foreach ($secretName in $CumpairSecrets.Keys) {
                    $fileName = ($secretName -creplace '([A-Z])', '_$1').ToLower().TrimStart('_')
                    $filePath = Join-Path $SECRETS_DIR "$fileName.txt"
                    if (-not (Test-Path $filePath)) {
                        $missingSecrets += $secretName
                    }
                }
                
                if ($missingSecrets.Count -gt 0) {
                    Write-CumpairMessage "Missing secrets: $($missingSecrets -join ', ')" "Warning"
                    Write-Host "Will generate missing secrets only..." -ForegroundColor $Colors.Info
                } else {
                    Write-CumpairMessage "All secrets present, skipping generation"
                    Write-Host "`nTo regenerate secrets, use: .\setup-cumpair-security.ps1 -Force" -ForegroundColor $Colors.Gray
                }
            }
        }

        # Step 3: Create directory structure
        Write-Host "`n[DIRS] Creating directory structure..." -ForegroundColor $Colors.Info
        
        @($SECRETS_DIR, $SCRIPTS_DIR, $NGINX_DIR, $BACKUP_DIR) | ForEach-Object {
            if (-not (Test-Path $_)) {
                New-Item -ItemType Directory -Path $_ -Force | Out-Null
                Write-CumpairMessage "Created directory: $_"
            } else {
                Write-CumpairMessage "Directory exists: $_"
            }
        }

        # Step 4: Generate Cumpair-specific secrets
        Write-Host "`n[KEYS] Generating Cumpair security secrets..." -ForegroundColor $Colors.Info
        
        $secretsGenerated = 0
        foreach ($secretName in $CumpairSecrets.Keys) {
            $config = $CumpairSecrets[$secretName]
            $fileName = ($secretName -creplace '([A-Z])', '_$1').ToLower().TrimStart('_')
            $filePath = Join-Path $SECRETS_DIR "$fileName.txt"
            
            # Skip if file exists and not forcing regeneration
            if ((Test-Path $filePath) -and -not $Force) {
                Write-CumpairMessage "$secretName already exists (skipping)" "Info" 1
                continue
            }
            
            # Generate secret based on type
            $secret = if ($secretName -like "*Key" -or $secretName -like "*Secret") {
                New-SecureToken -Length $config.Length
            } else {
                New-SecurePassword -Length $config.Length -Complexity $config.Complexity
            }
            
            if (New-CumpairSecretFile -Name $fileName -Value $secret -Description $config.Description) {
                Write-CumpairMessage $config.Description "Info" 2
                $secretsGenerated++
            }
        }

        if ($secretsGenerated -gt 0) {
            Write-CumpairMessage "Generated $secretsGenerated new secrets" "Success"
        }

        # Step 5: Set directory permissions
        Write-Host "`n[SECURE] Securing file permissions..." -ForegroundColor $Colors.Info
        Set-SecureFilePermissions -Path $SECRETS_DIR | Out-Null

        # Step 6: Create/update Cumpair environment configuration
        Write-Host "`n[CONFIG] Creating environment configuration..." -ForegroundColor $Colors.Info
        
        if (-not (Test-Path ".env") -or $Force) {
            if (Test-Path ".env.docker") {
                Copy-Item ".env.docker" ".env"
                Write-CumpairMessage "Environment configuration created from .env.docker template"
            } else {
                # Create basic .env if template doesn't exist
                $basicEnv = @"
# Cumpair Environment Configuration
# Generated by setup-cumpair-security.ps1 v$SCRIPT_VERSION

# Application Settings
APP_NAME=Cumpair
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=$($Environment.ToLower())

# Database Configuration
POSTGRES_DB=compair
POSTGRES_USER=compair
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PORT=6379

# Web Application
WEB_PORT=8000
MAX_FILE_SIZE=10485760

# Worker Configuration
CELERY_LOG_LEVEL=info
CELERY_CONCURRENCY=2

# Monitoring
FLOWER_PORT=5555
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_USER=admin

# Proxy and Scraping Services
PROXY_MANAGER_PORT=8001
CAPTCHA_SERVICE_PORT=9001
"@
                $basicEnv | Out-File -FilePath ".env" -Encoding UTF8
                Write-CumpairMessage "Basic environment configuration created"
            }
        } else {
            Write-CumpairMessage "Environment file already exists (skipping)"
        }

        # Step 7: Create Cumpair database initialization script
        Write-Host "`n[DB] Creating Cumpair database initialization script..." -ForegroundColor $Colors.Info
        
        $cumpairDbInit = @'
#!/bin/bash
set -e

echo "Initializing Cumpair PostgreSQL database..."

# Read password from Docker secret
if [ -f /run/secrets/db_password ]; then
    export POSTGRES_PASSWORD=$(cat /run/secrets/db_password)
fi

# Create Cumpair database schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions for Cumpair
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- Create indexes for performance (will be created by Alembic migrations)
    -- This script just ensures the database is ready for Cumpair
    
    -- Log initialization
    INSERT INTO information_schema.sql_features (feature_id, feature_name) 
    VALUES ('CUMPAIR_INIT', 'Cumpair Database Initialized') 
    ON CONFLICT DO NOTHING;
    
EOSQL

echo "Cumpair database initialization completed successfully"
'@

        $cumpairDbInit | Out-File -FilePath (Join-Path $SCRIPTS_DIR "init-db.sh") -Encoding UTF8
        Write-CumpairMessage "Cumpair database initialization script created"

        # Step 8: Create Cumpair health check script
        $cumpairHealthCheck = @'
#!/bin/bash
# Health check script for Cumpair Docker containers

check_database() {
    echo "Checking Cumpair database connection..."
    if pg_isready -h postgres -p 5432 -U compair; then
        echo "PostgreSQL is healthy"
        return 0
    else
        echo "PostgreSQL is not responding"
        return 1
    fi
}

check_redis() {
    echo "Checking Redis connection..."
    if redis-cli -h redis -p 6379 ping | grep -q PONG; then
        echo "Redis is healthy"
        return 0
    else
        echo "Redis is not responding"
        return 1
    fi
}

check_cumpair_web() {
    echo "Checking Cumpair web application..."
    if curl -f -s http://web:8000/health > /dev/null; then
        echo "Cumpair web application is healthy"
        return 0
    else
        echo "Cumpair web application is not responding"
        return 1
    fi
}

check_celery_worker() {
    echo "Checking Celery worker..."
    if docker ps | grep -q "cumpair.*worker"; then
        echo "Celery worker is running"
        return 0
    else
        echo "Celery worker not found (may not be enabled)"
        return 0  # Non-critical
    fi
}

# Main health check
main() {
    echo "Cumpair Docker Environment Health Check"
    echo "=========================================="
    
    local exit_code=0
    
    check_database || exit_code=1
    check_redis || exit_code=1
    check_cumpair_web || exit_code=1
    check_celery_worker
    
    if [ $exit_code -eq 0 ]; then
        echo "All critical Cumpair services are healthy"
    else
        echo "Some critical Cumpair services are unhealthy"
    fi
    
    exit $exit_code
}

main "$@"
'@

        $cumpairHealthCheck | Out-File -FilePath (Join-Path $SCRIPTS_DIR "cumpair-health-check.sh") -Encoding UTF8
        Write-CumpairMessage "Cumpair health check script created"

        # Step 9: Update .gitignore for security
        Write-Host "`n[GIT] Updating .gitignore for security..." -ForegroundColor $Colors.Info
        
        $gitignoreEntries = @(
            "",
            "# Cumpair Docker secrets (NEVER COMMIT)",
            "secrets/",
            "!secrets/README.md",
            "!secrets/*.example",
            "",
            "# Environment files",
            ".env",
            ".env.local",
            ".env.production",
            "",
            "# Docker volumes",
            "postgres_data/",
            "redis_data/",
            "grafana_data/",
            "prometheus_data/"
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
                Write-CumpairMessage "Updated .gitignore with security entries"
            } else {
                Write-CumpairMessage ".gitignore already contains security entries"
            }
        } else {
            $gitignoreEntries | Out-File ".gitignore" -Encoding UTF8
            Write-CumpairMessage "Created .gitignore with security entries"
        }

        # Step 10: Validate Docker Compose configuration
        if (-not $SkipValidation) {
            Write-Host "`n[DOCKER] Validating Docker Compose configuration..." -ForegroundColor $Colors.Info
            
            try {
                docker-compose -f docker-compose.secure.yml config | Out-Null
                Write-CumpairMessage "Docker Compose configuration is valid"
            } catch {
                Write-CumpairMessage "Docker Compose configuration validation failed" "Warning"
                Write-CumpairMessage "Run 'docker-compose -f docker-compose.secure.yml config' for details" "Info"
            }
        }

        # Step 11: Final summary
        Write-Host "`n[SUMMARY] CUMPAIR SECURITY SUMMARY" -ForegroundColor $Colors.Highlight
        Write-Host "=" * 50

        Write-CumpairMessage "Security Setup Complete!" "Success"
        Write-Host "   • Secrets generated with cryptographic security" -ForegroundColor $Colors.Gray
        Write-Host "   • File permissions restricted to current user" -ForegroundColor $Colors.Gray
        Write-Host "   • Database initialization script created" -ForegroundColor $Colors.Gray
        Write-Host "   • Health check scripts configured" -ForegroundColor $Colors.Gray
        Write-Host "   • .gitignore updated for security" -ForegroundColor $Colors.Gray

        Write-Host "`n[NEXT] NEXT STEPS:" -ForegroundColor $Colors.Info
        Write-Host "   1. Start Cumpair with secure Docker setup:" -ForegroundColor $Colors.White
        Write-Host "      .\docker-start-secure.ps1 -Profile basic" -ForegroundColor $Colors.Gray
        Write-Host ""
        Write-Host "   2. For full production setup:" -ForegroundColor $Colors.White
        Write-Host "      .\docker-start-secure.ps1 -Profile production -Build" -ForegroundColor $Colors.Gray
        Write-Host ""
        Write-Host "   3. Monitor with:" -ForegroundColor $Colors.White
        Write-Host "      .\scripts\cumpair-health-check.sh" -ForegroundColor $Colors.Gray

        Write-Host "`n[WARNING] SECURITY REMINDERS:" -ForegroundColor $Colors.Warning
        Write-Host "   • Never commit secrets/ directory to version control" -ForegroundColor $Colors.Gray
        Write-Host "   • Backup secrets securely before deploying" -ForegroundColor $Colors.Gray
        Write-Host "   • Rotate secrets regularly in production" -ForegroundColor $Colors.Gray
        Write-Host "   • Monitor logs for security events" -ForegroundColor $Colors.Gray

        Write-Host "`n[DONE] Cumpair Security Setup Complete!" -ForegroundColor $Colors.Success

    } catch {
        Write-Host "`n[ERROR] Setup failed: $($_.Exception.Message)" -ForegroundColor $Colors.Error
        Write-Host "Please check the error messages above and try again." -ForegroundColor $Colors.Yellow
        exit 1
    }
}

#endregion

# Execute main function
Main

# Generate actual secret files from the examples (if they exist)
if (Test-Path "secrets") {
    $exampleFiles = Get-ChildItem "secrets\*.example" -ErrorAction SilentlyContinue
    foreach ($exampleFile in $exampleFiles) {
        $actualFile = $exampleFile.FullName.Replace(".example", "")
        if (-not (Test-Path $actualFile) -or $Force) {
            $content = Get-Content $exampleFile.FullName -Raw
            $content | Out-File -FilePath $actualFile -Encoding UTF8 -NoNewline
            Write-CumpairMessage "Created actual secret file from example: $(Split-Path $actualFile -Leaf)" "Info"
        }
    }
}

Write-Host "`nPress any key to continue..." -ForegroundColor $Colors.Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")