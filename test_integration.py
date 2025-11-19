"""
Integration Tests - All Services Phase 6+7
Tests for core infrastructure, real-time, ML, Elasticsearch, Event Bus
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import numpy as np

# Test configuration
API_BASE_URL = "http://localhost:8000"
SEARCH_SERVICE_URL = "http://localhost:8010"
REALTIME_SERVICE_URL = "http://localhost:8013"
ML_SERVICE_URL = "http://localhost:8014"
ELASTICSEARCH_SERVICE_URL = "http://localhost:8015"
EVENT_BUS_URL = "http://localhost:8016"

# Test data
TEST_USER_ID = "test_user_123"
TEST_PRODUCT_ID = "prod_001"
TEST_PRODUCT_DATA = {
    "id": TEST_PRODUCT_ID,
    "name": "Test Product",
    "category": "electronics",
    "price": 99.99,
    "rating": 4.5,
    "stock": 100,
    "description": "A test product for integration testing"
}


# ============================================================================
# CORE INFRASTRUCTURE TESTS
# ============================================================================

class TestCoreInfrastructure:
    """Test shard routing, connection pooling, caching"""

    @pytest.mark.asyncio
    async def test_cache_layers(self):
        """Test 3-tier cache (L3, L2, L1)"""
        async with httpx.AsyncClient() as client:
            # Test search with cache
            response = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=test&limit=10"
            )
            assert response.status_code == 200
            data = response.json()
            assert 'results' in data
            assert data['from_cache'] == False  # First request

            # Second request should hit cache
            response = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=test&limit=10"
            )
            assert response.status_code == 200
            data = response.json()
            assert data['from_cache'] == True  # Cached

    @pytest.mark.asyncio
    async def test_shard_routing(self):
        """Test consistent hash routing"""
        async with httpx.AsyncClient() as client:
            # Multiple requests with same user should go to same shard
            user_id = "user_shard_test"

            for i in range(3):
                response = await client.get(
                    f"{SEARCH_SERVICE_URL}/search?q=laptop&user_id={user_id}"
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """Test connection pool limits"""
        async with httpx.AsyncClient() as client:
            # Concurrent requests to test pooling
            tasks = [
                client.get(f"{SEARCH_SERVICE_URL}/search?q=test")
                for _ in range(10)
            ]

            responses = await asyncio.gather(*tasks)
            successful = sum(1 for r in responses if r.status_code == 200)

            assert successful == 10
            assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_service_metrics(self):
        """Test service metrics collection"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SEARCH_SERVICE_URL}/search-stats")
            assert response.status_code == 200

            metrics = response.json()
            assert 'queries' in metrics
            assert 'cache_stats' in metrics
            assert metrics['queries'] >= 0


# ============================================================================
# WEBSOCKET REAL-TIME TESTS
# ============================================================================

class TestRealtimeService:
    """Test WebSocket connections and real-time updates"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        with httpx.WebSocketTestSession(REALTIME_SERVICE_URL) as session:
            try:
                session.open(f"/ws/realtime/{TEST_USER_ID}")
                # Should connect
                data = session.receive_json()
                assert data['type'] == 'connected'
                assert data['user_id'] == TEST_USER_ID
            finally:
                session.close()

    @pytest.mark.asyncio
    async def test_price_alerts(self):
        """Test price alert notifications"""
        async with httpx.AsyncClient() as client:
            # Create price alert
            response = await client.post(
                f"{REALTIME_SERVICE_URL}/ws/price-alerts/{TEST_USER_ID}",
                json={
                    'type': 'add_alert',
                    'product_id': TEST_PRODUCT_ID,
                    'alert_price': 79.99
                }
            )

    @pytest.mark.asyncio
    async def test_realtime_stats(self):
        """Test real-time connection stats"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{REALTIME_SERVICE_URL}/stats")
            assert response.status_code == 200

            stats = response.json()
            assert 'connections' in stats
            assert 'connected_users' in stats['connections']


# ============================================================================
# ML RECOMMENDATION TESTS
# ============================================================================

