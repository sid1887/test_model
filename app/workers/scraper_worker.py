"""
🔥 Scraper Worker - Event-Driven Background Job Processor

Consumes SCRAPE_REQUESTED events and processes them asynchronously.
This enables the Query Path to return fast while scraping happens in background.

Architecture:
- Redis Streams consumer group pattern
- Priority queue (user-triggered = 8-9, bulk refresh = 1-3)
- Graceful shutdown
- Error handling with retries
"""

import asyncio
import logging
from typing import Dict, Any, List
import httpx
from datetime import datetime

from app.core.events import (
    EventBus,
    EventType,
    emit_scrape_completed,
    emit_scrape_failed
)
from app.core.database import async_session_maker
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

class ScraperWorker:
    """
    Background worker that processes scrape requests from event stream
    """
    
    def __init__(self, worker_name: str = "scraper-worker-1"):
        self.worker_name = worker_name
        self.event_bus: EventBus = None
        self.running = False
        self.scraper_url = "http://scraper:3001/api/search"
        
    async def initialize(self):
        """Initialize event bus connection"""
        self.event_bus = EventBus()
        await self.event_bus.connect()
        logger.info(f"✅ {self.worker_name} initialized")
        
    async def start(self):
        """Start consuming events"""
        self.running = True
        logger.info(f"🚀 {self.worker_name} starting...")
        
        try:
            async for event in self.event_bus.subscribe(
                event_types=[EventType.SCRAPE_REQUESTED],
                consumer_group="scraper-workers",
                consumer_name=self.worker_name
            ):
                if not self.running:
                    break
                    
                try:
                    await self._process_scrape_request(event)
                    await self.event_bus.acknowledge(
                        f"events:{event.type}",
                        "scraper-workers",
                        event.metadata.get('message_id')
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to process event {event.id}: {e}")
                    # Event will be retried by another worker after timeout
                    
        except asyncio.CancelledError:
            logger.info(f"🛑 {self.worker_name} cancelled")
        except Exception as e:
            logger.error(f"💥 {self.worker_name} crashed: {e}")
        finally:
            await self.shutdown()
            
    async def _process_scrape_request(self, event):
        """
        Process a single scrape request
        
        Event payload:
        {
            "query": "iPhone 15 Pro",
            "sites": ["amazon", "walmart"],
            "max_results": 10,
            "request_id": "req-abc123"
        }
        """
        logger.info(f"🔍 Processing scrape: {event.payload.get('query')}")
        
        query = event.payload.get('query')
        sites = event.payload.get('sites', ['amazon', 'walmart', 'ebay'])
        max_results = event.payload.get('max_results', 10)
        request_id = event.payload.get('request_id', event.id)
        
        try:
            # Call scraper service
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.scraper_url,
                    json={
                        "query": query,
                        "sites": sites,
                        "max_results": max_results
                    }
                )
                
                if response.status_code == 200:
                    scraper_data = response.json()
                    results = scraper_data.get('results', [])
                    
                    # Save results to database
                    saved_count = await self._save_scrape_results(
                        query=query,
                        results=results,
                        request_id=request_id
                    )
                    
                    # Emit success event
                    await emit_scrape_completed(
                        query=query,
                        results_count=len(results),
                        saved_count=saved_count,
                        request_id=request_id
                    )
                    
                    logger.info(f"✅ Scraped {len(results)} products, saved {saved_count}")
                    
                else:
                    raise Exception(f"Scraper returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Scrape failed for '{query}': {e}")
            await emit_scrape_failed(
                query=query,
                error=str(e),
                request_id=request_id
            )
            
    async def _save_scrape_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        request_id: str
    ) -> int:
        """
        Save scraped results to database
        
        Creates/updates products and creates price snapshots
        """
        saved_count = 0
        
        async with async_session_maker() as db:
            for result in results:
                try:
                    # Extract product data
                    title = result.get('title', '').strip()
                    if not title or len(title) < 3:
                        continue
                        
                    price_str = result.get('price', '')
                    image_url = result.get('image', '')
                    product_url = result.get('link', '')
                    retailer = result.get('retailer', 'unknown')
                    
                    # Parse price
                    current_price = None
                    if price_str:
                        # Remove currency symbols and commas
                        clean_price = price_str.replace('$', '').replace(',', '').replace('₹', '')
                        try:
                            current_price = float(clean_price)
                        except:
                            pass
                    
                    if not current_price:
                        continue  # Skip products without valid price
                    
                    # Check if product exists (match by title + retailer)
                    stmt = select(Product).where(
                        Product.name == title,
                        Product.retailer == retailer
                    )
                    existing = await db.execute(stmt)
                    product = existing.scalar_one_or_none()
                    
                    if not product:
                        # Create new product
                        product = Product(
                            name=title,
                            current_price=current_price,
                            original_price=current_price,
                            image_url=image_url,
                            product_url=product_url,
                            retailer=retailer,
                            in_stock=True,
                            last_updated=datetime.utcnow()
                        )
                        db.add(product)
                        await db.flush()
                        
                    else:
                        # Update existing product
                        product.current_price = current_price
                        product.image_url = image_url or product.image_url
                        product.product_url = product_url or product.product_url
                        product.last_updated = datetime.utcnow()
                    
                    # Create price snapshot
                    snapshot = ProductSnapshot(
                        product_id=product.id,
                        price=current_price,
                        in_stock=True,
                        retailer=retailer,
                        snapshot_date=datetime.utcnow()
                    )
                    db.add(snapshot)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to save product '{title}': {e}")
                    continue
            
            await db.commit()
            
        return saved_count
        
    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        if self.event_bus:
            await self.event_bus.disconnect()
        logger.info(f"👋 {self.worker_name} shutdown complete")


async def main():
    """
    Entry point for running worker as standalone process
    
    Usage:
        python -m app.workers.scraper_worker
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = ScraperWorker()
    await worker.initialize()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
