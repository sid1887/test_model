"""
Monitoring and metrics setup using Prometheus
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
import time
import structlog
import sys
import os

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
