"""
Enhanced Price Comparison Service for Cumpair
Integrates web scraping, AI-powered product matching, and intelligent price analysis
"""

import asyncio
import json
import re
import numpy as np
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.models.price_comparison import PriceComparison
from app.services.scraping import scraper_client, scraping_engine
from app.services.ai_models import model_manager
from app.core.monitoring import logger, performance_timer
from app.core import config

# Import enhanced data pipeline and analytics services
from app.services.data_pipeline import data_pipeline_service, ScoringWeights
from app.services.pricing_analytics import pricing_analytics_service
from app.services.retailer_manager import retailer_manager, RetailerCategory, RetailerPriority

class CumpairPriceEngine:
    """Enhanced price comparison engine with AI-powered matching and 15+ retailers"""
    
    def __init__(self):
        self.scraper_client = scraper_client
        self.scraping_engine = scraping_engine
        self.clip_model = None
        self.similarity_threshold = 0.85
        self.retailer_manager = retailer_manager
        
        # Legacy configurations maintained for backward compatibility
        self.ecommerce_sites = {}
        self._load_legacy_configurations()
    
    def _load_legacy_configurations(self):
        """Load legacy configurations for backward compatibility"""
        # This method maintains compatibility with existing code
        # New implementations should use retailer_manager instead
        pass
    
    async def initialize(self):
        """Initialize the price comparison engine"""
        try:
            await self.scraper_client.initialize()
            self.clip_model = model_manager.get_model('clip')
            
            # Load configuration
            self.similarity_threshold = config.get('PRODUCT_MATCHING_THRESHOLD', 0.85)
            
            logger.info("✅ Cumpair Price Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cumpair Price Engine: {e}", exc_info=True)
            return False
    
    @performance_timer
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
        
        try:
            # Generate and validate search URLs
            search_urls = self._generate_search_urls(product_query)
            if not search_urls:
                logger.warning("No valid search URLs generated")
                return results
                
            # Execute scraping tasks with concurrency control
            scraping_tasks = []
            for site, urls in search_urls.items():
                for url in urls[:max_results]:
                    task = self._scrape_with_rate_limit(site, url, product_query)
                    scraping_tasks.append(task)
            
            # Process results with error handling
            successful_results = 0
            for result in await asyncio.gather(*scraping_tasks, return_exceptions=True):
                if isinstance(result, Exception):
                    logger.error(f"Scraping task failed: {result}", exc_info=True)
                    continue
                
                if result and result.get('status') == 'success':
                    site = result.get('site')
                    product_data = result.get('data', {})
                    
                    # Validate and normalize product data
                    validated = self._validate_product_data(product_data)
                    if not validated:
                        continue
                        
                    if site not in results['sites']:
                        results['sites'][site] = []
                    
                    results['sites'][site].append(product_data)
                    results['total_results'] += 1
                    successful_results += 1
                    
                    # Update price range
                    price = product_data['price']
                    results['price_range']['min'] = min(results['price_range']['min'], price)
                    results['price_range']['max'] = max(results['price_range']['max'], price)
            
            # Generate insights if we have results
            if successful_results > 0:
                logger.info(f"Processing {successful_results} valid products for insights")
                results['ai_insights'] = await self._generate_ai_insights(results, product_query)
                results['recommendations'] = await self._generate_recommendations(results)
            
            # Finalize price range
            if results['price_range']['min'] == float('inf'):
                results['price_range']['min'] = 0
                
            logger.info(f"✅ Price search completed: {results['total_results']} results found")
            return results
            
        except Exception as e:
            logger.error(f"❌ Price search failed: {e}", exc_info=True)
            results['error'] = str(e)
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
        db = next(get_db())
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {'error': 'Product not found', 'product_id': product_id}
            
            query = search_query or product.name or "generic product"
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
                    'description': product.description,
                    'image_url': product.image_url
                },
                'price_comparison': price_results,
                'ai_insights': ai_comparison,
                'comparison_id': comparison_record.id
            }
            
        except Exception as e:
            logger.error(f"❌ AI product comparison failed: {e}", exc_info=True)
            db.rollback()
            return {'error': str(e), 'product_id': product_id}
        finally:
            db.close()
    
    async def _generate_search_urls(self, product_query: str) -> Dict[str, List[str]]:
        """Generate search URLs using the enhanced retailer manager"""
        search_urls = {}
        
        try:
            # Get active retailers prioritized by priority level
            active_retailers = await self.retailer_manager.get_active_retailers()
            
            for retailer_config in active_retailers:
                retailer_key = retailer_config.domain.replace('.com', '')
                urls = await self.retailer_manager.generate_search_urls(
                    retailer_key, 
                    product_query, 
                    pages=2
                )
                if urls:
                    search_urls[retailer_config.domain] = urls
                    logger.info(f"Generated {len(urls)} URLs for {retailer_config.name}")
            
            # Log statistics
            total_urls = sum(len(urls) for urls in search_urls.values())
            logger.info(f"Generated {total_urls} search URLs across {len(search_urls)} retailers")
            
            return search_urls
            
        except Exception as e:
            logger.error(f"URL generation failed: {e}")
            # Fallback to legacy method if retailer manager fails
            return self._generate_legacy_search_urls(product_query)
    
    def _generate_legacy_search_urls(self, product_query: str) -> Dict[str, List[str]]:
        """Legacy URL generation method as fallback"""
        search_urls = {}
        clean_query = re.sub(r'[^\w\s-]', '', product_query).strip()
        encoded_query = clean_query.replace(' ', '+')
        
        # Basic legacy configurations
        legacy_sites = {
            'amazon.com': [f"https://www.amazon.com/s?k={encoded_query}"],
            'walmart.com': [f"https://www.walmart.com/search?q={encoded_query}"],
            'ebay.com': [f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}"],
            'bestbuy.com': [f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_query}"]
        }
        
        return legacy_sites

    async def _scrape_with_rate_limit(self, site: str, url: str, product_query: str) -> Dict:
        """Scrape a URL with site-specific rate limiting"""
        try:
            site_config = self.ecommerce_sites.get(site, {})
            await asyncio.sleep(site_config.get('rate_limit', 1.0))
            
            # Try dedicated scraper first
            scraper_result = await self.scraper_client.scrape_url(
                url, 
                params={
                    'product_query': product_query,
                    'site_config': site_config
                },
                timeout=15.0
            )
            
            if scraper_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'site': site,
                    'url': url,
                    'data': scraper_result.get('data', {}),
                    'method': 'dedicated_scraper'
                }
            
            # Fallback to adaptive scraping
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
            
        except asyncio.TimeoutError:
            logger.warning(f"⌛ Scraping timed out for {url}")
            return {
                'status': 'failed',
                'site': site,
                'url': url,
                'error': 'Scraping timeout'
            }
        except Exception as e:
            logger.error(f"❌ Scraping failed for {url}: {e}", exc_info=True)
            return {
                'status': 'failed',
                'site': site,
                'url': url,
                'error': str(e)
            }

    def _validate_product_data(self, product_data: Dict) -> bool:
        """Validate and normalize scraped product data"""
        if not product_data.get('title') or not product_data.get('price'):
            return False
            
        try:
            # Normalize price
            if isinstance(product_data['price'], str):
                product_data['price'] = float(re.sub(r'[^\d.]', '', product_data['price']))
            
            # Basic validation
            if product_data['price'] <= 0:
                return False
                
            # Normalize rating
            if 'rating' in product_data:
                if isinstance(product_data['rating'], str):
                    product_data['rating'] = float(re.search(r'(\d+\.\d+|\d+)', product_data['rating']).group(0))
                product_data['rating'] = min(5.0, max(0.0, product_data['rating']))
                
            return True
        except Exception as e:
            logger.warning(f"Validation failed for product data: {e}")
            return False

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
                
            # Enhanced price analysis using pricing service
            prices = [p.get('price', 0) for p in all_products if p.get('price', 0) > 0]
            if prices:
                insights['price_analysis'] = pricing_analytics_service.analyze_price_distribution(prices)
            
            # Market insights
            insights['market_insights'] = {
                'total_listings': len(all_products),
                'unique_sellers': len(set(p.get('seller', 'unknown') for p in all_products)),
                'average_rating': np.mean([p.get('rating', 0) for p in all_products if p.get('rating', 0) > 0]) or 0,
                'availability_rate': len([p for p in all_products if p.get('in_stock', False)]) / len(all_products),
                'image_availability': len([p for p in all_products if p.get('image_url')]) / len(all_products)
            }
            
            # Quality indicators
            insights['quality_indicators'] = {
                'high_rated_products': len([p for p in all_products if p.get('rating', 0) >= 4.0]),
                'products_with_reviews': len([p for p in all_products if p.get('review_count', 0) > 0]),
                'trusted_sellers': len([p for p in all_products if p.get('seller_rating', 0) >= 90])
            }
            
            # AI-powered product matching using CLIP
            if self.clip_model:
                insights['product_matching_score'] = await self._calculate_product_similarity(
                    all_products, original_query
                )
                
                # Add individual similarity scores
                insights['product_similarities'] = [
                    {'title': p.get('title'), 'score': p.get('similarity_score', 0)}
                    for p in all_products if 'similarity_score' in p
                ]
        
        except Exception as e:
            logger.error(f"❌ AI insights generation failed: {e}", exc_info=True)
            insights['error'] = str(e)
        
        return insights

    async def _calculate_product_similarity(self, products: List[Dict], original_query: str) -> float:
        """Calculate product similarity using CLIP model"""
        try:
            if not self.clip_model or not products:
                return 0.0
            
            # Extract product titles and filter valid ones
            valid_products = []
            titles = []
            for p in products:
                title = p.get('title', '')
                if title:
                    titles.append(title)
                    valid_products.append(p)
            
            if not titles:
                return 0.0
            
            # Encode query and titles using CLIP
            query_embedding = await self.clip_model.encode_text([original_query])
            title_embeddings = await self.clip_model.encode_text(titles)
            
            # Calculate cosine similarities
            similarities = []
            for i, embedding in enumerate(title_embeddings):
                similarity = self._cosine_similarity(query_embedding[0], embedding)
                similarities.append(similarity)
                valid_products[i]['similarity_score'] = similarity
            
            # Return average similarity score
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"❌ Product similarity calculation failed: {e}", exc_info=True)
            return 0.0

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """Generate smart recommendations based on price analysis"""
        recommendations = []
        
        try:
            if results['total_results'] == 0:
                return recommendations
            
            # Collect all products
            all_products = []
            for site_products in results['sites'].values():
                all_products.extend(site_products)
            
            if not all_products:
                return recommendations
            
            # Enhanced value scoring
            try:
                enhanced_products = await data_pipeline_service.calculate_value_score(
                    all_products, 
                    ScoringWeights.BALANCED,
                    {'price': 'price', 'rating': 'rating', 'review_count': 'review_count'}
                )
                
                if enhanced_products:
                    # Best value recommendation
                    best_value = max(enhanced_products, key=lambda x: x.get('value_score', 0))
                    recommendations.append({
                        'type': 'best_value',
                        'title': 'Best Value for Money',
                        'product': best_value,
                        'reason': f"AI-scored value: {best_value.get('value_score', 0):.2f}/5",
                        'value_score': best_value.get('value_score', 0)
                    })
                    
                    # Budget recommendation
                    budget_choice = min(enhanced_products, key=lambda x: x.get('price', float('inf')))
                    recommendations.append({
                        'type': 'budget_choice',
                        'title': 'Best Budget Option',
                        'product': budget_choice,
                        'reason': f"Price: ${budget_choice.get('price', 0):.2f}",
                        'value_score': budget_choice.get('value_score', 0)
                    })
                    
                    # Quality recommendation
                    quality_choice = max(enhanced_products, key=lambda x: x.get('rating', 0))
                    recommendations.append({
                        'type': 'quality_choice',
                        'title': 'Highest Quality Option',
                        'product': quality_choice,
                        'reason': f"Rating: {quality_choice.get('rating', 0):.1f}/5",
                        'value_score': quality_choice.get('value_score', 0)
                    })
            except Exception as e:
                logger.warning(f"Enhanced scoring failed: {e}, using fallback")
                # Fallback to simple scoring
                if all_products:
                    # Lowest price
                    cheapest = min(all_products, key=lambda x: x.get('price', float('inf')))
                    recommendations.append({
                        'type': 'lowest_price',
                        'title': 'Lowest Price',
                        'product': cheapest,
                        'reason': f"Price: ${cheapest.get('price', 0):.2f}"
                    })
                    
                    # Highest rated
                    highest_rated = max(all_products, key=lambda x: x.get('rating', 0))
                    recommendations.append({
                        'type': 'highest_rated',
                        'title': 'Highest Customer Rating',
                        'product': highest_rated,
                        'reason': f"Rating: {highest_rated.get('rating', 0):.1f}/5"
                    })
        
        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}", exc_info=True)
        
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
            if price_results.get('total_results', 0) > 0:
                market_avg = price_results.get('ai_insights', {}).get('price_analysis', {}).get('mean', 0)
                market_min = price_results.get('price_range', {}).get('min', 0)
                market_max = price_results.get('price_range', {}).get('max', 0)
                
                # Price positioning analysis
                if hasattr(product, 'price') and product.price:
                    product_price = float(product.price)
                    ai_comparison['price_positioning'] = {
                        'product_price': product_price,
                        'market_average': market_avg,
                        'position': self._calculate_price_position(product_price, market_min, market_max),
                        'competitiveness': self._calculate_competitiveness(product_price, market_avg),
                        'price_difference': product_price - market_avg,
                        'price_difference_percent': ((product_price - market_avg) / market_avg) * 100 if market_avg else 0
                    }
                
                # Market analysis
                ai_comparison['market_analysis'] = {
                    'market_size': price_results.get('total_results', 0),
                    'price_diversity': market_max - market_min if market_max > market_min else 0,
                    'average_rating': price_results.get('ai_insights', {}).get('market_insights', {}).get('average_rating', 0),
                    'quality_index': price_results.get('ai_insights', {}).get('quality_indicators', {}).get('high_rated_products', 0)
                }
                
                # Generate AI recommendations
                ai_comparison['recommendations'] = self._generate_ai_recommendations(product, price_results)
        
        except Exception as e:
            logger.error(f"❌ AI enhanced comparison failed: {e}", exc_info=True)
            ai_comparison['error'] = str(e)
        
        return ai_comparison

    def _calculate_price_position(self, product_price: float, market_min: float, market_max: float) -> str:
        """Calculate where the product price stands in the market"""
        if market_max <= market_min or market_min < 0:
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
        
        if ratio <= 0.85:
            return "highly_competitive"
        elif ratio <= 0.95:
            return "competitive"
        elif ratio <= 1.05:
            return "average"
        elif ratio <= 1.15:
            return "slightly_above"
        else:
            return "premium"

    def _generate_ai_recommendations(self, product: Product, price_results: Dict) -> List[str]:
        """Generate AI-powered recommendations for the product"""
        recommendations = []
        
        try:
            market_insights = price_results.get('ai_insights', {}).get('market_insights', {})
            price_analysis = price_results.get('ai_insights', {}).get('price_analysis', {})
            
            # Price competitiveness recommendations
            price_diff = price_analysis.get('mean', 0) - getattr(product, 'price', 0)
            if price_diff > 0:
                recommendations.append(f"Price ${price_diff:.2f} above market average - consider competitive adjustments")
            elif price_diff < 0:
                recommendations.append(f"Price ${abs(price_diff):.2f} below market average - opportunity to increase margin")
            
            # Quality recommendations
            avg_rating = market_insights.get('average_rating', 0)
            if avg_rating > 4.0 and getattr(product, 'rating', 0) < 4.0:
                recommendations.append("Market shows high customer satisfaction - improve product quality to match")
            
            # Availability recommendations
            availability_rate = market_insights.get('availability_rate', 0)
            if availability_rate < 0.8:
                recommendations.append("Low market availability - capitalize with reliable stock")
            
            # Promotional opportunities
            if price_analysis.get('skewness', 0) > 1.0:
                recommendations.append("Market shows price skew - consider promotional pricing strategies")
        
        except Exception as e:
            logger.error(f"❌ AI recommendation generation failed: {e}", exc_info=True)
        
        return recommendations

# Global instance
cumpair_price_engine = CumpairPriceEngine()