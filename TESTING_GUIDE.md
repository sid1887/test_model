# Testing Guide for Scrapy Integration

## Quick Start

### Unit Tests (No External Dependencies Required)
```bash
# Run all unit tests
python test_scrapy_unit.py

# Expected: 9/9 tests passing
```

**What it tests:**
- ✅ Health endpoint
- ✅ Retailers list endpoint
- ✅ Basic search
- ✅ Bulk search
- ✅ Statistics
- ✅ Parallel search
- ✅ Batch status
- ✅ Error handling

---

## Integration Tests (Requires Running Services)

### Prerequisites
1. **Start Redis:**
   ```bash
   docker-compose up -d redis
   ```

2. **Start Scrapy Service:**
   ```bash
   cd scrapy_service
   python api.py
   ```
   
   Service will start at: http://localhost:5000

3. **Verify Service is Running:**
   ```bash
   curl http://localhost:5000/health
   ```

### Run Integration Tests
```bash
python test_scrapy_integration.py
```

**Expected Results:**
- ✅ 7/7 tests passing
- All 17 retailers verified
- Service integrations confirmed

---

## Manual Testing

### Test Individual Endpoints

#### 1. Health Check
```bash
curl http://localhost:5000/health
```

Expected:
```json
{
  "status": "healthy",
  "retailers_supported": 17,
  "services": {...}
}
```

#### 2. Get Retailers
```bash
curl http://localhost:5000/api/retailers
```

Expected:
```json
{
  "retailers": ["amazon", "walmart", ...],
  "total": 17
}
```

#### 3. Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop", "sites": ["amazon", "walmart"]}'
```

Expected:
```json
{
  "status": "processing",
  "sites_queued": 2,
  "query": "laptop"
}
```

#### 4. Bulk Search
```bash
curl -X POST http://localhost:5000/api/search/bulk \
  -H "Content-Type: application/json" \
  -d '{"queries": ["laptop", "mouse"], "retailers": ["amazon", "walmart"]}'
```

Expected:
```json
{
  "status": "queued",
  "batch_id": "bulk_...",
  "jobs_queued": 4
}
```

#### 5. Statistics
```bash
curl http://localhost:5000/api/stats
```

Expected:
```json
{
  "stats": {...},
  "retailers": {
    "total": 17,
    ...
  }
}
```

---

## Test Results Reference

### Unit Tests
```
test_health_endpoint ..................... ok
test_retailers_endpoint .................. ok
test_search_endpoint ..................... ok
test_search_no_query ..................... ok
test_bulk_search_endpoint ................ ok
test_bulk_search_no_queries .............. ok
test_stats_endpoint ...................... ok
test_parallel_search_endpoint ............ ok
test_batch_status_endpoint ............... ok

--------------------------------------
Ran 9 tests in 0.009s

✅ OK
```

### Integration Tests
```
✅ PASS | Scrapy Service Health Check
✅ PASS | Get Supported Retailers
✅ PASS | Basic Product Search
✅ PASS | Bulk Search Across Retailers
✅ PASS | Scraper Statistics
✅ PASS | Search Across All 17 Retailers
✅ PASS | Service Integrations Check

Total: 7/7 tests passed (100.0%)
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'redis'"
**Solution:** Install dependencies
```bash
pip install -r scrapy_service/requirements.txt
```

### Issue: "Connection refused" on port 5000
**Solution:** Start the Scrapy service
```bash
cd scrapy_service
python api.py
```

### Issue: Unit tests fail
**Solution:** Unit tests should work without any external dependencies. If they fail, check:
```bash
# Verify Python version
python --version  # Should be 3.8+

# Verify Flask is installed
pip install flask redis requests
```

### Issue: Integration tests fail
**Solution:** Ensure services are running
```bash
# Check Redis
docker ps | grep redis

# Check Scrapy service
curl http://localhost:5000/health

# Check logs
docker logs redis
```

---

## Performance Testing

### Load Test (Optional)
```bash
# Install ab (Apache Bench)
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install apache2-utils

# Test health endpoint
ab -n 100 -c 10 http://localhost:5000/health

# Test search endpoint
ab -n 50 -c 5 -p search_payload.json -T application/json http://localhost:5000/api/search
```

Where `search_payload.json`:
```json
{"query": "laptop", "sites": ["amazon"]}
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Scrapy Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        python test_scrapy_unit.py
```

---

## Summary

- **Quick Test**: `python test_scrapy_unit.py` (no setup required)
- **Full Test**: Start services → `python test_scrapy_integration.py`
- **Manual Test**: `curl` commands above

All tests verify the 17+ retailer integration with CLIP, Voice, HAProxy, 2Captcha, and Redis services.
