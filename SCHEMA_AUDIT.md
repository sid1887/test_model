# Database Schema vs ORM Models Audit

## DATABASE TABLES (from db/init/02_schema.sql)

### 1. **products**
- id: UUID PRIMARY KEY
- title: TEXT NOT NULL
- canonical_sku: TEXT
- category: TEXT
- brand: TEXT
- main_image: TEXT
- description: TEXT
- metadata: JSONB (default '{}')
- avg_price: NUMERIC(12,2)
- min_price: NUMERIC(12,2)
- max_price: NUMERIC(12,2)
- views_count: INTEGER (default 0)
- searches_count: INTEGER (default 0)
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ
- last_scraped_at: TIMESTAMPTZ

### 2. **raw_scrapes**
- id: UUID PRIMARY KEY
- product_identifier: TEXT
- site_name: TEXT NOT NULL
- url: TEXT NOT NULL
- raw_data: JSONB NOT NULL
- headers: JSONB
- processed: BOOLEAN (default FALSE)
- processing_error: TEXT
- scraped_at: TIMESTAMPTZ
- processed_at: TIMESTAMPTZ

### 3. **product_prices**
- id: BIGSERIAL PRIMARY KEY
- product_id: UUID FK → products(id)
- site_name: TEXT NOT NULL
- site_product_id: TEXT
- site_url: TEXT
- price: NUMERIC(12,2) NOT NULL
- original_price: NUMERIC(12,2)
- discount_percent: NUMERIC(5,2)
- currency: TEXT (default 'INR')
- availability: TEXT
- in_stock: BOOLEAN (default TRUE)
- scraped_data: JSONB
- scraped_at: TIMESTAMPTZ
- created_at: TIMESTAMPTZ

### 4. **embeddings**
- id: UUID PRIMARY KEY
- product_id: UUID FK → products(id)
- model_name: TEXT NOT NULL
- model_version: TEXT
- vec: VECTOR(512)
- meta: JSONB
- created_at: TIMESTAMPTZ

### 5. **price_alerts**
- id: BIGSERIAL PRIMARY KEY
- user_id: UUID NOT NULL
- product_id: UUID FK → products(id)
- condition_type: TEXT NOT NULL
- threshold: NUMERIC(12,2)
- threshold_percent: NUMERIC(5,2)
- active: BOOLEAN (default TRUE)
- notification_channels: JSONB
- times_triggered: INTEGER (default 0)
- last_triggered_at: TIMESTAMPTZ
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ

### 6. **alert_history**
- id: BIGSERIAL PRIMARY KEY
- alert_id: BIGINT FK → price_alerts(id)
- product_price_id: BIGINT FK → product_prices(id)
- triggered_price: NUMERIC(12,2)
- previous_price: NUMERIC(12,2)
- payload: JSONB
- notification_sent: BOOLEAN (default FALSE)
- notification_error: TEXT
- triggered_at: TIMESTAMPTZ

### 7. **retailers**
- id: SERIAL PRIMARY KEY
- name: TEXT NOT NULL UNIQUE
- domain: TEXT NOT NULL
- scraper_config: JSONB
- active: BOOLEAN (default TRUE)
- last_scrape_at: TIMESTAMPTZ
- success_rate: NUMERIC(5,2)
- avg_response_time: NUMERIC(8,2)
- created_at: TIMESTAMPTZ

### 8. **smart_lists**
- id: BIGSERIAL PRIMARY KEY
- user_id: UUID NOT NULL
- name: TEXT NOT NULL
- description: TEXT
- auto_update: BOOLEAN (default TRUE)
- settings: JSONB
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ

### 9. **smart_list_items**
- id: BIGSERIAL PRIMARY KEY
- list_id: BIGINT FK → smart_lists(id)
- product_id: UUID FK → products(id)
- quantity: INTEGER (default 1)
- priority: INTEGER (default 0)
- notes: TEXT
- added_at: TIMESTAMPTZ

### 10. **analytics_insights**
- id: UUID PRIMARY KEY
- product_id: UUID FK → products(id)
- insight_type: TEXT NOT NULL
- data: JSONB NOT NULL
- model_name: TEXT
- confidence: NUMERIC(5,4)
- valid_from: TIMESTAMPTZ
- valid_until: TIMESTAMPTZ
- created_at: TIMESTAMPTZ

---

## ORM MODELS AUDIT

### ❌ **product.py** - COMPLETELY WRONG
Current has: name, image_path, specifications, detection_confidence, is_processed
Should have: title, main_image, metadata, avg_price, canonical_sku, etc.

### ❌ **analysis.py** - TABLE DOESN'T EXIST
Model exists but no corresponding table in schema

### ❌ **analytics.py** - WRONG TABLE MAPPING
Has PriceForecast, SentimentAnalysis but should map to analytics_insights

### ❌ **price_comparison.py** - WRONG TABLE
Should map to product_prices table

### ❌ **alert.py** - Needs validation
Check if maps to price_alerts correctly

### ❌ **smart_list.py** - Needs validation
Check if maps to smart_lists/smart_list_items

---

## ACTION PLAN

1. Delete or archive broken models (analysis.py)
2. Completely rewrite product.py to match products table
3. Create new models for missing tables (raw_scrapes, embeddings, retailers, analytics_insights)
4. Fix alert.py to match price_alerts schema
5. Fix smart_list.py to match smart_lists schema
6. Replace analytics.py with proper analytics_insights model
7. Replace price_comparison.py with product_prices model
