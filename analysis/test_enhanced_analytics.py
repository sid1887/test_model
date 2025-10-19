"""
Enhanced Data Pipelines & Pricing Analytics Test Suite
Tests the new value scoring, feature normalization, price forecasting, and sentiment analysis
"""

import asyncio
import aiohttp
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsTestSuite:
    """Comprehensive test suite for enhanced analytics features"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            'value_scoring': [],
            'price_forecasting': [],
            'sentiment_analysis': [],
            'feature_engineering': [],
            'analytics_summary': []
        }
    
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        logger.info("🚀 Analytics Test Suite initialized")
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        logger.info("✅ Test suite cleanup completed")
    
    async def test_value_scoring(self):
        """Test enhanced value scoring with different weight configurations"""
        logger.info("🧮 Testing Enhanced Value Scoring...")
        
        # Test different scoring configurations
        test_configs = [
            {
                "name": "Balanced Scoring",
                "payload": {
                    "weight_preset": "balanced",
                    "normalization_method": "min_max"
                }
            },
            {
                "name": "Price-Focused Scoring", 
                "payload": {
                    "weight_preset": "price_focused",
                    "normalization_method": "z_score"
                }
            },
            {
                "name": "Quality-Focused Scoring",
                "payload": {
                    "weight_preset": "quality_focused", 
                    "normalization_method": "robust"
                }
            },
            {
                "name": "Custom Weights",
                "payload": {
                    "weights": {
                        "price": 0.5,
                        "rating": 0.3,
                        "review_count": 0.15,
                        "availability": 0.05
                    },
                    "normalization_method": "min_max"
                }
            }
        ]
        
        for config in test_configs:
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/analytics/value-scoring",
                    json=config["payload"]
                ) as response:
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            'config_name': config["name"],
                            'status': 'success',
                            'products_scored': len(data.get('products', [])),
                            'processing_time_ms': processing_time,
                            'api_processing_time_ms': data.get('processing_time_ms', 0),
                            'metadata': data.get('metadata', {}),
                            'sample_scores': [
                                {
                                    'product_name': p.get('name', 'Unknown'),
                                    'value_score': p.get('value_score', 0),
                                    'price': p.get('price', 0)
                                }
                                for p in data.get('products', [])[:3]  # Top 3 products
                            ]
                        }
                        
                        logger.info(f"✅ {config['name']}: {result['products_scored']} products scored in {processing_time:.2f}ms")
                        
                    else:
                        error_text = await response.text()
                        result = {
                            'config_name': config["name"],
                            'status': 'failed',
                            'error': error_text,
                            'processing_time_ms': processing_time
                        }
                        logger.error(f"❌ {config['name']} failed: {error_text}")
                
                self.test_results['value_scoring'].append(result)
                
            except Exception as e:
                logger.error(f"❌ {config['name']} test failed: {e}")
                self.test_results['value_scoring'].append({
                    'config_name': config["name"],
                    'status': 'error',
                    'error': str(e)
                })
    
    async def test_price_forecasting(self):
        """Test price forecasting with Prophet"""
        logger.info("📈 Testing Price Forecasting...")
        
        # Test with different forecast configurations
        test_configs = [
            {
                "name": "Short-term Forecast (7 days)",
                "payload": {
                    "product_id": 1,
                    "forecast_days": 7,
                    "confidence_interval": 0.8
                }
            },
            {
                "name": "Medium-term Forecast (30 days)",
                "payload": {
                    "product_id": 1,
                    "forecast_days": 30,
                    "confidence_interval": 0.9
                }
            },
            {
                "name": "Long-term Forecast (60 days)",
                "payload": {
                    "product_id": 1,
                    "forecast_days": 60,
                    "confidence_interval": 0.95
                }
            }
        ]
        
        for config in test_configs:
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/analytics/price-forecast",
                    json=config["payload"]
                ) as response:
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        forecast_data = data.get('forecast_data', {})
                        validation_metrics = data.get('validation_metrics', {})
                        
                        result = {
                            'config_name': config["name"],
                            'status': 'success',
                            'product_id': forecast_data.get('product_id'),
                            'forecast_horizon_days': forecast_data.get('forecast_horizon_days'),
                            'historical_data_points': forecast_data.get('historical_data_points'),
                            'trend_direction': forecast_data.get('trend_analysis', {}).get('direction'),
                            'processing_time_ms': processing_time,
                            'api_processing_time_ms': data.get('processing_time_ms', 0),
                            'validation_metrics': validation_metrics.get('metrics', {}),
                            'accuracy_assessment': validation_metrics.get('accuracy_assessment'),
                            'price_insights': forecast_data.get('price_insights', {})
                        }
                        
                        logger.info(f"✅ {config['name']}: Forecast generated for product {result['product_id']}")
                        
                    else:
                        error_text = await response.text()
                        result = {
                            'config_name': config["name"],
                            'status': 'failed',
                            'error': error_text,
                            'processing_time_ms': processing_time
                        }
                        logger.error(f"❌ {config['name']} failed: {error_text}")
                
                self.test_results['price_forecasting'].append(result)
                
            except Exception as e:
                logger.error(f"❌ {config['name']} test failed: {e}")
                self.test_results['price_forecasting'].append({
                    'config_name': config["name"],
                    'status': 'error',
                    'error': str(e)
                })
    
    async def test_sentiment_analysis(self):
        """Test sentiment analysis with different NLP models"""
        logger.info("😊 Testing Sentiment Analysis...")
        
        # Test different sentiment models
        test_configs = [
            {
                "name": "VADER Sentiment Model",
                "payload": {
                    "product_id": 1,
                    "model": "vader",
                    "include_topics": True
                }
            },
            {
                "name": "TextBlob Sentiment Model",
                "payload": {
                    "product_id": 1,
                    "model": "textblob",
                    "include_topics": True
                }
            },
            {
                "name": "HuggingFace Sentiment Model",
                "payload": {
                    "product_id": 1,
                    "model": "huggingface",
                    "include_topics": False
                }
            },
            {
                "name": "Ensemble Sentiment Model",
                "payload": {
                    "product_id": 1,
                    "model": "ensemble",
                    "include_topics": True
                }
            }
        ]
        
        for config in test_configs:
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/analytics/sentiment-analysis",
                    json=config["payload"]
                ) as response:
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        sentiment_data = data.get('sentiment_data', {})
                        
                        result = {
                            'config_name': config["name"],
                            'status': 'success',
                            'sentiment_score': sentiment_data.get('sentiment_score'),
                            'sentiment_label': sentiment_data.get('sentiment_label'),
                            'confidence': sentiment_data.get('confidence'),
                            'total_reviews': sentiment_data.get('total_reviews'),
                            'model_used': sentiment_data.get('model'),
                            'processing_time_ms': processing_time,
                            'api_processing_time_ms': data.get('processing_time_ms', 0),
                            'topics': sentiment_data.get('topics', {}).get('top_topics', []) if sentiment_data.get('topics') else []
                        }
                        
                        logger.info(f"✅ {config['name']}: Sentiment {result['sentiment_label']} (score: {result['sentiment_score']})")
                        
                    else:
                        error_text = await response.text()
                        result = {
                            'config_name': config["name"],
                            'status': 'failed',
                            'error': error_text,
                            'processing_time_ms': processing_time
                        }
                        logger.error(f"❌ {config['name']} failed: {error_text}")
                
                self.test_results['sentiment_analysis'].append(result)
                
            except Exception as e:
                logger.error(f"❌ {config['name']} test failed: {e}")
                self.test_results['sentiment_analysis'].append({
                    'config_name': config["name"],
                    'status': 'error',
                    'error': str(e)
                })
    
    async def test_feature_engineering(self):
        """Test categorical feature engineering"""
        logger.info("🔧 Testing Feature Engineering...")
        
        test_configs = [
            {
                "name": "One-Hot Encoding",
                "payload": {
                    "categorical_features": ["brand", "category"],
                    "encoding_method": "onehot"
                }
            },
            {
                "name": "Label Encoding",
                "payload": {
                    "categorical_features": ["brand", "category", "source_name"],
                    "encoding_method": "label"
                }
            }
        ]
        
        for config in test_configs:
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/analytics/feature-engineering",
                    json=config["payload"]
                ) as response:
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            'config_name': config["name"],
                            'status': 'success',
                            'total_products': data.get('total_products'),
                            'features_engineered': data.get('metadata', {}).get('features_engineered', []),
                            'encoding_method': data.get('metadata', {}).get('encoding_method'),
                            'processing_time_ms': processing_time
                        }
                        
                        logger.info(f"✅ {config['name']}: {len(result['features_engineered'])} features engineered")
                        
                    else:
                        error_text = await response.text()
                        result = {
                            'config_name': config["name"],
                            'status': 'failed',
                            'error': error_text,
                            'processing_time_ms': processing_time
                        }
                        logger.error(f"❌ {config['name']} failed: {error_text}")
                
                self.test_results['feature_engineering'].append(result)
                
            except Exception as e:
                logger.error(f"❌ {config['name']} test failed: {e}")
                self.test_results['feature_engineering'].append({
                    'config_name': config["name"],
                    'status': 'error',
                    'error': str(e)
                })
    
    async def test_analytics_summary(self):
        """Test comprehensive analytics summary"""
        logger.info("📊 Testing Analytics Summary...")
        
        try:
            start_time = time.time()
            
            async with self.session.get(
                f"{self.base_url}/api/v1/analytics/products/1/analytics-summary"
            ) as response:
                
                processing_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = {
                        'status': 'success',
                        'product_id': data.get('product_id'),
                        'product_name': data.get('product_name'),
                        'has_price_stats': bool(data.get('price_statistics')),
                        'has_forecast': data.get('latest_forecast', {}).get('has_forecast', False),
                        'has_sentiment': data.get('latest_sentiment', {}).get('has_sentiment', False),
                        'processing_time_ms': processing_time,
                        'forecast_info': data.get('latest_forecast', {}),
                        'sentiment_info': data.get('latest_sentiment', {}),
                        'price_stats': data.get('price_statistics', {})
                    }
                    
                    logger.info(f"✅ Analytics Summary: Product {result['product_id']} - Forecast: {result['has_forecast']}, Sentiment: {result['has_sentiment']}")
                    
                else:
                    error_text = await response.text()
                    result = {
                        'status': 'failed',
                        'error': error_text,
                        'processing_time_ms': processing_time
                    }
                    logger.error(f"❌ Analytics Summary failed: {error_text}")
            
            self.test_results['analytics_summary'].append(result)
            
        except Exception as e:
            logger.error(f"❌ Analytics Summary test failed: {e}")
            self.test_results['analytics_summary'].append({
                'status': 'error',
                'error': str(e)
            })
    
    async def run_all_tests(self):
        """Run all analytics tests"""
        await self.setup()
        
        try:
            logger.info("🚀 Starting Enhanced Analytics Test Suite...")
            
            # Run all test categories
            await self.test_value_scoring()
            await self.test_price_forecasting()
            await self.test_sentiment_analysis()
            await self.test_feature_engineering()
            await self.test_analytics_summary()
            
            # Generate summary
            self.generate_test_summary()
            
        finally:
            await self.cleanup()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        logger.info("📋 Generating Test Summary...")
        
        summary = {
            'test_timestamp': datetime.now().isoformat(),
            'test_categories': {},
            'overall_stats': {
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'error_tests': 0
            }
        }
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            category_stats = {
                'total': len(tests),
                'successful': len([t for t in tests if t.get('status') == 'success']),
                'failed': len([t for t in tests if t.get('status') == 'failed']),
                'errors': len([t for t in tests if t.get('status') == 'error']),
                'avg_processing_time_ms': np.mean([t.get('processing_time_ms', 0) for t in tests if t.get('processing_time_ms')]) if tests else 0,
                'tests': tests
            }
            
            summary['test_categories'][category] = category_stats
            summary['overall_stats']['total_tests'] += category_stats['total']
            summary['overall_stats']['successful_tests'] += category_stats['successful']
            summary['overall_stats']['failed_tests'] += category_stats['failed']
            summary['overall_stats']['error_tests'] += category_stats['errors']
        
        # Calculate success rate
        total = summary['overall_stats']['total_tests']
        successful = summary['overall_stats']['successful_tests']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        summary['overall_stats']['success_rate_percent'] = round(success_rate, 2)
        
        # Save results
        filename = f"analytics_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        logger.info("=" * 70)
        logger.info("📊 ENHANCED ANALYTICS TEST RESULTS SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Overall Success Rate: {success_rate:.1f}% ({successful}/{total})")
        logger.info("")
        
        for category, stats in summary['test_categories'].items():
            category_success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status_icon = "✅" if category_success_rate >= 80 else "⚠️" if category_success_rate >= 50 else "❌"
            
            logger.info(f"{status_icon} {category.replace('_', ' ').title()}: {category_success_rate:.1f}% ({stats['successful']}/{stats['total']})")
            logger.info(f"   Avg Processing Time: {stats['avg_processing_time_ms']:.2f}ms")
        
        logger.info("")
        logger.info(f"📄 Detailed results saved to: {filename}")
        logger.info("=" * 70)
        
        return summary

async def main():
    """Main test execution"""
    test_suite = AnalyticsTestSuite()
    summary = await test_suite.run_all_tests()
    return summary

if __name__ == "__main__":
    asyncio.run(main())
