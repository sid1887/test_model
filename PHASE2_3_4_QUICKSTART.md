## Quick Start: Phase 2-4 Services

### Environment Setup

```bash
# 1. Create .env file (optional, for NewsAPI)
echo "NEWSAPI_KEY=your_key_here" > .env

# 2. Apply database migrations
# The following will be done automatically when postgres starts:
# - 01_extensions.sql (pgvector, pg_trgm, etc)
# - 02_schema.sql (products, prices, raw_scrapes, embeddings, etc)
# - 03_indexes.sql (optimization indexes)
# - 07_phase2_extensions.sql (new tables for Phase 2-4)
```

### Start Services

```bash
# Start all Phase 2-4 services
docker-compose -f docker-compose.services.yml --profile phase2 up -d

# Or start full microservices stack
docker-compose -f docker-compose.services.yml --profile full up -d

# Check service health
curl http://localhost:8006/health  # data-pipeline
curl http://localhost:8007/health  # scraper-optimization
curl http://localhost:8008/health  # multi-source-integration
```

---

## API Usage Examples

### Data Pipeline Service (8006)

#### 1. Record Price from Retailer
```bash
curl -X POST http://localhost:8006/api/prices/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "site_name": "amazon",
    "site_product_id": "B123456",
    "site_url": "https://amazon.com/dp/B123456",
    "price": 99.99,
    "original_price": 149.99,
    "discount_percent": 33.33,
    "in_stock": true,
    "currency": "USD"
  }'
```

#### 2. Get Price History
```bash
curl http://localhost:8006/api/prices/product/550e8400-e29b-41d4-a716-446655440000?days=30
```

#### 3. Detect Price Changes
```bash
curl http://localhost:8006/api/prices/changes/550e8400-e29b-41d4-a716-446655440000
```

#### 4. Link Duplicate Products
```bash
curl -X POST http://localhost:8006/api/products/link \
  -H "Content-Type: application/json" \
  -d '{
    "products_to_merge": ["id1", "id2", "id3"],
    "merge_metadata": true
  }'
```

#### 5. Find Deduplication Candidates
```bash
curl "http://localhost:8006/api/products/deduplicate-candidates?limit=50"
```

---

### Scraper Optimization Service (8007)

#### 1. Batch Concurrent Scraping
```bash
curl -X POST http://localhost:8007/api/scraper/batch \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [
      {
        "retailer": "amazon",
        "url": "https://api.amazon.com/products/electronics",
        "product_id": "prod_1"
      },
      {
        "retailer": "flipkart",
        "url": "https://api.flipkart.com/products/phones",
        "product_id": "prod_2"
      }
    ],
    "use_cache": true,
    "cache_only": false
  }'
```

#### 2. Cache Statistics
```bash
curl http://localhost:8007/api/cache/stats
# Returns: memory_used, keys_count, connected_clients
```

#### 3. Clear Retailer Cache
```bash
curl -X POST http://localhost:8007/api/cache/clear/amazon
```

#### 4. Warmup Cache
```bash
curl -X POST "http://localhost:8007/api/cache/warmup?retailer=amazon&force=false"
```

#### 5. Schedule Hourly Scrape
```bash
curl -X POST http://localhost:8007/api/scheduler/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "retailer": "amazon",
    "schedule_type": "hourly",
    "priority": 5
  }'
```

#### 6. Set Custom Rate Limit
```bash
curl -X POST "http://localhost:8007/api/distribution/set-rate-limit/amazon?requests_per_second=10&concurrent_requests=15"
```

---

### Multi-Source Integration Service (8008)

#### 1. Fetch News Articles
```bash
curl -X POST http://localhost:8008/api/news/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "query": "product pricing",
    "category": "tech",
    "language": "en",
    "sort_by": "publishedAt",
    "page_size": 50
  }'
```

#### 2. Get Trending News
```bash
curl "http://localhost:8008/api/news/trending?days=7&limit=20"
```

#### 3. Search News
```bash
curl "http://localhost:8008/api/news/search?q=cryptocurrency+market&limit=50"
```

#### 4. Fetch Cryptocurrency Prices
```bash
curl -X POST http://localhost:8008/api/crypto/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["bitcoin", "ethereum"],
    "vs_currency": "usd"
  }'
```

#### 5. Get Crypto Price History
```bash
curl "http://localhost:8008/api/crypto/prices/BTC?hours=24"
```

#### 6. Get Top Cryptocurrencies
```bash
curl "http://localhost:8008/api/crypto/top?limit=20"
```

