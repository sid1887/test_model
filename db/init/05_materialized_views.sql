-- Materialized Views for Performance
-- Pre-computed aggregations and frequently accessed data

-- ============================================================================
-- MV: Best Price Per Product
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_best_price_per_product AS
SELECT 
    p.id AS product_id,
    p.title,
    p.category,
    p.brand,
    pp.site_name AS best_price_site,
    pp.price AS best_price,
    pp.original_price,
    pp.discount_percent,
    pp.in_stock,
    pp.scraped_at AS price_updated_at,
    pp.site_url
FROM products p
JOIN LATERAL (
    SELECT *
    FROM product_prices pp2
    WHERE pp2.product_id = p.id
    AND pp2.in_stock = TRUE
    ORDER BY pp2.price ASC, pp2.scraped_at DESC
    LIMIT 1
) pp ON TRUE;

CREATE UNIQUE INDEX idx_mv_best_price_product ON mv_best_price_per_product(product_id);
CREATE INDEX idx_mv_best_price_category ON mv_best_price_per_product(category, best_price);

COMMENT ON MATERIALIZED VIEW mv_best_price_per_product IS 'Best available price per product, refreshed periodically';

-- ============================================================================
-- MV: Product Price History Summary (Last 30 days)
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_price_summary AS
SELECT 
    product_id,
    COUNT(*) AS price_check_count,
    MIN(price) AS min_price_30d,
    MAX(price) AS max_price_30d,
    AVG(price)::NUMERIC(12,2) AS avg_price_30d,
    STDDEV(price)::NUMERIC(12,2) AS price_volatility,
    COUNT(DISTINCT site_name) AS available_sites,
    MAX(scraped_at) AS last_updated
FROM product_prices
WHERE scraped_at > NOW() - INTERVAL '30 days'
GROUP BY product_id;

CREATE UNIQUE INDEX idx_mv_price_summary_product ON mv_product_price_summary(product_id);

COMMENT ON MATERIALIZED VIEW mv_product_price_summary IS '30-day price statistics per product';

-- ============================================================================
-- MV: Retailer Performance
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_retailer_performance AS
SELECT 
    rs.site_name,
    COUNT(*) AS total_scrapes,
    SUM(CASE WHEN rs.processed = TRUE THEN 1 ELSE 0 END) AS successful_scrapes,
    SUM(CASE WHEN rs.processing_error IS NOT NULL THEN 1 ELSE 0 END) AS failed_scrapes,
    ROUND(
        (SUM(CASE WHEN rs.processed = TRUE THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100,
        2
    ) AS success_rate,
    COUNT(DISTINCT DATE(rs.scraped_at)) AS days_active,
    MAX(rs.scraped_at) AS last_scrape_at
FROM raw_scrapes rs
WHERE rs.scraped_at > NOW() - INTERVAL '7 days'
GROUP BY rs.site_name;

CREATE UNIQUE INDEX idx_mv_retailer_perf_site ON mv_retailer_performance(site_name);

COMMENT ON MATERIALIZED VIEW mv_retailer_performance IS 'Retailer scraping performance metrics';

-- ============================================================================
-- MV: Trending Products (by views & searches)
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trending_products AS
SELECT 
    p.id AS product_id,
    p.title,
    p.category,
    p.brand,
    p.main_image,
    p.views_count,
    p.searches_count,
    (p.views_count * 0.6 + p.searches_count * 0.4)::INTEGER AS trending_score,
    bp.best_price,
    bp.best_price_site,
    p.created_at
FROM products p
LEFT JOIN mv_best_price_per_product bp ON bp.product_id = p.id
WHERE p.created_at > NOW() - INTERVAL '90 days'
ORDER BY trending_score DESC
LIMIT 100;

CREATE INDEX idx_mv_trending_score ON mv_trending_products(trending_score DESC);
CREATE INDEX idx_mv_trending_category ON mv_trending_products(category, trending_score DESC);

COMMENT ON MATERIALIZED VIEW mv_trending_products IS 'Top 100 trending products by engagement';

-- ============================================================================
-- MV: Active Alerts Summary
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_active_alerts_summary AS
SELECT 
    pa.user_id,
    COUNT(*) AS total_alerts,
    SUM(CASE WHEN pa.last_triggered_at IS NOT NULL THEN 1 ELSE 0 END) AS triggered_alerts,
    COUNT(DISTINCT pa.product_id) AS watched_products,
    MAX(pa.last_triggered_at) AS last_trigger_time
FROM price_alerts pa
WHERE pa.active = TRUE
GROUP BY pa.user_id;

CREATE UNIQUE INDEX idx_mv_alerts_user ON mv_active_alerts_summary(user_id);

COMMENT ON MATERIALIZED VIEW mv_active_alerts_summary IS 'Per-user alert statistics';

-- ============================================================================
-- Function: Refresh All Materialized Views
-- ============================================================================
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS TABLE(view_name TEXT, refresh_time INTERVAL) AS $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
BEGIN
    -- Refresh best prices
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_best_price_per_product;
    end_time := clock_timestamp();
    view_name := 'mv_best_price_per_product';
    refresh_time := end_time - start_time;
    RETURN NEXT;
    
    -- Refresh price summary
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_price_summary;
    end_time := clock_timestamp();
    view_name := 'mv_product_price_summary';
    refresh_time := end_time - start_time;
    RETURN NEXT;
    
    -- Refresh retailer performance
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_retailer_performance;
    end_time := clock_timestamp();
    view_name := 'mv_retailer_performance';
    refresh_time := end_time - start_time;
    RETURN NEXT;
    
    -- Refresh trending products
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW mv_trending_products;
    end_time := clock_timestamp();
    view_name := 'mv_trending_products';
    refresh_time := end_time - start_time;
    RETURN NEXT;
    
    -- Refresh alerts summary
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_active_alerts_summary;
    end_time := clock_timestamp();
    view_name := 'mv_active_alerts_summary';
    refresh_time := end_time - start_time;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views IS 'Refresh all materialized views and return timing';

-- Usage: SELECT * FROM refresh_all_materialized_views();

-- ============================================================================
-- Initial refresh
-- ============================================================================
REFRESH MATERIALIZED VIEW mv_best_price_per_product;
REFRESH MATERIALIZED VIEW mv_product_price_summary;
REFRESH MATERIALIZED VIEW mv_retailer_performance;
REFRESH MATERIALIZED VIEW mv_trending_products;
REFRESH MATERIALIZED VIEW mv_active_alerts_summary;

DO $$
BEGIN
    RAISE NOTICE '✅ Materialized views created and refreshed';
    RAISE NOTICE '   - mv_best_price_per_product';
    RAISE NOTICE '   - mv_product_price_summary';
    RAISE NOTICE '   - mv_retailer_performance';
    RAISE NOTICE '   - mv_trending_products';
    RAISE NOTICE '   - mv_active_alerts_summary';
    RAISE NOTICE '';
    RAISE NOTICE '💡 Refresh all views: SELECT * FROM refresh_all_materialized_views();';
END $$;
