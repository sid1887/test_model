# Debugging Guide - Known Issues

## Issue 1: Cache Hits Not Being Recorded (0% hit rate)

### Symptom
- Repeated searches show `cached: false` even on identical queries
- Response time same for first and second search (~2s)
- Statistics show 0 cache hits across all tests

### Root Cause Analysis
**Location**: `integration_wrapper.py` (lines 60-80, ScrapyIntegration.search method)

**Hypothesis**: Cache key generation may not match between calls
- Possible issue 1: Query string whitespace differences
- Possible issue 2: Retailer list ordering differences
- Possible issue 3: Redis connection/storage not working
- Possible issue 4: Cache timestamp logic preventing hits

### Debug Steps

**Step 1: Check Redis Connection**
```python
# File: debug_cache.py
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print("Redis ping:", r.ping())
print("Redis keys:", r.keys('*'))
print("Cache contents:", {k: r.get(k) for k in r.keys('cache:*')})
```

**Step 2: Check Cache Key Generation**
```python
# Add to integration_wrapper.py, line 65
cache_key = f"cache:{query}:{','.join(sorted(retailers))}"
print(f"DEBUG: Generated cache key: {cache_key}")
print(f"DEBUG: All cache keys in Redis: {r.keys('*')}")
```

**Step 3: Verify Timestamp Validation**
```python
# Check cache_data validation logic (line 74-76)
# Ensure timestamp check isn't rejecting valid cache

# Current logic:
if cache_data and (time.time() - cache_data['timestamp'] < 300):
    # ^ 300 seconds = 5 minutes

# Verify this is being hit by adding print:
print(f"DEBUG: Cache found, age: {time.time() - cache_data['timestamp']}s")
```

**Step 4: Run Corrected Test**
```python
# File: test_cache_debug.py
import requests
import time

print("=== CACHE HIT TEST ===")

# First search
print("\n1. First search (no cache expected)")
r1 = requests.post('http://localhost:7000/api/search', json={
    'query': 'phone',
    'retailers': ['amazon']
})
t1 = time.time()
print(f"Response: {r1.json()}")
print(f"Cached: {r1.json().get('cached', 'N/A')}")

# Second search (identical)
time.sleep(1)
print("\n2. Second search (cache HIT expected)")
r2 = requests.post('http://localhost:7000/api/search', json={
    'query': 'phone',
    'retailers': ['amazon']
})
t2 = time.time()
print(f"Response: {r2.json()}")
print(f"Cached: {r2.json().get('cached', 'N/A')}")
print(f"Speed improvement: {r1.elapsed.total_seconds():.2f}s → {r2.elapsed.total_seconds():.2f}s")
```

### Potential Fixes

**Fix 1: Normalize Query String**
```python
# integration_wrapper.py, line 65
import hashlib

# Old:
# cache_key = f"cache:{query}:{retailers}"

# New:
normalized_query = ' '.join(query.split()).lower()  # Normalize whitespace
normalized_retailers = ','.join(sorted(retailers))   # Sort for consistency
cache_key = f"cache:{normalized_query}:{normalized_retailers}"
```

**Fix 2: Debug Redis Storage**
```python
# Add detailed logging:
try:
    r.setex(cache_key, 300, json.dumps({
        'data': results,
        'timestamp': time.time()
    }))
    print(f"DEBUG: Stored cache key: {cache_key}")
except Exception as e:
    print(f"ERROR storing cache: {e}")
```

**Fix 3: Verify Response Includes Cached Flag**
```python
# Ensure search() returns cached flag:
return {
    'results': results,
    'cached': from_cache,  # Make sure this is set correctly
    'source': 'cache' if from_cache else 'scrapy',
    'response_time': time.time() - start
}
```

---

## Issue 2: Multi-Retailer Advanced Filtering Returns 500 Error

### Symptom
- Single retailer advanced search: ✓ 200 OK (29 products filtered)
- Multi-retailer advanced search: ✗ 500 Internal Server Error
- Single retailer doesn't filter, multi returns 500

### Root Cause Analysis
**Location**: `integration_wrapper.py` (lines 95-120, ScrapyIntegration.search_advanced method)

**Hypothesis**: Product structure inconsistency between retailers
- Amazon products: `{'title': '', 'price': '', ...}`
- Walmart products: `{'name': '', 'cost': '', ...}` (different key names)
- Filtering logic expects consistent key names

### Debug Steps

**Step 1: Inspect Product Structure per Retailer**
```python
# File: debug_product_structure.py
import requests

retailers = ['amazon', 'walmart', 'ebay']

for retailer in retailers:
    print(f"\n=== {retailer.upper()} ===")
    r = requests.post('http://localhost:5000/api/search', json={
        'query': 'phone',
        'sites': [retailer]
    })

    if r.status_code == 200:
        products = r.json().get('results', [])
        if products:
            print(f"Sample product keys: {products[0].keys()}")
            print(f"Sample product: {products[0]}")
        else:
            print("No products found")
    else:
        print(f"Error: {r.status_code}")
```

