#!/usr/bin/env python3
"""
Universal Package Installer for Docker Containers
Automatically installs missing Python packages at runtime
"""

import subprocess
import sys
import importlib
import logging
import os
from typing import List, Dict, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversalPackageInstaller:
    """Universal package installer for all containers"""
    
    def __init__(self):
        self.installed_packages = set()
        self.failed_packages = set()
        
    def check_package(self, package_name: str, import_name: Optional[str] = None) -> bool:
        """Check if a package is installed and importable"""
        try:
            if import_name:
                importlib.import_module(import_name)
            else:
                importlib.import_module(package_name)
            return True
        except ImportError:
            return False
            
    def install_package(self, package_name: str) -> bool:
        """Install a single package using pip"""
        try:
            logger.info(f"Installing package: {package_name}")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed: {package_name}")
                self.installed_packages.add(package_name)
                return True
            else:
                logger.error(f"Failed to install {package_name}: {result.stderr}")
                self.failed_packages.add(package_name)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing {package_name}")
            self.failed_packages.add(package_name)
            return False
        except Exception as e:
            logger.error(f"Error installing {package_name}: {e}")
            self.failed_packages.add(package_name)
            return False
            
    def install_packages_from_list(self, packages: List[str]) -> Dict[str, bool]:
        """Install multiple packages from a list"""
        results = {}
        for package in packages:
            results[package] = self.install_package(package)
            time.sleep(1)  # Small delay between installations
        return results
        
    def install_from_requirements(self, requirements_file: str = "requirements.txt") -> bool:
        """Install packages from requirements file"""
        if not os.path.exists(requirements_file):
            logger.warning(f"Requirements file not found: {requirements_file}")
            return False
            
        try:
            logger.info(f"Installing from {requirements_file}")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed from {requirements_file}")
                return True
            else:
                logger.error(f"Failed to install from {requirements_file}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing from {requirements_file}: {e}")
            return False
            
    def install_service_specific_packages(self, service_name: str) -> bool:
        """Install packages specific to a service"""
        service_packages = {
            'web': [
                'fastapi[all]', 'uvicorn[standard]', 'sqlalchemy', 'alembic',
                'psycopg2-binary', 'redis', 'celery', 'structlog', 'prometheus_client',
                'requests', 'beautifulsoup4', 'pandas', 'numpy', 'scikit-learn',
                'transformers', 'sentence-transformers', 'torch', 'torchvision',
                'opencv-python-headless', 'Pillow', 'python-multipart', 'python-jose[cryptography]',
                'passlib[bcrypt]'
            ],
            'worker': [
                'celery[redis]', 'requests', 'beautifulsoup4', 'pandas', 'numpy',
                'scikit-learn', 'transformers', 'sentence-transformers', 'torch',
                'torchvision', 'opencv-python-headless', 'Pillow', 'sqlalchemy',
                'psycopg2-binary', 'structlog', 'prometheus_client'
            ],
            'flower': [
                'flower', 'celery[redis]', 'prometheus_client', 'structlog'
            ],
            'scraper': [
                'requests', 'beautifulsoup4', 'selenium', 'scrapy', 'pandas',
                'numpy', 'structlog', 'prometheus_client'
            ],
            'proxy': [
                'requests', 'aiohttp', 'structlog', 'prometheus_client'
            ],
            'captcha': [
                'fastapi[all]', 'uvicorn[standard]', 'opencv-python-headless',
                'Pillow', 'numpy', 'structlog', 'prometheus_client'
            ]
        }
        
        packages = service_packages.get(service_name.lower(), [])
        if not packages:
            logger.info(f"No specific packages defined for service: {service_name}")
            return True
            
        logger.info(f"Installing {len(packages)} packages for service: {service_name}")
        results = self.install_packages_from_list(packages)
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Successfully installed {success_count}/{len(packages)} packages for {service_name}")
        
        return success_count > len(packages) * 0.8  # 80% success rate
        
    def upgrade_pip(self) -> bool:
        """Upgrade pip to latest version"""
        try:
            logger.info("Upgrading pip...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Successfully upgraded pip")
                return True
            else:
                logger.warning(f"Failed to upgrade pip: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"Error upgrading pip: {e}")
            return False
            
    def run_installation(self, service_name: str = None, requirements_file: str = None) -> bool:
        """Run complete installation process"""
        logger.info(f"🚀 Starting universal package installation for service: {service_name or 'unknown'}")
        
        # Upgrade pip first
        self.upgrade_pip()
        
        success = True
        
        # Install from requirements file if provided
        if requirements_file and os.path.exists(requirements_file):
            if not self.install_from_requirements(requirements_file):
                success = False
                
        # Install service-specific packages
        if service_name:
            if not self.install_service_specific_packages(service_name):
                success = False
                
        # Report results
        logger.info(f"📦 Installation complete!")
        logger.info(f"✅ Successfully installed: {len(self.installed_packages)} packages")
        if self.failed_packages:
            logger.warning(f"❌ Failed to install: {len(self.failed_packages)} packages")
            logger.warning(f"Failed packages: {', '.join(self.failed_packages)}")
            
        return success

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Package Installer')
    parser.add_argument('--service', help='Service name (web, worker, flower, etc.)')
    parser.add_argument('--requirements', help='Requirements file path')
    parser.add_argument('--packages', nargs='+', help='Specific packages to install')
    
    args = parser.parse_args()
    
    installer = UniversalPackageInstaller()
    
    # Install specific packages if provided
    if args.packages:
        results = installer.install_packages_from_list(args.packages)
        success = all(results.values())
    else:
        success = installer.run_installation(
            service_name=args.service,
            requirements_file=args.requirements
        )
    
    if success:
        logger.info("🎉 All installations completed successfully!")
        sys.exit(0)
    else:
        logger.error("⚠️ Some installations failed, but continuing...")
        sys.exit(0)  # Don't fail the container startup

if __name__ == "__main__":
    main()
