"""
Celery Worker Service - Main Entry Point
FastAPI wrapper around Celery for monitoring, task management, and health checks
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os
import json

from celery.result import AsyncResult
from celery_app import app as celery_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Celery Worker Service",
    description="Background job processing and task management",
    version="1.0.0"
)

# ============================================================================
# DATA MODELS
# ============================================================================

class TaskRequest(BaseModel):
    """Request to execute a task"""
    task_name: str
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

class TaskResponse(BaseModel):
    """Response with task info"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

class WorkerStats(BaseModel):
    """Worker statistics"""
    worker_name: str
    active_tasks: int
    processed_tasks: int
    failed_tasks: int
    uptime_seconds: int

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Check service and worker health"""
    try:
        # Check Celery connection
        stats = celery_app.control.inspect().stats()

        if not stats:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "No workers available",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "status": "healthy",
            "service": "celery-worker",
            "timestamp": datetime.utcnow().isoformat(),
            "workers_active": len(stats),
            "queues": list(celery_app.conf.task_queues)
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get worker statistics"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}
        active = inspect.active() or {}

        total_active = sum(len(tasks) for tasks in active.values())

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "workers": {
                name: {
                    "status": "online",
                    "queues": worker_stats.get("pool", {}).get("max-concurrency", "N/A"),
                    "processed": worker_stats.get("total", 0)
                }
                for name, worker_stats in stats.items()
            },
            "active_tasks": total_active,
            "queues": [q.name for q in celery_app.conf.task_queues]
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queues", tags=["Info"])
async def get_queues():
    """Get configured queues"""
    return {
        "queues": [
            {"name": q.name, "routing_key": q.routing_key}
            for q in celery_app.conf.task_queues
        ]
    }

# ============================================================================
# TASK SUBMISSION ENDPOINTS
# ============================================================================

@app.post("/task/submit", response_model=TaskResponse, tags=["Tasks"])
async def submit_task(request: TaskRequest):
    """
    Submit a task for execution

    Example:
    {
        "task_name": "tasks.scrape_retailer",
        "kwargs": {"retailer": "amazon", "priority": 10}
    }
    """
    try:
        logger.info(f"Submitting task: {request.task_name}")

        # Submit task
        result = celery_app.send_task(
            request.task_name,
            args=request.args,
            kwargs=request.kwargs
        )

        logger.info(f"Task submitted with ID: {result.id}")

        return TaskResponse(
            task_id=result.id,
            status="submitted"
        )
    except Exception as e:
        logger.error(f"Task submission error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/task/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task_status(task_id: str):
    """Get task status and result"""
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": result.status,
        }

        if result.status == "PENDING":
            response["error"] = "Task not found"
        elif result.status == "SUCCESS":
            response["result"] = result.result
        elif result.status == "FAILURE":
            response["error"] = str(result.info)
        elif result.status == "RETRY":
            response["error"] = f"Retry in progress: {result.info}"

        return TaskResponse(**response)
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/task/{task_id}/revoke", tags=["Tasks"])
async def revoke_task(task_id: str):
    """Revoke/cancel a task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)

        logger.info(f"Task revoked: {task_id}")

        return {"status": "revoked", "task_id": task_id}
    except Exception as e:
        logger.error(f"Task revoke error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SCHEDULED TASKS ENDPOINTS
# ============================================================================

@app.get("/schedule", tags=["Schedule"])
async def get_schedule():
    """Get scheduled tasks"""
    try:
        schedule = celery_app.conf.beat_schedule or {}

        tasks = []
        for name, config in schedule.items():
            tasks.append({
                "name": name,
                "task": config.get("task"),
                "schedule": str(config.get("schedule")),
                "args": config.get("args"),
                "kwargs": config.get("kwargs")
            })

        return {
            "scheduled_tasks": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"Schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/test", tags=["Schedule"])
async def test_scheduled_task(task_name: str):
    """Test execute a scheduled task"""
    try:
        schedule = celery_app.conf.beat_schedule or {}

        if task_name not in schedule:
            raise HTTPException(status_code=404, detail=f"Scheduled task '{task_name}' not found")

        config = schedule[task_name]

        result = celery_app.send_task(
            config["task"],
            args=config.get("args", []),
            kwargs=config.get("kwargs", {})
        )

        logger.info(f"Scheduled task executed: {task_name} (ID: {result.id})")

        return {
            "status": "executed",
            "task_name": task_name,
            "task_id": result.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test scheduled task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BATCH OPERATIONS ENDPOINTS
# ============================================================================

@app.post("/batch/submit", tags=["Batch"])
async def submit_batch_tasks(tasks: List[TaskRequest]):
    """Submit multiple tasks at once"""
    try:
        results = []

        for task_req in tasks:
            result = celery_app.send_task(
                task_req.task_name,
                args=task_req.args or [],
                kwargs=task_req.kwargs or {}
            )

            results.append({
                "task": task_req.task_name,
                "task_id": result.id
            })

        logger.info(f"Batch submitted: {len(results)} tasks")

        return {
            "status": "submitted",
            "count": len(results),
            "tasks": results
        }
    except Exception as e:
        logger.error(f"Batch submission error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/batch/status", tags=["Batch"])
async def get_batch_status(task_ids: List[str]):
    """Get status of multiple tasks"""
    try:
        results = []

        for task_id in task_ids:
            result = AsyncResult(task_id, app=celery_app)
            results.append({
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.status == "SUCCESS" else None
            })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "tasks": results
        }
    except Exception as e:
        logger.error(f"Batch status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WORKER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/workers", tags=["Workers"])
async def get_workers():
    """Get list of active workers"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}
        active = inspect.active() or {}

        workers = []
        for worker_name in stats.keys():
            workers.append({
                "name": worker_name,
                "status": "online",
                "active_tasks": len(active.get(worker_name, []))
            })

        return {
            "worker_count": len(workers),
            "workers": workers
        }
    except Exception as e:
        logger.error(f"Workers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workers/active", tags=["Workers"])
async def get_active_tasks():
    """Get all active tasks across workers"""
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}

        all_tasks = []
        for worker_name, tasks in active.items():
            for task in tasks:
                all_tasks.append({
                    "worker": worker_name,
                    "task_id": task["id"],
                    "task_name": task["name"],
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {})
                })

        return {
            "active_task_count": len(all_tasks),
            "tasks": all_tasks
        }
    except Exception as e:
        logger.error(f"Active tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workers/shutdown", tags=["Workers"])
async def shutdown_workers():
    """Gracefully shutdown all workers"""
    try:
        celery_app.control.shutdown()

        logger.warning("Workers shutdown initiated")

        return {"status": "shutdown_initiated"}
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# COMMON TASKS SHORTCUTS
# ============================================================================

@app.post("/tasks/scrape-retailer", tags=["Shortcuts"])
async def scrape_retailer_shortcut(retailer: str, priority: int = 10):
    """Shortcut: Scrape a retailer"""
    try:
        result = celery_app.send_task(
            "tasks.scraping.scrape_retailer",
            kwargs={"retailer": retailer, "priority": priority}
        )
        return TaskResponse(task_id=result.id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tasks/batch-scrape", tags=["Shortcuts"])
async def batch_scrape_shortcut(all_retailers: bool = True):
    """Shortcut: Batch scrape all retailers"""
    try:
        result = celery_app.send_task(
            "tasks.scraping.batch_scrape",
            kwargs={"all_retailers": all_retailers}
        )
        return TaskResponse(task_id=result.id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tasks/process-prices", tags=["Shortcuts"])
async def process_prices_shortcut():
    """Shortcut: Process prices"""
    try:
        result = celery_app.send_task("tasks.data.process_prices")
        return TaskResponse(task_id=result.id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tasks/fetch-news", tags=["Shortcuts"])
async def fetch_news_shortcut(page_size: int = 100):
    """Shortcut: Fetch news"""
    try:
        result = celery_app.send_task(
            "tasks.integration.fetch_news",
            kwargs={"page_size": page_size}
        )
        return TaskResponse(task_id=result.id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tasks/send-notification", tags=["Shortcuts"])
async def send_notification_shortcut(notification_type: str, recipient: str, message: str):
    """
    Shortcut: Send notification

    notification_type: 'email', 'sms', or 'push'
    """
    try:
        if notification_type == "email":
            result = celery_app.send_task(
                "tasks.notifications.send_email",
                kwargs={
                    "to_email": recipient,
                    "subject": "Notification",
                    "body": message
                }
            )
        elif notification_type == "sms":
            result = celery_app.send_task(
                "tasks.notifications.send_sms",
                kwargs={"phone": recipient, "message": message}
            )
        elif notification_type == "push":
            result = celery_app.send_task(
                "tasks.notifications.send_push",
                kwargs={
                    "user_id": recipient,
                    "title": "Notification",
                    "message": message
                }
            )
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")

        return TaskResponse(task_id=result.id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """API documentation"""
    return {
        "service": "Celery Worker",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "health": "GET /health",
            "stats": "GET /stats",
            "submit_task": "POST /task/submit",
            "task_status": "GET /task/{task_id}",
            "revoke_task": "POST /task/{task_id}/revoke",
            "workers": "GET /workers",
            "active_tasks": "GET /workers/active",
            "scheduled_tasks": "GET /schedule",
            "batch_submit": "POST /batch/submit",
            "batch_status": "POST /batch/status"
        },
        "shortcuts": {
            "scrape": "POST /tasks/scrape-retailer",
            "batch_scrape": "POST /tasks/batch-scrape",
            "process_prices": "POST /tasks/process-prices",
            "fetch_news": "POST /tasks/fetch-news",
            "send_notification": "POST /tasks/send-notification"
        }
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("CELERY_WORKER_PORT", 8009))

    print(f"\n{'='*60}")
    print(f"🚀 Celery Worker Service Starting")
    print(f"   Port: {port}")
    print(f"   Broker: {os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')}")
    print(f"   Backend: {os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')}")
    print(f"{'='*60}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