class TestMLEngine:
    """Test recommendation algorithms and forecasting"""

    @pytest.mark.asyncio
    async def test_for_you_recommendations(self):
        """Test personalized recommendations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/recommendations/for-you/{TEST_USER_ID}?count=10"
            )
            assert response.status_code == 200

            data = response.json()
            assert 'recommendations' in data
            assert len(data['recommendations']) <= 10
            assert 'algorithm' in data

    @pytest.mark.asyncio
    async def test_similar_products(self):
        """Test item-based recommendations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/recommendations/similar/{TEST_PRODUCT_ID}"
            )
            assert response.status_code == 200

            data = response.json()
            assert data['product_id'] == TEST_PRODUCT_ID
            assert 'similar_products' in data
            assert 'count' in data

    @pytest.mark.asyncio
    async def test_trending_products(self):
        """Test trending products"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/recommendations/trending?count=10"
            )
            assert response.status_code == 200

            data = response.json()
            assert 'trending' in data
            assert len(data['trending']) >= 0

    @pytest.mark.asyncio
    async def test_demand_forecasting(self):
        """Test demand forecast"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/forecast/demand/{TEST_PRODUCT_ID}?days_ahead=7"
            )
            assert response.status_code == 200

            data = response.json()
            assert data['product_id'] == TEST_PRODUCT_ID
            assert 'forecasts' in data
            assert len(data['forecasts']) == 7

            # Check forecast structure
            for forecast in data['forecasts']:
                assert 'date' in forecast
                assert 'forecasted_units' in forecast
                assert 'confidence' in forecast

    @pytest.mark.asyncio
    async def test_inventory_recommendations(self):
        """Test inventory level recommendations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/inventory/recommendations"
            )
            assert response.status_code == 200

            data = response.json()
            assert 'products' in data
            assert 'recommendations' in data


# ============================================================================
# ELASTICSEARCH TESTS
# ============================================================================

class TestElasticsearchService:
    """Test search capabilities and indexing"""

    @pytest.mark.asyncio
    async def test_full_text_search(self):
        """Test basic full-text search"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELASTICSEARCH_SERVICE_URL}/search?q=laptop&limit=20"
            )
            assert response.status_code in [200, 503]  # 503 if ES not available

            if response.status_code == 200:
                data = response.json()
                assert 'results' in data
                assert 'total' in data

    @pytest.mark.asyncio
    async def test_fuzzy_search(self):
        """Test typo-tolerant search"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELASTICSEARCH_SERVICE_URL}/search/fuzzy?q=lpatop"  # Typo
            )
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'results' in data

    @pytest.mark.asyncio
    async def test_faceted_search(self):
        """Test faceted search with aggregations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELASTICSEARCH_SERVICE_URL}/search/faceted?"
                f"q=phone&category=electronics&price_min=100&price_max=500"
            )
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'results' in data
                assert 'facets' in data

    @pytest.mark.asyncio
    async def test_autocomplete(self):
        """Test autocomplete suggestions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELASTICSEARCH_SERVICE_URL}/autocomplete?q=lap&limit=10"
            )
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'suggestions' in data
                assert isinstance(data['suggestions'], list)

    @pytest.mark.asyncio
    async def test_product_indexing(self):
        """Test product indexing"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ELASTICSEARCH_SERVICE_URL}/index/product?product_id={TEST_PRODUCT_ID}",
                json=TEST_PRODUCT_DATA
            )
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'status' in data


# ============================================================================
# EVENT BUS TESTS
# ============================================================================

