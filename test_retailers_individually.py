#!/usr/bin/env python3
"""Test each retailer to see current extraction"""
import requests

retailers = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg']
query = 'phone'

print("RETAILER EXTRACTION TEST")
print("=" * 50)

for retailer in retailers:
    try:
        r = requests.post('http://localhost:5000/api/search',
            json={'query': query, 'sites': [retailer]},
            timeout=30)
        data = r.json()
        products = data.get('total_products', 0)
        status = "✅" if products > 0 else "❌"
        print(f"{status} {retailer:12} : {products:2} products")
    except Exception as e:
        print(f"❌ {retailer:12} : ERROR - {str(e)[:40]}")

print("=" * 50)
