# Complete API Reference - Phase 2-4 Services

## Data Pipeline Service (Port 8006)

### Product Management

#### Link Products
```
POST /api/products/link
Content-Type: application/json

Request:
{
  "products_to_merge": ["id1", "id2", "id3"],
  "canonical_product_id": "id1",  // Optional
  "merge_metadata": true
}

Response (200):
{
  "status": "success",
  "canonical_product_id": "id1",
  "products_merged": 3,
  "merged_metadata": {...}
}
```

#### Find Deduplication Candidates
```
GET /api/products/deduplicate-candidates?limit=100

Response (200):
{
  "candidates_count": 45,
  "candidates": [
    {
      "product_1_id": "uuid1",
      "product_2_id": "uuid2",
      "title_1": "Product A",
      "title_2": "Product B",
      "title_similarity": 0.92,
      "category": "Electronics"
    },
    ...
  ]
}
```

#### Normalize Product Data
```
POST /api/products/normalize?product_id=uuid

Response (200):
{
  "status": "success",
  "product": {
    "id": "uuid",
    "title": "Normalized Title",
    "category": "Electronics > Mobile Phones",
    "metadata": {...}
  }
}
```

#### Validate Products
```
POST /api/validate/products

Response (200):
{
  "total_products": 150,
  "with_issues": 8,
  "issues": [
    {
      "product_id": "uuid",
      "issues": ["missing_image", "price_outlier"]
    }
  ]
}
```

### Price Management

#### Record Price Snapshot
```
POST /api/prices/snapshot
Content-Type: application/json

Request:
{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "site_name": "amazon",
  "site_product_id": "B123456",
  "site_url": "https://amazon.com/dp/B123456",
  "price": 99.99,
  "original_price": 149.99,
  "discount_percent": 33.33,
  "in_stock": true,
  "currency": "USD",
  "scraped_data": {
    "rating": 4.5,
    "reviews": 2000
  }
}

Response (200):
{
  "status": "success",
  "price_id": 12345,
  "recorded_at": "2025-11-19T10:30:00Z"
}
```

#### Get Product Price History
```
GET /api/prices/product/550e8400-e29b-41d4-a716-446655440000?days=30

Response (200):
{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "prices": [
    {
      "site_name": "amazon",
      "price": 99.99,
      "original_price": 149.99,
      "discount_percent": 33.33,
      "in_stock": true,
      "scraped_at": "2025-11-19T10:30:00Z",
      "currency": "USD"
    }
  ],
  "statistics": {
    "average": 105.50,
    "minimum": 89.99,
    "maximum": 149.99,
    "count": 25
  }
}
```

#### Detect Price Changes
```
GET /api/prices/changes/550e8400-e29b-41d4-a716-446655440000

Response (200):
{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "all_changes": [
    {
      "site_name": "amazon",
      "prev_price": 109.99,
      "current_price": 99.99,
      "percent_change": -9.09,
      "scraped_at": "2025-11-19T10:30:00Z"
    }
  ],
  "significant_changes": [
    // Only changes > 10%
  ],
  "total_significant": 3
}
```

### News Management

#### Ingest News Article
```
POST /api/news/ingest
Content-Type: application/json

Request:
{
  "title": "Apple announces new iPhone",
  "content": "Full article content...",
  "source": "TechNews",
  "url": "https://technews.com/article",
  "category": "tech",
  "published_at": "2025-11-19T08:00:00Z"
}

Response (200):
{
  "status": "success",
  "article_id": "uuid",
  "ingested_at": "2025-11-19T10:30:00Z"
}
```

#### Get Product Mentions in News
```
GET /api/news/product-mentions/550e8400-e29b-41d4-a716-446655440000

Response (200):
{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "mention_count": 5,
  "mentions": [
    {
      "id": "article_uuid",
      "title": "Article title",
      "content": "Article content...",
      "source": "NewsSource",
      "category": "tech",
      "published_at": "2025-11-19T08:00:00Z",
      "mention_type": "direct"
    }
  ]
}
```

