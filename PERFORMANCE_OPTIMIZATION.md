# Performance Optimization & Next Steps Guide

## 🎯 Current System Performance

### Baseline Metrics
```
Single Query Performance:
  - Amazon: 2-4 seconds
  - Walmart: 4-6 seconds
  - Zappos: 3-5 seconds
  Average: 4.7 seconds

Multi-Retailer (3 sites):
  - Response time: 6-12 seconds
  - Successful sites: 1-2 out of 3

Bulk Processing:
  - Job queueing: 0.1 seconds
  - Async response: 202 Accepted
  - Batch capacity: 51+ jobs/request

Retailer Coverage:
  - Working: 3/17 (Amazon, Walmart, Zappos)
  - Not working: 14/17
  - Root cause: JavaScript rendering not supported
```

## 🔧 Quick Fix Priority Matrix

### Priority 1: Critical System Issues (HIGH IMPACT, LOW EFFORT)
These fixes unlock major functionality improvements

#### Issue 1.1: Cache Hit Detection (Est. 15 min)
**Impact**: 90%+ response time reduction for repeated queries
**Status**: Identified - cache always showing 0 hits
**Fix Location**: `app/api/routes/scrapy.py` or wrapper caching logic

**Quick Diagnosis**:
```bash
# Check if cache hits are being recorded
curl -X POST http://localhost:7000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"phone","retailers":["amazon"]}'

# Note response_time on first call
# Make exact same request again
# Compare response_time - should be much faster if cached

# Expected: First ~4s, Second <0.5s
# Actual: First ~4s, Second ~4s (cache not working)
```

**Root Cause Analysis**:
1. Check if Redis is storing cache entries:
   ```bash
   redis-cli
   > KEYS cache:*
   > GET cache:phone:amazon
   ```

2. Check if cache keys match between requests:
   ```bash
   # Add logging to cache generation:
   # normalized_query = query.strip().lower()
   # normalized_sites = ','.join(sorted(retailers))
   # cache_key = f"cache:{normalized_query}:{normalized_sites}"
   ```

3. Verify timestamp validation isn't too strict:
   ```python
   # Cache TTL should be 300+ seconds
   # Current check: if time.time() - cached['timestamp'] < 300
   ```

**Fix Implementation**:
```python
# In wrapper caching logic, normalize all inputs:
def _get_cache_key(query: str, retailers: list) -> str:
    normalized_query = ' '.join(query.split()).lower()
    normalized_retailers = ','.join(sorted([r.lower() for r in retailers]))
    return f"cache:{normalized_query}:{normalized_retailers}"

# Test caching explicitly:
cache_key = _get_cache_key("phone", ["amazon"])
r.setex(cache_key, 300, json.dumps({...}))
cached_value = r.get(cache_key)
assert cached_value is not None  # Should not be None
```

**Validation**:
```bash
python -c "
import requests, time

# First search
start = time.time()
r1 = requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon']})
t1 = time.time() - start

# Second search (identical)
time.sleep(0.5)
start = time.time()
r2 = requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon']})
t2 = time.time() - start

print(f'First: {t1:.2f}s, Second: {t2:.2f}s')
print(f'Cache working: {t2 < t1/4}')  # Second should be 4x+ faster
"
```

---

#### Issue 1.2: Multi-Retailer Advanced Filtering 500 Error (Est. 20 min)
**Impact**: Enables filtering across multiple retailers at once
**Status**: Identified - returns 500 error on multi-retailer
**Fix Location**: `app/api/routes/scrapy.py` or wrapper advanced search endpoint

**Quick Diagnosis**:
```bash
# Test single retailer filtering (works)
curl -X POST http://localhost:7000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "phone",
    "retailers": ["amazon"],
    "min_price": 100,
    "max_price": 500
  }'
# Expected: 200 OK with filtered results

# Test multi-retailer filtering (fails)
curl -X POST http://localhost:7000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "phone",
    "retailers": ["amazon", "walmart", "ebay"],
    "min_price": 100,
    "max_price": 500
  }'
# Expected: 200 OK, Actual: 500 Error
```

**Root Cause Analysis**:
1. Product keys might differ between retailers:
   ```bash
   # Check Amazon products
   curl -X POST http://localhost:5000/api/search \
     -d '{"query":"phone","sites":["amazon"]}' | jq '.results[0]'
   # Expected keys: title, price, image, link

   # Check Walmart products
   curl -X POST http://localhost:5000/api/search \
     -d '{"query":"phone","sites":["walmart"]}' | jq '.results[0]'
   # Might have: name instead of title, cost instead of price
   ```

2. Check error logs:
   ```bash
   docker logs test_model-web-1 --tail 50 | grep -A 5 "search_advanced"
   # Look for: KeyError, AttributeError, TypeError
   ```

