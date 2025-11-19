"""
API Gateway Microservice
Central orchestrator that routes requests to all microservices
Preserves all existing API endpoints while calling downstream services
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import logging
import httpx
import os
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICES = {
    'ai_models': os.getenv("AI_MODELS_URL", "http://ai-models:8001"),
    'hf_connector': os.getenv("HF_CONNECTOR_URL", "http://hf-connector:8002"),
    'speech_image': os.getenv("SPEECH_IMAGE_URL", "http://speech-image:8003"),
    'feature_extract': os.getenv("FEATURE_EXTRACT_URL", "http://feature-extract:8004"),
    'scrapy_wrapper': os.getenv("SCRAPY_WRAPPER_URL", "http://scrapy-wrapper:8005"),
    'data_pipeline': os.getenv("DATA_PIPELINE_URL", "http://data-pipeline:8006"),
    'scraper_optimization': os.getenv("SCRAPER_OPTIMIZATION_URL", "http://scraper-optimization:8007"),
    'multi_source_integration': os.getenv("MULTI_SOURCE_INTEGRATION_URL", "http://multi-source-integration:8008"),
}

logger.info(f"Service URLs configured: {SERVICES}")

# ============================================================================
# MODELS
# ============================================================================

class SearchRequest(BaseModel):
    query: str
    retailers: Optional[List[str]] = None
    max_results: Optional[int] = 10

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Cumpair API Gateway",
    description="Central orchestrator for microservices (17+ retailers, multimodal search)",
    version="2.0.0 (Microservices)"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except:
    logger.warning("Could not mount static files")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def proxy_request(service_name: str, endpoint: str, method: str = "GET", data: dict = None):
    """Generic proxy function for microservices"""
    try:
        service_url = SERVICES.get(service_name)
        if not service_url:
            raise HTTPException(status_code=500, detail=f"Service {service_name} not configured")

        url = f"{service_url}{endpoint}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers={"Content-Type": "application/json"})
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code >= 400:
                logger.error(f"Service {service_name} error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)

            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
    except Exception as e:
        logger.error(f"Proxy error for {service_name}: {e}")
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)}")

# ============================================================================
# HEALTH & MONITORING
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Health check - verifies all downstream services"""
    services_status = {}
    all_healthy = True

    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/api/*/health".replace("*/", service_name.split("_")[0] + "-" if "_" in service_name else "models/").replace("/models-health", "/models/health"))
                # Construct proper health endpoint based on service
                health_endpoints = {
                    'ai_models': '/api/models/health',
                    'hf_connector': '/api/hf/health',
                    'speech_image': '/api/media/health',
                    'feature_extract': '/api/features/health',
                    'scrapy_wrapper': '/api/scrapy/health',
                }
                health_endpoint = health_endpoints.get(service_name, '/health')
                response = await client.get(f"{service_url}{health_endpoint}")
                services_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
                if response.status_code != 200:
                    all_healthy = False
        except Exception as e:
            services_status[service_name] = {"status": "unavailable", "error": str(e)}
            all_healthy = False

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "port": 8000,
        "timestamp": time.time(),
        "services": services_status
    }

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <html>
        <head>
            <title>Cumpair - Microservices Architecture</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .badge { display: inline-block; padding: 5px 10px; margin: 5px; border-radius: 3px; font-size: 12px; font-weight: bold; }
                .service { padding: 10px; margin: 10px 0; background: #f0f0f0; border-left: 4px solid #007bff; border-radius: 3px; }
                .green { background: #d4edda; border-left-color: #28a745; }
                .blue { background: #cfe2ff; border-left-color: #0d6efd; }
                .purple { background: #e2d5f5; border-left-color: #6f42c1; }
                code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
                .section { margin: 20px 0; }
                .phase-header { background: #f9f9f9; padding: 10px; margin: 15px 0 10px 0; border-left: 4px solid #ffc107; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏗️ Cumpair Microservices Architecture v2.0+</h1>
                <p><strong>API Gateway</strong> orchestrating <strong>9+ independent microservices</strong></p>
                <p>Monolithic 2-3 min restart → 30-45 sec microservices</p>

                <h2>📊 Core Microservices (Phase 1)</h2>
                <div class="service green">
                    <strong>✓ API Gateway</strong> (Port 8000) - Central orchestrator & service routing
                </div>
                <div class="service blue">
                    <strong>🤖 AI Models</strong> (Port 8001) - YOLO detection, CLIP encoding
                </div>
                <div class="service blue">
                    <strong>🤗 HF Connector</strong> (Port 8002) - Sentiment, NER, zero-shot classification
                </div>
                <div class="service blue">
                    <strong>🎤 Speech & Image</strong> (Port 8003) - Whisper STT, EasyOCR
                </div>
                <div class="service blue">
                    <strong>🔍 Feature Extract</strong> (Port 8004) - Embeddings, vector search
                </div>
                <div class="service blue">
                    <strong>🕷️ Scrapy Wrapper</strong> (Port 8005) - 17+ retailers proxy
                </div>
                <div class="service blue">
                    <strong>⚙️ Worker</strong> - Celery task queue

                <h2 class="phase-header">📦 Phase 2-4 Services (New!)</h2>

                <div class="service purple">
                    <strong>🔗 Data Pipeline</strong> (Port 8006)<br/>
                    Product linking, deduplication, price tracking, data normalization<br/>
                    • Link duplicate products across retailers<br/>
                    • Track price history & detect changes<br/>
                    • Ingest and link news to products<br/>
                    • Validate & normalize product data
                </div>

                <div class="service purple">
                    <strong>⚡ Scraper Optimization</strong> (Port 8007)<br/>
                    Concurrent scraping, Redis caching, scheduling<br/>
                    • Batch concurrent scraping (up to 20 concurrent)<br/>
                    • Redis cache with TTL (1 hour default)<br/>
                    • Exponential backoff retry logic<br/>
                    • Recurring scrape scheduling<br/>
                    • Per-retailer rate limiting
                </div>

                <div class="service purple">
                    <strong>📰 Multi-Source Integration</strong> (Port 8008)<br/>
                    News, cryptocurrency, stock data integration<br/>
                    • NewsAPI - Real-time news articles<br/>
                    • CoinGecko - Cryptocurrency prices<br/>
                    • yfinance - Stock prices & historical data
                </div>

                <h2>📚 API Documentation</h2>
                <ul>
                    <li><a href="/docs"><strong>🔗 Interactive API Docs (Swagger)</strong></a></li>
                    <li><a href="/redoc"><strong>📖 ReDoc Documentation</strong></a></li>
                    <li><a href="/api/v1/health"><strong>💚 Health Check</strong></a></li>
                </ul>

                <h2>🚀 Quick Examples</h2>

                <h3>1. Batch Concurrent Scraping</h3>
                <code>
curl -X POST "http://localhost:8007/api/scraper/batch" \\<br/>
  -H "Content-Type: application/json" \\<br/>
  -d '{"jobs": [{"retailer": "amazon", "url": "..."}, ...], "use_cache": true}'
                </code>

                <h3>2. Record Product Price</h3>
                <code>
curl -X POST "http://localhost:8006/api/prices/snapshot" \\<br/>
  -H "Content-Type: application/json" \\<br/>
  -d '{"product_id": "...", "site_name": "amazon", "price": 99.99}'
                </code>

                <h3>3. Get Price History</h3>
                <code>
curl "http://localhost:8006/api/prices/product/product_id?days=30"
                </code>

                <h3>4. Fetch News Articles</h3>
                <code>
curl -X POST "http://localhost:8008/api/news/fetch" \\<br/>
  -H "Content-Type: application/json" \\<br/>
  -d '{"query": "product pricing", "category": "tech", "page_size": 50}'
                </code>

                <h3>5. Get Cryptocurrency Prices</h3>
                <code>
curl -X POST "http://localhost:8008/api/crypto/fetch" \\<br/>
  -H "Content-Type: application/json" \\<br/>
  -d '{"symbols": ["bitcoin", "ethereum"]}'
                </code>

                <h2>🏗️ Architecture Benefits</h2>
                <ul>
                    <li>⚡ <strong>Fast Restarts</strong> - Restart one service in 2-10 sec vs 2-3 min</li>
                    <li>📦 <strong>Independent Scaling</strong> - Scale each service separately</li>
                    <li>🔧 <strong>Easier Development</strong> - Change one service, rebuild in seconds</li>
                    <li>🛡️ <strong>Resilient</strong> - Service failure doesn't crash entire app</li>
                    <li>📊 <strong>Per-Service Monitoring</strong> - Health checks per service</li>
                    <li>🚀 <strong>Concurrent Processing</strong> - 20x scraping speedup</li>
                    <li>💾 <strong>Smart Caching</strong> - Redis layer reduces API calls</li>
                    <li>🌍 <strong>Multi-Source Data</strong> - Unified product, news, market data</li>
                </ul>

                <h2>📋 Available Endpoints</h2>
                <p><strong>Data Pipeline (8006):</strong> /api/products/*, /api/prices/*, /api/news/*</p>
                <p><strong>Scraper Optimization (8007):</strong> /api/scraper/*, /api/cache/*, /api/scheduler/*, /api/distribution/*</p>
                <p><strong>Multi-Source (8008):</strong> /api/news/*, /api/crypto/*, /api/stocks/*</p>
                <p>See Swagger docs for full API reference</p>
            </div>
        </body>
    </html>
    """

# ============================================================================
# SCRAPY INTEGRATION
# ============================================================================

@app.post("/api/v1/scrapy/search")
async def search_products(request: SearchRequest):
    """Search products (proxied to Scrapy Wrapper → Scrapy Service)"""
    return await proxy_request('scrapy_wrapper', '/api/scrapy/search', 'POST', request.dict())

@app.get("/api/v1/scrapy/retailers")
async def get_retailers():
    """Get list of supported retailers"""
    return await proxy_request('scrapy_wrapper', '/api/scrapy/retailers', 'GET')

@app.get("/api/v1/scrapy/stats")
async def get_scrapy_stats():
    """Get Scrapy statistics"""
    return await proxy_request('scrapy_wrapper', '/api/scrapy/stats', 'GET')

# ============================================================================
# AI MODELS INTEGRATION
# ============================================================================

@app.post("/api/models/yolo-detect")
async def yolo_detect(image: UploadFile = File(...), confidence: float = 0.5):
    """YOLO object detection"""
    # Note: File upload needs special handling - direct call recommended
    raise HTTPException(status_code=501, detail="Use direct service URL http://localhost:8001/api/models/yolo-detect")

@app.post("/api/models/clip-encode-text")
async def clip_encode_text(texts: List[str]):
    """CLIP text encoding"""
    return await proxy_request('ai_models', '/api/models/clip-encode-text', 'POST', {'texts': texts})

# ============================================================================
# HF CONNECTOR INTEGRATION
# ============================================================================

@app.post("/api/hf/sentiment")
async def sentiment_analysis(texts: List[str]):
    """Sentiment analysis"""
    return await proxy_request('hf_connector', '/api/hf/sentiment', 'POST', {'texts': texts})

@app.post("/api/hf/zero-shot")
async def zero_shot_classify(text: str, labels: List[str]):
    """Zero-shot classification"""
    return await proxy_request('hf_connector', '/api/hf/zero-shot', 'POST', {'text': text, 'labels': labels})

# ============================================================================
# FEATURE EXTRACTION INTEGRATION
# ============================================================================

@app.post("/api/features/embed")
async def generate_embeddings(texts: List[str]):
    """Generate embeddings"""
    return await proxy_request('feature_extract', '/api/features/embed', 'POST', {'texts': texts})

@app.post("/api/features/search")
async def search_vectors(query: str, top_k: int = 5):
    """Search vector index"""
    return await proxy_request('feature_extract', '/api/features/search', 'POST', {'query': query, 'top_k': top_k})


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1
    )
