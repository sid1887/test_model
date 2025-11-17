-- LISTEN/NOTIFY Triggers for Real-time Updates
-- Enables push notifications to FastAPI for SSE/WebSocket

-- ============================================================================
-- TRIGGER: New Price Insert - Notify subscribers
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_price_insert() 
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    payload := json_build_object(
        'event', 'price_insert',
        'product_id', NEW.product_id,
        'product_price_id', NEW.id,
        'site_name', NEW.site_name,
        'price', NEW.price,
        'original_price', NEW.original_price,
        'in_stock', NEW.in_stock,
        'scraped_at', NEW.scraped_at
    );
    
    -- Notify on general channel
    PERFORM pg_notify('price_updates', payload::text);
    
    -- Notify on product-specific channel
    PERFORM pg_notify('product_' || NEW.product_id::text, payload::text);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notify_price_insert
AFTER INSERT ON product_prices
FOR EACH ROW
EXECUTE FUNCTION notify_price_insert();

COMMENT ON FUNCTION notify_price_insert IS 'Notifies listeners when new price is inserted';

-- ============================================================================
-- TRIGGER: Price Alert Fired - Notify user
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_alert_fired()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    alert_info RECORD;
BEGIN
    -- Get alert details
    SELECT 
        pa.user_id,
        pa.product_id,
        pa.condition_type,
        pa.threshold,
        pa.notification_channels
    INTO alert_info
    FROM price_alerts pa
    WHERE pa.id = NEW.alert_id;
    
    payload := json_build_object(
        'event', 'alert_fired',
        'alert_id', NEW.alert_id,
        'user_id', alert_info.user_id,
        'product_id', alert_info.product_id,
        'triggered_price', NEW.triggered_price,
        'previous_price', NEW.previous_price,
        'condition_type', alert_info.condition_type,
        'channels', alert_info.notification_channels,
        'triggered_at', NEW.triggered_at
    );
    
    -- Notify on user channel
    PERFORM pg_notify('user_' || alert_info.user_id::text, payload::text);
    
    -- Notify on general alerts channel
    PERFORM pg_notify('alert_fired', payload::text);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notify_alert_fired
AFTER INSERT ON alert_history
FOR EACH ROW
EXECUTE FUNCTION notify_alert_fired();

COMMENT ON FUNCTION notify_alert_fired IS 'Notifies user when their price alert is triggered';

-- ============================================================================
-- TRIGGER: Product Updated - Notify watchers
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_product_update()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    changes TEXT[];
BEGIN
    -- Track what changed
    IF OLD.title IS DISTINCT FROM NEW.title THEN
        changes := array_append(changes, 'title');
    END IF;
    IF OLD.avg_price IS DISTINCT FROM NEW.avg_price THEN
        changes := array_append(changes, 'price');
    END IF;
    IF OLD.metadata IS DISTINCT FROM NEW.metadata THEN
        changes := array_append(changes, 'metadata');
    END IF;
    
    -- Only notify if there are actual changes
    IF array_length(changes, 1) > 0 THEN
        payload := json_build_object(
            'event', 'product_update',
            'product_id', NEW.id,
            'changes', changes,
            'updated_at', NEW.updated_at
        );
        
        PERFORM pg_notify('product_updates', payload::text);
        PERFORM pg_notify('product_' || NEW.id::text, payload::text);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notify_product_update
AFTER UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION notify_product_update();

COMMENT ON FUNCTION notify_product_update IS 'Notifies when product info changes';

-- ============================================================================
-- TRIGGER: Raw Scrape Processing Error - Log & Notify
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_scrape_error()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    -- Only notify on error state
    IF NEW.processing_error IS NOT NULL AND OLD.processing_error IS NULL THEN
        payload := json_build_object(
            'event', 'scrape_error',
            'scrape_id', NEW.id,
            'site_name', NEW.site_name,
            'url', NEW.url,
            'error', NEW.processing_error,
            'scraped_at', NEW.scraped_at
        );
        
        PERFORM pg_notify('scrape_errors', payload::text);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notify_scrape_error
AFTER UPDATE ON raw_scrapes
FOR EACH ROW
EXECUTE FUNCTION notify_scrape_error();

-- ============================================================================
-- TRIGGER: Smart List Price Drop - Notify user
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_list_price_drop()
RETURNS TRIGGER AS $$
DECLARE
    affected_lists RECORD;
    payload JSON;
BEGIN
    -- Find all smart lists containing this product
    FOR affected_lists IN 
        SELECT DISTINCT sl.id, sl.user_id, sl.name
        FROM smart_lists sl
        JOIN smart_list_items sli ON sli.list_id = sl.id
        WHERE sli.product_id = NEW.product_id
        AND sl.auto_update = TRUE
    LOOP
        payload := json_build_object(
            'event', 'list_price_drop',
            'list_id', affected_lists.id,
            'list_name', affected_lists.name,
            'user_id', affected_lists.user_id,
            'product_id', NEW.product_id,
            'new_price', NEW.price,
            'site_name', NEW.site_name
        );
        
        PERFORM pg_notify('user_' || affected_lists.user_id::text, payload::text);
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Only notify on significant price drops (> 5%)
CREATE TRIGGER trg_notify_list_price_drop
AFTER INSERT ON product_prices
FOR EACH ROW
WHEN (NEW.discount_percent > 5)
EXECUTE FUNCTION notify_list_price_drop();

-- ============================================================================
-- UTILITY FUNCTION: Manual notification for testing
-- ============================================================================
CREATE OR REPLACE FUNCTION send_test_notification(
    channel TEXT,
    message TEXT
)
RETURNS VOID AS $$
BEGIN
    PERFORM pg_notify(channel, message);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION send_test_notification IS 'Send test notification for debugging';

-- Usage: SELECT send_test_notification('price_updates', '{"test": true}');

-- ============================================================================
-- Create notification channels reference table
-- ============================================================================
CREATE TABLE IF NOT EXISTS notification_channels (
    channel_name TEXT PRIMARY KEY,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO notification_channels (channel_name, description) VALUES
    ('price_updates', 'New price inserts from scraper'),
    ('alert_fired', 'Price alerts triggered'),
    ('product_updates', 'Product information changes'),
    ('scrape_errors', 'Scraping errors and failures')
ON CONFLICT (channel_name) DO NOTHING;

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ LISTEN/NOTIFY triggers created successfully';
    RAISE NOTICE '   Channels: price_updates, alert_fired, product_updates, scrape_errors';
    RAISE NOTICE '   Use: LISTEN channel_name; in psql to test';
END $$;
