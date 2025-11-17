#!/usr/bin/env python3
"""
Comprehensive Scrapy Integration Test
Tests all 17 retailers and service integrations

REQUIREMENTS:
1. Start the Scrapy service first:
   cd /home/runner/work/test_model/test_model/scrapy_service
   python api.py

2. Ensure Redis is running (for caching)

3. Run this test:
   python test_scrapy_integration.py
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
SCRAPY_API_URL = "http://localhost:5000"
MAIN_API_URL = "http://localhost:8000"

# Supported retailers
SUPPORTED_RETAILERS = [
    'amazon', 'walmart', 'ebay', 'target', 'bestbuy', 
    'newegg', 'costco', 'homedepot', 'lowes', 'macys',
    'overstock', 'wayfair', 'zappos', 'bhphotovideo', 
    'nordstrom', 'flipkart', 'aliexpress'
]

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"   {details}")
    print()

def test_health_check():
    """Test 1: Health check"""
    test_name = "Scrapy Service Health Check"
    try:
        response = requests.get(f"{SCRAPY_API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            passed = (
                data.get('status') == 'healthy' and
                data.get('retailers_supported') == len(SUPPORTED_RETAILERS)
            )
            details = f"Status: {data.get('status')}, Retailers: {data.get('retailers_supported')}"
            print_result(test_name, passed, details)
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_retailers_endpoint():
    """Test 2: Retailers list endpoint"""
    test_name = "Get Supported Retailers"
    try:
        response = requests.get(f"{SCRAPY_API_URL}/api/retailers", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            retailers = data.get('retailers', [])
            passed = (
                len(retailers) == len(SUPPORTED_RETAILERS) and
                all(r in SUPPORTED_RETAILERS for r in retailers)
            )
            details = f"Found {len(retailers)} retailers: {', '.join(retailers[:5])}..."
            print_result(test_name, passed, details)
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_basic_search():
    """Test 3: Basic search functionality"""
    test_name = "Basic Product Search"
    try:
        response = requests.post(
            f"{SCRAPY_API_URL}/api/search",
            json={
                'query': 'laptop',
                'sites': ['amazon', 'walmart', 'ebay']
            },
            timeout=10
        )
        
        if response.status_code == 202:  # Accepted
            data = response.json()
            passed = (
                data.get('status') == 'processing' and
                data.get('sites_queued') == 3
            )
            details = f"Query: {data.get('query')}, Sites queued: {data.get('sites_queued')}"
            print_result(test_name, passed, details)
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_bulk_search():
    """Test 4: Bulk search functionality"""
    test_name = "Bulk Search Across Retailers"
    try:
        queries = ['laptop', 'headphones', 'monitor']
        retailers = ['amazon', 'walmart', 'bestbuy', 'newegg', 'target']
        
        response = requests.post(
            f"{SCRAPY_API_URL}/api/search/bulk",
            json={
                'queries': queries,
                'retailers': retailers
            },
            timeout=10
        )
        
        if response.status_code == 202:  # Accepted
            data = response.json()
            expected_jobs = len(queries) * len(retailers)
            passed = (
                data.get('status') == 'queued' and
                data.get('jobs_queued') == expected_jobs
            )
            details = f"Batch ID: {data.get('batch_id')}, Jobs: {data.get('jobs_queued')}/{expected_jobs}"
            print_result(test_name, passed, details)
            
            # Test batch status
            if passed and data.get('batch_id'):
                time.sleep(2)
                status_response = requests.get(
                    f"{SCRAPY_API_URL}/api/batch/{data['batch_id']}",
                    timeout=5
                )
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Batch status: {status_data.get('progress')} complete")
            
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_stats_endpoint():
    """Test 5: Statistics endpoint"""
    test_name = "Scraper Statistics"
    try:
        response = requests.get(f"{SCRAPY_API_URL}/api/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            passed = (
                'stats' in data and
                'retailers' in data and
                data['retailers'].get('total') == len(SUPPORTED_RETAILERS)
            )
            details = f"Active retailers: {data['retailers'].get('active', 0)}/{data['retailers'].get('total', 0)}"
            if 'daily_stats' in data:
                details += f", Products today: {data['daily_stats'].get('total_products_scraped', 0)}"
            print_result(test_name, passed, details)
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_all_retailers():
    """Test 6: Search on all 17 retailers"""
    test_name = "Search Across All 17 Retailers"
    try:
        response = requests.post(
            f"{SCRAPY_API_URL}/api/search",
            json={
                'query': 'wireless mouse',
                'sites': SUPPORTED_RETAILERS
            },
            timeout=15
        )
        
        if response.status_code == 202:
            data = response.json()
            passed = data.get('sites_queued') == len(SUPPORTED_RETAILERS)
            details = f"All {data.get('sites_queued')} retailers queued successfully"
            print_result(test_name, passed, details)
            return passed
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def test_service_integrations():
    """Test 7: Verify service integrations are configured"""
    test_name = "Service Integrations Check"
    try:
        response = requests.get(f"{SCRAPY_API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            
            required_services = ['redis', 'voice_stt', 'clip_analysis', 'captcha_solver', 'proxy_service']
            all_available = all(services.get(s) == 'available' or services.get(s) == 'connected' 
                               for s in required_services)
            
            details = f"Services: {', '.join([f'{k}:{v}' for k, v in services.items()])}"
            print_result(test_name, all_available, details)
            return all_available
        else:
            print_result(test_name, False, f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(test_name, False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("=" * 80)
    print("SCRAPY SERVICE INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scrapy API: {SCRAPY_API_URL}")
    print(f"Main API: {MAIN_API_URL}")
    print("=" * 80)
    print()
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health_check()))
    results.append(("Retailers Endpoint", test_retailers_endpoint()))
    results.append(("Basic Search", test_basic_search()))
    results.append(("Bulk Search", test_bulk_search()))
    results.append(("Statistics", test_stats_endpoint()))
    results.append(("All Retailers", test_all_retailers()))
    results.append(("Service Integrations", test_service_integrations()))
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("=" * 80)
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
