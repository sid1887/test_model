#!/usr/bin/env python3
"""Test integration wrapper functionality"""

import requests
import json

print("=" * 70)
print("SCRAPY INTEGRATION WRAPPER TEST")
print("=" * 70)

# Test 1: Health
print("\n1. Health Check")
r = requests.get('http://localhost:7000/health')
print(f"   Status: {r.status_code}")
print(f"   Service: {r.json()['service']}")

# Test 2: Retailers
print("\n2. Get Retailers")
r = requests.get('http://localhost:7000/api/retailers')
data = r.json()
print(f"   Total: {data.get('total', 0)}")

# Test 3: Basic Search
print("\n3. Basic Search")
r = requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon', 'ebay'], 'cache': False},
    timeout=60)
data = r.json()
print(f"   Status: {r.status_code}")
print(f"   Products: {data.get('total_products', 0)}")
print(f"   Time: {data.get('response_time', 0):.1f}s")
print(f"   Cached: {data.get('cached', False)}")

# Test 4: Cached Search
print("\n4. Cached Search (same query)")
r = requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon', 'ebay'], 'cache': True},
    timeout=60)
data = r.json()
print(f"   Products: {data.get('total_products', 0)}")
print(f"   Time: {data.get('response_time', 0):.1f}s")
print(f"   From Cache: {data.get('cached', False)}")

# Test 5: Advanced Search with Filtering
print("\n5. Advanced Search with Price Filter")
r = requests.post('http://localhost:7000/api/search/advanced',
    json={
        'query': 'phone',
        'retailers': ['amazon', 'walmart'],
        'min_price': 0,
        'max_price': 1000,
        'rank_by': 'price'
    },
    timeout=60)
data = r.json()
print(f"   Status: {r.status_code}")
print(f"   Total products: {data.get('total_count', 0)}")
print(f"   Filtered products: {data.get('filtered_count', 0)}")

# Test 6: Statistics
print("\n6. Service Statistics")
r = requests.get('http://localhost:7000/api/stats')
data = r.json()
print(f"   Total searches: {data.get('total_searches', 0)}")
print(f"   Total products found: {data.get('total_products', 0)}")
print(f"   Cache size: {data.get('cache_size', 0)}")

print("\n" + "=" * 70)
print("ALL INTEGRATION TESTS COMPLETE")
print("=" * 70)
