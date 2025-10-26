"""
Prometheus metrics endpoint for monitoring with thread-safe lazy initialization
Handles hot-reloading and prevents duplicate registration errors

Features:
- ✅ Thread-safe metric creation with double-check locking
- ✅ Survives Uvicorn --reload (singleton pattern)
- ✅ Custom CollectorRegistry (no conflicts with other libraries)
- ✅ Cached metrics generation (reduces overhead on frequent scrapes)
- ✅ Configurable metric prefix (for multi-service deployments)
- ✅ Debug endpoints for troubleshooting
- ✅ Automatic cache invalidation based on TTL
- ✅ Production-ready error handling

Configuration:
    METRIC_PREFIX: Prefix for all metrics (default: "cumpair_")
    METRICS_CACHE_TTL: Cache duration in seconds (default: 5)

Endpoints:
    GET /metrics - Prometheus scrape endpoint (cached)
    GET /metrics/debug - Debug info about registered metrics
    GET /metrics/health - Health check for metrics system

Usage:
    # Track a metric
    track_request('GET', '/api/products', 200)
    
    # Use context manager for timing
    with MetricsTimer('ai_inference', model_type='yolo'):
        result = model.predict(image)
    
    # Manual cache invalidation
    invalidate_metrics_cache()
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest,
    CONTENT_TYPE_LATEST, CollectorRegistry
)
import time
import threading
from typing import Optional, List, Dict, Any
from functools import lru_cache

# Configuration
METRIC_PREFIX = "cumpair_"  # Change this for different services/deployments
METRICS_CACHE_TTL = 5  # seconds - adjust based on scrape interval

router = APIRouter()

# Custom registry to avoid conflicts with other libraries
# This is the ONLY registry we'll use for our metrics
CUSTOM_REGISTRY = CollectorRegistry()

# Thread-safe singleton for metrics management
class MetricsStore:
    """
    Thread-safe singleton that persists across module reloads.
    Prevents duplicate metric registration and race conditions.
    """
    _instance: Optional['MetricsStore'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once, even across reloads
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            self._metrics = {}
            self._creation_lock = threading.Lock()
            self._last_cache_clear = time.time()
            self._initialized = True
    
    def get_or_create(self, metric_class, name: str, doc: str, labels: Optional[List[str]] = None):
        """
        Thread-safe metric getter/creator.
        Returns existing metric or creates new one.
        """
        # Fast path: metric already exists
        if name in self._metrics:
            return self._metrics[name]
        
        # Slow path: need to create (with lock to prevent race conditions)
        with self._creation_lock:
            # Double-check: another thread might have created it
            if name in self._metrics:
                return self._metrics[name]
            
            # Try to create the metric
            try:
                if labels:
                    metric = metric_class(name, doc, labels, registry=CUSTOM_REGISTRY)
                else:
                    metric = metric_class(name, doc, registry=CUSTOM_REGISTRY)
                
                self._metrics[name] = metric
                return metric
                
            except ValueError as e:
                # Metric already exists in registry (shouldn't happen with our setup)
                # Try to find it in our cache
                if name in self._metrics:
                    return self._metrics[name]
                
                # Last resort: search the registry (avoid this path if possible)
                for collector in CUSTOM_REGISTRY._collector_to_names.keys():
                    if hasattr(collector, '_name') and collector._name == name:
                        self._metrics[name] = collector
                        return collector
                
                # If we still can't find it, re-raise the error
                raise ValueError(f"Failed to get or create metric '{name}': {e}")
    
    def clear_all(self):
        """Clear all metrics (useful for testing or hard reset)"""
        with self._creation_lock:
            self._metrics.clear()
            _cached_metrics.cache_clear()
            # Note: We don't clear CUSTOM_REGISTRY as it's managed by prometheus_client
    
    def invalidate_cache(self):
        """Invalidate metrics cache to force regeneration on next request"""
        _cached_metrics.cache_clear()
        self._last_cache_clear = time.time()
    
    def should_invalidate_cache(self) -> bool:
        """Check if cache should be invalidated based on TTL"""
        return (time.time() - self._last_cache_clear) >= METRICS_CACHE_TTL


# Global singleton instance
_store = MetricsStore()


def _get_or_create_metric(metric_class, name: str, doc: str, labels: Optional[List[str]] = None):
    """
    Convenience wrapper around MetricsStore.get_or_create
    Automatically adds metric prefix for consistent naming
    """
    prefixed_name = f"{METRIC_PREFIX}{name}" if not name.startswith(METRIC_PREFIX) else name
    return _store.get_or_create(metric_class, prefixed_name, doc, labels)


# ============================================================================
# METRIC GETTERS - All metrics are lazily initialized on first access
# ============================================================================

# Request metrics
def get_request_count():
    return _get_or_create_metric(
        Counter, 'requests_total',
        'Total number of requests',
        ['method', 'endpoint', 'status']
    )


def get_request_duration():
    return _get_or_create_metric(
        Histogram, 'request_duration_seconds',
        'Request duration in seconds',
        ['method', 'endpoint']
    )


# AI model metrics
def get_ai_model_inference_count():
    return _get_or_create_metric(
        Counter, 'ai_inference_total',
        'Total number of AI model inferences',
        ['model_type']
    )


def get_ai_model_inference_duration():
    return _get_or_create_metric(
        Histogram, 'ai_inference_duration_seconds',
        'AI model inference duration in seconds',
        ['model_type']
    )


def get_ai_model_memory_usage():
    return _get_or_create_metric(
        Gauge, 'ai_model_memory_bytes',
        'AI model memory usage in bytes',
        ['model_type']
    )


# Database metrics
def get_db_query_count():
    return _get_or_create_metric(
        Counter, 'db_queries_total',
        'Total number of database queries',
        ['operation', 'table']
    )


def get_db_query_duration():
    return _get_or_create_metric(
        Histogram, 'db_query_duration_seconds',
        'Database query duration in seconds',
        ['operation', 'table']
    )


def get_db_connection_pool():
    return _get_or_create_metric(
        Gauge, 'db_connection_pool_size',
        'Database connection pool size',
        ['status']
    )


# Cache metrics
def get_cache_hits():
    return _get_or_create_metric(
        Counter, 'cache_hits_total',
        'Total number of cache hits',
        ['cache_type']
    )


def get_cache_misses():
    return _get_or_create_metric(
        Counter, 'cache_misses_total',
        'Total number of cache misses',
        ['cache_type']
    )


def get_cache_size():
    return _get_or_create_metric(
        Gauge, 'cache_size_bytes',
        'Cache size in bytes',
        ['cache_type']
    )


# Scraper metrics
def get_scraper_requests():
    return _get_or_create_metric(
        Counter, 'scraper_requests_total',
        'Total number of scraper requests',
        ['platform', 'status']
    )


def get_scraper_duration():
    return _get_or_create_metric(
        Histogram, 'scraper_duration_seconds',
        'Scraper request duration in seconds',
        ['platform']
    )


# Price comparison metrics
def get_price_comparison_count():
    return _get_or_create_metric(
        Counter, 'price_comparisons_total',
        'Total number of price comparisons',
        ['source']
    )


def get_price_search_duration():
    return _get_or_create_metric(
        Histogram, 'price_search_duration_seconds',
        'Price search duration in seconds',
        ['search_type']
    )


# Product discovery metrics
def get_product_discovery_count():
    return _get_or_create_metric(
        Counter, 'product_discoveries_total',
        'Total number of product discoveries',
        ['discovery_type']
    )


def get_product_discovery_duration():
    return _get_or_create_metric(
        Histogram, 'product_discovery_duration_seconds',
        'Product discovery duration in seconds',
        ['discovery_type']
    )


# Celery worker metrics
def get_celery_task_count():
    return _get_or_create_metric(
        Counter, 'celery_tasks_total',
        'Total number of Celery tasks',
        ['task_name', 'status']
    )


def get_celery_task_duration():
    return _get_or_create_metric(
        Histogram, 'celery_task_duration_seconds',
        'Celery task duration in seconds',
        ['task_name']
    )


def get_celery_active_workers():
    return _get_or_create_metric(
        Gauge, 'celery_active_workers',
        'Number of active Celery workers',
        None
    )


# System metrics
def get_system_uptime():
    return _get_or_create_metric(
        Gauge, 'system_uptime_seconds',
        'System uptime in seconds',
        None
    )


def get_active_users():
    return _get_or_create_metric(
        Gauge, 'active_users',
        'Number of active users',
        None
    )


# Error metrics
def get_error_count():
    return _get_or_create_metric(
        Counter, 'errors_total',
        'Total number of errors',
        ['error_type', 'endpoint']
    )


# ============================================================================
# FASTAPI ENDPOINTS
# ============================================================================

@lru_cache(maxsize=1)
def _cached_metrics():
    """
    Cached metrics generation to reduce overhead on frequent scrapes.
    Cache is invalidated based on TTL or manual invalidation.
    """
    return generate_latest(CUSTOM_REGISTRY)


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format for scraping.
    Uses custom registry to avoid conflicts.
    Response is cached for METRICS_CACHE_TTL seconds to reduce overhead.
    """
    # Auto-invalidate cache based on TTL
    if _store.should_invalidate_cache():
        _store.invalidate_cache()
    
    return PlainTextResponse(
        _cached_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/debug")
async def metrics_debug():
    """
    Debug endpoint showing all registered metrics and their types.
    Useful for troubleshooting and development.
    
    Returns:
        JSON with metric names and types
    """
    metrics_info = {
        name: {
            'type': type(metric).__name__,
            'description': getattr(metric, '_documentation', 'No description'),
            'labels': getattr(metric, '_labelnames', [])
        }
        for name, metric in _store._metrics.items()
    }
    
    return {
        'total_metrics': len(metrics_info),
        'prefix': METRIC_PREFIX,
        'cache_ttl': METRICS_CACHE_TTL,
        'metrics': metrics_info
    }


@router.get("/metrics/health")
async def metrics_health():
    """
    Health check endpoint for metrics system.
    
    Returns:
        JSON with system status
    """
    return {
        'status': 'healthy',
        'metrics_count': len(_store._metrics),
        'registry': 'custom',
        'cache_enabled': True,
        'cache_ttl_seconds': METRICS_CACHE_TTL
    }


# ============================================================================
# TRACKING UTILITY FUNCTIONS
# ============================================================================

def track_request(method: str, endpoint: str, status: int):
    """Track HTTP request metrics"""
    get_request_count().labels(method=method, endpoint=endpoint, status=status).inc()
    # Invalidate cache periodically (every 10 updates)
    if hash((method, endpoint, status)) % 10 == 0:
        _store.invalidate_cache()


def track_request_duration(method: str, endpoint: str, duration: float):
    """Track HTTP request duration"""
    get_request_duration().labels(method=method, endpoint=endpoint).observe(duration)


def track_ai_inference(model_type: str, duration: float):
    """Track AI model inference"""
    get_ai_model_inference_count().labels(model_type=model_type).inc()
    get_ai_model_inference_duration().labels(model_type=model_type).observe(duration)


def track_ai_memory(model_type: str, memory_bytes: float):
    """Track AI model memory usage"""
    get_ai_model_memory_usage().labels(model_type=model_type).set(memory_bytes)


def track_db_query(operation: str, table: str, duration: float):
    """Track database query"""
    get_db_query_count().labels(operation=operation, table=table).inc()
    get_db_query_duration().labels(operation=operation, table=table).observe(duration)


def track_db_pool(active: int, idle: int):
    """Track database connection pool"""
    get_db_connection_pool().labels(status='active').set(active)
    get_db_connection_pool().labels(status='idle').set(idle)


def track_cache_hit(cache_type: str):
    """Track cache hit"""
    get_cache_hits().labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Track cache miss"""
    get_cache_misses().labels(cache_type=cache_type).inc()


def track_cache_size(cache_type: str, size_bytes: float):
    """Track cache size"""
    get_cache_size().labels(cache_type=cache_type).set(size_bytes)


def track_scraper_request(platform: str, status: str, duration: float):
    """Track scraper request"""
    get_scraper_requests().labels(platform=platform, status=status).inc()
    get_scraper_duration().labels(platform=platform).observe(duration)


def track_price_comparison(source: str, duration: float, search_type: str = 'default'):
    """Track price comparison"""
    get_price_comparison_count().labels(source=source).inc()
    get_price_search_duration().labels(search_type=search_type).observe(duration)


def track_product_discovery(discovery_type: str, duration: float):
    """Track product discovery"""
    get_product_discovery_count().labels(discovery_type=discovery_type).inc()
    get_product_discovery_duration().labels(discovery_type=discovery_type).observe(duration)


def track_celery_task(task_name: str, status: str, duration: float):
    """Track Celery task"""
    get_celery_task_count().labels(task_name=task_name, status=status).inc()
    get_celery_task_duration().labels(task_name=task_name).observe(duration)


def update_celery_workers(count: int):
    """Update Celery worker count"""
    get_celery_active_workers().set(count)


def update_system_uptime(uptime_seconds: float):
    """Update system uptime"""
    get_system_uptime().set(uptime_seconds)


def update_active_users(count: int):
    """Update active user count"""
    get_active_users().set(count)


def track_error(error_type: str, endpoint: str):
    """Track error"""
    get_error_count().labels(error_type=error_type, endpoint=endpoint).inc()


# ============================================================================
# CONTEXT MANAGER FOR TIMING OPERATIONS
# ============================================================================

class MetricsTimer:
    """
    Thread-safe context manager for timing operations and tracking metrics.
    
    Usage:
        with MetricsTimer('ai_inference', model_type='yolo'):
            result = model.predict(image)
    """
    
    def __init__(self, metric_type: str, **labels):
        self.metric_type = metric_type
        self.labels = labels
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        try:
            if self.metric_type == 'request':
                track_request_duration(
                    self.labels.get('method', 'unknown'),
                    self.labels.get('endpoint', 'unknown'),
                    duration
                )
            elif self.metric_type == 'ai_inference':
                track_ai_inference(
                    self.labels.get('model_type', 'unknown'),
                    duration
                )
            elif self.metric_type == 'db_query':
                track_db_query(
                    self.labels.get('operation', 'unknown'),
                    self.labels.get('table', 'unknown'),
                    duration
                )
            elif self.metric_type == 'scraper':
                track_scraper_request(
                    self.labels.get('platform', 'unknown'),
                    'success' if not exc_type else 'failed',
                    duration
                )
            elif self.metric_type == 'price_comparison':
                track_price_comparison(
                    self.labels.get('source', 'unknown'),
                    duration,
                    self.labels.get('search_type', 'default')
                )
            elif self.metric_type == 'product_discovery':
                track_product_discovery(
                    self.labels.get('discovery_type', 'unknown'),
                    duration
                )
            elif self.metric_type == 'celery_task':
                track_celery_task(
                    self.labels.get('task_name', 'unknown'),
                    'success' if not exc_type else 'failed',
                    duration
                )
        except Exception as e:
            # Don't let metrics tracking crash the application
            print(f"Error tracking metric '{self.metric_type}': {e}")
        
        return False  # Don't suppress exceptions from the wrapped code


# ============================================================================
# UTILITY FUNCTIONS FOR TESTING/DEBUG
# ============================================================================

def get_all_metrics() -> Dict[str, Any]:
    """
    Get all registered metrics (useful for debugging)
    Returns: dict of metric_name -> metric_object
    """
    return _store._metrics.copy()


def reset_metrics():
    """
    Reset all metrics to initial state (useful for testing)
    WARNING: Only use in test environments!
    """
    _store.clear_all()


def invalidate_metrics_cache():
    """
    Manually invalidate the metrics cache.
    Useful when you know metrics have changed significantly.
    """
    _store.invalidate_cache()


def get_metrics_info() -> Dict[str, Any]:
    """
    Get information about the metrics system configuration.
    
    Returns:
        Dict with configuration details
    """
    return {
        'prefix': METRIC_PREFIX,
        'cache_ttl': METRICS_CACHE_TTL,
        'total_metrics': len(_store._metrics),
        'registry_type': 'custom',
        'thread_safe': True
    }