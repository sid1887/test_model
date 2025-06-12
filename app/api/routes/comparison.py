"""
Enhanced Price comparison API endpoints supporting 15+ retailers
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel, Field
import asyncio
import httpx
import json

from app.core.database import get_db
from app.models.product import Product
from app.models.price_comparison import PriceComparison
from app.services.price_comparison import price_comparison_service
from app.services.retailer_manager import retailer_manager, RetailerCategory, RetailerPriority
from app.worker import scrape_prices_task

router = APIRouter()

class RealTimeSearchRequest(BaseModel):
    """Request model for real-time price search"""
    query: str = Field(..., description="Product search query")
    sites: Optional[List[str]] = Field(default=None, description="List of sites to search (defaults to high-priority retailers)")
    category: Optional[str] = Field(default=None, description="Retailer category filter")
    max_retailers: Optional[int] = Field(default=8, description="Maximum number of retailers to search")

class RetailerFilterRequest(BaseModel):
    """Request model for filtered retailer search"""
    query: str = Field(..., description="Product search query")
    category: Optional[RetailerCategory] = Field(default=None, description="Retailer category")
    priority: Optional[RetailerPriority] = Field(default=None, description="Retailer priority level")
    include_specialty: bool = Field(default=True, description="Include specialty retailers")

@router.get("/compare/{product_id}")
async def get_price_comparison(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest price comparison results for a product
    
    Args:
        product_id: ID of the product
        db: Database session
        
    Returns:
        Price comparison results
    """
    # Check if product exists
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get price comparisons
    stmt = select(PriceComparison).where(
        PriceComparison.product_id == product_id,
        PriceComparison.is_valid == True
    ).order_by(PriceComparison.price.asc())
    
    result = await db.execute(stmt)
    comparisons = result.scalars().all()
    
    if not comparisons:
        return {
            "product_id": product_id,
            "message": "No price comparisons available",
            "suggestion": f"Use POST /api/v1/compare/{product_id}/refresh to start price scraping"
        }
    
    # Group by source
    results_by_source = {}
    all_prices = []
    
    for comparison in comparisons:
        source = comparison.source_name
        if source not in results_by_source:
            results_by_source[source] = []
        
        comparison_data = {
            "id": comparison.id,
            "title": comparison.title,
            "price": float(comparison.price) if comparison.price else 0,
            "currency": comparison.currency,
            "original_price": float(comparison.original_price) if comparison.original_price else None,
            "discount_percentage": float(comparison.discount_percentage) if comparison.discount_percentage else None,
            "in_stock": comparison.in_stock,
            "rating": float(comparison.rating) if comparison.rating else None,
            "review_count": comparison.review_count,
            "seller_name": comparison.seller_name,
            "scraped_at": comparison.scraped_at.isoformat() if comparison.scraped_at else None,
            "confidence_score": float(comparison.confidence_score) if comparison.confidence_score else None
        }
        
        results_by_source[source].append(comparison_data)
        if comparison.price:
            all_prices.append(float(comparison.price))
    
    # Calculate statistics
    stats = {}
    if all_prices:
        stats = {
            "min_price": min(all_prices),
            "max_price": max(all_prices),
            "avg_price": sum(all_prices) / len(all_prices),
            "price_range": max(all_prices) - min(all_prices),
            "total_results": len(all_prices)
        }
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "total_sources": len(results_by_source),
        "price_statistics": stats,
        "results_by_source": results_by_source,
        "best_deals": sorted(
            [comp for comps in results_by_source.values() for comp in comps],
            key=lambda x: x["price"]
        )[:5]  # Top 5 best deals
    }

