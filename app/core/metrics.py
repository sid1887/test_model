"""
Prometheus Metrics Manager
Thread-safe singleton pattern for metrics with custom registry
"""

import threading
from typing import Optional
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from prometheus_client.multiprocess import MultiProcessCollector
import os


class MetricsManager:
    """
    Singleton metrics manager with lazy initialization
    Thread-safe metric creation with custom registry
    """
    _instance: Optional['MetricsManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._creation_lock = threading.Lock()
        
        # Check if running in multiprocess mode
        self.multiprocess_mode = os.getenv('PROMETHEUS_MULTIPROC_DIR') is not None
        
        if self.multiprocess_mode:
            # Use multiprocess registry
            self.registry = CollectorRegistry()
            MultiProcessCollector(self.registry)
        else:
            # Use custom registry for single process
            self.registry = CollectorRegistry()
        
        # Metrics cache
        self._metrics = {}
        
        # Initialize core metrics
        self._init_core_metrics()
    
    def _init_core_metrics(self):
        """Initialize core application metrics"""
        # HTTP Request metrics
        self._metrics['http_requests_total'] = Counter(
            'cumpair_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self._metrics['http_request_duration_seconds'] = Histogram(
            'cumpair_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Scraper metrics
        self._metrics['scraper_requests_total'] = Counter(
            'cumpair_scraper_requests_total',
            'Total scraper requests',
            ['retailer', 'status'],
            registry=self.registry
        )
        
        self._metrics['scraper_duration_seconds'] = Histogram(
            'cumpair_scraper_duration_seconds',
            'Scraper request duration',
            ['retailer'],
            registry=self.registry
        )
        
        self._metrics['scraper_products_found'] = Counter(
            'cumpair_scraper_products_found_total',
            'Total products found by scraper',
            ['retailer'],
            registry=self.registry
        )
        
        # Database metrics
        self._metrics['db_queries_total'] = Counter(
            'cumpair_db_queries_total',
            'Total database queries',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self._metrics['db_query_duration_seconds'] = Histogram(
            'cumpair_db_query_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            registry=self.registry
        )
        
        # Cache metrics
        self._metrics['cache_hits_total'] = Counter(
            'cumpair_cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self._metrics['cache_misses_total'] = Counter(
            'cumpair_cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # AI/ML metrics
        self._metrics['ai_requests_total'] = Counter(
            'cumpair_ai_requests_total',
            'Total AI/ML requests',
            ['model_type', 'status'],
            registry=self.registry
        )
        
        self._metrics['ai_processing_duration_seconds'] = Histogram(
            'cumpair_ai_processing_duration_seconds',
            'AI processing duration',
            ['model_type'],
            registry=self.registry
        )
        
        # Alert metrics
        self._metrics['alerts_fired_total'] = Counter(
            'cumpair_alerts_fired_total',
            'Total alerts fired',
            ['alert_type', 'channel'],
            registry=self.registry
        )
        
        self._metrics['alerts_active'] = Gauge(
            'cumpair_alerts_active',
            'Currently active alerts',
            ['alert_type'],
            registry=self.registry
        )
        
        # Notification metrics
        self._metrics['notifications_sent_total'] = Counter(
            'cumpair_notifications_sent_total',
            'Total notifications sent',
            ['channel', 'status'],
            registry=self.registry
        )
        
        # Worker metrics
        self._metrics['celery_tasks_total'] = Counter(
            'cumpair_celery_tasks_total',
            'Total Celery tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self._metrics['celery_task_duration_seconds'] = Histogram(
            'cumpair_celery_task_duration_seconds',
            'Celery task duration',
            ['task_name'],
            registry=self.registry
        )
        
        # System metrics
        self._metrics['active_connections'] = Gauge(
            'cumpair_active_connections',
            'Active WebSocket/SSE connections',
            ['connection_type'],
            registry=self.registry
        )
    
    def get_metric(self, name: str):
        """Get a metric by name (thread-safe)"""
        if name not in self._metrics:
            raise KeyError(f"Metric '{name}' not found. Available metrics: {list(self._metrics.keys())}")
        return self._metrics[name]
    
    def create_counter(self, name: str, description: str, labels: list = None):
        """Create a new counter metric (thread-safe)"""
        with self._creation_lock:
            if name in self._metrics:
                return self._metrics[name]
            
            full_name = f'cumpair_{name}' if not name.startswith('cumpair_') else name
            self._metrics[name] = Counter(
                full_name,
                description,
                labels or [],
                registry=self.registry
            )
            return self._metrics[name]
    
    def create_histogram(self, name: str, description: str, labels: list = None, buckets=None):
        """Create a new histogram metric (thread-safe)"""
        with self._creation_lock:
            if name in self._metrics:
                return self._metrics[name]
            
            full_name = f'cumpair_{name}' if not name.startswith('cumpair_') else name
            kwargs = {
                'name': full_name,
                'documentation': description,
                'labelnames': labels or [],
                'registry': self.registry
            }
            if buckets:
                kwargs['buckets'] = buckets
            
            self._metrics[name] = Histogram(**kwargs)
            return self._metrics[name]
    
    def create_gauge(self, name: str, description: str, labels: list = None):
        """Create a new gauge metric (thread-safe)"""
        with self._creation_lock:
            if name in self._metrics:
                return self._metrics[name]
            
            full_name = f'cumpair_{name}' if not name.startswith('cumpair_') else name
            self._metrics[name] = Gauge(
                full_name,
                description,
                labels or [],
                registry=self.registry
            )
            return self._metrics[name]
    
    def generate_latest(self):
        """Generate latest metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    def get_content_type(self):
        """Get content type for metrics endpoint"""
        return CONTENT_TYPE_LATEST


# Singleton instance getter
_metrics_manager = None
_manager_lock = threading.Lock()


def get_metrics_manager() -> MetricsManager:
    """
    Get the singleton MetricsManager instance
    Thread-safe lazy initialization
    """
    global _metrics_manager
    
    if _metrics_manager is None:
        with _manager_lock:
            if _metrics_manager is None:
                _metrics_manager = MetricsManager()
    
    return _metrics_manager


# Convenience functions for common metrics
def track_http_request(method: str, endpoint: str, status: int):
    """Track HTTP request"""
    manager = get_metrics_manager()
    manager.get_metric('http_requests_total').labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()


def track_http_duration(method: str, endpoint: str, duration: float):
    """Track HTTP request duration"""
    manager = get_metrics_manager()
    manager.get_metric('http_request_duration_seconds').labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_scraper_request(retailer: str, status: str):
    """Track scraper request"""
    manager = get_metrics_manager()
    manager.get_metric('scraper_requests_total').labels(
        retailer=retailer,
        status=status
    ).inc()


def track_alert_fired(alert_type: str, channel: str):
    """Track alert fired"""
    manager = get_metrics_manager()
    manager.get_metric('alerts_fired_total').labels(
        alert_type=alert_type,
        channel=channel
    ).inc()


def track_notification_sent(channel: str, status: str):
    """Track notification sent"""
    manager = get_metrics_manager()
    manager.get_metric('notifications_sent_total').labels(
        channel=channel,
        status=status
    ).inc()


def track_celery_task(task_name: str, status: str, duration: float = None):
    """Track Celery task execution"""
    manager = get_metrics_manager()
    manager.get_metric('celery_tasks_total').labels(
        task_name=task_name,
        status=status
    ).inc()
    
    if duration is not None:
        manager.get_metric('celery_task_duration_seconds').labels(
            task_name=task_name
        ).observe(duration)


def set_active_connections(connection_type: str, count: int):
    """Set active connections gauge"""
    manager = get_metrics_manager()
    manager.get_metric('active_connections').labels(
        connection_type=connection_type
    ).set(count)
