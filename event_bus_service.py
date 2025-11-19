"""
Event Bus Service (Port 8016) - Phase 7
Real-time event processing with Kafka & Redis Streams
"""

from fastapi import FastAPI, HTTPException
import logging
from typing import List, Dict, Optional, Callable
import asyncio
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import aioredis
from core_infrastructure import ShardedServiceBase

app = FastAPI(title="Event Bus Service", version="1.0")
logger = logging.getLogger('event_bus')

# Initialize service
event_service = ShardedServiceBase(service_name="EventBus")

# Event types
class EventType(str, Enum):
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRICE_CHANGED = "price.changed"
    INVENTORY_CHANGED = "inventory.changed"
    PURCHASE_COMPLETED = "purchase.completed"
    USER_REGISTERED = "user.registered"
    REVIEW_POSTED = "review.posted"
    CART_ABANDONED = "cart.abandoned"
    ORDER_SHIPPED = "order.shipped"


@dataclass
class Event:
    """Domain event"""
    event_type: EventType
    event_id: str
    aggregate_id: str  # user_id, product_id, order_id, etc
    data: Dict
    timestamp: datetime
    source: str


# ============================================================================
# REDIS STREAMS (Event Store)
# ============================================================================

class RedisEventStore:
    """Event storage and retrieval using Redis Streams"""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{self.redis_host}:{self.redis_port}',
            encoding='utf-8',
            max_size=50
        )
        logger.info(f"✅ Redis Event Store connected")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def append_event(self, event: Event) -> str:
        """Append event to stream"""
        try:
            stream_key = f"events:{event.event_type}"

            event_data = {
                'event_id': event.event_id,
                'aggregate_id': event.aggregate_id,
                'type': event.event_type.value,
                'data': json.dumps(event.data),
                'timestamp': event.timestamp.isoformat(),
                'source': event.source
            }

            event_id = await self.redis.xadd(stream_key, event_data)

            # Also append to global events stream
            await self.redis.xadd('events:all', event_data)

            # Add to user-specific stream for personal history
            user_stream = f"events:user:{event.aggregate_id}"
            await self.redis.xadd(user_stream, event_data)

            logger.info(f"Event appended: {event.event_type} -> {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Event append error: {e}")
            raise

    async def get_events(self, stream_key: str, start: str = '0',
                        count: int = 100) -> List[Dict]:
        """Get events from stream"""
        try:
            events = await self.redis.xrange(stream_key, start, count=count)
            return events or []
        except Exception as e:
            logger.error(f"Get events error: {e}")
            return []

    async def get_events_since(self, stream_key: str, event_id: str,
                              count: int = 100) -> List[Dict]:
        """Get events after specific event"""
        try:
            events = await self.redis.xrange(
                stream_key,
                f"({event_id}",  # Exclusive
                count=count
            )
            return events or []
        except Exception as e:
            logger.error(f"Get events since error: {e}")
            return []

    async def create_consumer_group(self, stream_key: str, group_name: str):
        """Create consumer group for stream"""
        try:
            await self.redis.xgroup_create(stream_key, group_name, id='0')
            logger.info(f"Consumer group created: {group_name}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Consumer group creation error: {e}")


# ============================================================================
# EVENT PROCESSORS
# ============================================================================

class EventProcessor:
    """Process events and trigger side effects"""

    def __init__(self, event_store: RedisEventStore, db_service: ShardedServiceBase):
        self.event_store = event_store
        self.db_service = db_service
        self.processors: Dict[EventType, List[Callable]] = {}

    def register_processor(self, event_type: EventType, handler: Callable):
        """Register event handler"""
        if event_type not in self.processors:
            self.processors[event_type] = []
        self.processors[event_type].append(handler)
        logger.info(f"Processor registered for {event_type}")

    async def process_event(self, event: Event):
        """Process event with all registered handlers"""
        try:
            handlers = self.processors.get(event.event_type, [])

            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {e}")
                    # Add to dead letter queue
                    await self.add_to_dlq(event, str(e))

        except Exception as e:
            logger.error(f"Event processing error: {e}")

    async def add_to_dlq(self, event: Event, error: str):
        """Add failed event to dead letter queue"""
        try:
            dlq_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'aggregate_id': event.aggregate_id,
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            }

            await self.event_store.redis.xadd('dlq:events', dlq_data)
            logger.warning(f"Event sent to DLQ: {event.event_id}")

        except Exception as e:
            logger.error(f"DLQ error: {e}")


