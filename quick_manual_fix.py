#!/usr/bin/env python3
"""
Quick manual fix that can be run inside Docker container
Run this inside the container to fix all issues immediately
"""

import os
import sys
import subprocess
from pathlib import Path

def fix_syntax_error():
    """Fix the syntax error in ai_models.py"""
    print("🔧 Fixing syntax error in ai_models.py...")
    
    ai_models_path = Path("/app/app/services/ai_models.py")
    if not ai_models_path.exists():
        print("❌ ai_models.py not found")
        return False
    
    # Read the file
    with open(ai_models_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the syntax error
    original_content = content
    content = content.replace("cv2 = None    YOLO = None", "cv2 = None\n    YOLO = None")
    
    if content != original_content:
        with open(ai_models_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Syntax error fixed!")
        return True
    else:
        print("ℹ️ No syntax error found")
        return True

def install_missing_deps():
    """Install missing dependencies"""
    print("📦 Installing missing dependencies...")
    
    packages = [
        "asyncpg",
        "aiofiles",
        "psycopg2-binary",
        "python-multipart",
        "prometheus-client"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}")

def test_imports():
    """Test critical imports"""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
    
    try:
        import asyncpg
        print("✅ asyncpg")
    except ImportError as e:
        print(f"❌ asyncpg: {e}")
    
    try:
        import aiofiles
        print("✅ aiofiles")
    except ImportError as e:
        print(f"❌ aiofiles: {e}")
    
    try:
        from app.core.config import settings
        print("✅ App config")
    except ImportError as e:
        print(f"❌ App config: {e}")
    
    try:
        from app.services.ai_models import ModelManager
        print("✅ AI models")
    except ImportError as e:
        print(f"❌ AI models: {e}")
    except SyntaxError as e:
        print(f"❌ AI models syntax error: {e}")

def main():
    """Main function"""
    print("🚀 Quick Manual Fix Starting...")
    
    # Step 1: Fix syntax errors
    fix_syntax_error()
    
    # Step 2: Install missing packages
    install_missing_deps()
    
    # Step 3: Test imports
    test_imports()
    
    print("✅ Manual fix complete!")
    print("🚀 You can now run: python main.py")

if __name__ == "__main__":
    main()