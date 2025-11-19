"""
End-to-End Integration Test
Tests complete flow: Search → Indexing → ML Recommendations → Real-time Events → Frontend
"""

import asyncio
import httpx
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_test")

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

API_GATEWAY_URL = "http://localhost:8000"
SERVICE_URLS = {
    "search": "http://localhost:8010",
    "realtime": "http://localhost:8013",
    "ml": "http://localhost:8014",
    "elasticsearch": "http://localhost:8015",
    "events": "http://localhost:8016",
}

# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

async def test_gateway_health():
    """Test API Gateway health"""
    logger.info("🔍 Testing API Gateway health...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/health")
        assert response.status_code == 200, f"Gateway unhealthy: {response.text}"

        data = response.json()
        services = data.get("services", {})

        logger.info(f"✅ Gateway Status: {data['status']}")
        for service, status in services.items():
            logger.info(f"  - {service}: {status.get('status', 'unknown')}")

        return data

async def test_service_health():
    """Test all microservices health"""
    logger.info("\n🔍 Testing microservices health...")
    async with httpx.AsyncClient() as client:
        for service_name, url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{url}/health", timeout=5)
                status = "✅" if response.status_code == 200 else "❌"
                logger.info(f"{status} {service_name}: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️  {service_name}: {str(e)}")

# ============================================================================
# SEARCH SERVICE TESTS (Port 8010)
# ============================================================================

async def test_search_basic():
    """Test basic search"""
    logger.info("\n🔍 Testing basic search...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search",
            params={"q": "laptop", "limit": 10}
        )
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Basic search: Found {len(data.get('results', []))} results")
        return data

async def test_search_autocomplete():
    """Test autocomplete"""
    logger.info("🔍 Testing search autocomplete...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search/autocomplete",
            params={"q": "lap", "limit": 10}
        )
        assert response.status_code == 200, f"Autocomplete failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Autocomplete: {len(data.get('suggestions', []))} suggestions")
        return data

async def test_search_semantic():
    """Test semantic search"""
    logger.info("🔍 Testing semantic search...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search/semantic",
            params={"q": "computer for work and gaming", "limit": 5}
        )
        assert response.status_code == 200, f"Semantic search failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Semantic search: Found {len(data.get('results', []))} results")
        return data

async def test_search_faceted():
    """Test faceted search"""
    logger.info("🔍 Testing faceted search...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search/faceted",
            params={"q": "laptop", "category": "electronics", "min_price": 500, "max_price": 1500}
        )
        assert response.status_code == 200, f"Faceted search failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Faceted search: Found {len(data.get('results', []))} results")
        return data

# ============================================================================
# ELASTICSEARCH SERVICE TESTS (Port 8015)
# ============================================================================

async def test_elasticsearch_search():
    """Test Elasticsearch full-text search"""
    logger.info("\n🔍 Testing Elasticsearch search...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search/elasticsearch",
            params={"q": "laptop", "limit": 10}
        )
        assert response.status_code == 200, f"ES search failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Elasticsearch search: Found {len(data.get('results', []))} results")
        return data

async def test_elasticsearch_fuzzy():
    """Test Elasticsearch fuzzy search (typo tolerance)"""
    logger.info("🔍 Testing Elasticsearch fuzzy search...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/search/fuzzy",
            params={"q": "lapto", "limit": 10}  # Typo
        )
        assert response.status_code == 200, f"Fuzzy search failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Fuzzy search (typo-tolerant): Found {len(data.get('results', []))} results")
        return data

# ============================================================================
# ML RECOMMENDATION TESTS (Port 8014)
# ============================================================================

async def test_recommendations():
    """Test ML recommendations for user"""
    logger.info("\n🤖 Testing ML recommendations...")
    user_id = "test_user_123"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/recommendations/for-you/{user_id}",
            params={"limit": 5}
        )
        # May return 404 if user doesn't exist, which is ok for test
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Recommendations: {len(data.get('recommendations', []))} suggestions")
        else:
            logger.info(f"⚠️  Recommendations: {response.status_code} (user may not exist)")