# ============================================================================
# EVENT HANDLERS (Side Effects)
# ============================================================================

async def handle_product_created(event: Event):
    """Handle new product creation"""
    try:
        product_id = event.aggregate_id
        product_data = event.data

        # Index in search
        logger.info(f"Indexing product: {product_id}")
        # In production: call search service

        # Update cache
        await event_service.cache.invalidate("trending:*")

        # Log to audit trail
        query = """
            INSERT INTO audit_log (event_type, entity_id, data, timestamp)
            VALUES ($1, $2, $3, NOW())
        """
        await event_service.write(
            product_id[:8],  # Use first 8 chars for shard
            query,
            ('product_created', product_id, json.dumps(product_data))
        )

    except Exception as e:
        logger.error(f"Product created handler error: {e}")
        raise


async def handle_price_changed(event: Event):
    """Handle price changes"""
    try:
        product_id = event.aggregate_id
        price_data = event.data

        logger.info(f"Price changed for {product_id}: {price_data}")

        # Check price alerts
        query = """
            SELECT user_id FROM price_alerts
            WHERE product_id = $1
            AND alert_price >= $2
            AND active = true
        """

        # In production: this would trigger notifications to users

        # Update cache for product
        await event_service.cache.invalidate(f"product:{product_id}")

    except Exception as e:
        logger.error(f"Price changed handler error: {e}")
        raise


async def handle_purchase_completed(event: Event):
    """Handle purchase completion"""
    try:
        order_id = event.aggregate_id
        purchase_data = event.data
        user_id = purchase_data.get('user_id')

        logger.info(f"Purchase completed: {order_id}")

        # Update user's purchase history
        query = """
            INSERT INTO purchase_history (user_id, order_id, total_amount, timestamp)
            VALUES ($1, $2, $3, NOW())
        """

        await event_service.write(
            user_id,
            query,
            (user_id, order_id, purchase_data.get('total'))
        )

        # Trigger recommendations rebuild
        await event_service.cache.invalidate(f"recommendations:user:{user_id}")

        # Update demand forecast cache
        for product_id in purchase_data.get('product_ids', []):
            await event_service.cache.invalidate(f"forecast:{product_id}")

    except Exception as e:
        logger.error(f"Purchase completed handler error: {e}")
        raise


async def handle_inventory_changed(event: Event):
    """Handle inventory changes"""
    try:
        product_id = event.aggregate_id
        inventory_data = event.data

        logger.info(f"Inventory changed for {product_id}: {inventory_data}")

        # Log inventory change
        query = """
            INSERT INTO inventory_log (product_id, previous_stock, current_stock, warehouse_id)
            VALUES ($1, $2, $3, $4)
        """

        await event_service.write(
            product_id[:8],
            query,
            (
                product_id,
                inventory_data.get('previous_stock'),
                inventory_data.get('current_stock'),
                inventory_data.get('warehouse_id')
            )
        )

        # Update stock cache
        await event_service.cache.invalidate(f"stock:{product_id}")

    except Exception as e:
        logger.error(f"Inventory changed handler error: {e}")
        raise


async def handle_review_posted(event: Event):
    """Handle new review posting"""
    try:
        review_id = event.aggregate_id
        review_data = event.data

        logger.info(f"Review posted: {review_id}")

        # Update product rating cache
        product_id = review_data.get('product_id')
        await event_service.cache.invalidate(f"product:{product_id}")

        # Index in Elasticsearch
        # In production: call Elasticsearch service

    except Exception as e:
        logger.error(f"Review posted handler error: {e}")
        raise


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

event_store = RedisEventStore()
event_processor = None


