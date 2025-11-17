#!/usr/bin/env python3
"""
Continuous scraper trigger - keeps the scraper active
"""

import requests
import time
import json
from datetime import datetime

SCRAPER_URL = "http://localhost:3001/api/scrape"
DB_HOST = "localhost"

# List of Amazon product search URLs to scrape
SCRAPE_URLS = [
    "https://www.amazon.com/s?k=laptop",
    "https://www.amazon.com/s?k=smartphone",
    "https://www.amazon.com/s?k=tablet",
    "https://www.amazon.com/s?k=headphones",
    "https://www.amazon.com/s?k=smartwatch",
    "https://www.amazon.com/s?k=camera",
    "https://www.amazon.com/s?k=monitor",
    "https://www.amazon.com/s?k=keyboard",
]

def trigger_scrape(url):
    """Trigger a single scrape request"""
    try:
        payload = {"url": url}
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping: {url}")
        
        response = requests.post(SCRAPER_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success - Found {data.get('items_count', 0)} items")
            return True
        else:
            print(f"  ❌ Failed - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def check_db_status():
    """Check database stats"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="compair",
            user="compair",
            password="compair123"
        )
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM products")
        products = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM product_prices")
        prices = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM embeddings")
        embeddings = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n📊 DATABASE STATUS:")
        print(f"   Products: {products}")
        print(f"   Prices: {prices}")
        print(f"   Embeddings: {embeddings}\n")
        
    except Exception as e:
        print(f"DB check error: {e}\n")

def main():
    print("\n" + "="*80)
    print("CONTINUOUS SCRAPER ENGINE")
    print("="*80 + "\n")
    
    check_db_status()
    
    # Trigger scraping in batches
    for i in range(3):  # 3 rounds
        print(f"\n🔄 SCRAPING ROUND {i+1}/3\n")
        
        for url in SCRAPE_URLS:
            trigger_scrape(url)
            time.sleep(2)  # Delay between requests
        
        check_db_status()
        
        if i < 2:
            print("⏳ Waiting 30 seconds before next round...\n")
            time.sleep(30)
    
    print("\n" + "="*80)
    print("✅ SCRAPING SESSION COMPLETE")
    print("="*80 + "\n")
    
    check_db_status()

if __name__ == "__main__":
    main()
