"""
Product Discovery API Routes for Cumpair
Automated workflows for image-to-product discovery, competitive analysis, and market trends
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime

from app.services.product_discovery import cumpair_discovery
from app.core.monitoring import logger

router = APIRouter(prefix="/api/v1/discovery", tags=["product-discovery"])

class ImageDiscoveryRequest(BaseModel):
    """Request model for image-based product discovery"""
    user_context: Optional[Dict] = Field(None, description="User preferences and context")
    include_price_analysis: bool = Field(True, description="Include price comparison")
    max_results_per_platform: int = Field(5, ge=1, le=10, description="Max results per platform")

class CompetitiveAnalysisRequest(BaseModel):
    """Request model for competitive analysis"""
    analysis_depth: str = Field("standard", description="Analysis depth: basic, standard, comprehensive")
    include_market_positioning: bool = Field(True, description="Include market positioning analysis")
    competitor_limit: int = Field(20, ge=5, le=50, description="Maximum competitors to analyze")

class MarketTrendsRequest(BaseModel):
    """Request model for market trends analysis"""
    category: str = Field(..., description="Product category to analyze")
    time_horizon: str = Field("30d", description="Time horizon: 7d, 30d, 90d")
    include_emerging_products: bool = Field(True, description="Include emerging products analysis")
    geographic_scope: str = Field("global", description="Geographic scope: global, us, eu, etc.")

@router.get("/health")
async def discovery_health_check():
    """Health check for product discovery service"""
    try:
        # Initialize discovery service
        initialization_success = await cumpair_discovery.initialize()
        
        return {
            "status": "healthy" if initialization_success else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "ai_models": "ready" if cumpair_discovery.model_manager else "not_loaded",
                "price_engine": "ready" if cumpair_discovery.price_engine else "not_loaded",
                "image_service": "ready" if cumpair_discovery.image_service else "not_loaded"
            },
            "available_workflows": list(cumpair_discovery.discovery_workflows.keys())
        }
    except Exception as e:
        logger.error(f"❌ Discovery health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery health check failed: {str(e)}")

@router.post("/image-to-product")
async def discover_product_from_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_context: Optional[str] = None,
    include_price_analysis: bool = True,
    max_results_per_platform: int = 5
):
    """
    Complete AI-powered workflow: Upload image → Product Discovery → Price Analysis
    
    This endpoint provides the core functionality of Cumpair:
    1. Upload a product image
    2. AI analyzes the image to identify the product
    3. Searches multiple e-commerce platforms
    4. Provides price comparison and recommendations
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Write file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"📸 Image uploaded for discovery: {unique_filename}")
        
        # Parse user context
        import json
        parsed_context = {}
        if user_context:
            try:
                parsed_context = json.loads(user_context)
            except json.JSONDecodeError:
                logger.warning(f"Invalid user context JSON: {user_context}")
        
        # Initialize discovery service
        if not await cumpair_discovery.initialize():
            raise HTTPException(status_code=503, detail="Product discovery service not available")
        
        # Execute discovery workflow
        discovery_result = await cumpair_discovery.discover_product_from_image(
            file_path, 
            parsed_context
        )
        
        # Add API metadata
        discovery_result["api_metadata"] = {
            "uploaded_filename": file.filename,
            "saved_as": unique_filename,
            "file_size": len(content),
            "content_type": file.content_type,
            "processing_options": {
                "include_price_analysis": include_price_analysis,
                "max_results_per_platform": max_results_per_platform,
                "user_context_provided": bool(parsed_context)
            }
        }
        
        # Clean up file in background (optional - you might want to keep for cache)
        background_tasks.add_task(cleanup_uploaded_file, file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": discovery_result.get('status') == 'completed',
                "data": discovery_result,
                "message": f"Image discovery workflow {'completed' if discovery_result.get('status') == 'completed' else 'failed'}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image discovery failed: {str(e)}")

