#!/usr/bin/env python3
"""
Development environment setup script
Installs and configures all necessary tools for code quality
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up development environment for code quality...")
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install Python development dependencies
    python_deps = [
        "black",
        "flake8",
        "isort",
        "pre-commit",
        "mypy"
    ]
    
    for dep in python_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Failed to install {dep}, continuing...")
    
    # Install pre-commit hooks
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        print("⚠️  Failed to install pre-commit hooks")
    
    # Check if Node.js dependencies are installed in frontend
    if Path("frontend/package.json").exists():
        os.chdir("frontend")
        if not run_command("npm install", "Installing frontend dependencies"):
            print("⚠️  Failed to install frontend dependencies")
        os.chdir("..")
    
    # Check if Node.js dependencies are installed in scraper
    if Path("scraper/package.json").exists():
        os.chdir("scraper")
        if not run_command("npm install", "Installing scraper dependencies"):
            print("⚠️  Failed to install scraper dependencies")
        os.chdir("..")
    
    print("\n🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("   1. Configure your IDE to use the .editorconfig file")
    print("   2. Enable format-on-save in your editor")
    print("   3. Run 'pre-commit run --all-files' to check all files")
    print("   4. The pre-commit hooks will now run automatically on each commit")
    
    print("\n💡 Available commands:")
    print("   black .                    # Format Python code")
    print("   flake8 .                   # Lint Python code")
    print("   npx eslint . --fix         # Fix JavaScript/TypeScript issues")
    print("   npx prettier . --write     # Format frontend code")
    print("   pre-commit run --all-files # Run all quality checks")

if __name__ == "__main__":
    main()
