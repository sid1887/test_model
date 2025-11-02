# 🔥 GOD ENGINE - EXECUTION GUIDE

## Complete System Launch & Testing

### 🚀 QUICK START (5 Commands)

```powershell
# 1. Start all services
docker-compose -f docker-compose.secure.yml up -d

# 2. Wait for services to be ready (30 seconds)
Start-Sleep -Seconds 30

# 3. Start event workers
docker exec -d test_model-web-1 python -m app.workers.manager

# 4. Run comprehensive tests
docker exec test_model-web-1 pytest tests/test_god_engine.py -v --asyncio-mode=auto

# 5. Run live demonstration
docker exec test_model-web-1 python demo_god_engine.py
```

---

## 📋 DETAILED EXECUTION STEPS

### Step 1: Environment Check

```powershell
# Check Docker is running
docker --version

# Check available resources
docker system df

# Clean old containers (optional)
docker-compose down --remove-orphans
```

### Step 2: Service Startup

```powershell
# Start all services with logs
docker-compose -f docker-compose.secure.yml up --build

# OR in detached mode
docker-compose -f docker-compose.secure.yml up -d --build

# Verify all services are up
docker-compose ps
```

**Expected Output:**
```
NAME                     STATUS    PORTS
test_model-web-1         Up        0.0.0.0:8000->8000/tcp
test_model-postgres-1    Up        5432/tcp
test_model-redis-1       Up        6379/tcp
test_model-redis-cache-1 Up        6379/tcp
test_model-redis-queue-1 Up        6379/tcp
test_model-scraper-1     Up        0.0.0.0:3000->3000/tcp
```

### Step 3: Health Verification

```powershell
# Check API health
curl http://localhost:8000/health

# Check service health
curl http://localhost:8000/health/services | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Check scraper health
curl http://localhost:3000/health
```

**Expected Health Response:**
```json
{
  "status": "healthy",
  "services": {
    "web_api": {"healthy": true, "latency_ms": 5},
    "postgres": {"healthy": true, "latency_ms": 10},
    "redis": {"healthy": true, "latency_ms": 2},
    "scraper": {"healthy": true, "latency_ms": 50}
  }
}
```

### Step 4: Start Event Workers

```powershell
# Start workers in background
docker exec -d test_model-web-1 python -m app.workers.manager

# Verify workers are running
docker exec test_model-web-1 ps aux | Select-String "worker"

# Check worker logs
docker exec test_model-web-1 tail -f /tmp/worker.log
```

**Expected Worker Output:**
```
🚀 Worker Manager Started
📦 Scraper Worker: READY
🖼️  Image AI Worker: READY
⚡ Listening for events...
```

### Step 5: Run Comprehensive Tests

```powershell
# Run all God Engine tests
docker exec test_model-web-1 pytest tests/test_god_engine.py -v --asyncio-mode=auto

# Run specific test categories
docker exec test_model-web-1 pytest tests/test_god_engine.py::TestCacheLayer -v
docker exec test_model-web-1 pytest tests/test_god_engine.py::TestPerformance -v
docker exec test_model-web-1 pytest tests/test_god_engine.py::TestE2E -v

# With coverage
docker exec test_model-web-1 pytest tests/test_god_engine.py --cov=app --cov-report=html
```

**Expected Test Output:**
```
tests/test_god_engine.py::TestCacheLayer::test_l1_cache_set_get PASSED
tests/test_god_engine.py::TestCacheLayer::test_l2_cache_with_ttl PASSED
tests/test_god_engine.py::TestQueryOptimizer::test_search_with_cache PASSED
tests/test_god_engine.py::TestHuggingFaceClient::test_sentiment_analysis PASSED
tests/test_god_engine.py::TestSearchAPI::test_unified_search PASSED
tests/test_god_engine.py::TestPerformance::test_search_latency PASSED
tests/test_god_engine.py::TestE2E::test_complete_search_flow PASSED

======================== 30 passed in 45.2s ========================
```

### Step 6: Live System Demonstration

```powershell
# Run interactive demonstration
docker exec -it test_model-web-1 python demo_god_engine.py
```

**Expected Demo Output:**
```
🔥 GOD ENGINE DEMONSTRATION

✅ DEMO 1: Service Health - All services operational
✅ DEMO 2: Unified Search - 10 products in 185ms (cache hit)
✅ DEMO 3: Streaming Search - Ghost→Real→Enriched→Complete
✅ DEMO 4: Cache Performance - 92% speed improvement
✅ DEMO 5: Metrics - Prometheus operational

🎯 Success Rate: 5/5 (100%)
🎉 ALL DEMONSTRATIONS PASSED!
```

---

## 🧪 MANUAL API TESTING

### Test 1: Unified Search

