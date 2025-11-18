"""
Adaptive Web Scraping Engine - Multi-layer scraping with anti-blocking measures
Implements direct API, HTML parsing, and headless browser strategies
Enhanced with dedicated web scraper integration, proxy management, and stealth browsing
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
import random
import time
import json
import logging
from typing import Optional, Dict, List, Any
import base64
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime, timedelta
import hashlib

from app.core.config import settings
from app.core.monitoring import SCRAPING_COUNT, logger
from app.services.stealth_browser import StealthBrowser, StealthSessionManager

# Integration with our dedicated web scraper
class CumpairScraperClient:
    """
    Enhanced client for dedicated Node.js scraper microservice

    Features:
    - Intelligent failover to Python scrapers
    - Request batching and deduplication
    - Circuit breaker pattern for service failures
    - Caching layer with Redis
    - HAProxy/2Captcha orchestration
    """

    def __init__(self, base_url: str = "http://scraper:3001"):
        self.base_url = base_url
        self.session = None
        self.available = False
        self.circuit_breaker = {
            'failures': 0,
            'last_attempt': None,
            'threshold': 5,  # Trip after 5 failures
            'timeout': 60  # Reset after 60 seconds
        }
        self.request_cache = {}  # In-memory cache for deduplication
        self.batch_queue = []
        self.batch_size = 10

    async def initialize(self):
        """Initialize with health check and service discovery"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        # Check circuit breaker
        if self._is_circuit_open():
            logger.warning("⚠️ Circuit breaker OPEN - scraper service disabled temporarily")
            return False

        try:
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    health = await response.json()
                    self.available = True
                    self.circuit_breaker['failures'] = 0
                    logger.info(f"✅ Scraper service: {health.get('status')}")
                    logger.info(f"   Redis: Connected={health.get('redis', {}).get('isConnected')}")
                    logger.info(f"   Proxy Pool: {health.get('scraper', {}).get('proxyPoolSize', 0)} proxies")
                    logger.info(f"   Active Browsers: {health.get('scraper', {}).get('activeBrowsers', 0)}")
                    return True
                else:
                    self._record_failure()
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Scraper service unavailable: {e}")
            self._record_failure()
            return False

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker['failures'] < self.circuit_breaker['threshold']:
            return False

        if self.circuit_breaker['last_attempt']:
            elapsed = time.time() - self.circuit_breaker['last_attempt']
            if elapsed > self.circuit_breaker['timeout']:
                # Reset circuit breaker
                self.circuit_breaker['failures'] = 0
                logger.info("🔄 Circuit breaker RESET - retrying scraper service")
                return False

        return True

    def _record_failure(self):
        """Record a service failure"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_attempt'] = time.time()
        self.available = False

    async def scrape_url(self, url: str, options: Dict = None) -> Dict:
        """
        Scrape single URL with intelligent routing and caching

        Features:
        - Cache checking before scraping
        - Automatic failover to Python scrapers
        - Request deduplication
        """
        # Check cache first
        cache_key = self._get_cache_key(url, options)
        if cache_key in self.request_cache:
            cached_time = self.request_cache[cache_key].get('timestamp', 0)
            if time.time() - cached_time < 300:  # 5-minute cache
                logger.debug(f"Cache HIT for {url}")
                return self.request_cache[cache_key]

        if not self.session:
            await self.initialize()

        if not self.available:
            logger.info("Scraper service unavailable, using Python fallback")
            return await self._fallback_scrape(url, options)

        try:
            payload = {
                "query": url,  # For search endpoints
                "url": url,
                "usePuppeteer": True,
                "cache": True,
                "cacheTTL": 300
            }
            if options:
                payload.update(options)

            async with self.session.post(
                f"{self.base_url}/api/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                result = await response.json()

                if response.status == 200 and (result.get("success") or result.get("products")):
                    # Cache successful result
                    cached_result = {
                        "status": "success",
                        "data": result.get("data", result),
                        "products": result.get("products", []),
                        "url": url,
                        "timestamp": time.time(),
                        "response_time": result.get("responseTime", 0),
                        "source": "node_scraper"
                    }
                    self.request_cache[cache_key] = cached_result
                    return cached_result
                else:
                    self._record_failure()
                    return await self._fallback_scrape(url, options)

        except asyncio.TimeoutError:
            logger.error(f"Scraper timeout for {url}")
            self._record_failure()
            return await self._fallback_scrape(url, options)
        except Exception as e:
            logger.error(f"Scraper error for {url}: {e}")
            self._record_failure()
            return await self._fallback_scrape(url, options)

    async def _fallback_scrape(self, url: str, options: Dict = None) -> Dict:
        """Fallback to Python-based scraping"""
        logger.info(f"Using Python fallback scraper for {url}")
        try:
            # Use the AdaptiveScrapingEngine as fallback
            from app.services.scraping import scraping_engine
            result = await scraping_engine.scrape_product(url, options.get('query', '') if options else '')
            result['source'] = 'python_fallback'
            return result
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "url": url,
                "source": "fallback_failed"
            }

    def _get_cache_key(self, url: str, options: Dict = None) -> str:
        """Generate cache key from URL and options"""
        import hashlib
        key_str = f"{url}:{json.dumps(options or {}, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def scrape_batch(self, urls: List[str], options: Dict = None) -> List[Dict]:
        """
        High-performance batch scraping with intelligent distribution

        Features:
        - Automatic batching for optimal performance
        - Parallel execution with concurrency limits
        - Mixed Node.js + Python scraping for resilience
        """
        if not self.session:
            await self.initialize()

        if not self.available or len(urls) > 20:
            # For large batches or when service unavailable, use hybrid approach
            return await self._hybrid_batch_scrape(urls, options)

        try:
            payload = {
                "urls": urls if isinstance(urls[0], str) else urls,
                "usePuppeteer": True,
                "cache": True
            }
            if options:
                payload.update(options)

            async with self.session.post(
                f"{self.base_url}/api/search/parallel",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Batch: {result.get('successful_sites', 0)}/{len(urls)} successful")
                    return result.get("results", [])
                else:
                    return await self._hybrid_batch_scrape(urls, options)

        except Exception as e:
            logger.error(f"Batch scraping error: {e}")
            return await self._hybrid_batch_scrape(urls, options)

    async def _hybrid_batch_scrape(self, urls: List[str], options: Dict = None) -> List[Dict]:
        """Hybrid scraping using both Node.js and Python scrapers"""
        logger.info(f"Using hybrid batch scraping for {len(urls)} URLs")

        # Split workload: First half to Node.js (if available), rest to Python
        split_point = len(urls) // 2 if self.available else 0

        tasks = []

        # Node.js batch (if available)
        if split_point > 0:
            tasks.append(self.scrape_batch(urls[:split_point], options))

        # Python parallel scraping for remaining URLs
        from app.services.scraping import scraping_engine
        for url in urls[split_point:]:
            tasks.append(scraping_engine.scrape_product(url, options.get('query', '') if options else ''))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        flattened = []
        for result in results:
            if isinstance(result, list):
                flattened.extend(result)
            elif isinstance(result, dict):
                flattened.append(result)

        return flattened

    async def search_multi_retailer(self, query: str, retailers: List[str] = None, max_results: int = 10) -> Dict:
        """
        Intelligent multi-retailer search with parallel execution

        Features:
        - Searches 6 retailers simultaneously: Amazon, Walmart, eBay, Target, BestBuy, Newegg
        - HAProxy rotation for load balancing
        - 2Captcha integration for blocked requests
        - Result aggregation and deduplication
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            return await self._fallback_multi_search(query, retailers, max_results)

        if retailers is None:
            retailers = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg']

        try:
            payload = {
                "query": query,
                "sites": retailers,
                "max_results": max_results
            }

            async with self.session.post(
                f"{self.base_url}/api/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Aggregate and deduplicate results
                    all_products = []
                    seen_titles = set()

                    for site_result in result.get('results', []):
                        for product in site_result.get('products', []):
                            title_normalized = product.get('title', '').lower().strip()
                            if title_normalized and title_normalized not in seen_titles:
                                seen_titles.add(title_normalized)
                                all_products.append(product)

                    logger.info(f"✅ Multi-retailer: {len(all_products)} unique products from {len(retailers)} retailers")

                    return {
                        "products": all_products,
                        "total_results": len(all_products),
                        "retailers_searched": len(retailers),
                        "successful_retailers": result.get('successful_sites', 0),
                        "query": query,
                        "source": "node_scraper"
                    }
                else:
                    return await self._fallback_multi_search(query, retailers, max_results)

        except Exception as e:
            logger.error(f"Multi-retailer search error: {e}")
            return await self._fallback_multi_search(query, retailers, max_results)

    async def _fallback_multi_search(self, query: str, retailers: List[str], max_results: int) -> Dict:
        """Fallback multi-retailer search using Python scrapers"""
        logger.info("Using Python fallback for multi-retailer search")

        # Generate search URLs for each retailer
        search_urls = {
            'amazon': f"https://www.amazon.com/s?k={query.replace(' ', '+')}",
            'walmart': f"https://www.walmart.com/search?q={query.replace(' ', '+')}",
            'ebay': f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}",
            'target': f"https://www.target.com/s?searchTerm={query.replace(' ', '+')}",
            'bestbuy': f"https://www.bestbuy.com/site/searchpage.jsp?st={query.replace(' ', '+')}",
            'newegg': f"https://www.newegg.com/p/pl?d={query.replace(' ', '+')}"
        }

        # Scrape all retailers in parallel
        from app.services.scraping import scraping_engine
        tasks = [
            scraping_engine.scrape_product(search_urls[retailer], query)
            for retailer in (retailers or search_urls.keys())
            if retailer in search_urls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_products = []
        successful = 0
        for result in results:
            if isinstance(result, dict) and result.get('status') == 'success':
                successful += 1
                products = result.get('data', {}).get('products', [])
                all_products.extend(products)

        return {
            "products": all_products,
            "total_results": len(all_products),
            "retailers_searched": len(retailers or search_urls),
            "successful_retailers": successful,
            "query": query,
            "source": "python_fallback"
        }

    async def get_stats(self) -> Dict:
        """Get comprehensive scraper statistics"""
        if not self.session:
            await self.initialize()

        stats = {
            "circuit_breaker": {
                "status": "OPEN" if self._is_circuit_open() else "CLOSED",
                "failures": self.circuit_breaker['failures'],
                "threshold": self.circuit_breaker['threshold']
            },
            "cache": {
                "size": len(self.request_cache),
                "hit_rate": "N/A"  # Could be tracked
            },
            "service_available": self.available
        }

        if self.available:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/stats",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        scraper_stats = await response.json()
                        stats["scraper_service"] = scraper_stats
                        return stats
            except Exception as e:
                logger.error(f"Error getting scraper stats: {e}")

        return stats

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

# Global scraper client instance
scraper_client = CumpairScraperClient()

class EnhancedProxyManager:
    """Enhanced proxy manager with health tracking and Redis persistence"""

    def __init__(self):
        self.proxy_pool = []
        self.failed_proxies = set()
        self.proxy_health = {}  # url -> {success_rate, last_check, latency}
        self.rota_client_url = settings.rota_url
        self.ua = UserAgent()
        self.session_cache = {}  # Cache sessions per proxy

    async def get_proxy(self) -> Optional[Dict]:
        """Get the best working proxy from the pool"""
        if not self.proxy_pool:
            await self.refresh_proxy_pool()

        # Sort proxies by health score (success_rate / latency)
        available_proxies = [
            p for p in self.proxy_pool
            if p['url'] not in self.failed_proxies
        ]

        if not available_proxies:
            await self.refresh_proxy_pool()
            available_proxies = self.proxy_pool[:5]  # Take first 5 if all failed

        # Select best proxy based on health metrics
        best_proxy = None
        best_score = -1

        for proxy in available_proxies:
            health = self.proxy_health.get(proxy['url'], {
                'success_rate': 0.5, 'latency': 1.0, 'last_check': None
            })

            # Calculate score: success_rate / (latency + 1)
            score = health['success_rate'] / (health['latency'] + 1)

            if score > best_score:
                best_score = score
                best_proxy = proxy

        return best_proxy

    async def refresh_proxy_pool(self):
        """Refresh proxy pool from Rota service and free sources"""
        try:
            # Try to get proxies from Rota service
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.rota_client_url}/proxies") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.proxy_pool = data.get('proxies', [])
                        logger.info(f"Loaded {len(self.proxy_pool)} proxies from Rota")
                        return
        except Exception as e:
            logger.warning(f"Failed to load proxies from Rota: {e}")

        # Fallback to free proxy sources
        await self._load_free_proxies()

    async def _load_free_proxies(self):
        """Load proxies from free sources"""
        free_proxies = [
            # Add some basic proxy configurations
            {'url': 'http://proxy1.example.com:8080', 'type': 'http'},
            {'url': 'http://proxy2.example.com:8080', 'type': 'http'},
        ]
        self.proxy_pool = free_proxies
        logger.info(f"Loaded {len(free_proxies)} free proxies")

    def report_failure(self, proxy_url: str):
        """Report a failed proxy"""
        self.failed_proxies.add(proxy_url)
        logger.warning(f"Proxy marked as failed: {proxy_url}")

    def get_user_agent(self) -> str:
        """Get a random user agent"""
        return self.ua.random

