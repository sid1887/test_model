# Multi-Tier Caching Architecture

**Phase:** 6 - Database Optimization
**Objective:** Implement 3-tier caching (Redis, PostgreSQL, Application) to achieve 80%+ cache hit rate
**Expected Improvement:** 40% latency reduction, 60% database load reduction

---

## Overview: 3-Tier Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ L3: In-Memory Cache (LRU, application process memory)     │  │
│  │ - Hot query results (top searches, trending products)     │  │
│  │ - User profiles (most active users)                       │  │
│  │ - Recommendation cache (per-user, 5 min TTL)             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           ↓ (cache miss)
┌─────────────────────────────────────────────────────────────────┐
│                      Redis Layer                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ L2: Redis Cache (distributed, 1-24 hour TTL)             │  │
│  │ - Search history (per user, 30 days)                     │  │
│  │ - Trending searches (7 days)                             │  │
│  │ - User region context (1 hour)                           │  │
│  │ - Geolocation results (24 hours)                         │  │
│  │ - Wishlist (1 hour)                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           ↓ (cache miss)
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Layer                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ L1: PostgreSQL Materialized Views (2-24 hour refresh)    │  │
│  │ - Product summaries (ratings, wishlists, purchases)       │  │
│  │ - Regional inventory (stock, pricing)                     │  │
│  │ - Trending products (by region)                           │  │
│  │ - Top recommendations (pre-computed)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section 1: L3 Cache - In-Memory (Application)

### Purpose
Fastest cache layer - application process memory using Python LRU cache for truly hot data.

### Implementation

```python
from functools import lru_cache
import asyncio
from typing import Dict, Any

class L3CacheManager:
    """In-memory L3 cache (application-level)"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, tuple] = {}  # {key: (value, expiry_time)}

    async def get(self, key: str) -> Any:
        """Get from L3 cache (no expiry check, instant)"""
        if key in self.cache:
            value, expiry = self.cache[key]
            # Check expiry (in-memory, very fast)
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set in L3 cache with TTL"""
        expiry_time = time.time() + ttl
        self.cache[key] = (value, expiry_time)

        # Simple LRU: remove oldest if over max size
        if len(self.cache) > self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

# Shared L3 cache instance
l3_cache = L3CacheManager(max_size=5000)

# Usage example
async def get_trending_products():
    """Cache top trending products in L3"""
    cache_key = "trending:products:global"

    # Check L3 first (microseconds)
    cached = await l3_cache.get(cache_key)
    if cached:
        return cached

    # Fall through to L2/L1
    trending = await get_from_db()

    # Cache in L3 (5 min TTL for hot data)
    await l3_cache.set(cache_key, trending, ttl=300)
    return trending
```

### L3 Cache Strategy

**What to Cache:**
1. **Top Searches** (updated hourly)
   - Top 100 trending queries
   - TTL: 5 minutes
   - Hit rate: 60%+ (Zipfian distribution)

2. **Popular Products** (updated daily)
   - Top 500 products by category
   - TTL: 30 minutes
   - Hit rate: 70%+

3. **User Profiles** (updated on login)
   - Currently logged-in users (~100 active)
   - TTL: 1 minute
   - Hit rate: 95%+

4. **Recommendation Warmth**
   - Pre-computed recommendations for active users
   - TTL: 10 minutes
   - Hit rate: 80%+

**L3 Cache Metrics:**
- Hit rate: 70-80%
- Latency: <1ms
- Memory per service: ~50MB
- Max concurrent users cached: 5,000

---

## Section 2: L2 Cache - Redis (Distributed)

### Purpose
Distributed cache layer for:
- Inter-service sharing
- Session persistence
- High-frequency queries
- Rate limiting data

### Redis Configuration

