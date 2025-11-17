#!/usr/bin/env python3
"""
Unit tests for Scrapy API endpoints
Tests the Flask app directly without requiring external services
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
import json
from datetime import datetime

# Mock Redis before importing the app
class MockRedis:
    def __init__(self):
        self.data = {}
    
    def ping(self):
        return True
    
    def hset(self, key, mapping=None, **kwargs):
        if mapping:
            self.data[key] = mapping
        return True
    
    def rpush(self, key, *values):
        if key not in self.data:
            self.data[key] = []
        self.data[key].extend(values)
        return len(self.data[key])
    
    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
        return len(keys)
    
    def expire(self, key, seconds):
        return True
    
    def hgetall(self, key):
        return self.data.get(key, {})
    
    def lrange(self, key, start, end):
        return self.data.get(key, [])
    
    def exists(self, key):
        return key in self.data
    
    def hincrby(self, key, field, amount=1):
        if key not in self.data:
            self.data[key] = {}
        self.data[key][field] = self.data[key].get(field, 0) + amount
        return self.data[key][field]

# Patch Redis
import scrapy_service.api as api_module
api_module.redis_client = MockRedis()

from scrapy_service.api import app, SUPPORTED_RETAILERS


class TestScrapyAPI(unittest.TestCase):
    """Test Scrapy API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['retailers_supported'], 17)
        self.assertIn('services', data)
    
    def test_retailers_endpoint(self):
        """Test retailers list endpoint"""
        response = self.client.get('/api/retailers')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['total'], 17)
        self.assertIn('retailers', data)
        self.assertEqual(len(data['retailers']), 17)
        
        # Check specific retailers
        for retailer in ['amazon', 'walmart', 'target', 'bestbuy', 'ebay']:
            self.assertIn(retailer, data['retailers'])
    
    def test_search_endpoint(self):
        """Test basic search endpoint"""
        response = self.client.post(
            '/api/search',
            data=json.dumps({'query': 'laptop', 'sites': ['amazon', 'walmart']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 202)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'processing')
        self.assertEqual(data['sites_queued'], 2)
        self.assertEqual(data['query'], 'laptop')
    
    def test_search_no_query(self):
        """Test search without query parameter"""
        response = self.client.post(
            '/api/search',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_bulk_search_endpoint(self):
        """Test bulk search endpoint"""
        response = self.client.post(
            '/api/search/bulk',
            data=json.dumps({
                'queries': ['laptop', 'mouse', 'keyboard'],
                'retailers': ['amazon', 'walmart']
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 202)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['jobs_queued'], 6)  # 3 queries * 2 retailers
        self.assertEqual(data['queries_count'], 3)
        self.assertEqual(data['retailers_count'], 2)
        self.assertIn('batch_id', data)
    
    def test_bulk_search_no_queries(self):
        """Test bulk search without queries"""
        response = self.client.post(
            '/api/search/bulk',
            data=json.dumps({'retailers': ['amazon']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('stats', data)
        self.assertIn('retailers', data)
        self.assertEqual(data['retailers']['total'], 17)
    
    def test_parallel_search_endpoint(self):
        """Test parallel search endpoint"""
        response = self.client.post(
            '/api/search/parallel',
            data=json.dumps({'query': 'laptop'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['query'], 'laptop')
    
    def test_batch_status_endpoint(self):
        """Test batch status endpoint"""
        # First create a batch
        response = self.client.post(
            '/api/search/bulk',
            data=json.dumps({
                'queries': ['laptop'],
                'retailers': ['amazon']
            }),
            content_type='application/json'
        )
        batch_id = response.get_json()['batch_id']
        
        # Check status
        response = self.client.get(f'/api/batch/{batch_id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data['batch_id'], batch_id)
        self.assertIn('total_jobs', data)
        self.assertIn('completed_jobs', data)


if __name__ == '__main__':
    print("=" * 70)
    print("SCRAPY API UNIT TESTS")
    print("=" * 70)
    print("Testing Flask endpoints without external dependencies...")
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestScrapyAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)
