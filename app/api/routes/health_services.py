"""
Comprehensive Health Check Service
Monitors all AI subsystems: CLIP, HF, YOLO, STT, CAPTCHA, Redis, DB, FAISS
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/services")
async def health_check_services():
    """
    Comprehensive health check of all AI services
    
    Returns status of:
    - CLIP (image-text matching)
    - HuggingFace API (text gen, sentiment, embeddings, captioning)
    - YOLO (object detection)
    - Voice STT (speech-to-text)
    - CAPTCHA service
    - Redis (caching/queue)
    - Database (PostgreSQL)
    - FAISS (vector index)
    """
    health_status = {}
    overall_healthy = True
    
    # Check CLIP service
    try:
        from app.services.clip_search import CLIPSearchService
        
        clip = CLIPSearchService()
        clip_health = await clip.health_check()
        health_status['clip'] = clip_health
        
        if not clip_health.get('healthy', False):
            overall_healthy = False
            
    except Exception as e:
        logger.error(f"CLIP health check failed: {e}")
        health_status['clip'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
        overall_healthy = False
    
    # Check HuggingFace connector
    try:
        from app.services.huggingface_connector import get_hf_connector
        
        hf = get_hf_connector()
        hf_health = await hf.health_check()
        health_status['huggingface'] = hf_health
        
        if not hf_health.get('healthy', False):
            # HF is optional, don't fail overall health
            pass
            
    except Exception as e:
        logger.error(f"HF health check failed: {e}")
        health_status['huggingface'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
    
    # Check Voice STT
    try:
        from app.services.voice_stt import get_stt_service
        
        stt = await get_stt_service()
        stt_health = await stt.health_check()
        health_status['voice_stt'] = stt_health
        
        if not stt_health.get('healthy', False):
            # STT is optional
            pass
            
    except Exception as e:
        logger.error(f"STT health check failed: {e}")
        health_status['voice_stt'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
    
    # Check Image Processor (YOLO, OCR, etc.)
    try:
        from app.services.image_processor import get_image_processor
        
        processor = await get_image_processor()
        processor_health = await processor.health_check()
        health_status['image_processor'] = processor_health
        
        if not processor_health.get('healthy', False):
            overall_healthy = False
            
    except Exception as e:
        logger.error(f"Image processor health check failed: {e}")
        health_status['image_processor'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
        overall_healthy = False
    
    # Check CAPTCHA service
    try:
        import aiohttp
        import os
        
        captcha_url = os.getenv('CAPTCHA_SERVICE_URL', 'http://localhost:9001')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{captcha_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    captcha_data = await response.json()
                    health_status['captcha'] = {
                        'status': 'healthy',
                        'data': captcha_data,
                        'healthy': True
                    }
                else:
                    health_status['captcha'] = {
                        'status': 'unreachable',
                        'healthy': False
                    }
                    # CAPTCHA is optional
                    
    except Exception as e:
        logger.warning(f"CAPTCHA health check failed: {e}")
        health_status['captcha'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
    
    # Check Redis
    try:
        import redis
        import os
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        r.ping()
        
        health_status['redis'] = {
            'status': 'healthy',
            'healthy': True
        }
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status['redis'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
        overall_healthy = False
    
    # Check Database
    try:
        from app.core.database import get_db_session
        
        async with get_db_session() as db:
            # Simple query to check connection
            await db.execute("SELECT 1")
            
            health_status['database'] = {
                'status': 'healthy',
                'healthy': True
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['database'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
        overall_healthy = False
    
    # Check FAISS index
    try:
        import os
        from pathlib import Path
        
        faiss_path = Path(os.getenv('FAISS_INDEX_PATH', 'models/faiss_index.bin'))
        
        if faiss_path.exists():
            health_status['faiss'] = {
                'status': 'healthy',
                'path': str(faiss_path),
                'healthy': True
            }
        else:
            health_status['faiss'] = {
                'status': 'not_found',
                'message': 'FAISS index not created yet',
                'healthy': False
            }
            # FAISS is optional for startup
            
    except Exception as e:
        logger.warning(f"FAISS health check failed: {e}")
        health_status['faiss'] = {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }
    
    # Overall status
    status_code = 200 if overall_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'healthy' if overall_healthy else 'degraded',
            'healthy': overall_healthy,
            'services': health_status,
            'critical_services_ok': all([
                health_status.get('redis', {}).get('healthy', False),
                health_status.get('database', {}).get('healthy', False),
                health_status.get('clip', {}).get('healthy', False) or 
                health_status.get('image_processor', {}).get('healthy', False)
            ])
        }
    )


@router.get("/")
async def health_check_basic():
    """Basic health check endpoint"""
    return JSONResponse({
        'status': 'ok',
        'service': 'cumpair-api',
        'version': '1.0.0'
    })


@router.get("/stats")
async def get_service_stats():
    """
    Get statistics from all AI services
    
    Returns metrics like:
    - Request counts
    - Average latencies
    - Error rates
    """
    stats = {}
    
    # Get HF stats
    try:
        from app.services.huggingface_connector import get_hf_connector
        
        hf = get_hf_connector()
        stats['huggingface'] = hf.get_stats()
        
    except Exception as e:
        stats['huggingface'] = {'error': str(e)}
    
    # Get STT stats
    try:
        from app.services.voice_stt import get_stt_service
        
        stt = await get_stt_service()
        stats['voice_stt'] = stt.get_stats()
        
    except Exception as e:
        stats['voice_stt'] = {'error': str(e)}
    
    # Get Image Processor stats
    try:
        from app.services.image_processor import get_image_processor
        
        processor = await get_image_processor()
        stats['image_processor'] = processor.get_stats()
        
    except Exception as e:
        stats['image_processor'] = {'error': str(e)}
    
    return JSONResponse({
        'status': 'ok',
        'stats': stats
    })
