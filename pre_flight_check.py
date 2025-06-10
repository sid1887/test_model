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
from datetime import datetime

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
            "Pillow"  # Note: capital P for Pillow
        ]
        
        # AI/ML packages with special handling
        self.AI_PACKAGES = [
            "torch",
            "torchvision", 
            "ultralytics",
            "opencv-python",
            "transformers",
            "sentence-transformers",
            "faiss-cpu",
            "scikit-learn"        ]
        
        # Package import name mappings
        self.IMPORT_MAPPINGS = {
            "Pillow": "PIL",
            "pillow": "PIL", 
            "opencv-python": "cv2",
            "opencv-python-headless": "cv2",
            "scikit-learn": "sklearn",
            "beautifulsoup4": "bs4",
            "python-multipart": "multipart",
            "pydantic-settings": "pydantic_settings",
            "python-jose": "jose",
            "psycopg2-binary": "psycopg2",            "faiss-cpu": "faiss",
            "faiss-gpu": "faiss"
        }

    def safe_import_check(self, package_name: str) -> bool:
        """Safely check if a package can be imported"""
        try:
            # Use mapping if available, otherwise convert package name
            import_name = self.IMPORT_MAPPINGS.get(package_name, package_name.replace("-", "_").lower())
            
            # Special handling for problematic packages
            if package_name in ["faiss-cpu", "faiss-gpu"]:
                return self._check_faiss_import()
            
            importlib.import_module(import_name)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking {package_name}: {e}")
            return False

    def _check_faiss_import(self) -> bool:
        """Special check for faiss which can have circular import issues"""
        try:
            import faiss
            # Try to use faiss to ensure it's actually working
            faiss.IndexFlatL2(10)
            return True
        except Exception as e:
            logger.warning(f"faiss import failed: {e}")
            return False

    def safe_auto_install(self, package_name: str) -> bool:
        """Safely install a package with error handling"""
        logger.info(f"⚠️ '{package_name}' not found. Installing safely...")
        
        try:
            # Check if already installed first
            if self.safe_import_check(package_name):
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
                # Verify installation by trying to import
                if self.safe_import_check(package_name):
                    logger.info(f"✅ Successfully installed and verified '{package_name}'")
                    self.installed_packages.append(package_name)
                    return True
                else:
                    logger.warning(f"⚠️ Package '{package_name}' installed but cannot be imported - may be corrupted")
                    # Try to fix corrupted installation
                    if self.handle_corrupted_package(package_name):
                        logger.info(f"✅ Successfully fixed and verified '{package_name}'")
                        self.installed_packages.append(package_name)
                        return True
                    else:
                        logger.error(f"❌ Could not fix corrupted '{package_name}' installation")
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

    def handle_corrupted_package(self, package_name: str) -> bool:
        """Handle corrupted package installations by attempting reinstallation"""
        logger.info(f"🔧 Attempting to fix corrupted '{package_name}' installation...")
        
        try:
            # First, try to uninstall the corrupted package
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", package_name, "-y"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info(f"🗑️ Uninstalled corrupted '{package_name}'")
                
                # Now reinstall it
                return self.safe_auto_install(package_name)
            else:
                logger.warning(f"⚠️ Could not uninstall '{package_name}': {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to fix corrupted '{package_name}': {e}")
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
                    "torch", "torchvision", "--index-url", 
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

    def generate_health_report(self) -> Dict:
        """Generate a comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "installed_packages": self.installed_packages,
            "failed_packages": self.failed_packages,
            "critical_failures": self.critical_failures,
            "total_checks": len(self.CRITICAL_PACKAGES) + len(self.AI_PACKAGES),
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


def main():
    """Main entry point for pre-flight check"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cumpair Pre-flight Dependency Check")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--force", action="store_true", help="Force reinstallation of packages")
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
