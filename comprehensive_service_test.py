#!/usr/bin/env python3
"""
Comprehensive Service Test Suite
Tests all deployed services from basic connectivity to advanced functionality
Structure: Infrastructure → Core Services → Microservices → Integration → Advanced Features
"""

import asyncio
import time
import json
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field
import aiohttp
import redis.asyncio as aioredis
import asyncpg
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)


@dataclass
class TestResult:
    """Store individual test results"""
    service: str
    test_name: str
    level: str  # BASIC, INTERMEDIATE, ADVANCED, INTEGRATION
    passed: bool
    duration: float
    message: str
    details: Optional[Dict] = None


@dataclass
class ServiceStatus:
    """Track overall service health"""
    name: str
    url: str
    healthy: bool = False
    response_time: float = 0.0
    tests_passed: int = 0
    tests_failed: int = 0
    errors: List[str] = field(default_factory=list)


class ComprehensiveServiceTester:
    """Main test orchestrator"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.services: Dict[str, ServiceStatus] = {}
        self.start_time = time.time()
        
        # Service configurations
        self.config = {
            # Infrastructure
            'redis_main': {'host': 'localhost', 'port': 6379, 'type': 'infrastructure'},
            'redis_captcha': {'host': 'localhost', 'port': 6380, 'type': 'infrastructure'},
            'redis_proxy': {'host': 'localhost', 'port': 6381, 'type': 'infrastructure'},
            'postgres': {'host': 'localhost', 'port': 5432, 'user': 'compair', 
                        'password': 'compair123', 'database': 'compair', 'type': 'infrastructure'},
            
            # Core Services
            'web_api': {'url': 'http://localhost:8000', 'type': 'core'},
            'frontend': {'url': 'http://localhost:8080', 'type': 'core'},
            'worker': {'url': 'http://localhost:8000', 'type': 'core'},  # Via API
            
            # Microservices
            'scraper': {'url': 'http://localhost:3001', 'type': 'microservice'},
            'captcha_solver': {'url': 'http://localhost:9001', 'type': 'microservice'},
            'proxy_api': {'url': 'http://localhost:8001', 'type': 'microservice'},
            'haproxy': {'url': 'http://localhost:8082', 'type': 'microservice'},
            'haproxy_stats': {'url': 'http://localhost:8083/stats', 'type': 'microservice'},
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self):
        """Initialize test session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self.print_header("COMPREHENSIVE SERVICE TEST SUITE")
        print(f"{Fore.CYAN}Testing {len(self.config)} services across 4 tiers{Style.RESET_ALL}\n")
    
    async def teardown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{text.center(80)}{Style.RESET_ALL}")
        print(f"{'='*80}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'-'*80}")
        print(f"  {text}")
        print(f"{'-'*80}{Style.RESET_ALL}\n")
    
    def record_result(self, service: str, test_name: str, level: str, 
                     passed: bool, duration: float, message: str, details: Optional[Dict] = None):
        """Record test result"""
        result = TestResult(service, test_name, level, passed, duration, message, details)
        self.results.append(result)
        
        if service not in self.services:
            self.services[service] = ServiceStatus(service, "")
        
        if passed:
            self.services[service].tests_passed += 1
            icon = f"{Fore.GREEN}✓{Style.RESET_ALL}"
        else:
            self.services[service].tests_failed += 1
            self.services[service].errors.append(message)
            icon = f"{Fore.RED}✗{Style.RESET_ALL}"
        
        print(f"{icon} [{level:12}] {service:20} - {test_name:40} ({duration:.3f}s)")
        if not passed:
            print(f"  {Fore.RED}└─ {message}{Style.RESET_ALL}")
        elif details:
            print(f"  {Fore.GREEN}└─ {details}{Style.RESET_ALL}")
    
    # ========================================================================
    # TIER 1: INFRASTRUCTURE TESTS (Basic Connectivity)
    # ========================================================================
    
    async def test_redis_instance(self, name: str, host: str, port: int):
        """Test Redis connectivity and basic operations"""
        start = time.time()
        try:
            # Basic connectivity
            redis_client = await aioredis.from_url(
                f"redis://{host}:{port}",
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Ping test
            pong = await redis_client.ping()
            assert pong, "Redis ping failed"
            
            # Write test
            test_key = f"test_key_{int(time.time())}"
            await redis_client.set(test_key, "test_value", ex=10)
            
            # Read test
            value = await redis_client.get(test_key)
            assert value == "test_value", "Redis read/write mismatch"
            
            # Info test
            info = await redis_client.info()
            
            await redis_client.close()
            
            duration = time.time() - start
            self.record_result(
                name, "Connection & Operations", "BASIC",
                True, duration, "Redis fully operational",
                {"version": info.get('redis_version', 'unknown'), "port": port}
            )
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                name, "Connection & Operations", "BASIC",
                False, duration, f"Redis error: {str(e)}"
            )
            return False
    
    async def test_postgres(self):
        """Test PostgreSQL connectivity and schema"""
        start = time.time()
        cfg = self.config['postgres']
        
        try:
            # Basic connectivity
            conn = await asyncpg.connect(
                host=cfg['host'],
                port=cfg['port'],
                user=cfg['user'],
                password=cfg['password'],
                database=cfg['database'],
                timeout=10
            )
            
            # Check database version
            version = await conn.fetchval('SELECT version()')
            
            # Check tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_names = [t['table_name'] for t in tables]
            
            # Check critical tables
            critical_tables = ['products', 'users', 'price_history', 'alerts']
            missing = [t for t in critical_tables if t not in table_names]
            
            await conn.close()
            
            duration = time.time() - start
            
            if missing:
                self.record_result(
                    'postgres', "Schema Validation", "BASIC",
                    False, duration, f"Missing tables: {missing}"
                )
            else:
                self.record_result(
                    'postgres', "Schema Validation", "BASIC",
                    True, duration, "Database schema valid",
                    {"tables": len(table_names), "version": version.split()[1]}
                )
            
            return len(missing) == 0
            
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'postgres', "Schema Validation", "BASIC",
                False, duration, f"Database error: {str(e)}"
            )
            return False
    
    # ========================================================================
    # TIER 2: CORE SERVICE TESTS (Health & Basic Endpoints)
    # ========================================================================
    
    async def test_http_health(self, service: str, url: str):
        """Test HTTP service health endpoint"""
        start = time.time()
        
        try:
            async with self.session.get(f"{url}/health") as resp:
                data = await resp.json()
                duration = time.time() - start
                
                if resp.status == 200 and data.get('status') in ['healthy', 'ok', 'up']:
                    self.record_result(
                        service, "Health Endpoint", "BASIC",
                        True, duration, "Service healthy",
                        {"status": data.get('status'), "response_time": f"{duration:.3f}s"}
                    )
                    self.services[service].healthy = True
                    self.services[service].response_time = duration
                    return True
                else:
                    self.record_result(
                        service, "Health Endpoint", "BASIC",
                        False, duration, f"Unhealthy status: {resp.status}"
                    )
                    return False
                    
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                service, "Health Endpoint", "BASIC",
                False, duration, f"Health check failed: {str(e)}"
            )
            return False
    
    async def test_web_api_endpoints(self):
        """Test Web API core endpoints"""
        url = self.config['web_api']['url']
        
        # Test 1: API Docs
        start = time.time()
        try:
            async with self.session.get(f"{url}/docs") as resp:
                duration = time.time() - start
                if resp.status == 200:
                    self.record_result(
                        'web_api', "OpenAPI Docs", "BASIC",
                        True, duration, "API documentation accessible"
                    )
                else:
                    self.record_result(
                        'web_api', "OpenAPI Docs", "BASIC",
                        False, duration, f"Docs returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'web_api', "OpenAPI Docs", "BASIC",
                False, duration, str(e)
            )
        
        # Test 2: Search endpoint (real-time search)
        start = time.time()
        try:
            search_payload = {
                "query": "laptop",
                "sites": ["amazon"],
                "max_results": 5
            }
            async with self.session.post(f"{url}/api/v1/real-time-search", json=search_payload) as resp:
                duration = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'web_api', "Real-Time Search API", "INTERMEDIATE",
                        True, duration, "Search endpoint working",
                        {"status": data.get('status', 'unknown')}
                    )
                else:
                    self.record_result(
                        'web_api', "Real-Time Search API", "INTERMEDIATE",
                        False, duration, f"Search returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'web_api', "Real-Time Search API", "INTERMEDIATE",
                False, duration, str(e)
            )
    
    async def test_frontend(self):
        """Test frontend accessibility"""
        url = self.config['frontend']['url']
        
        start = time.time()
        try:
            async with self.session.get(url) as resp:
                duration = time.time() - start
                content = await resp.text()
                
                if resp.status == 200 and 'root' in content:
                    self.record_result(
                        'frontend', "Page Load", "BASIC",
                        True, duration, "Frontend accessible",
                        {"size": f"{len(content)} bytes"}
                    )
                else:
                    self.record_result(
                        'frontend', "Page Load", "BASIC",
                        False, duration, f"Frontend returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'frontend', "Page Load", "BASIC",
                False, duration, str(e)
            )
    
    # ========================================================================
    # TIER 3: MICROSERVICE TESTS
    # ========================================================================
    
    async def test_scraper_service(self):
        """Test scraper microservice"""
        url = self.config['scraper']['url']
        
        # Test 1: Health
        await self.test_http_health('scraper', url)
        
        # Test 2: Scrape endpoint (if available)
        start = time.time()
        try:
            # Try to get scraper status
            async with self.session.get(f"{url}/status") as resp:
                duration = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'scraper', "Status Endpoint", "INTERMEDIATE",
                        True, duration, "Scraper status available",
                        data
                    )
                else:
                    self.record_result(
                        'scraper', "Status Endpoint", "INTERMEDIATE",
                        False, duration, f"Status returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'scraper', "Status Endpoint", "INTERMEDIATE",
                False, duration, f"Status check failed: {str(e)}"
            )
    
    async def test_captcha_service(self):
        """Test captcha solver service"""
        url = self.config['captcha_solver']['url']
        
        # Test 1: Health
        await self.test_http_health('captcha_solver', url)
        
        # Test 2: Service info
        start = time.time()
        try:
            async with self.session.get(f"{url}/api/v1/solver/info") as resp:
                duration = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'captcha_solver', "Solver Info", "INTERMEDIATE",
                        True, duration, "Captcha solver ready",
                        {"providers": data.get('providers', [])}
                    )
                else:
                    self.record_result(
                        'captcha_solver', "Solver Info", "INTERMEDIATE",
                        False, duration, f"Info returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'captcha_solver', "Solver Info", "INTERMEDIATE",
                False, duration, str(e)
            )
    
    async def test_proxy_service(self):
        """Test proxy management service"""
        url = self.config['proxy_api']['url']
        
        # Test 1: Health
        await self.test_http_health('proxy_api', url)
        
        # Test 2: Proxy list
        start = time.time()
        try:
            async with self.session.get(f"{url}/api/v1/proxies") as resp:
                duration = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'proxy_api', "Proxy List", "INTERMEDIATE",
                        True, duration, "Proxy API accessible",
                        {"proxies": len(data.get('proxies', []))}
                    )
                else:
                    self.record_result(
                        'proxy_api', "Proxy List", "INTERMEDIATE",
                        False, duration, f"Proxy list returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'proxy_api', "Proxy List", "INTERMEDIATE",
                False, duration, str(e)
            )
    
    async def test_haproxy(self):
        """Test HAProxy service"""
        
        # Test 1: Stats page
        start = time.time()
        try:
            url = self.config['haproxy_stats']['url']
            async with self.session.get(url) as resp:
                duration = time.time() - start
                content = await resp.text()
                
                if resp.status == 200 and 'Statistics Report' in content:
                    self.record_result(
                        'haproxy', "Stats Page", "BASIC",
                        True, duration, "HAProxy stats accessible"
                    )
                else:
                    self.record_result(
                        'haproxy', "Stats Page", "BASIC",
                        False, duration, f"Stats returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'haproxy', "Stats Page", "BASIC",
                False, duration, str(e)
            )
        
        # Test 2: Proxy endpoint
        start = time.time()
        try:
            url = self.config['haproxy']['url']
            async with self.session.get(url) as resp:
                duration = time.time() - start
                if resp.status in [200, 503]:  # 503 is ok if no backends
                    self.record_result(
                        'haproxy', "Proxy Endpoint", "INTERMEDIATE",
                        True, duration, "HAProxy proxy accessible",
                        {"status": resp.status}
                    )
                else:
                    self.record_result(
                        'haproxy', "Proxy Endpoint", "INTERMEDIATE",
                        False, duration, f"Proxy returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'haproxy', "Proxy Endpoint", "INTERMEDIATE",
                False, duration, str(e)
            )
    
    # ========================================================================
    # TIER 4: ADVANCED & INTEGRATION TESTS
    # ========================================================================
    
    async def test_celery_worker(self):
        """Test Celery worker via API"""
        url = self.config['web_api']['url']
        
        start = time.time()
        try:
            # Get health check which includes worker info
            async with self.session.get(f"{url}/api/v1/health") as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    celery_check = data.get('checks', {}).get('celery', {})
                    
                    if celery_check.get('status') == 'healthy':
                        self.record_result(
                            'worker', "Celery Worker Health", "INTERMEDIATE",
                            True, duration, "Celery worker operational",
                            {"active_workers": celery_check.get('active_workers', 0)}
                        )
                    else:
                        self.record_result(
                            'worker', "Celery Worker Health", "INTERMEDIATE",
                            False, duration, f"Celery status: {celery_check.get('status', 'unknown')}"
                        )
                else:
                    self.record_result(
                        'worker', "Celery Worker Health", "INTERMEDIATE",
                        False, duration, f"Health check returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'worker', "Celery Worker Health", "INTERMEDIATE",
                False, duration, str(e)
            )
    
    async def test_ai_features(self):
        """Test AI-powered features (CLIP, OCR, etc.)"""
        url = self.config['web_api']['url']
        
        # Test 1: Image search (CLIP) - using search-by-image endpoint
        start = time.time()
        try:
            # Test with a simple image URL
            payload = {
                "image_url": "https://example.com/test.jpg",
                "sites": ["amazon"],
                "max_results": 5
            }
            async with self.session.post(f"{url}/api/v1/search-by-image", json=payload) as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'web_api', "CLIP Image Search", "ADVANCED",
                        True, duration, "AI image search endpoint exists",
                        {"status": data.get('status', 'ok')}
                    )
                elif resp.status == 422:
                    # Endpoint exists but validation failed (expected without real image)
                    self.record_result(
                        'web_api', "CLIP Image Search", "ADVANCED",
                        True, duration, "Image search endpoint available (validation error expected)"
                    )
                elif resp.status == 404:
                    self.record_result(
                        'web_api', "CLIP Image Search", "ADVANCED",
                        False, duration, "Image search endpoint not found"
                    )
                else:
                    self.record_result(
                        'web_api', "CLIP Image Search", "ADVANCED",
                        False, duration, f"Image search returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'web_api', "CLIP Image Search", "ADVANCED",
                False, duration, str(e)
            )
        
        # Test 2: AI Analysis endpoint (includes OCR)
        start = time.time()
        try:
            async with self.session.get(f"{url}/api/v1/ai-models-status") as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    self.record_result(
                        'web_api', "AI Models Status", "ADVANCED",
                        True, duration, "AI models service available",
                        data
                    )
                elif resp.status == 404:
                    # Try alternative endpoint
                    async with self.session.get(f"{url}/health/services") as resp2:
                        if resp2.status == 200:
                            self.record_result(
                                'web_api', "AI Models Status", "ADVANCED",
                                True, duration, "Health services endpoint available"
                            )
                        else:
                            self.record_result(
                                'web_api', "AI Models Status", "ADVANCED",
                                False, duration, "AI status endpoints not found"
                            )
                else:
                    self.record_result(
                        'web_api', "AI Models Status", "ADVANCED",
                        False, duration, f"AI status returned {resp.status}"
                    )
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'web_api', "AI Models Status", "ADVANCED",
                False, duration, str(e)
            )
    
    async def test_end_to_end_workflow(self):
        """Test complete user workflow"""
        url = self.config['web_api']['url']
        
        self.print_section("INTEGRATION TEST: Complete Price Tracking Workflow")
        
        workflow_start = time.time()
        
        # Step 1: Search for product
        start = time.time()
        try:
            search_payload = {
                "query": "test product",
                "sites": ["amazon"],
                "max_results": 5
            }
            async with self.session.post(f"{url}/api/v1/real-time-search", json=search_payload) as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    search_data = await resp.json()
                    self.record_result(
                        'integration', "Step 1: Search", "INTEGRATION",
                        True, duration, "Product search successful",
                        {"status": search_data.get('status', 'unknown')}
                    )
                else:
                    self.record_result(
                        'integration', "Step 1: Search", "INTEGRATION",
                        False, duration, f"Search failed with {resp.status}"
                    )
                    return False
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'integration', "Step 1: Search", "INTEGRATION",
                False, duration, str(e)
            )
            return False
        
        # Step 2: Get product details (if results exist)
        if search_data.get('results'):
            start = time.time()
            try:
                product_id = search_data['results'][0].get('id')
                if product_id:
                    async with self.session.get(f"{url}/api/v1/products/{product_id}") as resp:
                        duration = time.time() - start
                        
                        if resp.status == 200:
                            product_data = await resp.json()
                            self.record_result(
                                'integration', "Step 2: Product Details", "INTEGRATION",
                                True, duration, "Product details retrieved",
                                {"product_id": product_id}
                            )
                        else:
                            self.record_result(
                                'integration', "Step 2: Product Details", "INTEGRATION",
                                False, duration, f"Product fetch failed with {resp.status}"
                            )
            except Exception as e:
                duration = time.time() - start
                self.record_result(
                    'integration', "Step 2: Product Details", "INTEGRATION",
                    False, duration, str(e)
                )
        
        workflow_duration = time.time() - workflow_start
        print(f"\n{Fore.CYAN}Total workflow duration: {workflow_duration:.3f}s{Style.RESET_ALL}\n")
    
    async def test_performance_metrics(self):
        """Test system performance under load"""
        url = self.config['web_api']['url']
        
        self.print_section("PERFORMANCE TEST: Concurrent Request Handling")
        
        # Test concurrent requests
        start = time.time()
        tasks = [
            self.session.get(f"{url}/health")
            for _ in range(50)
        ]
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start
            
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
            failed = len(responses) - successful
            avg_time = duration / len(responses)
            
            self.record_result(
                'web_api', "Concurrent Requests (50)", "ADVANCED",
                successful > 45, duration,
                f"Handled {successful}/{len(responses)} requests",
                {"avg_response": f"{avg_time:.3f}s", "failed": failed}
            )
            
        except Exception as e:
            duration = time.time() - start
            self.record_result(
                'web_api', "Concurrent Requests (50)", "ADVANCED",
                False, duration, str(e)
            )
    
    # ========================================================================
    # TEST ORCHESTRATION
    # ========================================================================
    
    async def run_all_tests(self):
        """Execute all tests in order"""
        
        # TIER 1: Infrastructure
        self.print_section("TIER 1: INFRASTRUCTURE TESTS (Basic Connectivity)")
        
        await self.test_redis_instance('redis_main', 'localhost', 6379)
        await self.test_redis_instance('redis_captcha', 'localhost', 6380)
        await self.test_redis_instance('redis_proxy', 'localhost', 6381)
        await self.test_postgres()
        
        # TIER 2: Core Services
        self.print_section("TIER 2: CORE SERVICE TESTS (Health & Basic Endpoints)")
        
        await self.test_http_health('web_api', self.config['web_api']['url'])
        await self.test_web_api_endpoints()
        await self.test_frontend()
        await self.test_celery_worker()
        
        # TIER 3: Microservices
        self.print_section("TIER 3: MICROSERVICE TESTS")
        
        await self.test_scraper_service()
        await self.test_captcha_service()
        await self.test_proxy_service()
        await self.test_haproxy()
        
        # TIER 4: Advanced & Integration
        self.print_section("TIER 4: ADVANCED & INTEGRATION TESTS")
        
        await self.test_ai_features()
        await self.test_end_to_end_workflow()
        await self.test_performance_metrics()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        
        total_duration = time.time() - self.start_time
        
        self.print_header("TEST EXECUTION SUMMARY")
        
        # Overall stats
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total_tests - passed
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Fore.CYAN}Total Tests:{Style.RESET_ALL} {total_tests}")
        print(f"{Fore.GREEN}Passed:{Style.RESET_ALL} {passed}")
        print(f"{Fore.RED}Failed:{Style.RESET_ALL} {failed}")
        print(f"{Fore.YELLOW}Pass Rate:{Style.RESET_ALL} {pass_rate:.1f}%")
        print(f"{Fore.CYAN}Total Duration:{Style.RESET_ALL} {total_duration:.2f}s\n")
        
        # Service breakdown
        self.print_section("SERVICE HEALTH OVERVIEW")
        
        for service_name, status in sorted(self.services.items()):
            total = status.tests_passed + status.tests_failed
            if total > 0:
                rate = (status.tests_passed / total * 100)
                health_icon = f"{Fore.GREEN}●{Style.RESET_ALL}" if status.healthy else f"{Fore.RED}●{Style.RESET_ALL}"
                
                print(f"{health_icon} {service_name:25} - {status.tests_passed}/{total} tests passed ({rate:.0f}%)")
                
                if status.errors:
                    for error in status.errors[:2]:  # Show first 2 errors
                        print(f"  {Fore.RED}└─ {error[:70]}{Style.RESET_ALL}")
        
        # Test level breakdown
        self.print_section("TEST LEVEL BREAKDOWN")
        
        levels = {}
        for result in self.results:
            if result.level not in levels:
                levels[result.level] = {'passed': 0, 'failed': 0}
            
            if result.passed:
                levels[result.level]['passed'] += 1
            else:
                levels[result.level]['failed'] += 1
        
        for level in ['BASIC', 'INTERMEDIATE', 'ADVANCED', 'INTEGRATION']:
            if level in levels:
                stats = levels[level]
                total = stats['passed'] + stats['failed']
                rate = (stats['passed'] / total * 100) if total > 0 else 0
                print(f"{level:15} - {stats['passed']:2}/{total:2} passed ({rate:5.1f}%)")
        
        # Failed tests detail
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            self.print_section("FAILED TESTS DETAIL")
            for result in failed_tests:
                print(f"{Fore.RED}✗ [{result.level}] {result.service} - {result.test_name}{Style.RESET_ALL}")
                print(f"  └─ {result.message}\n")
        
        # Final verdict
        self.print_header("FINAL VERDICT")
        
        if pass_rate >= 90:
            verdict = f"{Fore.GREEN}{Style.BRIGHT}EXCELLENT - System is production ready!{Style.RESET_ALL}"
        elif pass_rate >= 75:
            verdict = f"{Fore.YELLOW}{Style.BRIGHT}GOOD - Minor issues to address{Style.RESET_ALL}"
        elif pass_rate >= 50:
            verdict = f"{Fore.YELLOW}{Style.BRIGHT}FAIR - Several issues need attention{Style.RESET_ALL}"
        else:
            verdict = f"{Fore.RED}{Style.BRIGHT}POOR - Critical issues require immediate attention{Style.RESET_ALL}"
        
        print(f"{verdict}\n")
        
        # Save JSON report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'pass_rate': pass_rate,
                'duration': total_duration
            },
            'services': {
                name: {
                    'healthy': status.healthy,
                    'tests_passed': status.tests_passed,
                    'tests_failed': status.tests_failed,
                    'response_time': status.response_time,
                    'errors': status.errors
                }
                for name, status in self.services.items()
            },
            'results': [
                {
                    'service': r.service,
                    'test': r.test_name,
                    'level': r.level,
                    'passed': r.passed,
                    'duration': r.duration,
                    'message': r.message,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"{Fore.CYAN}Detailed report saved to: {report_file}{Style.RESET_ALL}\n")
        
        return pass_rate >= 75  # Return success if 75%+ pass rate


async def main():
    """Main entry point"""
    tester = ComprehensiveServiceTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
        success = tester.generate_report()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test execution interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())
