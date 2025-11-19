# Comprehensive TODO List - Full System Architecture Build

## PHASE 1: MICROSERVICES FOUNDATION (CORE SERVICES)

### 1.1 Rebuild Microservices with Complete Dependencies
- [ ] Rebuild `ai-models` service (one at a time, NO parallel builds)
  - [ ] Verify python-multipart installed
  - [ ] Verify YOLO, CLIP, sentence-transformers loaded
  - [ ] Test endpoints: /api/models/yolo-detect, /api/models/clip-encode
- [ ] Rebuild `hf-connector` service
  - [ ] Verify transformers, accelerate, datasets installed
  - [ ] Test endpoints: /api/hf/sentiment, /api/hf/zero-shot, /api/hf/ner
- [ ] Rebuild `speech-image` service
  - [ ] Verify whisper, easyocr, librosa installed
  - [ ] Test endpoints: /api/media/voice-to-text, /api/media/ocr
- [ ] Rebuild `feature-extract` service
  - [ ] Verify sentence-transformers, sklearn installed
  - [ ] Test endpoints: /api/features/embed, /api/features/search
- [ ] Rebuild `api-gateway` service
  - [ ] Verify routing to all downstream services
  - [ ] Test orchestration & service discovery

### 1.2 Create Worker Service Implementation
- [ ] Implement Celery task queue in `services/worker/main.py`
  - [ ] Connect to Redis (broker & backend)
  - [ ] Task types: scraping jobs, ML processing, news fetching, email notifications
  - [ ] Retry logic, error handling, logging
- [ ] Create Celery beat scheduler for periodic tasks
  - [ ] Hourly product scrape jobs
  - [ ] Daily news fetch & summarization
  - [ ] 4-hourly crypto/stock price updates
  - [ ] Nightly FAISS index rebuild

### 1.3 Verify External Services
- [ ] PostgreSQL: Check existing schema (products, prices, news, users)
- [ ] Redis: Verify connectivity and TTL settings
- [ ] Scrapy service: Confirm running on port 5000
- [ ] Captcha service: Verify availability (if needed)

---

## PHASE 2: DATA PIPELINE & LINKING

### 2.1 Product Data Linking
- [ ] Create unified product schema across retailers
  - [ ] Map different retailer product IDs to single canonical ID
  - [ ] Extract common fields: name, description, price, image, URL, category
  - [ ] Create `products` table in PostgreSQL with unique constraint on (retailer, sku)
  - [ ] Add full-text search index on name + description
- [ ] Build product deduplication system
  - [ ] Use CLIP embeddings to find duplicate products across retailers
  - [ ] Merge duplicate entries, keep retailer URLs separate
  - [ ] Maintain version history in `product_versions` table
- [ ] Create product enrichment pipeline
  - [ ] Extract features via YOLO (detect objects in images)
  - [ ] Generate embeddings via CLIP (semantic search)
  - [ ] Extract text via OCR (packaging info, specs)
  - [ ] Store embeddings in FAISS index for similarity search

### 2.2 Price Tracking & History
- [ ] Create `price_history` table in TimescaleDB (hypertable)
  - [ ] Fields: product_id, retailer, price, timestamp, discount%, stock_status
  - [ ] Index on (product_id, retailer, timestamp)
- [ ] Implement price change detection
  - [ ] Track % change, absolute change, trend (↑↓→)
  - [ ] Alert on significant drops (for notifications)
- [ ] Build price aggregation API
  - [ ] Show price across all retailers for single product
  - [ ] Historical price chart data
  - [ ] Price prediction (trend analysis)

### 2.3 News & Market Data Integration
- [ ] Create `news_articles` table
  - [ ] Fields: title, content, source, url, published_at, category (tech/crypto/general)
  - [ ] Add full-text search index
  - [ ] Add sentiment_score (from HF sentiment analysis)
- [ ] Create `crypto_prices` table
  - [ ] Fields: symbol, price, market_cap, volume, change_24h, timestamp
  - [ ] Real-time data via CoinGecko API
- [ ] Create `stock_prices` table
  - [ ] Fields: ticker, price, pe_ratio, volume, timestamp
  - [ ] Real-time data via yfinance or Alpha Vantage API
- [ ] Link news to products/markets
  - [ ] NER task: extract product mentions, company names, ticker symbols from news
  - [ ] Create `news_mentions` table linking news → products/stocks/crypto

### 2.4 Data Formatting & Normalization
- [ ] Standardize product names
  - [ ] Remove brand prefixes, special characters
  - [ ] Normalize weights/quantities (e.g., "1kg", "1000g" → same unit)
  - [ ] Create `product_name_mapping` for search improvements
- [ ] Standardize product categories
  - [ ] Create canonical category tree (Electronics → Phones → Smartphones)
  - [ ] Map retailer categories to canonical hierarchy
  - [ ] Store in `product_categories` table
- [ ] Normalize prices & currencies
  - [ ] Convert all prices to base currency (USD/INR)
  - [ ] Store exchange rates in `exchange_rates` table with timestamps
- [ ] Create data validation pipeline
  - [ ] Check for outliers (99% higher than average)
  - [ ] Validate URLs, images, descriptions
  - [ ] Flag suspicious/spam data

---

## PHASE 3: SCRAPER OPTIMIZATION

### 3.1 Improve Scraper Performance
- [ ] Implement concurrent scraping (asyncio)
  - [ ] Parallel requests to different retailer endpoints
  - [ ] Batch processing of product URLs
  - [ ] Connection pooling (HTTP keep-alive)
- [ ] Add caching layer in Redis
  - [ ] Cache product pages (TTL: 24 hours)
  - [ ] Cache category listings (TTL: 48 hours)
  - [ ] Detect & skip unchanged products (MD5 hash comparison)