#### 7. Fetch Stock Data
```bash
curl -X POST "http://localhost:8008/api/stocks/fetch?ticker=AAPL"
```

#### 8. Get Stock Price History
```bash
curl "http://localhost:8008/api/stocks/AAPL?days=30"
```

---

## Database Queries

### View Product Price History
```sql
SELECT site_name, price, discount_percent, in_stock, scraped_at
FROM product_prices
WHERE product_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY scraped_at DESC
LIMIT 100;
```

### Find Price Trends
```sql
SELECT
  product_id,
  site_name,
  AVG(price) as avg_price,
  MIN(price) as min_price,
  MAX(price) as max_price,
  COUNT(*) as price_points
FROM product_prices
WHERE scraped_at > NOW() - INTERVAL '7 days'
GROUP BY product_id, site_name
ORDER BY product_id;
```

### Get Latest News
```sql
SELECT id, title, source, published_at
FROM news_articles
WHERE published_at > NOW() - INTERVAL '24 hours'
ORDER BY published_at DESC
LIMIT 20;
```

### Track Crypto Prices
```sql
SELECT DISTINCT ON (symbol) symbol, price, change_24h, recorded_at
FROM crypto_prices
WHERE recorded_at > NOW() - INTERVAL '1 hour'
ORDER BY symbol, recorded_at DESC;
```

### Monitor Product Merges
```sql
SELECT original_id, canonical_id, merged_at
FROM product_versions
ORDER BY merged_at DESC
LIMIT 20;
```

---

## Performance Optimization Tips

### 1. Scraper Optimization
- **Batch Size:** Process 20-50 URLs at once for best throughput
- **Cache TTL:** Increase to 24 hours for stable data
- **Rate Limits:** Adjust per retailer based on their API limits

```bash
# Example: Set high-performance limits for Amazon
curl -X POST "http://localhost:8007/api/distribution/set-rate-limit/amazon?requests_per_second=20&concurrent_requests=30"

# Warmup cache before batch operations
curl -X POST "http://localhost:8007/api/cache/warmup?retailer=amazon&force=true"
```

### 2. Data Pipeline
- **Batch Insert:** When ingesting prices, group by product for bulk operations
- **Index Usage:** Database will auto-use indexes for product lookups
- **Dedup:** Run deduplication weekly to keep product catalog clean

### 3. Multi-Source Integration
- **Cache News:** NewsAPI articles change slowly, safe to cache 24 hours
- **Crypto Updates:** Fetch every 5-15 minutes for real-time data
- **Stock Data:** Update after market close (once per day sufficient)

---

## Troubleshooting

### Service Not Responding
```bash
# Check service logs
docker logs test_model-data-pipeline-1
docker logs test_model-scraper-optimization-1
docker logs test_model-multi-source-integration-1

# Verify database connection
docker exec test_model-postgres-1 psql -U postgres -d cumpair -c "SELECT version();"

# Check Redis
docker exec test_model-redis-1 redis-cli ping
```

### Out of Cache Space
```bash
# Clear all cache
docker exec test_model-redis-1 redis-cli FLUSHDB

# Or clear specific retailer
curl -X POST http://localhost:8007/api/cache/clear/amazon
```

### Database Migration Issues
```bash
# Connect to database
docker exec -it test_model-postgres-1 psql -U postgres -d cumpair

# Check tables
\dt

# Verify extensions
SELECT * FROM pg_extension;
```

### NewsAPI Not Working
- Verify `NEWSAPI_KEY` in environment
- Check API key is valid: https://newsapi.org
- Ensure query format is correct

---

## Next Steps

1. **Phase 5:** Implement Celery background jobs for async processing
2. **Phase 6:** Optimize database queries and add TimescaleDB
3. **Phase 7:** Setup comprehensive Redis caching strategy
4. **Phase 8:** Build FAISS vector index for similarity search
5. **Phase 9:** Enhance API Gateway with rate limiting
6. **Phase 10+:** Notifications, search, testing, deployment

---

## Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & Celery |
| API Gateway | 8000 | Main entry point |
| AI Models | 8001 | ML endpoints |
| HF Connector | 8002 | NLP tasks |
| Speech/Image | 8003 | Media processing |
| Feature Extract | 8004 | Embeddings |
| Scrapy Wrapper | 8005 | Scraper HTTP |
| **Data Pipeline** | **8006** | **Product/Price linking** |
| **Scraper Opt** | **8007** | **Concurrent scraping** |
| **Multi-Source** | **8008** | **News/Crypto/Stocks** |

---

Created: 2025-11-19
Last Updated: Phase 4 Complete
