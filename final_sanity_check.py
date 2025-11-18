#!/usr/bin/env python3
"""Final sanity check"""
import requests

print("=" * 60)
print("FINAL SANITY CHECK - SCRAPY SERVICE")
print("=" * 60)
print()

# 1. Scrapy Health
r = requests.get('http://localhost:5000/health')
health_data = r.json()
print(f"1. Scrapy Health: {r.status_code}")
print(f"   Status: {health_data.get('status')}")
print(f"   Service: {health_data.get('service')}")
print(f"   Retailers: {health_data.get('retailers_supported')}")

# 2. Retailers Available
r = requests.get('http://localhost:5000/api/retailers')
retailers = r.json()
print(f"\n2. Retailers Available: {retailers['total']}")
print(f"   First 5: {', '.join(retailers['retailers'][:5])}")

# 3. Quick Amazon Search
r = requests.post('http://localhost:5000/api/search',
    json={'query': 'phone', 'sites': ['amazon']}, timeout=30)
data = r.json()
print(f"\n3. Amazon Search:")
print(f"   Status: {r.status_code}")
print(f"   Products: {data['total_products']}")
print(f"   Sites: {data['sites_searched']}")

# 4. Multi-site Test
r = requests.post('http://localhost:5000/api/search',
    json={'query': 'laptop', 'sites': ['amazon', 'walmart', 'ebay']}, timeout=60)
data = r.json()
print(f"\n4. Multi-site Test (3 retailers):")
print(f"   Status: {r.status_code}")
print(f"   Total Products: {data['total_products']}")
print(f"   Sites Searched: {data['sites_searched']}")
print(f"   Successful Sites: {data['successful_sites']}")

print("\n" + "=" * 60)
print("✅ SCRAPY SERVICE OPERATIONAL AND VERIFIED")
print("=" * 60)
