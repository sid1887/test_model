"""
Comprehensive Product Testing Framework for Cumpair System
Tests ML models, web scraping, and search functionality with real product data
"""

import asyncio
import csv
import json
import os
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime
import concurrent.futures
import statistics

# Configure logging with proper encoding for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_product_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class CumpairTestFramework:
    def __init__(self, base_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CumpairTestFramework/1.0',
            'Accept': 'application/json'
        })
        
        self.test_results = {
            "text_search": [],
            "image_search": [],
            "clip_search": [],
            "web_scraping": [],
            "performance_metrics": {},
            "summary": {},
            "errors": []
        }
          # Load test data
        self.product_names = self.load_product_names()
        self.test_images = self.load_test_images()
        
        # Performance tracking
        self.start_time = None
        self.end_time = None
    
    def load_product_names(self) -> List[str]:
        """Load product names from CSV file with better error handling"""
        products = []
        csv_files = ['product_list.csv', 'products.csv', 'test_products.csv']
        
        for csv_file in csv_files:
            try:
                if os.path.exists(csv_file):
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        # Try to detect delimiter
                        sample = file.read(1024)
                        file.seek(0)
                        
                        # Detect delimiter
                        if '\t' in sample:
                            delimiter = '\t'
                        elif ';' in sample:
                            delimiter = ';'
                        else:
                            delimiter = ','
                        
                        reader = csv.reader(file, delimiter=delimiter)
                        header = next(reader, None)
                        
                        # Find name column (try common variations)
                        name_column = 0
                        if header:
                            name_columns = ['name', 'product_name', 'title', 'product_title', 'item_name']
                            for i, col in enumerate(header):
                                if col.lower().strip() in name_columns:
                                    name_column = i
                                    break
                        
                        # Read product names
                        for row in reader:
                            if row and len(row) > name_column:
                                product_name = row[name_column].strip()
                                if product_name and product_name not in products:
                                    products.append(product_name)
                    
                    print(f"✅ Loaded {len(products)} products from {csv_file}")
                    break
                    
            except Exception as e:
                print(f"⚠️ Error loading {csv_file}: {e}")
                continue
        
        # Fallback test products if no CSV found
        if not products:
            products = [
                "iPhone 15 Pro",
                "Samsung Galaxy S24",
                "MacBook Pro M3",
                "Dell XPS 13",
                "Sony WH-1000XM5",
                "Apple AirPods Pro",
                "Nintendo Switch OLED",
                "PlayStation 5",
                "iPad Air",
                "Google Pixel 8"
            ]
            print(f"⚠️ No CSV found, using {len(products)} fallback test products")
        
        return products
    
    def load_test_images(self) -> List[Dict[str, Any]]:
        """Load test images from multiple possible folders"""
        images = []
        image_folders = ['product_images_test', 'test_images', 'images', 'assets/images']
        
        for folder_name in image_folders:
            image_folder = Path(folder_name)
            if image_folder.exists():
                print(f"📁 Found image folder: {image_folder}")
                break
        else:
            print("⚠️ No image folder found, image tests will be skipped")
            return images
            
        supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}        
        for image_file in image_folder.rglob('*'):
            if image_file.suffix.lower() in supported_formats:
                try:
                    with Image.open(image_file) as img:
                        # Validate image
                        img.verify()
                        
                    # Reopen for getting info (verify() closes the image)
                    with Image.open(image_file) as img:
                        images.append({
                            'filename': image_file.name,
                            'path': str(image_file),
                            'size': img.size,
                            'format': img.format,
                            'mode': img.mode,
                            'file_size': image_file.stat().st_size
                        })
                except Exception as e:
                    print(f"⚠️ Error loading image {image_file}: {e}")
        
        print(f"✅ Loaded {len(images)} test images")
        return images
        
        print(f"✅ Loaded {len(images)} test images")
        return images
    
    def check_backend_health(self) -> Tuple[bool, str]:
        """Check if backend services are running with detailed status"""
        endpoints_to_check = [
            ("/docs", "API Documentation"),
            ("/health", "Health Check"),
            ("/", "Root Endpoint"),
            ("/api/v1/status", "API Status")
        ]
        
        for endpoint, description in endpoints_to_check:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    return True, f"{description} accessible"
            except Exception as e:
                continue
        
        return False, "No backend endpoints accessible"
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 for API upload"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to encode image {image_path}: {e}")
    
    def validate_response(self, response: requests.Response, expected_fields: List[str] = None) -> Dict[str, Any]:
        """Validate API response structure"""
        try:
            data = response.json()
            
            if expected_fields:
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    return {
                        "valid": False,
                        "error": f"Missing required fields: {missing_fields}",
                        "data": data
                    }
            
            return {"valid": True, "data": data}
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON response: {e}",
                "raw_response": response.text[:500]
            }
    
    def test_text_search(self, limit: int = 10) -> None:
        """Test text-based product search with enhanced validation"""
        print(f"\n🔍 Testing Text Search (first {limit} products)...")
        
        if not self.product_names:
            print("❌ No products loaded for text search")
            return
        
        for i, product_name in enumerate(self.product_names[:limit]):
            print(f"  [{i+1}/{min(limit, len(self.product_names))}] Testing: '{product_name}'")
            start_time = time.time()
            
            try:
                # Test text search endpoint
                payload = {"query": product_name, "top_k": 5}
                response = self.session.post(
                    f"{self.base_url}/api/v1/search-by-text",
                    json=payload,
                    timeout=15
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    validation = self.validate_response(response, ["results"])
                    
                    if validation["valid"]:
                        results = validation["data"]
                        result_count = len(results.get('results', []))
                        
                        self.test_results["text_search"].append({
                            "query": product_name,
                            "status": "success",
                            "response_time": response_time,
                            "results_count": result_count,
                            "results": results.get('results', [])[:3],  # Top 3 results
                            "has_prices": any('price' in str(r).lower() for r in results.get('results', [])),
                            "has_images": any('image' in str(r).lower() for r in results.get('results', []))
                        })
                        print(f"    ✅ Found {result_count} results ({response_time:.2f}s)")
                    else:
                        print(f"    ⚠️ Invalid response structure: {validation['error']}")
                        self.test_results["text_search"].append({
                            "query": product_name,
                            "status": "invalid_response",
                            "response_time": response_time,
                            "error": validation["error"]
                        })
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    print(f"    ❌ {error_msg}")
                    self.test_results["text_search"].append({
                        "query": product_name,
                        "status": "error",
                        "response_time": response_time,
                        "error": error_msg
                    })
                    
            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)[:100]
                print(f"    ❌ Exception: {error_msg}")
                self.test_results["text_search"].append({
                    "query": product_name,
                    "status": "exception",
                    "response_time": response_time,
                    "error": error_msg
                })
    
    def test_image_analysis(self, limit: int = 5) -> None:
        """Test image upload and analysis with better error handling"""
        print(f"\n📷 Testing Image Analysis (first {limit} images)...")
        
        if not self.test_images:
            print("❌ No test images loaded for analysis")
            return
        
        for i, image_info in enumerate(self.test_images[:limit]):
            print(f"  [{i+1}/{min(limit, len(self.test_images))}] Testing: '{image_info['filename']}'")
            start_time = time.time()
            
            try:
                # Validate image file exists and is readable
                if not os.path.exists(image_info['path']):
                    raise Exception(f"Image file not found: {image_info['path']}")
                
                # Check file size (limit to 10MB)
                if image_info.get('file_size', 0) > 10 * 1024 * 1024:
                    raise Exception(f"Image too large: {image_info['file_size']} bytes")
                
                # Test image upload and analysis
                with open(image_info['path'], 'rb') as img_file:
                    files = {'file': (image_info['filename'], img_file, 'image/jpeg')}
                    
                    response = self.session.post(
                        f"{self.base_url}/api/v1/analyze",
                        files=files,
                        timeout=30
                    )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    validation = self.validate_response(response)
                    
                    if validation["valid"]:
                        results = validation["data"]
                        self.test_results["image_search"].append({
                            "image": image_info['filename'],
                            "status": "success",
                            "response_time": response_time,
                            "analysis": results,
                            "image_info": {
                                "size": image_info['size'],
                                "format": image_info['format'],
                                "file_size": image_info.get('file_size', 0)
                            }
                        })
                        print(f"    ✅ Analysis completed ({response_time:.2f}s)")
                    else:
                        print(f"    ⚠️ Invalid response: {validation['error']}")
                        self.test_results["image_search"].append({
                            "image": image_info['filename'],
                            "status": "invalid_response",
                            "response_time": response_time,
                            "error": validation["error"]
                        })
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    print(f"    ❌ {error_msg}")
                    self.test_results["image_search"].append({
                        "image": image_info['filename'],
                        "status": "error",
                        "response_time": response_time,
                        "error": error_msg
                    })
                    
            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)[:100]
                print(f"    ❌ Exception: {error_msg}")
                self.test_results["image_search"].append({
                    "image": image_info['filename'],
                    "status": "exception",
                    "response_time": response_time,
                    "error": error_msg
                })
    
    def test_clip_search(self, limit: int = 5) -> None:
        """Test CLIP-based image search with enhanced validation"""
        print(f"\n🎯 Testing CLIP Image Search (first {limit} images)...")
        
        if not self.test_images:
            print("❌ No test images loaded for CLIP search")
            return
        
        for i, image_info in enumerate(self.test_images[:limit]):
            print(f"  [{i+1}/{min(limit, len(self.test_images))}] Testing: '{image_info['filename']}'")
            start_time = time.time()
            
            try:
                # Test CLIP search endpoint
                with open(image_info['path'], 'rb') as img_file:
                    files = {'file': (image_info['filename'], img_file, 'image/jpeg')}
                    
                    response = self.session.post(
                        f"{self.base_url}/api/v1/search-by-image",
                        files=files,
                        data={'top_k': 5},
                        timeout=25
                    )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    validation = self.validate_response(response, ["results"])
                    
                    if validation["valid"]:
                        results = validation["data"]
                        result_count = len(results.get('results', []))
                        
                        self.test_results["clip_search"].append({
                            "image": image_info['filename'],
                            "status": "success",
                            "response_time": response_time,
                            "results_count": result_count,
                            "results": results.get('results', [])[:3],  # Top 3 results
                            "similarity_scores": [r.get('similarity', 0) for r in results.get('results', [])[:3]]
                        })
                        print(f"    ✅ Found {result_count} similar products ({response_time:.2f}s)")
                    else:
                        print(f"    ⚠️ Invalid response: {validation['error']}")
                        self.test_results["clip_search"].append({
                            "image": image_info['filename'],
                            "status": "invalid_response",
                            "response_time": response_time,
                            "error": validation["error"]
                        })
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    print(f"    ❌ {error_msg}")
                    self.test_results["clip_search"].append({
                        "image": image_info['filename'],
                        "status": "error",
                        "response_time": response_time,
                        "error": error_msg
                    })
                    
            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)[:100]
                print(f"    ❌ Exception: {error_msg}")
                self.test_results["clip_search"].append({
                    "image": image_info['filename'],                "status": "exception",
                    "response_time": response_time,
                    "error": error_msg
                })
    
    def test_web_scraping(self, limit: int = 3) -> None:
        """Test real-time web scraping functionality with better error handling"""
        print(f"\n🌐 Testing Web Scraping (first {limit} products)...")
        
        if not self.product_names:
            print("❌ No products loaded for web scraping")
            return
        
        for i, product_name in enumerate(self.product_names[:limit]):
            print(f"  [{i+1}/{min(limit, len(self.product_names))}] Scraping: '{product_name}'")
            start_time = time.time()
            try:
                # Test scraping endpoint with proper JSON body (fixed from params)
                data = {
                    "query": product_name,
                    "sites": ["amazon", "walmart", "ebay"]  # Use list format for JSON
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/real-time-search",
                    json=data,
                    timeout=60  # Longer timeout for scraping
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    validation = self.validate_response(response)
                    
                    if validation["valid"]:
                        results = validation["data"]
                        valid_results = results.get('valid_results', [])
                        
                        self.test_results["web_scraping"].append({
                            "query": product_name,
                            "status": "success",
                            "response_time": response_time,
                            "sites_searched": len(results.get('results', [])),
                            "valid_results": len(valid_results),
                            "price_stats": results.get('price_statistics', {}),
                            "avg_price": self._calculate_avg_price(valid_results),
                            "price_range": self._get_price_range(valid_results)
                        })
                        print(f"    ✅ Found {len(valid_results)} valid results ({response_time:.2f}s)")
                    else:
                        print(f"    ⚠️ Invalid response: {validation['error']}")
                        self.test_results["web_scraping"].append({
                            "query": product_name,
                            "status": "invalid_response",
                            "response_time": response_time,
                            "error": validation["error"]
                        })
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    print(f"    ❌ {error_msg}")
                    self.test_results["web_scraping"].append({
                        "query": product_name,
                        "status": "error",
                        "response_time": response_time,
                        "error": error_msg
                    })
                    
            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)[:100]
                print(f"    ❌ Exception: {error_msg}")
                self.test_results["web_scraping"].append({
                    "query": product_name,
                    "status": "exception",
                    "response_time": response_time,
                    "error": error_msg
                })
    
    def _calculate_avg_price(self, results: List[Dict]) -> Optional[float]:
        """Calculate average price from results"""
        try:
            prices = []
            for result in results:
                price = result.get('price', 0)
                if isinstance(price, (int, float)) and price > 0:
                    prices.append(price)
                elif isinstance(price, str):
                    # Try to extract numeric value from string
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', price.replace(',', ''))
                    if price_match:
                        prices.append(float(price_match.group()))
            
            return statistics.mean(prices) if prices else None
        except Exception:
            return None
    
    def _get_price_range(self, results: List[Dict]) -> Optional[Dict[str, float]]:
        """Get price range from results"""
        try:
            prices = []
            for result in results:
                price = result.get('price', 0)
                if isinstance(price, (int, float)) and price > 0:
                    prices.append(price)
            
            if prices:
                return {"min": min(prices), "max": max(prices)}
            return None
        except Exception:
            return None
    
    def calculate_metrics(self) -> None:
        """Calculate performance metrics and summary with enhanced statistics"""
        print("\n📊 Calculating Performance Metrics...")
        
        def get_component_metrics(component_results: List[Dict]) -> Dict[str, Any]:
            if not component_results:
                return {
                    "success_rate": "0.0%",
                    "avg_response_time": "0.00s",
                    "median_response_time": "0.00s",
                    "total_tests": 0,
                    "successful": 0,
                    "failed": 0,
                    "response_times": []
                }
            
            successful = [r for r in component_results if r["status"] == "success"]
            failed = [r for r in component_results if r["status"] != "success"]
            response_times = [r["response_time"] for r in component_results]
            
            return {
                "success_rate": f"{(len(successful)/len(component_results)*100):.1f}%",
                "avg_response_time": f"{statistics.mean(response_times):.2f}s",
                "median_response_time": f"{statistics.median(response_times):.2f}s",
                "min_response_time": f"{min(response_times):.2f}s",
                "max_response_time": f"{max(response_times):.2f}s",
                "total_tests": len(component_results),
                "successful": len(successful),
                "failed": len(failed),
                "response_times": response_times
            }
        
        # Calculate metrics for each component
        self.test_results["performance_metrics"] = {
            "text_search": get_component_metrics(self.test_results["text_search"]),
            "image_analysis": get_component_metrics(self.test_results["image_search"]),
            "clip_search": get_component_metrics(self.test_results["clip_search"]),
            "web_scraping": get_component_metrics(self.test_results["web_scraping"])
        }
        
        # Overall summary
        all_results = (
            self.test_results["text_search"] + 
            self.test_results["image_search"] + 
            self.test_results["clip_search"] + 
            self.test_results["web_scraping"]
        )
        
        total_tests = len(all_results)
        total_successful = len([r for r in all_results if r["status"] == "success"])
        
        self.test_results["summary"] = {
            "overall_success_rate": f"{(total_successful/max(total_tests,1)*100):.1f}%",
            "total_tests": total_tests,
            "total_successful": total_successful,
            "total_failed": total_tests - total_successful,
            "products_available": len(self.product_names),
            "images_available": len(self.test_images),
            "test_duration": f"{(self.end_time - self.start_time):.2f}s" if self.end_time and self.start_time else "Unknown",
            "test_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backend_url": self.base_url,
            "frontend_url": self.frontend_url
        }
    
    def print_summary(self) -> None:
        """Print comprehensive test results summary"""
        print("\n" + "="*70)
        print("🎯 COMPREHENSIVE CUMPAIR TEST RESULTS SUMMARY")
        print("="*70)
        
        metrics = self.test_results["performance_metrics"]
        summary = self.test_results["summary"]
        
        # Overall statistics
        print(f"📊 Overall Success Rate: {summary['overall_success_rate']}")
        print(f"📈 Total Tests Run: {summary['total_tests']}")
        print(f"✅ Successful Tests: {summary['total_successful']}")
        print(f"❌ Failed Tests: {summary['total_failed']}")
        print(f"⏱️ Test Duration: {summary['test_duration']}")
        print(f"📦 Products Available: {summary['products_available']}")
        print(f"🖼️ Images Available: {summary['images_available']}")
        
        # Component performance
        print("\n📋 Component Performance Details:")
        print("-" * 50)
        
        for component, data in metrics.items():
            component_name = component.replace('_', ' ').title()
            print(f"\n{component_name}:")
            print(f"  Success Rate: {data['success_rate']}")
            print(f"  Avg Response: {data['avg_response_time']}")
            print(f"  Median Response: {data['median_response_time']}")
            print(f"  Response Range: {data.get('min_response_time', 'N/A')} - {data.get('max_response_time', 'N/A')}")
            print(f"  Tests: {data['successful']}/{data['total_tests']} passed")
        
        # Recommendations
        print("\n💡 Recommendations:")
        print("-" * 30)
        
        if float(summary['overall_success_rate'].rstrip('%')) < 80:
            print("⚠️  Overall success rate is below 80% - investigate failing components")
        
        for component, data in metrics.items():
            if float(data['avg_response_time'].rstrip('s')) > 5:
                print(f"⚠️  {component.replace('_', ' ').title()} is slow (>{data['avg_response_time']})")
            
            if float(data['success_rate'].rstrip('%')) < 70:
                print(f"❌ {component.replace('_', ' ').title()} has low success rate ({data['success_rate']})")
        
        print(f"\n🕐 Test Completed: {summary['test_timestamp']}")
        print(f"🌐 Backend URL: {summary['backend_url']}")
        print("="*70)
    
    def save_results(self, filename: str = None) -> None:
        """Save test results to JSON file with timestamp"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cumpair_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {filename}")
            
            # Also save a CSV summary for easy analysis
            self.save_csv_summary(filename.replace('.json', '_summary.csv'))
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def save_csv_summary(self, filename: str) -> None:
        """Save a CSV summary of test results"""
        try:
            summary_data = []
            
            # Add component summaries
            for component, metrics in self.test_results["performance_metrics"].items():
                summary_data.append({
                    'Component': component.replace('_', ' ').title(),
                    'Success Rate': metrics['success_rate'],
                    'Avg Response Time': metrics['avg_response_time'],
                    'Total Tests': metrics['total_tests'],
                    'Successful': metrics['successful'],
                    'Failed': metrics['failed']
                })
            
            df = pd.DataFrame(summary_data)
            df.to_csv(filename, index=False)
            print(f"📊 CSV summary saved to {filename}")
            
        except Exception as e:
            print(f"⚠️ Could not save CSV summary: {e}")
    
    def run_comprehensive_test(self, text_limit: int = 10, image_limit: int = 5, 
                             clip_limit: int = 5, scraping_limit: int = 3):
        """Run all tests in sequence with configurable limits"""
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive Cumpair System Test...")
        print(f"📦 Loaded {len(self.product_names)} products for testing")
        print(f"🖼️ Loaded {len(self.test_images)} test images")
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"🖥️ Frontend URL: {self.frontend_url}")
        
        # Check backend health first
        is_healthy, status_msg = self.check_backend_health()
        if not is_healthy:
            print(f"❌ Backend server health check failed: {status_msg}")
            print("   Please ensure the Cumpair server is running and accessible")
            return False
        
        print(f"✅ Backend server is healthy: {status_msg}")
        
        # Run all test suites with error handling
        try:
            self.test_text_search(limit=text_limit)
            self.test_image_analysis(limit=image_limit) 
            self.test_clip_search(limit=clip_limit)
            self.test_web_scraping(limit=scraping_limit)
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during testing: {e}")
            return False
        
        finally:
            self.end_time = time.time()
            
            # Calculate metrics and print summary
            self.calculate_metrics()
            self.print_summary()
            self.save_results()
            
            return True

    def run_quick_test(self):
        """Run a quick test with limited scope for rapid feedback"""
        print("⚡ Running Quick Test (limited scope)...")
        return self.run_comprehensive_test(
            text_limit=3, 
            image_limit=2, 
            clip_limit=2, 
            scraping_limit=1
        )
    
    def run_stress_test(self):
        """Run a comprehensive stress test with all available data"""
        print("💪 Running Stress Test (full scope)...")
        return self.run_comprehensive_test(
            text_limit=len(self.product_names), 
            image_limit=len(self.test_images), 
            clip_limit=len(self.test_images), 
            scraping_limit=min(10, len(self.product_names))
        )
    
    def test_concurrent_requests(self, num_concurrent: int = 5):
        """Test system under concurrent load"""
        print(f"\n🔥 Testing Concurrent Requests ({num_concurrent} simultaneous)...")
        
        if not self.product_names:
            print("❌ No products available for concurrent testing")
            return
        
        def make_request(product_name: str) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/search-by-text",
                    json={"query": product_name, "top_k": 3},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                return {
                    "product": product_name,
                    "status": "success" if response.status_code == 200 else "error",
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "product": product_name,
                    "status": "exception",
                    "response_time": time.time() - start_time,
                    "error": str(e)
                }
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            test_products = self.product_names[:num_concurrent]
            futures = [executor.submit(make_request, product) for product in test_products]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Analyze concurrent test results
        successful = len([r for r in results if r["status"] == "success"])
        avg_response_time = statistics.mean([r["response_time"] for r in results])
        
        print(f"  ✅ Concurrent Test Results:")
        print(f"    Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
        print(f"    Avg Response Time: {avg_response_time:.2f}s")
        print(f"    Max Response Time: {max(r['response_time'] for r in results):.2f}s")
        
        return results
    
    def generate_performance_report(self, output_file: str = "performance_report.html"):
        """Generate an HTML performance report"""
        try:
            html_content = self._create_html_report()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📊 Performance report generated: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating performance report: {e}")
            return False
    
    def _create_html_report(self) -> str:
        """Create HTML performance report"""
        metrics = self.test_results.get("performance_metrics", {})
        summary = self.test_results.get("summary", {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cumpair System Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .metric-card {{ 
                    border: 1px solid #ddd; margin: 10px; padding: 15px; 
                    border-radius: 5px; display: inline-block; min-width: 200px; 
                }}
                .success {{ background: #d4edda; border-color: #c3e6cb; }}
                .warning {{ background: #fff3cd; border-color: #ffeaa7; }}
                .error {{ background: #f8d7da; border-color: #f5c6cb; }}
                .table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Cumpair System Performance Report</h1>
                <p>Generated: {summary.get('test_timestamp', 'Unknown')}</p>
                <p>Test Duration: {summary.get('test_duration', 'Unknown')}</p>
            </div>
            
            <h2>📊 Overall Statistics</h2>
            <div class="metric-card {'success' if float(summary.get('overall_success_rate', '0%').rstrip('%')) >= 80 else 'warning'}">
                <h3>Overall Success Rate</h3>
                <p style="font-size: 24px; margin: 0;">{summary.get('overall_success_rate', 'N/A')}</p>
            </div>
            
            <div class="metric-card">
                <h3>Total Tests</h3>
                <p style="font-size: 24px; margin: 0;">{summary.get('total_tests', 0)}</p>
            </div>
            
            <div class="metric-card">
                <h3>Products Tested</h3>
                <p style="font-size: 24px; margin: 0;">{summary.get('products_available', 0)}</p>
            </div>
            
            <div class="metric-card">
                <h3>Images Tested</h3>
                <p style="font-size: 24px; margin: 0;">{summary.get('images_available', 0)}</p>
            </div>
            
            <h2>📋 Component Performance</h2>
            <table class="table">
                <tr>
                    <th>Component</th>
                    <th>Success Rate</th>
                    <th>Avg Response Time</th>
                    <th>Tests Run</th>
                    <th>Status</th>
                </tr>
        """
        
        for component, data in metrics.items():
            success_rate = float(data.get('success_rate', '0%').rstrip('%'))
            status_class = 'success' if success_rate >= 80 else 'warning' if success_rate >= 60 else 'error'
            status_text = '✅ Good' if success_rate >= 80 else '⚠️ Issues' if success_rate >= 60 else '❌ Poor'
            
            html += f"""
                <tr class="{status_class}">
                    <td>{component.replace('_', ' ').title()}</td>
                    <td>{data.get('success_rate', 'N/A')}</td>
                    <td>{data.get('avg_response_time', 'N/A')}</td>
                    <td>{data.get('successful', 0)}/{data.get('total_tests', 0)}</td>
                    <td>{status_text}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>🔍 Test Details</h2>
            <details>
                <summary>Click to view detailed test results</summary>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">
        """
        
        html += json.dumps(self.test_results, indent=2, ensure_ascii=False)[:5000]
        if len(json.dumps(self.test_results)) > 5000:
            html += "\n... (truncated for display)"
        
        html += """
                </pre>
            </details>
            
            <footer style="margin-top: 50px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
                <p><strong>Cumpair Testing Framework</strong> - Comprehensive system testing and performance monitoring</p>
                <p>For issues or questions, please check the system logs and API documentation.</p>
            </footer>
        </body>
        </html>
        """
        
        return html


