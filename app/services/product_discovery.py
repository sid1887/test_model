"""
Automated Product Discovery Workflow for Cumpair
Combines AI image analysis, web scraping, and intelligent product matching
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib
from pathlib import Path

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.models.analysis import Analysis
from app.services.ai_models import ModelManager, ProductAnalyzer
from app.services.price_comparison import cumpair_price_engine
from app.services.scraping import scraper_client
from app.services.image_analysis import ImageAnalysisService
from app.core.monitoring import logger

class CumpairProductDiscovery:
    """
    Automated product discovery and analysis workflow
    """
    
    def __init__(self):
        self.model_manager = None
        self.product_analyzer = None
        self.image_service = ImageAnalysisService()
        self.price_engine = cumpair_price_engine
        self.discovery_workflows = {
            'image_to_product': self._image_to_product_workflow,
            'text_to_products': self._text_to_products_workflow,
            'competitive_analysis': self._competitive_analysis_workflow,
            'market_discovery': self._market_discovery_workflow
        }
    
    async def initialize(self, model_manager: ModelManager = None):
        """Initialize the product discovery system"""
        try:
            if model_manager:
                self.model_manager = model_manager
                self.product_analyzer = ProductAnalyzer(model_manager)
            
            # Initialize other services
            await self.price_engine.initialize()
            logger.info("✅ Cumpair Product Discovery initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Product Discovery initialization failed: {e}")
            return False
    
    async def discover_product_from_image(self, image_path: str, user_context: Dict = None) -> Dict:
        """
        Complete workflow: Image → AI Analysis → Product Discovery → Price Comparison
        
        Args:
            image_path: Path to the product image
            user_context: Additional context from user (category, brand preferences, etc.)
            
        Returns:
            Comprehensive product discovery results
        """
        workflow_id = self._generate_workflow_id("image_discovery", image_path)
        logger.info(f"🔍 Starting image-to-product discovery workflow: {workflow_id}")
        
        result = {
            'workflow_id': workflow_id,
            'workflow_type': 'image_to_product',
            'status': 'processing',
            'timestamp': datetime.utcnow().isoformat(),
            'input': {
                'image_path': image_path,
                'user_context': user_context or {}
            },
            'stages': {},
            'final_results': {}
        }
        
        try:
            # Stage 1: AI Image Analysis
            logger.info(f"📸 Stage 1: AI Image Analysis for {workflow_id}")
            ai_analysis = await self._analyze_image_with_ai(image_path)
            result['stages']['ai_analysis'] = ai_analysis
            
            if not ai_analysis.get('success'):
                result['status'] = 'failed'
                result['error'] = 'AI analysis failed'
                return result
            
            # Stage 2: Generate Search Queries
            logger.info(f"🔤 Stage 2: Generating search queries for {workflow_id}")
            search_queries = self._generate_search_queries(ai_analysis, user_context)
            result['stages']['search_queries'] = search_queries
            
            # Stage 3: Multi-Platform Product Search
            logger.info(f"🌐 Stage 3: Multi-platform search for {workflow_id}")
            search_results = await self._execute_multi_platform_search(search_queries)
            result['stages']['search_results'] = search_results
            
            # Stage 4: AI Product Matching
            logger.info(f"🤖 Stage 4: AI product matching for {workflow_id}")
            matched_products = await self._match_products_with_ai(ai_analysis, search_results)
            result['stages']['matched_products'] = matched_products
            
            # Stage 5: Price Analysis & Recommendations
            logger.info(f"💰 Stage 5: Price analysis for {workflow_id}")
            price_analysis = await self._analyze_prices_and_recommend(matched_products)
            result['stages']['price_analysis'] = price_analysis
            
            # Stage 6: Generate Final Insights
            logger.info(f"💡 Stage 6: Generating insights for {workflow_id}")
            final_insights = self._generate_discovery_insights(result)
            result['final_results'] = final_insights
            
            result['status'] = 'completed'
            logger.info(f"✅ Product discovery workflow completed: {workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ Product discovery workflow failed: {workflow_id} - {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    async def discover_competitive_products(self, base_product_id: int, analysis_depth: str = "standard") -> Dict:
        """
        Discover competitive products for an existing product
        
        Args:
            base_product_id: ID of the base product to analyze
            analysis_depth: "basic", "standard", or "comprehensive"
            
        Returns:
            Competitive analysis results
        """
        workflow_id = self._generate_workflow_id("competitive_analysis", str(base_product_id))
        logger.info(f"🏆 Starting competitive analysis workflow: {workflow_id}")
        
        result = {
            'workflow_id': workflow_id,
            'workflow_type': 'competitive_analysis',
            'base_product_id': base_product_id,
            'analysis_depth': analysis_depth,
            'status': 'processing',
            'timestamp': datetime.utcnow().isoformat(),
            'stages': {},
            'competitive_insights': {}
        }
        
        try:
            # Get base product information
            db = next(get_db())
            base_product = db.query(Product).filter(Product.id == base_product_id).first()
            
            if not base_product:
                result['status'] = 'failed'
                result['error'] = f'Product {base_product_id} not found'
                return result
            
            # Stage 1: Analyze base product characteristics
            logger.info(f"📊 Stage 1: Analyzing base product for {workflow_id}")
            base_analysis = await self._analyze_base_product(base_product)
            result['stages']['base_analysis'] = base_analysis
            
            # Stage 2: Generate competitive search strategies
            logger.info(f"🎯 Stage 2: Generating competitive search strategies for {workflow_id}")
            search_strategies = self._generate_competitive_search_strategies(base_analysis, analysis_depth)
            result['stages']['search_strategies'] = search_strategies
            
            # Stage 3: Execute competitive searches
            logger.info(f"🔍 Stage 3: Executing competitive searches for {workflow_id}")
            competitive_products = await self._find_competitive_products(search_strategies)
            result['stages']['competitive_products'] = competitive_products
            
            # Stage 4: Compare and analyze
            logger.info(f"📈 Stage 4: Competitive comparison analysis for {workflow_id}")
            comparison_analysis = await self._analyze_competitive_landscape(
                base_product, competitive_products, analysis_depth
            )
            result['stages']['comparison_analysis'] = comparison_analysis
            
            # Stage 5: Generate strategic insights
            logger.info(f"💡 Stage 5: Generating strategic insights for {workflow_id}")
            strategic_insights = self._generate_competitive_insights(result)
            result['competitive_insights'] = strategic_insights
            
            result['status'] = 'completed'
            logger.info(f"✅ Competitive analysis completed: {workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ Competitive analysis failed: {workflow_id} - {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        finally:
            db.close()
        
        return result
    
    async def discover_market_trends(self, category: str, time_horizon: str = "30d") -> Dict:
        """
        Discover market trends and emerging products in a category
        
        Args:
            category: Product category to analyze
            time_horizon: Time horizon for trend analysis ("7d", "30d", "90d")
            
        Returns:
            Market trend analysis results
        """
        workflow_id = self._generate_workflow_id("market_trends", f"{category}_{time_horizon}")
        logger.info(f"📊 Starting market trends discovery: {workflow_id}")
        
        result = {
            'workflow_id': workflow_id,
            'workflow_type': 'market_trends',
            'category': category,
            'time_horizon': time_horizon,
            'status': 'processing',
            'timestamp': datetime.utcnow().isoformat(),
            'trend_analysis': {},
            'emerging_products': {},
            'market_insights': {}
        }
        
        try:
            # Stage 1: Define trend search parameters
            logger.info(f"⚙️ Stage 1: Defining trend parameters for {workflow_id}")
            trend_parameters = self._define_trend_parameters(category, time_horizon)
            
            # Stage 2: Execute trend searches
            logger.info(f"🔍 Stage 2: Executing trend searches for {workflow_id}")
            trend_data = await self._execute_trend_searches(trend_parameters)
            
            # Stage 3: Analyze market patterns
            logger.info(f"📈 Stage 3: Analyzing market patterns for {workflow_id}")
            pattern_analysis = self._analyze_market_patterns(trend_data)
            result['trend_analysis'] = pattern_analysis
            
            # Stage 4: Identify emerging products
            logger.info(f"🌟 Stage 4: Identifying emerging products for {workflow_id}")
            emerging_products = await self._identify_emerging_products(trend_data, pattern_analysis)
            result['emerging_products'] = emerging_products
            
            # Stage 5: Generate market insights
            logger.info(f"💡 Stage 5: Generating market insights for {workflow_id}")
            market_insights = self._generate_market_insights(result)
            result['market_insights'] = market_insights
            
            result['status'] = 'completed'
            logger.info(f"✅ Market trends discovery completed: {workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ Market trends discovery failed: {workflow_id} - {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    # Private workflow methods
    
    async def _analyze_image_with_ai(self, image_path: str) -> Dict:
        """Analyze image using AI models"""
        try:
            if not self.product_analyzer:
                return {'success': False, 'error': 'AI analyzer not available'}
            
            # Use the existing product analyzer
            analysis_result = await self.product_analyzer.analyze_product_image(image_path)
            
            return {
                'success': True,
                'ai_analysis': analysis_result,
                'extracted_features': analysis_result.get('features', {}),
                'detected_objects': analysis_result.get('objects', []),
                'categories': analysis_result.get('categories', []),
                'confidence_scores': analysis_result.get('confidence_scores', {})
            }
            
        except Exception as e:
            logger.error(f"❌ AI image analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_search_queries(self, ai_analysis: Dict, user_context: Dict = None) -> List[str]:
        """Generate search queries based on AI analysis and user context"""
        queries = []
        
        try:
            ai_data = ai_analysis.get('ai_analysis', {})
            categories = ai_data.get('categories', [])
            features = ai_data.get('extracted_features', {})
            
            # Base queries from AI detection
            for category in categories[:3]:  # Top 3 categories
                queries.append(category)
            
            # Feature-based queries
            if features:
                brand = features.get('brand', '')
                color = features.get('color', '')
                material = features.get('material', '')
                
                if brand and categories:
                    queries.append(f"{brand} {categories[0]}")
                
                if color and categories:
                    queries.append(f"{color} {categories[0]}")
                
                if material and categories:
                    queries.append(f"{material} {categories[0]}")
            
            # User context queries
            if user_context:
                user_category = user_context.get('preferred_category')
                user_brand = user_context.get('preferred_brand')
                
                if user_category:
                    queries.append(user_category)
                if user_brand and categories:
                    queries.append(f"{user_brand} {categories[0]}")
            
            # Remove duplicates and empty queries
            queries = list(set([q.strip() for q in queries if q.strip()]))
            
            logger.info(f"Generated {len(queries)} search queries")
            return queries[:5]  # Limit to top 5 queries
            
        except Exception as e:
            logger.error(f"❌ Search query generation failed: {e}")
            return ["product"]  # Fallback query
    
    async def _execute_multi_platform_search(self, queries: List[str]) -> Dict:
        """Execute searches across multiple platforms"""
        search_results = {
            'total_queries': len(queries),
            'executed_searches': 0,
            'total_products_found': 0,
            'platform_results': {},
            'aggregated_results': []
        }
        
        try:
            for query in queries:
                logger.info(f"🔍 Searching for: {query}")
                
                # Use the price engine for multi-platform search
                price_results = await self.price_engine.find_product_prices(query, max_results=5)
                
                if price_results.get('total_results', 0) > 0:
                    search_results['executed_searches'] += 1
                    search_results['total_products_found'] += price_results['total_results']
                    
                    # Store results by platform
                    for site, products in price_results.get('sites', {}).items():
                        if site not in search_results['platform_results']:
                            search_results['platform_results'][site] = []
                        search_results['platform_results'][site].extend(products)
                    
                    # Add to aggregated results
                    search_results['aggregated_results'].append({
                        'query': query,
                        'results': price_results
                    })
                
                # Rate limiting
                await asyncio.sleep(1.0)
            
            logger.info(f"Multi-platform search completed: {search_results['total_products_found']} products found")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Multi-platform search failed: {e}")
            search_results['error'] = str(e)
            return search_results
    
    async def _match_products_with_ai(self, ai_analysis: Dict, search_results: Dict) -> Dict:
        """Use AI to match and rank products based on image analysis"""
        matching_results = {
            'total_candidates': search_results.get('total_products_found', 0),
            'matched_products': [],
            'matching_scores': {},
            'top_matches': []
        }
        
        try:
            # Extract AI features for comparison
            ai_features = ai_analysis.get('ai_analysis', {}).get('extracted_features', {})
            ai_categories = ai_analysis.get('ai_analysis', {}).get('categories', [])
            
            all_products = []
            for result in search_results.get('aggregated_results', []):
                for site, products in result.get('results', {}).get('sites', {}).items():
                    for product in products:
                        product['source_query'] = result['query']
                        product['source_site'] = site
                        all_products.append(product)
            
            # Simple AI matching (in production, use actual CLIP embeddings)
            for product in all_products:
                product_title = product.get('title', '').lower()
                product_description = product.get('description', '').lower()
                
                # Calculate matching score
                score = 0.0
                
                # Category matching
                for category in ai_categories:
                    if category.lower() in product_title or category.lower() in product_description:
                        score += 0.3
                
                # Feature matching
                if ai_features:
                    for feature_type, feature_value in ai_features.items():
                        if feature_value and feature_value.lower() in product_title:
                            score += 0.2
                
                # Title relevance (simple keyword matching)
                if product.get('source_query', '').lower() in product_title:
                    score += 0.3
                
                # Rating bonus
                rating = product.get('rating', 0)
                if rating > 4.0:
                    score += 0.1
                elif rating > 3.5:
                    score += 0.05
                
                product['ai_matching_score'] = min(score, 1.0)  # Cap at 1.0
                matching_results['matched_products'].append(product)
            
            # Sort by matching score
            matching_results['matched_products'].sort(
                key=lambda x: x.get('ai_matching_score', 0), 
                reverse=True
            )
            
            # Get top 10 matches
            matching_results['top_matches'] = matching_results['matched_products'][:10]
            
            logger.info(f"AI product matching completed: {len(matching_results['top_matches'])} top matches")
            return matching_results
            
        except Exception as e:
            logger.error(f"❌ AI product matching failed: {e}")
            matching_results['error'] = str(e)
            return matching_results
    
    async def _analyze_prices_and_recommend(self, matched_products: Dict) -> Dict:
        """Analyze prices and generate recommendations"""
        price_analysis = {
            'price_statistics': {},
            'value_recommendations': [],
            'price_alerts': [],
            'market_positioning': {}
        }
        
        try:
            top_matches = matched_products.get('top_matches', [])
            if not top_matches:
                return price_analysis
            
            prices = [p.get('price', 0) for p in top_matches if p.get('price', 0) > 0]
            if not prices:
                return price_analysis
            
            # Calculate price statistics
            import numpy as np
            price_analysis['price_statistics'] = {
                'min_price': min(prices),
                'max_price': max(prices),
                'average_price': np.mean(prices),
                'median_price': np.median(prices),
                'price_range': max(prices) - min(prices),
                'price_std': np.std(prices)
            }
            
            # Generate value recommendations
            for product in top_matches[:5]:
                price = product.get('price', 0)
                rating = product.get('rating', 0)
                matching_score = product.get('ai_matching_score', 0)
                
                if price > 0:
                    # Calculate value score
                    price_percentile = (price - min(prices)) / (max(prices) - min(prices)) if max(prices) > min(prices) else 0.5
                    rating_score = rating / 5.0 if rating > 0 else 0.5
                    
                    value_score = (matching_score * 0.4 + rating_score * 0.3 + (1 - price_percentile) * 0.3)
                    
                    price_analysis['value_recommendations'].append({
                        'product': product,
                        'value_score': value_score,
                        'price_position': 'budget' if price_percentile < 0.33 else 'mid-range' if price_percentile < 0.66 else 'premium',
                        'recommendation_reason': self._generate_recommendation_reason(product, value_score, price_percentile)
                    })
            
            # Sort by value score
            price_analysis['value_recommendations'].sort(
                key=lambda x: x['value_score'], 
                reverse=True
            )
            
            logger.info(f"Price analysis completed: {len(price_analysis['value_recommendations'])} recommendations")
            return price_analysis
            
        except Exception as e:
            logger.error(f"❌ Price analysis failed: {e}")
            price_analysis['error'] = str(e)
            return price_analysis
    
    def _generate_recommendation_reason(self, product: Dict, value_score: float, price_percentile: float) -> str:
        """Generate human-readable recommendation reason"""
        reasons = []
        
        if value_score > 0.8:
            reasons.append("Excellent overall value")
        elif value_score > 0.6:
            reasons.append("Good value for money")
        
        if price_percentile < 0.33:
            reasons.append("budget-friendly price")
        elif price_percentile > 0.66:
            reasons.append("premium option")
        
        rating = product.get('rating', 0)
        if rating > 4.5:
            reasons.append("outstanding customer reviews")
        elif rating > 4.0:
            reasons.append("great customer satisfaction")
        
        matching_score = product.get('ai_matching_score', 0)
        if matching_score > 0.7:
            reasons.append("high similarity to your image")
        
        return ", ".join(reasons) if reasons else "matches your search criteria"
    
    def _generate_discovery_insights(self, workflow_result: Dict) -> Dict:
        """Generate final insights from the discovery workflow"""
        insights = {
            'summary': {},
            'key_findings': [],
            'recommendations': [],
            'confidence_level': 'medium'
        }
        
        try:
            # Extract key metrics
            ai_analysis = workflow_result.get('stages', {}).get('ai_analysis', {})
            search_results = workflow_result.get('stages', {}).get('search_results', {})
            matched_products = workflow_result.get('stages', {}).get('matched_products', {})
            price_analysis = workflow_result.get('stages', {}).get('price_analysis', {})
            
            # Summary
            insights['summary'] = {
                'total_products_discovered': search_results.get('total_products_found', 0),
                'platforms_searched': len(search_results.get('platform_results', {})),
                'top_matches_found': len(matched_products.get('top_matches', [])),
                'price_range_discovered': price_analysis.get('price_statistics', {})
            }
            
            # Key findings
            if ai_analysis.get('success'):
                insights['key_findings'].append("Successfully analyzed product image with AI")
            
            if search_results.get('total_products_found', 0) > 10:
                insights['key_findings'].append(f"Found {search_results['total_products_found']} similar products across multiple platforms")
            
            if matched_products.get('top_matches'):
                best_match = matched_products['top_matches'][0]
                insights['key_findings'].append(f"Best match: {best_match.get('title', 'Unknown')} with {best_match.get('ai_matching_score', 0):.2f} similarity score")
            
            # Recommendations
            value_recs = price_analysis.get('value_recommendations', [])
            if value_recs:
                top_value = value_recs[0]
                insights['recommendations'].append({
                    'type': 'best_value',
                    'title': 'Best Value Recommendation',
                    'product': top_value['product'],
                    'reason': top_value['recommendation_reason']
                })
            
            # Calculate confidence level
            confidence_factors = []
            if ai_analysis.get('success'):
                confidence_factors.append(0.3)
            if search_results.get('executed_searches', 0) >= 3:
                confidence_factors.append(0.3)
            if len(matched_products.get('top_matches', [])) >= 5:
                confidence_factors.append(0.2)
            if len(value_recs) >= 3:
                confidence_factors.append(0.2)
            
            confidence_score = sum(confidence_factors)
            if confidence_score >= 0.8:
                insights['confidence_level'] = 'high'
            elif confidence_score >= 0.5:
                insights['confidence_level'] = 'medium'
            else:
                insights['confidence_level'] = 'low'
            
            logger.info(f"Discovery insights generated with {insights['confidence_level']} confidence")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Insight generation failed: {e}")
            insights['error'] = str(e)
            return insights
    
    def _generate_workflow_id(self, workflow_type: str, input_identifier: str) -> str:
        """Generate unique workflow ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{workflow_type}_{input_identifier}_{timestamp}".encode()
        hash_suffix = hashlib.md5(hash_input).hexdigest()[:8]
        return f"{workflow_type}_{timestamp}_{hash_suffix}"
    
    # Workflow Methods (called by discovery_workflows dictionary)
    
    async def _image_to_product_workflow(self, image_path: str, context: Dict = None) -> Dict:
        """Core image-to-product workflow"""
        try:
            logger.info(f"🖼️ Starting image-to-product workflow for: {image_path}")
            
            # Step 1: AI Image Analysis
            analysis_result = await self._analyze_image_with_ai(image_path)
            
            if not analysis_result.get('success'):
                return {
                    'status': 'failed',
                    'error': 'Image analysis failed',
                    'details': analysis_result.get('error', 'Unknown error')
                }
            
            # Step 2: Generate search queries
            search_queries = self._generate_search_queries(analysis_result, context)
            
            # Step 3: Execute multi-platform search
            search_results = await self._execute_multi_platform_search(search_queries)
            
            return {
                'status': 'success',
                'workflow_type': 'image_to_product',
                'analysis': analysis_result,
                'search_queries': search_queries,
                'search_results': search_results,
                'summary': f"Found {search_results.get('total_products_found', 0)} products"
            }
                
        except Exception as e:
            logger.error(f"❌ Image-to-product workflow failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _text_to_products_workflow(self, text_query: str, context: Dict = None) -> Dict:
        """Text-based product discovery workflow"""
        try:
            logger.info(f"📝 Starting text-to-products workflow for: {text_query}")
            
            # Generate enhanced search queries
            search_queries = [text_query]
            if context:
                category = context.get('category')
                brand = context.get('brand')
                if category:
                    search_queries.append(f"{text_query} {category}")
                if brand:
                    search_queries.append(f"{brand} {text_query}")
            
            # Execute search
            search_results = await self._execute_multi_platform_search(search_queries)
            
            return {
                'status': 'success',
                'workflow_type': 'text_to_products',
                'query': text_query,
                'search_queries': search_queries,
                'results': search_results,
                'summary': f"Found {search_results.get('total_products_found', 0)} products for '{text_query}'"
            }
            
        except Exception as e:
            logger.error(f"❌ Text-to-products workflow failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _competitive_analysis_workflow(self, product_name: str, context: Dict = None) -> Dict:
        """Competitive analysis workflow"""
        try:
            logger.info(f"🏪 Starting competitive analysis for: {product_name}")
            
            # Search for the main product and competitors
            search_results = await self._execute_multi_platform_search([product_name])
            
            # Analyze competition
            competitors = []
            platform_results = search_results.get('platform_results', {})
            
            for platform, results in platform_results.items():
                for product in results.get('products', [])[:5]:  # Top 5 per platform
                    competitors.append({
                        'name': product.get('title', ''),
                        'price': product.get('price', 0),
                        'platform': platform,
                        'url': product.get('url', ''),
                        'rating': product.get('rating', 0),
                        'availability': product.get('availability', 'unknown')
                    })
            
            # Generate competitive insights
            price_analysis = self._analyze_competitive_pricing(competitors)
            
            return {
                'status': 'success',
                'workflow_type': 'competitive_analysis',
                'product': product_name,
                'competitors': competitors,
                'price_analysis': price_analysis,
                'insights': {
                    'total_competitors': len(competitors),
                    'platforms_analyzed': len(platform_results),
                    'price_range': price_analysis.get('price_range', {}),
                    'market_position': price_analysis.get('market_position', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Competitive analysis workflow failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _market_discovery_workflow(self, category: str, context: Dict = None) -> Dict:
        """Market discovery workflow"""
        try:
            logger.info(f"📊 Starting market discovery for category: {category}")
            
            # Generate category-based search terms
            search_terms = [
                category,
                f"best {category}",
                f"popular {category}",
                f"trending {category}",
                f"new {category}"
            ]
            
            # Execute searches
            search_results = await self._execute_multi_platform_search(search_terms)
            
            # Analyze market trends
            market_trends = self._analyze_market_trends(search_results, category)
            
            return {
                'status': 'success',
                'workflow_type': 'market_discovery',
                'category': category,
                'search_results': search_results,
                'market_trends': market_trends,
                'insights': {
                    'category_size': search_results.get('total_products_found', 0),
                    'trending_products': market_trends.get('trending', [])[:10],
                    'price_insights': market_trends.get('price_analysis', {}),
                    'platform_distribution': market_trends.get('platform_distribution', {})
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Market discovery workflow failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _analyze_competitive_pricing(self, competitors: List[Dict]) -> Dict:
        """Analyze competitive pricing"""
        if not competitors:
            return {'price_range': {}, 'market_position': 'unknown'}
        
        prices = [c.get('price', 0) for c in competitors if c.get('price', 0) > 0]
        if not prices:
            return {'price_range': {}, 'market_position': 'unknown'}
        
        return {
            'price_range': {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices) // 2]
            },
            'market_position': 'analyzed',
            'price_distribution': {
                'low': len([p for p in prices if p < sum(prices) / len(prices) * 0.8]),
                'medium': len([p for p in prices if sum(prices) / len(prices) * 0.8 <= p <= sum(prices) / len(prices) * 1.2]),
                'high': len([p for p in prices if p > sum(prices) / len(prices) * 1.2])
            }
        }
    
    def _analyze_market_trends(self, search_results: Dict, category: str) -> Dict:
        """Analyze market trends from search results"""
        platform_results = search_results.get('platform_results', {})
        all_products = []
        
        for platform, results in platform_results.items():
            all_products.extend(results.get('products', []))
        
        # Extract trending products (top rated, high availability)
        trending = sorted(all_products, key=lambda x: (x.get('rating', 0), x.get('price', 0)), reverse=True)
        
        # Price analysis
        prices = [p.get('price', 0) for p in all_products if p.get('price', 0) > 0]
        price_analysis = {
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'price_range': {'min': min(prices), 'max': max(prices)} if prices else {}
        }
        
        # Platform distribution
        platform_distribution = {}
        for platform, results in platform_results.items():
            platform_distribution[platform] = len(results.get('products', []))
        
        return {
            'trending': trending,
            'price_analysis': price_analysis,
            'platform_distribution': platform_distribution,
            'total_products_analyzed': len(all_products)
        }

# Global instance
cumpair_discovery = CumpairProductDiscovery()

# Service alias for consistency
product_discovery_service = cumpair_discovery
