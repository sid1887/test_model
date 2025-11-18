#!/usr/bin/env python3
"""Test each retailer individually to identify which ones work and which need selector refinement"""

import requests
import json
import time

retailers = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg', 'costco',
             'homedepot', 'lowes', 'macys', 'overstock', 'wayfair', 'zappos',
             'bhphotovideo', 'nordstrom', 'flipkart', 'aliexpress']

print("=" * 80)
print("RETAILER PERFORMANCE ANALYSIS")
print("=" * 80)
print(f"Testing {len(retailers)} retailers with query: 'phone'\n")

results = {}

for retailer in retailers:
    try:
        print(f"Testing {retailer:15} ... ", end="", flush=True)
        start = time.time()

        r = requests.post(
            'http://localhost:8000/api/v1/scrapy/search',
            json={'query': 'phone', 'retailers': [retailer]},
            timeout=60
        )

        elapsed = time.time() - start

        if r.status_code == 200:
            data = r.json()
            products = data.get('total_products', 0)
            successful = data.get('successful_sites', 0)
            status = "✓ WORKING" if products > 0 else "✗ NO RESULTS"
            print(f"{status:20} - {products:3} products ({elapsed:.1f}s)")
            results[retailer] = {
                'status': 'working' if products > 0 else 'failed',
                'products': products,
                'time': elapsed
            }
        else:
            print(f"✗ ERROR {r.status_code:3} ({elapsed:.1f}s)")
            results[retailer] = {'status': 'error', 'products': 0, 'time': elapsed}

    except Exception as e:
        print(f"✗ TIMEOUT/ERROR")
        results[retailer] = {'status': 'timeout', 'products': 0, 'time': 0}

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

working = [r for r, data in results.items() if data['status'] == 'working']
failed = [r for r, data in results.items() if data['status'] == 'failed']
errors = [r for r, data in results.items() if data['status'] in ['error', 'timeout']]

print(f"\n✓ WORKING ({len(working)}):")
for r in working:
    products = results[r]['products']
    print(f"    {r:15} - {products} products")

print(f"\n✗ NO RESULTS ({len(failed)}):")
for r in failed:
    print(f"    {r:15}")

if errors:
    print(f"\n⚠ ERRORS/TIMEOUTS ({len(errors)}):")
    for r in errors:
        print(f"    {r:15}")

total_products = sum(data['products'] for data in results.values())
avg_time = sum(data['time'] for data in results.values()) / len(results) if results else 0

print(f"\nOverall: {total_products} products from {len(working)} retailers")
print(f"Average response time: {avg_time:.1f}s")
print(f"Success rate: {len(working)}/{len(retailers)} ({100*len(working)//len(retailers)}%)")

# Save detailed results
with open('retailer_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nDetailed results saved to: retailer_analysis.json")
