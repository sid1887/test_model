"""
Scrapy Wrapper Microservice
Proxy to Scrapy microservice on port 5000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import logging
from typing import List, Optional
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Scrapy Wrapper Service",
    description="Proxy to Scrapy microservice (17+ retailers)",
    version="1.0.0"
)

# Get Scrapy service URL from environment
SCRAPY_SERVICE_URL = os.getenv("SCRAPY_SERVICE_URL", "http://localhost:5000")

# ============================================================================
# MODELS
# ============================================================================

class SearchRequest(BaseModel):
    query: str
    retailers: Optional[List[str]] = None
    max_results: Optional[int] = 10

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/scrapy/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SCRAPY_SERVICE_URL}/api/v1/health", timeout=5.0)
            scrapy_healthy = response.status_code == 200
    except Exception as e:
        logger.warning(f"Scrapy service unreachable: {e}")
        scrapy_healthy = False

    return {
        "status": "healthy",
        "service": "scrapy-wrapper",
        "port": 8005,
        "scrapy_service_url": SCRAPY_SERVICE_URL,
        "scrapy_healthy": scrapy_healthy,
        "timestamp": time.time()
    }


@app.post("/api/scrapy/search")
async def search_products(request: SearchRequest):
    """
    Search products via Scrapy service

    Proxies to: POST http://scrapy:5000/api/v1/search
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{SCRAPY_SERVICE_URL}/api/v1/search",
                json=request.dict(),
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Scrapy service error: {response.text}"
                )

            result = response.json()

            return {
                **result,
                "proxy_service": "scrapy-wrapper",
                "proxied": True
            }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Scrapy service timeout")
    except Exception as e:
        logger.error(f"Scrapy proxy error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to reach Scrapy service: {str(e)}")


@app.get("/api/scrapy/retailers")
async def get_retailers():
    """Get list of supported retailers"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SCRAPY_SERVICE_URL}/api/v1/scrapy/retailers",
                timeout=5.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get retailers"
                )

            return response.json()

    except Exception as e:
        logger.error(f"Get retailers error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to get retailers: {str(e)}")


@app.get("/api/scrapy/stats")
async def get_stats():
    """Get Scrapy service statistics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SCRAPY_SERVICE_URL}/api/v1/scrapy/stats",
                timeout=5.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get stats"
                )

            return response.json()

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8005))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
