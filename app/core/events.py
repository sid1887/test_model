"""
Event-Driven Architecture Backbone
Redis Streams based event system for parallel workstream coordination
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """All event types in the system"""
    # Product events
    PRODUCT_SEEN = "product.seen"
    PRODUCT_STALE = "product.stale"
    PRODUCT_MATCHED = "product.matched"
    PRODUCT_UPDATED = "product.updated"
    
    # Image/AI events
    IMAGE_UPLOADED = "image.uploaded"
    IMAGE_ANALYZED = "image.analyzed"
    BARCODE_DETECTED = "barcode.detected"
    CLIP_EMBEDDING_COMPUTED = "clip.embedding.computed"
    
    # Scraper events
    SCRAPE_REQUESTED = "scrape.requested"
    SCRAPE_COMPLETED = "scrape.completed"
    SCRAPE_FAILED = "scrape.failed"
    
    # Alert events
    ALERT_CREATED = "alert.created"
    ALERT_TRIGGERED = "alert.triggered"
    PRICE_DROPPED = "price.dropped"
    
    # Search events
    SEARCH_EXECUTED = "search.executed"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"


class Event(BaseModel):
    """Base event model"""
    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime = None
    request_id: Optional[str] = None
    priority: int = 5  # 1-10, higher = more urgent
    metadata: Dict[str, Any] = {}  # For message_id, stream_name, etc.
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class EventBus:
    """Redis Streams based event bus for parallel workstream coordination"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.stream_prefix = "events"
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("EventBus connected to Redis")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("EventBus disconnected")
    
    async def publish(self, event: Event) -> str:
        """
        Publish event to Redis Stream
        Returns: message_id
        """
        await self.connect()
        
        stream_name = f"{self.stream_prefix}:{event.type.value}"
        
        # Serialize event
        event_data = {
            "type": event.type.value,
            "payload": json.dumps(event.payload),
            "timestamp": event.timestamp.isoformat(),
            "request_id": event.request_id or "",
            "priority": str(event.priority)
        }
        
        # Add to stream with automatic ID
        message_id = await self.redis_client.xadd(stream_name, event_data)
        
        logger.debug(f"Published event {event.type.value} to {stream_name}: {message_id}")
        return message_id
    
    async def subscribe(
        self,
        event_types: list[EventType],
        consumer_group: str,
        consumer_name: str,
        block_ms: int = 1000
    ):
        """
        Subscribe to events using consumer groups
        Yields: Event objects
        """
        await self.connect()
        
        import asyncio
        
        # Create stream dict for reading
        streams = {
            f"{self.stream_prefix}:{event_type.value}": ">"
            for event_type in event_types
        }
        
        # Create consumer groups if they don't exist
        for stream_name in streams.keys():
            try:
                await self.redis_client.xgroup_create(
                    stream_name, consumer_group, id="0", mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
        
        # Read from streams
        while True:
            try:
                messages = await self.redis_client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    streams,
                    count=10,
                    block=block_ms
                )
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        # Deserialize event
                        event = Event(
                            type=EventType(data["type"]),
                            payload=json.loads(data["payload"]),
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            request_id=data.get("request_id") or None,
                            priority=int(data.get("priority", 5))
                        )
                        
                        # Add message metadata
                        event.metadata = {
                            'message_id': message_id,
                            'stream_name': stream_name
                        }
                        
                        yield event
                        
            except Exception as e:
                logger.error(f"Error reading from streams: {e}")
                await asyncio.sleep(1)
    
    async def acknowledge(self, stream_name: str, consumer_group: str, message_id: str):
        """Acknowledge message processing"""
        await self.redis_client.xack(stream_name, consumer_group, message_id)
    
    async def get_pending_count(self, stream_name: str, consumer_group: str) -> int:
        """Get count of pending messages in consumer group"""
        try:
            pending_info = await self.redis_client.xpending(stream_name, consumer_group)
            return pending_info['pending']
        except:
            return 0


# Global event bus instance
event_bus = EventBus()


# Helper functions for common events
async def emit_product_seen(product_id: int, source: str, request_id: str = None):
    """Emit when a product is seen/requested by user"""
    event = Event(
        type=EventType.PRODUCT_SEEN,
        payload={"product_id": product_id, "source": source},
        request_id=request_id,
        priority=8  # High priority - user triggered
    )
    await event_bus.publish(event)


async def emit_image_uploaded(image_id: str, file_path: str, request_id: str = None):
    """Emit when user uploads an image for product search"""
    event = Event(
        type=EventType.IMAGE_UPLOADED,
        payload={"image_id": image_id, "file_path": file_path},
        request_id=request_id,
        priority=9  # Very high priority - user waiting
    )
    await event_bus.publish(event)


async def emit_barcode_detected(barcode_value: str, barcode_type: str, image_id: str, request_id: str = None):
    """Emit when barcode is detected in image"""
    event = Event(
        type=EventType.BARCODE_DETECTED,
        payload={
            "barcode_value": barcode_value,
            "barcode_type": barcode_type,
            "image_id": image_id
        },
        request_id=request_id,
        priority=9
    )
    await event_bus.publish(event)


async def emit_scrape_requested(
    query: str,
    sites: list,
    max_results: int = 10,
    request_id: str = None,
    priority: int = 7
):
    """Emit when scrape is requested"""
    event = Event(
        type=EventType.SCRAPE_REQUESTED,
        payload={
            "query": query,
            "sites": sites,
            "max_results": max_results
        },
        request_id=request_id,
        priority=priority
    )
    await event_bus.publish(event)


async def emit_price_dropped(product_id: int, old_price: float, new_price: float, retailer: str):
    """Emit when price drops"""
    event = Event(
        type=EventType.PRICE_DROPPED,
        payload={
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price,
            "retailer": retailer,
            "drop_percentage": ((old_price - new_price) / old_price) * 100
        },
        priority=6
    )
    await event_bus.publish(event)


async def emit_product_matched(product_id: int, similarity: float, method: str, request_id: str = None):
    """Emit when AI matches a product from image"""
    event = Event(
        type=EventType.PRODUCT_MATCHED,
        payload={
            "product_id": product_id,
            "similarity": similarity,
            "method": method
        },
        request_id=request_id,
        priority=8
    )
    await event_bus.publish(event)


async def emit_scrape_completed(query: str, results_count: int, saved_count: int, request_id: str = None):
    """Emit when scrape completes successfully"""
    event = Event(
        type=EventType.SCRAPE_COMPLETED,
        payload={
            "query": query,
            "results_count": results_count,
            "saved_count": saved_count,
            "timestamp": datetime.utcnow().isoformat()
        },
        request_id=request_id,
        priority=5
    )
    await event_bus.publish(event)


async def emit_scrape_failed(query: str, error: str, request_id: str = None):
    """Emit when scrape fails"""
    event = Event(
        type=EventType.SCRAPE_FAILED,
        payload={
            "query": query,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        },
        request_id=request_id,
        priority=5
    )
    await event_bus.publish(event)


async def emit_search_executed(query: str, results_count: int, cache_hit: bool, latency_ms: float, request_id: str = None):
    """Emit search analytics event"""
    event = Event(
        type=EventType.SEARCH_EXECUTED,
        payload={
            "query": query,
            "results_count": results_count,
            "cache_hit": cache_hit,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        },
        request_id=request_id,
        priority=3
    )
    await event_bus.publish(event)
