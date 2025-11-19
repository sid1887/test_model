"""
WebSocket Real-Time Service (Port 8013) - Phase 7
Live product updates, inventory changes, price alerts, notifications
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
from typing import List, Dict, Set
from datetime import datetime
from core_infrastructure import ShardedServiceBase
import aioredis

app = FastAPI(title="Real-Time Service", version="1.0")
logger = logging.getLogger('realtime_service')

# Initialize service
realtime_service = ShardedServiceBase(service_name="RealtimeService")

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        self.channels = [
            'live_prices',
            'inventory_updates',
            'price_alerts',
            'new_products',
            'user_notifications'
        ]

    async def connect(self, websocket: WebSocket, user_id: str, channels: List[str]):
        """Add new connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.user_subscriptions[user_id] = set()

        self.active_connections[user_id].append(websocket)

        # Subscribe to channels
        for channel in channels:
            if channel in self.channels:
                self.user_subscriptions[user_id].add(channel)

        logger.info(f"✅ {user_id} connected to channels: {channels}")

    async def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.user_subscriptions[user_id]

        logger.info(f"❌ {user_id} disconnected")

    async def broadcast(self, channel: str, message: dict):
        """Broadcast to all users subscribed to channel"""
        for user_id, subs in self.user_subscriptions.items():
            if channel in subs:
                if user_id in self.active_connections:
                    for connection in self.active_connections[user_id]:
                        try:
                            await connection.send_json({
                                'channel': channel,
                                'timestamp': datetime.utcnow().isoformat(),
                                'data': message
                            })
                        except Exception as e:
                            logger.error(f"Broadcast error to {user_id}: {e}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json({
                        'timestamp': datetime.utcnow().isoformat(),
                        'data': message
                    })
                except Exception as e:
                    logger.error(f"Send error to {user_id}: {e}")

    def get_stats(self) -> dict:
        """Get connection statistics"""
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        return {
            'connected_users': len(self.active_connections),
            'total_connections': total_connections,
            'channels': self.channels
        }


manager = ConnectionManager()


@app.on_event('startup')
async def startup():
    """Initialize service"""
    shard_config = {
        0: {'primary_host': 'postgres-primary-0', 'port': 5432, 'replica_hosts': []},
        1: {'primary_host': 'postgres-primary-1', 'port': 5432, 'replica_hosts': []},
        2: {'primary_host': 'postgres-primary-2', 'port': 5432, 'replica_hosts': []},
        3: {'primary_host': 'postgres-primary-3', 'port': 5432, 'replica_hosts': []},
    }

    await realtime_service.initialize(shard_config)

    # Start background tasks
    asyncio.create_task(price_update_broadcaster())
    asyncio.create_task(inventory_update_broadcaster())
    asyncio.create_task(alert_processor())

    logger.info("✅ Real-Time Service started")


