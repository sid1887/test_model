#!/usr/bin/env python3
"""
Debug API responses
"""
import requests
import json

def debug_text_search():
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/search-by-text",
            json={"query": "wall clock", "limit": 5},
            timeout=10
        )
        print(f"Text Search Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Text search error: {e}")
        return False

def debug_image_search():
    try:
        from pathlib import Path
        test_images = list(Path("product_images_test").glob("*.jpg"))
        
        if not test_images:
            print("No test images found")
            return False
        
        with open(test_images[0], 'rb') as f:
            response = requests.post(
                "http://localhost:8000/api/v1/search-by-image",
                files={'file': (test_images[0].name, f, 'image/jpeg')},
                data={'top_k': 5},
                timeout=15
            )
        
        print(f"Image Search Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Image search error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging API responses...")
    print("\n📝 Text Search:")
    debug_text_search()
    print("\n🖼️ Image Search:")
    debug_image_search()
