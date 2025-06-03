"""
Compair System Test Suite
Tests all major components and endpoints
"""

import asyncio
import aiohttp
import json
import os
import tempfile
from PIL import Image
import numpy as np
import sys
from typing import Dict, Any

class CompairTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.scraper_url = "http://localhost:3001"
        self.test_results = []
        
    async def test_health_endpoint(self):
        """Test the health check endpoint"""
        print("🏥 Testing health endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health check passed: {data}")
                        return True
                    else:
                        print(f"❌ Health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_scraper_service(self):
        """Test the Node.js scraper service"""
        print("🕷️ Testing scraper service...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.scraper_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Scraper health check passed: {data}")
                        return True
                    else:
                        print(f"❌ Scraper health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Scraper service error: {e}")
            return False
    
    async def test_real_time_search(self):
        """Test real-time price search"""
        print("🔍 Testing real-time search...")
        try:
            test_data = {
                "query": "iPhone 15",
                "sites": ["amazon", "walmart", "ebay"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/real-time-search",
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results_count = len(data.get('results', []))
                        print(f"✅ Real-time search passed: Found {results_count} results")
                        
                        # Show sample result
                        if data.get('valid_results'):
                            sample = data['valid_results'][0]
                            print(f"   Sample: {sample.get('title', 'N/A')[:50]}... - {sample.get('price_text', 'N/A')}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Real-time search failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Real-time search error: {e}")
            return False
    
    def create_test_image(self) -> str:
        """Create a test image for image search testing"""
        # Create a simple test image
        img = Image.new('RGB', (300, 300), color='red')
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG')
        return temp_file.name
    
    async def test_image_search(self):
        """Test CLIP-based image search"""
        print("🖼️ Testing image search...")
        
        # Create test image
        test_image_path = self.create_test_image()
        
        try:
            data = aiohttp.FormData()
            data.add_field('file', 
                          open(test_image_path, 'rb'),
                          filename='test.jpg',
                          content_type='image/jpeg')
            data.add_field('top_k', '5')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/search-by-image",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results_count = len(data.get('results', []))
                        print(f"✅ Image search passed: Found {results_count} similar products")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Image search failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Image search error: {e}")
            return False
        finally:
            # Clean up test image
            try:
                os.unlink(test_image_path)
            except:
                pass
    
    async def test_direct_scraper(self):
        """Test scraper service directly"""
        print("🕸️ Testing direct scraper functionality...")
        try:
            test_data = {
                "query": "laptop",
                "sites": ["amazon", "walmart"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.scraper_url}/scrape",
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results_count = len(data.get('results', []))
                        print(f"✅ Direct scraper test passed: Found {results_count} products")
                        
                        # Show sample
                        if data.get('results'):
                            sample = data['results'][0]
                            print(f"   Sample: {sample.get('title', 'N/A')[:50]}... from {sample.get('site', 'N/A')}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Direct scraper test failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Direct scraper error: {e}")
            return False
    
    async def test_api_documentation(self):
        """Test API documentation availability"""
        print("📚 Testing API documentation...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/docs") as response:
                    if response.status == 200:
                        print("✅ API documentation is accessible")
                        return True
                    else:
                        print(f"❌ API documentation failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API documentation error: {e}")
            return False
    
    async def test_frontend(self):
        """Test frontend availability"""
        print("🌐 Testing frontend...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        content = await response.text()
                        if "Compair" in content:
                            print("✅ Frontend is accessible")
                            return True
                        else:
                            print("❌ Frontend loaded but content seems wrong")
                            return False
                    else:
                        print(f"❌ Frontend failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Frontend error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Running Compair System Tests")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Scraper Service", self.test_scraper_service),
            ("API Documentation", self.test_api_documentation),
            ("Frontend", self.test_frontend),
            ("Direct Scraper", self.test_direct_scraper),
            ("Real-time Search", self.test_real_time_search),
            ("Image Search", self.test_image_search),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Compair is ready to use.")
        else:
            print("⚠️ Some tests failed. Check the setup and try again.")
            print("\nTroubleshooting:")
            if not results.get("Health Check"):
                print("- Make sure the main app is running: python main.py")
            if not results.get("Scraper Service"):
                print("- Make sure the scraper is running: cd scraper && npm start")
            if not results.get("Real-time Search") or not results.get("Direct Scraper"):
                print("- Check internet connection and site accessibility")
        
        return passed == total

async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test mode - just health checks
        print("🚀 Running quick tests...")
        tester = CompairTester()
        await tester.test_health_endpoint()
        await tester.test_scraper_service()
        await tester.test_frontend()
    else:
        # Full test suite
        tester = CompairTester()
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
