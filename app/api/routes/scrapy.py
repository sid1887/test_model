"""
Scrapy Service Integration Routes
Provides access to advanced scraping capabilities with 17+ retailers
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.services.scraping import scrapy_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scrapy", tags=["Scrapy Service"])


# Request/Response Models
class SearchRequest(BaseModel):
    """Product search request"""
    query: str
    retailers: Optional[List[str]] = None
    max_results: Optional[int] = 10


class BulkSearchRequest(BaseModel):
    """Bulk search request"""
    queries: List[str]
    retailers: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """Search response"""
    products: List[Dict[str, Any]]
    query: str
    total_products: int
    sites_searched: int
    successful_sites: int
    timestamp: str
    status: Optional[str] = None
    sites_queued: Optional[int] = None
    message: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields from Scrapy service


class BulkSearchResponse(BaseModel):
    """Bulk search response"""
    status: str
    batch_id: str
    jobs_queued: int
    queries_count: int
    retailers_count: int
    message: str
    timestamp: str


# Endpoints
@router.get("/health")
async def health_check():
    """
    Check Scrapy service health

    Returns service status and capabilities
    """
    try:
        await scrapy_client.initialize()

        if not scrapy_client.available:
            return {
                "status": "unavailable",
                "message": "Scrapy service is not available",
                "retailers_supported": 0
            }

        stats = await scrapy_client.get_stats()

        return {
            "status": "healthy",
            "message": "Scrapy service is operational",
            "retailers_supported": len(scrapy_client.supported_retailers),
            "retailers": scrapy_client.supported_retailers,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retailers")
async def get_supported_retailers():
    """
    Get list of supported retailers

    Returns all 17+ supported e-commerce platforms
    """
    try:
        await scrapy_client.initialize()

        return {
            "retailers": scrapy_client.supported_retailers,
            "total": len(scrapy_client.supported_retailers),
            "categories": {
                "major_us": ["amazon", "walmart", "target", "bestbuy", "ebay"],
                "home_improvement": ["homedepot", "lowes"],
                "department_stores": ["macys", "nordstrom", "costco"],
                "specialty": ["newegg", "bhphotovideo"],
                "furniture": ["wayfair", "overstock"],
                "fashion": ["zappos"],
                "international": ["flipkart", "aliexpress"]
            }
        }
    except Exception as e:
        logger.error(f"Get retailers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_products(request: SearchRequest):
    """
    Search for products across multiple retailers with caching

    - **query**: Search query (e.g., "laptop", "wireless headphones")
    - **retailers**: Optional list of retailer names (defaults to top 10)
    - **max_results**: Maximum results per retailer (default 10)

    Returns cached or fresh search results.
    """
    import time
    import json
    import redis

    try:
        # Initialize Redis with error handling
        try:
            r = redis.Redis(host='redis', port=6379, decode_responses=True)
            r.ping()  # Test connection
            redis_available = True
        except Exception as e:
            logger.warning(f"Redis unavailable - caching disabled: {e}")
            r = None
            redis_available = False

        # NORMALIZE INPUTS FOR CONSISTENT CACHE KEYS
        normalized_query = ' '.join(request.query.split()).lower().strip()
        normalized_retailers = ','.join(sorted([x.lower() for x in (request.retailers or [])]))
        cache_key = f"cache:search:{normalized_query}:{normalized_retailers}"

        logger.info(f"Search cache key: {cache_key}")

        # CHECK CACHE FIRST
        cache_hit = False
        if redis_available:
            try:
                cached_data = r.get(cache_key)
                if cached_data:
                    cached_result = json.loads(cached_data)
                    cache_age = time.time() - cached_result.get('timestamp', 0)

                    # 5-minute TTL
                    if cache_age < 300:
                        logger.info(f"✓ CACHE HIT for '{request.query}': age={cache_age:.1f}s")
                        cache_hit = True
                        return {
                            **cached_result['data'],
                            'cached': True,
                            'cache_age': cache_age,
                            'source': 'cache'
                        }
                    else:
                        logger.info(f"Cache expired (age={cache_age:.1f}s), fetching fresh")
            except Exception as e:
                logger.warning(f"Cache retrieval error: {e}")

        # EXECUTE SEARCH (not cached)
        logger.info(f"Executing fresh search for '{request.query}'")
        start_time = time.time()

        result = await scrapy_client.search(
            query=request.query,
            retailers=request.retailers,
            max_results=request.max_results
        )

        response_time = time.time() - start_time

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # STORE IN CACHE
        if redis_available and result and 'products' in result:
            try:
                cache_data = {
                    'data': result,
                    'timestamp': time.time(),
                    'query': request.query,
                    'retailers': request.retailers
                }
                r.setex(cache_key, 300, json.dumps(cache_data))
                logger.info(f"✓ Stored in cache: {cache_key} (TTL: 300s)")
            except Exception as e:
                logger.warning(f"Cache storage error: {e}")

        return {
            **result,
            'cached': False,
            'response_time': response_time,
            'source': 'scrapy',
            'cache_key': cache_key
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/voice")
async def voice_search(audio: UploadFile = File(...)):
    """
    Voice-based product search using speech-to-text

    - **audio**: Audio file (WAV, MP3, etc.)

    Transcribes audio to text and performs product search.
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = await scrapy_client.voice_search(tmp_path)

            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])

            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/image")