class CaptchaSolver:
    """Enhanced CAPTCHA solving with self-hosted service, Tesseract, and CNN fallback"""

    def __init__(self):
        self.cnn_model = None
        self.self_hosted_endpoint = None
        self.ocr_engines = {}
        self._init_captcha_services()

    def _init_captcha_services(self):
        """Initialize available CAPTCHA solving services"""
        # Check for self-hosted 2captcha-compatible service
        self_hosted_url = getattr(settings, 'captcha_service_url', None)
        if self_hosted_url:
            self.self_hosted_endpoint = self_hosted_url
            logger.info(f"Self-hosted captcha service configured: {self_hosted_url}")

        # Initialize OCR engines
        try:
            import pytesseract
            self.ocr_engines['tesseract'] = pytesseract
            logger.info("Tesseract OCR initialized")
        except ImportError:
            logger.warning("Tesseract not available")

        try:
            import easyocr
            self.ocr_engines['easyocr'] = easyocr.Reader(['en'], gpu=False)  # Disable GPU for stability
            logger.info("EasyOCR initialized")
        except ImportError:
            logger.info("EasyOCR not available (pip install easyocr to enable)")
        except Exception as e:
            logger.info(f"EasyOCR initialization failed: {e}")

    async def solve_captcha(self, image_path: str, captcha_type: str = "text") -> Optional[str]:
        """
        Solve CAPTCHA using multiple methods with fallback chain

        Args:
            image_path: Path to CAPTCHA image
            captcha_type: Type of captcha (text, recaptcha, hcaptcha, etc.)

        Returns:
            Solved CAPTCHA text or None
        """
        methods = [
            self._solve_with_self_hosted,
            self._solve_with_easyocr,
            self._solve_with_tesseract,
            self._solve_with_cnn
        ]

        for method in methods:
            try:
                result = await method(image_path, captcha_type)
                if result:
                    logger.info(f"CAPTCHA solved with {method.__name__}: {result}")
                    return result
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed: {e}")
                continue

        logger.warning("All CAPTCHA solving methods failed")
        return None

    async def _solve_with_self_hosted(self, image_path: str, captcha_type: str) -> Optional[str]:
        """Solve using self-hosted 2captcha-compatible service"""
        if not self.self_hosted_endpoint:
            return None

        try:
            import aiohttp
            import base64

            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            async with aiohttp.ClientSession() as session:
                # Submit captcha
                submit_data = {
                    'method': 'base64',
                    'body': image_data,
                    'json': 1
                }

                if captcha_type == "recaptcha":
                    submit_data.update({
                        'method': 'userrecaptcha',
                        'googlekey': 'SITE_KEY_HERE',  # Would be dynamic
                        'pageurl': 'PAGE_URL_HERE'
                    })

                async with session.post(f"{self.self_hosted_endpoint}/in.php",
                                      data=submit_data) as response:
                    submit_result = await response.json()

                if submit_result.get('status') != 1:
                    return None

                captcha_id = submit_result.get('request')

                # Poll for result
                for _ in range(30):  # 30 attempts, 2 seconds each = 1 minute max
                    await asyncio.sleep(2)

                    async with session.get(f"{self.self_hosted_endpoint}/res.php",
                                         params={'action': 'get', 'id': captcha_id, 'json': 1}) as response:
                        result = await response.json()

                    if result.get('status') == 1:
                        return result.get('request')
                    elif result.get('error'):
                        logger.error(f"Self-hosted service error: {result.get('error')}")
                        return None

                return None

        except Exception as e:
            logger.error(f"Self-hosted captcha service failed: {e}")
            return None

    async def _solve_with_easyocr(self, image_path: str, captcha_type: str) -> Optional[str]:
        """Solve using EasyOCR"""
        if 'easyocr' not in self.ocr_engines:
            return None

        try:
            reader = self.ocr_engines['easyocr']
            results = reader.readtext(image_path)

            # Extract text with highest confidence
            if results:
                text = ' '.join([result[1] for result in results if result[2] > 0.5])
                text = ''.join(c for c in text if c.isalnum())  # Clean text

                if len(text) >= 4:
                    return text

            return None

        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return None

    async def _solve_with_tesseract(self, image_path: str, captcha_type: str) -> Optional[str]:
        """Solve using Tesseract OCR with enhanced preprocessing"""
        if 'tesseract' not in self.ocr_engines:
            return None

        try:
            from PIL import Image, ImageFilter, ImageEnhance
            import numpy as np

            # Enhanced preprocessing
            img = Image.open(image_path).convert('L')

            # Multiple preprocessing attempts
            preprocessing_methods = [
                lambda x: x.filter(ImageFilter.SHARPEN),
                lambda x: ImageEnhance.Contrast(x).enhance(2.0),
                lambda x: x.filter(ImageFilter.MedianFilter(3)),
                lambda x: x.point(lambda p: 255 if p > 128 else 0)  # Binary threshold
            ]

            for preprocess in preprocessing_methods:
                try:
                    processed_img = preprocess(img)

                    # Multiple Tesseract configurations
                    configs = [
                        '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        '--psm 6',
                        '--psm 13'
                    ]

                    for config in configs:
                        text = self.ocr_engines['tesseract'].image_to_string(processed_img, config=config)
                        text = ''.join(c for c in text.strip() if c.isalnum())

                        if text and len(text) >= 4:
                            return text

                except Exception:
                    continue

            return None

        except Exception as e:
            logger.error(f"Tesseract failed: {e}")
            return None

    async def _solve_with_cnn(self, image_path: str, captcha_type: str) -> Optional[str]:
        """Solve CAPTCHA using CNN model"""
        if not self.cnn_model:
            return None

        try:
            # This would be implemented with a trained CNN model
            # For now, it's a placeholder
            return None

        except Exception as e:
            logger.error(f"CNN captcha solving failed: {e}")
            return None

    def load_cnn_model(self, model_path: str):
        """Load a trained CNN model for captcha solving"""
        try:
            import torch
            self.cnn_model = torch.load(model_path, map_location='cpu')
            self.cnn_model.eval()
            logger.info(f"CNN captcha model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load CNN model: {e}")

    async def setup_self_hosted_service(self, service_url: str, api_key: str = None):
        """Setup self-hosted captcha service configuration"""
        self.self_hosted_endpoint = service_url
        if api_key:
            self.api_key = api_key

        # Test connection
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/res.php?action=getbalance") as response:
                    if response.status == 200:
                        logger.info("Self-hosted captcha service connection successful")
                        return True
        except Exception as e:
            logger.error(f"Failed to connect to self-hosted service: {e}")

        return False

