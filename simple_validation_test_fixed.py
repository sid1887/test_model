#!/usr/bin/env python3
"""
Enhanced Final Validation Test for Cumpair System
Comprehensive testing suite with improved error handling, logging, and metrics
"""
import requests
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('validation_test.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Data class for test results"""
    passed: bool
    message: str
    metrics: Dict = None
    error: Optional[str] = None

class CumpairValidator:
    """Enhanced validator for Cumpair system"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CumpairValidator/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            logger.debug(f"{method} {url} -> {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
    
    def test_server_health(self) -> TestResult:
        """Test if server is running and healthy"""
        logger.info("Testing server health...")
        
        try:
            start_time = time.time()
            response = self._make_request('GET', '/api/v1/health')
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    metrics = {
                        'response_time_ms': round(response_time * 1000, 2),
                        'status_code': response.status_code,
                        'server_status': status
                    }
                    
                    if status == 'healthy':
                        return TestResult(
                            passed=True,
                            message=f"Server healthy (response time: {metrics['response_time_ms']}ms)",
                            metrics=metrics
                        )
                    else:
                        return TestResult(
                            passed=False,
                            message=f"Server unhealthy: {status}",
                            metrics=metrics
                        )
                        
                except json.JSONDecodeError:
                    return TestResult(
                        passed=True,  # Assume healthy if we get 200 but no JSON
                        message=f"Server responding (response time: {round(response_time * 1000, 2)}ms)",
                        metrics={'response_time_ms': round(response_time * 1000, 2)}
                    )
            else:
                return TestResult(
                    passed=False,
                    message=f"Server returned status code {response.status_code}",
                    error=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            return TestResult(
                passed=False,
                message="Cannot connect to server - is it running?",
                error="Connection refused"
            )
        except requests.exceptions.Timeout:
            return TestResult(
                passed=False,
                message=f"Server health check timed out after {self.timeout}s",
                error="Timeout"
            )
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Unexpected error during health check: {str(e)}",
                error=str(e)
            )
    
    def test_text_search(self, query: str = "wall clock", top_k: int = 5) -> TestResult:
        """Test text search functionality with comprehensive validation"""
        logger.info(f"Testing text search with query: '{query}'...")
        
        try:
            start_time = time.time()
            response = self._make_request(
                'POST',
                '/api/v1/search-by-text',
                json={"query": query, "top_k": top_k}
            )
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return TestResult(
                    passed=False,
                    message=f"Text search failed with status {response.status_code}",
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                return TestResult(
                    passed=False,
                    message="Invalid JSON response from text search",
                    error=f"JSON decode error: {e}"
                )
            
            results = data.get("results", [])
            
            # Validate response structure
            if not isinstance(results, list):
                return TestResult(
                    passed=False,
                    message="Invalid response format - 'results' should be a list",
                    error="Invalid response structure"
                )
            
            # Check for duplicates
            product_ids = []
            valid_results = 0
            
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    logger.warning(f"Result {i} is not a dictionary")
                    continue
                
                product_id = result.get("product_id")
                if product_id:
                    product_ids.append(product_id)
                    valid_results += 1
                else:
                    logger.warning(f"Result {i} missing product_id")
            
            unique_ids = set(product_ids)
            duplicate_count = len(product_ids) - len(unique_ids)
            
            metrics = {
                'response_time_ms': round(response_time * 1000, 2),
                'total_results': len(results),
                'valid_results': valid_results,
                'unique_products': len(unique_ids),
                'duplicates': duplicate_count,
                'query': query,
                'requested_top_k': top_k
            }
            
            if duplicate_count == 0 and valid_results > 0:
                return TestResult(
                    passed=True,
                    message=f"Text search successful - {valid_results} unique results",
                    metrics=metrics
                )
            elif duplicate_count > 0:
                return TestResult(
                    passed=False,
                    message=f"Text search has {duplicate_count} duplicate(s)",
                    metrics=metrics,
                    error=f"{duplicate_count} duplicate product IDs found"
                )
            else:
                return TestResult(
                    passed=False,
                    message="Text search returned no valid results",
                    metrics=metrics,
                    error="No valid results with product_id"
                )
                
        except requests.exceptions.Timeout:
            return TestResult(
                passed=False,
                message=f"Text search timed out after {self.timeout}s",
                error="Request timeout"
            )
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Text search failed with error: {str(e)}",
                error=str(e)
            )
    
    def test_image_search(self, image_dir: str = "product_images_test", top_k: int = 5) -> TestResult:
        """Test image search functionality with comprehensive validation"""
        logger.info("Testing image search...")
        
        try:
            # Find test images
            image_path = Path(image_dir)
            if not image_path.exists():
                return TestResult(
                    passed=False,
                    message=f"Image directory '{image_dir}' not found",
                    error="Missing test images directory"
                )
            
            # Look for various image formats
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']
            test_images = []
            for ext in image_extensions:
                test_images.extend(list(image_path.glob(ext)))
                test_images.extend(list(image_path.glob(ext.upper())))
            
            if not test_images:
                return TestResult(
                    passed=False,
                    message=f"No test images found in '{image_dir}'",
                    error="No test images available"
                )
            
            # Use the first available image
            test_image = test_images[0]
            logger.info(f"Using test image: {test_image.name}")
            
            # Check file size
            file_size = test_image.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                logger.warning(f"Large image file: {file_size / 1024 / 1024:.1f}MB")
            
            start_time = time.time()
            
            with open(test_image, 'rb') as f:
                files = {'file': (test_image.name, f, 'image/jpeg')}
                data = {'top_k': top_k}
                
                response = self._make_request(
                    'POST',
                    '/api/v1/search-by-image',
                    files=files,
                    data=data
                )
            
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return TestResult(
                    passed=False,
                    message=f"Image search failed with status {response.status_code}",
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                return TestResult(
                    passed=False,
                    message="Invalid JSON response from image search",
                    error=f"JSON decode error: {e}"
                )
            
            results = response_data.get("results", [])
            
            # Validate response structure
            if not isinstance(results, list):
                return TestResult(
                    passed=False,
                    message="Invalid response format - 'results' should be a list",
                    error="Invalid response structure"
                )
            
            # Check for duplicates and validate results
            product_ids = []
            valid_results = 0
            
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    logger.warning(f"Result {i} is not a dictionary")
                    continue
                
                product_id = result.get("product_id")
                if product_id:
                    product_ids.append(product_id)
                    valid_results += 1
                else:
                    logger.warning(f"Result {i} missing product_id")
            
            unique_ids = set(product_ids)
            duplicate_count = len(product_ids) - len(unique_ids)
            
            metrics = {
                'response_time_ms': round(response_time * 1000, 2),
                'total_results': len(results),
                'valid_results': valid_results,
                'unique_products': len(unique_ids),
                'duplicates': duplicate_count,
                'test_image': test_image.name,
                'image_size_bytes': file_size,
                'requested_top_k': top_k,
                'available_images': len(test_images)
            }
            
            if duplicate_count == 0 and valid_results > 0:
                return TestResult(
                    passed=True,
                    message=f"Image search successful - {valid_results} unique results",
                    metrics=metrics
                )
            elif duplicate_count > 0:
                return TestResult(
                    passed=False,
                    message=f"Image search has {duplicate_count} duplicate(s)",
                    metrics=metrics,
                    error=f"{duplicate_count} duplicate product IDs found"
                )
            else:
                return TestResult(
                    passed=False,
                    message="Image search returned no valid results",
                    metrics=metrics,
                    error="No valid results with product_id"
                )
                
        except requests.exceptions.Timeout:
            return TestResult(
                passed=False,
                message=f"Image search timed out after {self.timeout}s",
                error="Request timeout"
            )
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Image search failed with error: {str(e)}",
                error=str(e)
            )

def print_test_result(test_name: str, result: TestResult, verbose: bool = True):
    """Print formatted test result"""
    status = "✅" if result.passed else "❌"
    print(f"{status} {test_name}: {result.message}")
    
    if verbose and result.metrics:
        for key, value in result.metrics.items():
            print(f"   • {key}: {value}")
    
    if result.error and not result.passed:
        print(f"   ⚠️  Error: {result.error}")

def main():
    """Run comprehensive validation tests"""
    print("🚀 Enhanced Final Validation Test for Cumpair System")
    print("=" * 60)
    
    # Initialize validator
    validator = CumpairValidator()
    
    # Track results
    test_results = []
    
    # Test 1: Server Health
    print("\n🏥 Testing server health...")
    health_result = validator.test_server_health()
    test_results.append(('Server Health', health_result))
    print_test_result('Server Health', health_result)
    
    if not health_result.passed:
        print("\n❌ Cannot proceed with other tests - server is not accessible")
        return
    
    # Test 2: Text Search
    print("\n📝 Testing text search...")
    text_result = validator.test_text_search("wall clock", top_k=5)
    test_results.append(('Text Search', text_result))
    print_test_result('Text Search', text_result)
    
    # Test 3: Image Search
    print("\n🖼️ Testing image search...")
    image_result = validator.test_image_search("product_images_test", top_k=5)
    test_results.append(('Image Search', image_result))
    print_test_result('Image Search', image_result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    passed_tests = sum(1 for _, result in test_results if result.passed)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  {test_name:.<30} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! System is ready for deployment.")
        logger.info("All validation tests passed successfully")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED. Issues need to be addressed before deployment.")
        logger.warning(f"Validation failed: {total_tests - passed_tests} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