```powershell
# Basic search
curl "http://localhost:8000/api/v2/search?q=iPhone%2015&limit=10" | ConvertFrom-Json | ConvertTo-Json -Depth 10

# With AI enrichment
curl "http://localhost:8000/api/v2/search?q=iPhone%2015&limit=10&enrich=true" | ConvertFrom-Json | ConvertTo-Json -Depth 10

# With vector search
curl "http://localhost:8000/api/v2/search?q=laptop&limit=5&use_vector=true" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 2: Streaming Search (SSE)

```powershell
# Stream search results
curl -N "http://localhost:8000/api/v2/search/stream?q=MacBook&limit=5"
```

**Expected SSE Stream:**
```
data: {"phase": "ghost", "results": [...], "timestamp": "..."}
data: {"phase": "real", "results": [...], "timestamp": "..."}
data: {"phase": "enriched", "results": [...], "timestamp": "..."}
data: {"phase": "realtime", "results": [...], "timestamp": "..."}
data: {"phase": "complete", "message": "Search complete"}
```

### Test 3: Image Search V2

```powershell
# Upload image for search
curl -X POST http://localhost:8000/api/v2/search/image `
  -F "file=@path/to/product.jpg" `
  -F "limit=10" `
  -F "enrich=true" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 4: Complete Product Context

```powershell
# Get all context for a product
curl "http://localhost:8000/api/v2/product/123/complete" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
  "product": {...},
  "ai_analysis": {
    "sentiment": {...},
    "entities": [...],
    "summary": "..."
  },
  "realtime_context": {
    "stocks": {...},
    "crypto": {...},
    "news": [...]
  },
  "similar_products": [...],
  "price_history": [...]
}
```

---

## 📊 MONITORING & METRICS

### Prometheus Metrics

```powershell
# View all metrics
curl http://localhost:8000/metrics

# Filter specific metrics
curl http://localhost:8000/metrics | Select-String "http_requests"
curl http://localhost:8000/metrics | Select-String "cache_hits"
curl http://localhost:8000/metrics | Select-String "ai_inference"
```

**Key Metrics to Monitor:**
- `http_requests_total` - Total API requests
- `http_request_duration_seconds` - Request latency
- `cache_hits_total` - Cache efficiency
- `cache_misses_total` - Cache misses
- `scrape_requests_total` - Scraping activity
- `ai_inference_total` - AI model usage
- `db_query_duration_seconds` - Database performance

### Service Health Dashboard

```powershell
# Real-time service health
while ($true) {
    Clear-Host
    curl http://localhost:8000/health/services | ConvertFrom-Json | ConvertTo-Json -Depth 10
    Start-Sleep -Seconds 5
}
```

---

## 🎨 FRONTEND INTEGRATION

### Generate API Client & Types

```powershell
# Generate TypeScript types and API client
docker exec test_model-web-1 python scripts/generate_frontend_api.py

# Copy generated files to frontend
docker cp test_model-web-1:/app/frontend/src/api/openapi.json ./frontend/src/api/
docker cp test_model-web-1:/app/frontend/src/api/types.ts ./frontend/src/api/
docker cp test_model-web-1:/app/frontend/src/api/client.ts ./frontend/src/api/
docker cp test_model-web-1:/app/frontend/src/api/hooks.ts ./frontend/src/api/
```

**Generated Files:**
- `openapi.json` - OpenAPI 3.0 schema
- `types.ts` - TypeScript interfaces for all DTOs
- `client.ts` - API client with all endpoints
- `hooks.ts` - React Query hooks (useUnifiedSearch, useImageSearch, etc.)

### Use in React Component

```typescript
import { useUnifiedSearch } from '@/api/hooks';

function SearchComponent() {
  const { data, isLoading } = useUnifiedSearch({
    q: "iPhone 15",
    limit: 10,
    enrich: true
  });

  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div>
      {data?.results.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

---

## 🔍 DEBUGGING

### Check Logs

```powershell
# Web API logs
docker logs test_model-web-1 --tail 100 -f

# Scraper logs
docker logs test_model-scraper-1 --tail 100 -f

# Database logs
docker logs test_model-postgres-1 --tail 100 -f

# Redis logs
docker logs test_model-redis-1 --tail 100 -f
```

### Inspect Container

```powershell
# Enter web container
docker exec -it test_model-web-1 bash

# Check Python environment
python -c "import app; print(app.__file__)"

# Test imports
python -c "from app.services.huggingface_client import hf_client; print(hf_client)"

# Check Redis connectivity
python -c "from app.core.cache import cache_manager; import asyncio; asyncio.run(cache_manager.connect()); print('Connected')"
```

### Database Queries

```powershell
# Connect to PostgreSQL
docker exec -it test_model-postgres-1 psql -U cumpair_user -d cumpair_db

# Check tables
\dt

# Count products
SELECT COUNT(*) FROM products;

# Recent snapshots
SELECT * FROM product_snapshots ORDER BY created_at DESC LIMIT 10;
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### Cache Warming

```powershell
# Pre-populate cache with common queries
$queries = @("iPhone", "MacBook", "PS5", "Xbox", "laptop")
foreach ($q in $queries) {
    curl "http://localhost:8000/api/v2/search?q=$q&limit=10&use_cache=true"
}
```