```yaml
# docker-compose.phase5-core.yml additions
redis:
  image: redis:7-alpine
  command:
    - redis-server
    - --maxmemory 512mb
    - --maxmemory-policy allkeys-lru
    - --databases 5
    - --appendonly yes
  ports:
    - "6379:6379"
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

### Data Structures & TTLs

```python
class L2CacheManager:
    """Distributed L2 cache in Redis"""

    def __init__(self, redis_client):
        self.redis = redis_client

    # ============================================================
    # Search Service Caching
    # ============================================================

    async def cache_search_history(self, user_id: str, search_query: str,
                                   result_count: int, search_type: str):
        """Store user search history (List, 30-day TTL)"""
        history_entry = {
            'query': search_query,
            'type': search_type,
            'result_count': result_count,
            'timestamp': datetime.utcnow().isoformat()
        }

        key = f"search_history:{user_id}"
        await self.redis.lpush(key, json.dumps(history_entry))

        # Keep last 100 searches
        await self.redis.ltrim(key, 0, 99)

        # 30-day TTL
        await self.redis.expire(key, 86400 * 30)

    async def get_search_history(self, user_id: str, limit: int = 20):
        """Retrieve user search history"""
        key = f"search_history:{user_id}"
        entries = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(e) for e in entries]

    async def cache_trending_searches(self, query: str):
        """Track trending searches (Sorted Set, 7-day TTL)"""
        key = "trending_searches"
        await self.redis.zincrby(key, 1, query)  # Increment counter
        await self.redis.expire(key, 86400 * 7)

    async def get_trending_searches(self, limit: int = 10):
        """Get top trending searches"""
        key = "trending_searches"
        trending = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)
        return [(query.decode(), int(score)) for query, score in trending]

    # ============================================================
    # User Service Caching
    # ============================================================

    async def cache_user_profile(self, user_id: str, profile: Dict):
        """Store user profile (String, 1-hour TTL)"""
        key = f"user_profile:{user_id}"
        await self.redis.setex(
            key,
            3600,  # 1 hour
            json.dumps(profile, default=str)
        )

    async def get_user_profile(self, user_id: str):
        """Retrieve cached user profile"""
        key = f"user_profile:{user_id}"
        profile = await self.redis.get(key)
        return json.loads(profile) if profile else None

    async def cache_recommendations(self, user_id: str, recommendations: List):
        """Store user recommendations (String, 10-minute TTL)"""
        key = f"recommendations:{user_id}"
        await self.redis.setex(
            key,
            600,  # 10 minutes
            json.dumps(recommendations, default=str)
        )

    async def invalidate_recommendations(self, user_id: str):
        """Invalidate user recommendations when wishlist changes"""
        key = f"recommendations:{user_id}"
        await self.redis.delete(key)

    # ============================================================
    # Geolocation Service Caching
    # ============================================================

    async def cache_geolocation(self, ip_address: str, location: Dict):
        """Store IP geolocation (String, 24-hour TTL)"""
        key = f"geoip:{ip_address}"
        await self.redis.setex(
            key,
            86400,  # 24 hours
            json.dumps(location)
        )

    async def get_geolocation(self, ip_address: str):
        """Retrieve cached IP geolocation"""
        key = f"geoip:{ip_address}"
        location = await self.redis.get(key)
        return json.loads(location) if location else None

    async def cache_user_context(self, user_id: str, context: Dict):
        """Store complete user region context (String, 1-hour TTL)"""
        key = f"user_context:{user_id}"
        await self.redis.setex(
            key,
            3600,  # 1 hour
            json.dumps(context, default=str)
        )

    async def get_user_context(self, user_id: str):
        """Retrieve user region context"""
        key = f"user_context:{user_id}"
        context = await self.redis.get(key)
        return json.loads(context) if context else None

    # ============================================================
    # Cache Invalidation
    # ============================================================

    async def invalidate_product(self, product_id: str):
        """Invalidate all caches for a product"""
        patterns = [
            f"search:full-text:*",
            f"search:semantic:*",
            f"product_details:{product_id}",
            f"regional_pricing:{product_id}:*"
        ]

        for pattern in patterns:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)

    async def invalidate_user_caches(self, user_id: str):
        """Invalidate all caches for a user"""
        patterns = [
            f"user_profile:{user_id}",
            f"recommendations:{user_id}",
            f"user_context:{user_id}",
            f"wishlist:{user_id}"
        ]

        for key in patterns:
            await self.redis.delete(key)
```

### L2 Cache Statistics

| Cache Key | Type | TTL | Hit Rate | Size/Item |
|-----------|------|-----|----------|-----------|
| search_history:* | List | 30d | 40% | 200B |
| trending_searches | ZSet | 7d | 65% | 100B |
| user_profile:* | String | 1h | 85% | 500B |
| recommendations:* | String | 10m | 60% | 2KB |
| geoip:* | String | 24h | 70% | 300B |
| user_context:* | String | 1h | 75% | 1KB |

**Total Redis Memory:** ~512MB (configured)
**Expected Hit Rate:** 65%
**Latency:** 5-10ms per lookup

---

## Section 3: L1 Cache - Materialized Views (PostgreSQL)

### Purpose
Pre-computed query results for complex aggregations that don't need real-time accuracy.

### Materialized Views

```sql
-- ============================================================
-- Product Summaries (hourly refresh)
-- ============================================================