- [ ] Implement smart retry logic
  - [ ] Exponential backoff on rate limits
  - [ ] Different strategies per retailer (some need delays, some allow burst)
  - [ ] Circuit breaker pattern (skip retailer if repeatedly failing)
- [ ] Add request distribution
  - [ ] Rotate user agents, proxies, request headers
  - [ ] Randomize request timing (2-5s delays between requests)
  - [ ] Geographic IP rotation if available

### 3.2 Expand Retailer Coverage
- [ ] Current retailers: Amazon, Flipkart, etc.
- [ ] Add new retailers:
  - [ ] Alibaba / AliExpress
  - [ ] eBay
  - [ ] Etsy
  - [ ] Local retailers (country-specific)
  - [ ] Direct brand websites
- [ ] Create retailer adapter pattern
  - [ ] Abstract class: `BaseRetailerScraper`
  - [ ] Implement per-retailer: `AmazonScraper`, `FlipkartScraper`, etc.
  - [ ] Shared utilities: pagination, filtering, error handling
- [ ] Handle retailer-specific challenges
  - [ ] JavaScript rendering (use Selenium/Playwright for SPAs)
  - [ ] CAPTCHA bypass (use captcha service already available)
  - [ ] Rate limiting (respect robots.txt, use delays)
  - [ ] Session management (login flows, cookies, auth tokens)

### 3.3 Increase Data Breadth & Depth
- [ ] Add product attributes scraping
  - [ ] Specifications (CPU, RAM, storage, etc.)
  - [ ] Colors, sizes, variants available
  - [ ] Warranty, return policy
  - [ ] Shipping info (cost, delivery time)
  - [ ] Store in `product_attributes` & `product_variants` tables
- [ ] Add seller/store information
  - [ ] Seller name, rating, review count
  - [ ] Product availability by location
  - [ ] Store: `seller_info` & `product_availability` tables
- [ ] Add review & rating data
  - [ ] Customer ratings, review counts
  - [ ] Extract sentiment from reviews (via HF sentiment)
  - [ ] Store: `product_reviews` & `review_sentiments` tables

### 3.4 Implement Intelligent Scheduling
- [ ] Create `scrape_schedules` table
  - [ ] Per-retailer, per-category scheduling rules
  - [ ] High-demand categories: hourly updates
  - [ ] Low-demand categories: daily updates
  - [ ] New categories: more frequent initially
- [ ] Implement delta scraping
  - [ ] Only scrape products that changed (via hash/ETag)
  - [ ] Full scrape weekly (verify completeness)
  - [ ] Quick scrape daily (verify prices/stock)
- [ ] Add priority queue for scraping
  - [ ] Priority 1: Trending products (high search volume)
  - [ ] Priority 2: Recently updated products
  - [ ] Priority 3: Inventory gaps
  - [ ] Queue: Redis sorted set (score = priority)

---

## PHASE 4: MULTI-SOURCE INTEGRATION

### 4.1 News Fetching Service
- [ ] Implement news scraper
  - [ ] Sources: NewsAPI, RSS feeds, Reddit, Twitter/X, Medium
  - [ ] Keywords: product names, brands, tech news, market news
  - [ ] Store: `news_sources` & `news_articles` tables
- [ ] Create news processing pipeline
  - [ ] Duplicate detection (via URL + title hash)
  - [ ] Sentiment analysis (HF sentiment endpoint)
  - [ ] NER extraction (HF NER endpoint) → extract products/companies
  - [ ] Summarization (HF summarization endpoint) for long articles
  - [ ] Topic classification (HF zero-shot endpoint)
- [ ] Link news to products/markets
  - [ ] Create `news_product_mentions` linking articles to products
  - [ ] Create `news_market_mentions` linking articles to stocks/crypto
- [ ] Celery task: Schedule daily news fetch
  - [ ] Task name: `fetch_and_process_news`
  - [ ] Run: Daily at 00:00, 06:00, 12:00, 18:00 UTC

### 4.2 Crypto Price Service
- [ ] Implement crypto data fetcher
  - [ ] Source: CoinGecko API (free, no auth needed)
  - [ ] Currencies: Bitcoin, Ethereum, major altcoins
  - [ ] Data: price, market cap, volume, 24h change, % change
  - [ ] Store: `crypto_prices` table
- [ ] Create `crypto_price_history` table (TimescaleDB hypertable)
  - [ ] Store every 15-min snapshot
  - [ ] Index on (symbol, timestamp)
- [ ] Add crypto price alerts
  - [ ] User can set alerts: "notify if Bitcoin > $50k"
  - [ ] Store: `crypto_alerts` & `crypto_alert_notifications` tables
- [ ] Celery task: Fetch crypto prices
  - [ ] Task name: `update_crypto_prices`
  - [ ] Run: Every 15 minutes
  - [ ] Fallback: If CoinGecko fails, use backup source (Alpha Vantage)

### 4.3 Stock Price Service
- [ ] Implement stock data fetcher
  - [ ] Source: yfinance (free) or Alpha Vantage (free tier available)
  - [ ] Tickers: FAANG, indices (S&P 500, Nifty 50)
  - [ ] Data: price, PE ratio, dividend yield, 52-week high/low
  - [ ] Store: `stock_prices` table
- [ ] Create `stock_price_history` table (TimescaleDB hypertable)
  - [ ] Store daily close prices
  - [ ] Index on (ticker, timestamp)
- [ ] Add stock price alerts
  - [ ] User alerts: "notify if AAPL > $150"
  - [ ] Store: `stock_alerts` & `stock_alert_notifications` tables
- [ ] Celery task: Fetch stock prices
  - [ ] Task name: `update_stock_prices`
  - [ ] Run: Daily at market close (4pm EST / 1:30am IST)
  - [ ] Weekend skip (no market data)

### 4.4 Create Unified Market Dashboard Service
- [ ] Implement `/api/dashboard` endpoint in api-gateway
  - [ ] Returns: trending products, price changes, market data, news
  - [ ] Cached in Redis (TTL: 5 min)
