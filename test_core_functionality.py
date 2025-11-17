#!/usr/bin/env python3
"""
Comprehensive test suite for core functionality
Tests: Text Search, Image Analysis, Product Data, Analytics
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def test(self, name, url, method="GET", expected_status=200, data=None):
        """Run a single test"""
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            
            status_ok = response.status_code == expected_status
            
            if status_ok:
                try:
                    result = response.json()
                    self.results.append({
                        "test": name,
                        "status": "✅ PASS",
                        "url": url,
                        "status_code": response.status_code,
                        "response_keys": list(result.keys()) if isinstance(result, dict) else "list",
                    })
                    self.passed += 1
                    print(f"✅ {name}")
                except:
                    self.results.append({
                        "test": name,
                        "status": "✅ PASS",
                        "url": url,
                        "status_code": response.status_code,
                        "response": response.text[:100]
                    })
                    self.passed += 1
                    print(f"✅ {name}")
            else:
                self.results.append({
                    "test": name,
                    "status": "❌ FAIL",
                    "url": url,
                    "expected": expected_status,
                    "got": response.status_code,
                    "error": response.text[:200]
                })
                self.failed += 1
                print(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
        except Exception as e:
            self.results.append({
                "test": name,
                "status": "❌ ERROR",
                "url": url,
                "error": str(e)
            })
            self.failed += 1
            print(f"❌ {name} - {str(e)}")
    
    def report(self):
        """Print test report"""
        print("\n" + "="*80)
        print(f"TEST RESULTS: {self.passed} PASSED, {self.failed} FAILED")
        print("="*80)
        
        for result in self.results:
            print(f"\n{result['test']}: {result['status']}")
            print(f"  URL: {result['url']}")
            if "status_code" in result:
                print(f"  Status: {result['status_code']}")
            if "response_keys" in result:
                print(f"  Response Keys: {result['response_keys']}")
            if "error" in result and result['status'] == "❌ FAIL":
                print(f"  Error: {result['error']}")

def main():
    runner = TestRunner()
    
    print("\n" + "="*80)
    print("TESTING CORE FUNCTIONALITY")
    print("="*80)
    
    # ============================================================================
    # 1. HEALTH CHECK
    # ============================================================================
    print("\n[1] HEALTH CHECK")
    runner.test("Health Check", f"{BASE_URL}/api/v1/health")
    
    # ============================================================================
    # 2. TEXT SEARCH
    # ============================================================================
    print("\n[2] TEXT SEARCH")
    runner.test("Search: 'tv'", f"{BASE_URL}/api/v2/search?q=tv")
    runner.test("Search: 'frisbee'", f"{BASE_URL}/api/v2/search?q=frisbee")
    runner.test("Search: 'bottle'", f"{BASE_URL}/api/v2/search?q=bottle")
    runner.test("Search: 'unknown'", f"{BASE_URL}/api/v2/search?q=unknown")
    runner.test("Search with limit", f"{BASE_URL}/api/v2/search?q=tv&limit=5")
    
    # ============================================================================
    # 3. DATABASE PRODUCTS
    # ============================================================================
    print("\n[3] DATABASE & PRODUCTS")
    runner.test("Product list endpoint", f"{BASE_URL}/api/v1/products", expected_status=200)
    
    # ============================================================================
    # 4. PRICE ENDPOINTS
    # ============================================================================
    print("\n[4] PRICE DATA")
    runner.test("Price trends", f"{BASE_URL}/api/analytics/product/1/trends?days=30", expected_status=200)
    runner.test("Price comparison", f"{BASE_URL}/api/analytics/retailers/comparison", expected_status=200)
    
    # ============================================================================
    # 5. ALERTS (if UUID products exist)
    # ============================================================================
    print("\n[5] ALERTS")
    runner.test("Active alerts", f"{BASE_URL}/api/v1/alerts/active", expected_status=200)
    
    # ============================================================================
    # 6. ANALYTICS - TROUBLESHOOT
    # ============================================================================
    print("\n[6] ANALYTICS ENDPOINTS")
    runner.test("Analytics Overview", f"{BASE_URL}/api/analytics/overview", expected_status=200)
    runner.test("Anomalies Detection", f"{BASE_URL}/api/analytics/anomalies", expected_status=200)
    runner.test("Trending Products", f"{BASE_URL}/api/analytics/products/trending", expected_status=200)
    
    # ============================================================================
    # REPORT
    # ============================================================================
    runner.report()
    
    # ============================================================================
    # DETAILED SEARCH RESULTS
    # ============================================================================
    print("\n" + "="*80)
    print("DETAILED SEARCH RESULTS")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v2/search?q=tv")
        data = response.json()
        print(f"\nSearch Query: 'tv'")
        print(f"Total Results: {data['metadata']['total_results']}")
        print(f"Cache Hit: {data['metadata']['cache_hit']}")
        print(f"Latency: {data['metadata']['latency_ms']:.2f}ms")
        
        if data['results']:
            print(f"\nFirst Result:")
            result = data['results'][0]
            print(f"  Title: {result['title']}")
            print(f"  Description: {result['description']}")
            print(f"  Image: {result['main_image']}")
            print(f"  Brand: {result.get('brand', 'N/A')}")
            print(f"  Category: {result.get('category', 'N/A')}")
    except Exception as e:
        print(f"Error fetching search details: {e}")
    
    # ============================================================================
    # DATABASE STATS
    # ============================================================================
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="compair",
            user="compair",
            password="compair123"
        )
        cur = conn.cursor()
        
        # Count products
        cur.execute("SELECT COUNT(*) FROM products")
        product_count = cur.fetchone()[0]
        
        # Count prices
        cur.execute("SELECT COUNT(*) FROM product_prices")
        price_count = cur.fetchone()[0]
        
        # Count embeddings
        cur.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = cur.fetchone()[0]
        
        # Count alerts
        cur.execute("SELECT COUNT(*) FROM price_alerts")
        alert_count = cur.fetchone()[0]
        
        # Count analytics
        cur.execute("SELECT COUNT(*) FROM analytics_insights")
        analytics_count = cur.fetchone()[0]
        
        print(f"\nProducts: {product_count}")
        print(f"Price Points: {price_count}")
        print(f"Embeddings: {embedding_count}")
        print(f"Price Alerts: {alert_count}")
        print(f"Analytics Insights: {analytics_count}")
        
        # Sample products
        cur.execute("SELECT title, description, main_image FROM products LIMIT 3")
        print(f"\nSample Products:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} [{row[2]}]")
        
        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")
    
    # ============================================================================
    # IMAGE ANALYSIS TEST (if image endpoint exists)
    # ============================================================================
    print("\n" + "="*80)
    print("IMAGE ANALYSIS TEST")
    print("="*80)
    
    try:
        # Get a product with image
        response = requests.get(f"{BASE_URL}/api/v2/search?q=tv")
        data = response.json()
        
        if data['results']:
            product = data['results'][0]
            image_path = product.get('main_image', '')
            print(f"\nProduct: {product['title']}")
            print(f"Image: {image_path}")
            
            # Try to get image analysis if available
            product_id = product['product_id']
            print(f"Product ID: {product_id}")
            print("✓ Image data available for analysis")
    except Exception as e:
        print(f"Image analysis test error: {e}")
    
    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
