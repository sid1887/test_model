#!/usr/bin/env python3
"""
Scraper Debug Tool - Test web scraping functionality and diagnose issues
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

class ScraperDebugger:
    def __init__(self):
        self.scraper_url = "http://localhost:3001"
        self.fastapi_url = "http://localhost:8000"
        
    def test_scraper_health(self):
        """Test if scraper service is running"""
        try:
            response = requests.get(f"{self.scraper_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Scraper service is healthy")
                return True
            else:
                print(f"❌ Scraper service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to scraper service: {e}")
            return False
    
    def test_single_site_scraping(self, query="laptop", site="amazon"):
        """Test scraping a single site with detailed debugging"""
        print(f"\n🔍 Testing {site} scraper with query: '{query}'")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.scraper_url}/scrape-single",
                json={"query": query, "site": site},
                timeout=60
            )
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Results found: {len(data.get('results', []))}")
                
                if data.get('results'):
                    print("\n📋 Sample results:")
                    for i, result in enumerate(data['results'][:2]):
                        print(f"  {i+1}. {result.get('title', 'No title')[:50]}...")
                        print(f"     Price: {result.get('price', 'No price')}")
                        print(f"     Link: {result.get('link', 'No link')[:80]}...")
                else:
                    print("❌ No results found")
                    
                return data
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during scraping: {e}")
            return None
    
    def test_all_sites_scraping(self, query="laptop"):
        """Test scraping all sites"""
        print(f"\n🔍 Testing all sites with query: '{query}'")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.scraper_url}/scrape",
                json={"query": query, "sites": ["amazon", "walmart", "ebay"]},
                timeout=120
            )
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Total results found: {len(data.get('results', []))}")
                
                # Show results by site
                sites_results = {}
                for result in data.get('results', []):
                    site = result.get('site', 'unknown')
                    if site not in sites_results:
                        sites_results[site] = []
                    sites_results[site].append(result)
                
                for site, results in sites_results.items():
                    print(f"  {site.capitalize()}: {len(results)} results")
                
                if data.get('results'):
                    print("\n📋 Sample results:")
                    for i, result in enumerate(data['results'][:3]):
                        print(f"  {i+1}. [{result.get('site', 'unknown')}] {result.get('title', 'No title')[:50]}...")
                        print(f"     Price: {result.get('price', 'No price')}")
                
                return data
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception during scraping: {e}")
            return None
    
    def test_different_queries(self):
        """Test with different query types"""
        queries = [
            "laptop",
            "iphone",
            "nike shoes",
            "samsung tv",
            "wireless headphones"
        ]
        
        print("\n🧪 Testing different queries...")
        results = {}
        
        for query in queries:
            print(f"\n--- Testing query: '{query}' ---")
            result = self.test_single_site_scraping(query, "amazon")
            results[query] = result
            time.sleep(2)  # Avoid rate limiting
        
        return results
    
    def analyze_selector_issues(self):
        """Create a simple HTML test to verify selectors"""
        print("\n🔍 Analyzing potential selector issues...")
        
        # Test queries that should definitely return results
        test_queries = ["laptop", "book", "phone"]
        
        for query in test_queries:
            print(f"\nTesting with query: '{query}'")
            for site in ["amazon", "walmart", "ebay"]:
                result = self.test_single_site_scraping(query, site)
                if result and result.get('results'):
                    print(f"✅ {site} working: {len(result['results'])} results")
                else:
                    print(f"❌ {site} not working: 0 results")
                time.sleep(1)
    
    def generate_debug_report(self):
        """Generate comprehensive debug report"""
        print("=" * 60)
        print("🔧 SCRAPER DEBUG REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test service health
        health_ok = self.test_scraper_health()
        
        if not health_ok:
            print("\n❌ Cannot proceed - scraper service not available")
            return
        
        # Test single site scraping
        print("\n" + "=" * 40)
        print("SINGLE SITE TESTING")
        print("=" * 40)
        
        amazon_result = self.test_single_site_scraping("laptop", "amazon")
        walmart_result = self.test_single_site_scraping("laptop", "walmart")
        ebay_result = self.test_single_site_scraping("laptop", "ebay")
        
        # Test all sites together
        print("\n" + "=" * 40)
        print("ALL SITES TESTING")
        print("=" * 40)
        
        all_sites_result = self.test_all_sites_scraping("laptop")
        
        # Test different queries
        print("\n" + "=" * 40)
        print("DIFFERENT QUERIES TESTING")
        print("=" * 40)
        
        query_results = self.test_different_queries()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        working_sites = []
        failing_sites = []
        
        for site, result in [("amazon", amazon_result), ("walmart", walmart_result), ("ebay", ebay_result)]:
            if result and result.get('results'):
                working_sites.append(site)
            else:
                failing_sites.append(site)
        
        print(f"Working sites: {working_sites if working_sites else 'None'}")
        print(f"Failing sites: {failing_sites if failing_sites else 'None'}")
        
        working_queries = sum(1 for result in query_results.values() if result and result.get('results'))
        total_queries = len(query_results)
        
        print(f"Working queries: {working_queries}/{total_queries}")
        
        if not working_sites:
            print("\n🚨 DIAGNOSIS: All scrapers are failing")
            print("Possible causes:")
            print("  1. CSS selectors are outdated")
            print("  2. Anti-bot measures are blocking requests")
            print("  3. Website structure has changed")
            print("  4. Rate limiting is too aggressive")
            print("  5. Puppeteer configuration issues")
            
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("  1. Update CSS selectors for each site")
            print("  2. Test with headless=False to see actual browser behavior")
            print("  3. Add more sophisticated anti-bot evasion")
            print("  4. Implement rotating proxies")
            print("  5. Check if sites require authentication")
        
        print("\n" + "=" * 60)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            debugger = ScraperDebugger()
            debugger.test_scraper_health()
            debugger.test_single_site_scraping("laptop", "amazon")
        elif sys.argv[1] == "--analyze":
            debugger = ScraperDebugger()
            debugger.analyze_selector_issues()
        else:
            print("Usage: python scraper_debug.py [--quick|--analyze]")
    else:
        debugger = ScraperDebugger()
        debugger.generate_debug_report()

if __name__ == "__main__":
    main()
