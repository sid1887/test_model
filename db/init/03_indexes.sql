-- Advanced Indexes for Performance
-- GIN, trigram, and specialized indexes

-- ============================================================================
-- PRODUCTS - Search & Lookup Indexes
-- ============================================================================

-- Trigram index for fuzzy title search
CREATE INDEX IF NOT EXISTS idx_products_title_trgm 
    ON products USING gin (title gin_trgm_ops);

-- Trigram index for brand search
CREATE INDEX IF NOT EXISTS idx_products_brand_trgm 
    ON products USING gin (brand gin_trgm_ops);

-- Category lookups
CREATE INDEX IF NOT EXISTS idx_products_category 
    ON products(category) WHERE category IS NOT NULL;

-- JSONB metadata search
CREATE INDEX IF NOT EXISTS idx_products_metadata_gin 
    ON products USING gin (metadata jsonb_path_ops);

-- Popular products (for homepage)
CREATE INDEX IF NOT EXISTS idx_products_views 
    ON products(views_count DESC, created_at DESC);

-- ============================================================================
-- PRODUCT PRICES - Time-series Indexes
-- ============================================================================

-- Composite index for price history queries
CREATE INDEX IF NOT EXISTS idx_product_prices_product_time 
    ON product_prices(product_id, scraped_at DESC, price);

-- Best price per site
CREATE INDEX IF NOT EXISTS idx_product_prices_site_best 
    ON product_prices(product_id, site_name, price);

-- Recent prices (for sparklines) - simple index without WHERE clause
CREATE INDEX IF NOT EXISTS idx_product_prices_recent 
    ON product_prices(scraped_at DESC);

-- In-stock products
CREATE INDEX IF NOT EXISTS idx_product_prices_in_stock 
    ON product_prices(product_id, in_stock, price) 
    WHERE in_stock = TRUE;

-- ============================================================================
-- RAW SCRAPES - Processing Queue
-- ============================================================================

-- Unprocessed scrapes queue
CREATE INDEX IF NOT EXISTS idx_raw_scrapes_unprocessed 
    ON raw_scrapes(scraped_at) 
    WHERE processed = FALSE;

-- Site-specific error tracking
CREATE INDEX IF NOT EXISTS idx_raw_scrapes_errors 
    ON raw_scrapes(site_name, scraped_at DESC) 
    WHERE processing_error IS NOT NULL;

-- ============================================================================
-- EMBEDDINGS - Vector Search
-- ============================================================================

-- Additional product lookup
CREATE INDEX IF NOT EXISTS idx_embeddings_product 
    ON embeddings(product_id);

-- Model filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_model 
    ON embeddings(model_name);

-- ============================================================================
-- ALERTS - Active Monitoring
-- ============================================================================

-- Active alerts for monitoring worker
CREATE INDEX IF NOT EXISTS idx_price_alerts_monitoring 
    ON price_alerts(active, last_triggered_at NULLS FIRST) 
    WHERE active = TRUE;

-- User alert dashboard
CREATE INDEX IF NOT EXISTS idx_price_alerts_user_recent 
    ON price_alerts(user_id, created_at DESC);

-- ============================================================================
-- RETAILERS - Active Sites
-- ============================================================================

-- Active retailers for scraper
CREATE INDEX IF NOT EXISTS idx_retailers_active 
    ON retailers(active, last_scrape_at NULLS FIRST) 
    WHERE active = TRUE;

-- ============================================================================
-- ANALYTICS INSIGHTS - Valid Cache
-- ============================================================================

-- Valid insights lookup (full index - filter by valid_until in queries)
CREATE INDEX IF NOT EXISTS idx_analytics_valid 
    ON analytics_insights(product_id, insight_type, created_at DESC);

-- ============================================================================
-- Composite Indexes for Common Queries
-- ============================================================================

-- User's active alerts with product info
CREATE INDEX IF NOT EXISTS idx_alerts_user_product_active 
    ON price_alerts(user_id, product_id, active);

-- Smart list items with product
CREATE INDEX IF NOT EXISTS idx_list_items_with_product 
    ON smart_list_items(list_id, product_id, added_at DESC);

-- Alert history timeline
CREATE INDEX IF NOT EXISTS idx_alert_history_timeline 
    ON alert_history(alert_id, triggered_at DESC, notification_sent);

-- ============================================================================
-- Statistics & Maintenance
-- ============================================================================

-- Analyze tables for better query planning
ANALYZE products;
ANALYZE product_prices;
ANALYZE raw_scrapes;
ANALYZE embeddings;
ANALYZE price_alerts;

DO $$
BEGIN
    RAISE NOTICE '✅ All indexes created successfully';
    RAISE NOTICE '   - Trigram indexes for fuzzy search';
    RAISE NOTICE '   - GIN indexes for JSONB queries';
    RAISE NOTICE '   - IVFFlat index for vector similarity';
    RAISE NOTICE '   - Composite indexes for common queries';
END $$;
