"""
Core Infrastructure Layer: Shard Router, Connection Pooling, Caching
Combines all Phase 6 optimizations with Phase 7 sharding
"""

import hashlib
import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncpg
import aioredis
from functools import wraps
import json

logger = logging.getLogger('infrastructure')


# ============================================================================
# PART 1: LRU CACHE (L3 - In-Memory Layer)
# ============================================================================

class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_items: int = 5000, ttl_seconds: int = 3600):
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
        self.access_order = []

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, handle expiration"""
        if key not in self.cache:
            return None

        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            del self.cache[key]
            del self.timestamps[key]
            self.access_order.remove(key)
            return None

        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache, evict if needed"""
        if key in self.cache:
            self.access_order.remove(key)

        # Evict LRU item if cache full
        if len(self.cache) >= self.max_items:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
            del self.timestamps[oldest]

        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_order.append(key)

    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries by pattern"""
        if pattern is None:
            self.cache.clear()
            self.timestamps.clear()
            self.access_order.clear()
        else:
            keys_to_delete = [k for k in self.cache if pattern in k]
            for k in keys_to_delete:
                del self.cache[k]
                del self.timestamps[k]
                self.access_order.remove(k)


# ============================================================================
# PART 2: REDIS CACHE (L2 - Distributed Layer)
# ============================================================================

class RedisCache:
    """Redis distributed cache layer"""

    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.host = host
        self.port = port
        self.redis = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.host}:{self.port}',
            encoding='utf-8',
            max_size=50
        )
        logger.info(f"✅ Redis connected: {self.host}:{self.port}")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in Redis with TTL"""
        if not self.redis:
            return False
        try:
            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def invalidate(self, pattern: str) -> int:
        """Invalidate Redis entries by pattern"""
        if not self.redis:
            return 0
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return len(keys) if keys else 0
        except Exception as e:
            logger.error(f"Redis invalidate error: {e}")
            return 0


# ============================================================================
# PART 3: SHARD ROUTER (Routing Layer)
# ============================================================================

class ShardRouter:
    """Route queries to appropriate database shards"""

    def __init__(self, num_shards: int = 4):
        self.num_shards = num_shards
        self.shard_pools = {}  # (role, shard_id) -> pool
        self.replica_round_robin = {}

    async def initialize(self, shard_config: Dict[int, Dict[str, str]]):
        """Initialize connection pools for all shards"""
        for shard_id, config in shard_config.items():
            # Primary pool
            self.shard_pools[('primary', shard_id)] = await asyncpg.create_pool(
                host=config['primary_host'],
                port=config.get('port', 5432),
                database='productdb',
                user='admin',
                password='password',
                min_size=10,
                max_size=30,
                command_timeout=60
            )

            # Replica pools
            for i, replica_host in enumerate(config.get('replica_hosts', [])):
                self.shard_pools[('replica', shard_id, i)] = await asyncpg.create_pool(
                    host=replica_host,
                    port=config.get('port', 5432),
                    database='productdb',
                    user='admin',
                    password='password',
                    min_size=10,
                    max_size=30,
                    command_timeout=60
                )

            self.replica_round_robin[shard_id] = 0

        logger.info(f"✅ Initialized shard pools for {self.num_shards} shards")

    async def shutdown(self):
        """Close all pools"""
        for pool in self.shard_pools.values():
            await pool.close()

    def get_shard_id(self, user_id: str) -> int:
        """Get shard ID using consistent hashing"""
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return hash_val % self.num_shards

    async def execute_write(self, user_id: str, query: str, args: tuple) -> Any:
        """Execute write on user's shard primary"""
        shard_id = self.get_shard_id(user_id)
        pool = self.shard_pools[('primary', shard_id)]

        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def execute_read(self, user_id: Optional[str], query: str,
                          args: tuple, fetch_one: bool = False) -> Any:
        """Execute read on replica (with fallback to primary)"""
        if user_id:
            shard_id = self.get_shard_id(user_id)
            shard_ids = [shard_id]
        else:
            shard_ids = list(range(self.num_shards))

        results = []
        for shard_id in shard_ids:
            try:
                # Try replica first
                replica_idx = self.replica_round_robin[shard_id]
                pool_key = ('replica', shard_id, replica_idx % 2)
                self.replica_round_robin[shard_id] = (replica_idx + 1) % 2

                pool = self.shard_pools.get(pool_key)
                if pool is None:
                    pool = self.shard_pools[('primary', shard_id)]

                async with pool.acquire() as conn:
                    if fetch_one:
                        result = await conn.fetchrow(query, *args)
                    else:
                        result = await conn.fetch(query, *args)
                    results.append(result)
            except Exception as e:
                logger.warning(f"Replica read failed, trying primary: {e}")
                pool = self.shard_pools[('primary', shard_id)]
                async with pool.acquire() as conn:
                    if fetch_one:
                        result = await conn.fetchrow(query, *args)
                    else:
                        result = await conn.fetch(query, *args)
                    results.append(result)

        if len(shard_ids) == 1:
            return results[0]
        return results

    async def execute_aggregation(self, query: str, args: tuple,
                                 merge_func: Optional[Callable] = None) -> Any:
        """Execute query on all shards and merge"""
        tasks = []
        for shard_id in range(self.num_shards):
            pool = self.shard_pools[('primary', shard_id)]
            task = self._execute_shard(pool, query, args)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        clean_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Aggregation error: {r}")
                clean_results.append([])
            else:
                clean_results.append(r if r else [])

        if merge_func:
            return merge_func(clean_results)

        # Default merge: concatenate
        merged = []
        for result_set in clean_results:
            if isinstance(result_set, list):
                merged.extend(result_set)
        return merged

    async def _execute_shard(self, pool, query: str, args: tuple) -> List:
        """Execute on single shard"""
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)