**Step 2: Check Filtering Logic**
```python
# integration_wrapper.py, line 105-115
# Look for assumptions about product key names

# Current likely issue:
for product in all_products:
    # Assumes 'price' key exists
    if min_price <= float(product['price']) <= max_price:
        # ^ FAILS if key is 'cost' or 'amount' or something else

# Should use:
def safe_get_price(product):
    """Try multiple possible price keys"""
    for key in ['price', 'cost', 'amount', 'product_price']:
        if key in product:
            try:
                return float(product[key])
            except ValueError:
                continue
    return None
```

**Step 3: Run Detailed Error Test**
```python
# File: test_advanced_filter_debug.py
import requests
import traceback

print("=== ADVANCED FILTER DEBUG ===")

# Test 1: Single retailer
print("\n1. Single retailer (should work)")
try:
    r = requests.post('http://localhost:7000/api/search/advanced', json={
        'query': 'phone',
        'retailers': ['amazon'],
        'min_price': 100,
        'max_price': 500
    })
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Results: {len(r.json().get('results', []))} products")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()

# Test 2: Multi retailer
print("\n2. Multi retailer (currently fails)")
try:
    r = requests.post('http://localhost:7000/api/search/advanced', json={
        'query': 'phone',
        'retailers': ['amazon', 'walmart', 'ebay'],
        'min_price': 100,
        'max_price': 500
    })
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Results: {len(r.json().get('results', []))} products")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
```

**Step 4: Check Web Service Logs**
```bash
# View actual error
docker logs test_model-web-1 --tail 50 -f

# Look for: KeyError, ValueError, AttributeError in filtering code
```

### Potential Fixes

**Fix 1: Standardize Product Format in Scrapy**
```python
# simple_scraper.py, yield section for each spider

# Ensure all retailers return same format:
yield {
    'title': title,      # Standard key
    'price': float(price),  # Standard format
    'image': image_url,
    'link': product_url,
    'source': 'amazon'    # Track source
}

# Not:
# 'name' instead of 'title'
# 'cost' instead of 'price'
# 'image_src' instead of 'image'
```

**Fix 2: Add Price Extraction Helper**
```python
# integration_wrapper.py, line 95
def _extract_price(product):
    """Safely extract price from product regardless of key name"""
    for key in ['price', 'cost', 'amount', 'product_price', 'sale_price']:
        value = product.get(key)
        if value:
            try:
                return float(str(value).replace('$', '').strip())
            except (ValueError, TypeError):
                continue
    return None

def _extract_title(product):
    """Safely extract title from product"""
    for key in ['title', 'name', 'product_name']:
        if key in product:
            return product[key]
    return None
```

**Fix 3: Add Try-Catch in Filtering**
```python
# integration_wrapper.py, search_advanced method
def search_advanced(self, query, retailers, min_price=0, max_price=10000, sort_by='price'):
    try:
        all_products = []
        for retailer in retailers:
            products = self.search(query, [retailer]).get('results', [])
            all_products.extend(products)

        # Safe filtering
        filtered = []
        for product in all_products:
            price = self._extract_price(product)
            if price and min_price <= price <= max_price:
                filtered.append(product)

        # Sort
        if sort_by == 'price':
            filtered.sort(key=lambda p: self._extract_price(p) or 0)

        return {'results': filtered, 'count': len(filtered)}

    except Exception as e:
        print(f"ERROR in search_advanced: {e}")
        traceback.print_exc()
        return {'error': str(e), 'results': []}
```

---

## Testing Protocol

### After Implementing Fixes

```bash
# Test 1: Verify individual fixes
python debug_cache.py
python debug_product_structure.py

# Test 2: Run updated test suite
python test_cache_debug.py
python test_advanced_filter_debug.py

# Test 3: Full regression test
python test_full_system.py

# Test 4: Performance check
python test_bulk_performance.py
```

### Success Criteria

**Cache Fix Success**:
- ✓ Second search shows `cached: true`
- ✓ Response time drops from ~2s to <100ms
- ✓ Statistics show >50% cache hit rate on repeated queries

**Advanced Filter Fix Success**:
- ✓ Multi-retailer search returns 200 (not 500)
- ✓ Filtering logic correctly filters by price
- ✓ Results properly deduplicated and ranked

---

## Quick Reference: File Locations

| Issue | File | Lines | Method |
|-------|------|-------|--------|
| Cache | integration_wrapper.py | 60-80 | search() |
| Advanced Filter | integration_wrapper.py | 95-120 | search_advanced() |
| Product Keys | simple_scraper.py | 100-200 | yield statements |
| Response Model | scrapy.py | 30-50 | SearchResponse class |
