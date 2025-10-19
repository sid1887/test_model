#!/usr/bin/env python3
"""
Comprehensive validation script for all the Docker and configuration fixes
This script validates all the improvements mentioned in the analysis report.
"""

import subprocess
import json
import sys
import os
from pathlib import Path
import requests
import time
import yaml
import re
from typing import Dict, List, Tuple, Optional

class FixValidator:
    def __init__(self):
        self.results = {
            "port_fixes": [],
            "docker_optimizations": [],
            "security_checks": [],
            "linting_checks": [],
            "dependency_checks": [],
            "overall_status": "PENDING"
        }
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
    def print_check(self, name: str, status: bool, details: str = ""):
        """Print a check result"""
        emoji = "✅" if status else "❌"
        print(f"{emoji} {name}")
        if details:
            print(f"   {details}")
        return status
        
    def validate_port_standardization(self) -> bool:
        """Validate that all scraper port references are standardized to 3001"""
        self.print_header("PORT STANDARDIZATION VALIDATION")
        
        all_passed = True
        
        # Check Docker Compose files
        compose_files = list(Path('.').glob('docker-compose*.yml'))
        for compose_file in compose_files:
            try:
                with open(compose_file, 'r') as f:
                    content = f.read()
                
                # Check for old port 3000 references
                if 'scraper:3000' in content:
                    all_passed = self.print_check(
                        f"{compose_file.name} - Port Reference", 
                        False, 
                        "Still contains scraper:3000 reference"
                    )
                else:
                    self.print_check(f"{compose_file.name} - Port Reference", True)
                      # Check for correct port mapping
                if '"3001:3001"' in content or "'3001:3001'" in content:
                    self.print_check(f"{compose_file.name} - Port Mapping", True)
                elif 'scraper:' in content:
                    # Only check port mapping if scraper service is actually defined
                    if re.search(r'^\s*scraper:\s*$', content, re.MULTILINE):
                        all_passed = self.print_check(
                            f"{compose_file.name} - Port Mapping", 
                            False, 
                            "Missing 3001:3001 port mapping"
                        )
                    else:
                        self.print_check(f"{compose_file.name} - Port Mapping", True, "No scraper service defined (OK)")
                else:
                    self.print_check(f"{compose_file.name} - Port Mapping", True, "No scraper service")
                    
            except Exception as e:
                all_passed = self.print_check(f"{compose_file.name}", False, f"Error: {e}")
        
        # Check scraper Dockerfile
        scraper_dockerfile = Path('scraper/Dockerfile')
        if scraper_dockerfile.exists():
            with open(scraper_dockerfile, 'r') as f:
                content = f.read()
            
            if 'EXPOSE 3001' in content:
                self.print_check("Scraper Dockerfile - EXPOSE", True)
            else:
                all_passed = self.print_check("Scraper Dockerfile - EXPOSE", False, "Should expose port 3001")
                
        # Check script files
        script_patterns = ['*.ps1', '*.sh', 'Makefile*']
        for pattern in script_patterns:
            for script_file in Path('.').rglob(pattern):
                if script_file.is_file():
                    try:
                        with open(script_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Look for localhost:3000 (should be 3001)
                        if 'localhost:3000' in content and 'scraper' in content.lower():
                            all_passed = self.print_check(
                                f"{script_file.name} - Port Reference", 
                                False, 
                                "Contains localhost:3000 reference"
                            )
                    except Exception:
                        pass  # Skip files we can't read
        
        self.results["port_fixes"] = all_passed
        return all_passed
        
    def validate_docker_optimizations(self) -> bool:
        """Validate Docker optimizations"""
        self.print_header("DOCKER OPTIMIZATIONS VALIDATION")
        
        all_passed = True
          # Check .dockerignore files
        dockerignore_files = [Path('.dockerignore'), Path('scraper/.dockerignore')]
        for dockerignore in dockerignore_files:
            if dockerignore.exists():
                with open(dockerignore, 'r') as f:
                    content = f.read()
                
                required_patterns = ['node_modules', 'pycache', '*.log', '*.pyc']
                missing_patterns = []
                for pattern in required_patterns:
                    if pattern not in content and f'**/{pattern}' not in content and f'**/*{pattern}' not in content:
                        missing_patterns.append(pattern)
                
                if not missing_patterns:
                    self.print_check(f"{dockerignore.name}", True)
                else:
                    all_passed = self.print_check(
                        f"{dockerignore.name}", 
                        False, 
                        f"Missing patterns: {missing_patterns}"
                    )
            else:
                all_passed = self.print_check(f"{dockerignore}", False, "File does not exist")
        
        # Check scraper Dockerfile for build optimization
        scraper_dockerfile = Path('scraper/Dockerfile')
        if scraper_dockerfile.exists():
            with open(scraper_dockerfile, 'r') as f:
                lines = f.readlines()
            
            # Check if package.json is copied before npm install
            package_copy_line = None
            npm_install_line = None
            code_copy_line = None
            
            for i, line in enumerate(lines):
                if 'COPY package*.json' in line:
                    package_copy_line = i
                elif 'npm ci' in line or 'npm install' in line:
                    npm_install_line = i
                elif 'COPY . .' in line:
                    code_copy_line = i
            
            if (package_copy_line is not None and 
                npm_install_line is not None and 
                code_copy_line is not None and
                package_copy_line < npm_install_line < code_copy_line):
                self.print_check("Scraper Dockerfile - Layer Optimization", True)
            else:
                all_passed = self.print_check(
                    "Scraper Dockerfile - Layer Optimization", 
                    False, 
                    "Dependencies should be installed before copying code"
                )
        
        # Check for health checks
        compose_files = list(Path('.').glob('docker-compose*.yml'))
        for compose_file in compose_files:
            try:
                with open(compose_file, 'r') as f:
                    content = f.read()
                
                if 'healthcheck:' in content:
                    self.print_check(f"{compose_file.name} - Health Checks", True)
                else:
                    self.print_check(f"{compose_file.name} - Health Checks", False, "No health checks found")
                    
            except Exception as e:
                all_passed = self.print_check(f"{compose_file.name}", False, f"Error: {e}")
        
        self.results["docker_optimizations"] = all_passed
        return all_passed
        
    def validate_security_enforcement(self) -> bool:
        """Validate security enforcement"""
        self.print_header("SECURITY ENFORCEMENT VALIDATION")
        
        all_passed = True
        
        # Check if .env enforcement exists
        secure_scripts = ['docker-start-secure-fixed.ps1', 'docker-start-secure.ps1']
        for script in secure_scripts:
            script_path = Path(script)
            if script_path.exists():
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'exit 1' in content and '.env' in content:
                    self.print_check(f"{script} - .env Enforcement", True)
                else:
                    all_passed = self.print_check(f"{script} - .env Enforcement", False, "No .env validation found")
                
                if 'secrets' in content and 'exit 1' in content:
                    self.print_check(f"{script} - Secrets Enforcement", True)
                else:
                    all_passed = self.print_check(f"{script} - Secrets Enforcement", False, "No secrets validation found")
            else:
                all_passed = self.print_check(f"{script}", False, "Script not found")
        
        # Check secrets directory structure
        secrets_dir = Path('secrets')
        if secrets_dir.exists():
            self.print_check("Secrets Directory", True)
            
            # Check .gitignore excludes secrets
            gitignore = Path('.gitignore')
            if gitignore.exists():
                with open(gitignore, 'r') as f:
                    gitignore_content = f.read()
                
                if 'secrets/' in gitignore_content:
                    self.print_check("Secrets .gitignore", True)
                else:
                    all_passed = self.print_check("Secrets .gitignore", False, "secrets/ not in .gitignore")
        else:
            self.print_check("Secrets Directory", False, "secrets/ directory not found")        
        self.results["security_checks"] = all_passed
        return all_passed
        
    def validate_linting_integration(self) -> bool:
        """Validate linting integration"""
        self.print_header("LINTING INTEGRATION VALIDATION")
        
        all_passed = True
        
        # Check pre-flight check includes linting
        preflight_file = Path('pre_flight_check.py')
        if preflight_file.exists():
            with open(preflight_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
              # Check for linting functionality
            linting_indicators = ['flake8', 'syntax_check', 'ast.parse', 'compile(']
            has_linting = any(indicator in content for indicator in linting_indicators)
            
            if has_linting:
                self.print_check("Pre-flight Linting Integration", True)
            else:
                all_passed = self.print_check("Pre-flight Linting Integration", False, "No linting checks found")
                
            if 'flake8' in content:
                self.print_check("Python Linting (flake8)", True)
            else:
                self.print_check("Python Linting (flake8)", False, "flake8 not integrated")
                
            # Check for JavaScript linting capability
            js_lint_indicators = ['npm', 'lint', 'eslint', 'jshint']
            has_js_lint = any(indicator in content for indicator in js_lint_indicators)
            
            if has_js_lint:
                self.print_check("JavaScript Linting", True)
            else:
                self.print_check("JavaScript Linting", False, "JS linting not integrated")
                
            if 'docker-compose' in content and 'config' in content:
                self.print_check("Docker Compose Validation", True)
            else:
                all_passed = self.print_check("Docker Compose Validation", False, "No compose validation")
        else:
            all_passed = self.print_check("Pre-flight Check File", False, "pre_flight_check.py not found")
        
        self.results["linting_checks"] = all_passed
        return all_passed
        
    def validate_dependency_management(self) -> bool:
        """Validate dependency management"""
        self.print_header("DEPENDENCY MANAGEMENT VALIDATION")
        all_passed = True
        
        # Check if dependency update checks exist
        preflight_file = Path('pre_flight_check.py')
        if preflight_file.exists():
            with open(preflight_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for dependency update functionality
            dep_check_indicators = ['outdated', 'pip.*list', 'npm.*outdated', 'update.*check']
            has_dep_checks = any(re.search(indicator, content) for indicator in dep_check_indicators)
            
            if has_dep_checks:
                self.print_check("Outdated Dependency Checks", True)
            else:
                all_passed = self.print_check("Outdated Dependency Checks", False, "No update checks found")
                
            if 'pip' in content and 'outdated' in content:
                self.print_check("Python Update Checks", True)
            else:
                all_passed = self.print_check("Python Update Checks", False, "No pip outdated check")
                
            if 'npm' in content and 'outdated' in content:
                self.print_check("JavaScript Update Checks", True)
            else:
                self.print_check("JavaScript Update Checks", False, "No npm outdated check")
        
        # Check requirements.txt files
        req_files = ['requirements.txt', 'requirements_complete.txt', 'emergency_requirements.txt']
        for req_file in req_files:
            req_path = Path(req_file)
            if req_path.exists():
                self.print_check(f"{req_file}", True)
            
        # Check scraper package.json
        scraper_package = Path('scraper/package.json')
        if scraper_package.exists():
            self.print_check("Scraper package.json", True)
        else:
            all_passed = self.print_check("Scraper package.json", False, "package.json not found")
        
        self.results["dependency_checks"] = all_passed
        return all_passed
        
    def test_docker_compose_syntax(self) -> bool:
        """Test Docker Compose file syntax"""
        self.print_header("DOCKER COMPOSE SYNTAX VALIDATION")
        
        all_passed = True
        compose_files = list(Path('.').glob('docker-compose*.yml'))
        
        for compose_file in compose_files:
            try:
                result = subprocess.run(
                    ['docker-compose', '-f', str(compose_file), 'config'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    self.print_check(f"{compose_file.name} Syntax", True)
                else:
                    all_passed = self.print_check(
                        f"{compose_file.name} Syntax", 
                        False, 
                        f"Syntax error: {result.stderr[:100]}..."
                    )
                    
            except subprocess.TimeoutExpired:
                all_passed = self.print_check(f"{compose_file.name} Syntax", False, "Timeout during validation")
            except FileNotFoundError:
                self.print_check(f"{compose_file.name} Syntax", False, "docker-compose not available")
                
        return all_passed
        
    def generate_summary_report(self) -> Dict:
        """Generate a comprehensive summary report"""
        self.print_header("VALIDATION SUMMARY REPORT")
        
        # Count successful validations
        total_checks = 0
        passed_checks = 0
        
        for category, result in self.results.items():
            if category != "overall_status":
                total_checks += 1
                if result:
                    passed_checks += 1
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Determine overall status
        if success_rate >= 90:
            overall_status = "EXCELLENT"
            status_emoji = "🎉"
        elif success_rate >= 75:
            overall_status = "GOOD"
            status_emoji = "✅"
        elif success_rate >= 50:
            overall_status = "NEEDS_IMPROVEMENT"
            status_emoji = "⚠️"
        else:
            overall_status = "CRITICAL_ISSUES"
            status_emoji = "❌"
        
        self.results["overall_status"] = overall_status
        
        print(f"\n{status_emoji} Overall Status: {overall_status}")
        print(f"📊 Success Rate: {success_rate:.1f}% ({passed_checks}/{total_checks})")
        
        # Detailed breakdown
        print(f"\n📋 Category Breakdown:")
        category_names = {
            "port_fixes": "Port Standardization",
            "docker_optimizations": "Docker Optimizations", 
            "security_checks": "Security Enforcement",
            "linting_checks": "Linting Integration",
            "dependency_checks": "Dependency Management"
        }
        
        for category, result in self.results.items():
            if category != "overall_status":
                emoji = "✅" if result else "❌"
                name = category_names.get(category, category)
                print(f"   {emoji} {name}")
        
        # Save detailed report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "validation_results": self.results,
            "success_rate": success_rate,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }
        
        report_file = Path("validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return report
        
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("🚀 Starting Comprehensive Fix Validation")
        print("This will validate all the improvements from the analysis report")
        
        # Run all validation categories
        validations = [
            self.validate_port_standardization,
            self.validate_docker_optimizations,
            self.validate_security_enforcement,
            self.validate_linting_integration,
            self.validate_dependency_management,
            self.test_docker_compose_syntax
        ]
        
        all_passed = True
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Validation error: {e}")
                all_passed = False
        
        # Generate summary
        self.generate_summary_report()
        
        return all_passed

def main():
    validator = FixValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick validation - just check critical fixes
        success = validator.validate_port_standardization()
        print(f"\n{'✅' if success else '❌'} Quick validation {'PASSED' if success else 'FAILED'}")
    else:
        # Full validation
        success = validator.run_all_validations()
        
        if success:
            print(f"\n🎉 All validations PASSED! Your fixes are working correctly.")
            print("💡 The project is now optimized according to the analysis report.")
        else:
            print(f"\n⚠️ Some validations FAILED. Check the details above.")
            print("🔧 Review the failed checks and apply the necessary fixes.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
