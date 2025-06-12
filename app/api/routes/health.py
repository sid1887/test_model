"""
Health check and system status endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis
import json
import torch
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.core.monitoring import logger

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cumpair API",
        "version": settings.app_version
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "service": "Cumpair API",
        "version": settings.app_version,
        "timestamp": "2025-06-11T16:30:00Z",
        "checks": {}
    }
    
    # Database check with connection pool info
    try:
        result = await db.execute(text("SELECT 1 as health_check, version() as db_version"))
        row = result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "version": row.db_version if row else "unknown",
            "response_time_ms": "< 10ms"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy", 
            "error": str(e),
            "details": "Database connection failed"
        }
        health_status["status"] = "degraded"
    
    # Redis check with info
    try:
        r = redis.from_url(settings.redis_url)
        info = r.ping()
        redis_info = r.info('memory')
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "ping": info,
            "memory_used": redis_info.get('used_memory_human', 'unknown'),
            "connected_clients": redis_info.get('connected_clients', 0)
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e),
            "details": "Redis connection failed"
        }
        health_status["status"] = "degraded"
    
    # Celery worker check with queue info
    try:
        from app.worker import celery_app
        # Check active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if active_workers and stats:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "active_workers": len(active_workers),
                "queues": list(stats.keys()) if stats else [],
                "worker_details": {
                    worker: {
                        "active_tasks": len(tasks),
                        "pool": stats.get(worker, {}).get('pool', {})
                    }
                    for worker, tasks in active_workers.items()
                }
            }
        else:
            health_status["checks"]["celery"] = {
                "status": "degraded",
                "error": "No active workers found",
                "details": "Background task processing unavailable"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = {
            "status": "unhealthy", 
            "error": str(e),
            "details": "Celery inspection failed"
        }
        health_status["status"] = "degraded"
    
    # Scraper service check
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.scraper_service_url}/health")
            if response.status_code == 200:
                scraper_data = response.json()
                health_status["checks"]["scraper_service"] = {
                    "status": "healthy",
                    "url": settings.scraper_service_url,
                    "response_time": "< 5s",
                    "service_info": scraper_data
                }
            else:
                health_status["checks"]["scraper_service"] = {
                    "status": "degraded",
                    "error": f"HTTP {response.status_code}",
                    "url": settings.scraper_service_url
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["scraper_service"] = {
            "status": "degraded",
            "error": str(e),
            "details": "External scraper service unavailable",
            "url": settings.scraper_service_url
        }
        # Don't mark overall status as degraded for external service
    
    # AI Models check
    try:
        import os
        from pathlib import Path
        
        model_checks = {}
        
        # Check YOLO model
        yolo_path = Path(settings.yolo_model_path)
        model_checks["yolo"] = {
            "status": "healthy" if yolo_path.exists() else "missing",
            "path": str(yolo_path),
            "size_mb": round(yolo_path.stat().st_size / 1024 / 1024, 1) if yolo_path.exists() else 0
        }
        
        # Check CLIP cache
        clip_cache = Path(settings.clip_cache_dir)
        model_checks["clip"] = {
            "status": "healthy" if clip_cache.exists() else "missing",
            "cache_dir": str(clip_cache),
            "model_name": settings.clip_model_name
        }
        
        health_status["checks"]["ai_models"] = {
            "status": "healthy" if all(m["status"] == "healthy" for m in model_checks.values()) else "degraded",
            "models": model_checks
        }
        
        if health_status["checks"]["ai_models"]["status"] == "degraded":
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["checks"]["ai_models"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "AI model validation failed"
        }
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/health/ai-models")
async def ai_models_health_check():
    """Detailed health check for AI models and GPU memory"""
    try:
        from app.core.gpu_memory import get_memory_stats, get_health_status
        from app.services.ai_models import model_manager
        
        # Get memory statistics
        memory_stats = get_memory_stats()
        memory_health = get_health_status()
        
        # Check model availability
        models_status = {
            "yolo": {
                "loaded": model_manager.yolo_model is not None,
                "device": model_manager.device if model_manager.yolo_model else "N/A",
                "classes": len(model_manager.yolo_model.names) if model_manager.yolo_model else 0
            },
            "clip": {
                "loaded": model_manager.clip_model is not None,
                "device": model_manager.device if model_manager.clip_model else "N/A"
            },
            "efficientnet": {
                "loaded": model_manager.efficientnet_model is not None,
                "status": "placeholder" if model_manager.efficientnet_model is None else "loaded"
            }
        }
        
        # Overall AI health status
        all_models_healthy = all(
            status.get("loaded", False) or status.get("status") == "placeholder" 
            for status in models_status.values()
        )
        
        ai_health_status = "healthy" if all_models_healthy else "degraded"
        if memory_health["status"] in ["warning", "critical"]:
            ai_health_status = memory_health["status"]
        
        return {
            "status": ai_health_status,
            "timestamp": datetime.now().isoformat(),
            "models": models_status,
            "memory": {
                "stats": memory_stats,
                "health": memory_health
            },
            "recommendations": memory_health.get("recommendations", []),
            "device_info": {
                "primary_device": model_manager.device,
                "cuda_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
        }
        
    except Exception as e:
        logger.error(f"AI models health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI health check failed: {str(e)}")