- [ ] Add market correlations
  - [ ] Calculate: product price trend vs crypto/stock prices
  - [ ] Example: "Tech products -5% correlated with NASDAQ -3%"
  - [ ] Store: `market_correlations` table

---

## PHASE 5: BACKGROUND JOB SYSTEM

### 5.1 Celery Task Queue Setup
- [ ] Configure Celery broker (Redis)
- [ ] Configure Celery result backend (Redis)
- [ ] Create `celery_config.py` with:
  - [ ] Task routing (send scraping tasks to scraper workers)
  - [ ] Task retry logic (max retries, exponential backoff)
  - [ ] Task timeouts (30 min for scraping, 5 min for API calls)
  - [ ] Error callbacks (log failures, alert on critical errors)

### 5.2 Implement Core Celery Tasks
- [ ] `scrape_retailer_products`
  - [ ] Args: retailer_id, category_id (optional)
  - [ ] Flow: fetch URLs → parse products → store in DB → update embeddings
  - [ ] Retry: 3 times with exponential backoff
  - [ ] Timeout: 30 minutes
  - [ ] On failure: alert, log error, flag retailer as temporarily down

- [ ] `process_product_embeddings`
  - [ ] Args: product_id
  - [ ] Flow: fetch product → generate CLIP embedding → update FAISS index
  - [ ] Async for bulk processing (queue many product_ids)
  - [ ] Batch process: 100 products at once for efficiency

- [ ] `fetch_and_process_news`
  - [ ] Args: none (runs on schedule)
  - [ ] Flow: fetch news → dedupe → sentiment → NER → link to products
  - [ ] Store results in DB

- [ ] `update_crypto_prices`
  - [ ] Args: none (runs on schedule)
  - [ ] Flow: fetch from API → store in DB → check alerts → notify users

- [ ] `update_stock_prices`
  - [ ] Args: none (runs on schedule)
  - [ ] Flow: fetch from API → store in DB → check alerts → notify users

- [ ] `send_notifications`
  - [ ] Args: user_id, notification_type, data
  - [ ] Integrations: Email (SendGrid), SMS (Twilio), Push (FCM)
  - [ ] Retry failed notifications (3x)

- [ ] `rebuild_faiss_index`
  - [ ] Args: none (runs nightly)
  - [ ] Flow: fetch all product embeddings → rebuild FAISS index → save to disk
  - [ ] Atomic swap (old index → new index)

### 5.3 Celery Beat Scheduler Setup
- [ ] Create `celery_beat_schedule.py` with:
  - [ ] Scraping tasks (hourly per retailer)
  - [ ] News fetch (4x daily)
  - [ ] Crypto prices (every 15 min)
  - [ ] Stock prices (daily at market close)
  - [ ] FAISS rebuild (nightly 00:00)
  - [ ] Database cleanup (weekly, remove old data)
  - [ ] Cache warming (cache popular searches)

### 5.4 Task Monitoring & Logging
- [ ] Create Celery Flower dashboard
  - [ ] Docker container: celery/flower
  - [ ] Port: 5555 (expose in docker-compose)
  - [ ] Shows: active tasks, task history, worker health
- [ ] Implement comprehensive logging
  - [ ] Task start/complete logs with duration
  - [ ] Error logs with full traceback
  - [ ] Performance metrics: items processed, time taken, rate
  - [ ] Store logs in `task_logs` table for analytics
- [ ] Add alerting
  - [ ] Alert if task queue depth > 1000
  - [ ] Alert if worker offline
  - [ ] Alert if task failure rate > 10%

---

## PHASE 6: DATABASE & CACHING OPTIMIZATION

### 6.1 PostgreSQL Schema Completion
- [ ] Create comprehensive schema (if not already done):

```sql
-- Products
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  description TEXT,
  category_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE product_retailers (
  id SERIAL PRIMARY KEY,
  product_id INT NOT NULL,
  retailer_id INT NOT NULL,
  retailer_sku TEXT,
  retailer_url TEXT UNIQUE,
  retailer_name TEXT,
  UNIQUE(product_id, retailer_id, retailer_sku)
);

-- Prices (TimescaleDB)
CREATE TABLE price_history (
  time TIMESTAMP NOT NULL,
  product_id INT NOT NULL,
  retailer_id INT NOT NULL,
  price DECIMAL(10, 2),
  currency TEXT,
  discount_percent INT,
  stock_status TEXT
);
SELECT create_hypertable('price_history', 'time', if_not_exists => TRUE);
CREATE INDEX ON price_history (product_id, retailer_id, time DESC);

-- News
CREATE TABLE news_articles (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  source_url TEXT UNIQUE,
  source_name TEXT,
  published_at TIMESTAMP,
  sentiment_score FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings & Search
CREATE TABLE product_embeddings (
  id SERIAL PRIMARY KEY,
  product_id INT NOT NULL UNIQUE,
  embedding VECTOR(384), -- sentence-transformers dimension
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ON product_embeddings USING hnsw (embedding vector_cosine_ops);

-- Users & Notifications
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE,
  phone TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_alerts (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  alert_type TEXT, -- 'price_drop', 'crypto_threshold', 'stock_alert'
  product_id INT,
  crypto_symbol TEXT,
  stock_ticker TEXT,
  condition TEXT, -- 'price < 100' or 'change > 5%'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications sent
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  notification_type TEXT, -- 'email', 'sms', 'push'
  title TEXT,
  content TEXT,
  sent_at TIMESTAMP,
  read_at TIMESTAMP
);
```

- [ ] Create all indexes for performance
- [ ] Add foreign key constraints
- [ ] Enable TimescaleDB for price_history

