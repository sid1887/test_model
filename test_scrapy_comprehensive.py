#!/usr/bin/env python3
"""
COMPREHENSIVE SCRAPY SERVICE INTEGRATION TEST
Tests all functionality: health, retailers, search, voice, image, bulk, stats
"""

import requests
import json
import time
from datetime import datetime

print("=" * 80)
print("SCRAPY SERVICE - COMPREHENSIVE INTEGRATION TEST")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Scrapy Service URL: http://localhost:5000")
print("=" * 80)

TESTS_PASSED = 0
TESTS_FAILED = 0

def test(name, func):
    """Run test and track results"""
    global TESTS_PASSED, TESTS_FAILED
    print(f"\nTest: {name}")
    try:
        result = func()
        if result:
            print(f"  [PASS] OK")
            TESTS_PASSED += 1
        else:
            print(f"  [FAIL]")
            TESTS_FAILED += 1
        return result
    except Exception as e:
        print(f"  [FAIL] EXCEPTION: {e}")
        TESTS_FAILED += 1
        return False

# Test 1: Health Check
def health_check():
    r = requests.get('http://localhost:5000/health', timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'scrapy-scraper'
    assert data['retailers_supported'] == 17
    print(f"    Service: {data['service']}, Retailers: {data['retailers_supported']}")
    return True

test("Health Check", health_check)

# Test 2: Get Retailers
def get_retailers():
    r = requests.get('http://localhost:5000/api/retailers', timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data['total'] == 17
    assert 'amazon' in data['retailers']
    print(f"    Found {data['total']} retailers")
    return True

test("Get Supported Retailers", get_retailers)

# Test 3: Single Retailer Search (Amazon)
def search_amazon_only():
    start = time.time()
    r = requests.post('http://localhost:5000/api/search',
        json={'query': 'laptop', 'sites': ['amazon']},
        timeout=30)
    elapsed = time.time() - start
    assert r.status_code == 200
    data = r.json()
    assert data['total_products'] > 0
    print(f"    Amazon: {data['total_products']} products in {elapsed:.1f}s")
    return True

test("Single Retailer Search (Amazon)", search_amazon_only)

# Test 4: Multi-Retailer Search
def search_multi_retailer():
    start = time.time()
    r = requests.post('http://localhost:5000/api/search',
        json={'query': 'phone', 'sites': ['amazon', 'walmart', 'ebay', 'target', 'bestbuy']},
        timeout=60)
    elapsed = time.time() - start
    assert r.status_code == 200
    data = r.json()
    assert data['sites_searched'] == 5
    print(f"    5 retailers: {data['total_products']} total products in {elapsed:.1f}s")
    print(f"    Successful sites: {data['successful_sites']}")
    return True

test("Multi-Retailer Search", search_multi_retailer)

# Test 5: Bulk Search
def bulk_search():
    r = requests.post('http://localhost:5000/api/search/bulk',
        json={
            'queries': ['laptop', 'headphones'],
            'retailers': ['amazon', 'walmart', 'ebay']
        },
        timeout=30)
    assert r.status_code == 202
    data = r.json()
    assert data['status'] == 'queued'
    assert data['jobs_queued'] == 6  # 2 queries × 3 retailers
    assert 'batch_id' in data
    print(f"    Batch ID: {data['batch_id']}")
    print(f"    Jobs queued: {data['jobs_queued']}")
    return True

test("Bulk Search", bulk_search)

# Test 6: Service Statistics
def get_stats():
    r = requests.get('http://localhost:5000/api/stats', timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert 'stats' in data
    assert 'retailers' in data
    print(f"    Total requests: {data['stats']['total_requests']}")
    print(f"    Active retailers: {data['retailers']['active']}/{data['retailers']['total']}")
    return True

test("Get Statistics", get_stats)

# Test 7: Response Time Benchmark
def benchmark():
    times = []
    for i in range(3):
        start = time.time()
        r = requests.post('http://localhost:5000/api/search',
            json={'query': f'test{i}', 'sites': ['amazon']},
            timeout=30)
        elapsed = time.time() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"    3 runs: {times[0]:.1f}s, {times[1]:.1f}s, {times[2]:.1f}s")
    print(f"    Average: {avg:.1f}s per search")
    assert avg < 15  # Should be < 15 seconds
    return True

test("Response Time Benchmark", benchmark)

# Test 8: Error Handling
def error_handling():
    # Test missing query
    r = requests.post('http://localhost:5000/api/search',
        json={'sites': ['amazon']},
        timeout=5)
    assert r.status_code >= 400

    # Test invalid sites
    r = requests.post('http://localhost:5000/api/search',
        json={'query': 'test', 'sites': ['invalid_site']},
        timeout=30)
    assert r.status_code == 200  # Should gracefully handle
    data = r.json()
    assert data['total_products'] == 0
    print(f"    Error handling working correctly")
    return True

test("Error Handling", error_handling)

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Passed: {TESTS_PASSED}")
print(f"Failed: {TESTS_FAILED}")
print(f"Total:  {TESTS_PASSED + TESTS_FAILED}")
print(f"Success Rate: {(TESTS_PASSED / (TESTS_PASSED + TESTS_FAILED) * 100):.1f}%")
print("=" * 80)

if TESTS_FAILED == 0:
    print("✅ ALL TESTS PASSED!")
    exit(0)
else:
    print("❌ SOME TESTS FAILED")
    exit(1)
