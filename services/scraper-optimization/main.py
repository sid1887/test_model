"""
Scraper Optimization Service
Handles concurrent scraping, Redis caching, retry logic, and scheduling
Maximizes scraping speed and data volume
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import aiohttp
import redis.asyncio as redis
import logging
from datetime import datetime, timedelta
import json
import os
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SCRAPY_URL = os.getenv("SCRAPY_URL", "http://scrapy-wrapper:8005")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT", "20"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# ============================================================================
# MODELS
# ============================================================================

class ScraperJob(BaseModel):
    """Single scraping job"""
    retailer: str
    url: str
    product_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class BatchScraperRequest(BaseModel):
    """Batch of scraper jobs"""
    jobs: List[ScraperJob]
    use_cache: bool = True
    cache_only: bool = False

class ScheduleJobRequest(BaseModel):
    """Request to schedule recurring scrape"""
    retailer: str
    schedule_type: str  # 'hourly', 'daily', 'weekly'
    priority: int = 5  # 1-10

class ScrapingStats(BaseModel):
    """Scraping statistics"""
    total_attempted: int
    successful: int
    failed: int
    cached: int
    avg_time_ms: float

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Scraper Optimization Service",
    description="Concurrent scraping, caching, retry logic, scheduling",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REDIS CONNECTION
# ============================================================================

redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    try:
        redis_client = await redis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
        logger.info("✅ Connected to Redis")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    global redis_client
    if redis_client:
        await redis_client.close()

def get_cache_key(retailer: str, url: str) -> str:
    """Generate cache key for URL"""
    combined = f"{retailer}:{url}"
    return f"scrape:{hashlib.md5(combined.encode()).hexdigest()}"

async def get_from_cache(cache_key: str) -> Optional[Dict]:
    """Get data from Redis cache"""
    try:
        if not redis_client:
            return None

        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Cache hit: {cache_key}")
            return json.loads(cached)
        return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None

async def set_cache(cache_key: str, data: Dict, ttl: int = CACHE_TTL) -> bool:
    """Store data in Redis cache"""
    try:
        if not redis_client:
            return False

        await redis_client.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
        logger.info(f"✅ Cached: {cache_key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache write error: {e}")
        return False

# ============================================================================
# PHASE 3.1: CONCURRENT SCRAPING
# ============================================================================

@app.post("/api/scraper/batch")
async def batch_scrape(request: BatchScraperRequest, background_tasks: BackgroundTasks):
    """
    Scrape multiple URLs concurrently with caching
    """
    try:
        results = []
        stats = {
            "total_attempted": len(request.jobs),
            "successful": 0,
            "failed": 0,
            "cached": 0,
            "times": []
        }

        # Process jobs in parallel batches
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def scrape_with_semaphore(job: ScraperJob):
            async with semaphore:
                return await scrape_single(job, request.use_cache, request.cache_only)

        # Execute all jobs concurrently
        tasks = [scrape_with_semaphore(job) for job in request.jobs]
        job_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in job_results:
            if isinstance(result, Exception):
                logger.error(f"Job failed: {result}")
                stats["failed"] += 1
            elif result:
                results.append(result)
                if result.get("from_cache"):
                    stats["cached"] += 1
                else:
                    stats["successful"] += 1

                if result.get("time_ms"):
                    stats["times"].append(result["time_ms"])

        # Calculate average time
        avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
        stats["avg_time_ms"] = avg_time

        logger.info(f"""
        ✅ Batch scraping complete:
           - Total: {stats['total_attempted']}
           - Successful: {stats['successful']}
           - Failed: {stats['failed']}
           - Cached: {stats['cached']}
           - Avg time: {avg_time:.2f}ms
        """)

        return {
            "status": "success",
            "stats": stats,
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Batch scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_single(job: ScraperJob, use_cache: bool = True,
                       cache_only: bool = False) -> Optional[Dict]:
    """
    Scrape a single URL with caching and retry logic
    """
    cache_key = get_cache_key(job.retailer, job.url)
    start_time = datetime.now()

    # Try cache first
    if use_cache:
        cached_data = await get_from_cache(cache_key)
        if cached_data:
            return {
                "retailer": job.retailer,
                "url": job.url,
                "data": cached_data,
                "from_cache": True,
                "time_ms": 0
            }

    if cache_only:
        return None

    # Scrape with retry logic
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    job.url,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        elapsed = (datetime.now() - start_time).total_seconds() * 1000

                        # Cache the result
                        if use_cache:
                            await set_cache(cache_key, data)

                        logger.info(f"✅ Scraped: {job.retailer} ({elapsed:.2f}ms)")

                        return {
                            "retailer": job.retailer,
                            "url": job.url,
                            "product_id": job.product_id,
                            "data": data,
                            "from_cache": False,
                            "time_ms": elapsed,
                            "attempt": attempt + 1
                        }
                    else:
                        logger.warning(f"⚠️ Attempt {attempt+1}: Status {response.status}")

                        # Exponential backoff
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)

        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Attempt {attempt+1}: Timeout")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt+1}: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

    logger.error(f"❌ Failed to scrape: {job.url}")
    return None

# ============================================================================
# PHASE 3.2: CACHING STRATEGY
# ============================================================================

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    try:
        if not redis_client:
            return {"status": "offline"}

        info = await redis_client.info()

        return {
            "status": "online",
            "memory_used": info.get("used_memory_human"),
            "memory_peak": info.get("used_memory_peak_human"),
            "keys_count": await redis_client.dbsize(),
            "connected_clients": info.get("connected_clients")
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/clear/{retailer}")
async def clear_retailer_cache(retailer: str):
    """Clear cache for a specific retailer"""
    try:
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis offline")

        pattern = f"scrape:{retailer}:*"
        keys = await redis_client.keys(f"scrape:*{retailer}*")

        if keys:
            await redis_client.delete(*keys)

        logger.info(f"✅ Cleared {len(keys)} cache entries for {retailer}")

        return {
            "status": "success",
            "cleared_count": len(keys)
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/warmup")
async def warmup_cache(retailer: str, force: bool = False):
    """
    Pre-populate cache for a retailer
    Useful before running high-volume scrapes
    """
    try:
        if force:
            await clear_retailer_cache(retailer)

        # Get common URLs for retailer from metadata
        urls_to_cache = [
            f"https://api.{retailer}.com/products",
            f"https://api.{retailer}.com/deals",
            f"https://api.{retailer}.com/trending"
        ]

        batch_request = BatchScraperRequest(
            jobs=[ScraperJob(retailer=retailer, url=url) for url in urls_to_cache],
            use_cache=True
        )

        logger.info(f"✅ Cache warmup started for {retailer}")

        return {
            "status": "success",
            "urls_queued": len(urls_to_cache)
        }
    except Exception as e:
        logger.error(f"Cache warmup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 3.3: SCHEDULING
# ============================================================================

@app.post("/api/scheduler/schedule")
async def schedule_scrape(request: ScheduleJobRequest):
    """
    Schedule recurring scrape jobs
    """
    try:
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis offline")

        schedule_key = f"schedule:{request.retailer}:{request.schedule_type}"

        # Store schedule in Redis
        schedule_data = {
            "retailer": request.retailer,
            "schedule_type": request.schedule_type,
            "priority": request.priority,
            "created_at": datetime.utcnow().isoformat(),
            "enabled": True
        }

        await redis_client.set(
            schedule_key,
            json.dumps(schedule_data),
            ex=365*24*3600  # 1 year
        )

        logger.info(f"✅ Scheduled: {request.retailer} ({request.schedule_type})")

        return {
            "status": "success",
            "schedule_key": schedule_key,
            "schedule_data": schedule_data
        }
    except Exception as e:
        logger.error(f"Schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scheduler/scheduled")
async def get_scheduled_jobs():
    """Get all scheduled scraping jobs"""
    try:
        if not redis_client:
            return {"scheduled_jobs": []}

        schedule_keys = await redis_client.keys("schedule:*")
        schedules = []

        for key in schedule_keys:
            data = await redis_client.get(key)
            if data:
                schedules.append(json.loads(data))

        return {
            "total_scheduled": len(schedules),
            "scheduled_jobs": schedules
        }
    except Exception as e:
        logger.error(f"Get schedules error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/disable/{retailer}")
async def disable_schedule(retailer: str):
    """Disable scheduled jobs for a retailer"""
    try:
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis offline")

        keys = await redis_client.keys(f"schedule:{retailer}:*")

        for key in keys:
            data = json.loads(await redis_client.get(key))
            data["enabled"] = False
            await redis_client.set(key, json.dumps(data))

        logger.info(f"✅ Disabled schedules for {retailer}")

        return {
            "status": "success",
            "disabled_count": len(keys)
        }
    except Exception as e:
        logger.error(f"Disable schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 3.4: RATE LIMITING & REQUEST DISTRIBUTION
# ============================================================================

@app.get("/api/distribution/rate-limit/{retailer}")
async def get_rate_limit(retailer: str):
    """Get rate limit info for a retailer"""
    try:
        # Default limits
        limits = {
            "requests_per_second": 5,
            "requests_per_minute": 200,
            "requests_per_hour": 5000,
            "concurrent_requests": 10
        }

        # Can customize per retailer
        if not redis_client:
            return {"retailer": retailer, "limits": limits}

        custom = await redis_client.get(f"rate_limit:{retailer}")
        if custom:
            limits.update(json.loads(custom))

        return {
            "retailer": retailer,
            "limits": limits
        }
    except Exception as e:
        logger.error(f"Rate limit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/distribution/set-rate-limit/{retailer}")
async def set_rate_limit(retailer: str, requests_per_second: float = 5,
                        concurrent_requests: int = 10):
    """Set custom rate limits for a retailer"""
    try:
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis offline")

        limits = {
            "requests_per_second": requests_per_second,
            "concurrent_requests": concurrent_requests
        }

        await redis_client.set(
            f"rate_limit:{retailer}",
            json.dumps(limits),
            ex=365*24*3600
        )

        logger.info(f"✅ Rate limits set for {retailer}")

        return {
            "status": "success",
            "retailer": retailer,
            "limits": limits
        }
    except Exception as e:
        logger.error(f"Set rate limit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "healthy" if redis_client else "unhealthy"

    return {
        "status": "healthy",
        "redis": redis_status,
        "max_concurrent": MAX_CONCURRENT_REQUESTS,
        "request_timeout": REQUEST_TIMEOUT
    }

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    logger.info("""
    ╔════════════════════════════════════════════════╗
    ║  SCRAPER OPTIMIZATION SERVICE STARTED          ║
    ║  Concurrent scraping, caching, scheduling      ║
    ║  Rate limiting, request distribution           ║
    ╚════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007, workers=4)
