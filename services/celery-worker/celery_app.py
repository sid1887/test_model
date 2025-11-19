"""
Celery Application Factory
Initialize and configure Celery app
"""

from celery import Celery
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue
import os

# Import config
from celery_config import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CELERY_TASK_ROUTES,
    CELERY_QUEUES,
    CELERY_BEAT_SCHEDULE,
    CELERY_TASK_TRACK_STARTED,
    CELERY_TASK_TIME_LIMIT,
    CELERY_TASK_SOFT_TIME_LIMIT,
    CELERY_RESULT_EXPIRES,
    CELERY_TASK_AUTORETRY_FOR,
    CELERY_TASK_MAX_RETRIES,
    CELERY_TASK_DEFAULT_RETRY_DELAY,
)

# Create Celery app
app = Celery('scraper-tasks')

# Configure from object
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=CELERY_TASK_TRACK_STARTED,
    task_time_limit=CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=CELERY_TASK_SOFT_TIME_LIMIT,
    result_expires=CELERY_RESULT_EXPIRES,
    task_autoretry_for=CELERY_TASK_AUTORETRY_FOR,
    task_max_retries=CELERY_TASK_MAX_RETRIES,
    task_default_retry_delay=CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_routes=CELERY_TASK_ROUTES,
    task_queues=CELERY_QUEUES,
    beat_schedule=CELERY_BEAT_SCHEDULE,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10
)

# Task logger
logger = get_task_logger(__name__)

# Task events
app.conf.task_track_started = True
app.conf.task_send_sent_event = True
app.conf.worker_send_task_events = True

print("✅ Celery App Initialized")
print(f"  App Name: {app.main}")
print(f"  Broker: {app.conf.broker_url}")
print(f"  Backend: {app.conf.result_backend}")
