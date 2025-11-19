# Phase 5: Quick Start Guide - Celery Background Jobs

## 🚀 30-Second Start

```bash
# 1. Start infrastructure (from workspace root)
docker-compose -f docker-compose.services.yml up -d \
  --profile phase5 \
  redis postgres

# 2. Build Celery services
docker-compose -f docker-compose.services.yml build \
  celery-worker celery-beat flower

# 3. Start services
docker-compose -f docker-compose.services.yml up -d \
  --profile phase5 \
  celery-worker celery-beat flower

# 4. Verify health
curl http://localhost:8009/health
```

---

## 📋 What's Running

| Service | Port | Command |
|---------|------|---------|
| **Redis** | 6379 | Message broker + result backend |
| **Celery Worker** | 8009 | Task execution (FastAPI) |
| **Celery Beat** | - | Scheduled task manager |
| **Flower** | 5555 | Monitoring dashboard |
| **PostgreSQL** | 5432 | Task data storage |

---

## 🎯 Common Tasks (5 minutes each)

### Submit a Scraping Task
```bash
curl -X POST http://localhost:8009/task/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "tasks.scraping.scrape_retailer",
    "kwargs": {
      "retailer": "amazon",
      "priority": 10
    }
  }'

# Response:
# {"task_id": "abc123def456", "status": "submitted"}
```

### Check Task Status
```bash
curl http://localhost:8009/task/abc123def456

# Response:
# {
#   "task_id": "abc123def456",
#   "status": "SUCCESS",
#   "result": {
#     "retailer": "amazon",
#     "product_count": 150,
#     "timestamp": "2025-01-15T10:30:00"
#   }
# }
```

### Batch Submit Tasks
```bash
curl -X POST http://localhost:8009/batch/submit \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "task_name": "tasks.scraping.scrape_retailer",
        "kwargs": {"retailer": "amazon"}
      },
      {
        "task_name": "tasks.scraping.scrape_retailer",
        "kwargs": {"retailer": "flipkart"}
      },
      {
        "task_name": "tasks.integration.fetch_news",
        "kwargs": {"page_size": 50}
      }
    ]
  }'
```

### Check Worker Status
```bash
curl http://localhost:8009/workers

# Response:
# {
#   "worker_count": 1,
#   "workers": [
#     {
#       "name": "celery@worker1",
#       "status": "online",
#       "active_tasks": 3
#     }
#   ]
# }
```

### View All Active Tasks
```bash
curl http://localhost:8009/workers/active
```

### View Scheduled Tasks
```bash
curl http://localhost:8009/schedule

# Shows:
# - Hourly: Scrape Amazon, Flipkart
# - 4-hourly: Fetch news
# - 15-min: Fetch crypto
# - Daily: Data processing
# - Weekly: Trend analysis
```

### Send a Notification
```bash
curl -X POST http://localhost:8009/tasks/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "recipient": "user@example.com",
    "message": "Product price dropped!"
  }'
```

---

## 🎛️ Monitoring Dashboard

### Flower Web UI
```
http://localhost:5555
```

**What you can see:**
- Real-time active tasks
- Worker status and uptime
- Task execution history
- Success/failure rates
- Task details and results
- Worker pool information
- Performance graphs

**Example workflow:**
1. Open http://localhost:5555 in browser
2. Click "Workers" tab to see active workers
3. Click "Tasks" tab to see recent executions
4. Click on a task to see details
5. Click "Graphs" tab for performance metrics

---

## 🔄 Scheduled Tasks (Automatic)

These run automatically without manual submission:

### Hourly Tasks
```
Every 1 hour:
  → Scrape Amazon
  → Scrape Flipkart
```

### 4-Hourly Tasks
```
Every 4 hours:
  → Fetch news articles
```

### 15-Minute Tasks
```
Every 15 minutes:
  → Fetch crypto prices
```

### Daily Tasks
```
Every 24 hours:
  → Full retailer scrape
  → Process prices
  → Normalize data
  → Stock price update
```

### Nightly Task (2 AM UTC)
```
Every night at 2 AM:
  → Rebuild FAISS index
```

### Weekly Task
```
Every week (Monday):
  → Trend analysis
```

---

## 📊 Example: Complete Daily Pipeline

```bash
# This runs automatically, but you can trigger manually:

curl -X POST http://localhost:8009/tasks/batch-scrape \
  -H "Content-Type: application/json" \
  -d '{"all_retailers": true}'

# Task sequence:
# 1. Batch scrape all retailers (concurrent)
# 2. Process and aggregate prices
# 3. Normalize product data
# 4. Detect and merge duplicates
# 5. Analyze trends
# 6. Store results in database
# 7. Send notifications for price alerts
```

