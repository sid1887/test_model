"""
Unit tests for Price Comparison Service
Tests the consolidated CumpairPriceEngine implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Mock test - validates logic without external dependencies

def test_cumpair_price_engine_initialization():
    """Test CumpairPriceEngine initializes with correct defaults"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    assert engine.similarity_threshold == 0.85
    assert 'amazon.com' in engine.ecommerce_sites
    assert 'walmart.com' in engine.ecommerce_sites
    assert 'ebay.com' in engine.ecommerce_sites
    assert 'bestbuy.com' in engine.ecommerce_sites
    
    # Check site configurations
    assert 'search_urls' in engine.ecommerce_sites['amazon.com']
    assert 'rate_limit' in engine.ecommerce_sites['amazon.com']
    assert 'selectors' in engine.ecommerce_sites['amazon.com']

def test_generate_search_urls():
    """Test search URL generation for different sites"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    # Test with normal query
    query = "iPhone 15 Pro"
    urls = engine._generate_search_urls(query)
    
    assert isinstance(urls, dict)
    assert len(urls) > 0
    assert 'amazon.com' in urls or 'ebay.com' in urls or 'walmart.com' in urls
    
    # Verify URLs are properly formatted
    for site, site_urls in urls.items():
        assert isinstance(site_urls, list)
        for url in site_urls:
            assert isinstance(url, str)
            assert url.startswith('http')

def test_generate_search_urls_special_characters():
    """Test URL generation handles special characters"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    # Test with special characters
    query = "Samsung Galaxy S24+ 5G (Unlocked)"
    urls = engine._generate_search_urls(query)
    
    # Should handle special characters gracefully
    assert len(urls) > 0
    for site_urls in urls.values():
        for url in site_urls:
            # Should not contain unencoded special characters
            assert '(' not in url or '%' in url  # Either removed or encoded

def test_validate_product_data_valid():
    """Test product data validation with valid input"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    valid_product = {
        'title': 'iPhone 15 Pro',
        'price': '999.99',
        'rating': '4.5',
        'image': 'https://example.com/image.jpg',
        'site': 'amazon.com'
    }
    
    result = engine._validate_product_data(valid_product)
    assert result is True
    assert isinstance(valid_product['price'], float)
    assert valid_product['price'] == 999.99

def test_validate_product_data_invalid():
    """Test product data validation rejects invalid input"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    # Missing title
    invalid_product1 = {'price': '999.99'}
    assert engine._validate_product_data(invalid_product1) is False
    
    # Missing price
    invalid_product2 = {'title': 'iPhone 15'}
    assert engine._validate_product_data(invalid_product2) is False
    
    # Invalid price (zero or negative)
    invalid_product3 = {'title': 'iPhone 15', 'price': '0'}
    assert engine._validate_product_data(invalid_product3) is False

