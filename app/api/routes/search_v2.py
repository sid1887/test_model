"""
Complete Search API v2 - God-Powered Comparison Engine
Combines: Query optimization, AI analysis, real-time feeds, scraper, cache
Target: <200ms cached, <2s fresh, full context enrichment
"""

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import asyncio
import json
import time

from app.core.database import get_db
from app.core.metrics import metrics
from app.services.query_optimizer import query_optimizer
from app.services.huggingface_client import hf_client
from app.services.realtime_feeds import realtime_feeds
from app.services.clip_search import clip_service
from app.services.image_processor import get_image_processor
from app.core.events import (
    emit_scrape_requested,
    emit_image_uploaded,
    emit_search_executed
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["Search V2 - God Engine"])


@router.get("/search")
async def unified_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    use_cache: bool = Query(default=True),
    use_vector: bool = Query(default=True),
    enrich: bool = Query(default=True, description="Add AI analysis & real-time data"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔥 UNIFIED SEARCH - The God Engine
    
    Combines:
    - Multi-tier cache (L1/L2)
    - FAISS vector search
    - Database optimization
    - HuggingFace AI analysis
    - Real-time stock/crypto/news feeds
    - Background scraper trigger
    
    Target: <200ms cached, <2s fresh
    """
    start_time = time.time()
    metrics.user_searches.labels(search_type="unified").inc()
    
    # Step 1: Query optimizer (cache-first, vector, DB)
    search_results = await query_optimizer.search_products(
        query=q,
        db=db,
        limit=limit,
        use_cache=use_cache,
        use_vector_search=use_vector
    )
    
    products = search_results["results"]
    metadata = search_results["metadata"]
    
    # Step 2: AI enrichment (parallel)
    if enrich and products:
        enrichment_tasks = {
            "query_analysis": hf_client.enhance_product_description(q),
            "realtime_context": realtime_feeds.get_product_context(q)
        }
        
        enrichment = await asyncio.gather(
            *enrichment_tasks.values(),
            return_exceptions=True
        )
        
        for key, result in zip(enrichment_tasks.keys(), enrichment):
            if not isinstance(result, Exception):
                metadata[key] = result
    
    # Step 3: Emit analytics event
    await emit_search_executed(
        query=q,
        results_count=len(products),
        cache_hit=metadata.get("cache_hit", False),
        latency_ms=metadata.get("latency_ms", 0)
    )
    
    total_latency = (time.time() - start_time) * 1000
    
    return {
        "query": q,
        "results": products,
        "metadata": {
            **metadata,
            "total_latency_ms": total_latency,
            "enriched": enrich,
            "timestamp": time.time()
        }
    }


@router.get("/search/stream")
async def streaming_search(
    q: str = Query(...),
    limit: int = Query(default=20),
    db: AsyncSession = Depends(get_db)
):
    """
    SSE Streaming Search - Ghost results → Real results
    Returns instant placeholders, then morphs to real data
    """
    async def event_generator():
        # Phase 1: Ghost results (instant)
        ghost_results = await query_optimizer.get_ghost_results(q, count=5)
        yield f"data: {json.dumps({'phase': 'ghost', 'results': ghost_results})}\n\n"
        
        # Phase 2: Real search (background)
        search_results = await query_optimizer.search_products(q, db, limit)
        yield f"data: {json.dumps({'phase': 'real', 'results': search_results['results']})}\n\n"
        
        # Phase 3: AI enrichment (optional)
        enrichment = await hf_client.enhance_product_description(q)
        yield f"data: {json.dumps({'phase': 'enriched', 'analysis': enrichment})}\n\n"
        
        # Phase 4: Real-time data (optional)
        realtime = await realtime_feeds.get_product_context(q)
        yield f"data: {json.dumps({'phase': 'realtime', 'context': realtime})}\n\n"
        
        # Done
        yield f"data: {json.dumps({'phase': 'complete'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/search/image")
async def image_search_v2(
    file: UploadFile = File(...),
    limit: int = Query(default=20),
    enrich: bool = Query(default=True),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    🖼️ Image Search V2 with full AI pipeline
    
    Flow:
    1. Upload image
    2. CLIP visual search
    3. Barcode detection
    4. OCR fallback
    5. HuggingFace image classification
    6. Real-time enrichment
    7. Scraper trigger
    """
    start_time = time.time()
    
    # Save image
    import uuid
    import os
    import shutil
    
    image_id = str(uuid.uuid4())
    upload_dir = "uploads/search_images"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    file_path = os.path.join(upload_dir, f"{image_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Emit event
    request_id = f"img-v2-{image_id[:8]}"
    await emit_image_uploaded(image_id, file_path, request_id)
    
    # Parallel AI analysis
    processor = await get_image_processor()
    
    analysis_tasks = {
        "clip": clip_service.search_by_image(file_path, top_k=limit),
        "barcode": processor._detect_barcodes(file_path),
        "ocr": processor._extract_text(file_path),
        "classification": hf_client.classify_image(f"file://{file_path}") if enrich else None
    }
    
    results = await asyncio.gather(
        *[task for task in analysis_tasks.values() if task],
        return_exceptions=True
    )
    
    analysis = {}
    for key, result in zip(analysis_tasks.keys(), results):
        if not isinstance(result, Exception):
            analysis[key] = result
        else:
            logger.error(f"{key} analysis failed: {result}")
            analysis[key] = None
    
    # Determine search query
    search_query = None
    detection_method = None
    
    if analysis.get("barcode") and len(analysis["barcode"]) > 0:
        search_query = analysis["barcode"][0]["data"]
        detection_method = "barcode"
    elif analysis.get("clip") and len(analysis["clip"]) > 0:
        # Get product from CLIP match
        top_match = analysis["clip"][0]
        search_query = top_match.get("name", "")
        detection_method = "clip"
    elif analysis.get("ocr") and len(analysis["ocr"]) > 5:
        search_query = analysis["ocr"][:100]
        detection_method = "ocr"
    
    if not search_query:
        return {
            "status": "no_detection",
            "message": "Could not identify product from image",
            "analysis": analysis,
            "latency_ms": (time.time() - start_time) * 1000
        }
    
    # Search with detected query
    search_results = await query_optimizer.search_products(
        search_query,
        db,
        limit=limit
    )
    
    # Trigger background scraper
    background_tasks.add_task(
        emit_scrape_requested,
        query=search_query,
        sites=["amazon", "walmart", "ebay"],
        max_results=limit,
        request_id=request_id,
        priority=9
    )
    
    # Real-time enrichment
    enrichment = None
    if enrich:
        enrichment = await realtime_feeds.get_product_context(search_query)
    
    return {
        "status": "success",
        "image_id": image_id,
        "detection": {
            "query": search_query,
            "method": detection_method,
            "confidence": analysis.get("clip", [{}])[0].get("similarity", 0.8) if detection_method == "clip" else 1.0
        },
        "analysis": analysis,
        "results": search_results["results"],
        "enrichment": enrichment,
        "metadata": {
            **search_results["metadata"],
            "total_latency_ms": (time.time() - start_time) * 1000
        }
    }


@router.post("/search/voice")
async def voice_search(
    audio: UploadFile = File(...),
    limit: int = Query(default=20),
    db: AsyncSession = Depends(get_db)
):
    """
    🎤 Voice Search with STT + AI
    
    Flow:
    1. Upload audio
    2. Whisper STT transcription
    3. HuggingFace NER extraction
    4. Search with entities
    5. Real-time enrichment
    """
    # TODO: Implement voice STT integration
    raise HTTPException(status_code=501, detail="Voice search coming soon")


@router.get("/product/{product_id}/complete")
async def get_complete_product_context(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    🔥 Complete Product Context
    
    Returns EVERYTHING:
    - Product details
    - Price history
    - AI sentiment analysis
    - Related stocks
    - Crypto correlation (if applicable)
    - Latest news
    - Similar products
    - Recommendations
    """
    from sqlalchemy import select
    from app.models.product import Product
    
    # Get product
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Parallel context gathering
    tasks = {
        "ai_analysis": hf_client.enhance_product_description(product.name),
        "realtime_feeds": realtime_feeds.get_product_context(product.name, product.category),
        "similar_products": query_optimizer.search_products(product.name, db, limit=5, use_cache=False),
        "price_history": get_price_history(product_id, db)
    }
    
    context = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True
    )
    
    result_context = {}
    for key, result in zip(tasks.keys(), context):
        if not isinstance(result, Exception):
            result_context[key] = result
        else:
            result_context[key] = None
    
    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "current_price": product.current_price,
            "original_price": product.original_price,
            "image_url": product.image_url,
            "product_url": product.product_url,
            "retailer": product.retailer,
            "in_stock": product.in_stock,
            "last_updated": product.last_updated
        },
        "context": result_context,
        "generated_at": time.time()
    }


async def get_price_history(product_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Get price history for product"""
    from sqlalchemy import select
    from app.models.product_snapshot import ProductSnapshot
    
    stmt = select(ProductSnapshot).where(
        ProductSnapshot.product_id == product_id
    ).order_by(ProductSnapshot.snapshot_date.desc()).limit(30)
    
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    
    return [
        {
            "price": s.price,
            "in_stock": s.in_stock,
            "date": s.snapshot_date.isoformat()
        }
        for s in snapshots
    ]
