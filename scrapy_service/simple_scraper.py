#!/usr/bin/env python3
"""
Simple Scrapy-based multi-retailer scraper
Designed for speed and simplicity
"""

import json
import sys
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request, signals
import time

logging.basicConfig(level=logging.WARNING)

# Global to collect results
COLLECTED_PRODUCTS = []

class FastEcommerceScraper(Spider):
    """Fast e-commerce spider using Scrapy's built-in concurrency"""

    name = 'fast_scraper'
    allowed_domains = [
        'amazon.com', 'walmart.com', 'ebay.com', 'target.com',
        'bestbuy.com', 'newegg.com'
    ]

    # Selectors per site
    SELECTORS = {
        'amazon.com': {
            'products': '[data-component-type="s-search-result"], .s-result-item',
            'title': 'h2 a span::text, .a-size-mini::text',
            'price': '.a-price-whole::text',
            'image': 'img.s-image::attr(src)',
            'link': 'h2 a::attr(href)'
        },
        'walmart.com': {
            'products': 'li[role="listitem"], [data-testid*="ProductCard"]',
            'title': 'span::text, a::text, h2::text',
            'price': 'span::text',
            'image': 'img::attr(src)',
            'link': 'a::attr(href)'
        },
        'ebay.com': {
            'products': '.s-item',
            'title': '.s-item__title::text',
            'price': '.s-item__price::text',
            'image': '.s-item__image img::attr(src)',
            'link': '.s-item__link::attr(href)'
        },
        'target.com': {
            'products': '[data-test*="ProductCard"], li',
            'title': 'a::text, h2::text, span::text',
            'price': 'span::text',
            'image': 'img::attr(src)',
            'link': 'a::attr(href)'
        },
        'bestbuy.com': {
            'products': '.sku-item, li',
            'title': 'h4::text, a::text, span::text',
            'price': 'span::text',
            'image': 'img::attr(src)',
            'link': 'a::attr(href)'
        },
        'newegg.com': {
            'products': '.item-cell, li',
            'title': '.item-title::text, a::text',
            'price': '.price-current::text, span::text',
            'image': 'img::attr(src)',
            'link': 'a::attr(href)'
        }
    }

    def __init__(self, query='', sites=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.sites = sites or ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg']
        self.products = []
        self.start_time = time.time()

    def start_requests(self):
        """Generate requests for all sites"""
        urls = {
            'amazon': f'https://www.amazon.com/s?k={self.query}',
            'walmart': f'https://www.walmart.com/search?q={self.query}',
            'ebay': f'https://www.ebay.com/sch/i.html?_nkw={self.query}',
            'target': f'https://www.target.com/s?searchTerm={self.query}',
            'bestbuy': f'https://www.bestbuy.com/site/searchpage.jsp?st={self.query}',
            'newegg': f'https://www.newegg.com/p/pl?d={self.query}',
        }

        for site in self.sites:
            if site in urls:
                yield Request(
                    urls[site],
                    callback=self.parse,
                    meta={'site': site, 'query': self.query, 'dont_obey_robotstxt': True},
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

    def parse(self, response):
        """Override in subclass"""
        raise NotImplementedError("Subclass must implement parse method")


def scrape_products(query, sites=None):
    """Simple function to scrape products"""
    global COLLECTED_PRODUCTS
    COLLECTED_PRODUCTS = []  # Reset before starting

    if not sites:
        sites = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg']

    # Create a custom spider that collects to global
    class ProductCollectorSpider(FastEcommerceScraper):
        def parse(self, response):
            """Parse product listings"""
            site = response.meta['site']
            domain = '.'.join(response.url.split('/')[2].split('.')[-2:])
            sel = self.SELECTORS.get(domain, self.SELECTORS.get('amazon.com', {}))

            for product_elem in response.css(sel.get('products', 'div')):
                try:
                    title = product_elem.css(sel.get('title', 'span::text')).get('')
                    if isinstance(title, list):
                        title = ' '.join(title)
                    title = (title or '').strip()

                    if not title or len(title) < 5:
                        continue

                    price = product_elem.css(sel.get('price', 'span::text')).get('N/A')
                    image = product_elem.css(sel.get('image', 'img::attr(src)')).get('')
                    link = product_elem.css(sel.get('link', 'a::attr(href)')).get('')

                    if link:
                        link = response.urljoin(link)

                    product = {
                        'title': title[:150],
                        'price': price,
                        'image': image,
                        'link': link,
                        'site': site,
                        'timestamp': datetime.now().isoformat()
                    }

                    COLLECTED_PRODUCTS.append(product)
                    yield product

                except Exception as e:
                    self.logger.debug(f"Error parsing product: {e}")
                    continue

    # Configure Scrapy for speed
    settings = {
        'CONCURRENT_REQUESTS': 6,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_TIMEOUT': 15,
        'RETRY_TIMES': 1,
        'COOKIES_ENABLED': False,
        'LOG_LEVEL': 'WARNING',
        'USER_AGENT': 'Mozilla/5.0',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,
        }
    }

    process = CrawlerProcess(settings)
    process.crawl(ProductCollectorSpider, query=query, sites=sites)
    process.start()

    return {
        'query': query,
        'total_products': len(COLLECTED_PRODUCTS),
        'sites_searched': len(sites),
        'successful_sites': len(set(p['site'] for p in COLLECTED_PRODUCTS)) if COLLECTED_PRODUCTS else 0,
        'products': COLLECTED_PRODUCTS,
        'timestamp': datetime.now().isoformat()
    }
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python simple_scraper.py <query> [site1,site2,...]")
        sys.exit(1)

    query = sys.argv[1]
    sites = sys.argv[2].split(',') if len(sys.argv) > 2 else None

    results = scrape_products(query, sites)
    print(json.dumps(results, indent=2))
