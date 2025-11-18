#!/usr/bin/env python3
"""Direct test of Scrapy API"""

import requests
import json
import time

print("Testing Scrapy Service...")
print("=" * 60)

# Test 1: Health
print("\n1. Health Check")
r = requests.get('http://localhost:5000/health', timeout=5)
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Service: {data.get('service')}")
print(f"   Retailers: {data.get('retailers_supported')}")

# Test 2: Retailers
print("\n2. Get Retailers")
r = requests.get('http://localhost:5000/api/retailers', timeout=5)
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Total retailers: {data.get('total')}")
print(f"   First 5: {data.get('retailers')[:5]}")

# Test 3: Search
print("\n3. Single Search (Amazon + Walmart)")
start = time.time()
r = requests.post('http://localhost:5000/api/search',
    json={'query': 'phone', 'sites': ['amazon', 'walmart']},
    timeout=60)
elapsed = time.time() - start
print(f"   Status: {r.status_code}")
print(f"   Time: {elapsed:.1f}s")
data = r.json()
print(f"   Total products: {data.get('total_products')}")
print(f"   Successful sites: {data.get('successful_sites')}")

# Test 4: Multi-site Search
print("\n4. Multi-site Search (5 retailers)")
start = time.time()
r = requests.post('http://localhost:5000/api/search',
    json={'query': 'laptop', 'sites': ['amazon', 'walmart', 'ebay', 'target', 'bestbuy']},
    timeout=120)
elapsed = time.time() - start
print(f"   Status: {r.status_code}")
print(f"   Time: {elapsed:.1f}s")
data = r.json()
print(f"   Total products: {data.get('total_products')}")
print(f"   Successful sites: {data.get('successful_sites')}")

# Test 5: Stats
print("\n5. Service Stats")
r = requests.get('http://localhost:5000/api/stats', timeout=5)
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Total requests: {data.get('stats', {}).get('total_requests')}")

print("\n" + "=" * 60)
print("Tests complete!")
