#!/usr/bin/env python3
"""
Scrapy Service Wrapper - Standalone integration layer
Provides high-level search endpoints that integrate Scrapy with other services
Runs on port 7000 as a demonstration of integration capabilities
"""

from flask import Flask, request, jsonify
import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scrapy service URL - use localhost when running outside Docker
import os
SCRAPY_URL = os.getenv('SCRAPY_URL', 'http://localhost:5000')

class ScrapyIntegration:
    """Integration layer for Scrapy service"""

    def __init__(self):
        self.scrapy_url = SCRAPY_URL
        logger.info(f"Using Scrapy service at: {self.scrapy_url}")
        self.cache = {}
        self.stats = {
            'total_searches': 0,
            'total_products': 0,
            'avg_response_time': 0
        }

    def search(self, query: str, retailers: Optional[List[str]] = None, use_cache: bool = True) -> Dict:
        """Search with optional caching"""
        import time
        start = time.time()

        # Check cache
        cache_key = f"{query}:{'|'.join(sorted(retailers or []))}"
        if use_cache and cache_key in self.cache:
            logger.info(f"Cache HIT for {cache_key}")
            return self.cache[cache_key]

        try:
            # Call Scrapy service
            payload = {
                'query': query,
                'sites': retailers or ['amazon', 'walmart', 'ebay']
            }

            response = requests.post(
                f"{self.scrapy_url}/api/search",
                json=payload,
                timeout=120
            )

            if response.status_code != 200:
                logger.error(f"Scrapy error: {response.status_code}")
                return {'error': 'Scrapy service error', 'status': 'error'}

            result = response.json()
            elapsed = time.time() - start

            # Add metadata
            result['response_time'] = elapsed
            result['cached'] = False
            result['timestamp'] = datetime.now().isoformat()

            # Update stats
            self.stats['total_searches'] += 1
            self.stats['total_products'] += result.get('total_products', 0)

            # Cache result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'error': str(e), 'status': 'error'}

    def get_retailers(self) -> Dict:
        """Get supported retailers"""
        try:
            response = requests.get(f"{self.scrapy_url}/api/retailers", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {'error': 'Could not fetch retailers', 'retailers': []}
        except Exception as e:
            logger.error(f"Get retailers error: {e}")
            return {'error': str(e), 'retailers': []}

    def bulk_search(self, queries: List[str], retailers: Optional[List[str]] = None) -> Dict:
        """Bulk search across multiple queries"""
        try:
            payload = {
                'queries': queries,
                'retailers': retailers or ['amazon', 'walmart', 'ebay']
            }

            response = requests.post(
                f"{self.scrapy_url}/api/search/bulk",
                json=payload,
                timeout=30
            )

            if response.status_code == 202:
                return response.json()
            return {'error': 'Bulk search failed', 'status': 'error'}

        except Exception as e:
            logger.error(f"Bulk search error: {e}")
            return {'error': str(e), 'status': 'error'}

# Initialize integration layer
integration = ScrapyIntegration()

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'scrapy-integration',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query')
        retailers = data.get('retailers')
        use_cache = data.get('cache', True)

        if not query:
            return jsonify({'error': 'Query required'}), 400

        result = integration.search(query, retailers, use_cache)

        status_code = 200 if result.get('status') != 'error' else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/retailers', methods=['GET'])
def get_retailers():
    """Get supported retailers"""
    return jsonify(integration.get_retailers())

@app.route('/api/bulk-search', methods=['POST'])
def bulk_search():
    """Bulk search endpoint"""
    try:
        data = request.get_json()
        queries = data.get('queries', [])
        retailers = data.get('retailers')

        if not queries:
            return jsonify({'error': 'Queries required'}), 400

        result = integration.bulk_search(queries, retailers)

        status_code = 202 if result.get('status') != 'error' else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Bulk search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Service statistics"""
    stats_data = integration.stats.copy()
    stats_data['cache_size'] = len(integration.cache)
    stats_data['avg_response_time'] = (
        stats_data['total_products'] / max(stats_data['total_searches'], 1)
    )
    return jsonify(stats_data)

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache"""
    integration.cache.clear()
    return jsonify({'status': 'cache cleared'})

# ============================================================================
# ADVANCED INTEGRATION EXAMPLES
# ============================================================================

@app.route('/api/search/advanced', methods=['POST'])
def search_advanced():
    """
    Advanced search with optional features:
    - Price filtering
    - Result ranking
    - Deduplication
    """
    try:
        data = request.get_json()
        query = data.get('query')
        retailers = data.get('retailers')
        min_price = data.get('min_price', 0)
        max_price = data.get('max_price', float('inf'))
        rank_by = data.get('rank_by', 'relevance')  # price, relevance

        # Get base results
        result = integration.search(query, retailers)

        if result.get('status') == 'error':
            return jsonify(result), 500

        # Filter by price
        products = result.get('products', [])
        filtered = []

        for product in products:
            price_str = product.get('price', 'N/A').replace(',', '')
            try:
                price = float(price_str) if price_str != 'N/A' else None
                if price is None or (min_price <= price <= max_price):
                    filtered.append(product)
            except:
                filtered.append(product)  # Keep if price unparseable

        # Rank results
        if rank_by == 'price':
            filtered.sort(key=lambda x: float(x.get('price', '999999').replace(',', ''))
                         if x.get('price') != 'N/A' else 999999)

        result['products'] = filtered
        result['filtered_count'] = len(filtered)
        result['total_count'] = len(products)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=7000,
        debug=False
    )
