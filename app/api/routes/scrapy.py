"""
Scrapy Service Integration Routes
Provides access to advanced scraping capabilities with 17+ retailers
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.services.scraping import scrapy_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scrapy", tags=["Scrapy Service"])


# Request/Response Models
class SearchRequest(BaseModel):
    """Product search request"""
    query: str
    retailers: Optional[List[str]] = None
    max_results: Optional[int] = 10


class BulkSearchRequest(BaseModel):
    """Bulk search request"""
    queries: List[str]
    retailers: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """Search response"""
    status: str
    query: Optional[str] = None
    sites_queued: Optional[int] = 0
    message: Optional[str] = None
    timestamp: Optional[str] = None


class BulkSearchResponse(BaseModel):
    """Bulk search response"""
    status: str
    batch_id: str
    jobs_queued: int
    queries_count: int
    retailers_count: int
    message: str
    timestamp: str


# Endpoints
@router.get("/health")
async def health_check():
    """
    Check Scrapy service health
    
    Returns service status and capabilities
    """
    try:
        await scrapy_client.initialize()
        
        if not scrapy_client.available:
            return {
                "status": "unavailable",
                "message": "Scrapy service is not available",
                "retailers_supported": 0
            }
        
        stats = await scrapy_client.get_stats()
        
        return {
            "status": "healthy",
            "message": "Scrapy service is operational",
            "retailers_supported": len(scrapy_client.supported_retailers),
            "retailers": scrapy_client.supported_retailers,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retailers")
async def get_supported_retailers():
    """
    Get list of supported retailers
    
    Returns all 17+ supported e-commerce platforms
    """
    try:
        await scrapy_client.initialize()
        
        return {
            "retailers": scrapy_client.supported_retailers,
            "total": len(scrapy_client.supported_retailers),
            "categories": {
                "major_us": ["amazon", "walmart", "target", "bestbuy", "ebay"],
                "home_improvement": ["homedepot", "lowes"],
                "department_stores": ["macys", "nordstrom", "costco"],
                "specialty": ["newegg", "bhphotovideo"],
                "furniture": ["wayfair", "overstock"],
                "fashion": ["zappos"],
                "international": ["flipkart", "aliexpress"]
            }
        }
    except Exception as e:
        logger.error(f"Get retailers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """
    Search for products across multiple retailers
    
    - **query**: Search query (e.g., "laptop", "wireless headphones")
    - **retailers**: Optional list of retailer names (defaults to top 10)
    - **max_results**: Maximum results per retailer (default 10)
    
    Returns queued job information. Results available via batch status endpoint.
    """
    try:
        result = await scrapy_client.search(
            query=request.query,
            retailers=request.retailers,
            max_results=request.max_results
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/voice")
async def voice_search(audio: UploadFile = File(...)):
    """
    Voice-based product search using speech-to-text
    
    - **audio**: Audio file (WAV, MP3, etc.)
    
    Transcribes audio to text and performs product search.
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = await scrapy_client.voice_search(tmp_path)
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/image")
async def image_search(image: UploadFile = File(...)):
    """
    Image-based product search using CLIP analysis
    
    - **image**: Product image file (JPG, PNG, etc.)
    
    Analyzes image with CLIP and performs product search.
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = await scrapy_client.image_search(tmp_path)
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/bulk", response_model=BulkSearchResponse)
async def bulk_search(request: BulkSearchRequest):
    """
    Bulk search across multiple queries and retailers
    
    - **queries**: List of search queries
    - **retailers**: Optional list of retailer names (defaults to all 17+)
    
    Creates a batch job for parallel processing. Use batch status endpoint to track progress.
    """
    try:
        result = await scrapy_client.bulk_search(
            queries=request.queries,
            retailers=request.retailers
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Get status of a bulk search batch
    
    - **batch_id**: Batch identifier from bulk search response
    
    Returns batch progress, completed jobs, and results count.
    """
    try:
        result = await scrapy_client.get_batch_status(batch_id)
        
        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail="Batch not found")
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    Get comprehensive Scrapy service statistics
    
    Returns scraping stats, retailer performance, and service health.
    """
    try:
        result = await scrapy_client.get_stats()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