### 6.2 Redis Caching Strategy
- [ ] Cache keys structure:
  ```
  product:{id}:details → product data (TTL: 24h)
  product:{id}:price → current prices across retailers (TTL: 1h)
  product:{id}:embedding → CLIP embedding (TTL: 7d)
  search:{query}:results → search results (TTL: 1h)
  dashboard:market → market overview (TTL: 5m)
  retailer:{id}:status → retailer health (TTL: 5m)
  session:{session_id} → user session (TTL: 24h)
  ```
- [ ] Implement cache warming
  - [ ] Cache top 1000 products on startup
  - [ ] Cache trending searches daily
  - [ ] Pre-cache embeddings for new products
- [ ] Implement cache invalidation
  - [ ] On price update: invalidate `product:{id}:price`
  - [ ] On new product: invalidate search cache
  - [ ] On bulk update: use cache tags for batch invalidation

### 6.3 FAISS Index Optimization
- [ ] Create FAISS index for semantic search
  - [ ] Index type: HNSW (hierarchical navigable small world)
  - [ ] Vector dimension: 384 (sentence-transformers)
  - [ ] Similarity metric: cosine distance
- [ ] Store index on disk
  - [ ] Location: `/data/faiss_index.bin`
  - [ ] Versioning: keep last 3 indexes (for rollback)
- [ ] Nightly index rebuild
  - [ ] Task: `rebuild_faiss_index`
  - [ ] Schedule: 00:00 UTC (low-traffic time)
  - [ ] Duration: ~30 min for 100k products
- [ ] Implement index warmup
  - [ ] Load index to memory on service startup
  - [ ] Pre-compute common searches

### 6.4 Object Storage for Media
- [ ] Setup local object storage (or cloud: S3, GCS)
  - [ ] Path: `/data/uploads/products/{product_id}/`
  - [ ] Files: images, extracted text (OCR), metadata
- [ ] Implement image optimization
  - [ ] Generate thumbnails (200x200, 600x600)
  - [ ] Store WebP + JPEG formats
  - [ ] Compress PDFs, spec sheets
- [ ] Create file management API
  - [ ] Upload image → generate embedding → extract OCR text
  - [ ] Serve via CDN (or direct serving with caching headers)

---

## PHASE 7: API GATEWAY ENHANCEMENT

### 7.1 Request Routing
- [ ] Implement intelligent routing in api-gateway
  ```python
  /api/products/* → product-srv
  /api/markets/* → market-srv (news/crypto/stocks)
  /api/search/* → search-srv (FAISS)
  /api/users/* → auth-srv
  /api/notifications/* → notify-srv
  ```
- [ ] Add request aggregation
  - [ ] `/api/products/{id}/full` → fetch product + prices + reviews + embeddings
  - [ ] `/api/dashboard` → fetch market + trending products + news
- [ ] Add response caching in gateway
  - [ ] Cache GET requests in Redis
  - [ ] Add Cache-Control headers (public, 5min)

### 7.2 Authentication & Authorization
- [ ] Implement JWT-based auth
  - [ ] Issue token on login
  - [ ] Verify token on each request
  - [ ] Store in Redis for quick validation
- [ ] Create user roles
  - [ ] `admin`: full access
  - [ ] `user`: can search, set alerts, view favorites
  - [ ] `scraper`: can trigger scraping jobs (internal only)
- [ ] Add rate limiting
  - [ ] Per-user: 100 req/min
  - [ ] Per-IP: 1000 req/min
  - [ ] Per-endpoint: 10k req/hour (scraper exempted)
  - [ ] Store in Redis using sliding window counter

### 7.3 Request/Response Handling
- [ ] Add request validation
  - [ ] Validate all query params, body params
  - [ ] Return 400 on invalid input with clear error messages
- [ ] Standardize response format
  ```json
  {
    "status": "success|error",
    "data": {...},
    "meta": {
      "timestamp": "2025-11-19T...",
      "version": "1.0",
      "request_id": "req_xyz"
    },
    "errors": []
  }
  ```
- [ ] Add request/response logging
  - [ ] Log all requests with duration
  - [ ] Log errors with full context
  - [ ] Alert on slow requests (> 5s)

---

## PHASE 8: NOTIFICATION SYSTEM

### 8.1 Email Notifications (SendGrid)
- [ ] Setup SendGrid integration
  - [ ] API key from environment
  - [ ] Create email templates (alerts, digest, verification)
- [ ] Implement email task
  - [ ] Celery task: `send_email`
  - [ ] Template rendering (Jinja2)
  - [ ] Error handling & retries
- [ ] Email types:
  - [ ] Price drop alerts
  - [ ] Weekly digest (trending products, deals)
  - [ ] Verification email
  - [ ] Password reset

### 8.2 SMS Notifications (Twilio)
- [ ] Setup Twilio integration
  - [ ] Account SID, auth token from environment
  - [ ] Twilio phone number configuration
- [ ] Implement SMS task
  - [ ] Celery task: `send_sms`
  - [ ] Message truncation (160 char limit)
  - [ ] Error handling & retries
- [ ] SMS types:
  - [ ] Price drop alerts (high-priority)
  - [ ] Stock alert notifications
  - [ ] Verification codes

### 8.3 Push Notifications (Firebase Cloud Messaging)
- [ ] Setup FCM integration
  - [ ] Firebase project setup
  - [ ] Server credentials from environment
- [ ] Implement push task
  - [ ] Celery task: `send_push_notification`
  - [ ] Token management (user device tokens)
  - [ ] Error handling & retries
- [ ] Push types:
  - [ ] Price drop alerts
  - [ ] New product in wishlist
  - [ ] Market news (crypto/stock alerts)

### 8.4 Notification Aggregation
- [ ] Implement digest notifications
  - [ ] Daily digest: top 5 deals, trending products
  - [ ] Weekly digest: market summary, news roundup
  - [ ] Store in `notification_digests` table