---

## 🔍 Queue Status

```bash
# Check which tasks are in which queues
curl http://localhost:8009/queues

# Response shows 5 queues:
# - scraping (priority 10)    ← Product scraping
# - ml (priority 9)            ← Embeddings, training
# - integration (priority 7)   ← External APIs
# - data (priority 8)          ← Processing, normalization
# - notifications (priority 4) ← Email, SMS, push
```

---

## 🛠️ Troubleshooting

### No Workers Available
```bash
# Check if worker is running
curl http://localhost:8009/health

# Restart worker
docker-compose -f docker-compose.services.yml restart celery-worker

# Check worker logs
docker logs test_model-celery-worker-1
```

### Tasks Not Executing
```bash
# Check if Redis is running
redis-cli ping

# Check scheduler
docker logs test_model-celery-beat-1

# Check worker queue stats
curl http://localhost:8009/stats
```

### High Task Failure Rate
```bash
# View failed tasks in Flower
http://localhost:5555

# Check worker capacity
curl http://localhost:8009/workers

# Consider scaling: add more workers
```

---

## 🎯 Integration with Other Services

### With Data Pipeline (8006)
```bash
# Data pipeline handles deduplication
Tasks call: POST /api/products/link
           POST /api/products/deduplicate-candidates
```

### With Scraper Optimization (8007)
```bash
# Scheduled scraping tasks use optimized concurrent scraping
Tasks call: POST /api/scraper/batch
           GET /api/scraper/cache/stats
```

### With Multi-Source Integration (8008)
```bash
# Scheduled fetch tasks get external data
Tasks call: POST /api/news/fetch
           POST /api/crypto/fetch
           POST /api/stocks/fetch
```

### With API Gateway (8000)
```bash
# Submit tasks via gateway
curl -X POST http://localhost:8000/api/celery/task/submit
```

---

## 📈 Performance Tips

### Scale Up
```bash
# Run multiple workers
docker run -d --name worker2 \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  test_model-celery-worker:latest \
  celery -A tasks worker --concurrency=8
```

### Monitor Performance
```bash
# Watch queue depth
while true; do
  curl -s http://localhost:8009/stats | jq '.active_tasks'
  sleep 5
done
```

### Adjust Concurrency
```bash
# In environment or docker-compose
CELERY_CONCURRENCY=8  # Default: 4
```

---

## 🚀 Next Steps

1. **Set up notifications:**
   - Configure SendGrid for emails
   - Configure Twilio for SMS
   - Configure Firebase for push

2. **Add custom tasks:**
   - Edit services/celery-worker/tasks.py
   - Add your business logic
   - Rebuild Docker image

3. **Monitor in production:**
   - Set up Prometheus + Grafana
   - Export Flower metrics
   - Alert on task failures

4. **Scale horizontally:**
   - Run multiple workers
   - Use load balancing
   - Configure worker pools

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| **services/celery-worker/main.py** | FastAPI worker API (800 lines) |
| **services/celery-worker/tasks.py** | Task definitions (400 lines) |
| **services/celery-worker/celery_config.py** | Configuration (200 lines) |
| **services/celery-worker/celery_app.py** | App initialization (50 lines) |
| **services/celery-beat/main.py** | Scheduler service (50 lines) |
| **docker/Dockerfile.celery-worker** | Worker Docker image |
| **docker/Dockerfile.celery-beat** | Beat Docker image |
| **requirements-celery.txt** | Python dependencies |

---

## ✨ Key Features Implemented

✅ **Task Queue** - 16+ tasks across 5 categories
✅ **Scheduling** - 12+ recurring tasks (hourly to weekly)
✅ **Monitoring** - Flower dashboard + REST endpoints
✅ **Retry Logic** - Exponential backoff (3 attempts)
✅ **Priority Queues** - 5 independent queues
✅ **Error Handling** - Comprehensive error catching
✅ **Async I/O** - Full async/await throughout
✅ **Database Integration** - PostgreSQL data persistence
✅ **API Integration** - NewsAPI, CoinGecko, yfinance
✅ **Notifications** - Email, SMS, push ready
✅ **Health Checks** - Service health endpoints
✅ **Batch Operations** - Submit/track multiple tasks

---

## 🎊 Status: Phase 5 COMPLETE

✅ Celery worker service (800 lines)
✅ Task definitions (400+ lines)
✅ Beat scheduler
✅ Flower monitoring
✅ Docker integration
✅ Docker Compose configuration
✅ Health checks
✅ API endpoints
✅ Documentation

**Ready for:** Phase 6 (Database Optimization)