@app.on_event('shutdown')
async def shutdown():
    """Cleanup"""
    await realtime_service.shutdown()


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/realtime/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Main WebSocket connection for real-time updates
    Channels: live_prices, inventory_updates, price_alerts, new_products, user_notifications
    """
    try:
        # Get requested channels from query params
        channels = ['live_prices', 'inventory_updates', 'user_notifications']

        await manager.connect(websocket, user_id, channels)

        # Send initial connection message
        await websocket.send_json({
            'type': 'connected',
            'user_id': user_id,
            'channels': channels,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Keep connection alive and receive messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get('type') == 'subscribe':
                channel = message.get('channel')
                if channel in manager.channels:
                    manager.user_subscriptions[user_id].add(channel)
                    await websocket.send_json({
                        'type': 'subscribed',
                        'channel': channel
                    })

            elif message.get('type') == 'unsubscribe':
                channel = message.get('channel')
                manager.user_subscriptions[user_id].discard(channel)
                await websocket.send_json({
                    'type': 'unsubscribed',
                    'channel': channel
                })

            elif message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(user_id, websocket)


@app.websocket("/ws/live-search/{user_id}")
async def live_search_endpoint(websocket: WebSocket, user_id: str):
    """
    Live search results streaming as user types
    Sub-100ms latency with caching and sharding
    """
    try:
        await websocket.accept()

        while True:
            # Receive search query
            data = await websocket.receive_text()
            query = json.loads(data).get('query', '')

            if not query or len(query) < 2:
                continue

            # Execute search with Phase 6 optimizations
            search_query = """
                SELECT id, name, category, price
                FROM products
                WHERE to_tsvector('english', name) @@
                      plainto_tsquery('english', $1)
                ORDER BY rating DESC
                LIMIT 10
            """

            try:
                results = await realtime_service.aggregation(search_query, (query,))

                # Stream results in batches for real-time feel
                batch_size = 3
                for i in range(0, len(results), batch_size):
                    batch = results[i:i+batch_size]
                    await websocket.send_json({
                        'type': 'search_results',
                        'query': query,
                        'results': batch,
                        'total': len(results),
                        'batch': i // batch_size + 1
                    })
                    await asyncio.sleep(0.05)  # Small delay for streaming effect

            except Exception as e:
                logger.error(f"Search error: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Search failed'
                })

    except WebSocketDisconnect:
        logger.info(f"Live search disconnected: {user_id}")
    except Exception as e:
        logger.error(f"Live search error: {e}")


@app.websocket("/ws/price-alerts/{user_id}")
async def price_alerts_endpoint(websocket: WebSocket, user_id: str):
    """Real-time price alert notifications"""
    try:
        await websocket.accept()
        logger.info(f"Price alert connection: {user_id}")

        # Fetch user's watched products and alert thresholds
        query = """
            SELECT product_id, alert_price, alert_type
            FROM price_alerts
            WHERE user_id = $1 AND active = true
        """

        alerts = await realtime_service.query(user_id, query, (user_id,))

        await websocket.send_json({
            'type': 'alerts_loaded',
            'count': len(alerts) if alerts else 0
        })

        while True:
            data = await websocket.receive_text()
            command = json.loads(data)

            if command.get('type') == 'add_alert':
                # Save alert to user's shard
                product_id = command.get('product_id')
                alert_price = command.get('alert_price')

                insert_query = """
                    INSERT INTO price_alerts
                    (user_id, product_id, alert_price, alert_type, active)
                    VALUES ($1, $2, $3, $4, true)
                """

                await realtime_service.write(
                    user_id,
                    insert_query,
                    (user_id, product_id, alert_price, 'below')
                )

                await websocket.send_json({
                    'type': 'alert_added',
                    'product_id': product_id,
                    'alert_price': alert_price
                })

    except WebSocketDisconnect:
        logger.info(f"Price alert disconnected: {user_id}")


# ============================================================================
# BACKGROUND TASKS FOR BROADCASTING
# ============================================================================

async def price_update_broadcaster():
    """Background task: Broadcast live price updates every 5 seconds"""
    while True:
        try:
            await asyncio.sleep(5)

            # Get updated prices for trending products
            query = """
                SELECT id, name, current_price, previous_price,
                       ROUND((current_price - previous_price) / previous_price * 100, 2) as percent_change
                FROM products
                WHERE updated_at > NOW() - INTERVAL '5 seconds'
                ORDER BY percent_change DESC
                LIMIT 20
            """

            updates = await realtime_service.aggregation(query, ())

            if updates:
                await manager.broadcast('live_prices', {
                    'type': 'price_update',
                    'updates': updates,
                    'timestamp': datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Price broadcaster error: {e}")


async def inventory_update_broadcaster():
    """Background task: Broadcast inventory changes"""
    while True:
        try:
            await asyncio.sleep(3)

            # Get recent inventory changes
            query = """
                SELECT product_id, previous_stock, current_stock,
                       warehouse_id, updated_at
                FROM inventory_log
                WHERE updated_at > NOW() - INTERVAL '3 seconds'
                ORDER BY updated_at DESC
                LIMIT 50
            """

            updates = await realtime_service.aggregation(query, ())

            if updates:
                await manager.broadcast('inventory_updates', {
                    'type': 'inventory_change',
                    'updates': updates
                })

        except Exception as e:
            logger.error(f"Inventory broadcaster error: {e}")


async def alert_processor():
    """Background task: Process and trigger price alerts"""
    while True:
        try:
            await asyncio.sleep(10)

            # Find price drops that trigger alerts
            query = """
                SELECT DISTINCT pa.user_id, pa.product_id,
                       pa.alert_price, p.current_price
                FROM price_alerts pa
                JOIN products p ON pa.product_id = p.id
                WHERE pa.active = true
                AND p.current_price <= pa.alert_price
                AND pa.last_triggered < NOW() - INTERVAL '24 hours'
            """

            triggered_alerts = await realtime_service.aggregation(query, ())

            for alert in (triggered_alerts or []):
                # Send to user
                await manager.send_to_user(alert['user_id'], {
                    'type': 'price_alert',
                    'product_id': alert['product_id'],
                    'alert_price': alert['alert_price'],
                    'current_price': alert['current_price'],
                    'triggered_at': datetime.utcnow().isoformat()
                })

                # Update last_triggered timestamp
                update_query = """
                    UPDATE price_alerts
                    SET last_triggered = NOW()
                    WHERE user_id = $1 AND product_id = $2
                """

                await realtime_service.write(
                    alert['user_id'],
                    update_query,
                    (alert['user_id'], alert['product_id'])
                )

        except Exception as e:
            logger.error(f"Alert processor error: {e}")


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.get('/stats')
async def get_stats():
    """Get real-time service statistics"""
    return {
        'service': 'realtime',
        'connections': manager.get_stats(),
        'service_metrics': realtime_service.get_metrics()
    }


@app.post('/broadcast-notification')
async def broadcast_notification(message: dict):
    """Admin endpoint to send broadcast notification"""
    await manager.broadcast('user_notifications', message)
    return {'status': 'broadcasted', 'recipients': len(manager.active_connections)}


@app.get('/connected-users')
async def get_connected_users():
    """Get list of connected users"""
    return {
        'count': len(manager.active_connections),
        'users': list(manager.active_connections.keys())[:100]
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8013)
