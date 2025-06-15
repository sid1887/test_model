#!/usr/bin/env python3
"""
Pre-flight Dependency Check for Cumpair AI System
This script ensures all required packages are installed before the main application starts.
"""

import importlib
import subprocess
import sys
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PreFlightChecker:
    """Pre-flight dependency checker and auto-installer"""
    
    def __init__(self):
        self.failed_packages = []
        self.installed_packages = []
        self.critical_failures = []
        
        # Core packages that are absolutely required
        self.CRITICAL_PACKAGES = [
            "fastapi",
            "uvicorn", 
            "pydantic",
            "sqlalchemy",
            "asyncpg",
            "redis",
            "celery",
            "numpy",
            "pillow"
        ]
        
        # AI/ML packages with special handling
        self.AI_PACKAGES = [
            "torch",
            "torchvision", 
            "ultralytics",
            "opencv-python",
            "transformers",
            "sentence-transformers",
            "clip-by-openai",  # Special case
            "faiss-cpu",
            "scikit-learn"
        ]
        
        # Web scraping packages
        self.SCRAPING_PACKAGES = [
            "scrapy",
            "playwright", 
            "requests",
            "aiohttp",
            "beautifulsoup4",
            "selenium",
            "fake-useragent"
        ]
        
        # Database packages
        self.DATABASE_PACKAGES = [
            "alembic",
            "psycopg2-binary"
        ]
        
        # Additional utility packages
        self.UTILITY_PACKAGES = [
            "python-multipart",
            "aiofiles",
            "httpx",
            "prometheus-client",
            "structlog",
            "pytesseract"
        ]    def safe_import_check(self, package_name: str, import_name: Optional[str] = None) -> bool:
        """Safely check if a package can be imported"""
        try:
            module_name = import_name or package_name.replace("-", "_").lower()
            
            # Handle special import name mappings
            import_mappings = {
                "pillow": "PIL",
                "opencv-python": "cv2",
                "opencv-python-headless": "cv2",
                "scikit-learn": "sklearn",
                "beautifulsoup4": "bs4",
                "python-multipart": "multipart",
                "pydantic-settings": "pydantic_settings",
                "python-jose": "jose",
                "psycopg2-binary": "psycopg2",
                "clip-by-openai": "clip"
            }
            
            if package_name in import_mappings:
                module_name = import_mappings[package_name]
            
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking {package_name}: {e}")
            return False    def safe_auto_install(self, package_name: str, import_name: Optional[str] = None) -> bool:
        """Safely install a package with error handling"""
        logger.info(f"⚠️ '{package_name}' not found. Installing safely...")
        
        try:
            # Check if already installed first using the corrected import check
            if self.safe_import_check(package_name, import_name):
                logger.info(f"✅ '{package_name}' is already available")
                return True
            
            # Install the package
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name, "--no-cache-dir"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify installation by trying to import with corrected check
                if self.safe_import_check(package_name, import_name):
                    logger.info(f"✅ Successfully installed and verified '{package_name}'")
                    self.installed_packages.append(package_name)
                    return True
                else:
                    logger.error(f"❌ Package '{package_name}' installed but cannot be imported")
                    return False
            else:
                logger.error(f"❌ Failed to install '{package_name}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Installation of '{package_name}' timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to install '{package_name}': {e}")
            return False

    def check_special_packages(self) -> bool:
        """Handle special cases for packages with different import names"""
        special_cases = {
            "opencv-python": "cv2",
            "opencv-python-headless": "cv2", 
            "pillow": "PIL",
            "scikit-learn": "sklearn",
            "beautifulsoup4": "bs4",
            "python-multipart": "multipart",
            "uvicorn[standard]": "uvicorn",
            "pydantic-settings": "pydantic_settings",
            "python-jose[cryptography]": "jose",
            "passlib[bcrypt]": "passlib",
            "psycopg2-binary": "psycopg2"
        }
        
        all_success = True
        
        for package, import_name in special_cases.items():
            if not self.safe_import_check(package, import_name):
                # For packages with extras, try the base package first
                base_package = package.split('[')[0]
                if not self.safe_auto_install(base_package, import_name):
                    all_success = False
                    self.failed_packages.append(package)
        
        return all_success

    def check_clip_installation(self) -> bool:
        """Special handling for CLIP which requires git installation"""
        logger.info("🔗 Checking CLIP installation...")
        
        try:
            import clip
            logger.info("✅ CLIP is already installed")
            return True
        except ImportError:
            logger.info("⚠️ CLIP not found. Installing from GitHub...")
            
            try:
                # Install CLIP from GitHub
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "git+https://github.com/openai/CLIP.git",
                    "--no-cache-dir"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    # Verify installation
                    try:
                        import clip
                        logger.info("✅ Successfully installed CLIP")
                        self.installed_packages.append("clip")
                        return True
                    except ImportError:
                        logger.error("❌ CLIP installed but cannot be imported")
                        return False
                else:
                    logger.error(f"❌ Failed to install CLIP: {result.stderr}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to install CLIP: {e}")
                return False

    def check_pytorch_installation(self) -> bool:
        """Special handling for PyTorch installation"""
        logger.info("🔥 Checking PyTorch installation...")
        
        try:
            import torch
            import torchvision
            logger.info(f"✅ PyTorch {torch.__version__} is already installed")
            return True
        except ImportError:
            logger.info("⚠️ PyTorch not found. Installing CPU version...")
            
            try:
                # Install CPU version of PyTorch (more reliable than CUDA for general use)
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "torch", "torchvision", "torchaudio", "--index-url", 
                    "https://download.pytorch.org/whl/cpu",
                    "--no-cache-dir"
                ], capture_output=True, text=True, timeout=600)  # 10 minute timeout for PyTorch
                
                if result.returncode == 0:
                    try:
                        import torch
                        logger.info(f"✅ Successfully installed PyTorch {torch.__version__}")
                        self.installed_packages.extend(["torch", "torchvision"])
                        return True
                    except ImportError:
                        logger.error("❌ PyTorch installed but cannot be imported")
                        return False
                else:
                    logger.error(f"❌ Failed to install PyTorch: {result.stderr}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to install PyTorch: {e}")
                return False

    def check_package_list(self, packages: List[str], category: str) -> bool:
        """Check and install a list of packages"""
        logger.info(f"📦 Checking {category} packages...")
        
        all_success = True
        for package in packages:
            if not self.safe_import_check(package):
                if not self.safe_auto_install(package):
                    all_success = False
                    self.failed_packages.append(package)
                    if package in self.CRITICAL_PACKAGES:
                        self.critical_failures.append(package)
        
        return all_success

    def check_system_dependencies(self) -> bool:
        """Check for system-level dependencies"""
        logger.info("🔧 Checking system dependencies...")
        
        # Check if we're in a Docker container or have the necessary system libs
        system_checks = []
        
        try:
            # Check if Tesseract is available (for OCR)
            result = subprocess.run(["tesseract", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Tesseract OCR is available")
            else:
                logger.warning("⚠️ Tesseract OCR not found - some features may be limited")
        except:
            logger.warning("⚠️ Tesseract OCR not found - some features may be limited")
        
        return True

    def create_emergency_requirements(self) -> None:
        """Create an emergency requirements file for manual installation"""
        if self.failed_packages:
            emergency_file = Path("emergency_requirements.txt")
            with open(emergency_file, "w") as f:
                f.write("# Emergency requirements file - packages that failed auto-installation\n")
                f.write("# Install manually with: pip install -r emergency_requirements.txt\n\n")
                for package in self.failed_packages:
                    f.write(f"{package}\n")
            
            logger.info(f"📝 Created emergency requirements file: {emergency_file}")

    def run_complete_check(self) -> bool:
        """Run the complete pre-flight check"""
        logger.info("🚀 Starting Cumpair Pre-flight Dependency Check...")
        logger.info("=" * 60)
        
        success = True
        
        # 1. Check critical packages first
        if not self.check_package_list(self.CRITICAL_PACKAGES, "Critical"):
            success = False
        
        # 2. Check PyTorch (special handling)
        if not self.check_pytorch_installation():
            success = False
        
        # 3. Check CLIP (special handling) 
        if not self.check_clip_installation():
            success = False
        
        # 4. Check other AI packages
        remaining_ai = [pkg for pkg in self.AI_PACKAGES if pkg not in ["torch", "torchvision"]]
        if not self.check_package_list(remaining_ai, "AI/ML"):
            success = False
        
        # 5. Check database packages
        if not self.check_package_list(self.DATABASE_PACKAGES, "Database"):
            success = False
        
        # 6. Check scraping packages
        if not self.check_package_list(self.SCRAPING_PACKAGES, "Web Scraping"):
            success = False
        
        # 7. Check utility packages
        if not self.check_package_list(self.UTILITY_PACKAGES, "Utility"):
            success = False
        
        # 8. Check special cases
        if not self.check_special_packages():
            success = False
        
        # 9. System dependencies
        self.check_system_dependencies()
        
        # Final report
        logger.info("=" * 60)
        logger.info("📊 Pre-flight Check Summary:")
        
        if self.installed_packages:
            logger.info(f"✅ Successfully installed: {len(self.installed_packages)} packages")
            for pkg in self.installed_packages:
                logger.info(f"   ➕ {pkg}")
        
        if self.failed_packages:
            logger.error(f"❌ Failed to install: {len(self.failed_packages)} packages")
            for pkg in self.failed_packages:
                logger.error(f"   ❌ {pkg}")
            self.create_emergency_requirements()
        
        if self.critical_failures:
            logger.error("🚨 CRITICAL FAILURES - Application may not start:")
            for pkg in self.critical_failures:
                logger.error(f"   🚨 {pkg}")
            return False
        
        if success:
            logger.info("🎉 All dependencies satisfied! Starting application...")
        else:
            logger.warning("⚠️ Some non-critical packages failed, but application should still work")
        
        return not bool(self.critical_failures)  # Return True if no critical failures


    def check_requirements_files(self) -> bool:
        """Check and install from requirements files if they exist"""
        logger.info("📄 Checking requirements files...")
        
        requirements_files = [
            "requirements.txt",
            "requirements_complete.txt"
        ]
        
        success = True
        for req_file in requirements_files:
            req_path = Path(req_file)
            if req_path.exists():
                logger.info(f"📦 Found {req_file}, checking packages...")
                try:
                    with open(req_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Parse requirements file
                    packages = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            # Handle git URLs and version specifiers
                            if line.startswith('git+'):
                                # Skip git packages for now, handle separately
                                continue
                            elif '==' in line:
                                package = line.split('==')[0]
                                packages.append(package)
                            elif '>=' in line:
                                package = line.split('>=')[0]
                                packages.append(package)
                            else:
                                packages.append(line)
                    
                    # Check only first 20 packages to avoid overwhelming output
                    sample_packages = packages[:20]
                    missing_count = 0
                    
                    for package in sample_packages:
                        if not self.safe_import_check(package):
                            missing_count += 1
                    
                    logger.info(f"📊 Requirements file {req_file}: {len(packages)} total packages, ~{missing_count} missing from sample")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not process {req_file}: {e}")
                    
        return success

    def generate_health_report(self) -> Dict:
        """Generate a comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "installed_packages": self.installed_packages,
            "failed_packages": self.failed_packages,
            "critical_failures": self.critical_failures,
            "total_checks": len(self.CRITICAL_PACKAGES) + len(self.AI_PACKAGES) + 
                          len(self.SCRAPING_PACKAGES) + len(self.DATABASE_PACKAGES) + len(self.UTILITY_PACKAGES),
            "success_rate": 0
        }
        
        total_attempted = len(self.installed_packages) + len(self.failed_packages)
        if total_attempted > 0:
            report["success_rate"] = len(self.installed_packages) / total_attempted * 100
        
        # Save report to file
        report_path = Path("pre_flight_health_report.json")
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📋 Health report saved to: {report_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save health report: {e}")
        
        return report

def main():
    """Main entry point for pre-flight check"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cumpair Pre-flight Dependency Check")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--force", action="store_true", help="Force reinstallation of packages")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional packages")
    parser.add_argument("--quick", action="store_true", help="Quick check of critical packages only")
    parser.add_argument("--docker", action="store_true", help="Running in Docker container")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    checker = PreFlightChecker()
    
    try:
        logger.info("🚀 Starting Cumpair Pre-flight Dependency Check...")
        
        if args.docker:
            logger.info("🐳 Running in Docker mode")
        
        if args.quick:
            logger.info("⚡ Quick check mode - critical packages only")
            success = checker.check_package_list(checker.CRITICAL_PACKAGES, "Critical")
        else:
            success = checker.run_complete_check()
            
            # Additional checks
            checker.check_requirements_files()
            
            # Generate health report
            report = checker.generate_health_report()
            logger.info(f"📊 Success rate: {report['success_rate']:.1f}%")
        
        if success:
            logger.info("✅ Pre-flight check completed successfully!")
            logger.info("🎉 All critical dependencies are satisfied!")
            logger.info("💡 You can now start the application safely.")
            sys.exit(0)
        else:
            logger.error("❌ Pre-flight check failed with critical errors!")
            logger.error("🚨 Critical packages are missing - application may not start properly.")
            logger.error("💡 Please check the emergency_requirements.txt file for manual installation.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Pre-flight check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error during pre-flight check: {e}")
        logger.error("📞 Please report this error with the full traceback")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
