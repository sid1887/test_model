"""
Unified API Gateway Service (Port 8000)
Integrates all Phase 7 microservices with proper routing, error handling, and inter-service communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

# ============================================================================
# SERVICE REGISTRY & CONFIGURATION
# ============================================================================

class ServiceRegistry:
    """Registry of all backend microservices"""

    SERVICES = {
        "search": {"host": "localhost", "port": 8010, "base_url": "http://localhost:8010"},
        "realtime": {"host": "localhost", "port": 8013, "base_url": "http://localhost:8013"},
        "ml": {"host": "localhost", "port": 8014, "base_url": "http://localhost:8014"},
        "elasticsearch": {"host": "localhost", "port": 8015, "base_url": "http://localhost:8015"},
        "events": {"host": "localhost", "port": 8016, "base_url": "http://localhost:8016"},
    }

    @classmethod
    def get_service(cls, name: str) -> Optional[str]:
        """Get service base URL"""
        service = cls.SERVICES.get(name)
        return service["base_url"] if service else None

    @classmethod
    def get_all_services(cls) -> Dict[str, str]:
        """Get all service URLs"""
        return {name: service["base_url"] for name, service in cls.SERVICES.items()}


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Cumpair Unified API Gateway",
    description="Central gateway integrating all Phase 7 microservices",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None


@app.on_event("startup")
async def startup_event():
    """Initialize gateway services"""
    global http_client

    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("🚀 API Gateway started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup gateway services"""
    global http_client

    if http_client:
        await http_client.aclose()

    logger.info("🛑 API Gateway shutdown")


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Check gateway and all service health"""
    services_status = {}

    for service_name, service_url in ServiceRegistry.get_all_services().items():
        try:
            if http_client:
                response = await http_client.get(f"{service_url}/health", timeout=5.0)
                services_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "code": response.status_code
                }
        except Exception as e:
            services_status[service_name] = {"status": "unreachable", "error": str(e)}

    all_healthy = all(s.get("status") == "healthy" for s in services_status.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "gateway": "ready",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status/services")
async def service_status():
    """Detailed service status"""
    return ServiceRegistry.get_all_services()


# ============================================================================
# SEARCH API ENDPOINTS (Port 8010)
# ============================================================================

@app.get("/api/search")
async def search(
    q: str = Query(...),
    limit: int = Query(20),
    offset: int = Query(0),
    cache: bool = Query(True),
    index: bool = Query(True),
):
    """Unified search across all indexed products"""
    try:
        search_url = f"{ServiceRegistry.get_service('search')}/search"

        if not http_client:
            raise HTTPException(status_code=503, detail="HTTP client unavailable")

        response = await http_client.get(
            search_url,
            params={"q": q, "limit": limit, "offset": offset, "cache": cache}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Search service error")

        return response.json()
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/semantic")
async def semantic_search(
    q: str = Query(...),
    limit: int = Query(10),
):
    """Semantic search using embeddings"""
    try:
        search_url = f"{ServiceRegistry.get_service('search')}/semantic-search"

        if not http_client:
            raise HTTPException(status_code=503, detail="HTTP client unavailable")

        response = await http_client.get(
            search_url,
            params={"q": q, "limit": limit}
        )

        return response.json()
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/autocomplete")
async def autocomplete(
    q: str = Query(...),
    limit: int = Query(10),
):
    """Autocomplete suggestions"""
    try:
        search_url = f"{ServiceRegistry.get_service('search')}/autocomplete"
        response = await http_client.get(search_url, params={"q": q, "limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/faceted")
async def faceted_search(
    q: str = Query(...),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    limit: int = Query(20),
):
    """Faceted search with filters"""
    try:
        search_url = f"{ServiceRegistry.get_service('search')}/faceted-search"
        params = {"q": q, "limit": limit}
        if category:
            params["category"] = category
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        response = await http_client.get(search_url, params=params)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/trending")
async def trending_search(limit: int = Query(10)):
    """Trending search queries"""
    try:
        search_url = f"{ServiceRegistry.get_service('search')}/trending"
        response = await http_client.get(search_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ELASTICSEARCH API ENDPOINTS (Port 8015)
# ============================================================================

@app.get("/api/search/elasticsearch")
async def elasticsearch_search(
    q: str = Query(...),
    limit: int = Query(10),
):
    """Full-text search via Elasticsearch"""
    try:
        es_url = f"{ServiceRegistry.get_service('elasticsearch')}/search"
        response = await http_client.get(es_url, params={"q": q, "limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/fuzzy")
async def fuzzy_search(
    q: str = Query(...),
    limit: int = Query(10),
):
    """Typo-tolerant fuzzy search"""
    try:
        es_url = f"{ServiceRegistry.get_service('elasticsearch')}/search/fuzzy"
        response = await http_client.get(es_url, params={"q": q, "limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/autocomplete-es")
async def autocomplete_elasticsearch(
    q: str = Query(...),
    limit: int = Query(10),
):
    """Elasticsearch autocomplete"""
    try:
        es_url = f"{ServiceRegistry.get_service('elasticsearch')}/autocomplete"
        response = await http_client.get(es_url, params={"q": q, "limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RECOMMENDATIONS API ENDPOINTS (Port 8014)
# ============================================================================

@app.get("/api/recommendations/for-you/{user_id}")
async def get_recommendations(user_id: str, limit: int = Query(10)):
    """Get personalized recommendations for user"""
    try:
        ml_url = f"{ServiceRegistry.get_service('ml')}/recommendations/for-you/{user_id}"
        response = await http_client.get(ml_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/similar/{product_id}")
async def get_similar_products(product_id: str, limit: int = Query(10)):
    """Get similar products"""
    try:
        ml_url = f"{ServiceRegistry.get_service('ml')}/recommendations/similar/{product_id}"
        response = await http_client.get(ml_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/trending")
async def get_trending(limit: int = Query(10)):
    """Get trending products"""
    try:
        ml_url = f"{ServiceRegistry.get_service('ml')}/recommendations/trending"
        response = await http_client.get(ml_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/demand/{product_id}")
async def forecast_demand(product_id: str):
    """Demand forecast for product"""
    try:
        ml_url = f"{ServiceRegistry.get_service('ml')}/forecast/demand/{product_id}"
        response = await http_client.get(ml_url)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REAL-TIME API ENDPOINTS (Port 8013)
# ============================================================================

@app.get("/api/realtime/stats")
async def realtime_stats():
    """Get real-time service statistics"""
    try:
        rt_url = f"{ServiceRegistry.get_service('realtime')}/stats"
        response = await http_client.get(rt_url)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/realtime/notify")
async def send_notification(user_id: str, message: str):
    """Send real-time notification to user"""
    try:
        rt_url = f"{ServiceRegistry.get_service('realtime')}/broadcast-notification"
        response = await http_client.post(
            rt_url,
            json={"user_id": user_id, "message": message}
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVENTS API ENDPOINTS (Port 8016)
# ============================================================================

@app.post("/api/events/publish")
async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
):
    """Publish event to event bus"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/publish"
        response = await http_client.post(
            events_url,
            json={"event_type": event_type, "data": data, "user_id": user_id}
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/stream/{stream_key}")
async def get_event_stream(stream_key: str, limit: int = Query(100)):
    """Get events from stream"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/stream/{stream_key}"
        response = await http_client.get(events_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/user/{user_id}")
async def get_user_events(user_id: str, limit: int = Query(100)):
    """Get events for user"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/user/{user_id}"
        response = await http_client.get(events_url, params={"limit": limit})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/dlq")
async def get_dead_letter_queue():
    """Get events in dead letter queue"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/dlq"
        response = await http_client.get(events_url)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/retry/{event_id}")
async def retry_event(event_id: str):
    """Retry failed event"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/retry-dlq/{event_id}"
        response = await http_client.post(events_url)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRICE ALERTS API (Combined: Events + Real-time)
# ============================================================================

@app.post("/api/alerts/price")
async def create_price_alert(
    product_id: str,
    target_price: float,
    user_id: str,
    background_tasks: BackgroundTasks,
):
    """Create price alert - publishes event and monitors"""
    try:
        # Publish price alert event
        event_data = {
            "product_id": product_id,
            "target_price": target_price,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        events_url = f"{ServiceRegistry.get_service('events')}/events/publish"

        event_response = await http_client.post(
            events_url,
            json={
                "event_type": "price_alert.created",
                "data": event_data,
                "user_id": user_id,
            }
        )

        return {
            "alert_id": event_response.json().get("id", "unknown"),
            "product_id": product_id,
            "target_price": target_price,
            "status": "created",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/user/{user_id}")
async def get_user_alerts(user_id: str):
    """Get all alerts for user"""
    try:
        events_url = f"{ServiceRegistry.get_service('events')}/events/user/{user_id}"
        response = await http_client.get(events_url)

        # Filter for alert events
        events = response.json().get("events", [])
        alerts = [e for e in events if e.get("type", "").startswith("price_alert")]

        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET REAL-TIME ENDPOINTS
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"✅ User {user_id} connected (total: {len(self.active_connections[user_id])})")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"❌ User {user_id} disconnected")

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all user connections"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    async def broadcast_all(self, message: Dict[str, Any]):
        """Broadcast to all connected users"""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")


manager = ConnectionManager()


@app.websocket("/ws/realtime/{user_id}")
async def websocket_realtime(websocket: WebSocket, user_id: str):
    """WebSocket connection for real-time updates"""
    await manager.connect(user_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "subscribe":
                    channel = message.get("channel")
                    logger.info(f"User {user_id} subscribed to {channel}")

                elif message.get("type") == "unsubscribe":
                    channel = message.get("channel")
                    logger.info(f"User {user_id} unsubscribed from {channel}")

                elif message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(user_id, websocket)


@app.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "connected_users": len(manager.active_connections),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "users": list(manager.active_connections.keys()),
    }


# ============================================================================
# BACKGROUND TASKS: SYNC REAL-TIME UPDATES
# ============================================================================

async def sync_realtime_updates():
    """Background task to sync real-time updates from services to connected clients"""
    while True:
        try:
            # Get updates from event bus
            events_url = f"{ServiceRegistry.get_service('events')}/events/stream/realtime"

            response = await http_client.get(events_url, params={"limit": 100})
            events = response.json().get("events", [])

            # Send to connected users
            for event in events:
                user_id = event.get("user_id")
                if user_id:
                    await manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "update",
                            "event": event,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            await asyncio.sleep(0.5)  # Poll every 500ms

        except Exception as e:
            logger.error(f"Realtime sync error: {e}")
            await asyncio.sleep(1)


# Start background task on startup
@app.on_event("startup")
async def start_realtime_sync():
    """Start real-time sync background task"""
    asyncio.create_task(sync_realtime_updates())


# ============================================================================
# ROOT & INFO ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Gateway info"""
    return {
        "name": "Cumpair API Gateway",
        "version": "1.0.0",
        "services": ServiceRegistry.get_all_services(),
        "endpoints": {
            "health": "/health",
            "services": "/status/services",
            "search": "/api/search",
            "recommendations": "/api/recommendations/for-you/{user_id}",
            "realtime": "/ws/realtime/{user_id}",
            "events": "/api/events/publish",
            "alerts": "/api/alerts/price",
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
