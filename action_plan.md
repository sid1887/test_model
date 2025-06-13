# Cumpair System - Immediate Action Plan

## Critical Issues Resolution Roadmap

### Issue #1: Web Scraping Complete Failure (HTTP 503)

**Problem**: 100% failure rate with HTTP 503 errors across all scraping attempts

### Root Cause Investigation Required:

1. **Check Scraping Service Status**

```text
bash
# Debug commands to run

curl -X POST "http://localhost:8000/api/v1/real-time-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test product", "limit": 5}'

# Check backend logs for scraping service errors

tail -f logs/scraping_service.log

```text

2. **Verify Target Website Accessibility**

```text
python
# Test script to check if target sites are blocking requests

import requests
import time

target_sites = [
    "https://www.amazon.com",
    "https://www.flipkart.com",
    "https://www.myntra.com"
]

for site in target_sites:
    try:
        response = requests.get(site, timeout=10)
        print(f"{site}: {response.status_code}")
    except Exception as e:
        print(f"{site}: ERROR - {e}")

```text

### Immediate Fixes to Implement:

1. **Add Request Headers and User Agent Rotation**

```text
python
# Update scraping service with proper headers

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

```text

2. **Implement Retry Logic with Exponential Backoff**

```text
python
import time
import random
from typing import Optional

async def scrape_with_retry(url: str, max_retries: int = 3) -> Optional[dict]:
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            await asyncio.sleep(random.uniform(1, 3))

            response = await make_request(url, headers=get_random_headers())
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Service unavailable - wait longer
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
                continue

        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            continue

    return None

```text

3. **Add Circuit Breaker Pattern**

```text
python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

```text

### Issue #2: Text Search Returns Empty Results

**Problem**: All text searches succeed but return 0 results

### Investigation Steps:

1. **Check Database Content**

```text
sql
-- Connect to PostgreSQL and run:
SELECT COUNT(*) FROM products;
SELECT * FROM products LIMIT 10;
SELECT * FROM product_search_vectors LIMIT 5;

```text

2. **Test Search Query Logic**

```text
python
# Create test script to verify search functionality

test_queries = [
    "wall clock",
    "painting",
    "soap tray",
    "diary pen",
    "fan"
]

for query in test_queries:
    # Test direct database search
    result = await search_products_in_db(query)
    print(f"Query: {query} -> Results: {len(result)}")

```text

### Immediate Fixes:

1. **Populate Database with Test Products**

```text
python
# Create database seeding script

test_products = [
    {
        "name": "Floral Print Round Wall Clock",
        "category": "home_decor",
        "brand": "Generic",
        "price": 25.99,
        "description": "Beautiful floral pattern wall clock"
    },
    # Add all 100 test products from CSV
]

async def seed_database():
    for product in test_products:
        await create_product(product)
        print(f"Added: {product['name']}")

```text

2. **Implement Fuzzy Search**

```text
python
from fuzzywuzzy import fuzz, process

async def fuzzy_product_search(query: str, threshold: int = 60):
    all_products = await get_all_products()

    matches = []
    for product in all_products:
        similarity = fuzz.ratio(query.lower(), product.name.lower())
        if similarity >= threshold:
            matches.append((product, similarity))

    return sorted(matches, key=lambda x: x[1], reverse=True)

```text

### Issue #3: Timeout Errors in Text Search

**Problem**: Some queries timeout after 10 seconds

### Immediate Fixes:

1. **Increase Timeout Configuration**

```text
python
# Update API client timeout settings

client = httpx.AsyncClient(timeout=30.0)  # Increase from 10s to 30s

```text

2. **Add Database Query Optimization**

```text
sql
-- Add proper indices for search performance
CREATE INDEX IF NOT EXISTS idx_products_name_gin ON products USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_products_description_gin ON products USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

```text

3. **Implement Query Caching**

```text
python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def cached_search(query: str):
    cache_key = f"search:{hash(query)}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        return json.loads(cached_result)

    result = await perform_search(query)
    redis_client.setex(cache_key, 300, json.dumps(result))  # 5 min cache
    return result

```text

## Implementation Priority

### Week 1 - Critical Fixes

- [ ] Debug web scraping HTTP 503 errors

- [ ] Add request headers and user agent rotation

- [ ] Implement retry logic with exponential backoff

- [ ] Seed database with test products

- [ ] Increase API timeout configurations

### Week 2 - Stability Improvements

- [ ] Add circuit breaker pattern for scraping

- [ ] Implement fuzzy search for text queries

- [ ] Add database query optimization indices

- [ ] Create Redis caching layer

- [ ] Add comprehensive logging and monitoring

### Testing Validation

After implementing fixes, re-run the comprehensive test:

```text
bash
cd d:\dev_packages\test_model
python comprehensive_test_fixed.py

```text

### Success Criteria:

- Web scraping success rate > 80%

- Text search returns relevant results

- All response times < 10 seconds

- Zero timeout errors

## Monitoring Setup

1. **Add Health Check Monitoring**

```text
python
@app.get("/api/v1/health/detailed")
async def detailed_health():
    return {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
        "scraping_service": await check_scraping_service(),
        "ai_models": await check_ai_models_status()
    }

```text

2. **Create Performance Dashboard**

- Success/failure rates by component

- Response time distributions

- Error tracking and alerting

- Resource utilization monitoring

---
*Action Plan Created: [Current Date]*
*Priority: CRITICAL - Implement within 1-2 weeks*