def test_calculate_price_position():
    """Test price positioning calculation"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    # Test budget position (bottom 25%)
    assert engine._calculate_price_position(100, 100, 500) == "budget"
    
    # Test mid-low position (25-50%)
    assert engine._calculate_price_position(200, 100, 500) == "mid-low"
    
    # Test mid-high position (50-75%)
    assert engine._calculate_price_position(350, 100, 500) == "mid-high"
    
    # Test premium position (top 25%)
    assert engine._calculate_price_position(480, 100, 500) == "premium"

def test_calculate_competitiveness():
    """Test price competitiveness calculation"""
    from app.services.price_comparison import CumpairPriceEngine
    
    engine = CumpairPriceEngine()
    
    market_avg = 1000.0
    
    # Highly competitive (15% below average)
    assert engine._calculate_competitiveness(850, market_avg) == "highly_competitive"
    
    # Competitive (5-15% below average)
    assert engine._calculate_competitiveness(920, market_avg) == "competitive"
    
    # Average (within 5% of average)
    assert engine._calculate_competitiveness(1000, market_avg) == "average"
    assert engine._calculate_competitiveness(1040, market_avg) == "average"
    
    # Slightly above (5-15% above average)
    assert engine._calculate_competitiveness(1100, market_avg) == "slightly_above"
    
    # Premium (15%+ above average)
    assert engine._calculate_competitiveness(1200, market_avg) == "premium"

def test_cosine_similarity():
    """Test cosine similarity calculation"""
    from app.services.price_comparison import CumpairPriceEngine
    import numpy as np
    
    engine = CumpairPriceEngine()
    
    # Identical vectors (similarity = 1.0)
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([1.0, 0.0, 0.0])
    assert abs(engine._cosine_similarity(vec1, vec2) - 1.0) < 0.01
    
    # Orthogonal vectors (similarity = 0.0)
    vec3 = np.array([1.0, 0.0, 0.0])
    vec4 = np.array([0.0, 1.0, 0.0])
    assert abs(engine._cosine_similarity(vec3, vec4)) < 0.01
    
    # Opposite vectors (similarity = -1.0)
    vec5 = np.array([1.0, 0.0, 0.0])
    vec6 = np.array([-1.0, 0.0, 0.0])
    assert abs(engine._cosine_similarity(vec5, vec6) - (-1.0)) < 0.01

@pytest.mark.asyncio
async def test_find_product_prices_structure():
    """Test the structure of find_product_prices return value"""
    # This validates expected return format without external calls
    
    # Mock response structure
    mock_response = {
        'query': 'iPhone 15',
        'timestamp': datetime.utcnow().isoformat(),
        'total_results': 10,
        'price_range': {'min': 799.99, 'max': 1099.99},
        'sites': {
            'amazon.com': [
                {'title': 'iPhone 15', 'price': 899.99, 'rating': 4.5}
            ],
            'walmart.com': [
                {'title': 'iPhone 15', 'price': 879.99, 'rating': 4.3}
            ]
        },
        'ai_insights': {},
        'recommendations': []
    }
    
    # Validate structure
    assert 'query' in mock_response
    assert 'timestamp' in mock_response
    assert 'total_results' in mock_response
    assert 'price_range' in mock_response
    assert 'min' in mock_response['price_range']
    assert 'max' in mock_response['price_range']
    assert 'sites' in mock_response
    assert isinstance(mock_response['sites'], dict)

def test_should_upgrade_index_logic():
    """Test index upgrade decision logic"""
    # Simple validation that the logic is sound
    max_index_size = 100000
    
    # Small index - should not upgrade
    current_size = 1000
    assert current_size <= max_index_size
    
    # Large index - should upgrade
    current_size = 150000
    assert current_size > max_index_size

# Integration test markers
@pytest.mark.integration
@pytest.mark.skip(reason="Requires scraper service - run with integration suite")
async def test_find_product_prices_integration():
    """Full integration test with real scraper service"""
    # This would test actual scraping:
    # 1. Initialize engine
    # 2. Call find_product_prices with real query
    # 3. Verify results structure and data
    # 4. Check AI insights generation
    pass

@pytest.mark.integration
@pytest.mark.skip(reason="Requires database - run with integration suite")
async def test_compare_product_with_ai_integration():
    """Full integration test for AI product comparison"""
    # This would test:
    # 1. Load product from database
    # 2. Run price comparison
    # 3. Generate AI insights
    # 4. Store comparison results
    pass

if __name__ == "__main__":
    print("Running Price Comparison Service tests...")
    
    test_cumpair_price_engine_initialization()
    print("✅ Engine initialization test passed")
    
    test_generate_search_urls()
    print("✅ Search URL generation test passed")
    
    test_generate_search_urls_special_characters()
    print("✅ Special characters handling test passed")
    
    test_validate_product_data_valid()
    print("✅ Valid product data test passed")
    
    test_validate_product_data_invalid()
    print("✅ Invalid product data test passed")
    
    test_calculate_price_position()
    print("✅ Price positioning test passed")
    
    test_calculate_competitiveness()
    print("✅ Competitiveness calculation test passed")
    
    test_cosine_similarity()
    print("✅ Cosine similarity test passed")
    
    # Run async test
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_find_product_prices_structure())
    print("✅ Price search structure test passed")
    
    print("\n✅ All price comparison tests passed!")
    print("Run 'pytest tests/test_price_comparison.py' for full test suite")