CREATE MATERIALIZED VIEW mv_product_summary AS
SELECT
    p.id,
    p.title,
    p.price,
    p.rating,
    p.reviews_count,
    p.category,
    p.retailer,
    COUNT(DISTINCT w.user_id) as wishlist_count,
    COUNT(DISTINCT pu.user_id) as purchase_count,
    MAX(pu.purchased_at) as last_purchase_date,
    AVG(rp.regional_price) as avg_regional_price,
    COUNT(DISTINCT rp.region_id) as regions_available
FROM products p
LEFT JOIN wishlist w ON p.id = w.product_id
LEFT JOIN purchases pu ON p.id = pu.product_id
LEFT JOIN regional_products rp ON p.id = rp.product_id
WHERE p.enabled = true
GROUP BY p.id
WITH DATA;

CREATE INDEX idx_mv_product_summary_rating
    ON mv_product_summary(rating DESC, reviews_count DESC);

-- Refresh hourly via cron job
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_summary;

-- ============================================================
-- Regional Inventory (2-hour refresh)
-- ============================================================

CREATE MATERIALIZED VIEW mv_regional_inventory AS
SELECT
    rp.region_id,
    rp.product_id,
    p.title,
    p.price as base_price,
    rp.local_title,
    rp.availability,
    rp.stock_level,
    rp.fulfillment_center,
    rp2.regional_price,
    rp2.markup_percentage,
    r.currency,
    r.shipping_cost,
    r.tax_rate
FROM regional_products rp
JOIN products p ON rp.product_id = p.id
LEFT JOIN regional_pricing rp2 ON (rp.product_id = rp2.product_id
    AND rp.region_id = rp2.region_id
    AND rp2.expiry_date > NOW())
JOIN regions r ON rp.region_id = r.id
WHERE rp2.expiry_date > NOW() OR rp2.id IS NULL
WITH DATA;

CREATE INDEX idx_mv_regional_inventory_region
    ON mv_regional_inventory(region_id, availability);

-- ============================================================
-- Popular Products by Category (daily refresh)
-- ============================================================

CREATE MATERIALIZED VIEW mv_popular_by_category AS
SELECT
    category,
    product_id,
    title,
    rating,
    reviews_count,
    row_number() OVER (PARTITION BY category ORDER BY reviews_count DESC) as category_rank
FROM products
WHERE enabled = true AND reviews_count > 0
WITH DATA;

CREATE INDEX idx_mv_popular_category_rank
    ON mv_popular_by_category(category, category_rank);

-- ============================================================
-- Top Recommendations (daily refresh, pre-computed for popular users)
-- ============================================================

CREATE MATERIALIZED VIEW mv_top_recommendations AS
SELECT
    u.id as user_id,
    p.id as product_id,
    p.title,
    p.price,
    p.rating,
    'trending' as reason,
    row_number() OVER (PARTITION BY u.id ORDER BY p.reviews_count DESC) as rank
FROM users u
CROSS JOIN LATERAL (
    SELECT id, title, price, rating, reviews_count
    FROM products
    WHERE reviews_count > (SELECT avg(reviews_count) FROM products)
    ORDER BY reviews_count DESC
    LIMIT 20
) p
LIMIT 100000;  -- Pre-compute for top 1000 active users

CREATE INDEX idx_mv_recommendations_user
    ON mv_top_recommendations(user_id, rank);
```

### Refresh Schedule

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Hourly refresh
@scheduler.scheduled_job('cron', hour='*')
async def refresh_product_summary():
    """Refresh product summary materialized view"""
    async with db.acquire() as conn:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_summary")
    logger.info("Refreshed mv_product_summary")

# Every 2 hours
@scheduler.scheduled_job('cron', hour='*/2')
async def refresh_regional_inventory():
    """Refresh regional inventory view"""
    async with db.acquire() as conn:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_regional_inventory")
    logger.info("Refreshed mv_regional_inventory")

# Daily
@scheduler.scheduled_job('cron', hour=2)
async def refresh_popular_products():
    """Refresh popular products by category"""
    async with db.acquire() as conn:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_by_category")
    logger.info("Refreshed mv_popular_by_category")

# Start scheduler
scheduler.start()
```

### L1 View Performance

| View | Refresh Interval | Query Time | Staleness |
|------|-----------------|-----------|-----------|
| mv_product_summary | 1 hour | 5ms | <1 hour |
| mv_regional_inventory | 2 hours | 8ms | <2 hours |
| mv_popular_by_category | 24 hours | 3ms | <24 hours |
| mv_top_recommendations | 6 hours | 10ms | <6 hours |

---

## Section 4: Cache Invalidation Strategy

### Event-Driven Invalidation

