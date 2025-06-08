#!/usr/bin/env python3
"""
Final Validation Test for Cumpair System
"""
import requests
import json
import time
from pathlib import Path

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_text_search():
    """Test text search functionality"""
    try:        response = requests.post(
            "http://localhost:8000/api/v1/search-by-text",
            json={"query": "wall clock", "top_k": 5},
            timeout=30
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            # Check for duplicates
            product_ids = [r.get("product_id") for r in results if r.get("product_id")]
            unique_ids = set(product_ids)
            has_duplicates = len(product_ids) != len(unique_ids)
            return not has_duplicates, len(results), len(product_ids) - len(unique_ids) if has_duplicates else 0
        return False, 0, 0
    except Exception as e:
        print(f"Text search error: {e}")
        return False, 0, 0

def test_image_search():
    """Test image search functionality"""
    try:
        from pathlib import Path
        test_images = list(Path("product_images_test").glob("*.jpg"))
        if not test_images:
            return False, 0, 0
        
        with open(test_images[0], 'rb') as f:            response = requests.post(
                "http://localhost:8000/api/v1/search-by-image",
                files={'file': (test_images[0].name, f, 'image/jpeg')},
                data={'top_k': 5},
                timeout=30
            )
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            # Check for duplicates
            product_ids = [r.get("product_id") for r in results if r.get("product_id")]
            unique_ids = set(product_ids)
            has_duplicates = len(product_ids) != len(unique_ids)
            return not has_duplicates, len(results), len(product_ids) - len(unique_ids) if has_duplicates else 0
        return False, 0, 0
    except Exception as e:
        print(f"Image search error: {e}")
        return False, 0, 0

def main():
    """Run validation tests"""
    print("🚀 Final Validation Test for Cumpair System")
    print("=" * 50)
    
    # Test server health
    print("🏥 Testing server health...")
    if not test_server_health():
        print("❌ Server is not running!")
        return
    print("✅ Server is healthy")
    
    # Test text search
    print("\n📝 Testing text search...")
    text_passed, text_count, text_dupes = test_text_search()
    if text_passed:
        print(f"✅ Text search passed - {text_count} results, no duplicates")
    else:
        print(f"❌ Text search failed - {text_dupes} duplicates found")
    
    # Test image search
    print("\n🖼️ Testing image search...")
    image_passed, image_count, image_dupes = test_image_search()
    if image_passed:
        print(f"✅ Image search passed - {image_count} results, no duplicates")
    else:
        print(f"❌ Image search failed - {image_dupes} duplicates found")
    
    # Summary
    total_tests = 3
    passed_tests = sum([True, text_passed, image_passed])
    
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️ Some tests failed. Issues need to be addressed.")

if __name__ == "__main__":
    main()
