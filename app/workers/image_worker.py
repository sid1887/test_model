"""
🔥 Image AI Worker - Multi-Modal Product Detection

Consumes IMAGE_UPLOADED events and runs AI models:
- CLIP: Visual similarity search
- YOLO: Object detection
- ZBar: Barcode/QR detection
- OCR: Text extraction

Then emits PRODUCT_MATCHED or SCRAPE_REQUESTED events
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import os

from app.core.events import (
    EventBus,
    EventType,
    emit_product_matched,
    emit_scrape_requested,
    emit_barcode_detected
)
from app.core.database import async_session_maker
from app.models.product import Product
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ImageAIWorker:
    """
    Background worker for AI-powered image analysis
    """
    
    def __init__(self, worker_name: str = "image-ai-worker-1"):
        self.worker_name = worker_name
        self.event_bus: EventBus = None
        self.running = False
        
        # Lazy-loaded AI models
        self.clip_service = None
        self.image_processor = None
        
    async def initialize(self):
        """Initialize event bus and AI models"""
        self.event_bus = EventBus()
        await self.event_bus.connect()
        
        # Initialize AI models
        try:
            from app.services.clip_search import clip_service
            await clip_service.initialize()
            self.clip_service = clip_service
            logger.info("✅ CLIP model loaded")
        except Exception as e:
            logger.warning(f"⚠️ CLIP initialization failed: {e}")
            
        try:
            from app.services.image_processor import get_image_processor
            self.image_processor = await get_image_processor()
            logger.info("✅ Image processor loaded")
        except Exception as e:
            logger.warning(f"⚠️ Image processor initialization failed: {e}")
            
        logger.info(f"✅ {self.worker_name} initialized")
        
    async def start(self):
        """Start consuming IMAGE_UPLOADED events"""
        self.running = True
        logger.info(f"🚀 {self.worker_name} starting...")
        
        try:
            async for event in self.event_bus.subscribe(
                event_types=[EventType.IMAGE_UPLOADED],
                consumer_group="image-ai-workers",
                consumer_name=self.worker_name
            ):
                if not self.running:
                    break
                    
                try:
                    await self._process_image(event)
                    await self.event_bus.acknowledge(
                        f"events:{event.type}",
                        "image-ai-workers",
                        event.metadata.get('message_id')
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to process event {event.id}: {e}")
                    
        except asyncio.CancelledError:
            logger.info(f"🛑 {self.worker_name} cancelled")
        except Exception as e:
            logger.error(f"💥 {self.worker_name} crashed: {e}")
        finally:
            await self.shutdown()
            
    async def _process_image(self, event):
        """
        Process uploaded image with multiple AI models
        
        Event payload:
        {
            "image_id": "uuid",
            "file_path": "/uploads/...",
            "request_id": "img-search-abc123"
        }
        """
        image_id = event.payload.get('image_id')
        file_path = event.payload.get('file_path')
        request_id = event.payload.get('request_id', event.id)
        
        logger.info(f"🖼️ Processing image: {image_id}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ Image file not found: {file_path}")
            return
            
        # Step 1: Barcode detection (fastest, most accurate)
        barcode_result = await self._detect_barcode(file_path, image_id, request_id)
        
        if barcode_result:
            logger.info(f"📊 Barcode detected: {barcode_result['data']}")
            # Emit scrape request with barcode
            await emit_scrape_requested(
                query=barcode_result['data'],
                sites=['amazon', 'walmart', 'ebay'],
                max_results=10,
                request_id=request_id,
                priority=9  # User waiting
            )
            return  # Barcode is most reliable, skip other methods
            
        # Step 2: CLIP visual similarity search
        clip_match = await self._clip_search(file_path, request_id)
        
        if clip_match and clip_match.get('similarity', 0) > 0.7:
            # High confidence match
            logger.info(f"🎯 CLIP match: product_id={clip_match['product_id']}, similarity={clip_match['similarity']:.2f}")
            
            await emit_product_matched(
                product_id=clip_match['product_id'],
                similarity=clip_match['similarity'],
                method='clip',
                request_id=request_id
            )
            
            # Still trigger scraper for fresh prices
            async with async_session_maker() as db:
                stmt = select(Product).where(Product.id == clip_match['product_id'])
                result = await db.execute(stmt)
                product = result.scalar_one_or_none()
                
                if product:
                    search_query = f"{product.brand} {product.name}" if product.brand else product.name
                    await emit_scrape_requested(
                        query=search_query,
                        sites=['amazon', 'walmart', 'ebay'],
                        max_results=10,
                        request_id=request_id,
                        priority=8
                    )
            return
            
        # Step 3: OCR text extraction (fallback)
        ocr_result = await self._extract_text(file_path)
        
        if ocr_result and len(ocr_result.strip()) > 5:
            logger.info(f"📝 OCR extracted: {ocr_result[:100]}")
            
            # Use first meaningful text as search query
            search_query = ocr_result.strip()[:100]
            
            await emit_scrape_requested(
                query=search_query,
                sites=['amazon', 'walmart', 'ebay'],
                max_results=10,
                request_id=request_id,
                priority=7
            )
            return
            
        # No detection method succeeded
        logger.warning(f"⚠️ No product detected from image {image_id}")
        
    async def _detect_barcode(
        self,
        file_path: str,
        image_id: str,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Detect barcodes/QR codes in image"""
        if not self.image_processor:
            return None
            
        try:
            barcodes = await self.image_processor._detect_barcodes(file_path)
            
            if barcodes and len(barcodes) > 0:
                barcode = barcodes[0]  # Use first detected barcode
                
                await emit_barcode_detected(
                    value=barcode['data'],
                    barcode_type=barcode['type'],
                    image_id=image_id,
                    request_id=request_id
                )
                
                return barcode
                
        except Exception as e:
            logger.error(f"Barcode detection failed: {e}")
            
        return None
        
    async def _clip_search(
        self,
        file_path: str,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Search for visually similar products using CLIP"""
        if not self.clip_service or not self.clip_service.clip_model:
            return None
            
        try:
            matches = await self.clip_service.search_by_image(
                file_path,
                top_k=1
            )
            
            if matches and len(matches) > 0:
                return matches[0]
                
        except Exception as e:
            logger.error(f"CLIP search failed: {e}")
            
        return None
        
    async def _extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from image using OCR"""
        if not self.image_processor:
            return None
            
        try:
            text = await self.image_processor._extract_text(file_path)
            return text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            
        return None
        
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
        python -m app.workers.image_worker
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = ImageAIWorker()
    await worker.initialize()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
