#!/usr/bin/env python3
"""
Cumpair Integration Test Suite
Tests the complete integrated system functionality
"""

import asyncio
import sys
import traceback
from pathlib import Path

async def test_service_imports():
    """Test all service imports"""
    print("🔥 Testing Service Imports...")
    
    tests = [
        ("Price Comparison Service", "from app.services.price_comparison import price_comparison_service"),
        ("Product Discovery Service", "from app.services.product_discovery import product_discovery_service"),
        ("Scraping Services", "from app.services.scraping import scraper_client, scraping_engine"),
        ("CLIP Search Service", "from app.services.clip_search import clip_service"),
        ("AI Models Service", "from app.services.ai_models import ModelManager"),
    ]
    
    results = {}
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}: OK")
            results[name] = True
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            results[name] = False
    
    return results

async def test_api_routes():
    """Test API routes import"""
    print("\n🔗 Testing API Routes...")
    
    routes = [
        ("Health Routes", "from app.api.routes.health import router"),
        ("Analysis Routes", "from app.api.routes.analysis import router"),
        ("Price Comparison Routes", "from app.api.routes.price_comparison import router"),
        ("Discovery Routes", "from app.api.routes.discovery import router"),
    ]
    
    results = {}
    for name, import_stmt in routes:
        try:
            exec(import_stmt)
            print(f"✅ {name}: OK")
            results[name] = True
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            results[name] = False
    
    return results

async def test_models():
    """Test database models"""
    print("\n📊 Testing Database Models...")
    
    models = [
        ("Product Model", "from app.models.product import Product"),
        ("Analysis Model", "from app.models.analysis import Analysis"),
        ("Price Comparison Model", "from app.models.price_comparison import PriceComparison, PriceHistory"),
    ]
    
    results = {}
    for name, import_stmt in models:
        try:
            exec(import_stmt)
            print(f"✅ {name}: OK")
            results[name] = True
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            results[name] = False
    
    return results

async def test_main_app():
    """Test main application"""
    print("\n🚀 Testing Main Application...")
    
    try:
        from main import app
        print(f"✅ FastAPI App: {app.title}")
        print(f"📝 Description: {app.description}")
        print(f"🔢 Version: {app.version}")
        
        # Check routes
        route_count = len(app.routes)
        print(f"🔗 Routes registered: {route_count}")
        
        return True
    except Exception as e:
        print(f"❌ Main application failed: {e}")
        traceback.print_exc()
        return False

async def test_worker():
    """Test Celery worker"""
    print("\n⚙️ Testing Celery Worker...")
    
    try:
        from app.worker import celery_app
        print(f"✅ Celery app: {celery_app.main}")
        
        # Test task registration
        tasks = list(celery_app.tasks.keys())
        print(f"📋 Registered tasks: {len(tasks)}")
        for task in tasks[:5]:  # Show first 5 tasks
            print(f"   - {task}")
        
        return True
    except Exception as e:
        print(f"❌ Celery worker failed: {e}")
        return False

async def test_config():
    """Test configuration"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        from app.core.config import settings
        print(f"✅ App Name: {settings.app_name}")
        print(f"🔢 Version: {settings.app_version}")
        print(f"🗄️ Database: {'configured' if settings.database_url else 'missing'}")
        print(f"📁 Upload Dir: {settings.upload_dir}")
        print(f"📏 Max File Size: {settings.max_file_size / 1024 / 1024:.1f}MB")
        
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

async def test_file_structure():
    """Test critical file structure"""
    print("\n📁 Testing File Structure...")
    
    critical_files = [
        "main.py",
        "app/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/services/price_comparison.py",
        "app/services/product_discovery.py",
        "app/api/routes/price_comparison.py",
        "app/api/routes/discovery.py",
        "requirements.txt",
    ]
    
    missing_files = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    return len(missing_files) == 0

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("🎯 CUMPAIR INTEGRATION TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, test_results in results.items():
        print(f"\n📊 {category}:")
        if isinstance(test_results, dict):
            for test_name, passed in test_results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {test_name}: {status}")
                total_tests += 1
                if passed:
                    passed_tests += 1
        else:
            status = "✅ PASS" if test_results else "❌ FAIL"
            print(f"   {status}")
            total_tests += 1
            if test_results:
                passed_tests += 1
    
    print(f"\n🏆 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Cumpair system is ready! 🚀")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

async def main():
    """Run all integration tests"""
    print("🔍 CUMPAIR - Comprehensive Integration Test Suite")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results["Service Imports"] = await test_service_imports()
    results["API Routes"] = await test_api_routes()
    results["Database Models"] = await test_models()
    results["Main Application"] = await test_main_app()
    results["Celery Worker"] = await test_worker()
    results["Configuration"] = await test_config()
    results["File Structure"] = await test_file_structure()
    
    # Print summary
    success = print_summary(results)
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Start the database: docker-compose up postgres redis -d")
        print("2. Run migrations: alembic upgrade head")
        print("3. Start the application: python main.py")
        print("4. Test the API: http://localhost:8000/docs")
        return 0
    else:
        print("\n🔧 Fix the failing tests before proceeding.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        sys.exit(1)