### Health Check
```
GET /health

Response (200):
{
  "status": "healthy"
}
```

---

## Scraper Optimization Service (Port 8007)

### Scraping

#### Batch Concurrent Scraping
```
POST /api/scraper/batch
Content-Type: application/json

Request:
{
  "jobs": [
    {
      "retailer": "amazon",
      "url": "https://api.amazon.com/products/electronics",
      "product_id": "prod_1",
      "metadata": {"category": "phones"}
    },
    {
      "retailer": "flipkart",
      "url": "https://api.flipkart.com/products/deals",
      "product_id": "prod_2"
    }
  ],
  "use_cache": true,
  "cache_only": false
}

Response (200):
{
  "status": "success",
  "stats": {
    "total_attempted": 2,
    "successful": 2,
    "failed": 0,
    "cached": 1,
    "avg_time_ms": 325.5
  },
  "results": [
    {
      "retailer": "amazon",
      "url": "https://...",
      "product_id": "prod_1",
      "data": {...},
      "from_cache": false,
      "time_ms": 425.0,
      "attempt": 1
    },
    {
      "retailer": "flipkart",
      "url": "https://...",
      "product_id": "prod_2",
      "data": {...},
      "from_cache": true,
      "time_ms": 0
    }
  ]
}
```

### Caching

#### Cache Statistics
```
GET /api/cache/stats

Response (200):
{
  "status": "online",
  "memory_used": "512.5 MB",
  "memory_peak": "1.2 GB",
  "keys_count": 15432,
  "connected_clients": 5
}
```

#### Clear Retailer Cache
```
POST /api/cache/clear/amazon

Response (200):
{
  "status": "success",
  "cleared_count": 1250
}
```

#### Warmup Cache
```
POST /api/cache/warmup?retailer=amazon&force=false

Response (200):
{
  "status": "success",
  "urls_queued": 3
}
```

### Scheduling

#### Schedule Recurring Scrape
```
POST /api/scheduler/schedule
Content-Type: application/json

Request:
{
  "retailer": "amazon",
  "schedule_type": "hourly",  // 'hourly', 'daily', 'weekly'
  "priority": 5  // 1-10
}

Response (200):
{
  "status": "success",
  "schedule_key": "schedule:amazon:hourly",
  "schedule_data": {
    "retailer": "amazon",
    "schedule_type": "hourly",
    "priority": 5,
    "created_at": "2025-11-19T10:30:00Z",
    "enabled": true
  }
}
```

#### Get Scheduled Jobs
```
GET /api/scheduler/scheduled

Response (200):
{
  "total_scheduled": 5,
  "scheduled_jobs": [
    {
      "retailer": "amazon",
      "schedule_type": "hourly",
      "priority": 5,
      "created_at": "2025-11-19T10:30:00Z",
      "enabled": true
    }
  ]
}
```

#### Disable Schedule
```
POST /api/scheduler/disable/amazon

Response (200):
{
  "status": "success",
  "disabled_count": 2
}
```

### Rate Limiting

#### Get Rate Limit
```
GET /api/distribution/rate-limit/amazon

Response (200):
{
  "retailer": "amazon",
  "limits": {
    "requests_per_second": 5,
    "requests_per_minute": 200,
    "requests_per_hour": 5000,
    "concurrent_requests": 10
  }
}
```

#### Set Rate Limit
```
POST /api/distribution/set-rate-limit/amazon?requests_per_second=10&concurrent_requests=15

Response (200):
{
  "status": "success",
  "retailer": "amazon",
  "limits": {
    "requests_per_second": 10,
    "concurrent_requests": 15
  }
}
```

### Health Check
```
GET /health

Response (200):
{
  "status": "healthy",
  "redis": "healthy",
  "max_concurrent": 20,
  "request_timeout": 30
}
```

---

## Multi-Source Integration Service (Port 8008)

### News

