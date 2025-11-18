#!/usr/bin/env python3
"""
Debug script to test CSS selectors on actual retailer pages
"""

import requests
from lxml import html as lxml_html

# Test URLs
TEST_URLS = {
    'amazon': 'https://www.amazon.com/s?k=phone',
    'walmart': 'https://www.walmart.com/search?q=phone',
    'ebay': 'https://www.ebay.com/sch/i.html?_nkw=phone',
    'target': 'https://www.target.com/s?searchTerm=phone',
    'bestbuy': 'https://www.bestbuy.com/site/searchpage.jsp?st=phone',
}

# Selectors to test
SELECTORS = {
    'amazon': {
        'products': '[data-component-type="s-search-result"], .s-result-item',
        'title': 'h2 a span::text, .a-size-mini::text',
    },
    'walmart': {
        'products': '[data-testid*="ProductCard"], li[data-item-id]',
        'title': '[data-testid*="product-title"]::text, span[role="heading"]::text',
    },
    'ebay': {
        'products': '.s-item, li.s-item',
        'title': '.s-item__title::text',
    },
    'target': {
        'products': '[data-test="@web/ProductCard"]',
        'title': '[data-test="product-title"]::text',
    },
    'bestbuy': {
        'products': '.sku-item, div[class*="productContainer"]',
        'title': 'h4.sku-title::text, div.sku-title::text',
    }
}

def test_selector(site, url):
    """Test selector on actual page"""
    print(f"\n{'='*60}")
    print(f"Testing {site.upper()} - {url}")
    print('='*60)

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return

        # Parse with lxml
        tree = lxml_html.fromstring(response.text)

        # Test product selector
        selector_config = SELECTORS.get(site, {})
        product_selector = selector_config.get('products', '')
        title_selector = selector_config.get('title', '')

        print(f"Testing product selector: {product_selector}")
        try:
            products = tree.cssselect(product_selector)
            print(f"✅ Found {len(products)} products")

            if products and title_selector:
                print(f"Testing title selector on first product: {title_selector}")
                first_product = products[0]
                titles = first_product.cssselect(title_selector)
                print(f"✅ Found {len(titles)} titles")
                if titles:
                    print(f"   Sample: {titles[0].text_content()[:100]}")
        except Exception as e:
            print(f"❌ Error with selector: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

# Test all sites
for site, url in TEST_URLS.items():
    test_selector(site, url)

print(f"\n{'='*60}")
print("DEBUG COMPLETE")
print('='*60)
