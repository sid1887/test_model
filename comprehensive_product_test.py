"""
Comprehensive Product Testing Framework for Cumpair System
Tests ML models, web scraping, and search functionality with real product data
"""

import asyncio
import csv
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

class CumpairTestFramework:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {
            "text_search": [],
            "image_search": [],
            "clip_search": [],
            "web_scraping": [],
            "performance_metrics": {},
            "summary": {}
        }
        
        # Load test data
        self.product_names = self.load_product_names()
        self.test_images = self.load_test_images()
        
    def load_product_names(self) -> List[str]:
        """Load product names from CSV file"""
        products = []
        try:
            with open('product_list.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    products.append(row['Product Name'].strip())
        except Exception as e:
            print(f"❌ Error loading product names: {e}")
        return products
    
    def load_test_images(self) -> List[Dict[str, Any]]:
        """Load test images from product_images_test folder"""
        images = []
        image_folder = Path('product_images_test')
        
        if not image_folder.exists():
            print(f"❌ Image folder not found: {image_folder}")
            return images
              for image_file in image_folder.glob('*'):
            if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    # Get image info
                    with Image.open(image_file) as img:
                        images.append({
                            'filename': image_file.name,
                            'path': str(image_file),
                            'size': img.size,
                            'format': img.format,
                            'mode': img.mode
                        })
                except Exception as e:
                    print(f"⚠️ Error loading image {image_file}: {e}")
        
        return images
    
    def check_backend_health(self) -> bool:
        """Check if backend services are running"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 for API upload"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def test_text_search(self, limit: int = 10) -> None:
        """Test text-based product search"""
        print(f"\n🔍 Testing Text Search (first {limit} products)...")
        
        for i, product_name in enumerate(self.product_names[:limit]):
            print(f"  [{i+1}/{limit}] Testing: '{product_name}'")
            start_time = time.time()
            
            try:                # Test text search endpoint
                response = requests.post(
                    f"{self.base_url}/api/v1/search-by-text",
                    json={"query": product_name, "top_k": 5},
                    timeout=10
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results = response.json()
                    self.test_results["text_search"].append({
                        "query": product_name,
                        "status": "success",
                        "response_time": response_time,
                        "results_count": len(results.get('results', [])),
                        "results": results.get('results', [])[:3]  # Top 3 results
                    })
                    print(f"    ✅ Found {len(results.get('results', []))} results ({response_time:.2f}s)")
                else:
                    self.test_results["text_search"].append({
                        "query": product_name,
                        "status": "error",
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"    ❌ Error: HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_results["text_search"].append({
                    "query": product_name,
                    "status": "error",
                    "error": str(e)
                })
                print(f"    ❌ Exception: {e}")
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
    
    async def test_image_search(self, limit: int = 5) -> None:
        """Test image-based product search"""
        print(f"\n📸 Testing Image Search (first {limit} images)...")
        
        for i, image_info in enumerate(self.test_images[:limit]):
            print(f"  [{i+1}/{limit}] Testing: '{image_info['filename']}'")
            start_time = time.time()
            
            try:                # Test image upload and analysis
                with open(image_info['path'], 'rb') as img_file:
                    files = {'file': (image_info['filename'], img_file, 'image/jpeg')}
                      response = requests.post(
                        f"{self.base_url}/api/v1/analyze",
                        files=files,
                        timeout=30
                    )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results = response.json()
                    self.test_results["image_search"].append({
                        "image": image_info['filename'],
                        "status": "success",
                        "response_time": response_time,
                        "analysis": results
                    })
                    print(f"    ✅ Analysis completed ({response_time:.2f}s)")
                    
                    # Print key findings
                    if 'objects_detected' in results:
                        objects = len(results['objects_detected'])
                        print(f"    📦 Detected {objects} objects")
                    
                else:
                    self.test_results["image_search"].append({
                        "image": image_info['filename'],
                        "status": "error",
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"    ❌ Error: HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_results["image_search"].append({
                    "image": image_info['filename'],
                    "status": "error",
                    "error": str(e)
                })
                print(f"    ❌ Exception: {e}")
            
            await asyncio.sleep(1)  # Longer delay for image processing
    
    async def test_clip_search(self, limit: int = 5) -> None:
        """Test CLIP-based similarity search"""
        print(f"\n🔗 Testing CLIP Similarity Search (first {limit} images)...")
        
        for i, image_info in enumerate(self.test_images[:limit]):
            print(f"  [{i+1}/{limit}] Testing CLIP search: '{image_info['filename']}'")
            start_time = time.time()
            
            try:                # Test CLIP search endpoint
                with open(image_info['path'], 'rb') as img_file:
                    files = {'file': (image_info['filename'], img_file, 'image/jpeg')}
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/search-by-image",
                        files=files,
                        data={'top_k': 5},
                        timeout=20
                    )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results = response.json()
                    self.test_results["clip_search"].append({
                        "image": image_info['filename'],
                        "status": "success",
                        "response_time": response_time,
                        "matches": len(results.get('matches', [])),
                        "results": results.get('matches', [])
                    })
                    print(f"    ✅ Found {len(results.get('matches', []))} similar items ({response_time:.2f}s)")
                else:
                    self.test_results["clip_search"].append({
                        "image": image_info['filename'],
                        "status": "error",
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"    ❌ Error: HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_results["clip_search"].append({
                    "image": image_info['filename'],
                    "status": "error",
                    "error": str(e)
                })
                print(f"    ❌ Exception: {e}")
            
            await asyncio.sleep(1)
    
    async def test_web_scraping(self, limit: int = 5) -> None:
        """Test web scraping functionality"""
        print(f"\n🕷️ Testing Web Scraping (first {limit} products)...")
        
        for i, product_name in enumerate(self.product_names[:limit]):
            print(f"  [{i+1}/{limit}] Scraping: '{product_name}'")
            start_time = time.time()
            
            try:                # Test scraping endpoint
                response = requests.post(
                    f"{self.base_url}/api/v1/real-time-search",
                    json={
                        "query": product_name,
                        "sites": ["amazon", "flipkart", "ebay"]
                    },
                    timeout=60  # Longer timeout for scraping
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results = response.json()
                    self.test_results["web_scraping"].append({
                        "query": product_name,
                        "status": "success",
                        "response_time": response_time,
                        "results_count": len(results.get('results', [])),
                        "sources_found": len(set(r.get('source', '') for r in results.get('results', []))),
                        "results": results.get('results', [])[:3]
                    })
                    print(f"    ✅ Scraped {len(results.get('results', []))} results ({response_time:.2f}s)")
                else:
                    self.test_results["web_scraping"].append({
                        "query": product_name,
                        "status": "error",
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"    ❌ Error: HTTP {response.status_code}")
                    
            except Exception as e:
                self.test_results["web_scraping"].append({
                    "query": product_name,
                    "status": "error",
                    "error": str(e)
                })
                print(f"    ❌ Exception: {e}")
            
            await asyncio.sleep(2)  # Delay to be respectful to target sites
    
    def generate_performance_metrics(self) -> None:
        """Calculate performance metrics"""
        print("\n📊 Calculating Performance Metrics...")
        
        # Text Search Metrics
        text_success = [r for r in self.test_results["text_search"] if r["status"] == "success"]
        text_times = [r["response_time"] for r in text_success]
        
        # Image Search Metrics
        image_success = [r for r in self.test_results["image_search"] if r["status"] == "success"]
        image_times = [r["response_time"] for r in image_success]
        
        # CLIP Search Metrics
        clip_success = [r for r in self.test_results["clip_search"] if r["status"] == "success"]
        clip_times = [r["response_time"] for r in clip_success]
        
        # Web Scraping Metrics
        scraping_success = [r for r in self.test_results["web_scraping"] if r["status"] == "success"]
        scraping_times = [r["response_time"] for r in scraping_success]
        
        self.test_results["performance_metrics"] = {
            "text_search": {
                "total_tests": len(self.test_results["text_search"]),
                "successful": len(text_success),
                "success_rate": len(text_success) / len(self.test_results["text_search"]) * 100 if self.test_results["text_search"] else 0,
                "avg_response_time": sum(text_times) / len(text_times) if text_times else 0,
                "min_response_time": min(text_times) if text_times else 0,
                "max_response_time": max(text_times) if text_times else 0
            },
            "image_search": {
                "total_tests": len(self.test_results["image_search"]),
                "successful": len(image_success),
                "success_rate": len(image_success) / len(self.test_results["image_search"]) * 100 if self.test_results["image_search"] else 0,
                "avg_response_time": sum(image_times) / len(image_times) if image_times else 0,
                "min_response_time": min(image_times) if image_times else 0,
                "max_response_time": max(image_times) if image_times else 0
            },
            "clip_search": {
                "total_tests": len(self.test_results["clip_search"]),
                "successful": len(clip_success),
                "success_rate": len(clip_success) / len(self.test_results["clip_search"]) * 100 if self.test_results["clip_search"] else 0,
                "avg_response_time": sum(clip_times) / len(clip_times) if clip_times else 0,
                "min_response_time": min(clip_times) if clip_times else 0,
                "max_response_time": max(clip_times) if clip_times else 0
            },
            "web_scraping": {
                "total_tests": len(self.test_results["web_scraping"]),
                "successful": len(scraping_success),
                "success_rate": len(scraping_success) / len(self.test_results["web_scraping"]) * 100 if self.test_results["web_scraping"] else 0,
                "avg_response_time": sum(scraping_times) / len(scraping_times) if scraping_times else 0,
                "min_response_time": min(scraping_times) if scraping_times else 0,
                "max_response_time": max(scraping_times) if scraping_times else 0
            }
        }
    
    def generate_summary_report(self) -> None:
        """Generate comprehensive test summary"""
        print("\n📋 Generating Summary Report...")
        
        metrics = self.test_results["performance_metrics"]
        
        self.test_results["summary"] = {
            "test_execution_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_products_tested": len(self.product_names),
            "total_images_tested": len(self.test_images),
            "overall_performance": {
                "text_search_success_rate": metrics["text_search"]["success_rate"],
                "image_search_success_rate": metrics["image_search"]["success_rate"],
                "clip_search_success_rate": metrics["clip_search"]["success_rate"],
                "web_scraping_success_rate": metrics["web_scraping"]["success_rate"],
                "avg_text_search_time": metrics["text_search"]["avg_response_time"],
                "avg_image_search_time": metrics["image_search"]["avg_response_time"],
                "avg_clip_search_time": metrics["clip_search"]["avg_response_time"],
                "avg_scraping_time": metrics["web_scraping"]["avg_response_time"]
            },
            "recommendations": self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on test results"""
        recommendations = []
        metrics = self.test_results["performance_metrics"]
        
        # Success rate recommendations
        if metrics["text_search"]["success_rate"] < 80:
            recommendations.append("🔧 Improve text search algorithm - success rate below 80%")
        
        if metrics["image_search"]["success_rate"] < 70:
            recommendations.append("🔧 Enhance image processing pipeline - success rate below 70%")
            
        if metrics["clip_search"]["success_rate"] < 75:
            recommendations.append("🔧 Optimize CLIP model performance - success rate below 75%")
            
        if metrics["web_scraping"]["success_rate"] < 60:
            recommendations.append("🔧 Improve web scraping reliability - success rate below 60%")
        
        # Performance recommendations
        if metrics["text_search"]["avg_response_time"] > 2:
            recommendations.append("⚡ Optimize text search response time - currently > 2s")
            
        if metrics["image_search"]["avg_response_time"] > 10:
            recommendations.append("⚡ Optimize image processing time - currently > 10s")
            
        if metrics["clip_search"]["avg_response_time"] > 5:
            recommendations.append("⚡ Optimize CLIP search time - currently > 5s")
        
        if not recommendations:
            recommendations.append("✅ All systems performing within acceptable parameters!")
        
        return recommendations
    
    def save_results(self, filename: str = "test_results.json") -> None:
        """Save test results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        print(f"💾 Test results saved to {filename}")
    
    def print_summary(self) -> None:
        """Print test summary to console"""
        print("\n" + "="*80)
        print("🎯 CUMPAIR SYSTEM TEST SUMMARY")
        print("="*80)
        
        summary = self.test_results["summary"]
        metrics = self.test_results["performance_metrics"]
        
        print(f"📅 Test Date: {summary['test_execution_time']}")
        print(f"📦 Products Tested: {summary['total_products_tested']}")
        print(f"🖼️ Images Tested: {summary['total_images_tested']}")
        
        print("\n📊 SUCCESS RATES:")
        print(f"  Text Search:    {metrics['text_search']['success_rate']:.1f}% ({metrics['text_search']['successful']}/{metrics['text_search']['total_tests']})")
        print(f"  Image Search:   {metrics['image_search']['success_rate']:.1f}% ({metrics['image_search']['successful']}/{metrics['image_search']['total_tests']})")
        print(f"  CLIP Search:    {metrics['clip_search']['success_rate']:.1f}% ({metrics['clip_search']['successful']}/{metrics['clip_search']['total_tests']})")
        print(f"  Web Scraping:   {metrics['web_scraping']['success_rate']:.1f}% ({metrics['web_scraping']['successful']}/{metrics['web_scraping']['total_tests']})")
        
        print("\n⏱️ AVERAGE RESPONSE TIMES:")
        print(f"  Text Search:    {metrics['text_search']['avg_response_time']:.2f}s")
        print(f"  Image Search:   {metrics['image_search']['avg_response_time']:.2f}s")
        print(f"  CLIP Search:    {metrics['clip_search']['avg_response_time']:.2f}s")
        print(f"  Web Scraping:   {metrics['web_scraping']['avg_response_time']:.2f}s")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in summary['recommendations']:
            print(f"  {rec}")
        
        print("="*80)

    async def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive Cumpair System Test")
        print(f"📋 Found {len(self.product_names)} products to test")
        print(f"🖼️ Found {len(self.test_images)} images to test")
        
        # Check backend health
        if not self.check_backend_health():
            print("❌ Backend not running! Please start the backend server first.")
            return
        
        print("✅ Backend is running, starting tests...")
        
        # Run all tests
        await self.test_text_search(limit=10)
        await self.test_image_search(limit=5)
        await self.test_clip_search(limit=5)
        await self.test_web_scraping(limit=5)
        
        # Generate metrics and reports
        self.generate_performance_metrics()
        self.generate_summary_report()
        
        # Save and display results
        self.save_results("cumpair_test_results.json")
        self.print_summary()

# Main execution
async def main():
    """Main test execution function"""
    tester = CumpairTestFramework()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
