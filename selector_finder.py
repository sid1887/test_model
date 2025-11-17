#!/usr/bin/env python3
"""
Selector finder - automatically detects CSS selectors for product listings on e-commerce sites
"""
import requests
import json
from bs4 import BeautifulSoup
import time

RETAILERS = {
    'amazon': 'https://www.amazon.com/s?k=phone',
    'walmart': 'https://www.walmart.com/search?q=phone',
    'ebay': 'https://www.ebay.com/sch/i.html?_nkw=phone',
    'target': 'https://www.target.com/s?searchTerm=phone',
    'bestbuy': 'https://www.bestbuy.com/site/searchpage.jsp?st=phone',
    'newegg': 'https://www.newegg.com/p/pl?d=phone',
}

def test_selector_on_url(url, selector_list, timeout=45):
    """Test selectors on a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {}
        for selector in selector_list:
            try:
                elements = soup.select(selector)
                results[selector] = len(elements)
                if elements:
                    # Try to extract title/price from first element
                    first = elements[0]
                    text_preview = first.get_text(strip=True)[:100]
                    print(f"  ✓ '{selector}': Found {len(elements)} items. Preview: {text_preview}")
            except Exception as e:
                results[selector] = 0
                print(f"  ✗ '{selector}': Error - {e}")
        
        return results
    except Exception as e:
        print(f"  ERROR: {e}")
        return {}

def main():
    """Main function"""
    print("=" * 80)
    print("SELECTOR FINDER - E-Commerce Site Analysis")
    print("=" * 80)
    
    # Common selectors to test
    common_product_selectors = [
        # Generic
        '.product', '.item', '[class*="product"]', '[class*="item"]', '[data-product]',
        
        # Amazon
        '[data-component-type="s-search-result"]', '.s-result-item', '.s-asin',
        
        # Walmart
        '[data-item-id]', '.productCard', '.search-result-item', '.tile',
        
        # eBay
        '.s-item', '.s-result-item', '[class*="tile"]', '[data-ebayid]',
        
        # Target
        '[data-test*="productCard"]', '.Card', '[class*="ProductCard"]',
        
        # BestBuy
        '.sku-item', '.sku', '[class*="productContainer"]',
        
        # Newegg
        '.item-cell', '[class*="product-item"]'
    ]
    
    for retailer, url in RETAILERS.items():
        print(f"\n🔍 Testing {retailer.upper()}")
        print(f"   URL: {url}")
        print(f"   Testing selectors...")
        results = test_selector_on_url(url, common_product_selectors)
        
        # Find best selector
        best_selectors = [(s, c) for s, c in results.items() if c > 0]
        best_selectors.sort(key=lambda x: x[1], reverse=True)
        
        if best_selectors:
            print(f"\n   📊 SUMMARY for {retailer}:")
            for selector, count in best_selectors[:5]:
                print(f"      🥇 {selector}: {count} products")
        else:
            print(f"\n   ⚠️  No selectors found! May require JavaScript rendering")
        
        time.sleep(2)  # Be respectful
    
    print("\n" + "=" * 80)
    print("Analysis complete!")

if __name__ == '__main__':
    main()
