"""
Adaptive Web Scraping Engine - Multi-layer scraping with anti-blocking measures
Implements direct API, HTML parsing, and headless browser strategies
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
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import re

from app.core.config import settings
from app.core.monitoring import SCRAPING_COUNT, logger

class ProxyManager:
    """Manages proxy rotation and failure handling"""
    
    def __init__(self):
        self.proxy_pool = []
        self.failed_proxies = set()
        self.rota_client_url = settings.rota_url
        self.ua = UserAgent()
    
    async def get_proxy(self) -> Optional[Dict]:
        """Get a working proxy from the pool"""
        if not self.proxy_pool:
            await self.refresh_proxy_pool()
        
        for proxy in self.proxy_pool:
            if proxy['url'] not in self.failed_proxies:
                return proxy
        
        # If all proxies failed, refresh pool
        await self.refresh_proxy_pool()
        return self.proxy_pool[0] if self.proxy_pool else None
    
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
    """CAPTCHA solving using Tesseract and CNN fallback"""
    
    def __init__(self):
        self.cnn_model = None
        # Load CNN model if available
        # self._load_cnn_model()
    
    def solve_captcha(self, image_path: str) -> Optional[str]:
        """
        Solve CAPTCHA using multiple methods
        
        Args:
            image_path: Path to CAPTCHA image
            
        Returns:
            Solved CAPTCHA text or None
        """
        try:
            import pytesseract
            from PIL import Image, ImageFilter
            import numpy as np
            
            # Load and preprocess image
            img = Image.open(image_path).convert('L')
            img = img.filter(ImageFilter.SHARPEN)
            img_array = np.array(img)
            
            # Adaptive thresholding
            img_array = np.where(img_array > 128, 255, 0)
            
            # OCR with Tesseract
            text = pytesseract.image_to_string(img_array, config='--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            text = text.strip()
            
            if text and text.isalnum() and len(text) >= 4:
                logger.info(f"CAPTCHA solved with Tesseract: {text}")
                return text
            
            # Fallback to CNN if available
            if self.cnn_model:
                text = self._solve_with_cnn(img_array)
                if text:
                    logger.info(f"CAPTCHA solved with CNN: {text}")
                    return text
            
            logger.warning("Failed to solve CAPTCHA")
            return None
            
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None
    
    def _solve_with_cnn(self, image_array) -> Optional[str]:
        """Solve CAPTCHA using CNN model (placeholder)"""
        # Implement CNN-based CAPTCHA solving
        # This would require a trained model
        return None

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
