import scrapy
import json
import logging
import os
import requests
from scrapy.http import Request
from datetime import datetime

logger = logging.getLogger(__name__)

class EcommerceSpider(scrapy.Spider):
    """Main e-commerce scraper spider supporting 15+ retailers"""

    name = 'ecommerce'
    allowed_domains = [
        'amazon.com', 'walmart.com', 'ebay.com', 'target.com',
        'bestbuy.com', 'newegg.com', 'flipkart.com', 'aliexpress.com',
        'costco.com', 'homedepot.com', 'lowes.com', 'macys.com',
        'overstock.com', 'wayfair.com', 'zappos.com', 'bhphotovideo.com',
        'nordstrom.com'
    ]
    
    # Service integration URLs
    captcha_service_url = os.getenv('CAPTCHA_SERVICE_URL', 'http://captcha-solver:9001')
    proxy_service_url = os.getenv('PROXY_SERVICE_URL', 'http://proxy-api:8001')
    haproxy_url = os.getenv('HAPROXY_URL', 'http://cumpair-proxy-manager:8080')

    # Site-specific selectors for 15+ retailers
    SELECTORS = {
        'amazon.com': {
            'products': '[data-component-type="s-search-result"], .s-result-item',
            'title': 'h2 span, a[data-component-type="s-pagination"] ~ * h2 span',
            'price': '.a-price-whole, .a-price .a-offscreen',
            'image': 'img.s-image',
            'link': 'h2 a, a[href*="/dp/"]'
        },
        'walmart.com': {
            'products': '[data-testid*="ProductCard"], li[role="listitem"]',
            'title': '[data-testid*="product-title"], a[href*="/product"]',
            'price': '[data-testid*="price"], [itemprop="price"]',
            'image': 'img',
            'link': 'a[href*="/product"]'
        },
        'ebay.com': {
            'products': '.s-item',
            'title': '.s-item__title',
            'price': '.s-item__price',
            'image': '.s-item__image img',
            'link': '.s-item__link'
        },
        'target.com': {
            'products': '[data-test*="ProductCard"], .ProductCard',
            'title': '[data-test*="product-title"], .ProductCard__title',
            'price': '[data-test*="current-price"], .Price',
            'image': 'img, [data-test*="product-image"]',
            'link': 'a[href*="/p/"]'
        },
        'bestbuy.com': {
            'products': '.sku-item, .product-item',
            'title': '.sku-title, .v-fw-regular',
            'price': '.priceView-customer-price span, .priceView-hero-price',
            'image': 'img.product-image, .primary-image',
            'link': '.sku-title a'
        },
        'newegg.com': {
            'products': '.item-cell, .item-container',
            'title': '.item-title, .item-brand',
            'price': '.price-current, .price-current-num',
            'image': '.item-img img, .product-image',
            'link': '.item-title'
        },
        'flipkart.com': {
            'products': 'div[class*="productGrid"] div[class*="product"]',
            'title': 'a[href*="/product"]',
            'price': 'div[class*="price"]',
            'image': 'img',
            'link': 'a[href*="/product"]'
        },
        'aliexpress.com': {
            'products': '.organic-list-offer',
            'title': '.organic-list-offer-title',
            'price': '.search-item-price',
            'image': 'img',
            'link': '.organic-list-offer-title'
        },
        'costco.com': {
            'products': '.product-tile, .product',
            'title': '.description, .product-title',
            'price': '.price, .product-price',
            'image': 'img.product-image, .product-img',
            'link': 'a'
        },
        'homedepot.com': {
            'products': '.plp-pod, .product-pod',
            'title': '.product-title, .pod-plp__title',
            'price': '.price, .price-format__main-price',
            'image': '.product-image, .product-pod__image img',
            'link': 'a'
        },
        'lowes.com': {
            'products': '.plp-tile, .product-tile',
            'title': '.product-title, .art-pd-title',
            'price': '.price, .price-current',
            'image': '.product-image img, .art-pd-image img',
            'link': 'a'
        },
        'macys.com': {
            'products': '.productThumbnail, .product-thumbnail',
            'title': '.product-title, .productDescription',
            'price': '.price, .product-price',
            'image': '.product-image img, .productThumbnailImage',
            'link': 'a'
        },
        'overstock.com': {
            'products': '.product-item, .product',
            'title': '.product-title, .product-name',
            'price': '.price, .product-price',
            'image': '.product-image img',
            'link': 'a'
        },
        'wayfair.com': {
            'products': '[data-testid="ProductCard"], .ProductCard',
            'title': '[data-testid="ProductName"], .ProductCard__name',
            'price': '[data-testid="PrimaryPrice"], .ProductCard__price',
            'image': '[data-testid="ProductCardImage"] img',
            'link': 'a'
        },
        'zappos.com': {
            'products': '[data-testid="product-grid-item"], .product',
            'title': '[data-testid="product-name"], .product-name',
            'price': '[data-testid="product-price"], .product-price',
            'image': '[data-testid="product-image"] img',
            'link': 'a'
        },
        'bhphotovideo.com': {
            'products': '[data-selenium="itemInner"], .js-item-container',
            'title': '[data-selenium="itemTitle"], .item-title',
            'price': '[data-selenium="itemPrice"], .price',
            'image': '[data-selenium="itemImage"] img',
            'link': 'a'
        },
        'nordstrom.com': {
            'products': '[data-testid="product-module"], .product-module',
            'title': '[data-testid="product-title"], .product-title',
            'price': '[data-testid="product-price"], .product-price',
            'image': '[data-testid="product-image"] img',
            'link': 'a'
        }
    }

    def start_requests(self):
        """Generate requests from incoming jobs"""
        # This will be called by the API
        pass
    
    def get_proxy(self):
        """Get proxy from proxy service via HAProxy"""
        try:
            # Try HAProxy first for load balancing
            response = requests.get(
                f'{self.haproxy_url}/api/v1/proxies/next',
                timeout=3
            )
            if response.status_code == 200:
                proxy_data = response.json()
                return proxy_data.get('proxy')
        except Exception as e:
            logger.warning(f'HAProxy unavailable, trying proxy service directly: {e}')
        
        try:
            # Fallback to direct proxy service
            response = requests.get(
                f'{self.proxy_service_url}/api/v1/proxies/next',
                timeout=3
            )
            if response.status_code == 200:
                proxy_data = response.json()
                return proxy_data.get('proxy')
        except Exception as e:
            logger.warning(f'Proxy service unavailable: {e}')
        
        return None
    
    def solve_captcha(self, image_url, captcha_type='image'):
        """Solve CAPTCHA using 2Captcha service"""
        try:
            response = requests.post(
                f'{self.captcha_service_url}/api/v1/solve',
                json={
                    'image_url': image_url,
                    'type': captcha_type
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info('CAPTCHA solved successfully')
                return result.get('solution')
            else:
                logger.error(f'CAPTCHA solving failed: {response.status_code}')
        except Exception as e:
            logger.error(f'Error solving CAPTCHA: {e}')
        
        return None

    def parse(self, response):
        """Parse product listings with CAPTCHA detection and proxy support"""
        
        # Check for CAPTCHA
        if self.is_captcha_page(response):
            logger.warning(f'CAPTCHA detected on {response.url}')
            # Try to solve CAPTCHA
            captcha_solution = self.solve_captcha(response.url)
            if captcha_solution:
                # Retry with CAPTCHA solution
                logger.info('Retrying with CAPTCHA solution')
                # In production, this would submit the CAPTCHA solution
                # For now, we'll just log and continue
            else:
                logger.error('Failed to solve CAPTCHA, skipping page')
                return

        # Get domain from URL
        domain = response.request.url.split('/')[2]
        base_domain = '.'.join(domain.split('.')[-2:])  # Get main domain

        selectors = self.SELECTORS.get(base_domain, self.SELECTORS.get('amazon.com'))
        query = response.meta.get('query', 'unknown')

        logger.info(f"Parsing {base_domain} for query: {query}")

        # Extract products
        product_count = 0
        for product in response.css(selectors['products']):
            try:
                title = product.css(selectors['title']).get()
                if title:
                    title = title.css('::text').get() or title.css('::attr(title)').get()
                    title = title.strip() if title else ''

                if not title or len(title) < 5:
                    continue

                price = product.css(selectors['price']).css('::text').get()
                image = product.css(selectors['image']).css('::attr(src), ::attr(data-src)').get()
                link = product.css(selectors['link']).css('::attr(href)').get()

                # Normalize link to absolute URL
                if link:
                    link = response.urljoin(link)

                product_data = {
                    'title': title,
                    'price': price or 'N/A',
                    'image': image or '',
                    'link': link or '',
                    'site': base_domain,
                    'query': query,
                    'timestamp': str(datetime.now().isoformat())
                }
                
                product_count += 1
                yield product_data

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue
        
        logger.info(f'Successfully extracted {product_count} products from {base_domain}')
    
    def is_captcha_page(self, response):
        """Detect if the page contains a CAPTCHA challenge"""
        captcha_indicators = [
            'captcha',
            'robot',
            'verify you are human',
            'security check',
            'unusual traffic',
            'Access Denied',
            'blocked'
        ]
        
        page_text = response.text.lower()
        return any(indicator in page_text for indicator in captcha_indicators)
