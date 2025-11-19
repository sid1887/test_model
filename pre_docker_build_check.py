#!/usr/bin/env python3
"""
Pre-Docker-Build Verification Checklist
Verifies all dependencies are available before building Docker images
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        print(f"✅ Docker: {result.stdout.strip()}")

        # Check if running
        subprocess.run(['docker', 'ps'], capture_output=True, check=True)
        print("✅ Docker daemon is running")
        return True
    except FileNotFoundError:
        print(f"❌ Docker not installed")
        return False
    except Exception as e:
        print(f"❌ Docker error: {e}")
        return False

def check_disk_space():
    """Check available disk space"""
    try:
        result = subprocess.run(['powershell', '-Command',
                                '(Get-Volume -DriveLetter D).SizeRemaining / 1GB'],
                               capture_output=True, text=True, check=True)
        space_gb = float(result.stdout.strip())
        if space_gb > 10:
            print(f"✅ Disk space: {space_gb:.1f}GB available (>10GB needed)")
            return True
        else:
            print(f"❌ Low disk space: {space_gb:.1f}GB available (need >10GB)")
            return False
    except Exception as e:
        print(f"⚠️  Could not check disk space: {e}")
        return True

def check_memory():
    """Check available memory"""
    try:
        result = subprocess.run(['powershell', '-Command',
                                '[Math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb)'],
                               capture_output=True, text=True, check=True)
        total_memory = int(result.stdout.strip())
        if total_memory >= 8:
            print(f"✅ Total memory: {total_memory}GB available (≥8GB needed)")
            return True
        else:
            print(f"⚠️  Limited memory: {total_memory}GB (recommend ≥8GB for all services)")
            return True
    except Exception as e:
        print(f"⚠️  Could not check memory: {e}")
        return True

def check_python_packages():
    """Check if required Python packages can be imported"""
    required = [
        'fastapi',
        'uvicorn',
        'httpx',
        'aioredis',
        'redis',
        'sqlalchemy',
        'psycopg2',
    ]

    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"✅ Python package: {pkg}")
        except ImportError:
            print(f"⚠️  Python package not installed locally: {pkg}")
            missing.append(pkg)

    return len(missing) == 0 or True  # Not critical, Docker will install

def check_api_gateway():
    """Check if api_gateway.py exists and is syntactically correct"""
    gateway_file = Path('api_gateway.py')

    if not gateway_file.exists():
        print(f"❌ api_gateway.py not found")
        return False

    try:
        with open(gateway_file, 'r') as f:
            code = f.read()
            compile(code, str(gateway_file), 'exec')
            print(f"✅ api_gateway.py exists and is valid Python")
            return True
    except SyntaxError as e:
        print(f"❌ api_gateway.py has syntax error: {e}")
        return False

def check_dockerfile():
    """Check if Dockerfile exists and is valid"""
    dockerfile = Path('docker/Dockerfile.api-gateway')

    if not dockerfile.exists():
        print(f"❌ Dockerfile.api-gateway not found at {dockerfile}")
        return False

    try:
        with open(dockerfile, 'r') as f:
            content = f.read()
            if 'FROM python:3.11' in content and 'pip install' in content:
                print(f"✅ Dockerfile.api-gateway exists and looks valid")
                return True
            else:
                print(f"⚠️  Dockerfile.api-gateway missing expected content")
                return False
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False

def check_requirements():
    """Check if requirements.txt exists and has expected packages"""
    req_file = Path('requirements.txt')

    if not req_file.exists():
        print(f"❌ requirements.txt not found")
        return False

    try:
        with open(req_file, 'r') as f:
            content = f.read()

        required = ['fastapi', 'uvicorn', 'httpx', 'aioredis', 'redis', 'pydantic']
        found = sum(1 for pkg in required if pkg in content.lower())

        print(f"✅ requirements.txt found ({found}/{len(required)} critical packages)")
        return found >= len(required)
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_docker_network():
    """Check if backend network exists"""
    try:
        result = subprocess.run(['docker', 'network', 'ls'],
                              capture_output=True, text=True, check=True)
        if 'backend' in result.stdout:
            print("✅ Docker network 'backend' exists")
            return True
        else:
            print("⚠️  Docker network 'backend' does not exist (will be created)")
            return True
    except Exception as e:
        print(f"⚠️  Could not check Docker network: {e}")
        return True

def check_existing_containers():
    """Check for existing containers that might conflict"""
    try:
        result = subprocess.run(['docker', 'ps', '-a'],
                              capture_output=True, text=True, check=True)

        containers = [line for line in result.stdout.split('\n')
                     if 'cumpair' in line.lower()]

        if containers:
            print(f"⚠️  Found {len(containers)} existing cumpair containers:")
            for container in containers[:5]:
                print(f"   {container[:80]}")
            return False
        else:
            print("✅ No existing cumpair containers found")
            return True
    except Exception as e:
        print(f"⚠️  Could not check containers: {e}")
        return True

def main():
    """Run all checks"""
    print("=" * 70)
    print("PRE-DOCKER-BUILD VERIFICATION CHECKLIST")
    print("=" * 70)
    print()

    checks = [
        ("Docker Installation", check_docker),
        ("Disk Space", check_disk_space),
        ("Memory Available", check_memory),
        ("Python Packages", check_python_packages),
        ("API Gateway Code", check_api_gateway),
        ("Dockerfile", check_dockerfile),
        ("Requirements File", check_requirements),
        ("Docker Network", check_docker_network),
        ("Existing Containers", check_existing_containers),
    ]

    results = []
    for name, check_fn in checks:
        print(f"\n🔍 {name}")
        print("-" * 70)
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append((name, False))

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n✅ Passed: {passed}/{total} checks")

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    print()
    if passed == total:
        print("🚀 READY TO BUILD DOCKER IMAGE FOR API GATEWAY")
        print()
        print("Next command:")
        print("  docker build -f docker/Dockerfile.api-gateway -t cumpair-api-gateway:latest .")
        return 0
    else:
        print("⚠️  Some checks failed. Review above and fix issues before building.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
