-- PostgreSQL Extensions for Cumpair Platform
-- Run this first on database initialization

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search & fuzzy matching
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- JSONB indexing support
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Vector embeddings for CLIP/AI models
CREATE EXTENSION IF NOT EXISTS "vector";

-- Time-series support (optional, uncomment if needed)
-- CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Log extension status
DO $$
BEGIN
    RAISE NOTICE '✅ All PostgreSQL extensions installed successfully';
END $$;
