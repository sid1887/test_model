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
        'amazon.com', 'walmart.com', 'ebay.com', 'target.com', 'bestbuy.com',
        'newegg.com', 'costco.com', 'homedepot.com', 'lowes.com', 'macys.com',
        'overstock.com', 'wayfair.com', 'zappos.com', 'bhphotovideo.com',
        'nordstrom.com', 'flipkart.com', 'aliexpress.com'
    ]

    # Selectors per site - CSS selectors for each retailer
    SELECTORS = {
        'amazon.com': {
            'products': '[data-component-type="s-search-result"], .s-result-item, div[data-index]',
            'title': 'h2 a span::text, .a-size-mini::text, span.a-size-base-plus',
            'price': '.a-price-whole::text, span.a-price-whole, .a-price-split',
            'image': 'img.s-image::attr(src), img::attr(src)',
            'link': 'h2 a::attr(href), a.a-link-normal::attr(href)'
        },
        'walmart.com': {
            'products': '[data-testid*="ProductCard"], div[data-item-id], li.productWrapper',
            'title': '[data-testid*="product-title"]::text, span.product-title, h2::text, a.product-link::text',
            'price': '[data-testid*="ProductPrice"]::text, div.product-price, span.price',
            'image': 'img[data-testid*="ProductImage"]::attr(src), img.product-image::attr(src)',
            'link': 'a[data-testid*="ProductLink"]::attr(href), a.product-link::attr(href)'
        },
        'ebay.com': {
            'products': '.s-item, li.s-item, div.s-item-container, .sgLnk.s-item',
            'title': '.s-item__title::text, h3.s-item__title::text, a.s-item__link::text, .LIGHT_ON::text',
            'price': '.s-item__price::text, span.BOLD::text, div.s-item__price::text, .s-price',
            'image': '.s-item__image img::attr(src), img.s-item-image::attr(src), img::attr(src)',
            'link': '.s-item__link::attr(href), a.s-item-link::attr(href), a.s-item__link::attr(href)'
        },
        'target.com': {
            'products': 'div[class*="ProductCard"], div[class*="Card"], article, div.product-item',
            'title': 'span[class*="product-name"]::text, a[class*="ProductTitle"]::text, span.product-title::text, h2::text, a::text',
            'price': 'span[class*="Price"]::text, span.current-price::text, div.price::text, span.h-text-bold::text, strong::text',
            'image': 'img[class*="ProductImage"]::attr(src), img[class*="image"]::attr(src), img::attr(src)',
            'link': 'a[href*="/p/"]::attr(href), a[class*="ProductCard"]::attr(href), a::attr(href)'
        },
        'bestbuy.com': {
            'products': 'div[class*="sku-item"], li[class*="sku"], article.sku-container, div.product-item',
            'title': 'h4.sku-title::text, span[class*="sku-title"]::text, a[class*="title"]::text, h2::text, a::text',
            'price': 'div.priceView::text, span.priceView::text, span.wasPrice::text, div.currentPrice::text, strong::text',
            'image': 'img[class*="productImage"]::attr(src), img[class*="image"]::attr(src), img::attr(src)',
            'link': 'a.sku-title::attr(href), a[href*="/product/"]::attr(href), a::attr(href)'
        },
        'newegg.com': {
            'products': 'div[class*="item-cell"], li[class*="item"], div.product-item, article',
            'title': 'a.item-title::text, span.item-title::text, a[class*="title"]::text, h2::text, a::text',
            'price': 'strong[class*="price"]::text, div.price-current::text, span[class*="price"]::text, strong::text, div.price::text',
            'image': 'img[data-src]::attr(data-src), img.product-img::attr(src), img[class*="image"]::attr(src), img::attr(src)',
            'link': 'a.item-title::attr(href), a[href*="/p/"]::attr(href), a::attr(href)'
        },
        'costco.com': {
            'products': 'div[data-item-id], div.product-item, li.product-tile',
            'title': 'h3::text, a.product-link::text, span.product-name',
            'price': 'div.product-price::text, span.price, div.price',
            'image': 'img.product-image::attr(src), img.lazy::attr(data-src)',
            'link': 'a.product-link::attr(href), a.product-title::attr(href)'
        },
        'homedepot.com': {
            'products': 'div[data-testid*="product"], li.product-item, article.product',
            'title': 'span.product-name::text, a.product-link::text, h2::text',
            'price': 'span.product-price::text, div.price::text, span.price',
            'image': 'img.product-image::attr(src), img::attr(src)',
            'link': 'a.product-link::attr(href), a[href*="/p/"]::attr(href)'
        },
        'lowes.com': {
            'products': '[data-product-id], li.product, div.product-item',
            'title': 'a.product-link::text, h2::text, span.product-title',
            'price': 'span.product-price::text, div.price::text, span.price',
            'image': 'img.product-image::attr(src), img::attr(src)',
            'link': 'a.product-link::attr(href), a[href*="/p/"]::attr(href)'
        },
        'macys.com': {
            'products': 'div[data-el="productTile"], li.productTile, div.product',
            'title': 'a.productDescLink::text, h2::text, span.product-title',
            'price': 'div.productPrice::text, span.price::text, div.price',
            'image': 'img.productImage::attr(src), img::attr(src)',
            'link': 'a.productDescLink::attr(href), a.product-link::attr(href)'
        },
        'overstock.com': {
            'products': 'div.prodSlot, li.productWrapper, div.product-item',
            'title': 'a.prodLink::text, h2::text, span.product-title',
            'price': 'span.prodPrice::text, div.price::text, span.price',
            'image': 'img.productImage::attr(src), img.lazy::attr(data-src)',
            'link': 'a.prodLink::attr(href), a.product-link::attr(href)'
        },
        'wayfair.com': {
            'products': 'div[data-testid*="ProductCard"], li.product, div.product-item',
            'title': 'span.product-title::text, h2::text, a::text',
            'price': 'span.ProductPrice::text, div.price::text, span.price',
            'image': 'img[data-testid*="ProductImage"]::attr(src), img::attr(src)',
            'link': 'a[data-testid*="ProductLink"]::attr(href), a.product-link::attr(href)'
        },
        'zappos.com': {
            'products': 'div.productResult, li.product, div.product-item',
            'title': 'h2.productName::text, a::text, span.product-title',
            'price': 'span.price::text, div.productPrice::text, span.productPrice',
            'image': 'img.productImage::attr(src), img::attr(src)',
            'link': 'a.productName::attr(href), a.product-link::attr(href)'
        },
        'bhphotovideo.com': {
            'products': 'div[data-product-id], li.product, div.product-item',
            'title': 'a.productTitle::text, h2::text, span.product-title',
            'price': 'span.productPrice::text, div.price::text, span.price',
            'image': 'img.productImage::attr(src), img::attr(src)',
            'link': 'a.productTitle::attr(href), a.product-link::attr(href)'
        },
        'nordstrom.com': {
            'products': 'div[data-test-id*="product"], li.product, div.product-item',
            'title': 'a.productName::text, h2::text, span.product-title',
            'price': 'span.productPrice::text, div.price::text, span.price',
            'image': 'img.productImage::attr(src), img::attr(src)',
            'link': 'a.productName::attr(href), a.product-link::attr(href)'
        },
        'flipkart.com': {
            'products': 'div._1AtVbE, li._15LC29, div.productCardImg',
            'title': 'a._1fGeY5::text, div.fHxwqd::text, h2::text',
            'price': 'div._30jeq3::text, span.hl05D5::text, span.price',
            'image': 'img._396cs4::attr(src), img::attr(src)',
            'link': 'a._1fGeY5::attr(href), a.productLink::attr(href)'
        },
        'aliexpress.com': {
            'products': 'div.organic, li.organic, div.search-card-e',
            'title': 'a._1mscb::text, h3::text, span.product-title',
            'price': 'span.search-card-e-price-main::text, div.price::text, span.price',
            'image': 'img._4uPu34::attr(src), img::attr(src)',
            'link': 'a._1mscb::attr(href), a.product-link::attr(href)'
        }
    }

    def __init__(self, query='', sites=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.sites = sites or ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg',
                               'costco', 'homedepot', 'lowes', 'flipkart']  # Top 10
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
            'costco': f'https://www.costco.com/CatalogSearch?keyword={self.query}',
            'homedepot': f'https://www.homedepot.com/s/{self.query}',
            'lowes': f'https://www.lowes.com/search?searchTerm={self.query}',
            'macys': f'https://www.macys.com/shop/search?keyword={self.query}',
            'overstock': f'https://www.overstock.com/search?keywords={self.query}',
            'wayfair': f'https://www.wayfair.com/keyword.php?keyword={self.query}',
            'zappos': f'https://www.zappos.com/search?term={self.query}',
            'bhphotovideo': f'https://www.bhphotovideo.com/c/search?Ntt={self.query}',
            'nordstrom': f'https://www.nordstrom.com/sr?keyword={self.query}',
            'flipkart': f'https://www.flipkart.com/search?q={self.query}',
            'aliexpress': f'https://www.aliexpress.com/wholesale?SearchText={self.query}',
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