class BaseScraper:
    """Base scraper class with common functionality"""

    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.captcha_solver = CaptchaSolver()
        self.session = None

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product information from BeautifulSoup object"""
        product_info = {
            'title': '',
            'price': 0.0,
            'currency': 'USD',
            'description': '',
            'rating': 0.0,
            'review_count': 0,
            'in_stock': True,
            'seller': '',
            'image_urls': [],
            'specifications': {}
        }

        # Generic extraction patterns
        # Title
        title_selectors = [
            'h1', '[data-testid="product-title"]', '.product-title',
            '#productTitle', '.pdp-product-name', '.product-name'
        ]
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                product_info['title'] = element.get_text(strip=True)
                break

        # Price
        price_selectors = [
            '.price', '.price-current', '[data-testid="price"]',
            '.a-price-whole', '.notranslate', '.price-display'
        ]
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        product_info['price'] = float(price_match.group())
                        break
                    except ValueError:
                        continue

        # Rating
        rating_selectors = [
            '[data-testid="rating"]', '.rating', '.stars',
            '.a-icon-alt', '.review-rating'
        ]
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        product_info['rating'] = float(rating_match.group())
                        break
                    except ValueError:
                        continue

        # Images
        img_elements = soup.find_all('img')
        product_info['image_urls'] = [
            urljoin(url, img.get('src', ''))
            for img in img_elements
            if img.get('src') and any(keyword in img.get('src', '').lower()
                                    for keyword in ['product', 'item', 'main'])
        ][:5]  # Limit to 5 images

        return product_info

class DirectAPIScraper(BaseScraper):
    """First layer: Direct API scraping"""

    async def scrape(self, url: str, product_query: str) -> Dict:
        """Attempt to scrape using direct API calls"""
        try:
            # Check if site has known API endpoints
            api_endpoints = self._discover_api_endpoints(url)

            for endpoint in api_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {'User-Agent': self.proxy_manager.get_user_agent()}
                        async with session.get(endpoint, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return {
                                    'status': 'success',
                                    'method': 'api',
                                    'data': data,
                                    'url': endpoint
                                }
                except Exception:
                    continue

            return {'status': 'failed', 'method': 'api', 'error': 'No working API found'}

        except Exception as e:
            return {'status': 'failed', 'method': 'api', 'error': str(e)}

    def _discover_api_endpoints(self, url: str) -> List[str]:
        """Discover potential API endpoints"""
        domain = urlparse(url).netloc
        endpoints = []

        # Common API patterns
        api_patterns = [
            f"https://{domain}/api/products/search",
            f"https://{domain}/api/v1/search",
            f"https://{domain}/search.json",
            f"https://{domain}/api/product",
        ]

        endpoints.extend(api_patterns)
        return endpoints

class HTMLParseScraper(BaseScraper):
    """Second layer: HTML parsing scraping"""

    async def scrape(self, url: str, product_query: str) -> Dict:
        """Scrape using HTML parsing with requests"""
        try:
            proxy = await self.proxy_manager.get_proxy()
            headers = {
                'User-Agent': self.proxy_manager.get_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            proxies = {'http': proxy['url'], 'https': proxy['url']} if proxy else None

            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                product_info = self.extract_product_info(soup, url)

                return {
                    'status': 'success',
                    'method': 'html_parse',
                    'data': product_info,
                    'url': url
                }
            else:
                return {
                    'status': 'failed',
                    'method': 'html_parse',
                    'error': f'HTTP {response.status_code}'
                }

        except Exception as e:
            if proxy:
                self.proxy_manager.report_failure(proxy['url'])
            return {'status': 'failed', 'method': 'html_parse', 'error': str(e)}

class HeadlessBrowserScraper(BaseScraper):
    """Third layer: Headless browser scraping"""

    async def scrape(self, url: str, product_query: str) -> Dict:
        """Scrape using headless browser (Playwright)"""
        try:
            async with async_playwright() as p:
                # Launch browser with stealth mode
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                context = await browser.new_context(
                    user_agent=self.proxy_manager.get_user_agent(),
                    viewport={'width': 1920, 'height': 1080}
                )

                page = await context.new_page()

                # Add stealth scripts
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)

                # Navigate to page
                await page.goto(url, wait_until='networkidle')

                # Wait for content to load
                await page.wait_for_timeout(2000)

                # Check for CAPTCHA
                captcha_selectors = ['.captcha', '#captcha', '[data-testid="captcha"]']
                for selector in captcha_selectors:
                    captcha_element = await page.query_selector(selector)
                    if captcha_element:
                        logger.warning("CAPTCHA detected, attempting to solve")
                        # Handle CAPTCHA (simplified)
                        await page.wait_for_timeout(5000)  # Wait for manual solving
                        break

                # Extract content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                product_info = self.extract_product_info(soup, url)

                await browser.close()

                return {
                    'status': 'success',
                    'method': 'browser',
                    'data': product_info,
                    'url': url
                }

        except Exception as e:
            return {'status': 'failed', 'method': 'browser', 'error': str(e)}

class AdaptiveScrapingEngine:
    """Main adaptive scraping engine that tries multiple strategies"""

    def __init__(self):
        self.proxy_manager = None  # ProxyManager not yet implemented
        self.strategies = [
            DirectAPIScraper(self.proxy_manager),
            HTMLParseScraper(self.proxy_manager),
            HeadlessBrowserScraper(self.proxy_manager)
        ]
        self.failure_patterns = {}

    async def scrape_product(self, url: str, product_query: str = "") -> Dict:
        """
        Execute adaptive scraping using multiple strategies

        Args:
            url: Target URL to scrape
            product_query: Search query for the product

        Returns:
            Scraping results with fallback handling
        """
        start_time = time.time()
        site_name = urlparse(url).netloc

        logger.info(f"Starting adaptive scraping for {site_name}")

        for i, strategy in enumerate(self.strategies):
            try:
                logger.info(f"Trying strategy {i+1}: {strategy.__class__.__name__}")

                result = await strategy.scrape(url, product_query)

                if result.get('status') == 'success':
                    processing_time = time.time() - start_time
                    result['processing_time'] = processing_time
                    result['strategy_used'] = strategy.__class__.__name__

                    SCRAPING_COUNT.labels(site=site_name, status='success').inc()
                    logger.info(f"Scraping successful with {strategy.__class__.__name__}")

                    return result
                else:
                    # Learn from failure
                    self._learn_from_failure(site_name, strategy.__class__.__name__, result)

            except Exception as e:
                logger.error(f"Strategy {strategy.__class__.__name__} failed: {e}")
                self._learn_from_failure(site_name, strategy.__class__.__name__, {'error': str(e)})
                continue

        # All strategies failed
        processing_time = time.time() - start_time
        SCRAPING_COUNT.labels(site=site_name, status='failed').inc()

        return {
            'status': 'failed',
            'error': 'All scraping strategies failed',
            'processing_time': processing_time,
            'url': url
        }

    def _learn_from_failure(self, site: str, strategy: str, result: Dict):
        """Learn from scraping failures to improve future attempts"""
        if site not in self.failure_patterns:
            self.failure_patterns[site] = {}

        if strategy not in self.failure_patterns[site]:
            self.failure_patterns[site][strategy] = []

        self.failure_patterns[site][strategy].append({
            'error': result.get('error', 'Unknown'),
            'timestamp': time.time()
        })

        # Log patterns for analysis
        logger.info(f"Failure pattern recorded: {site} - {strategy} - {result.get('error', 'Unknown')}")


class ScrapyServiceClient:
    """
    Client for integrating with the Scrapy service
    Provides access to 17+ retailers with full service integration

    Features:
    - Voice search via /api/search/voice
    - Image search via /api/search/image
    - Bulk search via /api/search/bulk
    - CLIP image analysis integration
    - CAPTCHA solving integration
    - HAProxy proxy rotation
    - Redis caching
    """

    def __init__(self, base_url: str = "http://scrapy_scraper:5000"):
        self.base_url = base_url
        self.session = None
        self.available = False
        self.supported_retailers = []

    async def initialize(self):
        """Initialize Scrapy service client"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    health = await response.json()
                    self.available = True
                    logger.info(f"✅ Scrapy service: {health.get('status')}")
                    logger.info(f"   Retailers: {health.get('retailers_supported', 0)}")
                    logger.info(f"   Services: {', '.join(health.get('services', {}).keys())}")

                    # Get supported retailers
                    retailers_resp = await self.session.get(f"{self.base_url}/api/retailers")
                    if retailers_resp.status == 200:
                        retailers_data = await retailers_resp.json()
                        self.supported_retailers = retailers_data.get('retailers', [])

                    return True
                else:
                    logger.warning(f"⚠️ Scrapy service unhealthy: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Scrapy service unavailable: {e}")
            self.available = False
            return False

    async def search(self, query: str, retailers: List[str] = None, max_results: int = 10) -> Dict:
        """
        Search for products across retailers

        Args:
            query: Search query
            retailers: List of retailer names (defaults to top 10)
            max_results: Maximum results per retailer

        Returns:
            Dict with products and metadata
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            logger.warning("Scrapy service not available for search")
            return {'products': [], 'error': 'Service unavailable'}

        try:
            payload = {
                'query': query,
                'sites': retailers or self.supported_retailers[:10]
            }

            async with self.session.post(
                f"{self.base_url}/api/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status in [200, 202]:  # Both OK and Accepted
                    result = await response.json()
                    logger.info(f"✅ Scrapy search completed: {result.get('total_products', 0)} products found")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Scrapy search failed: {response.status} - {error}")
                    return {'error': f'Search failed: {response.status}'}

        except Exception as e:
            logger.error(f"Scrapy search error: {e}")
            return {'error': str(e)}

    async def voice_search(self, audio_file_path: str) -> Dict:
        """
        Voice-based product search

        Args:
            audio_file_path: Path to audio file

        Returns:
            Dict with transcription and search results
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            logger.warning("Scrapy service not available for voice search")
            return {'error': 'Service unavailable'}

        try:
            with open(audio_file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('audio', f, filename='audio.wav')

                async with self.session.post(
                    f"{self.base_url}/api/search/voice",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    result = await response.json()
                    logger.info(f"✅ Voice search completed")
                    return result

        except Exception as e:
            logger.error(f"Voice search error: {e}")
            return {'error': str(e)}

    async def image_search(self, image_file_path: str) -> Dict:
        """
        Image-based product search using CLIP

        Args:
            image_file_path: Path to image file

        Returns:
            Dict with CLIP analysis and search results
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            logger.warning("Scrapy service not available for image search")
            return {'error': 'Service unavailable'}

        try:
            with open(image_file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('image', f, filename='image.jpg')

                async with self.session.post(
                    f"{self.base_url}/api/search/image",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    result = await response.json()
                    logger.info(f"✅ Image search completed")
                    return result

        except Exception as e:
            logger.error(f"Image search error: {e}")
            return {'error': str(e)}

    async def bulk_search(self, queries: List[str], retailers: List[str] = None) -> Dict:
        """
        Bulk search across multiple queries and retailers

        Args:
            queries: List of search queries
            retailers: List of retailer names (defaults to all)

        Returns:
            Dict with batch_id and job info
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            logger.warning("Scrapy service not available for bulk search")
            return {'error': 'Service unavailable'}

        try:
            payload = {
                'queries': queries,
                'retailers': retailers or self.supported_retailers
            }

            async with self.session.post(
                f"{self.base_url}/api/search/bulk",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 202:  # Accepted
                    result = await response.json()
                    logger.info(f"✅ Bulk search queued: {result.get('jobs_queued')} jobs")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Bulk search failed: {response.status} - {error}")
                    return {'error': f'Bulk search failed: {response.status}'}

        except Exception as e:
            logger.error(f"Bulk search error: {e}")
            return {'error': str(e)}

    async def get_batch_status(self, batch_id: str) -> Dict:
        """
        Get status of a bulk search batch

        Args:
            batch_id: Batch identifier

        Returns:
            Dict with batch status and progress
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            return {'error': 'Service unavailable'}

        try:
            async with self.session.get(
                f"{self.base_url}/api/batch/{batch_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                result = await response.json()
                return result

        except Exception as e:
            logger.error(f"Batch status error: {e}")
            return {'error': str(e)}

    async def get_stats(self) -> Dict:
        """
        Get Scrapy service statistics

        Returns:
            Dict with service statistics
        """
        if not self.session:
            await self.initialize()

        if not self.available:
            return {'error': 'Service unavailable'}

        try:
            async with self.session.get(
                f"{self.base_url}/api/stats",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                result = await response.json()
                return result

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {'error': str(e)}

    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None


# Global scraping engine instance
scraping_engine = AdaptiveScrapingEngine()

# Global Scrapy service client
scrapy_client = ScrapyServiceClient()
