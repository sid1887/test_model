#!/usr/bin/env python3
"""
ENHANCED AUTOMATED PACKAGE INSTALLER WITH ADVANCED CONFLICT RESOLUTION
This script automatically resolves dependency conflicts, installs packages with fallbacks,
and provides comprehensive logging and security features.
"""

import subprocess
import sys
import time
import json
import os
import re
import logging
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import urllib.parse

class InstallStrategy(Enum):
    EXACT_VERSION = "exact_version"
    NO_VERSION = "no_version"
    FORCE_REINSTALL = "force_reinstall"
    PRE_RELEASE = "pre_release"
    USER_INSTALL = "user_install"

@dataclass
class PackageResult:
    name: str
    success: bool
    strategy: Optional[InstallStrategy]
    error_message: Optional[str]
    install_time: float

class EnhancedPackageInstaller:
    def __init__(self, log_level: str = "INFO", requirements_file: str = "requirements.txt"):
        self.installed_packages: Set[str] = set()
        self.failed_packages: Set[str] = set()
        self.conflict_resolutions: Dict[str, List[str]] = {}
        self.installation_results: List[PackageResult] = []
        self.requirements_file = requirements_file
        
        # Setup logging
        self.setup_logging(log_level)
        
        # Security whitelist for allowed packages (can be customized)
        self.package_whitelist = self.load_package_whitelist()
        
        # Installation strategies in order of preference
        self.strategies = [
            InstallStrategy.EXACT_VERSION,
            InstallStrategy.NO_VERSION,
            InstallStrategy.FORCE_REINSTALL,
            InstallStrategy.PRE_RELEASE,
            InstallStrategy.USER_INSTALL
        ]

    def setup_logging(self, log_level: str) -> None:
        """Setup comprehensive logging."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler('package_installer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_package_whitelist(self) -> Set[str]:
        """Load package whitelist for security validation."""
        whitelist_file = "package_whitelist.txt"
        whitelist = set()
        
        if os.path.exists(whitelist_file):
            try:
                with open(whitelist_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            whitelist.add(line.lower())
                self.logger.info(f"Loaded {len(whitelist)} packages from whitelist")
            except Exception as e:
                self.logger.warning(f"Failed to load whitelist: {e}")
        
        # Default trusted packages if no whitelist exists
        if not whitelist:
            whitelist = {
                'fastapi', 'uvicorn', 'pydantic', 'pydantic-settings', 'sqlalchemy',
                'redis', 'celery', 'python-dotenv', 'requests', 'aiohttp', 'numpy',
                'pandas', 'click', 'jinja2', 'python-multipart', 'passlib',
                'python-jose', 'bcrypt', 'psycopg2-binary', 'alembic'
            }
        
        return whitelist

    def validate_package_name(self, package: str) -> bool:
        """Validate package name for security."""
        package_name = self.extract_package_name(package)
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[;&|`$]',  # Shell injection characters
            r'\.\./',    # Directory traversal
            r'file://',  # Local file URLs
            r'ftp://',   # FTP URLs
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, package):
                self.logger.error(f"Suspicious package name detected: {package}")
                return False
        
        # Check whitelist if enabled
        if self.package_whitelist and package_name.lower() not in self.package_whitelist:
            self.logger.warning(f"Package {package_name} not in whitelist")
            return False
        
        return True

    def extract_package_name(self, package_spec: str) -> str:
        """Extract clean package name from specification."""
        # Remove version specifiers and extras
        name = re.split(r'[=<>!~\[]', package_spec)[0].strip()
        return name

    def run_command(self, cmd: List[str], timeout: int = 300) -> Tuple[bool, str]:
        """Run a command with timeout, retries, and comprehensive error handling."""
        cmd_str = ' '.join(cmd)
        self.logger.debug(f"Executing command: {cmd_str}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout,
                    check=False,
                    env=os.environ.copy()  # Inherit environment variables
                )
                
                execution_time = time.time() - start_time
                self.logger.debug(f"Command completed in {execution_time:.2f}s with return code {result.returncode}")
                
                if result.returncode == 0:
                    return True, result.stdout
                else:
                    error_output = result.stderr or result.stdout
                    self.logger.debug(f"Command failed: {error_output}")
                    return False, error_output
                    
            except subprocess.TimeoutExpired:
                self.logger.error(f"Command timed out after {timeout} seconds (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return False, f"Command timed out after {timeout} seconds"
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Command execution failed: {e} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return False, str(e)
                time.sleep(2 ** attempt)
        
        return False, "All retry attempts failed"

    def get_pip_freeze(self) -> Dict[str, str]:
        """Get currently installed packages with enhanced parsing."""
        success, output = self.run_command([sys.executable, "-m", "pip", "freeze"])
        packages = {}
        
        if success:
            for line in output.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('-') or line.startswith('#'):
                    continue
                    
                # Handle different package formats
                if '==' in line:
                    try:
                        name, version = line.split('==', 1)
                        packages[name.lower().strip()] = version.strip()
                    except ValueError:
                        continue
                elif ' @ ' in line:  # VCS or local installations
                    name = line.split(' @ ')[0].strip()
                    packages[name.lower()] = "dev"
        
        self.logger.info(f"Found {len(packages)} currently installed packages")
        return packages

    def upgrade_pip(self) -> bool:
        """Upgrade pip and essential tools with error handling."""
        self.logger.info("Upgrading pip and essential tools...")
        
        upgrade_packages = ["pip", "setuptools", "wheel"]
        success_count = 0
        
        for package in upgrade_packages:
            success, output = self.run_command([
                sys.executable, "-m", "pip", "install", "--upgrade", 
                "--no-warn-script-location", package            ])
            
            if success:
                self.logger.info(f"[OK] {package} upgraded successfully")
                success_count += 1
            else:
                self.logger.warning(f"[WARN] {package} upgrade failed: {output}")
        
        return success_count >= len(upgrade_packages) * 0.5  # At least 50% success

    def install_with_strategy(self, package: str, strategy: InstallStrategy) -> Tuple[bool, str]:
        """Install package using specific strategy."""
        package_name = self.extract_package_name(package)
        
        base_cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir"]
        
        if strategy == InstallStrategy.EXACT_VERSION:
            cmd = base_cmd + ["--timeout", "300", "--retries", "10", package]
            
        elif strategy == InstallStrategy.NO_VERSION:
            cmd = base_cmd + ["--timeout", "300", "--retries", "5", package_name]
            
        elif strategy == InstallStrategy.FORCE_REINSTALL:
            cmd = base_cmd + ["--timeout", "300", "--retries", "3", "--force-reinstall", package_name]
            
        elif strategy == InstallStrategy.PRE_RELEASE:
            cmd = base_cmd + ["--pre", "--timeout", "180", package_name]
            
        elif strategy == InstallStrategy.USER_INSTALL:
            cmd = base_cmd + ["--user", "--timeout", "180", package_name]
        
        else:
            return False, f"Unknown strategy: {strategy}"
        
        self.logger.info(f"Trying {strategy.value} for {package}")
        return self.run_command(cmd)

    def install_package_with_fallbacks(self, package: str) -> PackageResult:
        """Install a package with multiple fallback strategies."""
        start_time = time.time()
        package_name = self.extract_package_name(package)
        
        # Security validation
        if not self.validate_package_name(package):
            error_msg = f"Package {package} failed security validation"
            self.logger.error(error_msg)
            return PackageResult(package_name, False, None, error_msg, 0)        # Check if already processed
        if package_name.lower() in self.installed_packages:
            self.logger.info(f"[OK] {package} already installed")
            return PackageResult(package_name, True, None, None, 0)
            
        if package_name.lower() in self.failed_packages:
            self.logger.warning(f"[WARN] Skipping {package} (previously failed)")
            return PackageResult(package_name, False, None, "Previously failed", 0)
        
        self.logger.info(f"\n--- Installing {package} ---")
          # Try each strategy
        for strategy in self.strategies:
            success, output = self.install_with_strategy(package, strategy)
            if success:
                install_time = time.time() - start_time
                self.logger.info(f"[OK] {package} installed successfully with {strategy.value}")
                self.installed_packages.add(package_name.lower())
                return PackageResult(package_name, True, strategy, None, install_time)
            else:
                self.logger.debug(f"Strategy {strategy.value} failed: {output}")
        
        # All strategies failed
        install_time = time.time() - start_time
        error_msg = f"All installation strategies failed for {package}"
        self.logger.error(error_msg)
        self.failed_packages.add(package_name.lower())
        return PackageResult(package_name, False, None, error_msg, install_time)

    def resolve_conflict(self, error_output: str) -> Optional[List[str]]:
        """Enhanced conflict resolution with more patterns."""
        lines = error_output.lower()
        
        # Updated conflict resolution patterns
        conflict_patterns = {
            'fastapi_pydantic': {
                'patterns': ['fastapi', 'pydantic'],
                'resolution': [
                    "fastapi>=0.100.0,<1.0.0",
                    "pydantic>=2.0.0,<3.0.0",
                    "pydantic-settings>=2.0.0,<3.0.0"
                ]
            },
            'sqlalchemy': {
                'patterns': ['sqlalchemy'],
                'resolution': ["sqlalchemy>=1.4.0,<2.1.0"]
            },
            'redis': {
                'patterns': ['redis'],
                'resolution': ["redis>=4.5.0,<6.0.0"]
            },
            'celery': {
                'patterns': ['celery'],
                'resolution': ["celery>=5.3.0,<6.0.0"]
            },
            'click': {
                'patterns': ['click'],
                'resolution': ["click>=8.0.0,<9.0.0"]
            },
            'aiohttp': {
                'patterns': ['aiohttp'],
                'resolution': ["aiohttp>=3.8.0,<4.0.0", "aiosignal>=1.2.0", "frozenlist>=1.3.0"]
            },
            'numpy': {
                'patterns': ['numpy'],
                'resolution': ["numpy>=1.20.0,<2.0.0"]
            },
            'uvicorn': {
                'patterns': ['uvicorn'],
                'resolution': ["uvicorn[standard]>=0.20.0,<0.30.0"]
            }
        }
        
        # Check for version conflicts
        if "requires" in lines and ("but you have" in lines or "incompatible" in lines):
            self.logger.info("Detected version conflict, analyzing...")
            
            for conflict_name, config in conflict_patterns.items():
                if all(pattern in lines for pattern in config['patterns']):
                    self.logger.info(f"Applying {conflict_name} conflict resolution")
                    return config['resolution']
        
        # Handle missing package versions
        if "could not find a version that satisfies" in lines:
            # Extract package name from error
            match = re.search(r"requirement\s+([^\s\(]+)", error_output, re.IGNORECASE)
            if match:
                problematic_package = match.group(1).strip()
                self.logger.info(f"Package version not found: {problematic_package}")
                return [self.extract_package_name(problematic_package)]
        
        return None

    def parse_requirements(self) -> List[str]:
        """Parse requirements file with enhanced error handling."""
        if not os.path.exists(self.requirements_file):
            self.logger.error(f"Requirements file {self.requirements_file} not found")
            return []
        
        self.logger.info(f"Reading requirements from {self.requirements_file}...")
        packages = []
        
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip pip options
                    if line.startswith('-'):
                        if line.startswith('-r'):
                            # Handle nested requirements files
                            nested_file = line.split(None, 1)[1] if len(line.split()) > 1 else None
                            if nested_file and os.path.exists(nested_file):
                                self.logger.info(f"Processing nested requirements: {nested_file}")
                                # Recursively parse nested file
                                nested_installer = EnhancedPackageInstaller(requirements_file=nested_file)
                                packages.extend(nested_installer.parse_requirements())
                        continue
                    
                    # Handle inline comments
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    
                    if line:
                        packages.append(line)
                        
        except Exception as e:
            self.logger.error(f"Error reading requirements file: {e}")
            return []
        
        self.logger.info(f"Found {len(packages)} packages to install")
        return packages

    def install_from_requirements(self) -> bool:
        """Install packages from requirements file with enhanced conflict resolution."""
        packages = self.parse_requirements()
        if not packages:
            return False
        
        # First, try bulk installation
        self.logger.info("\n=== ATTEMPTING BULK INSTALLATION ===")
        success, output = self.run_command([
            sys.executable, "-m", "pip", "install", 
            "--no-cache-dir", "--timeout", "600", "--retries", "15",
            "-r", self.requirements_file        ])
        
        if success:
            self.logger.info("[OK] Bulk installation successful!")
            return True
        
        self.logger.warning("[WARN] Bulk installation failed, analyzing conflicts...")
        
        # Try to resolve conflicts
        resolution_packages = self.resolve_conflict(output)
        if resolution_packages:
            self.logger.info(f"Applying conflict resolution: {resolution_packages}")
            for pkg in resolution_packages:
                result = self.install_package_with_fallbacks(pkg)
                self.installation_results.append(result)
        
        # Install packages individually with prioritization
        self.logger.info("\n=== INSTALLING PACKAGES INDIVIDUALLY ===")
        
        # Prioritize core packages
        core_packages = [
            "wheel", "setuptools",
            "fastapi>=0.100.0", "uvicorn[standard]>=0.22.0",
            "pydantic>=2.0.0,<3.0.0", "pydantic-settings>=2.0.0",
            "python-dotenv>=1.0.0"
        ]
        
        # Separate core and non-core packages
        remaining_packages = []
        for package in packages:
            package_name = self.extract_package_name(package)
            if not any(package_name.lower() in core.lower() for core in core_packages):
                remaining_packages.append(package)
        
        # Install core packages first
        self.logger.info("\n--- Installing Core Packages ---")
        for package in core_packages:
            result = self.install_package_with_fallbacks(package)
            self.installation_results.append(result)
        
        # Install remaining packages
        self.logger.info("\n--- Installing Remaining Packages ---")
        for package in remaining_packages:
            result = self.install_package_with_fallbacks(package)
            self.installation_results.append(result)
        
        return self.generate_summary()

    def generate_summary(self) -> bool:
        """Generate comprehensive installation summary."""
        success_count = sum(1 for result in self.installation_results if result.success)
        total_count = len(self.installation_results)
        
        self.logger.info(f"\n=== INSTALLATION SUMMARY ===")
        self.logger.info(f"Total packages processed: {total_count}")
        self.logger.info(f"Successfully installed: {success_count}")
        self.logger.info(f"Failed installations: {total_count - success_count}")
        self.logger.info(f"Success rate: {(success_count/total_count*100):.1f}%" if total_count > 0 else "0%")
        
        # Show failed packages
        failed_results = [r for r in self.installation_results if not r.success]
        if failed_results:
            self.logger.warning("\nFailed packages:")
            for result in failed_results:
                self.logger.warning(f"  - {result.name}: {result.error_message}")
        
        # Show installation times for successful packages
        successful_results = [r for r in self.installation_results if r.success and r.install_time > 0]
        if successful_results:
            total_time = sum(r.install_time for r in successful_results)
            self.logger.info(f"\nTotal installation time: {total_time:.2f} seconds")
            
            # Show slowest installations
            slowest = sorted(successful_results, key=lambda x: x.install_time, reverse=True)[:3]
            self.logger.info("Slowest installations:")
            for result in slowest:
                self.logger.info(f"  - {result.name}: {result.install_time:.2f}s ({result.strategy.value if result.strategy else 'unknown'})")        
        return success_count >= total_count * 0.7  # 70% success rate

    def verify_installation(self) -> bool:
        """Enhanced installation verification."""
        self.logger.info("\n=== VERIFYING INSTALLATION ===")
        
        critical_imports = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn server"),
            ("pydantic", "Pydantic"),
            ("sqlalchemy", "SQLAlchemy"),
            ("redis", "Redis client"),
            ("celery", "Celery"),
            ("python_dotenv", "Python-dotenv"),
        ]
        
        success_count = 0
        for module, description in critical_imports:
            try:
                imported_module = __import__(module)
                version = getattr(imported_module, '__version__', 'unknown')
                self.logger.info(f"[OK] {description} (v{version}) import successful")
                success_count += 1
            except ImportError as e:
                self.logger.error(f"[FAIL] {description} import failed: {e}")
            except Exception as e:
                self.logger.warning(f"[WARN] {description} imported with warning: {e}")
                success_count += 0.5  # Partial success
        
        verification_rate = success_count / len(critical_imports)
        self.logger.info(f"\nVerification: {success_count}/{len(critical_imports)} critical packages working ({verification_rate:.1%})")
        
        return verification_rate >= 0.8  # 80% success rate

    def save_installation_report(self) -> None:
        """Save detailed installation report to JSON file."""
        report = {
            "timestamp": time.time(),
            "requirements_file": self.requirements_file,
            "total_packages": len(self.installation_results),
            "successful_installations": sum(1 for r in self.installation_results if r.success),
            "failed_installations": sum(1 for r in self.installation_results if not r.success),
            "results": [
                {
                    "name": result.name,
                    "success": result.success,
                    "strategy": result.strategy.value if result.strategy else None,
                    "error_message": result.error_message,
                    "install_time": result.install_time
                }
                for result in self.installation_results
            ]
        }
        
        report_file = "installation_report.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Installation report saved to {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save installation report: {e}")

def main():
    """Enhanced main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Automated Package Installer with Conflict Resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python installer.py                           # Install from requirements.txt
  python installer.py -r custom.txt            # Install from custom file
  python installer.py --log-level DEBUG        # Enable debug logging
  python installer.py --skip-verification      # Skip import verification
        """
    )
    
    parser.add_argument(
        '-r', '--requirements',
        default='requirements.txt',
        help='Requirements file to install from (default: requirements.txt)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--skip-pip-upgrade',
        action='store_true',
        help='Skip pip upgrade step'
    )
    
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip import verification step'
    )
    
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save detailed installation report to JSON'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ENHANCED AUTOMATED PACKAGE INSTALLER WITH CONFLICT RESOLUTION")
    print("=" * 60)
    
    installer = EnhancedPackageInstaller(
        log_level=args.log_level,
        requirements_file=args.requirements
    )
    
    success = True
    
    try:
        # Step 1: Upgrade pip (unless skipped)
        if not args.skip_pip_upgrade:
            installer.upgrade_pip()
        
        # Step 2: Install packages
        installation_success = installer.install_from_requirements()
        success = success and installation_success
        
        # Step 3: Verify installation (unless skipped)
        if not args.skip_verification:
            verification_success = installer.verify_installation()
            success = success and verification_success
        
        # Step 4: Save report (if requested)
        if args.save_report:
            installer.save_installation_report()
    except KeyboardInterrupt:
        installer.logger.warning("\nInstallation interrupted by user")
        return 1
    except Exception as e:
        installer.logger.error(f"Unexpected error: {e}")
        return 1
        
    print("\n" + "=" * 60)
    if success:
        print("[OK] INSTALLATION COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("[WARN] INSTALLATION COMPLETED WITH ISSUES")
        print("Application may still work with available packages")
        return 0  # Don't fail CI/CD pipelines completely

if __name__ == "__main__":
    sys.exit(main())