- [ ] Notification preferences
  - [ ] User can choose: email, SMS, push
  - [ ] Quiet hours: don't send 22:00-08:00
  - [ ] Store: `notification_preferences` table

---

## PHASE 9: SEARCH & DISCOVERY

### 9.1 Full-Text Search
- [ ] Implement PostgreSQL full-text search
  - [ ] Index on `product.name` + `product.description`
  - [ ] Ranking by relevance (tf-idf)
  - [ ] Query: `SELECT * FROM products WHERE search_vector @@ to_tsquery(...)`
- [ ] Create `/api/search/text` endpoint
  - [ ] Input: query string, filters (category, price range, retailer)
  - [ ] Output: top 50 products with relevance score
  - [ ] Cache results (TTL: 1h)

### 9.2 Semantic Search (CLIP)
- [ ] Implement FAISS-based semantic search
  - [ ] Input: product ID or product description
  - [ ] Convert to embedding via feature-extract service
  - [ ] Search FAISS index (k-nearest neighbors)
  - [ ] Return top 20 similar products
- [ ] Create `/api/search/semantic` endpoint
  - [ ] Input: query text or product_id
  - [ ] Output: similar products with similarity score
  - [ ] Cache results (TTL: 1h)

### 9.3 Advanced Filters & Aggregations
- [ ] Implement faceted search
  - [ ] Facets: category, brand, price range, rating, availability
  - [ ] Show facet counts alongside results
  - [ ] Allow multi-select filters
- [ ] Create product comparison
  - [ ] `/api/products/compare?ids=1,2,3`
  - [ ] Show side-by-side: specs, prices, ratings, reviews
  - [ ] Highlight differences

### 9.4 Personalized Recommendations
- [ ] Implement recommendation engine
  - [ ] Collaborative filtering: users who viewed X also viewed Y
  - [ ] Content-based: similar products to user's wishlist
  - [ ] Trending: products trending in user's category
  - [ ] Store in `recommendations` table
- [ ] Create `/api/recommendations` endpoint
  - [ ] Input: user_id
  - [ ] Output: top 10 personalized recommendations
  - [ ] Cache per-user (TTL: 6h)

---

## PHASE 10: FRONTEND INTEGRATION PREP

### 10.1 API Endpoints Documentation
- [ ] Document all microservice endpoints
  - [ ] Methods: GET, POST, PUT, DELETE
  - [ ] Request/response schemas (OpenAPI/Swagger)
  - [ ] Error codes and messages
  - [ ] Example curl requests
- [ ] Create OpenAPI spec
  - [ ] File: `openapi.yaml`
  - [ ] Tools: auto-generate from code using FastAPI docstrings
- [ ] Setup Swagger UI
  - [ ] Endpoint: `/api/docs`
  - [ ] Interactive endpoint testing
  - [ ] Auto-generated from OpenAPI spec

### 10.2 GraphQL API (Optional)
- [ ] Implement GraphQL server (optional, if needed alongside REST)
  - [ ] Library: Strawberry or Graphene
  - [ ] Unified schema across services
  - [ ] Query example:
    ```graphql
    query {
      product(id: 123) {
        name
        prices { retailer, price }
        reviews { rating, text }
        similar(limit: 5) { id, name }
      }
    }
    ```

### 10.3 WebSocket Support (Real-time)
- [ ] Add WebSocket endpoint in api-gateway
  - [ ] Endpoint: `wss://api/ws/notifications`
  - [ ] Subscribe to: price updates, news, alerts
  - [ ] Flow: user connects → receive real-time updates → disconnect
  - [ ] Implementation: Python `websockets` library
- [ ] Create WebSocket tasks
  - [ ] On price change: broadcast to subscribed users
  - [ ] On new news: broadcast to subscribed users
  - [ ] On alert trigger: send to specific user

### 10.4 CORS & Security
- [ ] Configure CORS properly
  - [ ] Allowed origins: frontend domain
  - [ ] Methods: GET, POST, PUT, DELETE
  - [ ] Headers: Authorization, Content-Type
  - [ ] Credentials: allow with sameSite=Strict
- [ ] Add security headers
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff
  - [ ] Strict-Transport-Security: max-age=31536000
  - [ ] Content-Security-Policy: strict
- [ ] Implement CSRF protection
  - [ ] Token-based (POST requests need CSRF token)
  - [ ] Store in Redis or signed cookie

---

## PHASE 11: TESTING & VALIDATION

### 11.1 Unit Tests
- [ ] Write unit tests for each microservice
  - [ ] Test business logic (no external calls)
  - [ ] Mock databases, APIs
  - [ ] Aim: 80%+ code coverage
  - [ ] Framework: pytest
- [ ] Test data models
  - [ ] Valid inputs, boundary cases, edge cases
  - [ ] Invalid inputs (should raise errors)

### 11.2 Integration Tests
- [ ] Write integration tests
  - [ ] Test service-to-service communication
  - [ ] Test full request flow (gateway → service → DB)
  - [ ] Use test database, Redis instance
  - [ ] Cleanup after each test
- [ ] Test database operations
  - [ ] CRUD operations
  - [ ] Complex queries
  - [ ] Transactions, rollbacks

### 11.3 End-to-End Tests
- [ ] Write E2E tests
  - [ ] Full user flows (search → view → alert)
  - [ ] All microservices together
  - [ ] Use test environment (docker-compose.test.yml)
  - [ ] Cleanup after tests
- [ ] Load testing
  - [ ] Tool: Apache JMeter or Locust
  - [ ] Test: 100 concurrent users, 1000 req/min
  - [ ] Measure: latency, throughput, error rate
  - [ ] Target: < 500ms p95 latency

### 11.4 Data Validation Tests
- [ ] Verify data quality
  - [ ] Products: no duplicates, valid URLs, images exist
  - [ ] Prices: no outliers, valid currencies
  - [ ] News: no duplicates, valid timestamps
