"""
Advanced Stealth Browser System for Cumpair
Implements comprehensive anti-detection measures with Playwright
"""

import asyncio
import random
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrowserFingerprint:
    """Browser fingerprint configuration"""
    user_agent: str
    viewport: Dict[str, int]
    screen: Dict[str, int]
    timezone: str
    locale: str
    platform: str
    hardware_concurrency: int
    device_memory: int
    webgl_vendor: str
    webgl_renderer: str

@dataclass
class HumanBehavior:
    """Human-like interaction patterns"""
    typing_delay_range: tuple = (50, 150)  # ms
    click_delay_range: tuple = (100, 300)  # ms
    scroll_delay_range: tuple = (1000, 3000)  # ms
    page_load_wait_range: tuple = (2000, 5000)  # ms
    mouse_movement_steps: int = random.randint(10, 30)

class StealthBrowser:
    """Advanced stealth browser with comprehensive anti-detection"""
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.proxy_url = proxy_url
        self.fingerprint = self._generate_fingerprint()
        self.behavior = HumanBehavior()
        self._active_pages = {}
        
    async def initialize(self) -> bool:
        """Initialize the stealth browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser launch options with stealth configuration
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-popup-blocking',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-translate',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    '--no-default-browser-check',
                    '--no-first-run-suggestions',
                    '--disable-component-update'
                ]
            }
            
            # Add proxy if provided
            if self.proxy_url:
                proxy_config = self._parse_proxy_url(self.proxy_url)
                launch_options['proxy'] = proxy_config
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Create stealth context
            await self._create_stealth_context()
            
            logger.info("✅ Stealth browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize stealth browser: {e}")
            return False
    
    async def _create_stealth_context(self):
        """Create a browser context with stealth configurations"""
        context_options = {
            'viewport': self.fingerprint.viewport,
            'user_agent': self.fingerprint.user_agent,
            'locale': self.fingerprint.locale,
            'timezone_id': self.fingerprint.timezone,
            'java_script_enabled': True,
            'bypass_csp': True,
            'ignore_https_errors': True,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': f'{self.fingerprint.locale},en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        }
        
        self.context = await self.browser.new_context(**context_options)
        
        # Add stealth scripts to all pages
        await self.context.add_init_script(self._get_stealth_script())
        
        # Set up request/response interception
        self.context.on('request', self._handle_request)
        self.context.on('response', self._handle_response)
    
    def _generate_fingerprint(self) -> BrowserFingerprint:
        """Generate a realistic browser fingerprint"""
        # Common user agents with realistic configurations
        user_agents = [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'platform': 'Win32',
                'viewport': {'width': 1920, 'height': 1080},
                'screen': {'width': 1920, 'height': 1080}
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'platform': 'MacIntel',
                'viewport': {'width': 1440, 'height': 900},
                'screen': {'width': 1440, 'height': 900}
            },
            {
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'platform': 'Linux x86_64',
                'viewport': {'width': 1366, 'height': 768},
                'screen': {'width': 1366, 'height': 768}
            }
        ]
        
        config = random.choice(user_agents)
        
        return BrowserFingerprint(
            user_agent=config['user_agent'],
            viewport=config['viewport'],
            screen=config['screen'],
            timezone=random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Berlin']),
            locale=random.choice(['en-US', 'en-GB', 'de-DE', 'fr-FR']),
            platform=config['platform'],
            hardware_concurrency=random.choice([4, 8, 12, 16]),
            device_memory=random.choice([4, 8, 16, 32]),
            webgl_vendor='Google Inc. (Intel)',
            webgl_renderer=random.choice([
                'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
                'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
                'ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)'
            ])
        )
    
    def _get_stealth_script(self) -> str:
        """Generate comprehensive stealth JavaScript"""
        return f"""
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        // Override the `plugins` property to use a custom getter
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [{{
                0: {{
                    type: "application/x-google-chrome-pdf",
                    suffixes: "pdf",
                    description: "Portable Document Format",
                    enabledPlugin: Plugin
                }}
            }}],
        }});
        
        // Override the `languages` property to use a custom getter
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{self.fingerprint.locale}', 'en-US', 'en'],
        }});
        
        // Override the `hardwareConcurrency` property
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {self.fingerprint.hardware_concurrency},
        }});
        
        // Override the `deviceMemory` property
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {self.fingerprint.device_memory},
        }});
        
        // Override the `platform` property
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{self.fingerprint.platform}',
        }});
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {self.fingerprint.screen['width']},
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {self.fingerprint.screen['height']},
        }});
        Object.defineProperty(screen, 'availWidth', {{
            get: () => {self.fingerprint.screen['width']},
        }});
        Object.defineProperty(screen, 'availHeight', {{
            get: () => {self.fingerprint.screen['height'] - 40},
        }});
        
        // WebGL fingerprint spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{
                return '{self.fingerprint.webgl_vendor}';
            }}
            if (parameter === 37446) {{
                return '{self.fingerprint.webgl_renderer}';
            }}
            return getParameter(parameter);
        }};
        
        // Override Date.prototype.getTimezoneOffset
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {{
            return -300; // EST timezone offset
        }};
        
        // Spoof canvas fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        HTMLCanvasElement.prototype.toDataURL = function() {{
            const originalData = originalToDataURL.apply(this, arguments);
            // Add slight noise to canvas data
            return originalData.slice(0, -10) + Math.random().toString(36).substr(2, 9);
        }};
        
        CanvasRenderingContext2D.prototype.getImageData = function() {{
            const originalImageData = originalGetImageData.apply(this, arguments);
            // Add minimal noise to image data
            const data = originalImageData.data;
            for (let i = 0; i < data.length; i += 4) {{
                data[i] = data[i] + Math.floor(Math.random() * 3) - 1;
            }}
            return originalImageData;
        }};
        
        // Override permission queries
        const originalQuery = Permissions.prototype.query;
        Permissions.prototype.query = function(parameters) {{
            return originalQuery.apply(this, arguments).then(result => {{
                if (parameters.name === 'notifications') {{
                    result.state = 'default';
                }}
                return result;
            }});
        }};
        
        // Remove automation indicators
        window.chrome = {{
            runtime: {{
                onConnect: null,
                onMessage: null
            }}
        }};
        
        // Add noise to performance timing
        const originalNow = Performance.prototype.now;
        Performance.prototype.now = function() {{
            return originalNow.apply(this, arguments) + Math.random() * 0.1;
        }};
        
        // Override Intl.DateTimeFormat
        const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
            const options = originalResolvedOptions.apply(this, arguments);
            options.timeZone = '{self.fingerprint.timezone}';
            return options;
        }};
        """
    
    def _parse_proxy_url(self, proxy_url: str) -> Dict:
        """Parse proxy URL into Playwright proxy config"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(proxy_url)
            
            proxy_config = {
                'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            }
            
            if parsed.username and parsed.password:
                proxy_config['username'] = parsed.username
                proxy_config['password'] = parsed.password
            
            return proxy_config
            
        except Exception as e:
            logger.error(f"Failed to parse proxy URL {proxy_url}: {e}")
            return {}
    
    async def _handle_request(self, request):
        """Handle outgoing requests for additional stealth"""
        # Add random delays to requests
        if random.random() < 0.1:  # 10% of requests get a small delay
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Log request for debugging
        logger.debug(f"🌐 Request: {request.method} {request.url}")
    
    async def _handle_response(self, response):
        """Handle incoming responses"""
        # Log response for debugging
        logger.debug(f"📥 Response: {response.status} {response.url}")
    
    async def create_page(self, url: Optional[str] = None) -> Page:
        """Create a new stealth page"""
        if not self.context:
            await self.initialize()
        
        page = await self.context.new_page()
        page_id = f"page_{len(self._active_pages)}"
        self._active_pages[page_id] = page
        
        # Set additional page-specific stealth measures
        await page.set_extra_http_headers({
            'Referer': 'https://www.google.com/',
            'Origin': 'https://www.google.com',
        })
        
        # Add page event handlers
        page.on('dialog', lambda dialog: asyncio.create_task(dialog.dismiss()))
        
        if url:
            await self.navigate_with_stealth(page, url)
        
        return page
    
    async def navigate_with_stealth(self, page: Page, url: str, **kwargs) -> bool:
        """Navigate to URL with human-like behavior"""
        try:
            # Random pre-navigation delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate with timeout
            response = await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=30000,
                **kwargs
            )
            
            if not response or response.status >= 400:
                logger.warning(f"Navigation failed: {response.status if response else 'No response'}")
                return False
            
            # Post-navigation human behavior
            await self._simulate_human_behavior(page)
            
            logger.info(f"✅ Successfully navigated to: {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation failed for {url}: {e}")
            return False
    
    async def _simulate_human_behavior(self, page: Page):
        """Simulate human-like behavior on the page"""
        try:
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Random scroll behavior
            if random.random() < 0.7:  # 70% chance to scroll
                scroll_steps = random.randint(2, 5)
                for _ in range(scroll_steps):
                    await page.evaluate(f"""
                        window.scrollBy({{
                            top: {random.randint(100, 500)},
                            behavior: 'smooth'
                        }});
                    """)
                    await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Random mouse movements
            if random.random() < 0.5:  # 50% chance for mouse movement
                viewport = page.viewport_size
                for _ in range(random.randint(1, 3)):
                    x = random.randint(0, viewport['width'])
                    y = random.randint(0, viewport['height'])
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Random pause to mimic reading
            reading_time = random.uniform(2, 8)
            await asyncio.sleep(reading_time)
            
        except Exception as e:
            logger.debug(f"Human behavior simulation error: {e}")
    
    async def human_type(self, page: Page, selector: str, text: str):
        """Type text with human-like delays"""
        element = await page.wait_for_selector(selector, timeout=10000)
        await element.click()
        
        # Clear existing text
        await element.fill('')
        
        # Type character by character with realistic delays
        for char in text:
            await element.type(char)
            delay = random.randint(*self.behavior.typing_delay_range)
            await asyncio.sleep(delay / 1000)
    
    async def human_click(self, page: Page, selector: str, **kwargs):
        """Click with human-like behavior"""
        element = await page.wait_for_selector(selector, timeout=10000)
        
        # Get element position
        box = await element.bounding_box()
        if not box:
            await element.click(**kwargs)
            return
        
        # Calculate random click position within element
        x = box['x'] + random.uniform(0.1, 0.9) * box['width']
        y = box['y'] + random.uniform(0.1, 0.9) * box['height']
        
        # Move mouse to position with human-like path
        await page.mouse.move(x, y, steps=self.behavior.mouse_movement_steps)
        
        # Random pre-click delay
        delay = random.randint(*self.behavior.click_delay_range)
        await asyncio.sleep(delay / 1000)
        
        # Click
        await page.mouse.click(x, y)
        
        # Random post-click delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def solve_captcha_challenge(self, page: Page) -> bool:
        """Detect and solve CAPTCHA challenges"""
        try:
            # Common CAPTCHA selectors
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                '.captcha',
                '[data-testid="captcha"]',
                '#captcha',
                '.g-recaptcha',
                '.h-captcha',
                '.cloudflare-challenge'
            ]
            
            for selector in captcha_selectors:
                try:
                    captcha_element = await page.wait_for_selector(selector, timeout=2000)
                    if captcha_element:
                        logger.info(f"🔍 CAPTCHA detected: {selector}")
                        
                        # Handle different CAPTCHA types
                        if 'recaptcha' in selector:
                            return await self._solve_recaptcha(page, captcha_element)
                        elif 'cloudflare' in selector:
                            return await self._solve_cloudflare(page)
                        else:
                            return await self._solve_generic_captcha(page, captcha_element)
                            
                except Exception:
                    continue
            
            return True  # No CAPTCHA found
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA solving error: {e}")
            return False
    
    async def _solve_recaptcha(self, page: Page, captcha_element) -> bool:
        """Solve reCAPTCHA challenges"""
        try:
            # Check for checkbox reCAPTCHA
            checkbox = await page.query_selector('.recaptcha-checkbox-border')
            if checkbox:
                await self.human_click(page, '.recaptcha-checkbox-border')
                await asyncio.sleep(3)
                
                # Check if solved
                is_solved = await page.query_selector('.recaptcha-checkbox-checked')
                if is_solved:
                    logger.info("✅ reCAPTCHA checkbox solved")
                    return True
            
            # Handle image challenges (would integrate with captcha service)
            challenge_frame = await page.query_selector('iframe[title*="challenge"]')
            if challenge_frame:
                logger.info("🧩 Image challenge detected - would integrate with captcha service")
                # This would integrate with our self-hosted captcha service
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ reCAPTCHA solving error: {e}")
            return False
    
    async def _solve_cloudflare(self, page: Page) -> bool:
        """Handle Cloudflare challenges"""
        try:
            # Wait for Cloudflare to complete
            await page.wait_for_selector('.cf-browser-verification', timeout=5000)
            logger.info("⏳ Waiting for Cloudflare verification...")
            
            # Wait for redirect or completion
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if challenge is passed
            current_url = page.url
            if 'challenge' not in current_url.lower():
                logger.info("✅ Cloudflare challenge passed")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Cloudflare handling: {e}")
            return True  # Might not be a Cloudflare challenge
    
    async def _solve_generic_captcha(self, page: Page, captcha_element) -> bool:
        """Handle generic CAPTCHA challenges"""
        try:
            # Extract CAPTCHA image
            captcha_image = await captcha_element.screenshot()
            
            # This would integrate with our self-hosted captcha service
            logger.info("🧩 Generic CAPTCHA detected - would integrate with captcha service")
            
            return False  # Placeholder for captcha service integration
            
        except Exception as e:
            logger.error(f"❌ Generic CAPTCHA error: {e}")
            return False
    
    async def get_page_content(self, page: Page) -> Optional[str]:
        """Get page content with error handling"""
        try:
            return await page.content()
        except Exception as e:
            logger.error(f"❌ Failed to get page content: {e}")
            return None
    
    async def wait_for_selector_safe(self, page: Page, selector: str, timeout: int = 10000) -> bool:
        """Safely wait for selector with timeout"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self._active_pages.clear()
            logger.info("✅ Stealth browser cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Browser cleanup error: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

# Rate limiting and session management
class StealthSessionManager:
    """Manages multiple stealth browser sessions with rate limiting"""
    
    def __init__(self, max_concurrent: int = 5, proxy_pool: List[str] = None):
        self.max_concurrent = max_concurrent
        self.proxy_pool = proxy_pool or []
        self.active_sessions = {}
        self.session_semaphore = asyncio.Semaphore(max_concurrent)
        self.request_rates = {}  # domain -> last_request_time
        
    async def get_session(self, domain: str = None) -> StealthBrowser:
        """Get a stealth browser session with rate limiting"""
        await self.session_semaphore.acquire()
        
        try:
            # Select proxy for this session
            proxy_url = None
            if self.proxy_pool:
                proxy_url = random.choice(self.proxy_pool)
            
            # Create new stealth browser
            browser = StealthBrowser(proxy_url=proxy_url)
            await browser.initialize()
            
            # Rate limiting by domain
            if domain:
                await self._enforce_rate_limit(domain)
            
            return browser
            
        except Exception as e:
            self.session_semaphore.release()
            raise e
    
    async def _enforce_rate_limit(self, domain: str, min_delay: float = 2.0):
        """Enforce rate limiting per domain"""
        last_request = self.request_rates.get(domain, 0)
        time_since_last = time.time() - last_request
        
        if time_since_last < min_delay:
            delay = min_delay - time_since_last + random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
        
        self.request_rates[domain] = time.time()
    
    async def release_session(self, browser: StealthBrowser):
        """Release a browser session"""
        try:
            await browser.cleanup()
        finally:
            self.session_semaphore.release()