@app.on_event('startup')
async def startup():
    """Initialize event bus"""
    global event_processor

    shard_config = {
        0: {'primary_host': 'postgres-primary-0', 'port': 5432, 'replica_hosts': []},
        1: {'primary_host': 'postgres-primary-1', 'port': 5432, 'replica_hosts': []},
        2: {'primary_host': 'postgres-primary-2', 'port': 5432, 'replica_hosts': []},
        3: {'primary_host': 'postgres-primary-3', 'port': 5432, 'replica_hosts': []},
    }

    await event_service.initialize(shard_config)
    await event_store.connect()

    # Initialize event processor
    event_processor = EventProcessor(event_store, event_service)

    # Register event handlers
    event_processor.register_processor(EventType.PRODUCT_CREATED, handle_product_created)
    event_processor.register_processor(EventType.PRICE_CHANGED, handle_price_changed)
    event_processor.register_processor(EventType.PURCHASE_COMPLETED, handle_purchase_completed)
    event_processor.register_processor(EventType.INVENTORY_CHANGED, handle_inventory_changed)
    event_processor.register_processor(EventType.REVIEW_POSTED, handle_review_posted)

    # Start event processing loop
    asyncio.create_task(process_events_loop())

    logger.info("✅ Event Bus Service started")


@app.on_event('shutdown')
async def shutdown():
    """Cleanup"""
    await event_store.disconnect()
    await event_service.shutdown()


async def process_events_loop():
    """Background task: Process events from streams"""
    while True:
        try:
            await asyncio.sleep(1)

            # Process recent events from main stream
            events = await event_store.get_events('events:all', count=100)

            for event_id, event_data in events:
                event = Event(
                    event_type=EventType(event_data.get('type')),
                    event_id=event_data.get('event_id'),
                    aggregate_id=event_data.get('aggregate_id'),
                    data=json.loads(event_data.get('data', '{}')),
                    timestamp=datetime.fromisoformat(event_data.get('timestamp')),
                    source=event_data.get('source')
                )

                await event_processor.process_event(event)

        except Exception as e:
            logger.error(f"Event processing loop error: {e}")


# ============================================================================
# EVENT PUBLISHING ENDPOINTS
# ============================================================================

@app.post('/events/publish')
async def publish_event(event_type: str, aggregate_id: str, data: dict, source: str):
    """Publish event to bus"""
    if not event_processor:
        raise HTTPException(status_code=503, detail="Event bus not ready")

    try:
        try:
            evt_type = EventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown event type: {event_type}")

        import uuid
        event = Event(
            event_type=evt_type,
            event_id=str(uuid.uuid4()),
            aggregate_id=aggregate_id,
            data=data,
            timestamp=datetime.utcnow(),
            source=source
        )

        event_id = await event_store.append_event(event)

        # Process event
        await event_processor.process_event(event)

        return {
            'event_id': event_id,
            'event_type': event_type,
            'status': 'published'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publish error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/events/stream/{stream_key}')
async def get_stream_events(stream_key: str, count: int = 100):
    """Get events from stream"""
    try:
        if not event_store.redis:
            raise HTTPException(status_code=503, detail="Event store not ready")

        events = await event_store.get_events(stream_key, count=count)

        return {
            'stream': stream_key,
            'count': len(events),
            'events': events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/events/user/{user_id}')
async def get_user_events(user_id: str, count: int = 50):
    """Get all events for user"""
    try:
        if not event_store.redis:
            raise HTTPException(status_code=503, detail="Event store not ready")

        stream_key = f"events:user:{user_id}"
        events = await event_store.get_events(stream_key, count=count)

        return {
            'user_id': user_id,
            'count': len(events),
            'events': events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/events/dlq')
async def get_dead_letter_queue(count: int = 100):
    """Get dead letter queue events"""
    try:
        if not event_store.redis:
            raise HTTPException(status_code=503, detail="Event store not ready")

        dlq_events = await event_store.get_events('dlq:events', count=count)

        return {
            'dlq_count': len(dlq_events),
            'events': dlq_events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/events/retry-dlq/{event_id}')
async def retry_dlq_event(event_id: str):
    """Retry a dead letter queue event"""
    try:
        if not event_processor:
            raise HTTPException(status_code=503, detail="Event bus not ready")

        # In production: retrieve event from DLQ and retry
        logger.info(f"Retrying DLQ event: {event_id}")

        return {'status': 'retry_queued', 'event_id': event_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/stats')
async def get_event_bus_stats():
    """Get event bus statistics"""
    try:
        if not event_store.redis:
            return {'status': 'unavailable'}

        # Get stream info
        all_events = await event_store.get_events('events:all', count=0)
        dlq_events = await event_store.get_events('dlq:events', count=0)

        return {
            'service': 'event_bus',
            'total_events': len(all_events),
            'dlq_count': len(dlq_events),
            'service_metrics': event_service.get_metrics()
        }

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8016)