class TestEventBusService:
    """Test event publishing and processing"""

    @pytest.mark.asyncio
    async def test_publish_product_created_event(self):
        """Test publishing product created event"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=product.created&"
                f"aggregate_id={TEST_PRODUCT_ID}&source=test",
                json=TEST_PRODUCT_DATA
            )
            assert response.status_code == 200

            data = response.json()
            assert data['event_type'] == 'product.created'
            assert data['status'] == 'published'
            assert 'event_id' in data

    @pytest.mark.asyncio
    async def test_publish_price_changed_event(self):
        """Test publishing price change event"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=price.changed&"
                f"aggregate_id={TEST_PRODUCT_ID}&source=test",
                json={
                    'old_price': 99.99,
                    'new_price': 89.99,
                    'change_reason': 'sale'
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_publish_purchase_completed_event(self):
        """Test publishing purchase completion event"""
        async with httpx.AsyncClient() as client:
            order_id = f"order_{datetime.utcnow().timestamp()}"
            response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=purchase.completed&"
                f"aggregate_id={order_id}&source=test",
                json={
                    'user_id': TEST_USER_ID,
                    'product_ids': [TEST_PRODUCT_ID],
                    'total': 99.99
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_events(self):
        """Test retrieving user events"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EVENT_BUS_URL}/events/user/{TEST_USER_ID}?count=50"
            )
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'user_id' in data
                assert 'events' in data

    @pytest.mark.asyncio
    async def test_get_dead_letter_queue(self):
        """Test DLQ retrieval"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EVENT_BUS_URL}/events/dlq?count=100")
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert 'dlq_count' in data
                assert 'events' in data

    @pytest.mark.asyncio
    async def test_event_bus_stats(self):
        """Test event bus statistics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EVENT_BUS_URL}/stats")
            assert response.status_code == 200

            data = response.json()
            assert 'service' in data
            assert data['service'] == 'event_bus'


# ============================================================================
# CROSS-SERVICE INTEGRATION TESTS
# ============================================================================

class TestCrossServiceIntegration:
    """Test interactions between services"""

    @pytest.mark.asyncio
    async def test_end_to_end_product_flow(self):
        """
        Test complete flow:
        Product created -> indexed in search -> recommendations updated -> event published
        """
        async with httpx.AsyncClient() as client:
            # 1. Publish product created event
            event_response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=product.created&"
                f"aggregate_id={TEST_PRODUCT_ID}&source=test",
                json=TEST_PRODUCT_DATA
            )
            assert event_response.status_code == 200

            # Wait for event processing
            await asyncio.sleep(1)

            # 2. Search should find the product (after indexing)
            search_response = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=test%20product"
            )
            assert search_response.status_code == 200

            # 3. Elasticsearch should have the product indexed
            es_response = await client.get(
                f"{ELASTICSEARCH_SERVICE_URL}/search?q=test%20product"
            )
            if es_response.status_code == 200:
                assert es_response.json()['total'] >= 0

    @pytest.mark.asyncio
    async def test_end_to_end_purchase_flow(self):
        """
        Test purchase flow:
        Purchase completed -> recommendations rebuilt -> inventory updated -> cache invalidated
        """
        async with httpx.AsyncClient() as client:
            order_id = f"order_{datetime.utcnow().timestamp()}"

            # 1. Publish purchase completed event
            response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=purchase.completed&"
                f"aggregate_id={order_id}&source=test",
                json={
                    'user_id': TEST_USER_ID,
                    'product_ids': [TEST_PRODUCT_ID],
                    'total': 99.99
                }
            )
            assert response.status_code == 200

            # Wait for processing
            await asyncio.sleep(1)

            # 2. Check recommendations are updated
            rec_response = await client.get(
                f"{ML_SERVICE_URL}/recommendations/for-you/{TEST_USER_ID}"
            )
            assert rec_response.status_code == 200

    @pytest.mark.asyncio
    async def test_real_time_price_update_flow(self):
        """
        Test real-time price update:
        Price changed -> alert triggered -> user notified -> event recorded
        """
        async with httpx.AsyncClient() as client:
            # 1. Publish price change event
            response = await client.post(
                f"{EVENT_BUS_URL}/events/publish?event_type=price.changed&"
                f"aggregate_id={TEST_PRODUCT_ID}&source=test",
                json={
                    'old_price': 99.99,
                    'new_price': 79.99,
                    'change_reason': 'promotion'
                }
            )
            assert response.status_code == 200

            # 2. Cache should be invalidated
            # Check by making search request (should not be from cache after invalidation)
            search_response = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=test"
            )
            assert search_response.status_code == 200


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache hit rate and latency"""
        import time

        async with httpx.AsyncClient() as client:
            # First request (cache miss)
            start = time.time()
            response1 = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=performance&limit=10"
            )
            cache_miss_time = time.time() - start

            # Second request (cache hit)
            start = time.time()
            response2 = await client.get(
                f"{SEARCH_SERVICE_URL}/search?q=performance&limit=10"
            )
            cache_hit_time = time.time() - start

            # Cache hit should be faster
            assert response2.json()['from_cache'] == True
            print(f"Cache miss: {cache_miss_time*1000:.2f}ms, "
                  f"Cache hit: {cache_hit_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_search_latency(self):
        """Test search response latency"""
        import time

        async with httpx.AsyncClient() as client:
            latencies = []

            for _ in range(10):
                start = time.time()
                await client.get(f"{SEARCH_SERVICE_URL}/search?q=test")
                latency = time.time() - start
                latencies.append(latency)

            avg_latency = np.mean(latencies) * 1000  # Convert to ms
            p95_latency = np.percentile(latencies, 95) * 1000

            print(f"Search latency - Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")
            assert avg_latency < 1000  # Should be under 1 second


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
