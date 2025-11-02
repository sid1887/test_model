"""
Query Optimizer - Index-First Search with <200ms target
Implements cache-first, FAISS vector search, ghost results pattern
"""

from typing import Dict, List, Optional, Any
import time
import asyncio
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.core.cache import cache_manager, CacheLevel
from app.core.metrics import metrics
from app.models.product import Product
from app.services.clip_search import clip_service
from app.services.huggingface_client import hf_client
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    High-performance query engine with multiple lookup strategies
    Target: <200ms for cached queries, <2s for fresh queries
    """
    
    def __init__(self):
        self.cache_ttl = {
            "hot": 300,      # 5 minutes for frequently accessed
            "warm": 3600,    # 1 hour for normal queries
            "cold": 86400    # 24 hours for rare queries
        }
    
    async def search_products(
        self,
        query: str,
        db: AsyncSession,
        limit: int = 20,
        use_cache: bool = True,
        use_vector_search: bool = True
    ) -> Dict[str, Any]:
        """
        Multi-strategy product search with performance tracking
        
        Strategy:
        1. Check L1/L2 cache (fastest)
        2. Check FAISS vector index (fast)
        3. Check database with optimized query (medium)
        4. Trigger background scraper refresh (slow, async)
        """
        start_time = time.time()
        
        # Step 1: Cache lookup
        if use_cache:
            cache_key = f"search:{query}:{limit}"
            cached_result = await cache_manager.get("products", cache_key)
            
            if cached_result:
                metrics.track_cache_hit("L2", "products")
                logger.info(f"Cache HIT for '{query}' ({time.time() - start_time:.3f}s)")
                
                return {
                    "results": cached_result["results"],
                    "metadata": {
                        **cached_result["metadata"],
                        "cache_hit": True,
                        "latency_ms": (time.time() - start_time) * 1000
                    }
                }
        
        metrics.track_cache_miss("L2", "products")
        
        # Step 2: Vector search (if enabled and CLIP available)
        vector_results = []
        if use_vector_search and clip_service.clip_model:
            try:
                # Compute query embedding
                query_embedding = await hf_client.compute_embeddings(query)
                
                # Search FAISS index
                vector_results = await self._faiss_search(query_embedding, limit)
                
                if vector_results:
                    logger.info(f"Vector search found {len(vector_results)} results")
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # Step 3: Database search (always run for fresh data)
        db_results = await self._database_search(query, db, limit)
        
        # Step 4: Merge results (vector + database)
        merged_results = self._merge_results(vector_results, db_results, limit)
        
        # Step 5: Check staleness and trigger refresh if needed
        stale_threshold = 3600  # 1 hour
        needs_refresh = await self._check_staleness(merged_results, stale_threshold)
        
        if needs_refresh:
            # Trigger background scraper (fire and forget)
            asyncio.create_task(self._trigger_scraper_refresh(query))
        
        # Step 6: Cache results
        latency_ms = (time.time() - start_time) * 1000
        
        result_data = {
            "results": merged_results,
            "metadata": {
                "total_results": len(merged_results),
                "cache_hit": False,
                "vector_search_used": len(vector_results) > 0,
                "latency_ms": latency_ms,
                "needs_refresh": needs_refresh
            }
        }
        
        # Determine cache tier based on latency
        cache_tier = "hot" if latency_ms < 100 else ("warm" if latency_ms < 500 else "cold")
        await cache_manager.set(
            "products",
            f"search:{query}:{limit}",
            result_data,
            ttl=self.cache_ttl[cache_tier]
        )
        
        logger.info(f"Search '{query}' completed in {latency_ms:.1f}ms ({cache_tier} tier)")
        
        return result_data
    
    async def _faiss_search(
        self,
        query_embedding: List[float],
        k: int = 20
    ) -> List[Dict[str, Any]]:
        """Search FAISS vector index"""
        try:
            # FAISS search using CLIP service
            results = await clip_service.search_by_embedding(
                np.array(query_embedding),
                top_k=k
            )
            
            return results
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []
    
    async def _database_search(
        self,
        query: str,
        db: AsyncSession,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Optimized database search with multiple strategies"""
        start_time = time.time()
        
        # Extract search terms
        terms = query.lower().split()
        
        # Build query with ranking
        stmt = select(Product).where(
            or_(
                *[Product.name.ilike(f"%{term}%") for term in terms],
                *[Product.brand.ilike(f"%{term}%") for term in terms] if terms else [],
                Product.category.ilike(f"%{query}%")
            )
        ).limit(limit)
        
        result = await db.execute(stmt)
        products = result.scalars().all()
        
        duration = time.time() - start_time
        metrics.track_db_query("search", "products", duration)
        
        return [self._product_to_dict(p) for p in products]
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        db_results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from multiple sources"""
        seen_ids = set()
        merged = []
        
        # Add vector results first (ranked by similarity)
        for result in vector_results:
            product_id = result.get("product_id") or result.get("id")
            if product_id not in seen_ids:
                seen_ids.add(product_id)
                merged.append(result)
        
        # Add database results
        for result in db_results:
            product_id = result.get("product_id") or result.get("id")
            if product_id not in seen_ids and len(merged) < limit:
                seen_ids.add(product_id)
                merged.append(result)
        
        return merged[:limit]
    
    async def _check_staleness(
        self,
        results: List[Dict[str, Any]],
        threshold: int
    ) -> bool:
        """Check if results need refresh"""
        if not results:
            return True
        
        # Check last_updated timestamp
        now = time.time()
        for result in results:
            last_updated = result.get("last_updated")
            if last_updated:
                # Convert to timestamp if datetime
                if hasattr(last_updated, "timestamp"):
                    last_updated = last_updated.timestamp()
                
                if now - last_updated > threshold:
                    return True
        
        return False
    
    async def _trigger_scraper_refresh(self, query: str):
        """Trigger background scraper to refresh data"""
        from app.core.events import emit_scrape_requested
        
        try:
            await emit_scrape_requested(
                query=query,
                sites=["amazon", "walmart", "ebay"],
                max_results=20,
                priority=3  # Low priority background job
            )
            logger.info(f"Triggered background refresh for '{query}'")
        except Exception as e:
            logger.error(f"Failed to trigger scraper: {e}")
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert Product model to dict"""
        return {
            "id": product.id,
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "current_price": product.current_price,
            "original_price": product.original_price,
            "image_url": product.image_url,
            "product_url": product.product_url,
            "retailer": product.retailer,
            "in_stock": product.in_stock,
            "last_updated": product.last_updated
        }
    
    async def get_ghost_results(
        self,
        query: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Return ghost/placeholder results instantly while real search runs
        Used for perceived <100ms UX
        """
        return [
            {
                "id": f"ghost_{i}",
                "name": f"Loading product {i+1}...",
                "brand": "...",
                "current_price": 0.0,
                "is_ghost": True
            }
            for i in range(count)
        ]


# Global optimizer instance
query_optimizer = QueryOptimizer()