#### Fetch News Articles
```
POST /api/news/fetch
Content-Type: application/json

Request:
{
  "query": "product pricing",
  "category": "tech",  // Optional
  "language": "en",
  "sort_by": "publishedAt",  // 'relevancy', 'popularity', 'publishedAt'
  "page_size": 50
}

Response (200):
{
  "status": "success",
  "articles_fetched": 50,
  "articles": [
    {
      "title": "Article title",
      "description": "Description...",
      "source": {"name": "Source Name"},
      "url": "https://...",
      "publishedAt": "2025-11-19T08:00:00Z",
      "urlToImage": "https://..."
    }
  ]
}
```

#### Get Trending News
```
GET /api/news/trending?days=7&limit=20

Response (200):
{
  "trending_count": 20,
  "articles": [
    {
      "id": "uuid",
      "title": "Trending article",
      "content": "...",
      "source": "NewsSource",
      "url": "https://...",
      "category": "tech",
      "published_at": "2025-11-19T08:00:00Z",
      "ingested_at": "2025-11-19T10:30:00Z"
    }
  ]
}
```

#### Search News
```
GET /api/news/search?q=cryptocurrency+market&limit=50

Response (200):
{
  "query": "cryptocurrency market",
  "results": 12,
  "articles": [...]
}
```

### Cryptocurrency

#### Fetch Crypto Prices
```
POST /api/crypto/fetch
Content-Type: application/json

Request:
{
  "symbols": ["bitcoin", "ethereum"],  // Optional, top 50 if null
  "vs_currency": "usd"
}

Response (200):
{
  "status": "success",
  "crypto_count": 2,
  "prices": {
    "bitcoin": {
      "usd": 42500.00,
      "market_cap_usd": 835000000000,
      "usd_24h_vol": 25000000000,
      "usd_24h_change": 5.2
    },
    "ethereum": {
      "usd": 2250.00,
      "market_cap_usd": 270000000000,
      "usd_24h_vol": 15000000000,
      "usd_24h_change": 3.8
    }
  }
}
```

#### Get Crypto Price History
```
GET /api/crypto/prices/BTC?hours=24

Response (200):
{
  "symbol": "BTC",
  "current_price": 42500.00,
  "market_cap": 835000000000,
  "volume_24h": 25000000000,
  "change_24h": 5.2,
  "price_history": [
    {
      "symbol": "BTC",
      "price": 42500.00,
      "market_cap": 835000000000,
      "volume_24h": 25000000000,
      "change_24h": 5.2,
      "recorded_at": "2025-11-19T10:30:00Z"
    }
  ]
}
```

#### Get Top Cryptocurrencies
```
GET /api/crypto/top?limit=20

Response (200):
{
  "top_count": 20,
  "cryptos": [
    {
      "symbol": "BTC",
      "price": 42500.00,
      "market_cap": 835000000000,
      "volume_24h": 25000000000,
      "change_24h": 5.2
    }
  ]
}
```

### Stocks

#### Fetch Stock Data
```
POST /api/stocks/fetch?ticker=AAPL

Response (200):
{
  "status": "success",
  "stock": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "open": 180.50,
    "high": 182.25,
    "low": 179.75,
    "close": 181.50,
    "volume": 52000000,
    "trading_date": "2025-11-19"
  }
}
```

#### Get Stock Price History
```
GET /api/stocks/AAPL?days=30

Response (200):
{
  "ticker": "AAPL",
  "price_history": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "open": 180.50,
      "high": 182.25,
      "low": 179.75,
      "close": 181.50,
      "volume": 52000000,
      "trading_date": "2025-11-19"
    }
  ]
}
```

### Health Check
```
GET /health

Response (200):
{
  "status": "healthy",
  "database": "healthy",
  "newsapi": "configured",
  "coingecko": "available",
  "yfinance": "available"
}
```

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |
| 502 | Gateway Error |
| 504 | Timeout |

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limits

| Service | Default | Note |
|---------|---------|------|
| Scraper Opt | 20 concurrent | Configurable per retailer |
| NewsAPI | 100/day | Requires API key |
| CoinGecko | Unlimited | Free tier |
| yfinance | Unlimited | Free |

---

Created: 2025-11-19
Version: 1.0
Last Updated: Phase 2-4 Complete
