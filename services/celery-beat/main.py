"""
Celery Beat Scheduler Service
Manages scheduled task execution
"""

import os
import logging
from datetime import datetime

from celery.beat import PersistentScheduler
from celery_app import app as celery_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CeleryBeatScheduler:
    """Celery Beat Scheduler Service"""

    def __init__(self):
        self.app = celery_app
        self.scheduler = None
        self.logger = logger

    def start(self):
        """Start the beat scheduler"""
        try:
            self.logger.info("="*60)
            self.logger.info("🎵 Starting Celery Beat Scheduler")
            self.logger.info("="*60)

            # Get scheduler from app
            self.scheduler = self.app.Beat()

            # Log scheduled tasks
            schedule = self.app.conf.beat_schedule or {}
            self.logger.info(f"📅 Scheduled Tasks: {len(schedule)}")

            for task_name, config in schedule.items():
                self.logger.info(f"   ✓ {task_name}")
                self.logger.info(f"     Task: {config.get('task')}")
                self.logger.info(f"     Schedule: {config.get('schedule')}")
                self.logger.info(f"     Args: {config.get('args', [])}")
                self.logger.info(f"     Kwargs: {config.get('kwargs', {})}")

            self.logger.info("="*60)
            self.logger.info("✅ Beat Scheduler Ready")
            self.logger.info("="*60 + "\n")

            # Start scheduler
            self.scheduler.run()

        except Exception as e:
            self.logger.error(f"❌ Beat Scheduler Error: {e}")
            raise

    def stop(self):
        """Stop the beat scheduler"""
        try:
            self.logger.info("Stopping Beat Scheduler...")
            if self.scheduler:
                self.scheduler.stop()
            self.logger.info("✅ Beat Scheduler Stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")

if __name__ == "__main__":
    import signal

    scheduler = CeleryBeatScheduler()

    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal")
        scheduler.stop()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    scheduler.start()