- [ ] Create data quality reports
  - [ ] Generate daily: completeness, accuracy, validity metrics
  - [ ] Alert on threshold breaches

---

## PHASE 12: DEPLOYMENT & DOCKER BUILD

### 12.1 Docker Image Optimization
- [ ] Review all Dockerfiles
  - [ ] Use multi-stage builds (reduce image size)
  - [ ] Remove unnecessary dependencies
  - [ ] Consolidate RUN commands (reduce layers)
  - [ ] Sort packages for caching efficiency
- [ ] Optimize image layers
  - [ ] Copy only necessary files (use .dockerignore)
  - [ ] Install dependencies early (cache busting)
  - [ ] Move frequently-changing files to last layers
- [ ] Test image sizes
  - [ ] Target: api-gateway < 500MB, ml services < 5GB each
  - [ ] Verify all packages installed (no errors on `docker run`)

### 12.2 Docker Compose Optimization
- [ ] Review docker-compose.services.yml
  - [ ] Health checks: all services have them
  - [ ] Dependencies: correct startup order
  - [ ] Networks: all services on same network
  - [ ] Volumes: proper mounts for persistence
  - [ ] Environment variables: all sensitive data in .env
- [ ] Add profiles
  - [ ] `microservices`: all services
  - [ ] `dev`: only essential services (gateway, DB, redis)
  - [ ] `test`: test environment

### 12.3 Environment Configuration
- [ ] Create `.env.example` with all variables
  - [ ] Database: connection string, credentials
  - [ ] Redis: host, port, password
  - [ ] APIs: SendGrid, Twilio, CoinGecko keys
  - [ ] Services: ports, hosts, URLs
  - [ ] Security: JWT secret, CORS origins
- [ ] Create `.env.local` (for local development)
- [ ] Create `.env.production` (for production deployment)
- [ ] Validate all required env vars on startup

### 12.4 Dependency Pinning
- [ ] Pin all dependencies (NO `latest` or `*`)
  - [ ] Python: `requirements.txt` with versions
  - [ ] System: Alpine packages with versions
  - [ ] Node (if any): `package-lock.json`
- [ ] Create requirements files per service
  - [ ] `services/api-gateway/requirements.txt`
  - [ ] `services/ai-models/requirements.txt`
  - [ ] etc.
- [ ] Test all pins work together
  - [ ] Build fresh images from scratch
  - [ ] Verify no conflicts, deprecated packages

---

## PHASE 13: ADDITIONAL PACKAGES & DEPENDENCIES

### 13.1 Python Packages (ensure all included)
- [ ] Core: FastAPI, uvicorn, pydantic, python-multipart
- [ ] Database: psycopg2-binary, sqlalchemy, alembic
- [ ] Cache: redis
- [ ] Task queue: celery, celery[redis]
- [ ] ML/AI:
  - [ ] torch, transformers, sentence-transformers
  - [ ] tensorflow, ultralytics (YOLO)
  - [ ] easyocr, opencv-python
  - [ ] scikit-learn, numpy, scipy
- [ ] NLP: openai-whisper
- [ ] Web scraping: requests, httpx, beautifulsoup4, selenium, playwright
- [ ] API clients: coingecko, yfinance, alpha-vantage
- [ ] Notifications: sendgrid, twilio, firebase-admin
- [ ] Utilities: pydantic-settings, python-dateutil, pytz, click
- [ ] Monitoring: prometheus-client
- [ ] Testing: pytest, pytest-asyncio, pytest-cov
- [ ] Logging: python-json-logger
- [ ] Documentation: mkdocs

### 13.2 System Packages (APT for Linux/Docker)
- [ ] Build tools: build-essential, git, curl
- [ ] Python dev: python3-dev
- [ ] Database: postgresql-client
- [ ] Media: ffmpeg, libsm6, libxext6, libxrender-dev
- [ ] Image: libopenjp2-7, libtiff5, libwebp6, libharfbuzz0b
- [ ] Development: pkg-config, cmake
- [ ] Network: ca-certificates
- [ ] Compression: bzip2, xz-utils

### 13.3 Optional Packages (install as needed)
- [ ] GPU support: cuda-toolkit (if GPU available)
- [ ] Distributed tracing: jaeger-client
- [ ] Metrics: statsd
- [ ] Profiling: py-spy, flamegraph
- [ ] API gateway: nginx, haproxy (if using instead of FastAPI)

### 13.4 Dependency Security
- [ ] Scan for vulnerabilities
  - [ ] Tool: `safety check`, `pip-audit`, OWASP Dependency-Check
  - [ ] Run in CI/CD before deployment
  - [ ] Alert on high/critical vulnerabilities
- [ ] Create security policy
  - [ ] Update dependencies monthly
  - [ ] Patch security issues within 24h
  - [ ] Keep lock files in version control

---

## PHASE 14: MONITORING & OBSERVABILITY

### 14.1 Metrics & Monitoring
- [ ] Add Prometheus metrics
  - [ ] Endpoint: `/metrics` per service
  - [ ] Metrics: requests/sec, latency, errors, DB query time
  - [ ] Tool: prometheus-client library
- [ ] Setup Prometheus server
  - [ ] Docker container
  - [ ] Config: scrape all microservices
  - [ ] Retention: 15 days
- [ ] Setup Grafana dashboards
  - [ ] Container: grafana
  - [ ] Dashboards: service health, request latency, error rates
  - [ ] Alerts: on latency > 1s, error rate > 5%

### 14.2 Logging
- [ ] Centralized logging
  - [ ] All services log to stdout (Docker collects)
  - [ ] Format: JSON for easy parsing
  - [ ] ELK stack optional (Elasticsearch, Logstash, Kibana)
- [ ] Log levels
  - [ ] DEBUG: detailed info for development
  - [ ] INFO: important events (startup, task completion)
  - [ ] WARNING: potential issues (retry, timeout)
  - [ ] ERROR: failures (need attention)