@router.post("/compare/{product_id}/refresh")
async def refresh_price_comparison(
    product_id: int,
    search_queries: Optional[List[str]] = Query(None, description="Custom search queries"),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a fresh price comparison for a product
    
    Args:
        product_id: ID of the product
        search_queries: Optional custom search queries
        db: Database session
        
    Returns:
        Task information
    """
    # Check if product exists
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Generate search queries if not provided
    if not search_queries:
        search_queries = []
        
        # Use product name
        if product.name:
            search_queries.append(product.name)
        
        # Use brand and category if available
        if product.brand:
            search_queries.append(product.brand)
        
        if product.brand and product.name:
            search_queries.append(f"{product.brand} {product.name}")
        
        # Use specifications if available
        if product.specifications:
            specs = product.specifications
            if isinstance(specs, dict):
                for key, value in specs.items():
                    if isinstance(value, str) and len(value) > 3:
                        search_queries.append(value)
        
        # Ensure we have at least one query
        if not search_queries:
            search_queries = ["product"]
    
    # Limit search queries
    search_queries = search_queries[:5]
    
    # Start background task
    task = scrape_prices_task.delay(product_id, search_queries)
    
    return {
        "message": "Price comparison refresh started",
        "product_id": product_id,
        "task_id": task.id,
        "search_queries": search_queries,
        "estimated_time": "3-8 minutes"
    }

@router.get("/compare/{product_id}/history")
async def get_price_history(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get price history for a product
    
    Args:
        product_id: ID of the product
        db: Database session
        
    Returns:
        Price history data
    """
    # Check if product exists
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get price history using the service
    history = await price_comparison_service.get_price_history(product_id)
    
    if 'error' in history:
        raise HTTPException(status_code=500, detail=history['error'])
    
    return history

@router.get("/sources")
async def get_available_sources():
    """
    Get list of available price comparison sources
    
    Returns:
        List of supported platforms
    """
    return {
        "sources": list(price_comparison_service.platforms.keys()),
        "platform_details": {
            name: {
                "enabled": config["enabled"],
                "base_url": config["base_url"]
            }
            for name, config in price_comparison_service.platforms.items()
        }
    }

@router.get("/stats")
async def get_comparison_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall price comparison statistics
    
    Args:
        db: Database session
        
    Returns:
        System-wide statistics
    """
    try:
        # Total comparisons
        total_stmt = select(func.count(PriceComparison.id))
        total_result = await db.execute(total_stmt)
        total_comparisons = total_result.scalar() or 0
        
        # Comparisons by source
        source_stmt = select(
            PriceComparison.source_name,
            func.count(PriceComparison.id).label('count')
        ).group_by(PriceComparison.source_name)
        source_result = await db.execute(source_stmt)
        source_stats = {row.source_name: row.count for row in source_result}
        
        # Average confidence scores
        confidence_stmt = select(
            func.avg(PriceComparison.confidence_score).label('avg_confidence')
        ).where(PriceComparison.confidence_score.isnot(None))
        confidence_result = await db.execute(confidence_stmt)
        avg_confidence = confidence_result.scalar() or 0
        
        # Price ranges
        price_stmt = select(
            func.min(PriceComparison.price).label('min_price'),
            func.max(PriceComparison.price).label('max_price'),
            func.avg(PriceComparison.price).label('avg_price')
        ).where(PriceComparison.price > 0)
        price_result = await db.execute(price_stmt)
        price_stats = price_result.first()
        
        return {
            "total_comparisons": total_comparisons,
            "comparisons_by_source": source_stats,
            "average_confidence": float(avg_confidence),
            "price_statistics": {
                "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
                "max_price": float(price_stats.max_price) if price_stats.max_price else 0,
                "avg_price": float(price_stats.avg_price) if price_stats.avg_price else 0
            } if price_stats else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.delete("/compare/{product_id}")
async def delete_price_comparisons(
    product_id: int,
    source: Optional[str] = Query(None, description="Delete only from specific source"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete price comparison data for a product
    
    Args:
        product_id: ID of the product
        source: Optional source filter
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    stmt = select(PriceComparison).where(PriceComparison.product_id == product_id)
    
    if source:
        stmt = stmt.where(PriceComparison.source_name == source)
    
    result = await db.execute(stmt)
    comparisons = result.scalars().all()
    
    if not comparisons:
        raise HTTPException(
            status_code=404, 
            detail=f"No price comparisons found for product {product_id}" + 
                   (f" from source {source}" if source else "")
        )
    
    try:
        for comparison in comparisons:
            await db.delete(comparison)
        
        await db.commit()
        
        return {
            "message": f"Deleted {len(comparisons)} price comparisons",
            "product_id": product_id,
            "source": source
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.post("/real-time-search")
async def real_time_price_search(
    request: RealTimeSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform real-time price search across multiple e-commerce sites
    
    Args:
        request: Search request containing query and sites list
        db: Database session
          Returns:
        Real-time price comparison results
    """
    try:
        # Call Node.js scraper microservice
        scraper_url = "http://localhost:3000/api/search"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                scraper_url,
                json={"query": request.query, "sites": request.sites}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Scraper service error: {response.status_code}"
                )
            
            scraper_data = response.json()
            
        # Process and normalize results
        processed_results = []
        for result in scraper_data.get('results', []):
            # Extract numeric price
            price_text = result.get('price', '')
            try:
                # Remove currency symbols and extract number
                numeric_price = float(''.join(filter(str.isdigit or '.'.__eq__, price_text.replace(',', ''))))
            except (ValueError, TypeError):
                numeric_price = None
            
            processed_result = {
                'title': result.get('title', ''),
                'price_text': price_text,
                'price_numeric': numeric_price,
                'currency': 'USD',  # Default assumption
                'site': result.get('site', ''),
                'link': result.get('link', ''),
                'image_url': result.get('image', ''),
                'availability': 'in_stock',  # Default assumption
                'timestamp': scraper_data.get('metadata', {}).get('timestamp')
            }
            processed_results.append(processed_result)
        
        # Sort by price (cheapest first)
        valid_results = [r for r in processed_results if r['price_numeric'] is not None]
        valid_results.sort(key=lambda x: x['price_numeric'])
          # Calculate price statistics
        prices = [r['price_numeric'] for r in valid_results]
        price_stats = {}
        if prices:
            price_stats = {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'price_range': max(prices) - min(prices),
                'total_offers': len(prices)
            }
        
        return {
            'query': request.query,
            'results': processed_results,
            'valid_results': valid_results,
            'price_statistics': price_stats,
            'metadata': {
                'sites_searched': request.sites,
                'total_results': len(processed_results),
                'valid_price_results': len(valid_results),
                'search_timestamp': scraper_data.get('metadata', {}).get('timestamp'),
                'best_deal': valid_results[0] if valid_results else None
            }
        }
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail="Scraper service timeout - please try again"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503, 
            detail="Scraper service unavailable - please ensure it's running on port 3001"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Price search failed: {str(e)}"
        )