**Fix Implementation**:
```python
# Create robust price extraction:
def _safe_extract_price(product: dict) -> float:
    """Extract price from product with multiple fallbacks"""
    for key in ['price', 'cost', 'amount', 'sale_price', 'product_price']:
        if key in product:
            try:
                val = str(product[key]).replace('$', '').replace(',', '').strip()
                return float(val)
            except (ValueError, AttributeError):
                continue
    return None

def _safe_extract_title(product: dict) -> str:
    """Extract title from product with multiple fallbacks"""
    for key in ['title', 'name', 'product_name', 'product_title']:
        if key in product:
            return str(product[key])
    return "Unknown"

# Use in advanced search:
filtered_products = []
for product in all_products:
    price = _safe_extract_price(product)
    if price is not None and min_price <= price <= max_price:
        filtered_products.append(product)
```

**Validation**:
```bash
python test_advanced_filter_debug.py
# Should show:
# ✓ Single retailer: 200 OK
# ✓ Multi retailer: 200 OK (not 500)
```

---

### Priority 2: Retailer Coverage Expansion (MEDIUM IMPACT, HIGH EFFORT)
These unlock more product sources

#### Issue 2.1: 14 Retailers Returning 0 Products (Est. 2-4 hours)
**Impact**: Increases coverage from 3/17 (18%) to 8+/17 (47%+)
**Current Status**: CSS selectors enhanced but no improvement
**Root Cause**: JavaScript rendering not supported
**Solutions**:
1. Implement Selenium/Playwright for JS rendering
2. Reverse engineer API endpoints
3. Add fallback browser rendering

**Investigation Steps**:

```bash
# Step 1: Identify which retailers need JavaScript
python test_retailers.py > retailer_analysis.json

# Check response times
# If timeout at 30.7s → likely JS-heavy (BestBuy, Costco, AliExpress)
# If timeout at <5s → selectors issue or different key names

# Step 2: Analyze HTML for each failing retailer
# For eBay:
curl -s "https://www.ebay.com/sch/i.html?_nkw=phone" | grep -o "class=\"[^\"]*item[^\"]*\"" | head -10

# For Target:
curl -s "https://www.target.com/s?searchTerm=phone" | grep -o "data-test=\"[^\"]*\"" | head -10

# For BestBuy:
curl -s "https://www.bestbuy.com/site/searchpage.jsp?st=phone" | grep -o "class=\"[^\"]*sku-item[^\"]*\"" | head -10
```

**Implementation Roadmap**:

**Phase 1: Selenium Integration (1-2 hours)**
```python
# app/services/selenium_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumScraper:
    def __init__(self):
        self.driver = webdriver.Chrome(options=self._get_options())

    def _get_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return options

    def scrape_with_js(self, url: str, selector: str, wait_time: int = 10):
        """Scrape JavaScript-rendered content"""
        self.driver.get(url)
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            return [e.text for e in element]
        except Exception as e:
            return []
```

**Phase 2: API Endpoint Reverse Engineering (1-2 hours)**
```python
# Many retailers have hidden APIs
# Example: Target uses GraphQL endpoint
# Example: BestBuy uses REST API with specific headers

# Check network tab in browser DevTools for:
# - GraphQL endpoints
# - REST API patterns
# - AJAX request patterns
```

**Phase 3: Fallback Strategy (30 min)**
```python
# For each retailer, try:
# 1. Direct CSS selector (fast, ~1-2s)
# 2. API endpoint (fast, <1s)
# 3. Selenium rendering (slower, ~5-10s)
# 4. Return empty results if all fail
```

---

### Priority 3: Response Time Optimization (LOW IMPACT, MEDIUM EFFORT)
Target: <3s single, <5s multi

#### Issue 3.1: Parallel Request Processing
**Current**: Sequential requests per retailer (A → B → C = ~12s for 3)
**Target**: Parallel requests (A || B || C = ~4-6s for 3)

```python
# Use asyncio for parallel requests:
import asyncio

async def search_multiple_retailers(query: str, retailers: list):
    """Search all retailers in parallel"""
    tasks = [
        search_single_retailer(query, retailer)
        for retailer in retailers
    ]
    results = await asyncio.gather(*tasks)
    return combine_results(results)

async def search_single_retailer(query: str, retailer: str):
    """Single retailer search"""
    # ... existing logic
    pass
```

#### Issue 3.2: Connection Pooling
**Current**: New connection per request
**Target**: Connection pool (10-20 concurrent)

```python
# Ensure aiohttp session reuse:
# In __init__:
self.session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit_per_host=5, limit=20)
)
```

---

## 📊 Testing & Validation

### Comprehensive Test Suite

