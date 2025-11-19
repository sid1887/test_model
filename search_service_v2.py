"""
Search Service (Port 8010) - Phase 6 + Phase 7 Integration
Real-time search with sharding, caching, connection pooling
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import logging
import asyncio
from typing import List, Optional
from core_infrastructure import ShardedServiceBase

app = FastAPI(title="Search Service", version="2.0")
logger = logging.getLogger('search_service')

# Initialize service
search_service = ShardedServiceBase(service_name="SearchService")

# Shard configuration (Phase 6 + 7)
SHARD_CONFIG = {
    0: {
        'primary_host': 'postgres-primary-0',
        'port': 5432,
        'replica_hosts': ['postgres-replica-0-1', 'postgres-replica-0-2']
    },
    1: {
        'primary_host': 'postgres-primary-1',
        'port': 5432,
        'replica_hosts': ['postgres-replica-1-1', 'postgres-replica-1-2']
    },
    2: {
        'primary_host': 'postgres-primary-2',
        'port': 5432,
        'replica_hosts': ['postgres-replica-2-1', 'postgres-replica-2-2']
    },
    3: {
        'primary_host': 'postgres-primary-3',
        'port': 5432,
        'replica_hosts': ['postgres-replica-3-1', 'postgres-replica-3-2']
    }
}


@app.on_event('startup')
async def startup():
    """Initialize service with all Phase 6+7 features"""
    await search_service.initialize(SHARD_CONFIG)
    logger.info("✅ Search Service started with Phase 6+7 features")


@app.on_event('shutdown')
async def shutdown():
    """Cleanup"""
    await search_service.shutdown()


# ============================================================================
# PHASE 6+7: SEARCH ENDPOINTS WITH ADVANCED FEATURES
# ============================================================================

@app.get('/search')
async def search(
    q: str,
    user_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Full-text search with caching and sharding
    Phase 6: Connection pooling, query optimization
    Phase 7: Cross-shard search aggregation
    """
    try:
        # Build cache key
        cache_key = f"search:{q}:{limit}:{offset}"

        # Try cache first
        cached = await search_service.cache.get(cache_key)
        if cached:
            return {
                'query': q,
                'results': cached,
                'from_cache': True,
                'count': len(cached)
            }

        # Cross-shard aggregation query
        query = """
            SELECT id, name, category, price, rating, match_score
            FROM products
            WHERE to_tsvector('english', name || ' ' || description) @@
                  plainto_tsquery('english', $1)
            ORDER BY match_score DESC, rating DESC
            LIMIT $2 OFFSET $3
        """

        results = await search_service.aggregation(query, (q, limit, offset))

        # Cache results (5 minute TTL)
        await search_service.cache.set(cache_key, results, ttl=300)

        return {
            'query': q,
            'results': results,
            'from_cache': False,
            'count': len(results)
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/semantic-search')
async def semantic_search(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 10
):
    """
    Semantic search using embeddings and vector index
    Phase 6: GIN index on embeddings, optimized queries
    Phase 7: Cross-shard vector search
    """
    try:
        cache_key = f"semantic:{query}:{limit}"
        cached = await search_service.cache.get(cache_key)
        if cached:
            return {
                'query': query,
                'results': cached,
                'from_cache': True
            }

        # Get query embedding (would use embedding service)
        query_embedding = await get_embedding(query)

        # Cross-shard vector search (Phase 7)
        query_sql = """
            SELECT id, name, category, price,
                   1 - (embedding <-> $1::vector) as similarity
            FROM product_embeddings
            WHERE embedding <-> $1::vector < 0.3
            ORDER BY similarity DESC
            LIMIT $2
        """

        results = await search_service.aggregation(
            query_sql,
            (str(query_embedding), limit)
        )

        await search_service.cache.set(cache_key, results, ttl=300)

        return {
            'query': query,
            'results': results,
            'search_type': 'semantic',
            'count': len(results)
        }

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/autocomplete')
async def autocomplete(q: str, limit: int = 10):
    """
    Autocomplete with trie index optimization
    Phase 6: Prefix index for fast matching
    Phase 7: Aggregated suggestions from all shards
    """
    try:
        cache_key = f"autocomplete:{q}"
        cached = await search_service.cache.get(cache_key)
        if cached:
            return {'suggestions': cached, 'from_cache': True}

        # Prefix matching using optimized index
        query = """
            SELECT DISTINCT name FROM products
            WHERE name ILIKE $1 || '%'
            ORDER BY popularity DESC
            LIMIT $2
        """

        results = await search_service.aggregation(query, (q, limit))
        await search_service.cache.set(cache_key, results, ttl=600)

        return {'suggestions': [r['name'] for r in results]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/faceted-search')
async def faceted_search(
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[float] = None,
    limit: int = 20
):
    """
    Faceted search with bitmap indexes
    Phase 6: Partial indexes for common filters
    Phase 7: Cross-shard aggregation with facet counts
    """
    try:
        cache_key = f"faceted:{category}:{price_min}:{price_max}:{rating_min}:{limit}"
        cached = await search_service.cache.get(cache_key)
        if cached:
            return cached

        # Build WHERE clause
        conditions = []
        params = []

        if category:
            conditions.append("category = $" + str(len(params) + 1))
            params.append(category)

        if price_min is not None:
            conditions.append("price >= $" + str(len(params) + 1))
            params.append(price_min)

        if price_max is not None:
            conditions.append("price <= $" + str(len(params) + 1))
            params.append(price_max)

        if rating_min is not None:
            conditions.append("rating >= $" + str(len(params) + 1))
            params.append(rating_min)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        query = f"""
            SELECT id, name, category, price, rating
            FROM products
            WHERE {where_clause}
            ORDER BY rating DESC
            LIMIT ${len(params)}
        """

        results = await search_service.aggregation(query, tuple(params))

        # Get facet counts
        facets = await get_facet_counts(category, price_min, price_max)

        response = {
            'results': results,
            'facets': facets,
            'total': len(results)
        }

        await search_service.cache.set(cache_key, response, ttl=600)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/trending')
async def get_trending(hours: int = 24, limit: int = 10):
    """
    Get trending products with materialized view
    Phase 6: Materialized view updated every 5 mins
    Phase 7: Aggregates across all shards
    """
    try:
        cache_key = f"trending:{hours}:{limit}"
        cached = await search_service.cache.get(cache_key)
        if cached:
            return {'trending': cached, 'from_cache': True}

        # Query materialized view (updated by Phase 6 background job)
        query = """
            SELECT product_id, name, views, purchases,
                   trend_score, category
            FROM mv_trending_products
            WHERE time_period >= NOW() - INTERVAL '1 hour' * $1
            ORDER BY trend_score DESC
            LIMIT $2
        """

        results = await search_service.aggregation(query, (hours, limit))
        await search_service.cache.set(cache_key, results, ttl=300)

        return {'trending': results, 'count': len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/add-search-tracking')
async def track_search(product_id: str, user_id: str, search_term: str):
    """
    Track search for analytics (Phase 7)
    Writes to user's shard for consistency
    """
    try:
        query = """
            INSERT INTO search_tracking (user_id, product_id, search_term, timestamp)
            VALUES ($1, $2, $3, NOW())
        """

        await search_service.write(user_id, query, (user_id, product_id, search_term))

        # Invalidate trending cache
        await search_service.cache.invalidate("trending:*")

        return {'status': 'tracked'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/search-stats')
async def get_search_stats():
    """Get service metrics (Phase 6)"""
    return search_service.get_metrics()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_embedding(text: str) -> List[float]:
    """Get text embedding (placeholder)"""
    # In production: call embedding service
    import numpy as np
    np.random.seed(hash(text) % 2**32)
    return np.random.rand(768).tolist()


async def get_facet_counts(category: Optional[str],
                          price_min: Optional[float],
                          price_max: Optional[float]) -> dict:
    """Get facet counts for filters"""
    return {
        'categories': [
            {'name': 'Electronics', 'count': 1250},
            {'name': 'Clothing', 'count': 2340},
            {'name': 'Books', 'count': 890}
        ],
        'price_ranges': [
            {'range': '0-50', 'count': 1200},
            {'range': '50-100', 'count': 1500},
            {'range': '100+', 'count': 2000}
        ],
        'ratings': [
            {'rating': '4+', 'count': 3500},
            {'rating': '3+', 'count': 4200}
        ]
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8010)