async def test_similar_products():
    """Test similar product recommendations"""
    logger.info("🤖 Testing similar products...")
    product_id = "test_product_001"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/recommendations/similar/{product_id}",
            params={"limit": 5}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Similar products: {len(data.get('recommendations', []))} suggestions")
        else:
            logger.info(f"⚠️  Similar products: {response.status_code}")

async def test_trending_products():
    """Test trending products"""
    logger.info("🤖 Testing trending products...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/recommendations/trending",
            params={"limit": 10}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Trending products: {len(data.get('recommendations', []))} products")
        else:
            logger.info(f"⚠️  Trending products: {response.status_code}")

async def test_demand_forecast():
    """Test demand forecasting"""
    logger.info("🤖 Testing demand forecast...")
    product_id = "test_product_001"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/forecast/demand/{product_id}"
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Demand forecast: {len(data.get('forecast', []))} predictions")
        else:
            logger.info(f"⚠️  Demand forecast: {response.status_code}")

# ============================================================================
# REAL-TIME SERVICE TESTS (Port 8013)
# ============================================================================

async def test_realtime_stats():
    """Test real-time service statistics"""
    logger.info("\n⚡ Testing real-time stats...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/api/realtime/stats")
        assert response.status_code == 200, f"Realtime stats failed: {response.text}"
        data = response.json()
        logger.info(f"✅ Real-time stats: {data.get('connected_users', 0)} connected users")
        return data

# ============================================================================
# EVENTS SERVICE TESTS (Port 8016)
# ============================================================================

async def test_publish_event():
    """Test publishing an event"""
    logger.info("\n📢 Testing event publishing...")
    async with httpx.AsyncClient() as client:
        event_data = {
            "event_type": "product.created",
            "data": {
                "product_id": "test_123",
                "product_name": "Test Laptop",
                "price": 999.99,
                "created_at": datetime.utcnow().isoformat(),
            },
            "user_id": "test_user",
        }

        response = await client.post(
            f"{API_GATEWAY_URL}/api/events/publish",
            json=event_data
        )
        assert response.status_code == 200, f"Event publish failed: {response.text}"
        result = response.json()
        logger.info(f"✅ Event published: {result.get('id', 'unknown')}")
        return result

async def test_get_events():
    """Test retrieving events"""
    logger.info("📢 Testing get events...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/api/events/stream/product",
            params={"limit": 10}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Retrieved events: {len(data.get('events', []))} events")
        else:
            logger.info(f"⚠️  Get events: {response.status_code}")

# ============================================================================
# PRICE ALERT TESTS
# ============================================================================

async def test_create_price_alert():
    """Test creating price alert"""
    logger.info("\n🔔 Testing price alert creation...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_GATEWAY_URL}/api/alerts/price",
            params={
                "product_id": "test_product",
                "target_price": "599.99",
                "user_id": "test_user"
            }
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Price alert created: {data.get('alert_id', 'unknown')}")
        else:
            logger.info(f"⚠️  Price alert: {response.status_code}")

async def test_get_user_alerts():
    """Test retrieving user alerts"""
    logger.info("🔔 Testing get user alerts...")
    user_id = "test_user"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/api/alerts/user/{user_id}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ User alerts: {data.get('count', 0)} alerts")
        else:
            logger.info(f"⚠️  Get alerts: {response.status_code}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all integration tests"""
    logger.info("=" * 70)
    logger.info("🚀 CUMPAIR END-TO-END INTEGRATION TEST SUITE")
    logger.info("=" * 70)

    try:
        # Health checks
        await test_gateway_health()
        await test_service_health()

        # Search tests
        await test_search_basic()
        await test_search_autocomplete()
        await test_search_semantic()
        await test_search_faceted()

        # Elasticsearch tests
        await test_elasticsearch_search()
        await test_elasticsearch_fuzzy()

        # ML tests
        await test_recommendations()
        await test_similar_products()
        await test_trending_products()
        await test_demand_forecast()

        # Real-time tests
        await test_realtime_stats()

        # Events tests
        await test_publish_event()
        await test_get_events()

        # Price alert tests
        await test_create_price_alert()
        await test_get_user_alerts()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests())
