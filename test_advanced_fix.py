import requests

print("=== ADVANCED SEARCH FIX TEST ===\n")

# Test 1: Single retailer (should work)
print("1. Single retailer advanced search")
try:
    r = requests.post("http://localhost:8000/api/v1/scrapy/search/advanced",
        params={
            "query": "phone",
            "retailers": ["amazon"],
            "min_price": 100,
            "max_price": 500,
            "rank_by": "price"
        },
        timeout=120)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Total found: {data.get('total_found')}")
        print(f"   After filtering: {data.get('after_filtering')}")
        print("   ✓ Single retailer works")
    else:
        print(f"   Error: {r.text[:200]}")
except Exception as e:
    print(f"   Exception: {e}")

# Test 2: Multi retailer (this was returning 500)
print("\n2. Multi retailer advanced search (THIS WAS BROKEN)")
try:
    r = requests.post("http://localhost:8000/api/v1/scrapy/search/advanced",
        params={
            "query": "phone",
            "retailers": ["amazon", "walmart"],
            "min_price": 100,
            "max_price": 500,
            "rank_by": "price"
        },
        timeout=120)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Total found: {data.get('total_found')}")
        print(f"   After filtering: {data.get('after_filtering')}")
        print("   ✅ Multi retailer NOW WORKS!")
    else:
        print(f"   ✗ Error: {r.text[:200]}")
except Exception as e:
    print(f"   Exception: {e}")
