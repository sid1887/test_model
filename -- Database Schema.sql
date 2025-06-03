-- Database Schema
-- Generated on 2025-06-03T13:35:49.589Z

-- Total tables: 4

-- Table: alembic_version
-- Columns: 1
CREATE TABLE alembic_version (
    version_num character varying NOT NULL
);

-- Table: analyses
-- Columns: 12
CREATE TABLE analyses (
    id integer NOT NULL DEFAULT nextval('analyses_id_seq'::regclass),
    product_id integer NOT NULL,
    analysis_type character varying NOT NULL,
    raw_results json,
    processed_results json,
    confidence_score numeric,
    processing_time numeric,
    model_version character varying,
    status character varying,
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);

-- Table: price_comparisons
-- Columns: 26
CREATE TABLE price_comparisons (
    id integer NOT NULL DEFAULT nextval('price_comparisons_id_seq'::regclass),
    product_id integer NOT NULL,
    source_name character varying NOT NULL,
    source_url character varying NOT NULL,
    title character varying,
    description text,
    price numeric,
    currency character varying,
    original_price numeric,
    discount_percentage numeric,
    in_stock boolean,
    stock_quantity integer,
    rating numeric,
    review_count integer,
    seller_name character varying,
    seller_rating numeric,
    shipping_cost numeric,
    shipping_time character varying,
    additional_data json,
    scraping_method character varying,
    proxy_used character varying,
    scraping_duration numeric,
    is_valid boolean,
    confidence_score numeric,
    scraped_at timestamp with time zone DEFAULT now(),
    price_updated_at timestamp with time zone
);

-- Table: products
-- Columns: 13
CREATE TABLE products (
    id integer NOT NULL DEFAULT nextval('products_id_seq'::regclass),
    name character varying NOT NULL,
    brand character varying,
    category character varying,
    image_path character varying NOT NULL,
    image_hash character varying,
    specifications json,
    detection_confidence numeric,
    specification_confidence numeric,
    is_processed boolean,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);

