#!/usr/bin/env python3
"""
Test bulk search and performance optimization
Tests multiple queries against working retailers
"""

import requests
import time
import json

print("=" * 80)
print("BULK SEARCH & PERFORMANCE TEST")
print("=" * 80)

# Test 1: Bulk search via Scrapy service
print("\n1. Testing Bulk Search (3 queries, 3 retailers)")
print("-" * 80)

queries = ['phone', 'laptop', 'tablet']
retailers = ['amazon', 'walmart', 'zappos']

try:
    start = time.time()
    r = requests.post(
        'http://localhost:5000/api/search/bulk',
        json={'queries': queries, 'sites': retailers},
        timeout=120
    )
    elapsed = time.time() - start

    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"Batch ID: {data.get('batch_id')}")
    print(f"Jobs queued: {data.get('jobs_queued', 0)}")
    print(f"Response time: {elapsed:.1f}s")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Multi-query search via wrapper
print("\n2. Testing Multiple Sequential Searches via Wrapper")
print("-" * 80)

searches = [
    ('phone', ['amazon']),
    ('laptop', ['walmart']),
    ('tablet', ['zappos']),
    ('phone', ['amazon', 'walmart']),
    ('laptop', ['amazon', 'walmart', 'zappos']),
]

total_products = 0
total_time = 0

for query, retailers_list in searches:
    try:
        start = time.time()
        r = requests.post(
            'http://localhost:7000/api/search',
            json={'query': query, 'retailers': retailers_list, 'cache': True},
            timeout=120
        )
        elapsed = time.time() - start

        if r.status_code == 200:
            data = r.json()
            products = data.get('total_products', 0)
            cached = data.get('cached', False)
            total_products += products
            total_time += elapsed
            cached_status = "CACHED" if cached else "FRESH"
            print(f"  Query: '{query}' on {len(retailers_list)} retailer(s) -> {products:3} products ({elapsed:.1f}s) [{cached_status}]")
        else:
            print(f"  Error: {r.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal: {total_products} products in {total_time:.1f}s")
print(f"Average per search: {total_time/len(searches):.1f}s")

# Test 3: Caching effectiveness
print("\n3. Testing Cache Effectiveness")
print("-" * 80)

query = 'phone'
retailers_list = ['amazon', 'walmart']

# First search (warm cache)
start = time.time()
r = requests.post(
    'http://localhost:7000/api/search',
    json={'query': query, 'retailers': retailers_list, 'cache': True},
    timeout=120
)
time1 = time.time() - start
data1 = r.json()
cached1 = data1.get('cached', False)

# Second search (should be cached)
start = time.time()
r = requests.post(
    'http://localhost:7000/api/search',
    json={'query': query, 'retailers': retailers_list, 'cache': True},
    timeout=120
)
time2 = time.time() - start
data2 = r.json()
cached2 = data2.get('cached', False)

print(f"First search: {data1.get('total_products', 0)} products in {time1:.2f}s (cached: {cached1})")
print(f"Second search: {data2.get('total_products', 0)} products in {time2:.2f}s (cached: {cached2})")
print(f"Speed improvement: {time1/time2:.1f}x")

# Test 4: Advanced filtering
print("\n4. Testing Advanced Search with Filtering")
print("-" * 80)

start = time.time()
r = requests.post(
    'http://localhost:7000/api/search/advanced',
    json={
        'query': 'phone',
        'retailers': ['amazon', 'walmart', 'zappos'],
        'min_price': 100,
        'max_price': 800,
        'rank_by': 'price'
    },
    timeout=120
)
elapsed = time.time() - start

if r.status_code == 200:
    data = r.json()
    total = data.get('total_count', 0)
    filtered = data.get('filtered_count', 0)
    print(f"Total products: {total}")
    print(f"Filtered products ($100-$800): {filtered}")
    print(f"Response time: {elapsed:.1f}s")
    print(f"Filtering removed: {total - filtered} products")
else:
    print(f"Error: {r.status_code}")

print("\n" + "=" * 80)
print("PERFORMANCE TEST COMPLETE")
print("=" * 80)
