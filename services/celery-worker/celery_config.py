"""
Celery Configuration
Central configuration for Celery task queue and scheduler
"""

import os
from kombu import Exchange, Queue
from datetime import timedelta

# Broker & Backend
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

# Task Configuration
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Task Execution
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Result Settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_RESULT_PERSISTENT = True

# Retry Settings
CELERY_TASK_AUTORETRY_FOR = (Exception,)
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 60 seconds

# Task Routes (for different queues)
CELERY_TASK_ROUTES = {
    # High priority scraping tasks
    'tasks.scraping.scrape_retailer': {'queue': 'scraping', 'priority': 10},
    'tasks.scraping.batch_scrape': {'queue': 'scraping', 'priority': 10},

    # Data processing tasks
    'tasks.data.process_prices': {'queue': 'data', 'priority': 8},
    'tasks.data.deduplicate_products': {'queue': 'data', 'priority': 7},
    'tasks.data.normalize_data': {'queue': 'data', 'priority': 6},

    # ML/AI tasks (high resource)
    'tasks.ml.generate_embeddings': {'queue': 'ml', 'priority': 9},
    'tasks.ml.train_model': {'queue': 'ml', 'priority': 5},
    'tasks.ml.detect_duplicates': {'queue': 'ml', 'priority': 8},

    # Integration tasks
    'tasks.integration.fetch_news': {'queue': 'integration', 'priority': 7},
    'tasks.integration.fetch_crypto': {'queue': 'integration', 'priority': 7},
    'tasks.integration.fetch_stocks': {'queue': 'integration', 'priority': 7},

    # Notification tasks
    'tasks.notifications.send_email': {'queue': 'notifications', 'priority': 4},
    'tasks.notifications.send_sms': {'queue': 'notifications', 'priority': 4},
    'tasks.notifications.send_push': {'queue': 'notifications', 'priority': 4},
}

# Queue Configuration
CELERY_QUEUES = (
    Queue('scraping', Exchange('scraping'), routing_key='scraping', priority=10),
    Queue('data', Exchange('data'), routing_key='data', priority=8),
    Queue('ml', Exchange('ml'), routing_key='ml', priority=9),
    Queue('integration', Exchange('integration'), routing_key='integration', priority=7),
    Queue('notifications', Exchange('notifications'), routing_key='notifications', priority=4),
    Queue('default', Exchange('default'), routing_key='default', priority=5),
)

# Celery Beat Schedule (Scheduled Tasks)
CELERY_BEAT_SCHEDULE = {
    # Scraping Tasks
    'scrape-amazon-hourly': {
        'task': 'tasks.scraping.scrape_retailer',
        'schedule': timedelta(hours=1),
        'args': ('amazon',),
        'kwargs': {'priority': 10}
    },
    'scrape-flipkart-hourly': {
        'task': 'tasks.scraping.scrape_retailer',
        'schedule': timedelta(hours=1),
        'args': ('flipkart',),
        'kwargs': {'priority': 10}
    },
    'scrape-all-daily': {
        'task': 'tasks.scraping.batch_scrape',
        'schedule': timedelta(days=1),
        'kwargs': {'all_retailers': True}
    },

    # Data Processing
    'deduplicate-daily': {
        'task': 'tasks.data.deduplicate_products',
        'schedule': timedelta(days=1),
        'kwargs': {'use_ml': True, 'threshold': 0.85}
    },
    'normalize-data-daily': {
        'task': 'tasks.data.normalize_data',
        'schedule': timedelta(days=1),
    },

    # Integration Tasks
    'fetch-news-4h': {
        'task': 'tasks.integration.fetch_news',
        'schedule': timedelta(hours=4),
        'kwargs': {'page_size': 100}
    },
    'fetch-crypto-15m': {
        'task': 'tasks.integration.fetch_crypto',
        'schedule': timedelta(minutes=15),
    },
    'fetch-stocks-daily': {
        'task': 'tasks.integration.fetch_stocks',
        'schedule': timedelta(days=1),
        'kwargs': {'market_close': True}
    },

    # ML Tasks
    'generate-embeddings-daily': {
        'task': 'tasks.ml.generate_embeddings',
        'schedule': timedelta(days=1),
        'kwargs': {'model': 'clip'}
    },
    'rebuild-index-nightly': {
        'task': 'tasks.ml.rebuild_faiss_index',
        'schedule': timedelta(days=1, hours=2),  # 2 AM UTC
    },

    # Trend Analysis (Weekly)
    'analyze-trends-weekly': {
        'task': 'tasks.data.analyze_trends',
        'schedule': timedelta(weeks=1),
    },
}

# Worker Settings
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Event Settings
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Network Settings
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

print("✅ Celery Configuration Loaded")
print(f"  Broker: {CELERY_BROKER_URL}")
print(f"  Backend: {CELERY_RESULT_BACKEND}")
print(f"  Queues: {len(CELERY_QUEUES)}")
print(f"  Scheduled Tasks: {len(CELERY_BEAT_SCHEDULE)}")