### 14.3 Distributed Tracing
- [ ] Add request tracing
  - [ ] Each request gets unique ID
  - [ ] Passed through all services
  - [ ] Tool: Jaeger or Zipkin (optional)
  - [ ] Helps debug multi-service issues

### 14.4 Health Checks
- [ ] Implement health endpoints
  - [ ] `/health` → quick check (always ok)
  - [ ] `/health/deep` → check DB, cache, dependencies
  - [ ] Used by load balancers, orchestrators
- [ ] Health check in docker-compose
  - [ ] Interval: 10s
  - [ ] Timeout: 5s
  - [ ] Retries: 3
  - [ ] Status: healthy, unhealthy, starting

---

## PHASE 15: PRODUCTION READINESS

### 15.1 Pre-deployment Checklist
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code reviewed by team
- [ ] No security warnings (SAST, dependency scanning)
- [ ] Documentation complete (API docs, architecture)
- [ ] Load testing done (meets SLA)
- [ ] Disaster recovery plan documented
- [ ] Rollback procedure documented
- [ ] On-call runbook prepared

### 15.2 Deployment Strategy
- [ ] Blue-green deployment
  - [ ] Deploy to "green" environment
  - [ ] Route traffic when healthy
  - [ ] Keep "blue" for quick rollback
- [ ] Canary deployment (optional)
  - [ ] Route 5% traffic to new version
  - [ ] Monitor metrics
  - [ ] Gradually increase to 100%
- [ ] Automated rollback
  - [ ] If health checks fail → rollback
  - [ ] If error rate spikes → rollback

### 15.3 Database Migration
- [ ] Use Alembic for schema migrations
  - [ ] File: `alembic/versions/001_initial_schema.py`
  - [ ] Run: `alembic upgrade head`
  - [ ] Rollback: `alembic downgrade -1`
- [ ] Backup before migration
  - [ ] `pg_dump database > backup.sql`
  - [ ] Store in S3/cloud storage
  - [ ] Verify restore works
- [ ] Test migrations
  - [ ] Test on staging first
  - [ ] Verify data integrity after
  - [ ] Monitor query performance

### 15.4 Capacity Planning
- [ ] Estimate resource usage
  - [ ] CPU: profile services
  - [ ] Memory: set limits in docker-compose
  - [ ] Disk: estimate data growth
  - [ ] Network: estimate bandwidth
- [ ] Auto-scaling rules
  - [ ] Scale-up if: CPU > 70%, Memory > 80%
  - [ ] Scale-down if: CPU < 30%, Memory < 50%
  - [ ] Min replicas: 2, Max replicas: 10

---

## PHASE 16: FRONTEND-BACKEND INTEGRATION

### 16.1 Frontend Setup
- [ ] React/Vue/Next.js project structure
  - [ ] Components: Search, ProductCard, Dashboard, Alerts
  - [ ] Pages: Home, Product Detail, Comparison, Dashboard
  - [ ] State management: Redux/Pinia/Zustand
- [ ] Environment configuration
  - [ ] `.env.local` with API base URL
  - [ ] `.env.production` with production API URL

### 16.2 Backend API Integration
- [ ] Create API client utilities
  - [ ] Axios or Fetch with interceptors
  - [ ] Handle auth tokens (JWT)
  - [ ] Handle errors consistently
  - [ ] Add retry logic
- [ ] Implement authentication flow
  - [ ] Login page → get JWT token
  - [ ] Store token in localStorage/cookies
  - [ ] Add token to all API requests
  - [ ] Handle token expiry → refresh or re-login

### 16.3 Frontend Pages Integration
- [ ] Search page
  - [ ] Call `/api/search/text` with query + filters
  - [ ] Display results with pagination
  - [ ] Cache results client-side
- [ ] Product detail page
  - [ ] Call `/api/products/{id}/full`
  - [ ] Display: specs, prices, reviews, similar products
  - [ ] Add to wishlist, set price alert
- [ ] Dashboard page
  - [ ] Call `/api/dashboard`
  - [ ] Display: trending products, deals, market data
  - [ ] Real-time updates via WebSocket
- [ ] Alerts page
  - [ ] Show user's active alerts
  - [ ] Allow add/edit/delete alerts
  - [ ] Show notification history

### 16.4 Frontend Features
- [ ] Search with autocomplete
  - [ ] Call `/api/search/suggestions?q=...` (debounced)
  - [ ] Show popular searches
  - [ ] Show recent searches (client-side)
- [ ] Product comparison
  - [ ] Select 2-3 products
  - [ ] Call `/api/products/compare`
  - [ ] Show side-by-side specs and prices
- [ ] Wishlist & price tracking
  - [ ] Add to wishlist API call
  - [ ] Show wishlist with price history chart
  - [ ] Notify when price drops

---

## PHASE 17: FINAL VALIDATION & TESTING

### 17.1 End-to-End User Flow Testing
- [ ] User flow 1: Search & Price Compare
  - [ ] Search for "iPhone 15"
  - [ ] View results with prices from different retailers
  - [ ] Compare 2 products
  - [ ] Set price alert
  - [ ] Verify alert received (email/SMS/push)

- [ ] User flow 2: Dashboard & News
  - [ ] View dashboard (trending, market data, news)
  - [ ] Click on news article
  - [ ] See related products mentioned in article
  - [ ] Verify sentiment score correct

- [ ] User flow 3: Alerts & Notifications
  - [ ] Set crypto alert: "Bitcoin > $50k"
  - [ ] Wait for notification
  - [ ] Verify notification in app + email + SMS

### 17.2 Data Quality Validation
- [ ] Product data quality
  - [ ] Check: no null names, valid URLs, images exist
  - [ ] Check: no duplicates (same SKU)
  - [ ] Check: prices reasonable (not 0 or 999999)
  - [ ] Sample 100 random products → manual review