def main():
    """Main test execution with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cumpair System Testing Framework')
    parser.add_argument('--mode', choices=['quick', 'full', 'stress'], default='full',
                        help='Test mode: quick (limited), full (standard), stress (comprehensive)')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                        help='Backend server URL')
    parser.add_argument('--frontend-url', default='http://localhost:3000',
                        help='Frontend server URL')
    parser.add_argument('--concurrent', type=int, default=0,
                        help='Run concurrent load test with specified number of requests')
    parser.add_argument('--report', action='store_true',
                        help='Generate HTML performance report')
    parser.add_argument('--text-limit', type=int, default=10,
                        help='Number of text search tests to run')
    parser.add_argument('--image-limit', type=int, default=5,
                        help='Number of image tests to run')
    parser.add_argument('--scraping-limit', type=int, default=3,
                        help='Number of web scraping tests to run')
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = CumpairTestFramework(
        base_url=args.backend_url,
        frontend_url=args.frontend_url
    )
    
    # Run tests based on mode
    try:
        if args.mode == 'quick':
            success = framework.run_quick_test()
        elif args.mode == 'stress':
            success = framework.run_stress_test()
        else:  # full
            success = framework.run_comprehensive_test(
                text_limit=args.text_limit,
                image_limit=args.image_limit,
                clip_limit=args.image_limit,
                scraping_limit=args.scraping_limit
            )
        
        # Run concurrent test if requested
        if args.concurrent > 0:
            framework.test_concurrent_requests(args.concurrent)
        
        # Generate report if requested
        if args.report:
            framework.generate_performance_report()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())