"""
🚀 Worker Manager - Run all background workers
Starts scraper worker and image AI worker in parallel
"""

import asyncio
import logging
import signal
from app.workers.scraper_worker import ScraperWorker
from app.workers.image_worker import ImageAIWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages multiple workers with graceful shutdown"""
    
    def __init__(self):
        self.workers = []
        self.running = False
        
    async def start_all(self):
        """Start all workers"""
        logger.info("🚀 Starting all workers...")
        
        # Create workers
        scraper_worker = ScraperWorker("scraper-worker-1")
        image_worker = ImageAIWorker("image-ai-worker-1")
        
        # Initialize
        await scraper_worker.initialize()
        await image_worker.initialize()
        
        self.workers = [scraper_worker, image_worker]
        self.running = True
        
        # Start all workers in parallel
        tasks = [
            asyncio.create_task(scraper_worker.start()),
            asyncio.create_task(image_worker.start())
        ]
        
        logger.info("✅ All workers started")
        
        # Wait for all to complete (or cancel)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("🛑 Workers cancelled")
            
    async def shutdown(self):
        """Gracefully shutdown all workers"""
        logger.info("🛑 Shutting down all workers...")
        
        for worker in self.workers:
            await worker.shutdown()
            
        logger.info("👋 All workers stopped")


async def main():
    """Main entry point"""
    manager = WorkerManager()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(manager.shutdown())
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await manager.start_all()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
