#!/usr/bin/env python3
"""
Enhanced Startup Script for Cumpair AI System
This script runs pre-flight checks and then starts the application
"""

import sys
import os
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pre_flight_check import PreFlightChecker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CumpairStartup:
    """Enhanced startup manager for Cumpair"""
    
    def __init__(self):
        self.pre_flight_passed = False
        self.startup_mode = "production"
        
    def run_pre_flight_check(self, quick_mode: bool = False) -> bool:
        """Run pre-flight dependency check"""
        logger.info("Running pre-flight dependency check...")
        
        try:
            checker = PreFlightChecker()
            
            if quick_mode:
                # Quick check - only critical packages
                success = checker.check_package_list(checker.CRITICAL_PACKAGES, "Critical")
                if success:
                    # Also check PyTorch and CLIP as they're essential for AI features
                    success = success and checker.check_pytorch_installation()
                    success = success and checker.check_clip_installation()
            else:
                # Full check
                success = checker.run_complete_check()
            
            if success:
                logger.info("Pre-flight check passed!")
                self.pre_flight_passed = True
                return True
            else:
                logger.error("Pre-flight check failed!")
                if checker.critical_failures:
                    logger.error("Critical packages missing - cannot start application")
                    return False
                else:
                    logger.warning("Some packages missing but application should work")
                    self.pre_flight_passed = True
                    return True
                    
        except Exception as e:
            logger.error(f"Pre-flight check error: {e}")
            return False
    
    def check_environment(self) -> bool:
        """Check the runtime environment"""
        logger.info("Checking runtime environment...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        
        logger.info(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required directories
        required_dirs = ["models", "uploads", "app", "logs"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                logger.info(f"Creating directory: {dir_name}")
                dir_path.mkdir(exist_ok=True)
        
        # Check for main.py
        if not Path("main.py").exists():
            logger.error("main.py not found!")
            return False
        
        return True
    
    def start_application(self, development_mode: bool = False) -> None:
        """Start the main application"""
        logger.info("Starting Cumpair AI System...")
        
        try:
            if development_mode:
                logger.info("Starting in development mode with auto-reload")
                import uvicorn
                uvicorn.run(
                    "main:app",
                    host="0.0.0.0",
                    port=8000,
                    reload=True,
                    log_level="info"
                )
            else:
                logger.info("Starting in production mode")
                # Import and run the main application
                from main import app
                import uvicorn
                uvicorn.run(
                    app,
                    host="0.0.0.0", 
                    port=8000,
                    log_level="info"
                )
                
        except ImportError as e:
            logger.error(f"Failed to import main application: {e}")
            logger.error("This usually means dependencies are missing. Run pre-flight check again.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Application startup failed: {str(e)}")
            sys.exit(1)
    
    def run_startup_sequence(self, skip_preflight=False, dev_mode=False, quick_check=False):
        """Run the complete startup sequence"""
        logger.info("Cumpair AI System - Enhanced Startup")
        logger.info("==================================================")
        
        # Step 1: Check runtime environment
        logger.info("Checking runtime environment...")
        logger.info(f"Python {sys.version.split()[0]}")
        
        if not self.check_environment():
            logger.error("Environment check failed!")
            sys.exit(1)
            
        # Step 2: Run pre-flight check unless skipped
        if not skip_preflight:
            if not self.run_pre_flight_check(quick_mode=quick_check):
                logger.error("Pre-flight check failed!")
                sys.exit(1)
        else:
            logger.warning("Skipping pre-flight check (not recommended)")
            
        # Step 3: Start application
        logger.info("All checks passed! Starting application...")
        self.start_application(development_mode=dev_mode)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cumpair AI System Enhanced Startup")
    parser.add_argument("--skip-preflight", action="store_true", 
                       help="Skip pre-flight dependency check")
    parser.add_argument("--dev", action="store_true",
                       help="Start in development mode with auto-reload")
    parser.add_argument("--quick-check", action="store_true",
                       help="Run quick pre-flight check (critical packages only)")
    parser.add_argument("--preflight-only", action="store_true",
                       help="Run only pre-flight check, don't start application")
    
    args = parser.parse_args()
    
    startup_manager = CumpairStartup()
    
    if args.preflight_only:
        logger.info("Running pre-flight check only...")
        success = startup_manager.run_pre_flight_check(quick_mode=args.quick_check)
        sys.exit(0 if success else 1)
    
    try:
        startup_manager.run_startup_sequence(
            skip_preflight=args.skip_preflight,
            dev_mode=args.dev,
            quick_check=args.quick_check
        )
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
