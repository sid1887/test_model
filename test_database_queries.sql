-- Test queries for Database MCP Assistant Extension
-- Use these to verify the extension is working with our Compair database

-- 1. Basic connectivity test - show all tables
SELECT table_name, table_schema 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 2. Check products table structure and data
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'products' 
ORDER BY ordinal_position;

-- 3. View all products with their analysis status
SELECT 
    id,
    name,
    brand,
    category,
    is_processed,
    created_at
FROM products 
ORDER BY created_at DESC;

-- 4. Check analysis results for products
SELECT 
    p.id as product_id,
    p.name as product_name,
    a.analysis_type,
    a.status,
    a.confidence_score,
    a.processing_time,
    a.model_version,
    a.created_at
FROM products p
LEFT JOIN analyses a ON p.id = a.product_id
ORDER BY p.id, a.created_at DESC;

-- 5. Check CLIP indexing status (if any products exist)
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN is_processed = true THEN 1 END) as processed_products,
    COUNT(CASE WHEN is_processed = false THEN 1 END) as pending_products
FROM products;

-- 6. View detailed analysis results (JSON data)
SELECT 
    p.name,
    a.raw_results->>'object_detection' as object_detection,
    a.raw_results->>'brand_recognition' as brand_recognition,
    a.raw_results->>'category_classification' as category_classification,
    a.processed_results
FROM products p
JOIN analyses a ON p.id = a.product_id
WHERE a.status = 'completed'
ORDER BY a.created_at DESC;

-- 7. Check for any price comparison data
SELECT 
    p.name as product_name,
    pc.source_name,
    pc.price,
    pc.currency,
    pc.title,
    pc.in_stock
FROM products p
LEFT JOIN price_comparisons pc ON p.id = pc.product_id
ORDER BY p.id;

-- 8. Database health check
SELECT 
    'products' as table_name, COUNT(*) as record_count FROM products
UNION ALL
SELECT 
    'analyses' as table_name, COUNT(*) as record_count FROM analyses
UNION ALL
SELECT 
    'price_comparisons' as table_name, COUNT(*) as record_count FROM price_comparisons;
