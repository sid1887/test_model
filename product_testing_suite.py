#!/usr/bin/env python3
"""
Comprehensive Product Testing for Cumpair System
Tests with real product data (95 products) and random images for validation
"""

import requests
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import pandas as pd

# Configure logging with UTF-8 encoding for Windows
import sys
if sys.platform.startswith('win'):
    # Handle Windows console encoding issues
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_product_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    response_time: float
    status_code: Optional[int]
    error: Optional[str]
    data: Optional[Dict[str, Any]]

@dataclass
class ProductTestResult:
    """Product-specific test result"""
    product_name: str
    test_type: str  # 'text_search' or 'image_search'
    success: bool
    response_time: float
    results_count: int
    has_duplicates: bool
    top_similarity: Optional[float]
    error: Optional[str]

class CumpairTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test data paths
        self.product_csv_path = Path("product_list.csv")
        self.test_images_dir = Path("product_images_test")
        
        # Results storage
        self.test_results: List[TestResult] = []
        self.product_results: List[ProductTestResult] = []
        
    def load_products(self) -> List[str]:
        """Load product names from CSV"""
        try:
            df = pd.read_csv(self.product_csv_path)
            products = df['Product Name'].tolist()
            logger.info(f"Loaded {len(products)} products from CSV")
            return products
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
            return []
    
    def get_test_images(self) -> List[Path]:
        """Get list of test image files"""
        if not self.test_images_dir.exists():
            logger.error(f"Test images directory not found: {self.test_images_dir}")
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        images = [
            img for img in self.test_images_dir.iterdir()
            if img.suffix.lower() in image_extensions
        ]
        logger.info(f"Found {len(images)} test images")
        return images
      def test_server_health(self) -> TestResult:
        """Test if server is running and healthy"""
        start_time = time.time()
        try:
            # Try the root endpoint first, then health endpoint
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 404:
                # Try health endpoint
                response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 404:
                # Try docs endpoint to confirm server is running
                response = self.session.get(f"{self.base_url}/docs")
            
            response_time = time.time() - start_time
            
            if response.status_code in [200, 404]:  # 404 is OK if server is running
                return TestResult(
                    test_name="Server Health",
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=None,
                    data={"status": "Server is responding"}
                )
            else:
                return TestResult(
                    test_name="Server Health",
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=f"Unexpected status code: {response.status_code}",
                    data=None
                )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name="Server Health",
                success=False,
                response_time=response_time,
                status_code=None,
                error=str(e),
                data=None
            )
    
    def test_text_search(self, query: str, top_k: int = 10) -> ProductTestResult:
        """Test text search for a specific product"""
        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.base_url}/api/search/text",
                json={"query": query, "top_k": top_k},
                headers={'Content-Type': 'application/json'}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Check for duplicates
                product_ids = [r.get('product_id') for r in results]
                has_duplicates = len(product_ids) != len(set(product_ids))
                
                # Get top similarity score
                top_similarity = results[0].get('similarity_score') if results else None
                
                return ProductTestResult(
                    product_name=query,
                    test_type="text_search",
                    success=True,
                    response_time=response_time,
                    results_count=len(results),
                    has_duplicates=has_duplicates,
                    top_similarity=top_similarity,
                    error=None
                )
            else:
                response_time = time.time() - start_time
                return ProductTestResult(
                    product_name=query,
                    test_type="text_search",
                    success=False,
                    response_time=response_time,
                    results_count=0,
                    has_duplicates=False,
                    top_similarity=None,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            response_time = time.time() - start_time
            return ProductTestResult(
                product_name=query,
                test_type="text_search",
                success=False,
                response_time=response_time,
                results_count=0,
                has_duplicates=False,
                top_similarity=None,
                error=str(e)
            )
    
    def test_image_search(self, image_path: Path, top_k: int = 10) -> ProductTestResult:
        """Test image search with a specific image"""
        start_time = time.time()
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                data = {'top_k': top_k}
                
                response = self.session.post(
                    f"{self.base_url}/api/search/image",
                    files=files,
                    data=data
                )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                results = response_data.get('results', [])
                
                # Check for duplicates
                product_ids = [r.get('product_id') for r in results]
                has_duplicates = len(product_ids) != len(set(product_ids))
                
                # Get top similarity score
                top_similarity = results[0].get('similarity_score') if results else None
                
                return ProductTestResult(
                    product_name=image_path.name,
                    test_type="image_search",
                    success=True,
                    response_time=response_time,
                    results_count=len(results),
                    has_duplicates=has_duplicates,
                    top_similarity=top_similarity,
                    error=None
                )
            else:
                response_time = time.time() - start_time
                return ProductTestResult(
                    product_name=image_path.name,
                    test_type="image_search",
                    success=False,
                    response_time=response_time,
                    results_count=0,
                    has_duplicates=False,
                    top_similarity=None,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            response_time = time.time() - start_time
            return ProductTestResult(
                product_name=image_path.name,
                test_type="image_search",
                success=False,
                response_time=response_time,
                results_count=0,
                has_duplicates=False,
                top_similarity=None,
                error=str(e)
            )
    
    def run_product_list_tests(self, sample_size: int = 20) -> None:
        """Test with products from the CSV list"""
        logger.info("=== PRODUCT LIST TESTING ===")
        
        products = self.load_products()
        if not products:
            logger.error("No products loaded, skipping product list tests")
            return
        
        # Sample products for testing (to avoid overwhelming the system)
        test_products = random.sample(products, min(sample_size, len(products)))
        logger.info(f"Testing with {len(test_products)} randomly selected products")
        
        for i, product in enumerate(test_products, 1):
            logger.info(f"Testing product {i}/{len(test_products)}: {product}")
            
            result = self.test_text_search(product)
            self.product_results.append(result)            if result.success:
                logger.info(f"[OK] Text search successful - {result.results_count} results, "
                          f"top similarity: {result.top_similarity:.3f}, "
                          f"duplicates: {result.has_duplicates}")
            else:
                logger.error(f"[FAIL] Text search failed: {result.error}")
            
            # Small delay between requests
            time.sleep(0.5)
    
    def run_image_tests(self, sample_size: int = 10) -> None:
        """Test with random images"""
        logger.info("=== RANDOM IMAGE TESTING ===")
        
        images = self.get_test_images()
        if not images:
            logger.error("No test images found, skipping image tests")
            return
        
        # Sample images for testing
        test_images = random.sample(images, min(sample_size, len(images)))
        logger.info(f"Testing with {len(test_images)} randomly selected images")
        
        for i, image_path in enumerate(test_images, 1):
            logger.info(f"Testing image {i}/{len(test_images)}: {image_path.name}")
            
            result = self.test_image_search(image_path)
            self.product_results.append(result)
            
            if result.success:
                logger.info(f"✅ Image search successful - {result.results_count} results, "
                          f"top similarity: {result.top_similarity:.3f}, "
                          f"duplicates: {result.has_duplicates}")
            else:
                logger.error(f"❌ Image search failed: {result.error}")
            
            # Small delay between requests
            time.sleep(0.5)
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        logger.info("=== COMPREHENSIVE TEST REPORT ===")
        
        # Overall statistics
        total_tests = len(self.product_results)
        successful_tests = sum(1 for r in self.product_results if r.success)
        text_search_tests = [r for r in self.product_results if r.test_type == "text_search"]
        image_search_tests = [r for r in self.product_results if r.test_type == "image_search"]
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful Tests: {successful_tests}/{total_tests} ({100*successful_tests/total_tests:.1f}%)")
        logger.info(f"Text Search Tests: {len(text_search_tests)}")
        logger.info(f"Image Search Tests: {len(image_search_tests)}")
        
        # Performance metrics
        successful_results = [r for r in self.product_results if r.success]
        if successful_results:
            avg_response_time = sum(r.response_time for r in successful_results) / len(successful_results)
            avg_results_count = sum(r.results_count for r in successful_results) / len(successful_results)
            avg_similarity = sum(r.top_similarity for r in successful_results if r.top_similarity) / len([r for r in successful_results if r.top_similarity])
            duplicate_count = sum(1 for r in successful_results if r.has_duplicates)
            
            logger.info(f"Average Response Time: {avg_response_time:.3f}s")
            logger.info(f"Average Results Count: {avg_results_count:.1f}")
            logger.info(f"Average Top Similarity: {avg_similarity:.3f}")
            logger.info(f"Tests with Duplicates: {duplicate_count}/{len(successful_results)} ({100*duplicate_count/len(successful_results):.1f}%)")
        
        # Error analysis
        failed_results = [r for r in self.product_results if not r.success]
        if failed_results:
            logger.info("=== FAILED TESTS ===")
            for result in failed_results:
                logger.error(f"❌ {result.test_type}: {result.product_name} - {result.error}")
        
        # Save detailed results to JSON
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': successful_tests/total_tests if total_tests > 0 else 0,
                'text_search_tests': len(text_search_tests),
                'image_search_tests': len(image_search_tests)
            },
            'results': [asdict(r) for r in self.product_results]
        }
        
        with open('comprehensive_test_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info("Detailed results saved to comprehensive_test_results.json")

def main():
    """Main test execution"""
    logger.info("Starting Comprehensive Product Testing")
    logger.info(f"Timestamp: {datetime.now()}")
    
    tester = CumpairTester()
    
    # Test server health first
    health_result = tester.test_server_health()
    tester.test_results.append(health_result)
    
    if not health_result.success:
        logger.error("❌ Server health check failed, aborting tests")
        logger.error(f"Error: {health_result.error}")
        return
    
    logger.info("✅ Server is healthy, proceeding with tests")
    
    # Run product list tests
    tester.run_product_list_tests(sample_size=25)  # Test 25 products
    
    # Run image tests
    tester.run_image_tests(sample_size=15)  # Test 15 images
    
    # Generate comprehensive report
    tester.generate_report()
    
    logger.info("=== TESTING COMPLETE ===")

if __name__ == "__main__":
    main()