- [ ] Price data quality
  - [ ] Check: price history consistent (no wild jumps)
  - [ ] Check: currency correct per retailer
  - [ ] Check: all prices updated within 24h
- [ ] News data quality
  - [ ] Check: no duplicate articles
  - [ ] Check: sentiment scores in [-1, 1] range
  - [ ] Check: NER entities found correctly
- [ ] Create data quality report
  - [ ] Run nightly
  - [ ] Alert if quality drops below threshold

### 17.3 Performance Validation
- [ ] API response times
  - [ ] Search: < 500ms
  - [ ] Product detail: < 300ms
  - [ ] Dashboard: < 1000ms
  - [ ] Measure via Grafana/APM
- [ ] Database query performance
  - [ ] Full-text search: < 100ms
  - [ ] FAISS similarity search: < 50ms
  - [ ] Complex joins: < 200ms
  - [ ] Add indexes if needed
- [ ] Scraper performance
  - [ ] Products/min per retailer
  - [ ] Errors per 1000 products
  - [ ] Network bandwidth used
  - [ ] Compare to baseline, alert on degradation

### 17.4 Security & Compliance
- [ ] Security testing
  - [ ] SQL injection tests (should fail safely)
  - [ ] XSS tests (should be blocked)
  - [ ] CSRF tests (should require tokens)
  - [ ] JWT tampering (should fail)
- [ ] Data privacy
  - [ ] User data encrypted in transit (HTTPS)
  - [ ] Passwords hashed (bcrypt)
  - [ ] Sensitive data not logged
  - [ ] GDPR compliance (data deletion, export)
- [ ] Dependency scanning
  - [ ] Run `safety check`, `pip-audit`
  - [ ] Fix high/critical vulnerabilities
  - [ ] Document known issues

---

## PHASE 18: DEPLOYMENT & LAUNCH

### 18.1 Fresh Docker Build
- [ ] Clean build from scratch
  ```bash
  # Remove all images
  docker rmi $(docker images -q test_model-*)

  # Build fresh images one-by-one
  docker-compose -f docker-compose.services.yml build api-gateway
  docker-compose -f docker-compose.services.yml build scrapy-wrapper
  docker-compose -f docker-compose.services.yml build feature-extract
  docker-compose -f docker-compose.services.yml build worker
  docker-compose -f docker-compose.services.yml build ai-models
  docker-compose -f docker-compose.services.yml build hf-connector
  docker-compose -f docker-compose.services.yml build speech-image
  ```

- [ ] Verify all images built successfully
  - [ ] Check image sizes
  - [ ] Verify no build errors
  - [ ] Test container startup

### 18.2 Staging Environment
- [ ] Deploy to staging
  ```bash
  docker-compose -f docker-compose.services.yml --profile microservices up -d
  ```
- [ ] Run smoke tests
  - [ ] Health checks pass
  - [ ] All endpoints respond
  - [ ] Search works
  - [ ] Alerts work
  - [ ] Notifications sent
- [ ] Load test (100 concurrent users)
  - [ ] Measure latency, throughput
  - [ ] Verify no crashes
  - [ ] Monitor resource usage

### 18.3 Production Deployment
- [ ] Tag docker images for registry
  ```bash
  docker tag test_model-api-gateway:latest registry.example.com/test_model-api-gateway:v1.0
  docker push registry.example.com/test_model-api-gateway:v1.0
  ```
- [ ] Deploy with k8s or docker swarm (optional)
  - [ ] Create deployment manifests
  - [ ] Health checks, resource limits
  - [ ] Rolling update strategy
- [ ] Monitor production
  - [ ] Watch error rates (should be < 0.1%)
  - [ ] Watch latency (p95 < 500ms)
  - [ ] Watch resource usage
  - [ ] Alert on any anomalies

### 18.4 Post-Launch Monitoring
- [ ] First 24 hours: high-touch monitoring
  - [ ] Assign on-call engineer
  - [ ] Check metrics every 1 hour
  - [ ] Be ready to rollback
- [ ] First week: daily review
  - [ ] Error rates, latencies
  - [ ] Data quality issues
  - [ ] Scraper health
  - [ ] Notification delivery
- [ ] Weekly thereafter
  - [ ] Performance review
  - [ ] Dependency updates
  - [ ] Data cleanup, index optimization

---

## FINAL CHECKLIST

### Critical Path (Must-Have)
- [ ] All 8 microservices built & running
- [ ] postgres + redis healthy
- [ ] API gateway routing to all services
- [ ] Celery tasks working
- [ ] Scraper pulling products
- [ ] Notifications sending
- [ ] Frontend-backend integration complete
- [ ] E2E user flows working
- [ ] All tests passing

### High-Priority (Should-Have)
- [ ] News, crypto, stock data fetching
- [ ] FAISS search working
- [ ] Price tracking & alerts
- [ ] User authentication
- [ ] Monitoring & alerting setup
- [ ] Documentation complete

### Nice-to-Have (Can-Do)
- [ ] GraphQL API
- [ ] WebSocket real-time updates
- [ ] Recommendation engine
- [ ] Advanced filters & faceted search
- [ ] Mobile app

### Success Criteria
- ✅ All services deployed
- ✅ 10k products indexed
- ✅ API response time < 500ms p95
- ✅ Scraper: 1000+ products/day per retailer
- ✅ 0 alerts about failures/errors
- ✅ Users can search, compare, set alerts
- ✅ News/market data fresh (< 1h old)
- ✅ Notifications delivered within 5 minutes

---

**Next Steps:**
1. Start with PHASE 1: Rebuild microservices (one-by-one)
2. Then verify all services healthy
3. Move to PHASE 2: Data linking & normalization
4. Continue through phases sequentially
5. Final testing & production deployment

This is a comprehensive roadmap for a production-grade system! 🚀