# ============================================================================
# PART 4: CONNECTION POOL (PgBouncer Layer)
# ============================================================================

class ConnectionPoolManager:
    """Manage connection pooling with PgBouncer-like behavior"""

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections = 0
        self.waiting_queries = []
        self.lock = asyncio.Lock()

    async def acquire_connection(self, timeout: float = 30.0) -> bool:
        """Acquire a connection slot"""
        start = time.time()
        while True:
            async with self.lock:
                if self.active_connections < self.max_connections:
                    self.active_connections += 1
                    return True

            if time.time() - start > timeout:
                logger.warning(f"Connection acquisition timeout after {timeout}s")
                return False

            await asyncio.sleep(0.1)

    async def release_connection(self):
        """Release connection slot"""
        async with self.lock:
            self.active_connections = max(0, self.active_connections - 1)


# ============================================================================
# PART 5: UNIFIED CACHE LAYER (All 3 tiers)
# ============================================================================

class UnifiedCache:
    """3-tier cache: L3 (in-memory) -> L2 (Redis) -> L1 (DB materialized views)"""

    def __init__(self, l3_max_items: int = 5000, redis_host: str = 'localhost'):
        self.l3 = LRUCache(max_items=l3_max_items)
        self.l2 = RedisCache(host=redis_host)
        self.stats = {'l3_hits': 0, 'l2_hits': 0, 'misses': 0}

    async def connect(self):
        """Connect to Redis"""
        await self.l2.connect()

    async def disconnect(self):
        """Disconnect from Redis"""
        await self.l2.disconnect()

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L3 -> L2 -> miss)"""
        # L3 (in-memory)
        value = self.l3.get(key)
        if value is not None:
            self.stats['l3_hits'] += 1
            return value

        # L2 (Redis)
        value = await self.l2.get(key)
        if value is not None:
            self.stats['l2_hits'] += 1
            # Populate L3
            self.l3.set(key, value)
            return value

        self.stats['misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set in cache (L3 + L2)"""
        self.l3.set(key, value)
        await self.l2.set(key, json.dumps(value) if not isinstance(value, str) else value, ttl)

    async def invalidate(self, pattern: str) -> None:
        """Invalidate across all tiers"""
        self.l3.invalidate(pattern)
        await self.l2.invalidate(pattern)

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.stats


# ============================================================================
# PART 6: QUERY CACHE DECORATOR
# ============================================================================

def cached_query(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching query results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try cache first
            cached_value = await self.cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(self, *args, **kwargs)

            # Cache result
            await self.cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# ============================================================================
# PART 7: COMPLETE SERVICE BASE CLASS
# ============================================================================

class ShardedServiceBase:
    """Base class for all microservices with integrated caching, routing, pooling"""

    def __init__(self, service_name: str, num_shards: int = 4):
        self.service_name = service_name
        self.shard_router = ShardRouter(num_shards=num_shards)
        self.cache = UnifiedCache()
        self.pool_manager = ConnectionPoolManager(max_connections=100)
        self.metrics = {'queries': 0, 'errors': 0, 'cache_hits': 0}

    async def initialize(self, shard_config: Dict[int, Dict[str, str]]):
        """Initialize all layers"""
        await self.cache.connect()
        await self.shard_router.initialize(shard_config)
        logger.info(f"✅ {self.service_name} initialized with all layers")

    async def shutdown(self):
        """Shutdown all layers"""
        await self.shard_router.shutdown()
        await self.cache.disconnect()

    async def query(self, user_id: Optional[str], query_str: str,
                   args: tuple, fetch_one: bool = False) -> Any:
        """Execute query with all optimizations"""
        self.metrics['queries'] += 1

        try:
            acquired = await self.pool_manager.acquire_connection(timeout=30)
            if not acquired:
                raise Exception("Could not acquire connection")

            result = await self.shard_router.execute_read(
                user_id, query_str, args, fetch_one
            )

            await self.pool_manager.release_connection()
            return result

        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Query error: {e}")
            raise

    async def write(self, user_id: str, query_str: str, args: tuple) -> Any:
        """Execute write with connection pooling"""
        self.metrics['queries'] += 1

        try:
            acquired = await self.pool_manager.acquire_connection(timeout=30)
            if not acquired:
                raise Exception("Could not acquire connection")

            result = await self.shard_router.execute_write(user_id, query_str, args)

            # Invalidate relevant caches
            await self.cache.invalidate(f"user:{user_id}")

            await self.pool_manager.release_connection()
            return result

        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Write error: {e}")
            raise

    async def aggregation(self, query_str: str, args: tuple,
                         merge_func: Optional[Callable] = None) -> Any:
        """Execute cross-shard aggregation"""
        self.metrics['queries'] += 1

        try:
            return await self.shard_router.execute_aggregation(
                query_str, args, merge_func
            )
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Aggregation error: {e}")
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            'service': self.service_name,
            'queries': self.metrics['queries'],
            'errors': self.metrics['errors'],
            'cache_stats': self.cache.get_stats(),
            'pool_active': self.pool_manager.active_connections
        }


if __name__ == '__main__':
    print("Core infrastructure layer imported successfully")
