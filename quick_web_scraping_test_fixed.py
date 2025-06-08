#!/usr/bin/env python3
"""
Quick Web Scraping Test - Focus on eBay first, then add other sites
Tests the fixed real-time search endpoint with JSON body format
"""

import requests
import json
import time

def test_web_scraping_fixed():
    """Test web scraping with the fixed JSON body format"""
    base_url = "http://localhost:8000"
    
    # Test with just eBay first (known working scraper)
    test_cases = [
        {
            "name": "eBay Only Test",
            "data": {
                "query": "laptop",
                "sites": ["ebay"]
            }
        },
        {
            "name": "All Sites Test", 
            "data": {
                "query": "iPhone",
                "sites": ["amazon", "walmart", "ebay"]
            }
        }
    ]
    
    session = requests.Session()
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}")
        print(f"   Query: {test_case['data']['query']}")
        print(f"   Sites: {test_case['data']['sites']}")
        
        start_time = time.time()
        
        try:
            response = session.post(
                f"{base_url}/api/v1/real-time-search",
                json=test_case['data'],
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Response Time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                valid_results = data.get('valid_results', [])
                
                print(f"   ✅ Total Results: {len(results)}")
                print(f"   ✅ Valid Results: {len(valid_results)}")
                
                if valid_results:
                    sample = valid_results[0]
                    print(f"   📱 Sample: {sample.get('title', 'N/A')[:50]}...")
                    print(f"   💰 Price: {sample.get('price_text', 'N/A')}")
                    print(f"   🏪 Site: {sample.get('site', 'N/A')}")
                
                # Show price statistics if available
                price_stats = data.get('price_statistics', {})
                if price_stats:
                    print(f"   📊 Price Range: ${price_stats.get('min_price', 0):.2f} - ${price_stats.get('max_price', 0):.2f}")
                    print(f"   📊 Average: ${price_stats.get('avg_price', 0):.2f}")
            
            elif response.status_code == 422:
                print(f"   ❌ Validation Error (422): The endpoint correctly expects JSON body")
                print(f"   📝 Response: {response.text[:200]}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   📝 Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after 60 seconds")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    print("🔧 Testing Fixed Web Scraping with JSON Body Format")
    print("=" * 60)
    test_web_scraping_fixed()
