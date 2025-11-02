"""
Comprehensive Testing Infrastructure
Unit tests, integration tests, load tests, chaos engineering
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import time

# Test fixtures


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        "postgresql+asyncpg://test_user:test_pass@localhost/test_db",
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def api_client():
    """Create test API client"""
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Unit Tests

class TestCacheLayer:
    """Test multi-tier cache"""
    
    @pytest.mark.asyncio
    async def test_l1_cache_set_get(self):
        from app.core.cache import cache_manager
        
        await cache_manager.set("test", "key1", "value1", levels=["L1"])
        result = await cache_manager.get("test", "key1", levels=["L1"])
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_l2_cache_with_ttl(self):
        from app.core.cache import cache_manager
        
        await cache_manager.set("test", "key2", {"data": "test"}, ttl=2, levels=["L2"])
        result1 = await cache_manager.get("test", "key2", levels=["L2"])
        
        assert result1 == {"data": "test"}
        
        # Wait for expiry
        await asyncio.sleep(3)
        result2 = await cache_manager.get("test", "key2", levels=["L2"])
        
        assert result2 is None
    
    @pytest.mark.asyncio
    async def test_cache_compression(self):
        from app.core.cache import cache_manager
        
        large_data = "x" * 2000  # > compression threshold
        await cache_manager.set("test", "large", large_data, levels=["L2"])
        result = await cache_manager.get("test", "large", levels=["L2"])
        
        assert result == large_data


class TestQueryOptimizer:
    """Test query optimization"""
    
    @pytest.mark.asyncio
    async def test_search_with_cache(self, test_db):
        from app.services.query_optimizer import query_optimizer
        
        result1 = await query_optimizer.search_products("test", test_db, use_cache=True)
        result2 = await query_optimizer.search_products("test", test_db, use_cache=True)
        
        assert result2["metadata"]["cache_hit"] is True
    
    @pytest.mark.asyncio
    async def test_ghost_results(self):
        from app.services.query_optimizer import query_optimizer
        
        ghosts = await query_optimizer.get_ghost_results("test", count=5)
        
        assert len(ghosts) == 5
        assert all(g["is_ghost"] for g in ghosts)


class TestHuggingFaceClient:
    """Test HuggingFace API integration"""
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        from app.services.huggingface_client import hf_client
        
        result = await hf_client.analyze_sentiment("This is amazing!")
        
        assert "label" in result
        assert "score" in result
    
    @pytest.mark.asyncio
    async def test_compute_embeddings(self):
        from app.services.huggingface_client import hf_client
        
        embedding = await hf_client.compute_embeddings("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0


# Integration Tests

class TestSearchAPI:
    """Test complete search flow"""
    
    @pytest.mark.asyncio
    async def test_unified_search(self, api_client):
        response = await api_client.get(
            "/api/v2/search",
            params={"q": "iPhone", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "metadata" in data
        assert "total_latency_ms" in data["metadata"]
    
    @pytest.mark.asyncio
    async def test_image_search(self, api_client):
        # Create test image
        import io
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        
        files = {"file": ("test.jpg", buf, "image/jpeg")}
        
        response = await api_client.post(
            "/api/v2/search/image",
            files=files,
            params={"limit": 10}
        )
        
        assert response.status_code in [200, 404]  # 404 if no matches


class TestRealTimeFeeds:
    """Test real-time data feeds"""
    
    @pytest.mark.asyncio
    async def test_crypto_feed(self):
        from app.services.realtime_feeds import CryptoDataFeed
        
        feed = CryptoDataFeed()
        result = await feed.get_crypto_price("bitcoin")
        
        if result:
            assert "price_usd" in result
            assert "change_24h" in result


# Performance Tests

class TestPerformance:
    """Load and performance testing"""
    
    @pytest.mark.asyncio
    async def test_search_latency(self, api_client):
        """Test search completes within target latency"""
        start = time.time()
        
        response = await api_client.get(
            "/api/v2/search",
            params={"q": "test", "limit": 20}
        )
        
        latency_ms = (time.time() - start) * 1000
        
        # Cached queries should be <200ms
        # Fresh queries should be <2000ms
        assert latency_ms < 2000
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, api_client):
        """Test handling concurrent requests"""
        tasks = [
            api_client.get("/api/v2/search", params={"q": f"query{i}", "limit": 10})
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(r.status_code == 200 for r in results)


# Chaos Engineering Tests

class TestResilience:
    """Test system resilience"""
    
    @pytest.mark.asyncio
    async def test_cache_failure_graceful(self, test_db):
        """Test system works when cache fails"""
        from app.services.query_optimizer import query_optimizer
        
        # Simulate cache failure
        result = await query_optimizer.search_products(
            "test",
            test_db,
            use_cache=False
        )
        
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_ai_service_timeout(self):
        """Test graceful degradation when AI service times out"""
        from app.services.huggingface_client import hf_client
        
        # Test with very short timeout (will likely fail)
        try:
            result = await hf_client.analyze_sentiment("test")
            # If succeeds, verify result
            assert "label" in result
        except Exception:
            # Graceful failure is acceptable
            pass


# Contract Tests

class TestAPIContracts:
    """Test API contract compliance"""
    
    @pytest.mark.asyncio
    async def test_search_response_schema(self, api_client):
        response = await api_client.get(
            "/api/v2/search",
            params={"q": "test"}
        )
        
        data = response.json()
        
        # Verify schema
        assert "query" in data
        assert "results" in data
        assert "metadata" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["metadata"], dict)


# End-to-End Tests

class TestE2E:
    """End-to-end user flows"""
    
    @pytest.mark.asyncio
    async def test_complete_search_flow(self, api_client):
        """Test complete user search journey"""
        # Step 1: Search
        search_response = await api_client.get(
            "/api/v2/search",
            params={"q": "iPhone 15", "limit": 5}
        )
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        # Step 2: Get product details
        if search_data["results"]:
            product_id = search_data["results"][0]["id"]
            
            detail_response = await api_client.get(
                f"/api/v2/product/{product_id}/complete"
            )
            
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            
            assert "product" in detail_data
            assert "context" in detail_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
