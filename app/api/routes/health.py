"""
Health check and system status endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis
import json
from app.core.database import get_db
from app.core.config import settings

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
        "checks": {}
    }
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Redis check
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Celery check
    try:
        from app.worker import celery_app
        # Check if Celery workers are active
        active_workers = celery_app.control.active()
        if active_workers:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "active_workers": len(active_workers)
            }
        else:
            health_status["checks"]["celery"] = {
                "status": "unhealthy",
                "error": "No active workers"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status
