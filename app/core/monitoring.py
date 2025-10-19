"""
Monitoring and metrics setup using Prometheus
"""

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
except Exception:
    # Fallback shims when prometheus_client isn't available to avoid crashes
    class _Noop:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            return None
        def observe(self, *args, **kwargs):
            return None
    def Counter(*args, **kwargs):
        return _Noop()
    def Histogram(*args, **kwargs):
        return _Noop()
    def Gauge(*args, **kwargs):
        return _Noop()
    def generate_latest():
        return b""
from fastapi import FastAPI, Response
import time
import structlog
import sys
import os
from functools import wraps
from typing import Callable, Any

# Configure structured logging properly
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'cumpair_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'cumpair_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ANALYSIS_COUNT = Counter(
    'cumpair_analysis_total',
    'Total number of image analyses',
    ['status']
)

SCRAPING_COUNT = Counter(
    'cumpair_scraping_total',
    'Total number of scraping attempts',
    ['site', 'status']
)

ACTIVE_TASKS = Gauge(
    'cumpair_active_tasks',
    'Number of active Celery tasks'
)

# Setup structured logging
logger = structlog.get_logger()

def performance_timer(func: Callable) -> Callable:
    """Decorator to measure and log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} completed",
                duration_seconds=duration,
                function=func.__name__
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                duration_seconds=duration,
                function=func.__name__,
                error=str(e)
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} completed",
                duration_seconds=duration,
                function=func.__name__
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                duration_seconds=duration,
                function=func.__name__,
                error=str(e)
            )
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def setup_monitoring(app: FastAPI):
    """Setup monitoring middleware and endpoints"""
    
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        """Middleware to collect request metrics"""
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type="text/plain"
        )
    
    logger.info("Monitoring setup completed")
