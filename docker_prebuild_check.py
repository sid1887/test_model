#!/usr/bin/env python3
"""
Docker Pre-Build Validation Script
Checks all dependencies, configurations, and potential issues before Docker build
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class DockerPreBuildChecker:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def log(self, message: str, level: str = 'info'):
        """Pretty logging"""
        if level == 'success':
            print(f"{GREEN}✓{RESET} {message}")
            self.passed.append(message)
        elif level == 'warning':
            print(f"{YELLOW}⚠{RESET} {message}")
            self.warnings.append(message)
        elif level == 'error':
            print(f"{RED}✗{RESET} {message}")
            self.issues.append(message)
        else:
            print(f"{BLUE}ℹ{RESET} {message}")
    
    def check_file_exists(self, filepath: str, critical: bool = True) -> bool:
        """Check if a file exists"""
        path = self.root_dir / filepath
        if path.exists():
            self.log(f"Found {filepath}", 'success')
            return True
        else:
            level = 'error' if critical else 'warning'
            self.log(f"Missing {filepath}", level)
            return False
    
    def check_docker_installed(self):
        """Check if Docker and Docker Compose are installed"""
        print(f"\n{BLUE}[1/10] Checking Docker Installation...{RESET}")
        
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Docker installed: {result.stdout.strip()}", 'success')
            else:
                self.log("Docker not found or not working", 'error')
        except FileNotFoundError:
            self.log("Docker not installed", 'error')
        
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Docker Compose installed: {result.stdout.strip()}", 'success')
            else:
                self.log("Docker Compose not found", 'error')
        except FileNotFoundError:
            self.log("Docker Compose not installed", 'error')
    
    def check_dockerfiles(self):
        """Check all Dockerfiles exist"""
        print(f"\n{BLUE}[2/10] Checking Dockerfiles...{RESET}")
        
        dockerfiles = [
            'Dockerfile',
            'frontend/Dockerfile',
            'scraper/Dockerfile',
            'captcha-service/Dockerfile'
        ]
        
        for dockerfile in dockerfiles:
            self.check_file_exists(dockerfile, critical=True)
    
    def check_docker_compose(self):
        """Check docker-compose.yml and validate it"""
        print(f"\n{BLUE}[3/10] Checking Docker Compose Configuration...{RESET}")
        
        if self.check_file_exists('docker-compose.yml', critical=True):
            # Validate docker-compose.yml
            try:
                result = subprocess.run(
                    ['docker-compose', 'config'],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.log("docker-compose.yml is valid", 'success')
                else:
                    self.log(f"docker-compose.yml validation failed: {result.stderr}", 'error')
            except Exception as e:
                self.log(f"Could not validate docker-compose.yml: {e}", 'warning')
    
    def check_env_files(self):
        """Check environment configuration files"""
        print(f"\n{BLUE}[4/10] Checking Environment Files...{RESET}")
        
        env_files = [
            '.env.example',
            'frontend/.env.example',
            'scraper/.env.example'
        ]
        
        for env_file in env_files:
            self.check_file_exists(env_file, critical=False)
        
        # Check if .env exists (not critical but recommended)
        if not (self.root_dir / '.env').exists():
            self.log("No .env file found (will use docker-compose environment)", 'warning')
    
    def check_package_files(self):
        """Check all package dependency files"""
        print(f"\n{BLUE}[5/10] Checking Dependency Files...{RESET}")
        
        # Backend
        self.check_file_exists('requirements.txt', critical=True)
        self.check_file_exists('auto_install_packages.py', critical=False)
        
        # Frontend
        self.check_file_exists('frontend/package.json', critical=True)
        self.check_file_exists('frontend/package-lock.json', critical=False)
        
        # Scraper
        self.check_file_exists('scraper/package.json', critical=True)
        self.check_file_exists('scraper/package-lock.json', critical=False)
    
    def check_startup_scripts(self):
        """Check startup and health check scripts"""
        print(f"\n{BLUE}[6/10] Checking Startup Scripts...{RESET}")
        
        scripts = [
            'scripts/start.sh',
            'scripts/healthcheck.sh'
        ]
        
        for script in scripts:
            if self.check_file_exists(script, critical=True):
                # Check if executable
                script_path = self.root_dir / script
                if os.access(script_path, os.X_OK):
                    self.log(f"{script} is executable", 'success')
                else:
                    self.log(f"{script} is not executable (will be fixed in Docker)", 'warning')
    
    def check_database_migrations(self):
        """Check Alembic migrations"""
        print(f"\n{BLUE}[7/10] Checking Database Migrations...{RESET}")
        
        self.check_file_exists('alembic.ini', critical=True)
        self.check_file_exists('alembic/env.py', critical=True)
        
        versions_dir = self.root_dir / 'alembic' / 'versions'
        if versions_dir.exists():
            migrations = list(versions_dir.glob('*.py'))
            migrations = [m for m in migrations if not m.name.startswith('__')]
            self.log(f"Found {len(migrations)} migration files", 'success')
            
            # Check for critical migrations
            migration_names = [m.stem for m in migrations]
            if any('initial' in name.lower() for name in migration_names):
                self.log("Initial migration found", 'success')
            else:
                self.log("No initial migration found", 'warning')
        else:
            self.log("No migrations directory found", 'error')
    
    def check_port_conflicts(self):
        """Check for potential port conflicts"""
        print(f"\n{BLUE}[8/10] Checking Port Configuration...{RESET}")
        
        ports = {
            8000: 'web (FastAPI)',
            5432: 'postgres',
            6379: 'redis',
            3001: 'scraper',
            9001: 'captcha',
            8080: 'frontend (Nginx)',
            5555: 'flower (optional)',
            9090: 'prometheus (optional)',
            3002: 'grafana (optional)'
        }
        
        for port, service in ports.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.log(f"Port {port} ({service}) is already in use", 'warning')
                else:
                    self.log(f"Port {port} ({service}) is available", 'success')
            except Exception as e:
                self.log(f"Could not check port {port}: {e}", 'warning')
    
    def check_service_consistency(self):
        """Check consistency between services"""
        print(f"\n{BLUE}[9/10] Checking Service Consistency...{RESET}")
        
        # Check CAPTCHA_SERVICE_URL consistency
        compose_path = self.root_dir / 'docker-compose.yml'
        scraper_env = self.root_dir / 'scraper' / '.env.example'
        
        if compose_path.exists():
            with open(compose_path) as f:
                compose_content = f.read()
                if 'captcha:9001' in compose_content:
                    self.log("Captcha service URL consistent in docker-compose.yml", 'success')
                else:
                    self.log("Captcha service URL issue in docker-compose.yml", 'warning')
        
        # Check frontend env vars use correct prefix
        frontend_env = self.root_dir / 'frontend' / '.env.example'
        if frontend_env.exists():
            with open(frontend_env) as f:
                env_content = f.read()
                if 'VITE_' in env_content:
                    self.log("Frontend uses correct VITE_ prefix", 'success')
                elif 'NEXT_PUBLIC_' in env_content:
                    self.log("Frontend uses wrong NEXT_PUBLIC_ prefix (should be VITE_)", 'error')
    
    def check_nginx_config(self):
        """Check Nginx configuration for frontend"""
        print(f"\n{BLUE}[10/10] Checking Nginx Configuration...{RESET}")
        
        if self.check_file_exists('frontend/nginx.conf', critical=True):
            nginx_conf = self.root_dir / 'frontend' / 'nginx.conf'
            with open(nginx_conf) as f:
                content = f.read()
                
                # Check for critical configurations
                checks = [
                    ('listen 3000', 'Listening on port 3000'),
                    ('try_files', 'SPA routing configured'),
                    ('proxy_pass http://web:8000', 'API proxy configured'),
                    ('Upgrade $http_upgrade', 'WebSocket support configured')
                ]
                
                for check_str, desc in checks:
                    if check_str in content:
                        self.log(desc, 'success')
                    else:
                        self.log(f"Missing: {desc}", 'warning')
    
    def generate_report(self):
        """Generate final report"""
        print(f"\n{'='*60}")
        print(f"{BLUE}DOCKER PRE-BUILD VALIDATION REPORT{RESET}")
        print(f"{'='*60}")
        
        print(f"\n{GREEN}✓ PASSED: {len(self.passed)}{RESET}")
        
        if self.warnings:
            print(f"\n{YELLOW}⚠ WARNINGS: {len(self.warnings)}{RESET}")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"  • {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more")
        
        if self.issues:
            print(f"\n{RED}✗ CRITICAL ISSUES: {len(self.issues)}{RESET}")
            for issue in self.issues:
                print(f"  • {issue}")
        
        print(f"\n{'='*60}")
        
        if self.issues:
            print(f"{RED}❌ BUILD NOT READY - Fix critical issues first{RESET}")
            return False
        elif self.warnings:
            print(f"{YELLOW}⚠️  BUILD READY WITH WARNINGS{RESET}")
            print(f"You can proceed, but review warnings to avoid runtime issues")
            return True
        else:
            print(f"{GREEN}✅ BUILD READY - All checks passed!{RESET}")
            return True
    
    def run(self):
        """Run all checks"""
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}DOCKER PRE-BUILD VALIDATION{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        self.check_docker_installed()
        self.check_dockerfiles()
        self.check_docker_compose()
        self.check_env_files()
        self.check_package_files()
        self.check_startup_scripts()
        self.check_database_migrations()
        self.check_port_conflicts()
        self.check_service_consistency()
        self.check_nginx_config()
        
        return self.generate_report()

if __name__ == '__main__':
    checker = DockerPreBuildChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
