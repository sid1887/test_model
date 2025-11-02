"""
🧪 Test Image-to-Scraper Integration
Tests the complete multi-modal product search flow
"""

import asyncio
import httpx
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"


async def test_image_search():
    """Test image upload → AI detection → scraper search"""
    print("\n" + "="*80)
    print("🧪 TEST: Image Search (Image → AI → Scraper → Prices)")
    print("="*80)
    
    # Create a test image file (or use existing)
    test_image_path = "test_product_image.jpg"
    
    if not os.path.exists(test_image_path):
        print("⚠️ No test image found. Please provide a product image as 'test_product_image.jpg'")
        print("   Example: Take a photo of any product (cereal box, phone, book, etc.)")
        return
    
    print(f"📷 Using test image: {test_image_path}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Upload image and trigger search
            with open(test_image_path, 'rb') as f:
                files = {'file': (test_image_path, f, 'image/jpeg')}
                
                response = await client.post(
                    f"{BASE_URL}/api/v1/comparison/search-by-image",
                    files=files,
                    params={
                        'sites': ['amazon', 'walmart', 'ebay'],
                        'max_results': 10
                    }
                )
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ Search Status: {data.get('status')}")
                print(f"🔍 Detected Query: {data.get('detected_query')}")
                print(f"🎯 Detection Method: {data.get('detection_method')}")
                print(f"📈 Confidence: {data.get('detection_confidence', 0):.2%}")
                
                results = data.get('results', [])
                print(f"\n🛒 Found {len(results)} products:")
                
                for i, product in enumerate(results[:5], 1):  # Show first 5
                    print(f"\n  {i}. {product.get('title', 'N/A')[:80]}")
                    print(f"     💵 Price: {product.get('price', 'N/A')}")
                    print(f"     🏪 Retailer: {product.get('retailer', 'N/A')}")
                    print(f"     🔗 Link: {product.get('link', 'N/A')[:80]}")
                
                print("\n✅ IMAGE SEARCH TEST PASSED!")
                return True
            else:
                print(f"❌ Request failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_barcode_search():
    """Test barcode search directly"""
    print("\n" + "="*80)
    print("🧪 TEST: Barcode Search")
    print("="*80)
    
    # Use a real UPC code (e.g., Coca-Cola)
    test_barcode = "049000050103"  # Coca-Cola 12oz can
    
    print(f"🏷️ Testing barcode: {test_barcode}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/comparison/search-by-barcode",
                params={
                    'barcode': test_barcode,
                    'barcode_type': 'UPC',
                    'sites': ['amazon', 'walmart'],
                    'max_results': 10
                }
            )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Search Status: {data.get('status')}")
            print(f"🏷️ Barcode: {data.get('barcode')}")
            
            results = data.get('results', [])
            print(f"\n🛒 Found {len(results)} products:")
            
            for i, product in enumerate(results[:5], 1):
                print(f"\n  {i}. {product.get('title', 'N/A')[:80]}")
                print(f"     💵 Price: {product.get('price', 'N/A')}")
                print(f"     🏪 Retailer: {product.get('retailer', 'N/A')}")
            
            print("\n✅ BARCODE SEARCH TEST PASSED!")
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_existing_smart_search():
    """Test existing smart search endpoint"""
    print("\n" + "="*80)
    print("🧪 TEST: Existing Smart Search")
    print("="*80)
    
    query = "iPhone 15 Pro Max"
    print(f"🔍 Testing query: {query}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/comparison/smart-search",
                params={
                    'query': query,
                    'sites': ['amazon', 'walmart', 'ebay'],
                    'max_results': 10
                }
            )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"\n🛒 Found {len(results)} products:")
            
            for i, product in enumerate(results[:3], 1):
                print(f"\n  {i}. {product.get('title', 'N/A')[:80]}")
                print(f"     💵 Price: {product.get('price', 'N/A')}")
                print(f"     🏪 Retailer: {product.get('retailer', 'N/A')}")
            
            print("\n✅ SMART SEARCH TEST PASSED!")
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n🔥 MULTI-MODAL PRODUCT SEARCH - INTEGRATION TESTS")
    print("="*80)
    
    results = []
    
    # Test 1: Existing smart search
    results.append(await test_existing_smart_search())
    
    # Test 2: Barcode search
    results.append(await test_barcode_search())
    
    # Test 3: Image search (requires test image)
    results.append(await test_image_search())
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Multi-modal search is operational!")
    else:
        print("\n⚠️ Some tests failed. Check logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