### Database Indexing

```sql
-- Create indexes for performance
CREATE INDEX idx_products_name ON products USING gin(to_tsvector('english', name));
CREATE INDEX idx_snapshots_product_id ON product_snapshots(product_id);
CREATE INDEX idx_snapshots_created_at ON product_snapshots(created_at DESC);
```

---

## 🚨 TROUBLESHOOTING

### Issue: Tests Failing

**Symptom:** `pytest tests/test_god_engine.py` fails

**Solutions:**
```powershell
# 1. Check HuggingFace API key
docker exec test_model-web-1 echo $HUGGINGFACE_API_KEY

# 2. Set API key if missing
docker-compose -f docker-compose.secure.yml down
$env:HUGGINGFACE_API_KEY="hf_your_api_key_here"
docker-compose -f docker-compose.secure.yml up -d

# 3. Skip AI tests if no API key
docker exec test_model-web-1 pytest tests/test_god_engine.py -v -k "not huggingface"
```

### Issue: Cache Not Working

**Symptom:** `cache_hit` always false

**Solutions:**
```powershell
# 1. Check Redis connectivity
docker exec test_model-web-1 python -c "import redis; r = redis.Redis(host='redis-cache', port=6379); print(r.ping())"

# 2. Restart Redis
docker-compose -f docker-compose.secure.yml restart redis-cache

# 3. Check cache logs
docker logs test_model-redis-cache-1
```

### Issue: Scraper Timeout

**Symptom:** Image search returns 503

**Solutions:**
```powershell
# 1. Check scraper health
curl http://localhost:3000/health

# 2. Restart scraper
docker-compose -f docker-compose.secure.yml restart scraper

# 3. Check scraper logs
docker logs test_model-scraper-1 --tail 50
```

---

## 📈 LOAD TESTING

### Using Apache Bench (ab)

```powershell
# Install Apache Bench (if not available)
# Chocolatey: choco install apache-httpd

# 100 requests, 10 concurrent
ab -n 100 -c 10 "http://localhost:8000/api/v2/search?q=test&limit=10"

# With keep-alive
ab -n 1000 -c 50 -k "http://localhost:8000/api/v2/search?q=laptop&limit=5"
```

### Using PowerShell

```powershell
# Simple load test
1..100 | ForEach-Object -Parallel {
    $response = Invoke-WebRequest "http://localhost:8000/api/v2/search?q=test&limit=10"
    $response.StatusCode
} -ThrottleLimit 10
```

---

## 🎯 SUCCESS CRITERIA

### ✅ System is Operational When:

1. **All Services Healthy**
   - `curl http://localhost:8000/health/services` returns all green
   
2. **Tests Pass**
   - `pytest tests/test_god_engine.py` shows 30/30 passed
   
3. **API Responding**
   - Unified search returns results in <2s (cold)
   - Cached searches return in <200ms
   
4. **Workers Active**
   - Event workers processing scrape requests
   - Image AI worker enriching products
   
5. **Metrics Flowing**
   - `curl http://localhost:8000/metrics` shows non-zero counters
   
6. **Frontend Integration Ready**
   - `scripts/generate_frontend_api.py` generates all files
   - TypeScript types compile without errors

---

## 🔥 FINAL CHECKLIST

- [ ] Docker services running (`docker-compose ps`)
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] Workers started (`docker exec -d test_model-web-1 python -m app.workers.manager`)
- [ ] Tests pass (`pytest tests/test_god_engine.py`)
- [ ] Demo successful (`python demo_god_engine.py`)
- [ ] API responding (`curl http://localhost:8000/api/v2/search?q=test`)
- [ ] Metrics available (`curl http://localhost:8000/metrics`)
- [ ] Frontend files generated (`python scripts/generate_frontend_api.py`)

---

## 📞 NEXT STEPS

After successful execution:

1. **Integrate Frontend**: Use generated API client in React
2. **Load Testing**: Run comprehensive performance tests
3. **Fix Scrapers**: Update Walmart/eBay selectors
4. **Deploy to Production**: Kubernetes manifests
5. **Add API Gateway**: Kong or Envoy for rate limiting
6. **Scale Database**: Read replicas and partitioning

---

## 🎉 SUCCESS!

If all steps passed:

```
🔥🔥🔥 GOD ENGINE IS FULLY OPERATIONAL 🔥🔥🔥

✅ Infrastructure Layer: Multi-tier cache, service registry
✅ AI/ML Pipeline: 10 HuggingFace models + CLIP
✅ Query Optimization: <200ms target achieved
✅ Real-Time Data: Stocks, crypto, news integrated
✅ Search API V2: Unified, streaming, image, voice
✅ Frontend Integration: TypeScript types + React hooks
✅ Testing Infrastructure: 30+ tests passing
✅ Observability: Prometheus metrics operational

🚀 Ready for production deployment!
```
