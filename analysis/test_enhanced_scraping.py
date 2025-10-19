"""
Enhanced Scraping System Integration Test
Tests the complete adaptive scraping pipeline with proxy management and stealth browsing
"""

import asyncio
import time
import json
from typing import List, Dict
import logging

from app.services.adaptive_scraper import AdaptiveScrapingEngine, ScrapingResult
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedScrapingTest:
    """Comprehensive test suite for the enhanced scraping system"""
    
    def __init__(self):
        self.scraper = AdaptiveScrapingEngine()
        self.test_results = []
        
        # Test URLs for different complexity levels
        self.test_urls = [
            {
                'url': 'https://httpbin.org/html',
                'description': 'Simple HTTP test page',
                'expected_strategy': 'simple_http'
            },
            {
                'url': 'https://quotes.toscrape.com/',
                'description': 'JavaScript-free quotes page',
                'expected_strategy': 'simple_http'
            },
            {
                'url': 'https://quotes.toscrape.com/js/',
                'description': 'JavaScript-required quotes page',
                'expected_strategy': 'stealth_browser'
            },
            {
                'url': 'https://httpbin.org/user-agent',
                'description': 'User agent detection test',
                'expected_strategy': 'simple_http'
            }
        ]
    
    async def run_comprehensive_test(self) -> Dict:
        """Run the complete test suite"""
        logger.info("🚀 Starting Enhanced Scraping System Test")
        logger.info("=" * 60)
        
        start_time = time.time()
        results = {
            'timestamp': time.time(),
            'test_duration': 0,
            'total_tests': len(self.test_urls),
            'passed_tests': 0,
            'failed_tests': 0,
            'strategy_performance': {},
            'detailed_results': []
        }
        
        # Test each URL
        for i, test_case in enumerate(self.test_urls, 1):
            logger.info(f"\n🧪 Test {i}/{len(self.test_urls)}: {test_case['description']}")
            logger.info(f"   URL: {test_case['url']}")
            
            try:
                # Execute scraping
                scraping_result = await self.scraper.scrape_product(test_case['url'])
                
                # Evaluate result
                test_result = self._evaluate_test_result(test_case, scraping_result)
                results['detailed_results'].append(test_result)
                
                if test_result['passed']:
                    results['passed_tests'] += 1
                    logger.info(f"   ✅ PASSED - {test_result['summary']}")
                else:
                    results['failed_tests'] += 1
                    logger.info(f"   ❌ FAILED - {test_result['summary']}")
                
                # Track strategy performance
                strategy = scraping_result.method_used
                if strategy:
                    if strategy not in results['strategy_performance']:
                        results['strategy_performance'][strategy] = {
                            'attempts': 0, 'successes': 0, 'avg_response_time': 0
                        }
                    
                    results['strategy_performance'][strategy]['attempts'] += 1
                    if scraping_result.success:
                        results['strategy_performance'][strategy]['successes'] += 1
                    
                    # Update average response time
                    current_avg = results['strategy_performance'][strategy]['avg_response_time']
                    current_attempts = results['strategy_performance'][strategy]['attempts']
                    new_avg = ((current_avg * (current_attempts - 1)) + scraping_result.response_time) / current_attempts
                    results['strategy_performance'][strategy]['avg_response_time'] = new_avg
                
                # Small delay between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ EXCEPTION - {str(e)}")
                results['failed_tests'] += 1
                results['detailed_results'].append({
                    'test_case': test_case,
                    'passed': False,
                    'summary': f"Exception: {str(e)}",
                    'scraping_result': None
                })
        
        # Test proxy management
        await self._test_proxy_management(results)
        
        # Test strategy adaptation
        await self._test_strategy_adaptation(results)
        
        # Calculate final metrics
        results['test_duration'] = time.time() - start_time
        results['success_rate'] = results['passed_tests'] / results['total_tests'] if results['total_tests'] > 0 else 0
        
        # Calculate strategy success rates
        for strategy, stats in results['strategy_performance'].items():
            stats['success_rate'] = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0
        
        await self._generate_test_report(results)
        
        return results
    
    def _evaluate_test_result(self, test_case: Dict, scraping_result: ScrapingResult) -> Dict:
        """Evaluate if a test case passed or failed"""
        test_result = {
            'test_case': test_case,
            'scraping_result': {
                'success': scraping_result.success,
                'method_used': scraping_result.method_used,
                'proxy_used': scraping_result.proxy_used,
                'captcha_solved': scraping_result.captcha_solved,
                'response_time': scraping_result.response_time,
                'retry_count': scraping_result.retry_count,
                'error': scraping_result.error,
                'data_extracted': bool(scraping_result.data) if scraping_result.data else False
            },
            'passed': False,
            'summary': ''
        }
        
        if scraping_result.success:
            test_result['passed'] = True
            test_result['summary'] = f"Success with {scraping_result.method_used} in {scraping_result.response_time:.2f}s"
            
            # Additional validation
            if scraping_result.data:
                test_result['summary'] += f" (Data: {len(scraping_result.data)} fields)"
                
            if scraping_result.proxy_used:
                test_result['summary'] += f" (Proxy: ✅)"
                
            if scraping_result.captcha_solved:
                test_result['summary'] += f" (CAPTCHA: ✅)"
                
        else:
            test_result['summary'] = f"Failed: {scraping_result.error}"
            
            # Partial credit for trying advanced strategies
            if scraping_result.method_used in ['stealth_browser', 'full_browser']:
                test_result['summary'] += " (Advanced strategy attempted)"
        
        return test_result
    
    async def _test_proxy_management(self, results: Dict):
        """Test proxy management functionality"""
        logger.info("\n🔍 Testing Proxy Management...")
        
        try:
            # Test proxy retrieval
            proxy = await self.scraper.proxy_manager.get_proxy()
            if proxy:
                logger.info(f"   ✅ Proxy retrieved: {proxy.get('url', 'Unknown')}")
                results['proxy_management'] = {'status': 'working', 'proxy_available': True}
            else:
                logger.info("   ⚠️ No proxies available (normal for first run)")
                results['proxy_management'] = {'status': 'no_proxies', 'proxy_available': False}
                
        except Exception as e:
            logger.error(f"   ❌ Proxy management error: {e}")
            results['proxy_management'] = {'status': 'error', 'error': str(e)}
    
    async def _test_strategy_adaptation(self, results: Dict):
        """Test strategy adaptation and learning"""
        logger.info("\n🧠 Testing Strategy Adaptation...")
        
        try:
            # Get current strategy statistics
            stats = await self.scraper.get_strategy_stats()
            
            if stats:
                logger.info(f"   ✅ Strategy statistics collected: {len(stats)} domain-strategy combinations")
                results['strategy_adaptation'] = {'status': 'working', 'stats_count': len(stats)}
                
                # Show top performing strategies
                sorted_stats = sorted(
                    stats.items(), 
                    key=lambda x: x[1]['success_rate'], 
                    reverse=True
                )
                
                logger.info("   📊 Top performing strategies:")
                for i, (key, stat) in enumerate(sorted_stats[:3]):
                    domain, strategy = key.split(':')
                    logger.info(f"      {i+1}. {strategy} on {domain}: {stat['success_rate']:.2%} success")
                    
            else:
                logger.info("   ⚠️ No strategy statistics available yet")
                results['strategy_adaptation'] = {'status': 'no_data', 'stats_count': 0}
                
        except Exception as e:
            logger.error(f"   ❌ Strategy adaptation error: {e}")
            results['strategy_adaptation'] = {'status': 'error', 'error': str(e)}
    
    async def _generate_test_report(self, results: Dict):
        """Generate a comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 ENHANCED SCRAPING SYSTEM TEST REPORT")
        logger.info("=" * 60)
        
        # Overall results
        logger.info(f"⏱️  Test Duration: {results['test_duration']:.2f} seconds")
        logger.info(f"📊 Total Tests: {results['total_tests']}")
        logger.info(f"✅ Passed: {results['passed_tests']}")
        logger.info(f"❌ Failed: {results['failed_tests']}")
        logger.info(f"📈 Success Rate: {results['success_rate']:.1%}")
        
        # Strategy performance
        if results['strategy_performance']:
            logger.info("\n🎯 STRATEGY PERFORMANCE:")
            for strategy, stats in results['strategy_performance'].items():
                logger.info(f"   {strategy}:")
                logger.info(f"      Success Rate: {stats['success_rate']:.1%}")
                logger.info(f"      Avg Response Time: {stats['avg_response_time']:.2f}s")
                logger.info(f"      Attempts: {stats['attempts']}")
        
        # Component status
        if 'proxy_management' in results:
            proxy_status = results['proxy_management']['status']
            logger.info(f"\n🌐 Proxy Management: {proxy_status}")
            
        if 'strategy_adaptation' in results:
            adaptation_status = results['strategy_adaptation']['status']
            logger.info(f"🧠 Strategy Adaptation: {adaptation_status}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        
        if results['success_rate'] < 0.5:
            logger.info("   • Consider checking proxy service connectivity")
            logger.info("   • Verify test URLs are accessible")
            
        if results.get('proxy_management', {}).get('status') == 'no_proxies':
            logger.info("   • Start proxy service: .\\start-proxy-service.ps1")
            logger.info("   • Wait for proxy discovery (may take 2-3 minutes)")
            
        if results['success_rate'] >= 0.8:
            logger.info("   • ✅ System is performing excellently!")
            logger.info("   • Ready for production scraping tasks")
        
        # Save detailed results
        report_file = f"enhanced_scraping_test_results_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n📁 Detailed results saved to: {report_file}")
        logger.info("=" * 60)

async def main():
    """Run the enhanced scraping system test"""
    test_suite = EnhancedScrapingTest()
    
    try:
        results = await test_suite.run_comprehensive_test()
        
        # Cleanup
        await test_suite.scraper.cleanup()
        
        # Exit with appropriate code
        if results['success_rate'] >= 0.5:
            exit(0)  # Success
        else:
            exit(1)  # Failure
            
    except Exception as e:
        logger.error(f"❌ Test suite failed with exception: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