# Generic fallback selectors for retailers
GENERIC_FALLBACK = {
    'products': 'div[class*="product"], li[class*="product"], article, div.item, li.item',
    'title': 'h2, h3, h4, a[href*="/p/"], a[href*="/product"], span[role="heading"]',
    'price': 'span[class*="price"], div[class*="price"], span[data-price], span.amount',
    'image': 'img[alt], img[src*="product"], img[loading="lazy"]',
    'link': 'a[href*="/p/"], a[href*="/product"], a[data-productid], a[data-product]'
}


def scrape_products(query, sites=None):
    """Simple function to scrape products"""
    global COLLECTED_PRODUCTS
    COLLECTED_PRODUCTS = []  # Reset before starting

    if not sites:
        sites = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg']

    # Create a custom spider that collects to global
    class ProductCollectorSpider(FastEcommerceScraper):
        def parse(self, response):
            """Parse product listings with smart fallback"""
            site = response.meta['site']
            domain = '.'.join(response.url.split('/')[2].split('.')[-2:])
            sel = self.SELECTORS.get(domain, self.SELECTORS.get('amazon.com', {}))

            # Try specific selectors first, fall back to generic
            product_selector = sel.get('products', GENERIC_FALLBACK['products'])
            products = response.css(product_selector)

            # If no products found with specific selector, try generic
            if not products:
                products = response.css(GENERIC_FALLBACK['products'])

            self.logger.info(f"Found {len(products)} product containers for {site}")

            for product_elem in products:
                try:
                    # Try to extract title
                    title_sel = sel.get('title', GENERIC_FALLBACK['title'])
                    title_parts = product_elem.css(title_sel).getall()

                    if not title_parts:
                        # Fallback: try to get any text
                        title_parts = product_elem.css('::text').getall()

                    title = ' '.join([t.strip() for t in title_parts if t.strip()])[:150]

                    if not title or len(title) < 3:
                        continue

                    # Extract price (try multiple patterns)
                    price_sel = sel.get('price', GENERIC_FALLBACK['price'])
                    price = product_elem.css(price_sel).get('N/A')

                    # Extract image
                    image_sel = sel.get('image', GENERIC_FALLBACK['image'])
                    image = product_elem.css(image_sel).get('')

                    # Extract link
                    link_sel = sel.get('link', GENERIC_FALLBACK['link'])
                    link = product_elem.css(link_sel).get('')

                    if link:
                        link = response.urljoin(link)

                    # Only add if we have title
                    if title:
                        product = {
                            'title': title,
                            'price': str(price)[:50] if price else 'N/A',
                            'image': str(image)[:300] if image else '',
                            'link': link[:500] if link else '',
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
