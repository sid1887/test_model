-- Phase 2 Database Schema Extensions
-- Product linking, news, market data, and additional tracking tables

-- ============================================================================
-- PRODUCT VERSIONS - Track merged products
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_versions (
    id BIGSERIAL PRIMARY KEY,
    original_id UUID REFERENCES products(id) ON DELETE CASCADE,
    canonical_id UUID REFERENCES products(id) ON DELETE CASCADE,

    -- Merge details
    merge_reason TEXT,
    metadata_retained JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    merged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_product_versions_original ON product_versions(original_id);
CREATE INDEX idx_product_versions_canonical ON product_versions(canonical_id);

COMMENT ON TABLE product_versions IS 'Track product merges and deduplication history';

-- ============================================================================
-- NEWS ARTICLES - News data from multiple sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    source TEXT NOT NULL,
    url TEXT UNIQUE,

    -- Classification
    category TEXT,  -- 'tech', 'crypto', 'stocks', 'general', 'retail'
    sentiment_score NUMERIC(3,2),  -- -1 to 1 from HF sentiment analysis

    -- NER extraction
    entities JSONB DEFAULT '{}'::jsonb,  -- {companies: [], products: [], symbols: []}

    -- Timestamps
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_articles_source ON news_articles(source, published_at DESC);
CREATE INDEX idx_news_articles_category ON news_articles(category, published_at DESC);
CREATE INDEX idx_news_articles_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_articles_entities_gin ON news_articles USING gin (entities jsonb_path_ops);

-- Full-text search index
CREATE INDEX idx_news_articles_fts ON news_articles USING gin (
    to_tsvector('english', title || ' ' || COALESCE(content, ''))
);

COMMENT ON TABLE news_articles IS 'News articles from multiple sources with NER entities and sentiment';

-- ============================================================================
-- NEWS MENTIONS - Link news to products/stocks/crypto
-- ============================================================================
CREATE TABLE IF NOT EXISTS news_mentions (
    id BIGSERIAL PRIMARY KEY,
    article_id UUID REFERENCES news_articles(id) ON DELETE CASCADE,

    -- Can mention: products, stocks, or crypto
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    stock_symbol TEXT,  -- e.g., 'AAPL'
    crypto_symbol TEXT,  -- e.g., 'BTC'

    -- Mention type
    mention_type TEXT,  -- 'direct', 'indirect', 'competitor', 'supplier'
    context TEXT,  -- Excerpt around the mention
    relevance_score NUMERIC(3,2),  -- 0 to 1

    mentioned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_mentions_article ON news_mentions(article_id);
CREATE INDEX idx_news_mentions_product ON news_mentions(product_id);
CREATE INDEX idx_news_mentions_stock ON news_mentions(stock_symbol);
CREATE INDEX idx_news_mentions_crypto ON news_mentions(crypto_symbol);

COMMENT ON TABLE news_mentions IS 'Link news articles to products, stocks, and crypto';

-- ============================================================================
-- CRYPTO PRICES - Cryptocurrency price tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS crypto_prices (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,  -- 'BTC', 'ETH', etc.
    name TEXT,  -- Full name

    -- Price data
    price NUMERIC(20,8) NOT NULL,
    market_cap NUMERIC(20,2),
    volume_24h NUMERIC(20,2),
    change_24h NUMERIC(8,4),  -- Percent change
    change_7d NUMERIC(8,4),
    change_30d NUMERIC(8,4),

    -- Additional metrics
    market_cap_rank INTEGER,
    circulating_supply NUMERIC(20,2),
    total_supply NUMERIC(20,2),
    ath NUMERIC(20,8),  -- All-time high
    atl NUMERIC(20,8),  -- All-time low

    -- Source
    source TEXT DEFAULT 'coingecko',  -- Data source

    -- Timestamp
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crypto_prices_symbol_recorded ON crypto_prices(symbol, recorded_at DESC);
CREATE INDEX idx_crypto_prices_recorded ON crypto_prices(recorded_at DESC);

COMMENT ON TABLE crypto_prices IS 'Real-time cryptocurrency prices from CoinGecko';

-- ============================================================================
-- STOCK PRICES - Stock price tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,  -- 'AAPL', 'GOOGL', etc.
    company_name TEXT,

    -- Price data
    open NUMERIC(10,2),
    high NUMERIC(10,2),
    low NUMERIC(10,2),
    close NUMERIC(10,2),
    volume BIGINT,

    -- Metrics
    pe_ratio NUMERIC(8,2),
    dividend_yield NUMERIC(6,4),
    market_cap NUMERIC(20,2),
    change_percent NUMERIC(8,4),

    -- Additional
    sector TEXT,
    industry TEXT,

    -- Source
    source TEXT DEFAULT 'yfinance',  -- Data source

    -- Timestamp (daily data)
    trading_date DATE NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_prices_ticker_date ON stock_prices(ticker, trading_date DESC);
CREATE INDEX idx_stock_prices_recorded ON stock_prices(recorded_at DESC);
CREATE UNIQUE INDEX idx_stock_prices_ticker_date_unique ON stock_prices(ticker, trading_date);

COMMENT ON TABLE stock_prices IS 'Daily stock prices from yfinance';

-- ============================================================================
-- PRODUCT CATEGORIES - Canonical category hierarchy
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES product_categories(id) ON DELETE CASCADE,

    -- Metadata
    icon TEXT,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_product_categories_parent ON product_categories(parent_id);

COMMENT ON TABLE product_categories IS 'Canonical product category hierarchy';

-- ============================================================================
-- PRODUCT CATEGORY MAPPING - Map retailer categories to canonical
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_category_mapping (
    id BIGSERIAL PRIMARY KEY,
    retailer_name TEXT NOT NULL,
    retailer_category TEXT NOT NULL,
    canonical_category_id INTEGER REFERENCES product_categories(id),

    -- Mapping metadata
    confidence NUMERIC(3,2),  -- 0 to 1
    is_manual BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_category_mapping_retailer ON product_category_mapping(retailer_name, retailer_category);
CREATE UNIQUE INDEX idx_category_mapping_unique ON product_category_mapping(retailer_name, retailer_category);

COMMENT ON TABLE product_category_mapping IS 'Map retailer-specific categories to canonical categories';

-- ============================================================================
-- PRODUCT NAME MAPPING - Map variant names to canonical
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_name_mapping (
    id BIGSERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,

    -- Mapping metadata
    retailer TEXT,
    similarity_score NUMERIC(3,2),
    is_manual BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_name_mapping_canonical ON product_name_mapping(canonical_name);
CREATE INDEX idx_name_mapping_variant ON product_name_mapping(variant_name);
CREATE UNIQUE INDEX idx_name_mapping_unique ON product_name_mapping(canonical_name, variant_name);

COMMENT ON TABLE product_name_mapping IS 'Map product name variants to canonical names';

-- ============================================================================
-- EXCHANGE RATES - Currency conversion tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate NUMERIC(12,6) NOT NULL,

    source TEXT DEFAULT 'fixer.io',

    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exchange_rates_currencies ON exchange_rates(from_currency, to_currency, recorded_at DESC);

COMMENT ON TABLE exchange_rates IS 'Exchange rates for multi-currency price normalization';

-- ============================================================================
-- PRICE PREDICTIONS - ML-generated price forecasts
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,

    -- Prediction details
    predicted_price NUMERIC(12,2),
    confidence_interval_lower NUMERIC(12,2),
    confidence_interval_upper NUMERIC(12,2),
    confidence_score NUMERIC(3,2),

    -- Model info
    model_name TEXT,
    model_version TEXT,

    -- Timeline
    prediction_date DATE NOT NULL,
    days_ahead INTEGER,  -- How many days in advance
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Validity
    valid_until TIMESTAMPTZ
);

CREATE INDEX idx_price_predictions_product_date ON price_predictions(product_id, prediction_date DESC);

COMMENT ON TABLE price_predictions IS 'ML-generated price predictions for trending products';

-- ============================================================================
-- Update triggers for news articles
-- ============================================================================
CREATE TRIGGER update_news_articles_updated_at BEFORE UPDATE ON news_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Create trigger function for automatic price aggregation
-- ============================================================================
CREATE OR REPLACE FUNCTION update_product_price_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET
        avg_price = (SELECT AVG(price) FROM product_prices WHERE product_id = NEW.product_id),
        min_price = (SELECT MIN(price) FROM product_prices WHERE product_id = NEW.product_id AND in_stock = TRUE),
        max_price = (SELECT MAX(price) FROM product_prices WHERE product_id = NEW.product_id),
        last_scraped_at = NEW.scraped_at
    WHERE id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_price_stats AFTER INSERT ON product_prices
    FOR EACH ROW EXECUTE FUNCTION update_product_price_stats();

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Phase 2 schema extensions created successfully';
    RAISE NOTICE '   - Product versions (deduplication tracking)';
    RAISE NOTICE '   - News articles & mentions';
    RAISE NOTICE '   - Crypto & stock prices';
    RAISE NOTICE '   - Category & name mapping';
    RAISE NOTICE '   - Exchange rates';
    RAISE NOTICE '   - Price predictions';
END $$;