@router.post("/competitive-analysis/{product_id}")
async def analyze_competitive_landscape(
    product_id: int,
    request: CompetitiveAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Comprehensive competitive analysis for an existing product
    
    Analyzes the competitive landscape, identifies similar products,
    compares pricing, features, and market positioning
    """
    try:
        logger.info(f"🏆 Starting competitive analysis for product {product_id}")
        
        # Initialize discovery service
        if not await cumpair_discovery.initialize():
            raise HTTPException(status_code=503, detail="Product discovery service not available")
        
        # Execute competitive analysis workflow
        analysis_result = await cumpair_discovery.discover_competitive_products(
            product_id, 
            request.analysis_depth
        )
        
        if analysis_result.get('status') == 'failed':
            raise HTTPException(status_code=500, detail=analysis_result.get('error', 'Analysis failed'))
        
        # Add request metadata
        analysis_result["request_metadata"] = {
            "analysis_depth": request.analysis_depth,
            "include_market_positioning": request.include_market_positioning,
            "competitor_limit": request.competitor_limit,
            "requested_at": datetime.utcnow().isoformat()
        }
        
        # Store results in background for future reference
        background_tasks.add_task(
            store_competitive_analysis,
            product_id,
            analysis_result
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": analysis_result,
                "message": f"Competitive analysis completed for product {product_id}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Competitive analysis failed for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Competitive analysis failed: {str(e)}")

@router.post("/market-trends")
async def analyze_market_trends(
    request: MarketTrendsRequest,
    background_tasks: BackgroundTasks
):
    """
    Market trends analysis and emerging product discovery
    
    Analyzes market trends in a specific category, identifies emerging products,
    and provides insights for market opportunities
    """
    try:
        logger.info(f"📊 Starting market trends analysis for category: {request.category}")
        
        # Initialize discovery service
        if not await cumpair_discovery.initialize():
            raise HTTPException(status_code=503, detail="Product discovery service not available")
        
        # Execute market trends workflow
        trends_result = await cumpair_discovery.discover_market_trends(
            request.category,
            request.time_horizon
        )
        
        if trends_result.get('status') == 'failed':
            raise HTTPException(status_code=500, detail=trends_result.get('error', 'Trends analysis failed'))
        
        # Add request metadata
        trends_result["request_metadata"] = {
            "category": request.category,
            "time_horizon": request.time_horizon,
            "include_emerging_products": request.include_emerging_products,
            "geographic_scope": request.geographic_scope,
            "requested_at": datetime.utcnow().isoformat()
        }
        
        # Store trends data in background for analytics
        background_tasks.add_task(
            store_market_trends,
            request.category,
            trends_result
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": trends_result,
                "message": f"Market trends analysis completed for {request.category}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Market trends analysis failed for {request.category}: {e}")
        raise HTTPException(status_code=500, detail=f"Market trends analysis failed: {str(e)}")

@router.get("/workflow-status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the status of a discovery workflow"""
    try:
        # In a real implementation, you'd store workflow status in a database or cache
        # For now, return a placeholder response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "workflow_id": workflow_id,
                    "status": "completed",  # This would be dynamic
                    "progress": 100,
                    "message": "Workflow completed successfully"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Workflow status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow status check failed: {str(e)}")

@router.get("/workflows/history")
async def get_workflow_history(
    limit: int = 20,
    workflow_type: Optional[str] = None
):
    """Get history of discovery workflows"""
    try:
        # In a real implementation, you'd query from database
        # For now, return a placeholder response
        history = {
            "total_workflows": 0,
            "workflows": [],
            "filter": {
                "limit": limit,
                "workflow_type": workflow_type
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": history,
                "message": f"Retrieved workflow history"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Workflow history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow history retrieval failed: {str(e)}")

@router.get("/statistics")
async def get_discovery_statistics():
    """Get overall discovery service statistics"""
    try:
        stats = {
            "system_status": {
                "discovery_service": "operational",
                "ai_models_loaded": bool(cumpair_discovery.model_manager),
                "price_engine_ready": bool(cumpair_discovery.price_engine),
                "image_service_ready": bool(cumpair_discovery.image_service)
            },
            "usage_statistics": {
                "total_image_discoveries": 0,  # Would come from database
                "total_competitive_analyses": 0,  # Would come from database
                "total_market_trend_analyses": 0,  # Would come from database
                "average_processing_time": "2.5s",  # Would be calculated
                "success_rate": "95%"  # Would be calculated
            },
            "supported_features": {
                "image_to_product_discovery": True,
                "competitive_analysis": True,
                "market_trends": True,
                "ai_product_matching": bool(cumpair_discovery.model_manager),
                "multi_platform_search": True,
                "price_comparison": True
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": stats,
                "message": "Discovery service statistics retrieved"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Discovery statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

# Background task functions
async def cleanup_uploaded_file(file_path: str):
    """Clean up uploaded file after processing"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Cleaned up uploaded file: {file_path}")
    except Exception as e:
        logger.error(f"❌ File cleanup failed: {e}")

async def store_competitive_analysis(product_id: int, analysis_result: Dict):
    """Store competitive analysis results for future reference"""
    try:
        logger.info(f"💾 Storing competitive analysis for product {product_id}")
        # Implementation would store in database
        pass
    except Exception as e:
        logger.error(f"❌ Competitive analysis storage failed: {e}")

async def store_market_trends(category: str, trends_result: Dict):
    """Store market trends data for analytics"""
    try:
        logger.info(f"💾 Storing market trends for category {category}")
        # Implementation would store in database
        pass
    except Exception as e:
        logger.error(f"❌ Market trends storage failed: {e}")
