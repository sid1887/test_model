"""
Prometheus metrics endpoint for monitoring
"""

from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, 
    CONTENT_TYPE_LATEST, REGISTRY
)
import time
from datetime import datetime

router = APIRouter()

# Request metrics
request_count = Counter(
    'cumpair_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'cumpair_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# AI model metrics
ai_model_inference_count = Counter(
    'cumpair_ai_inference_total',
    'Total number of AI model inferences',
    ['model_type']
)

ai_model_inference_duration = Histogram(
    'cumpair_ai_inference_duration_seconds',
    'AI model inference duration in seconds',
    ['model_type']
)

ai_model_memory_usage = Gauge(
    'cumpair_ai_model_memory_bytes',
    'AI model memory usage in bytes',
    ['model_type']
)

# Database metrics
db_query_count = Counter(
    'cumpair_db_queries_total',
    'Total number of database queries',
    ['operation', 'table']
)

db_query_duration = Histogram(
    'cumpair_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

db_connection_pool = Gauge(
    'cumpair_db_connection_pool_size',
    'Database connection pool size',
    ['status']
)

# Cache metrics
cache_hits = Counter(
    'cumpair_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cumpair_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

cache_size = Gauge(
    'cumpair_cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)

# Scraper metrics
scraper_requests = Counter(
    'cumpair_scraper_requests_total',
    'Total number of scraper requests',
    ['platform', 'status']
)

scraper_duration = Histogram(
    'cumpair_scraper_duration_seconds',
    'Scraper request duration in seconds',
    ['platform']
)

# Price comparison metrics
price_comparison_count = Counter(
    'cumpair_price_comparisons_total',
    'Total number of price comparisons',
    ['source']
)

price_search_duration = Histogram(
    'cumpair_price_search_duration_seconds',
    'Price search duration in seconds',
    ['search_type']
)

# Product discovery metrics
product_discovery_count = Counter(
    'cumpair_product_discoveries_total',
    'Total number of product discoveries',
    ['discovery_type']
)

product_discovery_duration = Histogram(
    'cumpair_product_discovery_duration_seconds',
    'Product discovery duration in seconds',
    ['discovery_type']
)

# Celery worker metrics
celery_task_count = Counter(
    'cumpair_celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status']
)

celery_task_duration = Histogram(
    'cumpair_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name']
)

celery_active_workers = Gauge(
    'cumpair_celery_active_workers',
    'Number of active Celery workers'
)

# System metrics
system_uptime = Gauge(
    'cumpair_system_uptime_seconds',
    'System uptime in seconds'
)

active_users = Gauge(
    'cumpair_active_users',
    'Number of active users'
)

# Error metrics
error_count = Counter(
    'cumpair_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format for scraping
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

# Utility functions for tracking metrics
def track_request(method: str, endpoint: str, status: int):
    """Track HTTP request metrics"""
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()

def track_request_duration(method: str, endpoint: str, duration: float):
    """Track HTTP request duration"""
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def track_ai_inference(model_type: str, duration: float):
    """Track AI model inference"""
    ai_model_inference_count.labels(model_type=model_type).inc()
    ai_model_inference_duration.labels(model_type=model_type).observe(duration)

def track_ai_memory(model_type: str, memory_bytes: float):
    """Track AI model memory usage"""
    ai_model_memory_usage.labels(model_type=model_type).set(memory_bytes)

def track_db_query(operation: str, table: str, duration: float):
    """Track database query"""
    db_query_count.labels(operation=operation, table=table).inc()
    db_query_duration.labels(operation=operation, table=table).observe(duration)

def track_db_pool(active: int, idle: int):
    """Track database connection pool"""
    db_connection_pool.labels(status='active').set(active)
    db_connection_pool.labels(status='idle').set(idle)

def track_cache_hit(cache_type: str):
    """Track cache hit"""
    cache_hits.labels(cache_type=cache_type).inc()

def track_cache_miss(cache_type: str):
    """Track cache miss"""
    cache_misses.labels(cache_type=cache_type).inc()

def track_cache_size(cache_type: str, size_bytes: float):
    """Track cache size"""
    cache_size.labels(cache_type=cache_type).set(size_bytes)

def track_scraper_request(platform: str, status: str, duration: float):
    """Track scraper request"""
    scraper_requests.labels(platform=platform, status=status).inc()
    scraper_duration.labels(platform=platform).observe(duration)

def track_price_comparison(source: str, duration: float, search_type: str = 'default'):
    """Track price comparison"""
    price_comparison_count.labels(source=source).inc()
    price_search_duration.labels(search_type=search_type).observe(duration)

def track_product_discovery(discovery_type: str, duration: float):
    """Track product discovery"""
    product_discovery_count.labels(discovery_type=discovery_type).inc()
    product_discovery_duration.labels(discovery_type=discovery_type).observe(duration)

def track_celery_task(task_name: str, status: str, duration: float):
    """Track Celery task"""
    celery_task_count.labels(task_name=task_name, status=status).inc()
    celery_task_duration.labels(task_name=task_name).observe(duration)

def update_celery_workers(count: int):
    """Update Celery worker count"""
    celery_active_workers.set(count)

def update_system_uptime(uptime_seconds: float):
    """Update system uptime"""
    system_uptime.set(uptime_seconds)

def update_active_users(count: int):
    """Update active user count"""
    active_users.set(count)

def track_error(error_type: str, endpoint: str):
    """Track error"""
    error_count.labels(error_type=error_type, endpoint=endpoint).inc()

# Context manager for timing operations
class MetricsTimer:
    """Context manager for timing operations and tracking metrics"""
    
    def __init__(self, metric_type: str, **labels):
        self.metric_type = metric_type
        self.labels = labels
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
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
        
        return False  # Don't suppress exceptions

# Example usage:
# with MetricsTimer('ai_inference', model_type='yolo'):
#     result = model.predict(image)
