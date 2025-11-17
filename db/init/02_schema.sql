-- Core Schema with JSONB Support
-- Production-ready tables for Cumpair platform

-- ============================================================================
-- PRODUCTS - Canonical product entities
-- ============================================================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    canonical_sku TEXT,
    category TEXT,
    brand TEXT,
    main_image TEXT,
    description TEXT,
    
    -- JSONB for flexible metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Normalized fields
    avg_price NUMERIC(12,2),
    min_price NUMERIC(12,2),
    max_price NUMERIC(12,2),
    
    -- Tracking
    views_count INTEGER DEFAULT 0,
    searches_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ
);

-- Unique constraint on canonical_sku if present
CREATE UNIQUE INDEX idx_products_canonical_sku ON products(canonical_sku) WHERE canonical_sku IS NOT NULL;

COMMENT ON TABLE products IS 'Canonical product catalog with JSONB metadata';
COMMENT ON COLUMN products.metadata IS 'Flexible JSONB: variants, specs, tags, site_mappings';

-- ============================================================================
-- RAW SCRAPES - Every scrape stored as JSONB
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_scrapes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_identifier TEXT,
    site_name TEXT NOT NULL,
    url TEXT NOT NULL,
    
    -- Raw scraped data as JSONB
    raw_data JSONB NOT NULL,
    headers JSONB,
    
    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    
    -- Timestamps
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_raw_scrapes_site_processed ON raw_scrapes(site_name, processed, scraped_at DESC);
CREATE INDEX idx_raw_scrapes_raw_data_gin ON raw_scrapes USING gin (raw_data jsonb_path_ops);

COMMENT ON TABLE raw_scrapes IS 'Raw scraper output stored as JSONB for flexibility';

-- ============================================================================
-- PRODUCT PRICES - Normalized price snapshots
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_prices (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Site information
    site_name TEXT NOT NULL,
    site_product_id TEXT,
    site_url TEXT,
    
    -- Price data
    price NUMERIC(12,2) NOT NULL,
    original_price NUMERIC(12,2),
    discount_percent NUMERIC(5,2),
    currency TEXT DEFAULT 'INR',
    
    -- Availability
    availability TEXT,
    in_stock BOOLEAN DEFAULT TRUE,
    
    -- Structured data from scrape
    scraped_data JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_product_prices_product_scraped ON product_prices(product_id, scraped_at DESC);
CREATE INDEX idx_product_prices_site_product ON product_prices(site_name, site_product_id);
CREATE INDEX idx_product_prices_price ON product_prices(product_id, price);
CREATE INDEX idx_product_prices_scraped_data_gin ON product_prices USING gin (scraped_data jsonb_path_ops);

COMMENT ON TABLE product_prices IS 'Price snapshots per site with JSONB for flexible offer data';

-- ============================================================================
-- EMBEDDINGS - Vector storage for AI/CLIP
-- ============================================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Model info
    model_name TEXT NOT NULL,
    model_version TEXT,
    
    -- Vector (adjust dimensionality based on model)
    vec VECTOR(512),  -- CLIP ViT-B/32 uses 512 dimensions
    
    -- Metadata
    meta JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (IVFFlat)
CREATE INDEX idx_embeddings_vec_ivfflat ON embeddings 
    USING ivfflat (vec vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX idx_embeddings_product_model ON embeddings(product_id, model_name);

COMMENT ON TABLE embeddings IS 'Vector embeddings for semantic/image search using pgvector';

-- ============================================================================
-- PRICE ALERTS - User price triggers
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Alert conditions
    condition_type TEXT NOT NULL,  -- 'below', 'percent_drop', 'back_in_stock'
    threshold NUMERIC(12,2),
    threshold_percent NUMERIC(5,2),
    
    -- Configuration
    active BOOLEAN DEFAULT TRUE,
    notification_channels JSONB DEFAULT '["email"]'::jsonb,
    
    -- Tracking
    times_triggered INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_alerts_user_active ON price_alerts(user_id, active);
CREATE INDEX idx_price_alerts_product_active ON price_alerts(product_id, active);

COMMENT ON TABLE price_alerts IS 'User-configured price alerts with flexible notification channels';

-- ============================================================================
-- ALERT HISTORY - Alert trigger events
-- ============================================================================
CREATE TABLE IF NOT EXISTS alert_history (
    id BIGSERIAL PRIMARY KEY,
    alert_id BIGINT REFERENCES price_alerts(id) ON DELETE CASCADE,
    product_price_id BIGINT REFERENCES product_prices(id),
    
    -- Event details
    triggered_price NUMERIC(12,2),
    previous_price NUMERIC(12,2),
    payload JSONB DEFAULT '{}'::jsonb,
    
    -- Notification status
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_error TEXT,
    
    -- Timestamp
    triggered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_history_alert_triggered ON alert_history(alert_id, triggered_at DESC);

-- ============================================================================
-- RETAILERS - Site/retailer configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS retailers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    
    -- Scraper configuration
    scraper_config JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    last_scrape_at TIMESTAMPTZ,
    
    -- Performance metrics
    success_rate NUMERIC(5,2),
    avg_response_time NUMERIC(8,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN retailers.scraper_config IS 'Scraper selectors, rate limits, auth config';

-- ============================================================================
-- SMART LISTS - User shopping lists
-- ============================================================================
CREATE TABLE IF NOT EXISTS smart_lists (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Configuration
    auto_update BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_smart_lists_user ON smart_lists(user_id);

-- ============================================================================
-- SMART LIST ITEMS - Products in lists
-- ============================================================================
CREATE TABLE IF NOT EXISTS smart_list_items (
    id BIGSERIAL PRIMARY KEY,
    list_id BIGINT REFERENCES smart_lists(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    quantity INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 0,
    notes TEXT,
    
    added_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_smart_list_items_list ON smart_list_items(list_id);
CREATE UNIQUE INDEX idx_smart_list_items_list_product ON smart_list_items(list_id, product_id);

-- ============================================================================
-- ANALYTICS INSIGHTS - Cached analytics results
-- ============================================================================
CREATE TABLE IF NOT EXISTS analytics_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    insight_type TEXT NOT NULL,  -- 'trend', 'forecast', 'anomaly', 'sentiment'
    
    -- Results stored as JSONB
    data JSONB NOT NULL,
    
    -- Metadata
    model_name TEXT,
    confidence NUMERIC(5,4),
    
    -- Validity
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analytics_insights_product_type ON analytics_insights(product_id, insight_type, valid_until DESC);

COMMENT ON TABLE analytics_insights IS 'Cached AI-generated insights with expiration';

-- ============================================================================
-- Create updated_at trigger function
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_price_alerts_updated_at BEFORE UPDATE ON price_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_smart_lists_updated_at BEFORE UPDATE ON smart_lists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Core schema with JSONB created successfully';
END $$;