```bash
# Run all tests with detailed reporting
python run_all_tests.py

# Individual tests:
python test_full_system.py       # System integration (7/7 pass)
python test_retailers.py          # Retailer analysis (3/17 working)
python test_bulk_performance.py   # Bulk & caching
python test_multimodal.py         # Image/voice endpoints
```

### Performance Benchmarking

```bash
# Single retailer benchmark
python -c "
import requests, time
retailers = ['amazon', 'walmart', 'zappos', 'ebay', 'target']
for r in retailers:
    start = time.time()
    requests.post('http://localhost:8000/api/v1/scrapy/search',
        json={'query': 'phone', 'retailers': [r]})
    elapsed = time.time() - start
    print(f'{r}: {elapsed:.2f}s')
"

# Cache performance benchmark
python -c "
import requests, time
# First search (no cache)
start = time.time()
requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon']})
t1 = time.time() - start

# Second search (should be cached)
start = time.time()
requests.post('http://localhost:7000/api/search',
    json={'query': 'laptop', 'retailers': ['amazon']})
t2 = time.time() - start

print(f'First: {t1:.3f}s, Second: {t2:.3f}s, Improvement: {t1/t2:.1f}x')
"

# Bulk search benchmark
python test_bulk_performance.py
```

---

## 🚀 Deployment Checklist

### Pre-Production Validation

- [ ] All 7 system integration tests passing
- [ ] Cache hit rate >50% on repeated queries
- [ ] Multi-retailer advanced filtering returns 200
- [ ] Bulk search queues 50+ jobs successfully
- [ ] Response times < 5s for multi-retailer
- [ ] Error logs clear of exceptions
- [ ] Redis connection stable
- [ ] PostgreSQL queries optimized
- [ ] Docker containers running without restarts

### Production Readiness Checklist

- [ ] 5+ retailers working reliably
- [ ] Multimodal search (image/voice) tested
- [ ] Rate limiting configured
- [ ] CAPTCHA solving integrated (2Captcha)
- [ ] Monitoring & alerting in place
- [ ] Rollback procedure documented
- [ ] Load testing completed
- [ ] Security audit done

---

## 🎓 Learning Resources & Documentation

### Key Files Reference
```
System Status:          SYSTEM_STATUS.md
Debugging Guide:        DEBUGGING_GUIDE.md
Quick Start:            QUICK_START.md
Architecture:           This file
Performance Metrics:    SYSTEM_STATUS.md#Performance
```

### API Documentation
- **Web Service**: http://localhost:8000/docs (OpenAPI/Swagger)
- **Scrapy Direct**: http://localhost:5000/docs (if available)
- **Redis CLI**: `redis-cli` (local development)

### Docker Management
```bash
# View logs with context
docker logs test_model-web-1 -f --tail 100 | grep "search"

# Restart services
docker restart test_model-web-1
docker restart test_model-scrapy_scraper-1

# Check resource usage
docker stats test_model-web-1 test_model-scrapy_scraper-1
```

---

## 💡 Next Immediate Actions

### Today (Estimated Time: 1-2 hours)
1. **Fix cache detection** (15 min)
   - Verify Redis storage
   - Normalize cache keys
   - Test with repeated queries

2. **Fix multi-retailer filtering** (20 min)
   - Inspect product structure per retailer
   - Add safe price/title extraction
   - Add error handling

3. **Validate fixes** (30 min)
   - Run test suite
   - Check performance metrics
   - Update documentation

### This Week (Estimated Time: 4-8 hours)
1. **Expand retailer coverage** (2-4 hours)
   - Analyze failing retailers
   - Implement Selenium/API solutions
   - Test each retailer individually

2. **Test multimodal search** (1-2 hours)
   - Create test images/audio
   - Test CLIP image understanding
   - Test voice transcription

3. **Performance optimization** (1-2 hours)
   - Implement parallel requests
   - Add connection pooling
   - Benchmark improvements

### Next Phase (Estimated Time: 8-16 hours)
1. Frontend integration
2. Celery workers for scaling
3. CAPTCHA solving integration
4. Production hardening

---

## 📞 Support & Troubleshooting

### Common Issues

**Cache not working?**
- Check Redis connection: `redis-cli ping`
- Check stored keys: `redis-cli KEYS cache:*`
- Clear cache: `redis-cli FLUSHALL`

**Advanced filtering returns 500?**
- Check logs: `docker logs test_model-web-1 --tail 50`
- Verify product structure: `python debug_product_structure.py`
- Test single retailer first

**Services not starting?**
- Check Docker: `docker ps`
- Check logs: `docker logs [container-name]`
- Verify ports: `netstat -an | findstr :8000`
- Restart all: `docker-compose up -d`

**Performance degradation?**
- Check Redis connection
- Monitor memory usage: `docker stats`
- Check concurrent requests
- Review error logs for timeouts
