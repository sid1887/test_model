"""
Enhanced Price Comparison API Routes for Cumpair
Integrates web scraping, AI-powered analysis, and intelligent product matching
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.price_comparison import cumpair_price_engine
from app.services.scraping import scraper_client
from app.models.product import Product
from app.models.price_comparison import PriceComparison
from app.core.monitoring import logger

router = APIRouter(prefix="/api/v1/price-comparison", tags=["price-comparison"])

class PriceSearchRequest(BaseModel):
    """Request model for price search"""
    query: str = Field(..., description="Product search query")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results per site")
    include_ai_insights: bool = Field(True, description="Include AI-powered insights")

class ProductPriceCompareRequest(BaseModel):
    """Request model for product price comparison"""
    product_id: int = Field(..., description="Product ID to compare")
    custom_query: Optional[str] = Field(None, description="Custom search query override")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results per site")

class BatchPriceSearchRequest(BaseModel):
    """Request model for batch price search"""
    queries: List[str] = Field(..., description="List of product queries")
    max_results_per_query: int = Field(5, ge=1, le=20, description="Max results per query")

@router.get("/health")
async def health_check():
    """Health check for price comparison service"""
    try:
        # Check scraper service connectivity
        scraper_stats = await scraper_client.get_stats()
        
        # Check price engine status
        engine_initialized = await cumpair_price_engine.initialize()
        
        return {
            "status": "healthy" if engine_initialized else "degraded",
            "timestamp": "2025-06-04T15:20:00Z",
            "services": {
                "scraper_service": {
                    "status": "connected" if scraper_stats else "disconnected",
                    "stats": scraper_stats
                },
                "ai_engine": {
                    "status": "ready" if engine_initialized else "error",
                    "clip_model": "loaded" if cumpair_price_engine.clip_model else "not_loaded"
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Price comparison health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/search")
async def search_product_prices(
    request: PriceSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Search for product prices across multiple e-commerce sites
    with AI-powered analysis and insights
    """
    try:
        logger.info(f"🔍 Starting price search for: {request.query}")
        
        # Initialize price engine if needed
        if not await cumpair_price_engine.initialize():
            raise HTTPException(status_code=503, detail="Price comparison engine not available")
        
        # Execute price search
        results = await cumpair_price_engine.find_product_prices(
            request.query, 
            max_results=request.max_results
        )
        
        # Add metadata
        results["search_metadata"] = {
            "requested_by": "api",
            "max_results_requested": request.max_results,
            "ai_insights_included": request.include_ai_insights,
            "search_id": f"search_{hash(request.query)}_{int(results.get('timestamp', '0').replace('-', '').replace(':', '').replace('T', '').replace('Z', ''))}"
        }
        
        # Store search results in background for analytics
        background_tasks.add_task(
            store_search_analytics, 
            request.query, 
            results, 
            db
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": results,
                "message": f"Found {results.get('total_results', 0)} price listings"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Price search failed for '{request.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Price search failed: {str(e)}")

@router.post("/compare/{product_id}")
async def compare_product_prices(
    product_id: int,
    request: ProductPriceCompareRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Compare prices for an existing product with AI-enhanced analysis
    """
    try:
        logger.info(f"🔍 Starting AI price comparison for product {product_id}")
        
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Initialize price engine
        if not await cumpair_price_engine.initialize():
            raise HTTPException(status_code=503, detail="Price comparison engine not available")
        
        # Execute AI-powered comparison
        comparison_results = await cumpair_price_engine.compare_product_with_ai(
            product_id, 
            request.custom_query
        )
        
        if "error" in comparison_results:
            raise HTTPException(status_code=500, detail=comparison_results["error"])
        
        # Add API metadata
        comparison_results["api_metadata"] = {
            "comparison_type": "ai_enhanced",
            "product_id": product_id,
            "custom_query_used": bool(request.custom_query),
            "timestamp": comparison_results.get("price_comparison", {}).get("timestamp")
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": comparison_results,
                "message": f"AI comparison completed for product {product_id}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Product comparison failed for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Product comparison failed: {str(e)}")

@router.post("/batch-search")
async def batch_price_search(
    request: BatchPriceSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Batch price search for multiple products with concurrent processing
    """
    try:
        if len(request.queries) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 queries allowed per batch")
        
        logger.info(f"🔍 Starting batch price search for {len(request.queries)} products")
        
        # Initialize price engine
        if not await cumpair_price_engine.initialize():
            raise HTTPException(status_code=503, detail="Price comparison engine not available")
        
        # Execute batch searches concurrently
        import asyncio
        search_tasks = [
            cumpair_price_engine.find_product_prices(query, request.max_results_per_query)
            for query in request.queries
        ]
        
        batch_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        successful_searches = 0
        
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                processed_results.append({
                    "query": request.queries[i],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append({
                    "query": request.queries[i],
                    "status": "success",
                    "data": result
                })
                successful_searches += 1
        
        response_data = {
            "batch_metadata": {
                "total_queries": len(request.queries),
                "successful_searches": successful_searches,
                "failed_searches": len(request.queries) - successful_searches,
                "timestamp": "2025-06-04T15:20:00Z"
            },
            "results": processed_results
        }
        
        # Store batch analytics in background
        background_tasks.add_task(
            store_batch_analytics,
            request.queries,
            processed_results,
            db
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": response_data,
                "message": f"Batch search completed: {successful_searches}/{len(request.queries)} successful"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Batch price search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")

@router.get("/history/{product_id}")
async def get_price_history(
    product_id: int,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """Get price comparison history for a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Get price comparison history
        comparisons = db.query(PriceComparison)\
            .filter(PriceComparison.product_id == product_id)\
            .order_by(PriceComparison.created_at.desc())\
            .limit(limit)\
            .all()
        
        history_data = []
        for comparison in comparisons:
            history_data.append({
                "id": comparison.id,
                "search_query": comparison.search_query,
                "total_results": comparison.total_results,
                "price_range": {
                    "min": comparison.price_range_min,
                    "max": comparison.price_range_max
                },
                "created_at": comparison.created_at.isoformat(),
                "ai_insights": comparison.ai_insights_json
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "product_id": product_id,
                    "product_name": product.name,
                    "history_count": len(history_data),
                    "history": history_data
                },
                "message": f"Retrieved {len(history_data)} price comparison records"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Price history retrieval failed for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.get("/stats")
async def get_price_comparison_stats(db: Session = Depends(get_db)):
    """Get overall price comparison statistics"""
    try:
        # Get scraper stats
        scraper_stats = await scraper_client.get_stats()
        
        # Get database stats
        total_comparisons = db.query(PriceComparison).count()
        recent_comparisons = db.query(PriceComparison)\
            .filter(PriceComparison.created_at >= "2025-06-04")\
            .count()
        
        stats = {
            "system_stats": {
                "total_price_comparisons": total_comparisons,
                "recent_comparisons_today": recent_comparisons,
                "scraper_service": scraper_stats
            },
            "engine_status": {
                "ai_engine_initialized": bool(cumpair_price_engine.clip_model),
                "supported_sites": list(cumpair_price_engine.ecommerce_sites.keys()),
                "similarity_threshold": cumpair_price_engine.similarity_threshold
            },
            "performance_metrics": {
                "average_response_time": scraper_stats.get("averageResponseTime", 0),
                "success_rate": f"{scraper_stats.get('successRate', 0)}%",
                "total_requests": scraper_stats.get("totalRequests", 0)
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": stats,
                "message": "Price comparison statistics retrieved"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Background task functions
async def store_search_analytics(query: str, results: Dict, db: Session):
    """Store search analytics for future insights"""
    try:
        # This could be expanded to store detailed analytics
        logger.info(f"📊 Storing analytics for search: {query}")
        # Implementation for analytics storage
        pass
    except Exception as e:
        logger.error(f"❌ Analytics storage failed: {e}")

async def store_batch_analytics(queries: List[str], results: List[Dict], db: Session):
    """Store batch search analytics"""
    try:
        logger.info(f"📊 Storing batch analytics for {len(queries)} queries")
        # Implementation for batch analytics storage
        pass
    except Exception as e:
        logger.error(f"❌ Batch analytics storage failed: {e}")
