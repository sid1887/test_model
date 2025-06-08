"""
FastAPI routes for product analysis and image upload
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import uuid
import os
import shutil
from pathlib import Path
import aiofiles
from datetime import datetime
import hashlib

# Database imports
from app.models.product import Product
from app.models.analysis import Analysis
from app.core.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# AI services
from app.services.ai_models import product_analyzer, model_manager
import asyncio

from app.core.database import get_db
from app.core.config import settings
from app.core.monitoring import logger
from app.models.product import Product
from app.models.analysis import Analysis
from app.worker import analyze_image_task, full_product_analysis_task
from app.services.clip_search import clip_service

router = APIRouter()

# Request models
class TextSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10

@router.post("/analyze")
async def analyze_product_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    full_analysis: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and analyze a product image
    
    Args:
        file: Image file to analyze
        full_analysis: Whether to include price comparison
        db: Database session
        
    Returns:
        Analysis task information and initial results
    """
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size
    file_size = 0
    chunk_size = 1024
    temp_file_path = None
    
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed"
            )
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        upload_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > settings.max_file_size:
                    os.remove(upload_path)
                    raise HTTPException(
                        status_code=413, 
                        detail="File too large"
                    )
                buffer.write(chunk)
        
        # Create product record
        product = Product(
            name=f"Product from {file.filename}",
            image_path=upload_path,
            is_processed=False
        )
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        # Start background analysis
        if full_analysis:
            task = full_product_analysis_task.delay(upload_path, product.id)
        else:
            task = analyze_image_task.delay(upload_path, product.id)
        
        return {
            "message": "Image uploaded successfully",
            "product_id": product.id,
            "task_id": task.id,
            "status": "processing",
            "full_analysis": full_analysis,
            "estimated_time": "2-5 minutes" if full_analysis else "30-60 seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if something went wrong
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/analyze/{product_id}")
async def get_analysis_result(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis results for a product
    
    Args:
        product_id: ID of the product
        db: Database session
        
    Returns:
        Analysis results
    """
    # Get product
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get latest analysis
    stmt = select(Analysis).where(
        Analysis.product_id == product_id
    ).order_by(Analysis.created_at.desc())
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        return {
            "product_id": product_id,
            "status": "pending",
            "message": "Analysis not yet started"
        }
    
    response = {
        "product_id": product_id,
        "status": analysis.status,
        "analysis_type": analysis.analysis_type,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }
    
    if analysis.status == "completed":
        response["results"] = analysis.processed_results or analysis.raw_results
        response["confidence_score"] = float(analysis.confidence_score) if analysis.confidence_score else None
        response["processing_time"] = float(analysis.processing_time) if analysis.processing_time else None
    elif analysis.status == "failed":
        response["error"] = analysis.error_message
    
    return response

@router.get("/analyze/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status and results
    """
    try:
        from app.worker import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'status': 'pending',
                'message': 'Task is waiting to be processed'
            }
        elif result.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'status': 'processing',
                'progress': result.info.get('progress', 0),
                'message': result.info.get('message', 'Processing...')
            }
        elif result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'status': 'completed',
                'result': result.result
            }
        else:  # FAILURE
            response = {
                'task_id': task_id,
                'status': 'failed',
                'error': str(result.info)
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.delete("/analyze/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a product and its analysis results
    
    Args:
        product_id: ID of the product to delete
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    # Get product
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        # Delete image file
        if product.image_path and os.path.exists(product.image_path):
            os.remove(product.image_path)
        
        # Delete from database (cascading will handle related records)
        await db.delete(product)
        await db.commit()
        
        return {
            "message": f"Product {product_id} deleted successfully"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 10,
    processed_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List products with pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        processed_only: Only return processed products
        db: Database session
        
    Returns:
        List of products
    """
    stmt = select(Product)
    
    if processed_only:
        stmt = stmt.where(Product.is_processed == True)
    
    stmt = stmt.offset(skip).limit(limit).order_by(Product.created_at.desc())
    
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return {
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "is_processed": product.is_processed,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "specifications": product.specifications
            }
            for product in products
        ],
        "total": len(products),
        "skip": skip,
        "limit": limit
    }

@router.post("/search-by-image")
async def search_products_by_image(
    file: UploadFile = File(...),
    top_k: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for similar products using image upload (CLIP-based)
    
    Args:
        file: Image file to search with
        top_k: Number of results to return
        db: Database session
          Returns:
        List of similar products with similarity scores
    """
    # Validate file
    if not file or not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save uploaded file temporarily
        file_extension = os.path.splitext(file.filename)[1]
        temp_filename = f"search_{uuid.uuid4()}{file_extension}"
        temp_file_path = os.path.join(settings.upload_dir, temp_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Save file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize CLIP service if not already done
        if clip_service.clip_model is None:
            await clip_service.initialize()
        
        # Perform image search
        search_results = await clip_service.search_by_image(
            temp_file_path, top_k=top_k
        )
        
        # Enhance results with database information
        enhanced_results = []
        for result in search_results:
            # Get full product details from database
            stmt = select(Product).where(Product.id == result['product_id'])
            db_result = await db.execute(stmt)
            product = db_result.scalar_one_or_none()
            
            if product:
                enhanced_result = {
                    'product_id': product.id,
                    'title': product.name,
                    'brand': product.brand,
                    'category': product.category,
                    'specifications': product.specifications,
                    'similarity_score': result['similarity_score'],
                    'image_path': result['image_path'],
                    'detection_confidence': float(product.detection_confidence) if product.detection_confidence else None
                }
                enhanced_results.append(enhanced_result)
        
        return {
            'query_type': 'image',
            'results': enhanced_results,
            'total_results': len(enhanced_results),
            'search_metadata': {
                'model_used': 'CLIP',
                'top_k': top_k
            }
        }
        
    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/search-by-text")
async def search_products_by_text(
    request: TextSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for products using text query (CLIP-based)
    
    Args:
        request: Text search request containing query and top_k
        db: Database session
        
    Returns:
        List of matching products with similarity scores
    """
    try:
        # Initialize CLIP service if not already done
        if clip_service.clip_model is None:
            await clip_service.initialize()
        
        # Perform text search
        search_results = await clip_service.search_by_text(request.query, top_k=request.top_k)
        
        # Enhance results with database information
        enhanced_results = []
        for result in search_results:
            # Get full product details from database
            stmt = select(Product).where(Product.id == result['product_id'])
            db_result = await db.execute(stmt)
            product = db_result.scalar_one_or_none()
            
            if product:
                enhanced_result = {
                    'product_id': product.id,
                    'title': product.name,
                    'brand': product.brand,
                    'category': product.category,
                    'specifications': product.specifications,
                    'similarity_score': result['similarity_score'],
                    'image_path': result['image_path'],                    'detection_confidence': float(product.detection_confidence) if product.detection_confidence else None
                }
                enhanced_results.append(enhanced_result)
        
        return {
            'query_type': 'text',
            'query': request.query,
            'results': enhanced_results,
            'total_results': len(enhanced_results),
            'search_metadata': {
                'model_used': 'CLIP',
                'top_k': request.top_k
            }
        }
        
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")

@router.post("/hybrid-search")
async def hybrid_search_products(
    query: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    top_k: int = 10,
    text_weight: float = 0.5,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform hybrid text + image search for products
    
    Args:
        query: Text search query (optional)
        file: Image file to search with (optional)
        top_k: Number of results to return
        text_weight: Weight for text vs image search (0.0-1.0)
        db: Database session
        
    Returns:
        List of matching products with combined similarity scores
    """
    if not query and not file:
        raise HTTPException(
            status_code=400, 
            detail="At least one of query or file must be provided"
        )
    
    temp_file_path = None
    
    try:        # Handle image file if provided
        if file:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # Save uploaded file temporarily
            file_extension = os.path.splitext(file.filename)[1]
            temp_filename = f"hybrid_search_{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(settings.upload_dir, temp_filename)
            
            # Ensure upload directory exists
            os.makedirs(settings.upload_dir, exist_ok=True)
            
            # Save file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # Initialize CLIP service if not already done
        if clip_service.clip_model is None:
            await clip_service.initialize()
        
        # Perform hybrid search
        search_results = await clip_service.hybrid_search(
            query_text=query,
            query_image_path=temp_file_path,
            top_k=top_k,
            text_weight=text_weight
        )
        
        # Enhance results with database information
        enhanced_results = []
        for result in search_results:
            # Get full product details from database
            stmt = select(Product).where(Product.id == result['product_id'])
            db_result = await db.execute(stmt)
            product = db_result.scalar_one_or_none()
            
            if product:
                enhanced_result = {
                    'product_id': product.id,
                    'title': product.name,
                    'brand': product.brand,
                    'category': product.category,
                    'specifications': product.specifications,
                    'hybrid_score': result['hybrid_score'],
                    'text_component': result['text_component'],
                    'image_component': result['image_component'],
                    'image_path': result['image_path'],
                    'detection_confidence': float(product.detection_confidence) if product.detection_confidence else None
                }
                enhanced_results.append(enhanced_result)
        
        return {
            'query_type': 'hybrid',
            'text_query': query,
            'has_image': file is not None,
            'results': enhanced_results,
            'total_results': len(enhanced_results),
            'search_metadata': {
                'model_used': 'CLIP',
                'top_k': top_k,
                'text_weight': text_weight,
                'image_weight': 1 - text_weight
            }
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
