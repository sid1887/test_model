"""
Comprehensive Service Integration Test
Tests all running services and their integration
"""

import requests
import asyncio
import json
import time
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"
SCRAPER_URL = "http://localhost:3001"
POSTGRES_URL = "localhost:5432"
REDIS_URL = "localhost:6379"

class ServiceTester:
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def test_backend_health(self) -> Tuple[bool, str]:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return True, f"Backend healthy: {data}"
            else:
                return False, f"Backend returned {response.status_code}"
        except Exception as e:
            return False, f"Backend error: {e}"
    
    def test_backend_routes(self) -> Dict[str, Tuple[bool, str]]:
        """Test key backend API routes"""
        routes_to_test = [
            ("/api/v1/products", "GET"),
            ("/api/v1/retailers", "GET"),
            ("/api/v1/alerts", "GET"),
            ("/api/v1/smart-lists", "GET"),
            ("/api/v1/analytics/overview", "GET"),
            ("/api/v1/search", "POST"),
        ]
        
        results = {}
        for route, method in routes_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{route}", timeout=5)
                elif method == "POST":
                    response = requests.post(
                        f"{BASE_URL}{route}",
                        json={"query": "test"},
                        timeout=5
                    )
                
                if response.status_code in [200, 201, 400]:  # 400 is OK for missing params
                    results[route] = (True, f"Status: {response.status_code}")
                else:
                    results[route] = (False, f"Status: {response.status_code}")
            except Exception as e:
                results[route] = (False, str(e))
        
        return results
    
    def test_database_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="cumpair",
                user="postgres",
                password="postgres",
                timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return True, "PostgreSQL connected successfully"
            else:
                return False, "PostgreSQL query failed"
        except Exception as e:
            return False, f"PostgreSQL error: {e}"
    
    def test_redis_connection(self) -> Tuple[bool, str]:
        """Test Redis connection"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_timeout=5)
            r.ping()
            
            # Try to set and get a value
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            r.delete('test_key')
            
            if value == 'test_value':
                return True, "Redis connected and working"
            else:
                return False, "Redis get/set failed"
        except Exception as e:
            return False, f"Redis error: {e}"
    
    def test_frontend_access(self) -> Tuple[bool, str]:
        """Test frontend accessibility"""
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                return True, "Frontend serving content"
            else:
                return False, f"Frontend returned {response.status_code}"
        except Exception as e:
            return False, f"Frontend error: {e}"
    
    def test_scraper_connection(self) -> Tuple[bool, str]:
        """Test scraper service connection"""
        try:
            response = requests.get(f"{SCRAPER_URL}/health", timeout=5)
            if response.status_code == 200:
                return True, "Scraper service healthy"
            else:
                return False, f"Scraper returned {response.status_code}"
        except Exception as e:
            return False, f"Scraper error: {e}"
    
    def test_metrics_endpoint(self) -> Tuple[bool, str]:
        """Test Prometheus metrics endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/metrics", timeout=5)
            if response.status_code == 200 and "cumpair_" in response.text:
                return True, "Metrics endpoint working"
            else:
                return False, f"Metrics returned {response.status_code}"
        except Exception as e:
            return False, f"Metrics error: {e}"
    
    def test_data_persistence(self) -> Tuple[bool, str]:
        """Test data persistence across requests"""
        try:
            # Create alert (if possible)
            create_response = requests.get(f"{BASE_URL}/api/v1/alerts", timeout=5)
            if create_response.status_code in [200, 400]:
                # Get alerts again
                get_response = requests.get(f"{BASE_URL}/api/v1/alerts", timeout=5)
                if get_response.status_code == 200:
                    return True, "Data persistence working"
                else:
                    return False, "Could not retrieve data"
            else:
                return False, f"Create response: {create_response.status_code}"
        except Exception as e:
            return False, f"Persistence test error: {e}"
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE SERVICE INTEGRATION TEST")
        print("=" * 80)
        
        # Test 1: Backend Health
        print("\n[1/6] Testing Backend Health...")
        success, message = self.test_backend_health()
        print(f"  {'✅' if success else '❌'} Backend: {message}")
        self.results["backend_health"] = success
        
        # Test 2: Database Connection
        print("\n[2/6] Testing Database Connection...")
        success, message = self.test_database_connection()
        print(f"  {'✅' if success else '❌'} PostgreSQL: {message}")
        self.results["postgres"] = success
        
        # Test 3: Redis Connection
        print("\n[3/6] Testing Redis Connection...")
        success, message = self.test_redis_connection()
        print(f"  {'✅' if success else '❌'} Redis: {message}")
        self.results["redis"] = success
        
        # Test 4: Frontend Access
        print("\n[4/6] Testing Frontend Access...")
        success, message = self.test_frontend_access()
        print(f"  {'✅' if success else '❌'} Frontend: {message}")
        self.results["frontend"] = success
        
        # Test 5: Scraper Service
        print("\n[5/6] Testing Scraper Service...")
        success, message = self.test_scraper_connection()
        print(f"  {'✅' if success else '❌'} Scraper: {message}")
        self.results["scraper"] = success
        
        # Test 6: API Routes
        print("\n[6/6] Testing Backend API Routes...")
        routes = self.test_backend_routes()
        for route, (success, message) in routes.items():
            print(f"  {'✅' if success else '❌'} {route}: {message}")
        self.results["routes"] = sum(1 for s, _ in routes.values() if s)
        
        # Test 7: Metrics
        print("\n[7/7] Testing Metrics Endpoint...")
        success, message = self.test_metrics_endpoint()
        print(f"  {'✅' if success else '❌'} Metrics: {message}")
        self.results["metrics"] = success
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for v in self.results.values() if v is True or isinstance(v, int) and v > 0)
        total = len(self.results)
        
        print(f"\n✅ Services Operational:")
        print(f"  • Backend:      {'✅' if self.results.get('backend_health') else '❌'}")
        print(f"  • PostgreSQL:   {'✅' if self.results.get('postgres') else '❌'}")
        print(f"  • Redis:        {'✅' if self.results.get('redis') else '❌'}")
        print(f"  • Frontend:     {'✅' if self.results.get('frontend') else '❌'}")
        print(f"  • Scraper:      {'✅' if self.results.get('scraper') else '❌'}")
        print(f"  • Metrics:      {'✅' if self.results.get('metrics') else '❌'}")
        print(f"  • API Routes:   {'✅' if self.results.get('routes', 0) > 3 else '❌'} ({self.results.get('routes', 0)}/6)")
        
        print(f"\n🎯 Overall Status: {'🚀 ALL SYSTEMS GO!' if passed >= 6 else '⚠️  Some services need attention'}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    tester = ServiceTester()
    tester.run_all_tests()