```python
class CacheInvalidator:
    """Manage cache invalidation across all layers"""

    async def on_product_update(self, product_id: str):
        """Product updated - invalidate related caches"""

        # L3: Clear in-memory
        await l3_cache.clear_pattern(f"*{product_id}*")

        # L2: Clear Redis
        keys = await redis.keys(f"*{product_id}*")
        if keys:
            await redis.delete(*keys)

        # L1: Mark materialized view as stale
        # (Will be refreshed on next schedule)

    async def on_wishlist_change(self, user_id: str, product_id: str):
        """Wishlist changed - invalidate recommendations"""
        await l2_cache.invalidate_recommendations(user_id)

    async def on_purchase(self, user_id: str, product_id: str):
        """Purchase made - invalidate user caches"""
        await l2_cache.invalidate_user_caches(user_id)

        # Also invalidate product popularity
        await redis.delete(f"product_popularity:{product_id}")

    async def on_price_change(self, region_id: str, product_id: str):
        """Regional price changed - invalidate related caches"""
        # Invalidate regional pricing caches
        pattern = f"regional_pricing:{region_id}:{product_id}*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)

        # Invalidate regional inventory view
        # (Will be refreshed on next schedule)
```

---

## Section 5: Cache Warming Strategy

### Pre-load Caches on Startup

```python
async def warm_caches():
    """Pre-load caches on service startup"""

    logger.info("Warming up L3 cache...")

    # Pre-load top 100 searches
    top_searches = await db.fetch(
        "SELECT query FROM search_history GROUP BY query ORDER BY COUNT(*) DESC LIMIT 100"
    )
    for row in top_searches:
        # Trigger CLIP encoding + cache
        await search_semantic(row['query'])

    logger.info("Warming up L2 cache...")

    # Pre-load trending products
    trending = await db.fetch(
        "SELECT * FROM products ORDER BY reviews_count DESC LIMIT 500"
    )
    await l2_cache.set("trending:products", trending, ttl=3600)

    # Pre-load popular products per category
    categories = await db.fetch("SELECT DISTINCT category FROM products")
    for cat_row in categories:
        category = cat_row['category']
        popular = await db.fetch(
            "SELECT * FROM products WHERE category = $1 ORDER BY reviews_count DESC LIMIT 20",
            category
        )
        await l2_cache.set(f"popular:category:{category}", popular, ttl=3600)

    logger.info("Cache warming complete!")

# Call on service startup
@app.on_event("startup")
async def startup():
    await warm_caches()
```

---

## Section 6: Distributed Cache for Multi-Service Deployment

### Redis Cluster Configuration

```yaml
# docker-compose with Redis cluster
redis-cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
  ports:
    - "7000:7000"
    - "7001:7001"
    - "7002:7002"
    - "7003:7003"
    - "7004:7004"
    - "7005:7005"
```

### Client Configuration

```python
from redis.asyncio import Redis
from redis.asyncio.cluster import RedisCluster

# Single-node (development)
redis = await Redis.from_url("redis://redis:6379/0")

# Cluster (production)
redis_cluster = await RedisCluster.from_url(
    "redis://redis-cluster:7000",
    skip_full_coverage_check=True
)
```

---

## Section 7: Monitoring Cache Performance

```python
class CacheMetrics:
    """Track cache performance metrics"""

    def __init__(self):
        self.l3_hits = 0
        self.l3_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.l1_queries = 0

    def get_hit_rates(self):
        """Calculate hit rates"""
        return {
            'l3_hit_rate': self.l3_hits / (self.l3_hits + self.l3_misses) if self.l3_hits + self.l3_misses > 0 else 0,
            'l2_hit_rate': self.l2_hits / (self.l2_hits + self.l2_misses) if self.l2_hits + self.l2_misses > 0 else 0,
            'total_hit_rate': (self.l3_hits + self.l2_hits) / (self.l3_hits + self.l3_misses + self.l2_hits + self.l2_misses + 1)
        }

# Global metrics
cache_metrics = CacheMetrics()

# Expose via Prometheus
@app.get("/metrics/cache")
async def cache_metrics():
    rates = cache_metrics.get_hit_rates()
    return {
        'l3_hit_rate': rates['l3_hit_rate'],
        'l2_hit_rate': rates['l2_hit_rate'],
        'total_hit_rate': rates['total_hit_rate']
    }
```

---

## Summary: Expected Performance Gains

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cache Hit Rate | 20% | 80% | 4x |
| Average Latency | 200ms | 50ms | 4x |
| Database Load | 100% | 30% | 3.3x |
| Throughput | 500 req/sec | 2,000 req/sec | 4x |

**Key Benefits:**
- ✅ 80%+ cache hit rate
- ✅ 4x latency reduction
- ✅ 70% database load reduction
- ✅ 4x throughput increase
- ✅ Horizontal scaling via Redis
- ✅ Fast cache invalidation strategy
