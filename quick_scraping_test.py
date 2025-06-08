import requests

def test_web_scraping():
    """Quick test for web scraping endpoint"""
    print("Testing web scraping endpoint...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/real-time-search",
            params={"query": "laptop", "sites": ["amazon"]},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_web_scraping()