@router.post("/smart-search")
async def smart_price_search(
    query: Optional[str] = None,
    product_id: Optional[int] = None,
    include_similar: bool = True,
    sites: Optional[List[str]] = Query(default=["amazon", "walmart", "ebay"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Smart search that combines CLIP similarity with real-time price search
    
    Args:
        query: Text search query (optional if product_id provided)
        product_id: Existing product ID to search for (optional)
        include_similar: Whether to include similar products in search
        sites: List of sites to search
        db: Database session
        
    Returns:
        Smart search results with similarity and price data
    """
    try:
        search_queries = []
        
        # If product_id provided, get product details
        if product_id:
            stmt = select(Product).where(Product.id == product_id)
            result = await db.execute(stmt)
            product = result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Use product name as primary query
            search_queries.append(product.name)
            
            # Add brand + name combination
            if product.brand:
                search_queries.append(f"{product.brand} {product.name}")
        
        # Add explicit query if provided
        if query:
            search_queries.append(query)
        
        if not search_queries:
            raise HTTPException(
                status_code=400, 
                detail="Either query or product_id must be provided"
            )
          # Perform searches for all query variations
        all_results = []
        for search_query in search_queries:
            try:
                # Call Node.js scraper
                scraper_url = "http://localhost:3000/api/search"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        scraper_url,
                        json={"query": search_query, "sites": sites}
                    )
                    
                    if response.status_code == 200:
                        scraper_data = response.json()
                        results = scraper_data.get('results', [])
                        
                        # Add query context to results
                        for result in results:
                            result['search_query'] = search_query
                            result['query_type'] = 'exact' if search_query == query else 'derived'
                        
                        all_results.extend(results)
            
            except Exception as e:
                # Log error but continue with other queries
                continue
        
        # Remove duplicates (same link/title)
        seen_links = set()
        unique_results = []
        for result in all_results:
            link = result.get('link', '')
            title = result.get('title', '')
            identifier = f"{link}_{title}"
            
            if identifier not in seen_links:
                seen_links.add(identifier)
                unique_results.append(result)
        
        # Process and normalize prices
        processed_results = []
        for result in unique_results:
            price_text = result.get('price', '')
            try:
                # Extract numeric price
                numeric_price = float(''.join(filter(str.isdigit or '.'.__eq__, price_text.replace(',', ''))))
            except (ValueError, TypeError):
                numeric_price = None
            
            processed_result = {
                'title': result.get('title', ''),
                'price_text': price_text,
                'price_numeric': numeric_price,
                'currency': 'USD',
                'site': result.get('site', ''),
                'link': result.get('link', ''),
                'image_url': result.get('image', ''),
                'search_query': result.get('search_query', ''),
                'query_type': result.get('query_type', 'unknown')
            }
            processed_results.append(processed_result)
        
        # Sort by price and calculate statistics
        valid_results = [r for r in processed_results if r['price_numeric'] is not None]
        valid_results.sort(key=lambda x: x['price_numeric'])
        
        # Group by site for comparison
        site_best_deals = {}
        for result in valid_results:
            site = result['site']
            if site not in site_best_deals or result['price_numeric'] < site_best_deals[site]['price_numeric']:
                site_best_deals[site] = result
        
        # Price statistics
        prices = [r['price_numeric'] for r in valid_results]
        price_stats = {}
        if prices:
            price_stats = {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'median_price': sorted(prices)[len(prices)//2],
                'price_range': max(prices) - min(prices),
                'savings_potential': max(prices) - min(prices) if len(prices) > 1 else 0
            }
        
        return {
            'original_query': query,
            'product_id': product_id,
            'search_queries_used': search_queries,
            'all_results': processed_results,
            'valid_results': valid_results,
            'site_best_deals': site_best_deals,
            'price_statistics': price_stats,
            'recommendations': {
                'best_overall_deal': valid_results[0] if valid_results else None,
                'highest_savings': price_stats.get('savings_potential', 0),
                'recommended_sites': list(site_best_deals.keys())
            },
            'metadata': {
                'total_results': len(processed_results),
                'valid_price_results': len(valid_results),
                'sites_searched': sites,
                'search_timestamp': None  # Add timestamp
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Smart search failed: {str(e)}"
        )

@router.get("/retailers")
async def get_available_retailers():
    """
    Get list of all supported retailers with their status and categories
    
    Returns:
        List of retailer configurations
    """
    try:
        retailers = await retailer_manager.get_retailer_list_for_frontend()
        stats = await retailer_manager.get_retailer_performance_stats()
        
        return {
            "retailers": retailers,
            "statistics": stats,
            "total_retailers": len(retailers),
            "categories": {
                "general": [r for r in retailers if r['category'] == 'general'],
                "electronics": [r for r in retailers if r['category'] == 'electronics'],
                "fashion": [r for r in retailers if r['category'] == 'fashion'],
                "home_improvement": [r for r in retailers if r['category'] == 'home_improvement'],
                "wholesale": [r for r in retailers if r['category'] == 'wholesale'],
                "specialty": [r for r in retailers if r['category'] == 'specialty']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retailers: {str(e)}")

@router.post("/enhanced-search")
async def enhanced_retailer_search(
    request: RetailerFilterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced search using retailer filtering and prioritization
    
    Args:
        request: Enhanced search request with retailer filters
        db: Database session
        
    Returns:
        Filtered and prioritized search results
    """
    try:
        # Get filtered retailers
        active_retailers = await retailer_manager.get_active_retailers(
            category=request.category,
            priority=request.priority
        )
        
        if not active_retailers:
            raise HTTPException(
                status_code=400, 
                detail="No retailers match the specified criteria"
            )
        
        # Convert to site names for scraper
        sites = [retailer.domain.replace('.com', '') for retailer in active_retailers]
        
        # Call enhanced scraper service
        scraper_url = "http://localhost:3001/api/search"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                scraper_url,
                json={"query": request.query, "sites": sites}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Enhanced scraper service error: {response.status_code}"
                )
            
            scraper_data = response.json()
        
        # Process and enrich results with retailer metadata
        enhanced_results = []
        for result in scraper_data.get('results', []):
            site = result.get('site', '')
            retailer_config = await retailer_manager.get_retailer_config(site)
            
            if retailer_config:
                result['retailer_info'] = {
                    'name': retailer_config.name,
                    'category': retailer_config.category.value,
                    'priority': retailer_config.priority.value,
                    'base_url': retailer_config.base_url
                }
            
            enhanced_results.append(result)
        
        # Sort by retailer priority and price
        enhanced_results.sort(key=lambda x: (
            x.get('retailer_info', {}).get('priority', 3),
            float(''.join(filter(str.isdigit or '.'.__eq__, x.get('price', '999').replace(',', '')))) or 999
        ))
        
        return {
            'query': request.query,
            'results': enhanced_results,
            'search_metadata': {
                'retailers_searched': len(sites),
                'category_filter': request.category.value if request.category else None,
                'priority_filter': request.priority.value if request.priority else None,
                'total_results': len(enhanced_results),
                'retailers_used': sites,
                'timestamp': scraper_data.get('metadata', {}).get('timestamp')
            }
        }
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail="Enhanced scraper service timeout - please try again"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503, 
            detail="Enhanced scraper service unavailable - please ensure it's running on port 3001"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Enhanced search failed: {str(e)}"
        )

@router.get("/retailers/{retailer_key}/config")
async def get_retailer_config(retailer_key: str):
    """
    Get configuration details for a specific retailer
    
    Args:
        retailer_key: Retailer identifier
        
    Returns:
        Retailer configuration details
    """
    try:
        config = await retailer_manager.get_retailer_config(retailer_key)
        if not config:
            raise HTTPException(status_code=404, detail="Retailer not found")
        
        return {
            "retailer": config.to_dict(),
            "search_urls_example": await retailer_manager.generate_search_urls(
                retailer_key, "example product", pages=1
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retailer config: {str(e)}")

@router.post("/retailers/{retailer_key}/status")
async def update_retailer_status(
    retailer_key: str,
    status: str = Query(..., description="New status (active/inactive/maintenance)")
):
    """
    Update retailer status
    
    Args:
        retailer_key: Retailer identifier
        status: New status
        
    Returns:
        Update confirmation
    """
    try:
        if status not in ["active", "inactive", "maintenance"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        success = await retailer_manager.update_retailer_status(retailer_key, status)
        if not success:
            raise HTTPException(status_code=404, detail="Retailer not found")
        
        return {
            "message": f"Retailer {retailer_key} status updated to {status}",
            "retailer_key": retailer_key,
            "new_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update retailer status: {str(e)}")
