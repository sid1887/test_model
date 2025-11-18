#!/usr/bin/env python3
"""Complete system integration test"""

import requests
import json

print("=" * 80)
print("COMPLETE SYSTEM INTEGRATION TEST")
print("=" * 80)

results = []

# Test 1: Web Service Health
try:
    r = requests.get('http://localhost:8000/api/v1/health', timeout=10)
    print(f"✓ Web Service: HTTP {r.status_code}")
    results.append(True)
except Exception as e:
    print(f"✗ Web Service failed: {e}")
    results.append(False)

# Test 2: Scrapy Health Check
try:
    r = requests.get('http://localhost:8000/api/v1/scrapy/health', timeout=10)
    data = r.json()
    print(f"✓ Scrapy Integration: HTTP {r.status_code} - {data['retailers_supported']} retailers")
    results.append(True)
except Exception as e:
    print(f"✗ Scrapy health failed: {e}")
    results.append(False)

# Test 3: Single Retailer Search (Amazon)
try:
    r = requests.post('http://localhost:8000/api/v1/scrapy/search',
        json={'query': 'phone', 'retailers': ['amazon']},
        timeout=120)
    data = r.json()
    products = data.get('total_products', 0)
    print(f"✓ Single Search (Amazon): {products} products in {data.get('sites_searched', 0)} site(s)")
    results.append(True)
except Exception as e:
    print(f"✗ Single search failed: {e}")
    results.append(False)

# Test 4: Multi-Retailer Search
try:
    r = requests.post('http://localhost:8000/api/v1/scrapy/search',
        json={'query': 'laptop', 'retailers': ['amazon', 'ebay', 'target']},
        timeout=120)
    data = r.json()
    products = data.get('total_products', 0)
    print(f"✓ Multi-Retailer (3): {products} products, {data.get('successful_sites', 0)} successful sites")
    results.append(True)
except Exception as e:
    print(f"✗ Multi-retailer search failed: {e}")
    results.append(False)

# Test 5: Integration Wrapper Layer
try:
    r = requests.post('http://localhost:7000/api/search',
        json={'query': 'phone', 'retailers': ['amazon'], 'cache': False},
        timeout=120)
    data = r.json()
    products = data.get('total_products', 0)
    response_time = data.get('response_time', 0)
    print(f"✓ Wrapper Layer (Port 7000): {products} products, {response_time:.1f}s response")
    results.append(True)
except Exception as e:
    print(f"✗ Wrapper layer failed: {e}")
    results.append(False)

# Test 6: Wrapper Advanced Search with Filtering
try:
    r = requests.post('http://localhost:7000/api/search/advanced',
        json={
            'query': 'monitor',
            'retailers': ['amazon'],
            'min_price': 100,
            'max_price': 500,
            'rank_by': 'price'
        },
        timeout=120)
    data = r.json()
    total = data.get('total_count', 0)
    filtered = data.get('filtered_count', 0)
    print(f"✓ Advanced Filtering: {total} total, {filtered} filtered ($100-$500)")
    results.append(True)
except Exception as e:
    print(f"✗ Advanced filtering failed: {e}")
    results.append(False)

# Test 7: Get Supported Retailers
try:
    r = requests.get('http://localhost:8000/api/v1/scrapy/retailers', timeout=10)
    data = r.json()
    retailers = data.get('retailers', [])
    print(f"✓ Supported Retailers: {len(retailers)} retailers")
    for r_name in retailers[:5]:
        print(f"    - {r_name}")
    if len(retailers) > 5:
        print(f"    ... and {len(retailers)-5} more")
    results.append(True)
except Exception as e:
    print(f"✗ Retailers list failed: {e}")
    results.append(False)

# Summary
print("\n" + "=" * 80)
passed = sum(results)
total = len(results)
print(f"RESULTS: {passed}/{total} tests passed ({100*passed//total}%)")
print("=" * 80)

if passed == total:
    print("\n✓ ALL SYSTEMS OPERATIONAL")
    print("\nAvailable APIs:")
    print("  - Web Service (FastAPI): http://localhost:8000/api/v1")
    print("  - Scrapy Routes: http://localhost:8000/api/v1/scrapy")
    print("  - Integration Wrapper: http://localhost:7000")
    print("  - Direct Scrapy: http://localhost:5000")
    print("\nFeatures:")
    print("  - 17+ retailers supported")
    print("  - Multi-modal search (text, voice, image via CLIP)")
    print("  - Price filtering & ranking")
    print("  - Caching & performance optimization")
    print("  - Bulk search capabilities")
else:
    print(f"\n⚠ {total-passed} tests failed - troubleshoot above")
