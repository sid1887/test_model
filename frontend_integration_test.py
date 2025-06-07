#!/usr/bin/env python3
"""
Frontend Integration Test for Cumpair System
Tests the integration between the enhanced frontend and backend services
"""

import requests
import json
import time
from typing import Dict, Any

def test_backend_health():
    """Test if backend services are responsive"""
    print("🔍 Testing Backend Health...")
    
    try:
        # Test FastAPI main health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI Server: Running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ FastAPI Server: Error {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FastAPI Server: Connection failed - {e}")
        return False
    
    try:
        # Test scraper service health
        response = requests.get("http://localhost:3001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Scraper Service: Running")
        else:
            print(f"❌ Scraper Service: Error {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Scraper Service: Not responding - {e}")
    
    return True

def test_api_endpoints():
    """Test key API endpoints that the frontend uses"""
    print("\n🔍 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        ("/", "GET", "Root endpoint"),
        ("/api/products", "GET", "Products API"),
        ("/api/search", "GET", "Search API"),
        ("/docs", "GET", "API Documentation"),
    ]
    
    results = []
    
    for endpoint, method, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {description}: {response.status_code}")
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Connection failed - {e}")
            results.append({
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "error": str(e)
            })
    
    return results

def test_frontend_connection():
    """Test if frontend is accessible"""
    print("\n🔍 Testing Frontend Connection...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Next.js Frontend: Running")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            return True
        else:
            print(f"❌ Next.js Frontend: Error {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Next.js Frontend: Connection failed - {e}")
        return False

def test_search_functionality():
    """Test search functionality that connects frontend to backend"""
    print("\n🔍 Testing Search Integration...")
    
    try:
        # Test text search
        search_data = {
            "query": "iPhone 15",
            "limit": 5
        }
        
        response = requests.post(
            "http://localhost:8000/api/search",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Text Search: Working ({len(results.get('results', []))} results)")
            return True
        else:
            print(f"⚠️  Text Search: Returned {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Search Integration: Connection failed - {e}")
        return False

def generate_integration_report():
    """Generate a comprehensive integration test report"""
    print("=" * 60)
    print("🚀 CUMPAIR SYSTEM INTEGRATION TEST REPORT")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    backend_health = test_backend_health()
    api_results = test_api_endpoints()
    frontend_connection = test_frontend_connection()
    search_integration = test_search_functionality()
    
    end_time = time.time()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 4
    passed_tests = sum([
        backend_health,
        len([r for r in api_results if r['success']]) > 0,
        frontend_connection,
        search_integration
    ])
    
    print(f"⏱️  Test Duration: {end_time - start_time:.2f} seconds")
    print(f"📈 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ The enhanced Cumpair frontend is successfully integrated with the backend!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review the issues above.")
    
    # Detailed API Results
    print("\n📋 API Endpoint Details:")
    for result in api_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['endpoint']}: {result['status_code']}")
    
    print("\n🌐 Service URLs:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Scraper:  http://localhost:3001")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = generate_integration_report()
    exit(0 if success else 1)
