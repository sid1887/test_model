# Scrapy Service Integration - Complete Documentation

## Overview

The Scrapy service provides advanced web scraping capabilities for 17+ major e-commerce retailers with full integration of CLIP image analysis, voice search, HAProxy load balancing, and 2Captcha solving.

## Supported Retailers (17+)

### Major US Retailers
- **Amazon** - amazon.com
- **Walmart** - walmart.com
- **Target** - target.com
- **Best Buy** - bestbuy.com
- **eBay** - ebay.com

### Home Improvement
- **Home Depot** - homedepot.com
- **Lowe's** - lowes.com

### Department Stores
- **Macy's** - macys.com
- **Nordstrom** - nordstrom.com
- **Costco** - costco.com

### Specialty Retailers
- **Newegg** - newegg.com (Electronics)
- **B&H Photo** - bhphotovideo.com (Photography)

### Furniture & Home
- **Wayfair** - wayfair.com
- **Overstock** - overstock.com

### Fashion
- **Zappos** - zappos.com

### International
- **Flipkart** - flipkart.com (India)
- **AliExpress** - aliexpress.com (China)

## Service Integration

### 1. CLIP Image Analysis
- **Pipeline**: `CLIPAnalysisPipeline`
- **Function**: Automatically analyzes product images during scraping
- **Output**: Image embeddings and feature vectors
- **Configuration**: `ENABLE_CLIP_ANALYSIS=true` in environment

### 2. Voice Search (Speech-to-Text)
- **Endpoint**: `/api/v1/scrapy/search/voice`
- **Provider**: Configurable (OpenAI Whisper, Google STT, etc.)
- **Input**: Audio file (WAV, MP3, etc.)
- **Process**: Audio → Transcription → Product Search

### 3. HAProxy Load Balancing
- **Function**: Proxy rotation for avoiding rate limits
- **Fallback**: Direct proxy service if HAProxy unavailable
- **Configuration**: `HAPROXY_URL` environment variable

### 4. 2Captcha Integration
- **Function**: Automatic CAPTCHA detection and solving
- **Service**: 2Captcha API
- **Detection**: Pattern-based CAPTCHA page detection
- **Configuration**: `CAPTCHA_SERVICE_URL` environment variable

### 5. Redis Caching
- **Pipelines**: `RedisPipeline`
- **Features**:
  - Product caching (1-hour TTL)
  - Search result indexing
  - Statistics tracking
  - Deduplication

## API Endpoints

### Main API Endpoints (FastAPI)

#### 1. Health Check
```http
GET /api/v1/scrapy/health
```

Response:
```json
{
  "status": "healthy",
  "retailers_supported": 17,
  "retailers": ["amazon", "walmart", ...],
  "stats": {...}
}
```

#### 2. Get Supported Retailers
```http
GET /api/v1/scrapy/retailers
```

Response:
```json
{
  "retailers": ["amazon", "walmart", ...],
  "total": 17,
  "categories": {
    "major_us": [...],
    "home_improvement": [...],
    ...
  }
}
```

#### 3. Text Search
```http
POST /api/v1/scrapy/search
Content-Type: application/json

{
  "query": "laptop",
  "retailers": ["amazon", "walmart", "bestbuy"],
  "max_results": 10
}
```

Response:
```json
{
  "status": "processing",
  "query": "laptop",
  "sites_queued": 3,
  "message": "Scraping jobs have been queued",
  "timestamp": "2025-11-17T05:30:00Z"
}
```

#### 4. Voice Search
```http
POST /api/v1/scrapy/search/voice
Content-Type: multipart/form-data

audio: <audio file>
```

Response:
```json
{
  "transcription": "wireless headphones",
  "status": "processing",
  "sites_queued": 10,
  ...
}
```

#### 5. Image Search
```http
POST /api/v1/scrapy/search/image
Content-Type: multipart/form-data

image: <image file>
```

Response:
```json
{
  "description": "red running shoes",
  "clip_features": [...],
  "status": "processing",
  "sites_queued": 10,
  ...
}
```

#### 6. Bulk Search
```http
POST /api/v1/scrapy/search/bulk
Content-Type: application/json

{
  "queries": ["laptop", "headphones", "monitor"],
  "retailers": ["amazon", "walmart", "bestbuy", "newegg"]
}
```

Response:
```json
{
  "status": "queued",
  "batch_id": "bulk_1700123456.789",
  "jobs_queued": 12,
  "queries_count": 3,
  "retailers_count": 4,
  "message": "Bulk search queued for processing",
  "timestamp": "2025-11-17T05:30:00Z"
}
```

#### 7. Batch Status
```http
GET /api/v1/scrapy/batch/{batch_id}
```

Response:
```json
{
  "batch_id": "bulk_1700123456.789",
  "total_jobs": 12,
  "completed_jobs": 8,
  "progress": "66.7%",
  "results_count": 240,
  "status": "processing",
  "created_at": "2025-11-17T05:30:00Z",
  "timestamp": "2025-11-17T05:31:00Z"
}
```

#### 8. Statistics
```http
GET /api/v1/scrapy/stats
```

Response:
```json
{
  "stats": {
    "total_requests": 1543,
    "successful_requests": 1487,
    "failed_requests": 56,
    ...
  },
  "daily_stats": {
    "date": "2025-11-17",
    "total_products_scraped": 15234,
    "by_retailer": {
      "amazon": 3421,
      "walmart": 2876,
      ...
    }
  },
  "retailers": {
    "supported": ["amazon", "walmart", ...],
    "total": 17,
    "active": 15
  }
}
```

### Direct Scrapy Service Endpoints

#### 1. Search
```http
POST http://scrapy-service:5000/api/search
```

#### 2. Voice Search
```http
POST http://scrapy-service:5000/api/search/voice
```

