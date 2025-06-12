"""
Enhanced Adaptive Scraping Engine with Anti-Block Measures
Integrates proxy management, stealth browsing, and CAPTCHA solving
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import json
import logging

from app.services.stealth_browser import StealthBrowser, StealthSessionManager
from app.services.scraping import EnhancedProxyManager, CaptchaSolver
from app.core.config import settings
from app.core.monitoring import logger

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    method_used: Optional[str] = None
    proxy_used: Optional[str] = None
    captcha_solved: bool = False
    response_time: float = 0.0
    retry_count: int = 0

@dataclass
class ScrapingStrategy:
    """Configuration for a scraping strategy"""
    name: str
    priority: int
    requires_proxy: bool = False
    requires_browser: bool = False
    max_retries: int = 3
    timeout: int = 30
    success_rate_threshold: float = 0.7

class AdaptiveScrapingEngine:
    """
    Enhanced adaptive scraping engine with multiple strategies and anti-block measures
    """
    
    def __init__(self):
        self.proxy_manager = EnhancedProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.session_manager = StealthSessionManager(max_concurrent=3)
        self.strategy_stats = {}  # Track success rates per strategy
        
        # Define scraping strategies in order of preference
        self.strategies = [
            ScrapingStrategy("direct_api", 1, requires_proxy=False, requires_browser=False),
            ScrapingStrategy("simple_http", 2, requires_proxy=True, requires_browser=False),
            ScrapingStrategy("stealth_browser", 3, requires_proxy=True, requires_browser=True),
            ScrapingStrategy("full_browser", 4, requires_proxy=True, requires_browser=True, timeout=60)
        ]
        
        # Site-specific configurations
        self.site_configs = {
            'amazon.com': {
                'selectors': {
                    'title': '#productTitle',
                    'price': '.a-price-whole',
                    'rating': '.a-icon-alt',
                    'availability': '#availability span'
                },
                'anti_bot_indicators': [
                    'robot check',
                    'captcha',
                    'automated queries'
                ],
                'required_strategy': 'stealth_browser'
            },
            'ebay.com': {
                'selectors': {
                    'title': 'h1#x-title-label-lbl',
                    'price': '.notranslate',
                    'condition': '.u-flL.condText'
                },
                'anti_bot_indicators': [
                    'security challenge',
                    'verify you are human'
                ]
            },
            'default': {
                'selectors': {
                    'title': ['h1', '.product-title', '[data-testid="product-title"]'],
                    'price': ['.price', '.cost', '[data-testid="price"]'],
                    'rating': ['.rating', '.stars', '[data-testid="rating"]']
                }
            }
        }
    
    async def scrape_product(self, url: str, **kwargs) -> ScrapingResult:
        """
        Scrape product information using adaptive strategies
        """
        start_time = time.time()
        domain = urlparse(url).netloc.lower()
        
        # Get site-specific configuration
        site_config = self._get_site_config(domain)
        
        # Determine optimal strategy based on domain and success rates
        strategy = await self._select_strategy(domain, site_config)
        
        logger.info(f"🎯 Scraping {url} using strategy: {strategy.name}")
        
        # Execute scraping with selected strategy
        result = await self._execute_strategy(url, strategy, site_config, **kwargs)
        result.response_time = time.time() - start_time
        
        # Update strategy statistics
        self._update_strategy_stats(domain, strategy.name, result.success)
        
        return result
    
    def _get_site_config(self, domain: str) -> Dict:
        """Get site-specific configuration"""
        # Remove 'www.' prefix and check for exact match
        clean_domain = domain.replace('www.', '')
        
        for site_domain, config in self.site_configs.items():
            if site_domain in clean_domain:
                return config
        
        return self.site_configs['default']
    
    async def _select_strategy(self, domain: str, site_config: Dict) -> ScrapingStrategy:
        """Select optimal scraping strategy based on domain and success rates"""
        
        # Check if site requires specific strategy
        required_strategy = site_config.get('required_strategy')
        if required_strategy:
            for strategy in self.strategies:
                if strategy.name == required_strategy:
                    return strategy
        
        # Select based on success rates and strategy priority
        best_strategy = None
        best_score = -1
        
        for strategy in self.strategies:
            # Get success rate for this domain + strategy combination
            key = f"{domain}:{strategy.name}"
            stats = self.strategy_stats.get(key, {'attempts': 0, 'successes': 0})
            
            if stats['attempts'] > 0:
                success_rate = stats['successes'] / stats['attempts']
            else:
                success_rate = 0.8  # Default optimistic rate for untested strategies
            
            # Calculate score: success_rate / priority (lower priority = higher score)
            score = success_rate / strategy.priority
            
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy or self.strategies[0]
    
    async def _execute_strategy(self, url: str, strategy: ScrapingStrategy, site_config: Dict, **kwargs) -> ScrapingResult:
        """Execute scraping with the selected strategy"""
        
        for retry in range(strategy.max_retries):
            try:
                if strategy.name == "direct_api":
                    result = await self._scrape_direct_api(url, site_config, **kwargs)
                elif strategy.name == "simple_http":
                    result = await self._scrape_simple_http(url, site_config, **kwargs)
                elif strategy.name == "stealth_browser":
                    result = await self._scrape_stealth_browser(url, site_config, **kwargs)
                elif strategy.name == "full_browser":
                    result = await self._scrape_full_browser(url, site_config, **kwargs)
                else:
                    result = ScrapingResult(False, error=f"Unknown strategy: {strategy.name}")
                
                result.method_used = strategy.name
                result.retry_count = retry
                
                if result.success:
                    return result
                
                # If anti-bot detection, escalate to more sophisticated strategy
                if result.error and any(indicator in result.error.lower() 
                                      for indicator in site_config.get('anti_bot_indicators', [])):
                    logger.warning(f"🤖 Anti-bot detection triggered, escalating strategy")
                    break
                
                # Wait before retry with exponential backoff
                if retry < strategy.max_retries - 1:
                    delay = (2 ** retry) + random.uniform(1, 3)
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Strategy {strategy.name} error on attempt {retry + 1}: {e}")
                
                if retry == strategy.max_retries - 1:
                    return ScrapingResult(False, error=str(e), method_used=strategy.name, retry_count=retry)
        
        # If all retries failed, try escalating to next strategy
        current_index = self.strategies.index(strategy)
        if current_index < len(self.strategies) - 1:
            next_strategy = self.strategies[current_index + 1]
            logger.info(f"🔄 Escalating to strategy: {next_strategy.name}")
            return await self._execute_strategy(url, next_strategy, site_config, **kwargs)
        
        return ScrapingResult(False, error="All strategies failed", method_used=strategy.name)
    
    async def _scrape_direct_api(self, url: str, site_config: Dict, **kwargs) -> ScrapingResult:
        """Attempt direct API scraping (fastest method)"""
        try:
            # This would integrate with known APIs (Amazon Product API, etc.)
            # For now, return not supported
            return ScrapingResult(False, error="Direct API not available for this site")
            
        except Exception as e:
            return ScrapingResult(False, error=f"Direct API error: {e}")
    
    async def _scrape_simple_http(self, url: str, site_config: Dict, **kwargs) -> ScrapingResult:
        """Simple HTTP scraping with proxy and user agent rotation"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            # Get proxy
            proxy = await self.proxy_manager.get_proxy()
            user_agent = self.proxy_manager.get_user_agent()
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                proxy_url = proxy['url'] if proxy else None
                
                async with session.get(url, headers=headers, proxy=proxy_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Check for anti-bot indicators
                        if any(indicator in html.lower() 
                              for indicator in site_config.get('anti_bot_indicators', [])):
                            return ScrapingResult(False, error="Anti-bot detection triggered")
                        
                        # Parse with BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        data = self._extract_product_data(soup, site_config, url)
                        
                        return ScrapingResult(True, data=data, proxy_used=proxy_url)
                    else:
                        return ScrapingResult(False, error=f"HTTP {response.status}")
                        
        except Exception as e:
            return ScrapingResult(False, error=f"Simple HTTP error: {e}")
    
    async def _scrape_stealth_browser(self, url: str, site_config: Dict, **kwargs) -> ScrapingResult:
        """Stealth browser scraping with CAPTCHA solving"""
        try:
            # Get proxy for browser
            proxy = await self.proxy_manager.get_proxy()
            proxy_url = proxy['url'] if proxy else None
            
            # Get stealth browser session
            domain = urlparse(url).netloc
            browser = await self.session_manager.get_session(domain)
            
            try:
                # Create stealth page
                page = await browser.create_page()
                
                # Navigate with stealth
                nav_success = await browser.navigate_with_stealth(page, url)
                if not nav_success:
                    return ScrapingResult(False, error="Navigation failed")
                
                # Check for CAPTCHA and solve if present
                captcha_solved = await browser.solve_captcha_challenge(page)
                
                # Extract content
                html = await browser.get_page_content(page)
                if html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    data = self._extract_product_data(soup, site_config, url)
                    
                    return ScrapingResult(
                        True, 
                        data=data, 
                        proxy_used=proxy_url,
                        captcha_solved=captcha_solved
                    )
                else:
                    return ScrapingResult(False, error="Failed to get page content")
                    
            finally:
                await self.session_manager.release_session(browser)
                
        except Exception as e:
            return ScrapingResult(False, error=f"Stealth browser error: {e}")
    
    async def _scrape_full_browser(self, url: str, site_config: Dict, **kwargs) -> ScrapingResult:
        """Full browser scraping with maximum stealth and human simulation"""
        try:
            # Similar to stealth browser but with more extensive human simulation
            proxy = await self.proxy_manager.get_proxy()
            proxy_url = proxy['url'] if proxy else None
            
            browser = await self.session_manager.get_session(urlparse(url).netloc)
            
            try:
                page = await browser.create_page()
                
                # Extended navigation with more human-like behavior
                nav_success = await browser.navigate_with_stealth(page, url)
                if not nav_success:
                    return ScrapingResult(False, error="Navigation failed")
                
                # Extended human behavior simulation
                await asyncio.sleep(random.uniform(3, 8))  # Longer reading time
                
                # Multiple scroll and interaction attempts
                for _ in range(random.randint(2, 4)):
                    await page.evaluate("""
                        window.scrollBy({
                            top: Math.random() * 500 + 200,
                            behavior: 'smooth'
                        });
                    """)
                    await asyncio.sleep(random.uniform(1, 3))
                
                # Check and solve CAPTCHA
                captcha_solved = await browser.solve_captcha_challenge(page)
                
                # Wait for dynamic content
                await page.wait_for_load_state('networkidle', timeout=30000)
                
                # Extract data
                html = await browser.get_page_content(page)
                if html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    data = self._extract_product_data(soup, site_config, url)
                    
                    return ScrapingResult(
                        True, 
                        data=data, 
                        proxy_used=proxy_url,
                        captcha_solved=captcha_solved
                    )
                else:
                    return ScrapingResult(False, error="Failed to get page content")
                    
            finally:
                await self.session_manager.release_session(browser)
                
        except Exception as e:
            return ScrapingResult(False, error=f"Full browser error: {e}")
    
    def _extract_product_data(self, soup, site_config: Dict, url: str) -> Dict:
        """Extract product data using site-specific selectors"""
        data = {
            'title': '',
            'price': 0.0,
            'currency': 'USD',
            'rating': 0.0,
            'availability': '',
            'description': '',
            'image_urls': [],
            'specifications': {},
            'source_url': url
        }
        
        selectors = site_config.get('selectors', {})
        
        # Extract title
        title_selectors = selectors.get('title', [])
        if isinstance(title_selectors, str):
            title_selectors = [title_selectors]
            
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                data['title'] = element.get_text(strip=True)
                break
        
        # Extract price
        price_selectors = selectors.get('price', [])
        if isinstance(price_selectors, str):
            price_selectors = [price_selectors]
            
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric price
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        data['price'] = float(price_match.group())
                        break
                    except ValueError:
                        continue
        
        # Extract rating
        rating_selectors = selectors.get('rating', [])
        if isinstance(rating_selectors, str):
            rating_selectors = [rating_selectors]
            
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        data['rating'] = float(rating_match.group())
                        break
                    except ValueError:
                        continue
        
        # Extract images
        img_elements = soup.find_all('img')
        data['image_urls'] = [
            urljoin(url, img.get('src', '')) 
            for img in img_elements[:5]  # Limit to first 5 images
            if img.get('src') and not img.get('src').startswith('data:')
        ]
        
        return data
    
    def _update_strategy_stats(self, domain: str, strategy_name: str, success: bool):
        """Update strategy success statistics"""
        key = f"{domain}:{strategy_name}"
        
        if key not in self.strategy_stats:
            self.strategy_stats[key] = {'attempts': 0, 'successes': 0}
        
        self.strategy_stats[key]['attempts'] += 1
        if success:
            self.strategy_stats[key]['successes'] += 1
    
    async def get_strategy_stats(self) -> Dict:
        """Get current strategy statistics"""
        return {
            key: {
                **stats,
                'success_rate': stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0
            }
            for key, stats in self.strategy_stats.items()
        }
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.session_manager.cleanup()
            logger.info("✅ Adaptive scraping engine cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

# Global scraping engine instance
adaptive_scraper = AdaptiveScrapingEngine()
