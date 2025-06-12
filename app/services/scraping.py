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
    """Client to communicate with our dedicated scraper service"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = None
        
    async def initialize(self):
        """Initialize the scraper client session"""
        self.session = aiohttp.ClientSession()
        
        # Test connection to scraper service
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ Connected to dedicated scraper service")
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Dedicated scraper service not available: {e}")
            return False
        
    async def scrape_url(self, url: str, options: Dict = None) -> Dict:
        """Scrape a single URL using the dedicated scraper"""
        if not self.session:
            await self.initialize()
            
        try:
            payload = {"url": url}
            if options:
                payload.update(options)
                
            async with self.session.post(
                f"{self.base_url}/api/scrape",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if result.get("success"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "url": url,
                        "timestamp": result.get("timestamp"),
                        "response_time": result.get("responseTime")
                    }
                else:
                    return {
                        "status": "failed",
                        "error": result.get("error", "Unknown error"),
                        "url": url
                    }
                    
        except Exception as e:
            logger.error(f"❌ Scraper service error for {url}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "url": url
            }
    
    async def scrape_batch(self, urls: List[str], options: Dict = None) -> List[Dict]:
        """Scrape multiple URLs concurrently"""
        if not self.session:
            await self.initialize()
            
        try:
            payload = {"urls": urls}
            if options:
                payload.update(options)
                
            async with self.session.post(
                f"{self.base_url}/api/scrape/batch",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                results = await response.json()
                return results.get("results", [])
                
        except Exception as e:
            logger.error(f"❌ Batch scraper service error: {e}")
            return []
    
    async def get_stats(self) -> Dict:
        """Get scraper statistics"""
        if not self.session:
            await self.initialize()
            
        try:
            async with self.session.get(f"{self.base_url}/api/stats") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"❌ Error getting scraper stats: {e}")
            return {}
    
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
    
    def __init__(self, proxy_manager: ProxyManager):
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
        self.proxy_manager = ProxyManager()
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

# Global scraping engine instance
scraping_engine = AdaptiveScrapingEngine()
