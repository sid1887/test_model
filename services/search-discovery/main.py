"""
Search & Discovery Service
Full-text + Semantic CLIP Search with Advanced Filtering
Port: 8010
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncpg
import numpy as np
from redis import asyncio as aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Search & Discovery Service",
    description="Full-text and semantic CLIP search with advanced filtering",
    version="1.0.0"
)

# Database config
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "admin",
    "password": "password",
    "database": "productdb"
}

REDIS_URL = "redis://redis:6379/2"

# ============================================================================
# DATA MODELS
# ============================================================================

class SearchType(str, Enum):
    """Search type enumeration"""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    IMAGE = "image"

class SortBy(str, Enum):
    """Sort options"""
    RELEVANCE = "relevance"
    PRICE_LOW = "price_low"
    PRICE_HIGH = "price_high"
    RATING = "rating"
    NEWEST = "newest"
    POPULARITY = "popularity"

class SearchRequest(BaseModel):
    """Full-text search request"""
    query: str
    search_type: SearchType = SearchType.HYBRID
    filters: Optional[Dict[str, Any]] = {}
    sort_by: SortBy = SortBy.RELEVANCE
    page: int = 1
    limit: int = 20
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    retailer: Optional[str] = None

class ImageSearchRequest(BaseModel):
    """Image-based semantic search"""
    image_url: str
    image_embedding: Optional[List[float]] = None
    limit: int = 20
    threshold: float = 0.7

class SearchResult(BaseModel):
    """Individual search result"""
    product_id: str
    title: str
    price: float
    rating: float
    reviews_count: int
    image_url: str
    retailer: str
    relevance_score: float
    category: str

class SearchResponse(BaseModel):
    """Search response"""
    query: str
    search_type: SearchType
    total_results: int
    page: int
    limit: int
    results: List[SearchResult]
    facets: Optional[Dict[str, Any]] = {}
    execution_time_ms: float
    timestamp: str

class SearchHistory(BaseModel):
    """Search history item"""
    query: str
    search_type: SearchType
    result_count: int
    timestamp: str
    user_id: Optional[str] = None

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def get_db_pool():
    """Get database connection pool"""
    return await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)

async def get_redis_client():
    """Get Redis client"""
    return await aioredis.from_url(REDIS_URL)

# ============================================================================
# FULL-TEXT SEARCH ENDPOINTS
# ============================================================================

@app.post("/search/full-text", response_model=SearchResponse)
async def full_text_search(request: SearchRequest):
    """
    Full-text search with PostgreSQL FTS

    Features:
    - Full-text indexing via PostgreSQL tsvector
    - Price range filtering
    - Category filtering
    - Retailer filtering
    - Sorting options
    - Pagination
    """
    try:
        start_time = datetime.utcnow()

        logger.info(f"🔍 Full-text search: {request.query}")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Build dynamic WHERE clause
            where_clauses = []
            params = [request.query]
            param_count = 1

            # FTS search
            where_clauses.append(f"to_tsvector('english', title || ' ' || description) @@ plainto_tsquery('english', $1)")

            # Price filter
            if request.min_price is not None:
                param_count += 1
                where_clauses.append(f"price >= ${param_count}")
                params.append(request.min_price)

            if request.max_price is not None:
                param_count += 1
                where_clauses.append(f"price <= ${param_count}")
                params.append(request.max_price)

            # Category filter
            if request.category:
                param_count += 1
                where_clauses.append(f"category = ${param_count}")
                params.append(request.category)

            # Retailer filter
            if request.retailer:
                param_count += 1
                where_clauses.append(f"retailer = ${param_count}")
                params.append(request.retailer)

            where_clause = " AND ".join(where_clauses)

            # Sort clause
            sort_map = {
                SortBy.PRICE_LOW: "price ASC",
                SortBy.PRICE_HIGH: "price DESC",
                SortBy.RATING: "rating DESC",
                SortBy.NEWEST: "created_at DESC",
                SortBy.POPULARITY: "reviews_count DESC",
                SortBy.RELEVANCE: "ts_rank(to_tsvector('english', title || ' ' || description), plainto_tsquery('english', $1)) DESC"
            }
            sort_clause = sort_map.get(request.sort_by, sort_map[SortBy.RELEVANCE])

            # Total count
            count_query = f"SELECT COUNT(*) as total FROM products WHERE {where_clause}"
            total_result = await conn.fetchval(count_query, *params)
            total_results = total_result or 0

            # Paginated results
            offset = (request.page - 1) * request.limit
            query = f"""
                SELECT
                    id, title, price, rating, reviews_count, image_url, retailer, category,
                    ts_rank(to_tsvector('english', title || ' ' || description), plainto_tsquery('english', $1)) as relevance
                FROM products
                WHERE {where_clause}
                ORDER BY {sort_clause}
                LIMIT ${ param_count + 1} OFFSET ${param_count + 2}
            """

            rows = await conn.fetch(query, *params, request.limit, offset)

        await pool.close()

        # Format results
        results = [
            SearchResult(
                product_id=str(row['id']),
                title=row['title'],
                price=float(row['price']),
                rating=float(row['rating'] or 0),
                reviews_count=int(row['reviews_count'] or 0),
                image_url=row['image_url'] or "",
                retailer=row['retailer'],
                relevance_score=float(row['relevance'] or 0),
                category=row['category']
            )
            for row in rows
        ]

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"✅ Found {len(results)} results in {execution_time:.2f}ms")

        return SearchResponse(
            query=request.query,
            search_type=SearchType.FULL_TEXT,
            total_results=total_results,
            page=request.page,
            limit=request.limit,
            results=results,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Full-text search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SEMANTIC CLIP SEARCH ENDPOINTS
# ============================================================================

@app.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Semantic search using CLIP embeddings

    Features:
    - Vector similarity search via pgvector
    - Top-k nearest neighbors
    - Relevance threshold
    - Filtering options
    - Pagination
    """
    try:
        start_time = datetime.utcnow()

        logger.info(f"🧠 Semantic search: {request.query}")

        # Get CLIP embedding for query
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer('clip-ViT-B-32')
        query_embedding = model.encode(request.query, convert_to_tensor=True)
        query_vector = query_embedding.cpu().numpy().tolist()

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Build filters
            where_clauses = []
            params = [query_vector]
            param_count = 1

            if request.category:
                param_count += 1
                where_clauses.append(f"category = ${param_count}")
                params.append(request.category)

            if request.min_price is not None:
                param_count += 1
                where_clauses.append(f"price >= ${param_count}")
                params.append(request.min_price)

            if request.max_price is not None:
                param_count += 1
                where_clauses.append(f"price <= ${param_count}")
                params.append(request.max_price)

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Vector similarity search
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count

            query = f"""
                SELECT
                    id, title, price, rating, reviews_count, image_url, retailer, category,
                    1 - (embedding <-> $1::vector) as similarity
                FROM product_embeddings
                WHERE {where_clause} AND (1 - (embedding <-> $1::vector)) > 0.5
                ORDER BY similarity DESC
                LIMIT ${limit_param} OFFSET ${offset_param}
            """

            offset = (request.page - 1) * request.limit
            rows = await conn.fetch(query, *params, request.limit, offset)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total FROM product_embeddings
                WHERE {where_clause} AND (1 - (embedding <-> $1::vector)) > 0.5
            """
            total_result = await conn.fetchval(count_query, *params)
            total_results = total_result or 0

        await pool.close()

        # Format results
        results = [
            SearchResult(
                product_id=str(row['id']),
                title=row['title'],
                price=float(row['price']),
                rating=float(row['rating'] or 0),
                reviews_count=int(row['reviews_count'] or 0),
                image_url=row['image_url'] or "",
                retailer=row['retailer'],
                relevance_score=float(row['similarity']),
                category=row['category']
            )
            for row in rows
        ]

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"✅ Found {len(results)} semantic results in {execution_time:.2f}ms")

        return SearchResponse(
            query=request.query,
            search_type=SearchType.SEMANTIC,
            total_results=total_results,
            page=request.page,
            limit=request.limit,
            results=results,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HYBRID SEARCH (FULL-TEXT + SEMANTIC)
# ============================================================================

@app.post("/search/hybrid")
async def hybrid_search(request: SearchRequest):
    """
    Hybrid search combining full-text and semantic

    Features:
    - Dual indexing (FTS + vectors)
    - Result fusion (RRF - Reciprocal Rank Fusion)
    - Combined ranking
    - Best of both worlds
    """
    try:
        start_time = datetime.utcnow()

        logger.info(f"🔀 Hybrid search: {request.query}")

        # Run both searches in parallel
        text_task = full_text_search(request)
        semantic_request = SearchRequest(
            query=request.query,
            search_type=SearchType.SEMANTIC,
            filters=request.filters,
            page=1,
            limit=100  # Get more results for fusion
        )
        semantic_task = semantic_search(semantic_request)

        text_results, semantic_results = await asyncio.gather(text_task, semantic_task)

        # Fuse results using RRF
        result_scores = {}

        for rank, result in enumerate(text_results.results, 1):
            key = result.product_id
            result_scores[key] = result_scores.get(key, 0) + 1 / (60 + rank)

        for rank, result in enumerate(semantic_results.results, 1):
            key = result.product_id
            result_scores[key] = result_scores.get(key, 0) + 1 / (60 + rank)

        # Sort by fusion score
        sorted_results = sorted(result_scores.items(), key=lambda x: x[1], reverse=True)

        # Get top results with limit and pagination
        offset = (request.page - 1) * request.limit
        fused_product_ids = [pid for pid, _ in sorted_results[offset:offset + request.limit]]

        # Merge and deduplicate
        all_results = {}
        for result in text_results.results + semantic_results.results:
            if result.product_id not in all_results:
                all_results[result.product_id] = result

        final_results = [all_results[pid] for pid in fused_product_ids if pid in all_results]

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"✅ Hybrid search: {len(final_results)} fused results in {execution_time:.2f}ms")

        return SearchResponse(
            query=request.query,
            search_type=SearchType.HYBRID,
            total_results=len(sorted_results),
            page=request.page,
            limit=request.limit,
            results=final_results,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# IMAGE SEARCH ENDPOINTS
# ============================================================================

@app.post("/search/image")
async def image_search(request: ImageSearchRequest):
    """
    Search by image using CLIP embeddings

    Features:
    - Image URL to embedding
    - Vector similarity
    - Visual duplicate detection
    - Similar product recommendations
    """
    try:
        start_time = datetime.utcnow()

        logger.info(f"🖼️ Image search: {request.image_url[:50]}...")

        # Get image embedding
        if request.image_embedding is None:
            from PIL import Image
            import requests
            from io import BytesIO
            from sentence_transformers import SentenceTransformer

            response = requests.get(request.image_url, timeout=10)
            image = Image.open(BytesIO(response.content))

            model = SentenceTransformer('clip-ViT-B-32')
            embedding = model.encode(image, convert_to_tensor=True)
            image_vector = embedding.cpu().numpy().tolist()
        else:
            image_vector = request.image_embedding

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            query = """
                SELECT
                    id, title, price, rating, reviews_count, image_url, retailer, category,
                    1 - (image_embedding <-> $1::vector) as similarity
                FROM product_embeddings
                WHERE (1 - (image_embedding <-> $1::vector)) > $2
                ORDER BY similarity DESC
                LIMIT $3
            """

            rows = await conn.fetch(query, image_vector, request.threshold, request.limit)

        await pool.close()

        # Format results
        results = [
            SearchResult(
                product_id=str(row['id']),
                title=row['title'],
                price=float(row['price']),
                rating=float(row['rating'] or 0),
                reviews_count=int(row['reviews_count'] or 0),
                image_url=row['image_url'] or "",
                retailer=row['retailer'],
                relevance_score=float(row['similarity']),
                category=row['category']
            )
            for row in rows
        ]

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"✅ Image search: {len(results)} similar products in {execution_time:.2f}ms")

        return SearchResponse(
            query="[Image Search]",
            search_type=SearchType.IMAGE,
            total_results=len(results),
            page=1,
            limit=request.limit,
            results=results,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SEARCH HISTORY ENDPOINTS
# ============================================================================

@app.post("/search/history/add")
async def add_search_history(user_id: str, search: SearchHistory):
    """Add search to user history"""
    try:
        redis = await get_redis_client()

        history_key = f"search_history:{user_id}"
        await redis.lpush(history_key, search.json())
        await redis.ltrim(history_key, 0, 99)  # Keep last 100
        await redis.expire(history_key, 86400 * 30)  # 30 days

        await redis.close()

        logger.info(f"📝 Added search history for {user_id}: {search.query}")

        return {"status": "added", "user_id": user_id}

    except Exception as e:
        logger.error(f"Search history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/history/{user_id}")
async def get_search_history(user_id: str, limit: int = 50):
    """Get user search history"""
    try:
        redis = await get_redis_client()

        history_key = f"search_history:{user_id}"
        history = await redis.lrange(history_key, 0, limit - 1)

        await redis.close()

        import json
        parsed_history = [json.loads(h) for h in history]

        logger.info(f"📚 Retrieved {len(parsed_history)} searches for {user_id}")

        return {
            "user_id": user_id,
            "count": len(parsed_history),
            "history": parsed_history
        }

    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/trending")
async def get_trending_searches(limit: int = 20):
    """Get trending searches globally"""
    try:
        redis = await get_redis_client()

        trending = await redis.zrevrange("trending_searches", 0, limit - 1, withscores=True)

        await redis.close()

        results = [
            {"query": query.decode() if isinstance(query, bytes) else query, "count": int(count)}
            for query, count in trending
        ]

        logger.info(f"📈 Retrieved {len(results)} trending searches")

        return {"count": len(results), "trending": results}

    except Exception as e:
        logger.error(f"Trending searches error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/trending/update")
async def update_trending(query: str):
    """Update trending search counter"""
    try:
        redis = await get_redis_client()

        await redis.zincrby("trending_searches", 1, query)
        await redis.expire("trending_searches", 86400 * 7)  # 7 days

        await redis.close()

        return {"status": "updated", "query": query}

    except Exception as e:
        logger.error(f"Update trending error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADVANCED FILTERING ENDPOINTS
# ============================================================================

@app.get("/search/facets")
async def get_facets(category: Optional[str] = None):
    """
    Get search facets (categories, price ranges, retailers)

    For dynamic filtering UI
    """
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Categories
            categories = await conn.fetch("""
                SELECT DISTINCT category, COUNT(*) as count
                FROM products
                GROUP BY category
                ORDER BY count DESC
            """)

            # Price ranges
            price_ranges = await conn.fetch("""
                SELECT
                    CASE
                        WHEN price < 100 THEN 'Under $100'
                        WHEN price < 500 THEN '$100-$500'
                        WHEN price < 1000 THEN '$500-$1000'
                        ELSE 'Over $1000'
                    END as range,
                    COUNT(*) as count
                FROM products
                GROUP BY range
            """)

            # Retailers
            retailers = await conn.fetch("""
                SELECT DISTINCT retailer, COUNT(*) as count
                FROM products
                GROUP BY retailer
                ORDER BY count DESC
            """)

        await pool.close()

        facets = {
            "categories": [{"name": cat['category'], "count": cat['count']} for cat in categories],
            "price_ranges": [{"range": pr['range'], "count": pr['count']} for pr in price_ranges],
            "retailers": [{"name": ret['retailer'], "count": ret['count']} for ret in retailers]
        }

        logger.info(f"📊 Retrieved facets data")

        return facets

    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AUTOCOMPLETE ENDPOINTS
# ============================================================================

@app.get("/search/autocomplete")
async def search_autocomplete(q: str = Query(..., min_length=2)):
    """
    Search autocomplete suggestions

    Features:
    - Prefix matching
    - Trending terms
    - Previous searches
    - Top products
    """
    try:
        redis = await get_redis_client()
        pool = await get_db_pool()

        suggestions = set()

        # Trending searches
        trending = await redis.zrevrange("trending_searches", 0, 4)
        suggestions.update([t.decode() if isinstance(t, bytes) else t for t in trending if q.lower() in t.lower()])

        # Product title prefix matching
        async with pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT DISTINCT title
                FROM products
                WHERE lower(title) LIKE $1
                LIMIT 10
            """, q.lower() + "%")

            suggestions.update([p['title'] for p in products])

        await pool.close()
        await redis.close()

        return {
            "query": q,
            "suggestions": list(suggestions)[:10]
        }

    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Service health check"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await pool.close()

        redis = await get_redis_client()
        await redis.ping()
        await redis.close()

        return {
            "status": "healthy",
            "service": "search-discovery",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Search & Discovery",
        "version": "1.0.0",
        "port": 8010,
        "endpoints": {
            "health": "GET /health",
            "full_text_search": "POST /search/full-text",
            "semantic_search": "POST /search/semantic",
            "hybrid_search": "POST /search/hybrid",
            "image_search": "POST /search/image",
            "autocomplete": "GET /search/autocomplete",
            "trending": "GET /search/trending",
            "facets": "GET /search/facets",
            "history": "GET /search/history/{user_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn

    print(f"\n{'='*60}")
    print(f"🔍 Search & Discovery Service Starting")
    print(f"   Port: 8010")
    print(f"   Full-text + Semantic CLIP Search")
    print(f"   Hybrid ranking, autocomplete, trending")
    print(f"{'='*60}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        log_level="info"
    )
