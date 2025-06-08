#!/usr/bin/env python3
"""
Quick web scraping test to diagnose the connection issues
"""

import requests
import json
import time

def test_real_time_search():
    """Test the real-time search endpoint directly"""
    print("🔍 Testing Real-Time Search Endpoint...")
    
    url = 'http://localhost:8000/api/v1/real-time-search'
    data = {
        'query': 'laptop',
        'sites': ['amazon', 'walmart']
    }
    
    try:
        print(f"📡 Sending request to: {url}")
        print(f"📝 Request data: {data}")
        
        start_time = time.time()
        # Use query parameters instead of JSON body for real-time search
        response = requests.post(url, params=data, timeout=60)
        response_time = time.time() - start_time
        
        print(f"⏱️ Response time: {response_time:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Found {len(result.get('results', []))} results")
            
            if result.get('results'):
                print("\n📦 Sample results:")
                for i, item in enumerate(result['results'][:3]):
                    print(f"  {i+1}. {item.get('title', 'N/A')[:60]}...")
                    print(f"     Price: {item.get('price', 'N/A')} | Source: {item.get('source', 'N/A')}")
            else:
                print("⚠️ No results found in response")
                print(f"Response keys: {list(result.keys())}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_scraper_service():
    """Test the Node.js scraper service directly"""
    print("\n🕷️ Testing Scraper Service Health...")
    
    try:
        response = requests.get('http://localhost:3001/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraper service healthy: {data}")
        else:
            print(f"❌ Scraper service error: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach scraper service: {e}")

def test_fastapi_service():
    """Test FastAPI service availability"""
    print("\n🚀 Testing FastAPI Service...")
    
    try:
        response = requests.get('http://localhost:8000/docs', timeout=10)
        if response.status_code == 200:
            print("✅ FastAPI service is running")
        else:
            print(f"❌ FastAPI service error: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach FastAPI service: {e}")

if __name__ == "__main__":
    print("🧪 Quick Web Scraping Diagnostic Test")
    print("=" * 50)
    
    test_fastapi_service()
    test_scraper_service()
    test_real_time_search()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
