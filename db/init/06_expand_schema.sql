-- ============================================================================
-- EXPANDED SCHEMA - Additional tables for full analytics functionality
-- Production-ready expansion to 02_schema.sql
-- ============================================================================

-- ============================================================================
-- FORECAST VALIDATIONS - Track accuracy of price forecasts over time
-- ============================================================================
CREATE TABLE IF NOT EXISTS forecast_validations (
    id BIGSERIAL PRIMARY KEY,
    forecast_id BIGINT,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Validation metadata
    validation_date TIMESTAMPTZ DEFAULT NOW(),
    validation_period_days INTEGER,
    actual_data_points INTEGER,
    
    -- Accuracy metrics
    mae NUMERIC(12,4),           -- Mean Absolute Error
    mape NUMERIC(8,4),           -- Mean Absolute Percentage Error
    rmse NUMERIC(12,4),          -- Root Mean Square Error
    accuracy_band_10pct NUMERIC(5,2),  -- % within 10% of actual
    
    -- Prediction vs actual data
    predictions_vs_actual JSONB DEFAULT '{}'::jsonb,
    
    -- Performance assessment
    accuracy_grade VARCHAR(20),  -- A, B, C, D, F
    model_performance VARCHAR(20),  -- excellent, good, fair, poor
    
    -- Status
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_forecast_validations_forecast ON forecast_validations(forecast_id);
CREATE INDEX idx_forecast_validations_product ON forecast_validations(product_id);
CREATE INDEX idx_forecast_validations_date ON forecast_validations(validation_date DESC);

COMMENT ON TABLE forecast_validations IS 'Accuracy tracking for price forecast models';

-- ============================================================================
-- SENTIMENT TRENDS - Sentiment analysis over time
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentiment_trends (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Time period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_type VARCHAR(20) DEFAULT 'weekly',  -- daily, weekly, monthly
    
    -- Sentiment metrics
    avg_sentiment_score NUMERIC(5,4) NOT NULL,
    sentiment_change NUMERIC(5,4),  -- Change from previous period
    sentiment_volatility NUMERIC(5,4),  -- Standard deviation
    
    -- Review volume
    total_reviews INTEGER NOT NULL,
    positive_reviews INTEGER NOT NULL,
    negative_reviews INTEGER NOT NULL,
    neutral_reviews INTEGER NOT NULL,
    
    -- Trend indicators
    trend_direction VARCHAR(20),  -- improving, declining, stable
    trend_strength NUMERIC(5,4),  -- 0 to 1 scale
    
    -- Topic trends
    trending_topics JSONB DEFAULT '{}'::jsonb,
    topic_changes JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sentiment_trends_product ON sentiment_trends(product_id);
CREATE INDEX idx_sentiment_trends_period ON sentiment_trends(product_id, period_end DESC);

COMMENT ON TABLE sentiment_trends IS 'Historical sentiment analysis trends per product';

-- ============================================================================
-- PRICE COMPARISONS - Detailed price comparison snapshots
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_comparisons (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Comparison metadata
    comparison_date TIMESTAMPTZ DEFAULT NOW(),
    num_retailers INTEGER,
    
    -- Price statistics
    lowest_price NUMERIC(12,2),
    highest_price NUMERIC(12,2),
    avg_price NUMERIC(12,2),
    median_price NUMERIC(12,2),
    
    -- Availability
    in_stock_count INTEGER,
    out_of_stock_count INTEGER,
    
    -- Detailed comparison data
    comparison_data JSONB DEFAULT '{}'::jsonb,
    
    -- Results
    best_deal_retailer TEXT,
    best_deal_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_comparisons_product ON price_comparisons(product_id);
CREATE INDEX idx_price_comparisons_date ON price_comparisons(product_id, comparison_date DESC);

COMMENT ON TABLE price_comparisons IS 'Periodic price comparison snapshots across retailers';

-- ============================================================================
-- PRICE HISTORY - Historical price tracking per retailer
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    site_name TEXT NOT NULL,
    site_product_id TEXT,
    
    -- Historical price data
    price NUMERIC(12,2) NOT NULL,
    original_price NUMERIC(12,2),
    discount_percent NUMERIC(5,2),
    currency TEXT DEFAULT 'INR',
    
    -- Availability
    in_stock BOOLEAN DEFAULT TRUE,
    
    -- Source
    scraped_from JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_history_product_site ON price_history(product_id, site_name);
CREATE INDEX idx_price_history_product_date ON price_history(product_id, recorded_at DESC);
CREATE INDEX idx_price_history_site_product ON price_history(site_name, site_product_id, recorded_at DESC);

COMMENT ON TABLE price_history IS 'Complete price history per site for trend analysis';

-- ============================================================================
-- PRODUCT SNAPSHOTS - Point-in-time product data snapshots
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_snapshots (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Snapshot data
    snapshot_data JSONB NOT NULL,
    
    -- Metadata
    snapshot_type VARCHAR(50),  -- 'automated', 'manual', 'scheduled'
    reason TEXT,
    
    -- Timestamps
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_product_snapshots_product ON product_snapshots(product_id);
CREATE INDEX idx_product_snapshots_time ON product_snapshots(product_id, snapshot_at DESC);

COMMENT ON TABLE product_snapshots IS 'Historical snapshots of product data for audit trail';

-- ============================================================================
-- NOTIFICATIONS - Notification queue and status
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    alert_id BIGINT REFERENCES price_alerts(id) ON DELETE SET NULL,
    
    -- Notification content
    notification_type VARCHAR(50),  -- 'price_drop', 'back_in_stock', 'forecast'
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    
    -- Channel and status
    channel VARCHAR(50),  -- 'email', 'sms', 'push'
    status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, failed, bounced
    
    -- Delivery
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    delivery_error TEXT,
    
    -- Data
    data JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_notifications_alert ON notifications(alert_id);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

COMMENT ON TABLE notifications IS 'Notification queue for price alerts and events';

-- ============================================================================
-- USER PREFERENCES - User analytics and notification settings
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    
    -- Notification preferences
    notify_email BOOLEAN DEFAULT TRUE,
    notify_sms BOOLEAN DEFAULT FALSE,
    notify_push BOOLEAN DEFAULT FALSE,
    
    -- Analytics preferences
    share_analytics BOOLEAN DEFAULT FALSE,
    email_digest_frequency VARCHAR(50) DEFAULT 'weekly',  -- daily, weekly, monthly
    
    -- Notification settings
    notification_settings JSONB DEFAULT '{
        "price_drop_enabled": true,
        "back_in_stock_enabled": true,
        "price_forecast_enabled": true,
        "quiet_hours_enabled": false,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00"
    }'::jsonb,
    
    -- Preferences
    preferences JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);

COMMENT ON TABLE user_preferences IS 'User notification and analytics preferences';

-- ============================================================================
-- LIST COMPARE JOBS - Tracking list comparison operations
-- ============================================================================
CREATE TABLE IF NOT EXISTS list_compare_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id BIGINT REFERENCES smart_lists(id) ON DELETE CASCADE,
    
    -- Job metadata
    job_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    
    -- Results
    results JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    
    -- Progress
    items_processed INTEGER DEFAULT 0,
    items_total INTEGER,
    
    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_list_compare_jobs_list ON list_compare_jobs(list_id);
CREATE INDEX idx_list_compare_jobs_status ON list_compare_jobs(status);

COMMENT ON TABLE list_compare_jobs IS 'Tracking for async list comparison jobs';

-- ============================================================================
-- LIST TEMPLATES - Pre-made shopping list templates
-- ============================================================================
CREATE TABLE IF NOT EXISTS list_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template info
    name TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Template data
    template_data JSONB NOT NULL,
    preview_products JSONB DEFAULT '[]'::jsonb,
    
    -- Public/private
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID,
    
    -- Usage stats
    times_used INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_list_templates_public ON list_templates(is_public);
CREATE INDEX idx_list_templates_category ON list_templates(category);

COMMENT ON TABLE list_templates IS 'Pre-made templates for quick list creation';

-- ============================================================================
-- Create/update triggers for new tables
-- ============================================================================
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_list_templates_updated_at BEFORE UPDATE ON list_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Expanded schema with analytics tables created successfully';
END $$;
