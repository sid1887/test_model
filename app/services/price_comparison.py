"""
Enhanced Price Comparison Service for Cumpair
Integrates web scraping, AI-powered product matching, and intelligent price analysis
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.models.price_comparison import PriceComparison, PriceHistory
from app.services.scraping import scraper_client, scraping_engine
from app.services.ai_models import get_clip_model
from app.core.monitoring import logger
import numpy as np

class CumpairPriceEngine:
    """Enhanced price comparison engine with AI-powered matching"""
    
    def __init__(self):
        self.scraper_client = scraper_client
        self.scraping_engine = scraping_engine
        self.clip_model = None
        self.similarity_threshold = 0.85
        
        # E-commerce site configurations for Cumpair
        self.ecommerce_sites = {
            'amazon.com': {
                'selectors': {
                    'title': ['#productTitle', '.product-title'],
                    'price': ['.a-price-whole', '.a-price .a-offscreen'],
                    'rating': ['.a-icon-alt', '.cr-widget-FocalReviews'],
                    'availability': ['#availability span', '.a-color-success']
                },
                'rate_limit': 2.0  # seconds between requests
            },
            'ebay.com': {
                'selectors': {
                    'title': ['#x-title-label-lbl', '.it-ttl'],
                    'price': ['.u-flL.condText', '.u-flL.u-bold'],
                    'rating': ['.ebay-review-star-rating', '.reviews'],
                    'availability': ['.u-flL.vi-acc-del-range']
                },
                'rate_limit': 1.5
            },
            'walmart.com': {
                'selectors': {
                    'title': ['[data-automation-id="product-title"]', 'h1'],
                    'price': ['[data-automation-id="product-price"]', '.price-current'],
                    'rating': ['.average-rating', '.star-rating'],
                    'availability': ['[data-automation-id="fulfillment-summary"]']
                },
                'rate_limit': 2.5
            }
        }
    
    async def initialize(self):
        """Initialize the price comparison engine"""
        try:
            # Initialize scraper client
            await self.scraper_client.initialize()
            
            # Load CLIP model for product matching
            self.clip_model = await get_clip_model()
            
            logger.info("✅ Cumpair Price Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cumpair Price Engine: {e}")
            return False
    
    async def find_product_prices(self, product_query: str, max_results: int = 10) -> Dict:
        """
        Find prices for a product across multiple e-commerce sites
        
        Args:
            product_query: Product search query or description
            max_results: Maximum number of results per site
            
        Returns:
            Comprehensive price comparison results
        """
        logger.info(f"🔍 Starting price search for: {product_query}")
        
        results = {
            'query': product_query,
            'timestamp': datetime.utcnow().isoformat(),
            'total_results': 0,
            'price_range': {'min': float('inf'), 'max': 0},
            'sites': {},
            'ai_insights': {},
            'recommendations': []
        }
        
        # Generate search URLs for different e-commerce sites
        search_urls = self._generate_search_urls(product_query)
        
        # Scrape prices concurrently with rate limiting
        scraping_tasks = []
        for site, urls in search_urls.items():
            for url in urls[:max_results]:
                task = self._scrape_with_rate_limit(site, url, product_query)
                scraping_tasks.append(task)
        
        # Execute scraping tasks
        scraping_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        
        # Process results
        for result in scraping_results:
            if isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")
                continue
            
            if result and result.get('status') == 'success':
                site = result.get('site')
                if site not in results['sites']:
                    results['sites'][site] = []
                
                product_data = result.get('data', {})
                if product_data.get('price', 0) > 0:
                    results['sites'][site].append(product_data)
                    results['total_results'] += 1
                    
                    # Update price range
                    price = product_data['price']
                    results['price_range']['min'] = min(results['price_range']['min'], price)
                    results['price_range']['max'] = max(results['price_range']['max'], price)
        
        # AI-powered product matching and insights
        if results['total_results'] > 0:
            results['ai_insights'] = await self._generate_ai_insights(results, product_query)
            results['recommendations'] = self._generate_recommendations(results)
        
        # Fix infinite min price
        if results['price_range']['min'] == float('inf'):
            results['price_range']['min'] = 0
        
        logger.info(f"✅ Price search completed: {results['total_results']} results found")
        return results
    
    async def compare_product_with_ai(self, product_id: int, search_query: str = None) -> Dict:
        """
        AI-powered product comparison using existing product data
        
        Args:
            product_id: ID of the product to compare
            search_query: Optional custom search query
            
        Returns:
            Detailed comparison with AI insights
        """
        try:
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {'error': 'Product not found', 'product_id': product_id}
            
            # Use product name/title as search query if not provided
            query = search_query or product.name or "generic product"
            
            # Find prices using the enhanced search
            price_results = await self.find_product_prices(query)
            
            # Enhanced AI comparison
            ai_comparison = await self._ai_enhanced_comparison(product, price_results)
            
            # Store comparison results
            comparison_record = PriceComparison(
                product_id=product_id,
                search_query=query,
                results_json=json.dumps(price_results),
                ai_insights_json=json.dumps(ai_comparison),
                total_results=price_results.get('total_results', 0),
                price_range_min=price_results.get('price_range', {}).get('min', 0),
                price_range_max=price_results.get('price_range', {}).get('max', 0)
            )
            
            db.add(comparison_record)
            db.commit()
            
            return {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description
                },
                'price_comparison': price_results,
                'ai_insights': ai_comparison,
                'comparison_id': comparison_record.id
            }
            
        except Exception as e:
            logger.error(f"❌ AI product comparison failed: {e}")
            return {'error': str(e), 'product_id': product_id}
        finally:
            db.close()
    
    def _generate_search_urls(self, product_query: str) -> Dict[str, List[str]]:
        """Generate search URLs for different e-commerce sites"""
        search_urls = {}
        
        # Clean and encode the product query
        clean_query = re.sub(r'[^\w\s-]', '', product_query).strip()
        encoded_query = clean_query.replace(' ', '+')
        
        # Amazon search URLs
        search_urls['amazon.com'] = [
            f"https://www.amazon.com/s?k={encoded_query}",
            f"https://www.amazon.com/s?k={encoded_query}&ref=sr_pg_2"
        ]
        
        # eBay search URLs
        search_urls['ebay.com'] = [
            f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}",
            f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}&_pgn=2"
        ]
        
        # Walmart search URLs
        search_urls['walmart.com'] = [
            f"https://www.walmart.com/search/?query={encoded_query}",
            f"https://www.walmart.com/search/?page=2&query={encoded_query}"
        ]
        
        return search_urls
    
    async def _scrape_with_rate_limit(self, site: str, url: str, product_query: str) -> Dict:
        """Scrape a URL with site-specific rate limiting"""
        try:
            # Apply rate limiting
            site_config = self.ecommerce_sites.get(site, {})
            rate_limit = site_config.get('rate_limit', 1.0)
            await asyncio.sleep(rate_limit)
            
            # Try dedicated scraper first
            scraper_result = await self.scraper_client.scrape_url(url, {
                'product_query': product_query,
                'site_config': site_config
            })
            
            if scraper_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'site': site,
                    'url': url,
                    'data': scraper_result.get('data', {}),
                    'method': 'dedicated_scraper'
                }
            
            # Fallback to adaptive scraping engine
            adaptive_result = await self.scraping_engine.scrape_product(url, product_query)
            
            if adaptive_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'site': site,
                    'url': url,
                    'data': adaptive_result.get('data', {}),
                    'method': 'adaptive_engine'
                }
            
            return {
                'status': 'failed',
                'site': site,
                'url': url,
                'error': 'Both scraping methods failed'
            }
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {url}: {e}")
            return {
                'status': 'failed',
                'site': site,
                'url': url,
                'error': str(e)
            }
    
    async def _generate_ai_insights(self, results: Dict, original_query: str) -> Dict:
        """Generate AI-powered insights from price comparison results"""
        insights = {
            'product_matching_score': 0.0,
            'price_analysis': {},
            'market_insights': {},
            'quality_indicators': {},
            'recommendations': []
        }
        
        try:
            all_products = []
            for site_products in results['sites'].values():
                all_products.extend(site_products)
            
            if not all_products:
                return insights
            
            # Price analysis
            prices = [p.get('price', 0) for p in all_products if p.get('price', 0) > 0]
            if prices:
                insights['price_analysis'] = {
                    'average': np.mean(prices),
                    'median': np.median(prices),
                    'std_deviation': np.std(prices),
                    'price_spread': max(prices) - min(prices),
                    'coefficient_variation': np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
                }
            
            # Market insights
            insights['market_insights'] = {
                'total_listings': len(all_products),
                'unique_sellers': len(set(p.get('seller', 'unknown') for p in all_products)),
                'average_rating': np.mean([p.get('rating', 0) for p in all_products if p.get('rating', 0) > 0]) or 0,
                'availability_rate': len([p for p in all_products if p.get('in_stock', False)]) / len(all_products)
            }
            
            # Quality indicators
            insights['quality_indicators'] = {
                'high_rated_products': len([p for p in all_products if p.get('rating', 0) >= 4.0]),
                'products_with_reviews': len([p for p in all_products if p.get('review_count', 0) > 0]),
                'trusted_sellers': len([p for p in all_products if p.get('seller_rating', 0) >= 95])
            }
            
            # AI-powered product matching using CLIP
            if self.clip_model:
                insights['product_matching_score'] = await self._calculate_product_similarity(
                    all_products, original_query
                )
            
        except Exception as e:
            logger.error(f"❌ AI insights generation failed: {e}")
            insights['error'] = str(e)
        
        return insights
    
    async def _calculate_product_similarity(self, products: List[Dict], original_query: str) -> float:
        """Calculate product similarity using CLIP model"""
        try:
            if not self.clip_model or not products:
                return 0.0
            
            # Extract product titles
            titles = [p.get('title', '') for p in products if p.get('title')]
            if not titles:
                return 0.0
            
            # Use CLIP to calculate semantic similarity
            # This is a simplified version - in practice, you'd use the actual CLIP model
            similarity_scores = []
            
            for title in titles:
                # Simple semantic matching (replace with actual CLIP embedding comparison)
                title_words = set(title.lower().split())
                query_words = set(original_query.lower().split())
                
                if title_words and query_words:
                    intersection = len(title_words.intersection(query_words))
                    union = len(title_words.union(query_words))
                    jaccard_similarity = intersection / union if union > 0 else 0
                    similarity_scores.append(jaccard_similarity)
            
            return np.mean(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Product similarity calculation failed: {e}")
            return 0.0
    
    def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """Generate smart recommendations based on price analysis"""
        recommendations = []
        
        try:
            if results['total_results'] == 0:
                return recommendations
            
            price_range = results['price_range']
            price_spread = price_range['max'] - price_range['min']
            
            # Best value recommendation
            all_products = []
            for site_products in results['sites'].values():
                all_products.extend(site_products)
            
            if all_products:
                # Find products with good price-to-rating ratio
                scored_products = []
                for product in all_products:
                    price = product.get('price', 0)
                    rating = product.get('rating', 0)
                    if price > 0 and rating > 0:
                        # Simple value score (higher is better)
                        value_score = (rating / 5.0) / (price / price_range['max']) if price_range['max'] > 0 else 0
                        scored_products.append((product, value_score))
                
                # Sort by value score
                scored_products.sort(key=lambda x: x[1], reverse=True)
                
                if scored_products:
                    best_value = scored_products[0][0]
                    recommendations.append({
                        'type': 'best_value',
                        'title': 'Best Value for Money',
                        'product': best_value,
                        'reason': f"Great balance of price (${best_value.get('price', 0):.2f}) and rating ({best_value.get('rating', 0):.1f}/5)"
                    })
                
                # Lowest price recommendation
                cheapest = min(all_products, key=lambda x: x.get('price', float('inf')))
                if cheapest.get('price', 0) > 0:
                    recommendations.append({
                        'type': 'lowest_price',
                        'title': 'Lowest Price Found',
                        'product': cheapest,
                        'reason': f"Cheapest option at ${cheapest.get('price', 0):.2f}"
                    })
                
                # Highest rated recommendation
                highest_rated = max(all_products, key=lambda x: x.get('rating', 0))
                if highest_rated.get('rating', 0) > 0:
                    recommendations.append({
                        'type': 'highest_rated',
                        'title': 'Highest Customer Rating',
                        'product': highest_rated,
                        'reason': f"Top rated at {highest_rated.get('rating', 0):.1f}/5 stars"
                    })
        
        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
        
        return recommendations
    
    async def _ai_enhanced_comparison(self, product: Product, price_results: Dict) -> Dict:
        """Enhanced AI comparison with existing product data"""
        ai_comparison = {
            'similarity_analysis': {},
            'price_positioning': {},
            'market_analysis': {},
            'recommendations': []
        }
        
        try:
            # Analyze how the existing product compares to market findings
            if price_results.get('total_results', 0) > 0:
                market_avg = price_results.get('ai_insights', {}).get('price_analysis', {}).get('average', 0)
                market_min = price_results.get('price_range', {}).get('min', 0)
                market_max = price_results.get('price_range', {}).get('max', 0)
                
                # If product has a price, compare it to market
                if hasattr(product, 'price') and product.price:
                    product_price = float(product.price)
                    
                    ai_comparison['price_positioning'] = {
                        'product_price': product_price,
                        'market_average': market_avg,
                        'position': self._calculate_price_position(product_price, market_min, market_max),
                        'competitiveness': self._calculate_competitiveness(product_price, market_avg)
                    }
                
                # Market analysis
                ai_comparison['market_analysis'] = {
                    'market_size': price_results.get('total_results', 0),
                    'price_diversity': market_max - market_min if market_max > market_min else 0,
                    'average_rating': price_results.get('ai_insights', {}).get('market_insights', {}).get('average_rating', 0)
                }
                
                # Generate AI recommendations
                ai_comparison['recommendations'] = self._generate_ai_recommendations(product, price_results)
        
        except Exception as e:
            logger.error(f"❌ AI enhanced comparison failed: {e}")
            ai_comparison['error'] = str(e)
        
        return ai_comparison
    
    def _calculate_price_position(self, product_price: float, market_min: float, market_max: float) -> str:
        """Calculate where the product price stands in the market"""
        if market_max <= market_min:
            return "unknown"
        
        position_ratio = (product_price - market_min) / (market_max - market_min)
        
        if position_ratio <= 0.25:
            return "budget"
        elif position_ratio <= 0.50:
            return "mid-low"
        elif position_ratio <= 0.75:
            return "mid-high"
        else:
            return "premium"
    
    def _calculate_competitiveness(self, product_price: float, market_avg: float) -> str:
        """Calculate how competitive the product price is"""
        if market_avg <= 0:
            return "unknown"
        
        ratio = product_price / market_avg
        
        if ratio <= 0.8:
            return "very_competitive"
        elif ratio <= 0.95:
            return "competitive"
        elif ratio <= 1.05:
            return "average"
        elif ratio <= 1.2:
            return "above_average"
        else:
            return "premium_priced"
    
    def _generate_ai_recommendations(self, product: Product, price_results: Dict) -> List[str]:
        """Generate AI-powered recommendations for the product"""
        recommendations = []
        
        try:
            market_insights = price_results.get('ai_insights', {}).get('market_insights', {})
            price_analysis = price_results.get('ai_insights', {}).get('price_analysis', {})
            
            avg_rating = market_insights.get('average_rating', 0)
            price_variation = price_analysis.get('coefficient_variation', 0)
            
            # Market positioning recommendations
            if avg_rating > 4.0:
                recommendations.append("Market shows high customer satisfaction - ensure your product quality meets expectations")
            
            if price_variation > 0.3:
                recommendations.append("High price variation in market - consider competitive pricing strategy")
            
            # Availability recommendations
            availability_rate = market_insights.get('availability_rate', 0)
            if availability_rate < 0.7:
                recommendations.append("Low market availability - opportunity for stock availability advantage")
            
            # Quality recommendations
            quality_indicators = price_results.get('ai_insights', {}).get('quality_indicators', {})
            high_rated_ratio = quality_indicators.get('high_rated_products', 0) / max(market_insights.get('total_listings', 1), 1)
            
            if high_rated_ratio > 0.6:
                recommendations.append("Market dominated by high-rated products - focus on quality and customer satisfaction")
        
        except Exception as e:
            logger.error(f"❌ AI recommendation generation failed: {e}")
        
        return recommendations

# Global instance
cumpair_price_engine = CumpairPriceEngine()

# Backward compatibility alias
price_comparison_service = cumpair_price_engine