async def image_search(image: UploadFile = File(...)):
    """
    Image-based product search using CLIP analysis

    - **image**: Product image file (JPG, PNG, etc.)

    Analyzes image with CLIP and performs product search.
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = await scrapy_client.image_search(tmp_path)

            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])

            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/advanced")
async def advanced_search(
    query: str,
    retailers: Optional[List[str]] = None,
    min_price: float = 0,
    max_price: float = 999999,
    rank_by: str = 'price'
):
    """
    Advanced search with filtering and ranking

    - **query**: Search query
    - **retailers**: List of retailers (can be multiple)
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **rank_by**: Ranking method ('price', 'title', 'relevance')

    Searches multiple retailers, filters by price, and ranks results.
    """
    from app.utils.product_helpers import safe_extract_price, normalize_product

    try:
        all_products = []

        # Fetch from all retailers in parallel if multiple
        retailer_list = retailers or []
        logger.info(f"Advanced search: query='{query}', retailers={retailer_list}, price=${min_price}-${max_price}")

        for retailer in retailer_list:
            try:
                result = await scrapy_client.search(query, [retailer])
                products = result.get('products', [])

                # Normalize all products
                normalized = [normalize_product(p) for p in products]
                all_products.extend(normalized)
                logger.info(f"  {retailer}: {len(products)} products")
            except Exception as e:
                logger.warning(f"Error fetching from {retailer}: {e}")
                continue

        logger.info(f"Total products before filtering: {len(all_products)}")

        # SAFE FILTERING
        filtered = []
        for product in all_products:
            try:
                price = safe_extract_price(product)

                # Skip if no price extracted
                if price is None:
                    logger.debug(f"No price found for: {product.get('title', 'unknown')}")
                    continue

                # Filter by price range
                if min_price <= price <= max_price:
                    filtered.append(product)

            except Exception as e:
                logger.warning(f"Error filtering product: {e}")
                # Skip problematic product and continue
                continue

        logger.info(f"Total products after filtering: {len(filtered)}")

        # RANKING
        if rank_by == 'price':
            filtered.sort(key=lambda p: safe_extract_price(p) or float('inf'))
        elif rank_by == 'title':
            filtered.sort(key=lambda p: p.get('title', ''))
        # else: keep original order (relevance)

        return {
            'query': query,
            'retailers': retailer_list,
            'filters': {
                'price_min': min_price,
                'price_max': max_price,
                'rank_by': rank_by
            },
            'results': filtered,
            'total_found': len(all_products),
            'after_filtering': len(filtered),
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Advanced search error: {e}", exc_info=True)
        return {
            'error': str(e),
            'status': 'error',
            'results': []
        }


@router.post("/search/bulk", response_model=BulkSearchResponse)
async def bulk_search(request: BulkSearchRequest):
    """
    Bulk search across multiple queries and retailers

    - **queries**: List of search queries
    - **retailers**: Optional list of retailer names (defaults to all 17+)

    Creates a batch job for parallel processing. Use batch status endpoint to track progress.
    """
    try:
        result = await scrapy_client.bulk_search(
            queries=request.queries,
            retailers=request.retailers
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Get status of a bulk search batch

    - **batch_id**: Batch identifier from bulk search response

    Returns batch progress, completed jobs, and results count.
    """
    try:
        result = await scrapy_client.get_batch_status(batch_id)

        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail="Batch not found")
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    Get comprehensive Scrapy service statistics

    Returns scraping stats, retailer performance, and service health.
    """
    try:
        result = await scrapy_client.get_stats()

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
