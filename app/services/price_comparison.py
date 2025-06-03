"""
Price Comparison Service - Orchestrates scraping across multiple platforms
"""

import asyncio
from typing import Dict, List, Optional
import time
from urllib.parse import quote_plus
import logging

from app.services.scraping import scraping_engine
from app.core.database import async_session_maker
from app.models.product import Product
from app.models.price_comparison import PriceComparison
from app.core.monitoring import logger
from sqlalchemy import select

class PriceComparisonService:
    """Service for comparing prices across multiple platforms"""
    
    def __init__(self):
        self.platforms = {
            'amazon': {
                'search_url': 'https://www.amazon.com/s?k={query}',
                'base_url': 'https://www.amazon.com',
                'enabled': True
            },
            'ebay': {
                'search_url': 'https://www.ebay.com/sch/i.html?_nkw={query}',
                'base_url': 'https://www.ebay.com',
                'enabled': True
            },
            'walmart': {
                'search_url': 'https://www.walmart.com/search?q={query}',
                'base_url': 'https://www.walmart.com',
                'enabled': True
            },
            'bestbuy': {
                'search_url': 'https://www.bestbuy.com/site/searchpage.jsp?st={query}',
                'base_url': 'https://www.bestbuy.com',
                'enabled': True
            },
            'target': {
                'search_url': 'https://www.target.com/s?searchTerm={query}',
                'base_url': 'https://www.target.com',
                'enabled': True
            }
        }
    
    async def compare_prices(self, product_id: int, search_queries: List[str]) -> Dict:
        """
        Compare prices across multiple platforms
        
        Args:
            product_id: Database ID of the product
            search_queries: List of search terms to use
            
        Returns:
            Price comparison results
        """
        logger.info(f"Starting price comparison for product {product_id}")
        start_time = time.time()
        
        all_results = []
        
        # Try each search query on each platform
        for query in search_queries:
            query_results = await self._search_all_platforms(query)
            all_results.extend(query_results)
        
        # Filter and rank results
        filtered_results = self._filter_and_rank_results(all_results)
        
        # Save results to database
        await self._save_price_comparisons(product_id, filtered_results)
        
        processing_time = time.time() - start_time
        
        result = {
            'product_id': product_id,
            'total_results': len(filtered_results),
            'platforms_searched': len(self.platforms),
            'search_queries': search_queries,
            'processing_time': processing_time,
            'results': filtered_results[:20],  # Top 20 results
            'status': 'completed'
        }
        
        logger.info(f"Price comparison completed for product {product_id} in {processing_time:.2f}s")
        return result
    
    async def _search_all_platforms(self, query: str) -> List[Dict]:
        """Search all enabled platforms for a given query"""
        search_tasks = []
        
        for platform_name, platform_config in self.platforms.items():
            if platform_config['enabled']:
                search_url = platform_config['search_url'].format(
                    query=quote_plus(query)
                )
                
                task = self._search_platform(platform_name, search_url, query)
                search_tasks.append(task)
        
        # Execute searches concurrently
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Platform search failed: {result}")
        
        return all_results
    
    async def _search_platform(self, platform_name: str, search_url: str, query: str) -> List[Dict]:
        """Search a specific platform"""
        try:
            logger.info(f"Searching {platform_name} for: {query}")
            
            # Use the adaptive scraping engine
            scrape_result = await scraping_engine.scrape_product(search_url, query)
            
            if scrape_result.get('status') == 'success':
                product_data = scrape_result.get('data', {})
                
                # Extract multiple products if available (for search results pages)
                products = self._extract_products_from_search(product_data, platform_name)
                
                return products
            else:
                logger.warning(f"Failed to scrape {platform_name}: {scrape_result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching {platform_name}: {e}")
            return []
    
    def _extract_products_from_search(self, search_data: Dict, platform_name: str) -> List[Dict]:
        """Extract individual products from search results"""
        products = []
        
        # If it's a single product page
        if search_data.get('title') and search_data.get('price'):
            product = {
                'source_name': platform_name,
                'title': search_data.get('title', ''),
                'price': search_data.get('price', 0),
                'currency': search_data.get('currency', 'USD'),
                'description': search_data.get('description', ''),
                'rating': search_data.get('rating', 0),
                'review_count': search_data.get('review_count', 0),
                'in_stock': search_data.get('in_stock', True),
                'seller_name': search_data.get('seller', ''),
                'image_urls': search_data.get('image_urls', []),
                'confidence_score': 0.8  # Base confidence for direct matches
            }
            products.append(product)
        
        # TODO: Add logic to parse search results pages with multiple products
        # This would involve analyzing the HTML structure to find product cards/listings
        
        return products
    
    def _filter_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """Filter and rank price comparison results"""
        if not results:
            return []
        
        # Remove duplicates based on title similarity
        unique_results = self._remove_duplicates(results)
        
        # Filter out results with no price
        valid_results = [r for r in unique_results if r.get('price', 0) > 0]
        
        # Sort by price (ascending)
        sorted_results = sorted(valid_results, key=lambda x: x.get('price', float('inf')))
        
        # Add ranking information
        for i, result in enumerate(sorted_results):
            result['rank'] = i + 1
            result['price_rank'] = 'lowest' if i == 0 else 'competitive' if i < 5 else 'higher'
        
        return sorted_results
    
    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on title similarity"""
        unique_results = []
        seen_titles = set()
        
        for result in results:
            title = result.get('title', '').lower().strip()
            
            # Simple deduplication based on title
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(result)
        
        return unique_results
    
    async def _save_price_comparisons(self, product_id: int, results: List[Dict]):
        """Save price comparison results to database"""
        try:
            async with async_session_maker() as session:
                for result in results:
                    price_comparison = PriceComparison(
                        product_id=product_id,
                        source_name=result.get('source_name', ''),
                        source_url=result.get('source_url', ''),
                        title=result.get('title', ''),
                        description=result.get('description', ''),
                        price=result.get('price', 0),
                        currency=result.get('currency', 'USD'),
                        in_stock=result.get('in_stock', True),
                        rating=result.get('rating', 0),
                        review_count=result.get('review_count', 0),
                        seller_name=result.get('seller_name', ''),
                        confidence_score=result.get('confidence_score', 0.5),
                        scraping_method=result.get('scraping_method', 'adaptive'),
                        additional_data=result
                    )
                    session.add(price_comparison)
                
                await session.commit()
                logger.info(f"Saved {len(results)} price comparisons to database")
                
        except Exception as e:
            logger.error(f"Failed to save price comparisons: {e}")
    
    async def get_price_history(self, product_id: int) -> Dict:
        """Get price history for a product"""
        try:
            async with async_session_maker() as session:
                stmt = select(PriceComparison).where(
                    PriceComparison.product_id == product_id
                ).order_by(PriceComparison.scraped_at.desc())
                
                result = await session.execute(stmt)
                comparisons = result.scalars().all()
                
                # Group by source
                history_by_source = {}
                for comparison in comparisons:
                    source = comparison.source_name
                    if source not in history_by_source:
                        history_by_source[source] = []
                    
                    history_by_source[source].append({
                        'price': float(comparison.price) if comparison.price else 0,
                        'currency': comparison.currency,
                        'date': comparison.scraped_at.isoformat() if comparison.scraped_at else None,
                        'in_stock': comparison.in_stock
                    })
                
                # Calculate price statistics
                all_prices = [float(c.price) for c in comparisons if c.price and c.price > 0]
                
                stats = {}
                if all_prices:
                    stats = {
                        'min_price': min(all_prices),
                        'max_price': max(all_prices),
                        'avg_price': sum(all_prices) / len(all_prices),
                        'price_range': max(all_prices) - min(all_prices)
                    }
                
                return {
                    'product_id': product_id,
                    'total_entries': len(comparisons),
                    'sources': list(history_by_source.keys()),
                    'price_statistics': stats,
                    'history_by_source': history_by_source
                }
                
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return {'error': str(e)}

# Global service instance
price_comparison_service = PriceComparisonService()