#### 3. Image Search
```http
POST http://scrapy-service:5000/api/search/image
```

#### 4. Bulk Search
```http
POST http://scrapy-service:5000/api/search/bulk
```

#### 5. Parallel Search
```http
POST http://scrapy-service:5000/api/search/parallel
```

## Usage Examples

### Python Client (via ScrapyServiceClient)

```python
from app.services.scraping import scrapy_client

# Initialize
await scrapy_client.initialize()

# Text search
result = await scrapy_client.search(
    query="wireless mouse",
    retailers=["amazon", "walmart", "bestbuy"]
)

# Voice search
result = await scrapy_client.voice_search("/path/to/audio.wav")

# Image search
result = await scrapy_client.image_search("/path/to/image.jpg")

# Bulk search
result = await scrapy_client.bulk_search(
    queries=["laptop", "monitor", "keyboard"],
    retailers=["amazon", "newegg", "bestbuy"]
)

# Check batch status
status = await scrapy_client.get_batch_status(batch_id)

# Get statistics
stats = await scrapy_client.get_stats()
```

### cURL Examples

```bash
# Text search
curl -X POST http://localhost:8000/api/v1/scrapy/search \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop", "retailers": ["amazon", "walmart"]}'

# Voice search
curl -X POST http://localhost:8000/api/v1/scrapy/search/voice \
  -F "audio=@audio.wav"

# Image search
curl -X POST http://localhost:8000/api/v1/scrapy/search/image \
  -F "image=@product.jpg"

# Bulk search
curl -X POST http://localhost:8000/api/v1/scrapy/search/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["laptop", "headphones"],
    "retailers": ["amazon", "walmart", "bestbuy"]
  }'

# Get batch status
curl http://localhost:8000/api/v1/scrapy/batch/bulk_1700123456.789

# Get statistics
curl http://localhost:8000/api/v1/scrapy/stats
```

## Configuration

### Environment Variables

```bash
# Scrapy Service
SCRAPY_SERVICE_URL=http://scrapy-service:5000

# CLIP Service
CLIP_SERVICE_URL=http://web-api:8000
ENABLE_CLIP_ANALYSIS=true

# Voice STT
VOICE_STT_URL=http://web-api:8000/api/v1/voice/transcribe
VOICE_STT_PROVIDER=local
VOICE_STT_MODEL=openai/whisper-large-v2

# HAProxy
HAPROXY_URL=http://cumpair-proxy-manager:8080

# Proxy Service
PROXY_SERVICE_URL=http://proxy-api:8001

# CAPTCHA Service
CAPTCHA_SERVICE_URL=http://captcha-solver:9001
CAPTCHA_TIMEOUT=120

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

### Scrapy Settings

```python
# scrapy_service/settings.py

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 30

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
```

## Performance Optimization

### 1. Parallel Scraping
- Concurrent requests: 16 total
- Per domain: 2 concurrent
- Auto-throttling enabled

### 2. Caching
- Redis-backed caching
- 1-hour TTL for products
- Deduplication pipeline

### 3. Bulk Processing
- Batch job processing
- Progress tracking
- Result aggregation

### 4. Proxy Rotation
- HAProxy load balancing
- Automatic proxy rotation
- Health-based selection

## Testing

### Integration Test

```bash
# Run comprehensive integration test
python test_scrapy_integration.py
```

Tests include:
1. ✅ Health check
2. ✅ Retailers endpoint
3. ✅ Basic search
4. ✅ Bulk search
5. ✅ Statistics
6. ✅ All retailers search
7. ✅ Service integrations

### Manual Testing

```bash
# Test Scrapy service directly
curl http://localhost:5000/health

# Test via main API
curl http://localhost:8000/api/v1/scrapy/health

# Interactive API docs
open http://localhost:8000/docs
```

## Monitoring

### Key Metrics

1. **Scraping Performance**
   - Total requests
   - Success rate
   - Average response time
   - Products scraped per retailer

2. **Service Health**
   - Redis connectivity
   - CLIP service availability
   - Voice STT availability
   - CAPTCHA solver availability
   - Proxy service availability

3. **Retailer Performance**
   - Products per retailer
   - Success rate per retailer
   - CAPTCHA encounters
   - Proxy usage

### Logs

```bash
# Scrapy service logs
docker logs scrapy-service

# Main API logs
docker logs web-api

# All services
docker logs --tail=100 -f scrapy-service web-api redis
```

## Troubleshooting

### Common Issues

1. **Scrapy service unavailable**
   - Check service is running: `docker ps | grep scrapy`
   - Check logs: `docker logs scrapy-service`
   - Verify network: `docker network inspect cumpair_default`

2. **No results from search**
   - Check Redis connection
   - Verify retailer selectors are up to date
   - Check for CAPTCHA blocks
   - Review scraper logs

3. **CAPTCHA blocking**
   - Verify 2Captcha service is running
   - Check CAPTCHA API key
   - Review proxy rotation settings
   - Increase delays between requests

4. **Slow performance**
   - Enable Redis caching
   - Increase concurrent requests (carefully)
   - Use bulk search for multiple queries
   - Check proxy performance

## Future Enhancements

- [ ] Add more international retailers
- [ ] Implement machine learning for selector adaptation
- [ ] Add real-time price monitoring
- [ ] Implement distributed scraping with Celery
- [ ] Add GraphQL API support
- [ ] Implement WebSocket for real-time updates
- [ ] Add blockchain verification for price history
- [ ] Implement AI-powered product matching

## Support

For issues or questions:
1. Check logs: `docker logs scrapy-service`
2. Review documentation: `/docs`
3. Run integration tests: `python test_scrapy_integration.py`
4. Check service status: `curl http://localhost:5000/health`
