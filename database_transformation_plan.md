# Database Transformation Plan - PostgreSQL with JSONB & pgvector

## Overview
Transform the current database to a production-ready PostgreSQL setup with:
- JSONB for flexible data storage
- pgvector for AI embeddings
- Proper indexing and partitioning
- Real-time LISTEN/NOTIFY
- TimescaleDB for time-series data

## Current State Analysis
- Using AsyncSession (SQLAlchemy async)
- Basic models: Product, PriceComparison, Analysis, Alert, SmartList
- Missing: proper JSONB usage, vector search, partitioning

## Target Architecture

```
Scraper (Node.js) → raw_scrapes (JSONB)
         ↓
Processor (Celery) → products + product_prices (normalized)
         ↓
AI Engine → embeddings (pgvector)
         ↓
Alert Engine ← LISTEN/NOTIFY ← product_prices trigger
         ↓
FastAPI ← SSE/WebSocket ← Frontend
```

## Implementation Phases

### Phase 1: Database Setup (Immediate)
1. Add PostgreSQL extensions
2. Create new schema with JSONB tables
3. Add indexes (GIN, trigram, ivfflat)

### Phase 2: Migration Scripts (Next)
1. Create Alembic migrations
2. Migrate existing data
3. Update models to use async SQLAlchemy properly

### Phase 3: Real-time Features (After migration)
1. Add LISTEN/NOTIFY triggers
2. Implement SSE for frontend
3. Add connection pooling (pgbouncer)

### Phase 4: Optimization (Production)
1. Add TimescaleDB for price history
2. Create materialized views
3. Set up monitoring & backups

## Files to Create/Modify

### New Files:
- `db/init/01_extensions.sql` - PostgreSQL extensions
- `db/init/02_schema.sql` - New schema
- `db/init/03_indexes.sql` - Indexes
- `db/init/04_triggers.sql` - LISTEN/NOTIFY triggers
- `alembic/versions/xxx_jsonb_transformation.py` - Migration
- `app/core/database_v2.py` - Updated async database layer
- `app/models_v2/` - New models with JSONB

### Modified Files:
- `docker-compose.yml` - Add pgvector, pgbouncer
- `app/core/database.py` - Fix async queries
- All route files using `.query()` - Convert to async

## Execution Steps

1. **Stop current services**
2. **Create new database schema**
3. **Rebuild backend with fixed async queries**
4. **Test services**
5. **Gradually migrate to JSONB**
