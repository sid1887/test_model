"""
Multi-Tier Cache Layer
L1: In-memory (local process)
L2: Redis (shared, fast)
L3: Database (persistent)

Implements cache-aside pattern with TTL and compression
"""

from typing import Optional, Any, Union, List
import json
import pickle
import zlib
from datetime import timedelta
from functools import wraps
import hashlib
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CacheLevel:
    L1 = "L1"  # In-memory
    L2 = "L2"  # Redis
    L3 = "L3"  # Database


class CacheManager:
    """Multi-tier caching system"""
    
    def __init__(self):
        self.l1_cache: dict = {}  # In-memory cache
        self.l2_client: Optional[redis.Redis] = None  # Redis
        self.compression_threshold = 1024  # Compress if > 1KB
        
    async def connect(self):
        """Initialize Redis connection for L2 cache"""
        if not self.l2_client:
            self.l2_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False  # Handle binary for compression
            )
            logger.info("L2 Cache (Redis) connected")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.l2_client:
            await self.l2_client.close()
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"cache:{namespace}:{key}"
    
    def _hash_key(self, key: str) -> str:
        """Hash long keys for efficiency"""
        if len(key) > 200:
            return hashlib.sha256(key.encode()).hexdigest()
        return key
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize and optionally compress value"""
        serialized = pickle.dumps(value)
        
        if len(serialized) > self.compression_threshold:
            compressed = zlib.compress(serialized)
            return b"COMPRESSED:" + compressed
        
        return serialized
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize and decompress if needed"""
        if data.startswith(b"COMPRESSED:"):
            decompressed = zlib.decompress(data[11:])
            return pickle.loads(decompressed)
        
        return pickle.loads(data)
    
    async def get(
        self,
        namespace: str,
        key: str,
        levels: List[str] = [CacheLevel.L1, CacheLevel.L2]
    ) -> Optional[Any]:
        """Get value from cache, checking multiple levels"""
        cache_key = self._make_key(namespace, self._hash_key(key))
        
        # L1: In-memory
        if CacheLevel.L1 in levels:
            if cache_key in self.l1_cache:
                logger.debug(f"L1 cache HIT: {namespace}:{key[:50]}")
                return self.l1_cache[cache_key]
        
        # L2: Redis
        if CacheLevel.L2 in levels:
            await self.connect()
            try:
                data = await self.l2_client.get(cache_key)
                if data:
                    value = self._deserialize(data)
                    
                    # Promote to L1
                    if CacheLevel.L1 in levels:
                        self.l1_cache[cache_key] = value
                    
                    logger.debug(f"L2 cache HIT: {namespace}:{key[:50]}")
                    return value
            except Exception as e:
                logger.error(f"L2 cache error: {e}")
        
        logger.debug(f"Cache MISS: {namespace}:{key[:50]}")
        return None
    
    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        levels: List[str] = [CacheLevel.L1, CacheLevel.L2]
    ):
        """Set value in cache at specified levels"""
        cache_key = self._make_key(namespace, self._hash_key(key))
        
        # L1: In-memory
        if CacheLevel.L1 in levels:
            self.l1_cache[cache_key] = value
        
        # L2: Redis
        if CacheLevel.L2 in levels:
            await self.connect()
            try:
                data = self._serialize(value)
                if ttl:
                    await self.l2_client.setex(cache_key, ttl, data)
                else:
                    await self.l2_client.set(cache_key, data)
                
                logger.debug(f"Cached at L2: {namespace}:{key[:50]} (TTL: {ttl})")
            except Exception as e:
                logger.error(f"L2 cache set error: {e}")
    
    async def delete(
        self,
        namespace: str,
        key: str,
        levels: List[str] = [CacheLevel.L1, CacheLevel.L2]
    ):
        """Delete value from cache"""
        cache_key = self._make_key(namespace, self._hash_key(key))
        
        if CacheLevel.L1 in levels:
            self.l1_cache.pop(cache_key, None)
        
        if CacheLevel.L2 in levels:
            await self.connect()
            try:
                await self.l2_client.delete(cache_key)
            except Exception as e:
                logger.error(f"L2 cache delete error: {e}")
    
    async def invalidate_pattern(self, namespace: str, pattern: str):
        """Invalidate all keys matching pattern"""
        await self.connect()
        try:
            search_pattern = f"cache:{namespace}:{pattern}"
            cursor = 0
            
            while True:
                cursor, keys = await self.l2_client.scan(
                    cursor, match=search_pattern, count=100
                )
                
                if keys:
                    await self.l2_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} keys matching {pattern}")
                
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
    
    def clear_l1(self):
        """Clear entire L1 cache"""
        self.l1_cache.clear()
        logger.info("L1 cache cleared")
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        await self.connect()
        
        info = await self.l2_client.info("stats")
        
        return {
            "l1_size": len(self.l1_cache),
            "l2_hits": info.get("keyspace_hits", 0),
            "l2_misses": info.get("keyspace_misses", 0),
            "l2_hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        }


# Global cache instance
cache_manager = CacheManager()


def cached(
    namespace: str,
    ttl: int = 3600,
    key_func=None,
    levels: List[str] = [CacheLevel.L1, CacheLevel.L2]
):
    """
    Decorator for caching function results
    
    Usage:
        @cached("products", ttl=300)
        async def get_product(product_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            cached_value = await cache_manager.get(namespace, cache_key, levels)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(namespace, cache_key, result, ttl, levels)
            
            return result
        
        return wrapper
    return decorator
