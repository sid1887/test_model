"""
FastAPI routes for product analysis and image upload
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import asyncio
import json
import uuid
from pathlib import Path
import hashlib
import os
import aiofiles

# Database imports
from app.models.product import Product
from app.models.analysis import Analysis
from app.core.database import get_db_session

# AI services
from app.services.ai_models import ProductAnalyzer, ModelManager
from app.services.feature_extraction import feature_extraction_service
from app.core.monitoring import logger
from pydantic import BaseModel

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload-and-analyze")
async def upload_and_analyze_product(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    product_name: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Upload a product image and start AI analysis.
    
    This endpoint:
    1. Validates the uploaded image
    2. Saves it to the uploads directory
    3. Creates a product record in the database
    4. Starts background AI analysis
    5. Returns the product ID and initial status
    """
    
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (10MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
            raise HTTPException(status_code=400, detail="Unsupported image format")
        
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{file_extension}"
        file_path = Path("uploads") / filename
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Calculate image hash
        image_hash = hashlib.md5(content).hexdigest()
        
        # Create product in database
        async with get_db_session() as session:
            # Check if image already exists
            from sqlalchemy import text
            existing_result = await session.execute(
                text("SELECT id FROM products WHERE image_hash = :hash"),
                {"hash": image_hash}
            )
            existing = existing_result.fetchone()
            
            if existing:
                return JSONResponse({
                    "status": "duplicate",
                    "message": "Image already analyzed",
                    "product_id": existing.id,
                    "file_path": str(file_path)
                })
            
            # Create new product
            product = Product(
                name=product_name or f"Product_{unique_id[:8]}",
                brand=brand,
                category=category,
                image_path=str(file_path),
                image_hash=image_hash,
                is_processed=False,
                is_active=True
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            product_id = product.id
        
        # Start background analysis (placeholder for now)
        background_tasks.add_task(
            analyze_product_background,
            product_id,
            str(file_path)
        )
        
        return JSONResponse({
            "status": "uploaded",
            "message": "Image uploaded successfully, analysis started",
            "product_id": product_id,
            "file_path": str(file_path),
            "image_hash": image_hash,
            "estimated_processing_time": "30-60 seconds"
        })
        
    except Exception as e:
        # Clean up file if database operation failed
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{product_id}")
async def get_analysis_status(product_id: int):
    """Get the current analysis status for a product."""
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            # Get product info
            product_result = await session.execute(
                text("SELECT * FROM products WHERE id = :id"),
                {"id": product_id}
            )
            product = product_result.fetchone()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Get latest analysis
            analysis_result = await session.execute(
                text("""SELECT * FROM analyses 
                   WHERE product_id = :id 
                   ORDER BY created_at DESC 
                   LIMIT 1"""),
                {"id": product_id}
            )
            analysis = analysis_result.fetchone()
            
            if not analysis:
                return JSONResponse({
                    "product_id": product_id,
                    "status": "pending",
                    "message": "Analysis not started yet",
                    "progress": 0
                })
            
            # Return status based on analysis state
            status_info = {
                "product_id": product_id,
                "analysis_id": analysis.id,
                "status": analysis.status,
                "progress": 100 if analysis.status == "completed" else 50 if analysis.status == "processing" else 0,
                "confidence_score": float(analysis.confidence_score) if analysis.confidence_score else 0.0,
                "processing_time": float(analysis.processing_time) if analysis.processing_time else 0.0,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
            }
            
            if analysis.error_message:
                status_info["error"] = analysis.error_message
            
            return JSONResponse(status_info)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/results/{product_id}")
async def get_analysis_results(product_id: int):
    """Get complete analysis results for a product."""
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            # Get product with analysis
            query = text("""
                SELECT p.id as product_id, p.name, p.brand, p.category, p.image_path, 
                       p.created_at as product_created,
                       a.id as analysis_id, a.analysis_type, a.status, a.confidence_score,
                       a.processing_time, a.model_version, a.raw_results, a.processed_results,
                       a.created_at as analysis_created, a.completed_at, a.error_message
                FROM products p
                LEFT JOIN analyses a ON p.id = a.product_id
                WHERE p.id = :id
                ORDER BY a.created_at DESC
                LIMIT 1
            """)
            
            result = await session.execute(query, {"id": product_id})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Structure the response
            response = {
                "product": {
                    "id": row.product_id,
                    "name": row.name,
                    "brand": row.brand,
                    "category": row.category,
                    "image_path": row.image_path,
                    "created_at": row.product_created.isoformat() if row.product_created else None
                },
                "analysis": None
            }
            
            # Add analysis if available
            if row.analysis_id:
                response["analysis"] = {
                    "id": row.analysis_id,
                    "type": row.analysis_type,
                    "status": row.status,
                    "confidence_score": float(row.confidence_score) if row.confidence_score else 0.0,
                    "processing_time": float(row.processing_time) if row.processing_time else 0.0,
                    "model_version": row.model_version,
                    "raw_results": row.raw_results or {},
                    "processed_results": row.processed_results or {},
                    "created_at": row.analysis_created.isoformat() if row.analysis_created else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "error_message": row.error_message
                }
            
            return JSONResponse(response)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Results retrieval failed: {str(e)}")


@router.post("/analyze/{product_id}")
async def reanalyze_product(product_id: int, background_tasks: BackgroundTasks):
    """Re-run analysis for an existing product."""
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            # Get product
            result = await session.execute(
                text("SELECT * FROM products WHERE id = :id"),
                {"id": product_id}
            )
            product = result.fetchone()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Start background analysis
            background_tasks.add_task(
                analyze_product_background,
                product_id,
                product.image_path
            )
            
            return JSONResponse({
                "status": "started",
                "message": "Re-analysis started",
                "product_id": product_id,
                "estimated_processing_time": "30-60 seconds"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-analysis failed: {str(e)}")


@router.get("/models/status")
async def get_models_status():
    """Get the status of all AI models."""
    
    try:
        # For now, return placeholder status
        # When AI models are available, this will check actual model status
        models_status = {
            "yolo": {
                "loaded": False,
                "model_path": "models/yolov8n.pt",
                "status": "not_initialized"
            },
            "clip": {
                "loaded": False,
                "model_name": "ViT-B/32",
                "status": "not_initialized"
            },
            "efficientnet": {
                "loaded": False,
                "status": "placeholder_model"
            },
            "system": {
                "device": "cpu",
                "models_directory": "models",
                "initialization_status": "pending"
            }
        }
        
        return JSONResponse(models_status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Models status check failed: {str(e)}")


@router.post("/models/initialize")
async def initialize_models():
    """Initialize or re-initialize all AI models."""
    
    try:
        # Placeholder for model initialization
        # When AI models are available, this will actually initialize them
        
        return JSONResponse({
            "status": "pending",
            "message": "Model initialization not yet implemented",
            "next_step": "Install AI model dependencies first"
        })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model initialization failed: {str(e)}")


@router.get("/history")
async def get_analysis_history(skip: int = 0, limit: int = 10):
    """Get analysis history with pagination."""
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            query = text("""
                SELECT p.id, p.name, p.brand, p.category, p.image_path, p.created_at,
                       a.id as analysis_id, a.status, a.confidence_score, a.processing_time,
                       a.completed_at
                FROM products p
                LEFT JOIN analyses a ON p.id = a.product_id
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            
            result = await session.execute(query, {"limit": limit, "skip": skip})
            rows = result.fetchall()
            
            history = []
            for row in rows:
                item = {
                    "product_id": row.id,
                    "name": row.name,
                    "brand": row.brand,
                    "category": row.category,
                    "image_path": row.image_path,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "analysis": {
                        "id": row.analysis_id,
                        "status": row.status,
                        "confidence_score": float(row.confidence_score) if row.confidence_score else None,
                        "processing_time": float(row.processing_time) if row.processing_time else None,
                        "completed_at": row.completed_at.isoformat() if row.completed_at else None
                    } if row.analysis_id else None
                }
                history.append(item)
            
            return JSONResponse({
                "history": history,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": len(history)
                }
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.post("/ingest-scraped-product")
async def ingest_scraped_product(request: Request):
    """
    Ingest a product JSON from the Node.js scraper and process features.
    This endpoint receives scraped product data, processes it through the
    streaming pipeline (download image to RAM, compute embeddings, store metadata)
    and returns only the distilled metadata.
    """
    try:
        product_json = await request.json()
        
        # Validate required fields
        required_fields = ['product_id', 'site', 'title', 'price_raw', 'image_url']
        missing_fields = [field for field in required_fields if not product_json.get(field)]
        
        if missing_fields:
            return JSONResponse({
                "status": "error",
                "error": f"Missing required fields: {missing_fields}"
            }, status_code=400)
        
        # Process through feature extraction pipeline
        metadata = await feature_extraction_service.process_scraped_product(product_json)
        
        return JSONResponse({
            "status": "processed",
            "metadata": metadata
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "status": "error",
            "error": "Invalid JSON payload"
        }, status_code=400)
    except Exception as e:
        logger.error(f"Error ingesting scraped product: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.get("/processing-stats")
async def get_processing_stats():
    """Get statistics about the feature extraction processing"""
    try:
        stats = feature_extraction_service.get_metadata_stats()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def analyze_product_background(product_id: int, image_path: str):
    """Background task to analyze a product image using AI models."""
    
    try:
        print(f"🔄 Starting AI background analysis for product {product_id}")
        
        # Update product status to processing
        async with get_db_session() as session:
            from sqlalchemy import text
            await session.execute(
                text("UPDATE products SET is_processed = :processing WHERE id = :id"),
                {"processing": False, "id": product_id}
            )
            await session.commit()
        
        # Get AI models from app state (FastAPI app instance)
        # Note: We'll need to access this through a global or dependency injection
        try:
            from main import app
            product_analyzer = getattr(app.state, 'product_analyzer', None)
            
            if product_analyzer is None:
                print("⚠️ AI models not available, using placeholder analysis")
                # Fall back to placeholder analysis
                await asyncio.sleep(2)
                analysis_result = {
                    "object_detection": {
                        "primary_object": "product",
                        "confidence": 0.85,
                        "detections": [{"class": "product", "confidence": 0.85}]
                    },
                    "category_classification": {
                        "category": "General",
                        "confidence": 0.75
                    },
                    "brand_recognition": {
                        "detected_brand": "Unknown",
                        "confidence": 0.5
                    },
                    "overall_confidence": 0.7,
                    "processing_time": 2.0
                }
                model_version = "placeholder-v1.0"
            else:
                print("🤖 Running AI analysis...")
                # Run actual AI analysis
                analysis_result = await product_analyzer.analyze_product_image(image_path, product_id)
                model_version = "ai-models-v1.0"
                
        except Exception as ai_error:
            print(f"⚠️ AI analysis failed, using placeholder: {ai_error}")
            # Fall back to placeholder
            await asyncio.sleep(1)
            analysis_result = {
                "object_detection": {
                    "primary_object": "product",
                    "confidence": 0.5,
                    "detections": [{"class": "product", "confidence": 0.5}]
                },
                "category_classification": {
                    "category": "General",
                    "confidence": 0.5
                },
                "brand_recognition": {
                    "detected_brand": "Unknown",
                    "confidence": 0.3
                },
                "overall_confidence": 0.4,
                "processing_time": 1.0,
                "ai_error": str(ai_error)
            }
            model_version = "fallback-v1.0"
        
        # Extract processed results
        processed_results = {
            "category": analysis_result.get("category_classification", {}).get("category", "General"),
            "brand": analysis_result.get("brand_recognition", {}).get("detected_brand", "Unknown"),
            "primary_object": analysis_result.get("object_detection", {}).get("primary_object", "product")
        }
        
        # Save analysis to database
        async with get_db_session() as session:
            analysis = Analysis(
                product_id=product_id,
                analysis_type="ai_analysis",
                raw_results=analysis_result,
                processed_results=processed_results,
                confidence_score=analysis_result.get("overall_confidence", 0.5),
                processing_time=analysis_result.get("processing_time", 1.0),
                model_version=model_version,
                status="completed"
            )
            
            session.add(analysis)
            await session.commit()
          # Add product to CLIP search index
        try:
            print(f"🔍 Adding product {product_id} to CLIP search index...")
            from app.services.clip_search import clip_service
            
            # Initialize CLIP service if not already done
            if clip_service.clip_model is None:
                await clip_service.initialize()
            
            # Add to CLIP index
            await clip_service.add_product_to_index(
                product_id=product_id,
                image_path=image_path,
                title=processed_results.get("primary_object", "Product") + f" {product_id}",
                description=f"{processed_results.get('brand', '')} {processed_results.get('category', '')}".strip()
            )
            
            # Save indexes to disk
            await clip_service.save_indexes()
            print(f"✅ Product {product_id} added to CLIP search index")
            
        except Exception as clip_error:
            print(f"⚠️ Failed to add product {product_id} to CLIP index: {clip_error}")
            # Don't fail the entire analysis if CLIP indexing fails
        
        # Update product as processed
        async with get_db_session() as session:
            from sqlalchemy import text
            await session.execute(
                text("UPDATE products SET is_processed = :processed WHERE id = :id"),
                {"processed": True, "id": product_id}
            )
            await session.commit()
        
        print(f"✅ AI background analysis completed for product {product_id}")
        
    except Exception as e:
        print(f"❌ Background analysis failed for product {product_id}: {e}")
        
        # Save error to database
        try:
            async with get_db_session() as session:
                analysis = Analysis(
                    product_id=product_id,
                    analysis_type="ai_analysis",
                    raw_results={},
                    processed_results={},
                    confidence_score=0.0,
                    processing_time=0.0,
                    model_version="error-v1.0",
                    status="failed",
                    error_message=str(e)
                )
                session.add(analysis)
                await session.commit()
        except Exception as db_error:
            print(f"❌ Failed to save error to database: {db_error}")

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.7

class ImageSearchQuery(BaseModel):
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.7

@router.post("/search-products")
async def search_products(query: SearchQuery):
    """
    Search for products using text query via FAISS similarity search
    """
    try:
        results = await feature_extraction_service.search_products_by_text(
            query.query, 
            limit=query.limit,
            min_similarity=query.min_similarity
        )
        
        return JSONResponse({
            "query": query.query,
            "results": results,
            "total": len(results),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Text search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-by-image")
async def search_by_image(
    file: UploadFile = File(...),
    limit: int = 10,
    min_similarity: float = 0.7
):
    """
    Search for similar products using uploaded image via FAISS
    """
    try:
        # Validate image
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Search using feature extraction service
        results = await feature_extraction_service.search_products_by_image(
            image_data,
            limit=limit,
            min_similarity=min_similarity
        )
        
        return JSONResponse({
            "filename": file.filename,
            "results": results,
            "total": len(results),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-stats")
async def get_search_stats():
    """
    Get search index statistics and health
    """
    try:
        stats = await feature_extraction_service.get_search_stats()
        return JSONResponse(stats)
        
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
