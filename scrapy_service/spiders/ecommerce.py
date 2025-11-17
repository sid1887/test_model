import scrapy
import json
import logging
from scrapy.http import Request

logger = logging.getLogger(__name__)

class EcommerceSpider(scrapy.Spider):
    """Main e-commerce scraper spider"""

    name = 'ecommerce'
    allowed_domains = [
        'amazon.com', 'walmart.com', 'ebay.com', 'target.com',
        'bestbuy.com', 'newegg.com', 'flipkart.com', 'aliexpress.com'
    ]

    # Site-specific selectors
    SELECTORS = {
        'amazon.com': {
            'products': '[data-component-type="s-search-result"], .s-result-item',
            'title': 'h2 span, a[data-component-type="s-pagination"] ~ * h2 span',
            'price': '.a-price-whole',
            'image': 'img.s-image',
            'link': 'h2 a, a[href*="/dp/"]'
        },
        'walmart.com': {
            'products': '[data-testid*="ProductCard"], li[role="listitem"]',
            'title': '[data-testid*="product-title"], a[href*="/product"]',
            'price': '[data-testid*="price"]',
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
            'products': '[data-test*="ProductCard"]',
            'title': 'a[data-test*="product-title"]',
            'price': '[data-test*="current-price"]',
            'image': 'img',
            'link': 'a[href*="/p/"]'
        },
        'bestbuy.com': {
            'products': '.sku-item',
            'title': '.sku-title a',
            'price': '.priceView-customer-price span',
            'image': 'img.product-image',
            'link': '.sku-title a'
        },
        'newegg.com': {
            'products': '.item-cell',
            'title': '.item-title',
            'price': '.price-current',
            'image': '.item-img img',
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
        }
    }

    def start_requests(self):
        """Generate requests from incoming jobs"""
        # This will be called by the API
        pass

    def parse(self, response):
        """Parse product listings"""

        # Get domain from URL
        domain = response.request.url.split('/')[2]
        base_domain = '.'.join(domain.split('.')[-2:])  # Get main domain

        selectors = self.SELECTORS.get(base_domain, self.SELECTORS.get('amazon.com'))
        query = response.meta.get('query', 'unknown')

        logger.info(f"Parsing {base_domain} for query: {query}")

        # Extract products
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

                yield {
                    'title': title,
                    'price': price or 'N/A',
                    'image': image or '',
                    'link': link or '',
                    'site': base_domain,
                    'query': query,
                    'timestamp': str(__import__('datetime').datetime.now().isoformat())
                }

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue
