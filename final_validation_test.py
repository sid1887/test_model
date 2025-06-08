"""
Final Validation Test for Cumpair System Improvements
Tests all enhancements and validates the system is working correctly
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, List
import time

class FinalValidationTester:
    """Comprehensive validation test for enhanced Cumpair system"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        self.test_images_dir = Path("product_images_test")
        
    def log_test(self, test_name: str, result: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results[test_name] = {
            'passed': result,
            'details': details,
            'timestamp': time.time()
        }
    
    def test_server_health(self) -> bool:
        """Test if server is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                self.log_test("Server Health Check", True, "Server is running")
            else:
                self.log_test("Server Health Check", False, f"Status: {response.status_code}")
            return is_healthy
        except Exception as e:
            self.log_test("Server Health Check", False, f"Server not responding: {e}")
            return False
    
    def test_text_search_deduplication(self) -> bool:
        """Test text search for duplicate results"""
        try:
            # Test common queries that might return duplicates
            test_queries = [
                "wall clock",
                "painting", 
                "soap tray",
                "fan",
                "utility knife"
            ]
            
            all_passed = True
            for query in test_queries:
                response = requests.post(
                    f"{self.base_url}/api/v1/search-by-text",
                    json={"query": query, "limit": 5},
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    
                    # Check for duplicates by product_id
                    product_ids = [r.get("product_id") for r in results if r.get("product_id")]
                    unique_ids = set(product_ids)
                    
                    if len(product_ids) != len(unique_ids):
                        duplicates_found = len(product_ids) - len(unique_ids)
                        self.log_test(f"Text Search Dedup: '{query}'", False, 
                                    f"Found {duplicates_found} duplicate results")
                        all_passed = False
                    else:
                        self.log_test(f"Text Search Dedup: '{query}'", True, 
                                    f"No duplicates in {len(results)} results")
                else:
                    self.log_test(f"Text Search Dedup: '{query}'", False, 
                                f"API error: {response.status_code}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Text Search Deduplication", False, f"Test failed: {e}")
            return False
    
    def test_image_search_deduplication(self) -> bool:
        """Test image search for duplicate results"""
        try:
            # Get test images
            test_images = list(self.test_images_dir.glob("*.jpg"))[:3]
            
            if not test_images:
                self.log_test("Image Search Deduplication", False, "No test images found")
                return False
            
            all_passed = True
            for image_path in test_images:
                with open(image_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{self.base_url}/api/v1/search-by-image",
                        files=files,
                        data={'limit': 5},
                        timeout=15
                    )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    
                    # Check for duplicates by product_id
                    product_ids = [r.get("product_id") for r in results if r.get("product_id")]
                    unique_ids = set(product_ids)
                    
                    if len(product_ids) != len(unique_ids):
                        duplicates_found = len(product_ids) - len(unique_ids)
                        self.log_test(f"Image Search Dedup: {image_path.name}", False, 
                                    f"Found {duplicates_found} duplicate results")
                        all_passed = False
                    else:
                        self.log_test(f"Image Search Dedup: {image_path.name}", True, 
                                    f"No duplicates in {len(results)} results")
                else:
                    self.log_test(f"Image Search Dedup: {image_path.name}", False, 
                                f"API error: {response.status_code}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Image Search Deduplication", False, f"Test failed: {e}")
            return False
    
    def test_metadata_completeness(self) -> bool:
        """Test that products have complete metadata"""
        try:
            # Test text search to get product metadata
            response = requests.post(
                f"{self.base_url}/api/v1/search-by-text",
                json={"query": "product", "limit": 10},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Metadata Completeness", False, f"API error: {response.status_code}")
                return False
            
            results = response.json().get("results", [])
            
            if not results:
                self.log_test("Metadata Completeness", False, "No products returned")
                return False
            
            incomplete_count = 0
            for result in results:
                missing_fields = []
                
                if not result.get("brand"):
                    missing_fields.append("brand")
                if not result.get("category"):
                    missing_fields.append("category")
                if not result.get("specifications"):
                    missing_fields.append("specifications")
                
                if missing_fields:
                    incomplete_count += 1
                    print(f"   Product {result.get('product_id')}: Missing {', '.join(missing_fields)}")
            
            if incomplete_count == 0:
                self.log_test("Metadata Completeness", True, 
                            f"All {len(results)} products have complete metadata")
                return True
            else:
                self.log_test("Metadata Completeness", False, 
                            f"{incomplete_count}/{len(results)} products missing metadata")
                return False
                
        except Exception as e:
            self.log_test("Metadata Completeness", False, f"Test failed: {e}")
            return False
    
    def test_search_performance(self) -> bool:
        """Test search response times"""
        try:
            # Text search performance
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/search-by-text",
                json={"query": "wall clock", "limit": 5},
                timeout=10
            )
            text_search_time = time.time() - start_time
            
            text_passed = response.status_code == 200 and text_search_time < 5.0
            self.log_test("Text Search Performance", text_passed, 
                        f"Response time: {text_search_time:.2f}s")
            
            # Image search performance (if we have test images)
            test_images = list(self.test_images_dir.glob("*.jpg"))
            if test_images:
                start_time = time.time()
                with open(test_images[0], 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{self.base_url}/api/v1/search-by-image",
                        files=files,
                        data={'limit': 5},
                        timeout=15
                    )
                image_search_time = time.time() - start_time
                
                image_passed = response.status_code == 200 and image_search_time < 10.0
                self.log_test("Image Search Performance", image_passed, 
                            f"Response time: {image_search_time:.2f}s")
                
                return text_passed and image_passed
            
            return text_passed
            
        except Exception as e:
            self.log_test("Search Performance", False, f"Test failed: {e}")
            return False
    
    def test_clip_index_integrity(self) -> bool:
        """Test CLIP index integrity and size"""
        try:
            # Test multiple searches to ensure index is stable
            queries = ["clock", "painting", "tray", "fan", "knife"]
            
            for query in queries:
                response = requests.post(
                    f"{self.base_url}/api/v1/search-by-text",
                    json={"query": query, "limit": 3},
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.log_test("CLIP Index Integrity", False, 
                                f"Failed query '{query}': {response.status_code}")
                    return False
                
                results = response.json().get("results", [])
                
                # Check that results have required fields
                for result in results:
                    required_fields = ['product_id', 'similarity_score', 'name']
                    missing = [f for f in required_fields if f not in result]
                    if missing:
                        self.log_test("CLIP Index Integrity", False, 
                                    f"Missing fields in result: {missing}")
                        return False
            
            self.log_test("CLIP Index Integrity", True, 
                        f"All {len(queries)} queries successful with valid results")
            return True
            
        except Exception as e:
            self.log_test("CLIP Index Integrity", False, f"Test failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test API error handling"""
        try:
            # Test invalid text search
            response = requests.post(
                f"{self.base_url}/api/v1/search-by-text",
                json={"invalid": "data"},
                timeout=5
            )
            
            # Should return proper error response
            error_handled = response.status_code in [400, 422]
            self.log_test("Error Handling - Invalid Text Search", error_handled, 
                        f"Status: {response.status_code}")
            
            # Test empty image upload
            response = requests.post(
                f"{self.base_url}/api/v1/search-by-image",
                files={},
                timeout=5
            )
            
            # Should return proper error response
            error_handled2 = response.status_code in [400, 422]
            self.log_test("Error Handling - Empty Image Upload", error_handled2, 
                        f"Status: {response.status_code}")
            
            return error_handled and error_handled2
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Test failed: {e}")
            return False
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['passed'])
        
        report = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_details': self.test_results,
            'overall_status': 'PASS' if passed_tests == total_tests else 'FAIL'
        }
        
        print("\n" + "="*80)
        print("🎯 FINAL VALIDATION REPORT")
        print("="*80)
        print(f"📊 Tests: {passed_tests}/{total_tests} passed ({report['success_rate']:.1f}%)")
        print(f"🎉 Overall Status: {report['overall_status']}")
        
        if report['failed_tests'] > 0:
            print(f"\n❌ Failed Tests ({report['failed_tests']}):")
            for test_name, result in self.test_results.items():
                if not result['passed']:
                    print(f"   • {test_name}: {result['details']}")
        
        return report

def main():
    """Run comprehensive validation tests"""
    print("🚀 Starting Final Validation Test for Cumpair System")
    print("="*60)
    
    tester = FinalValidationTester()
    
    # Check server health first
    if not tester.test_server_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    print("✅ Server is running - Starting validation tests...\n")
    
    # Run all validation tests
    tester.test_text_search_deduplication()
    tester.test_image_search_deduplication()
    tester.test_metadata_completeness()
    tester.test_search_performance()
    tester.test_clip_index_integrity()
    tester.test_error_handling()
    
    # Generate final report
    report = tester.generate_report()
    
    # Save report
    with open('final_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to 'final_validation_report.json'")
    
    if report['overall_status'] == 'PASS':
        print("🎉 All tests passed! System is ready for production.")
    else:
        print("⚠️ Some tests failed. Please address the issues before deployment.")

if __name__ == "__main__":
    main()
