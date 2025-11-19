# Phase 5: Celery Worker API Reference

## Base URL
```
http://localhost:8009
```

---

## 🏥 Health & Status Endpoints

### GET /health
Check service and worker health

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "celery-worker",
  "timestamp": "2025-01-15T10:30:00",
  "workers_active": 2,
  "queues": ["scraping", "data", "ml", "integration", "notifications"]
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "message": "No workers available",
  "timestamp": "2025-01-15T10:30:00"
}
```

---

### GET /stats
Get detailed worker statistics

**Response (200 OK):**
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "workers": {
    "celery@worker1": {
      "status": "online",
      "queues": 4,
      "processed": 1250
    },
    "celery@worker2": {
      "status": "online",
      "queues": 4,
      "processed": 890
    }
  },
  "active_tasks": 3,
  "queues": ["scraping", "data", "ml", "integration", "notifications"]
}
```

---

### GET /queues
Get configured queue information

**Response (200 OK):**
```json
{
  "queues": [
    {
      "name": "scraping",
      "routing_key": "scraping"
    },
    {
      "name": "ml",
      "routing_key": "ml"
    },
    {
      "name": "integration",
      "routing_key": "integration"
    },
    {
      "name": "data",
      "routing_key": "data"
    },
    {
      "name": "notifications",
      "routing_key": "notifications"
    }
  ]
}
```

---

## 📝 Task Management Endpoints

### POST /task/submit
Submit a task for execution

**Request Body:**
```json
{
  "task_name": "tasks.scraping.scrape_retailer",
  "args": [],
  "kwargs": {
    "retailer": "amazon",
    "priority": 10
  }
}
```

**Response (200 OK):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "submitted"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Invalid task name or parameters"
}
```

**Example Tasks:**
```bash
# Scrape retailer
{
  "task_name": "tasks.scraping.scrape_retailer",
  "kwargs": {"retailer": "amazon"}
}

# Batch scrape
{
  "task_name": "tasks.scraping.batch_scrape",
  "kwargs": {"all_retailers": true}
}

# Process prices
{
  "task_name": "tasks.data.process_prices"
}

# Deduplicate
{
  "task_name": "tasks.data.deduplicate_products",
  "kwargs": {"use_ml": true, "threshold": 0.85}
}

# Fetch news
{
  "task_name": "tasks.integration.fetch_news",
  "kwargs": {"page_size": 100}
}

# Send email
{
  "task_name": "tasks.notifications.send_email",
  "kwargs": {
    "to_email": "user@example.com",
    "subject": "Price Alert",
    "body": "Product price dropped!"
  }
}
```

---

### GET /task/{task_id}
Get task status and result

**Parameters:**
- `task_id` (string, required): Celery task ID

**Response (200 OK - PENDING):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "PENDING",
  "error": "Task not found"
}
```

**Response (200 OK - SUCCESS):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "SUCCESS",
  "result": {
    "retailer": "amazon",
    "product_count": 150,
    "error_count": 0,
    "timestamp": "2025-01-15T10:30:00"
  }
}
```

**Response (200 OK - FAILURE):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "FAILURE",
  "error": "Connection timeout"
}
```

**Task Status Values:**
- `PENDING` - Task waiting for execution
- `STARTED` - Task execution started
- `SUCCESS` - Task completed successfully
- `FAILURE` - Task failed (check error field)
- `RETRY` - Task will be retried
- `REVOKED` - Task was cancelled

---

### POST /task/{task_id}/revoke
Revoke/cancel a task

**Parameters:**
- `task_id` (string, required): Task ID to revoke

**Response (200 OK):**
```json
{
  "status": "revoked",
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

## 📅 Scheduled Tasks Endpoints

### GET /schedule
Get list of scheduled tasks

**Response (200 OK):**
```json
{
  "scheduled_tasks": 11,
  "tasks": [
    {
      "name": "scrape-amazon-hourly",
      "task": "tasks.scraping.scrape_retailer",
      "schedule": "00:01:00 (every 1 hour)",
      "args": ["amazon"],
      "kwargs": {"priority": 10}
    },
    {
      "name": "fetch-news-4h",
      "task": "tasks.integration.fetch_news",
      "schedule": "04:00:00 (every 4 hours)",
      "args": [],
      "kwargs": {"page_size": 100}
    },
    {
      "name": "fetch-crypto-15m",
      "task": "tasks.integration.fetch_crypto",
      "schedule": "00:15:00 (every 15 minutes)",
      "args": [],
      "kwargs": {}
    },
    {
      "name": "rebuild-index-nightly",
      "task": "tasks.ml.rebuild_faiss_index",
      "schedule": "crontab(hour=2, minute=0)",
      "args": [],
      "kwargs": {}
    }
  ]
}
```

---

### POST /schedule/test
Test execute a scheduled task

**Query Parameters:**
- `task_name` (string, required): Name of scheduled task

**Request:**
```bash
POST /schedule/test?task_name=scrape-amazon-hourly
```

**Response (200 OK):**
```json
{
  "status": "executed",
  "task_name": "scrape-amazon-hourly",
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Scheduled task 'invalid-task' not found"
}
```

---

## 🔄 Batch Operations Endpoints

### POST /batch/submit
Submit multiple tasks at once

**Request Body:**
```json
[
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
```

**Response (200 OK):**
```json
{
  "status": "submitted",
  "count": 3,
  "tasks": [
    {
      "task": "tasks.scraping.scrape_retailer",
      "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    },
    {
      "task": "tasks.scraping.scrape_retailer",
      "task_id": "8c6976e5-b5410ff7-8f7ae-1c0e9bedf8b3"
    },
    {
      "task": "tasks.integration.fetch_news",
      "task_id": "0b8c2567-4372-11e7-b114-b82a72d1a78c"
    }
  ]
}
```

---

### POST /batch/status
Get status of multiple tasks

**Request Body:**
```json
{
  "task_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "8c6976e5-b5410ff7-8f7ae-1c0e9bedf8b3",
    "0b8c2567-4372-11e7-b114-b82a72d1a78c"
  ]
}
```

**Response (200 OK):**
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "tasks": [
    {
      "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "SUCCESS",
      "result": {"retailer": "amazon", "product_count": 150}
    },
    {
      "task_id": "8c6976e5-b5410ff7-8f7ae-1c0e9bedf8b3",
      "status": "STARTED",
      "result": null
    },
    {
      "task_id": "0b8c2567-4372-11e7-b114-b82a72d1a78c",
      "status": "FAILURE",
      "result": null
    }
  ]
}
```

---

## 👷 Worker Management Endpoints

### GET /workers
Get list of active workers

**Response (200 OK):**
```json
{
  "worker_count": 2,
  "workers": [
    {
      "name": "celery@worker1",
      "status": "online",
      "active_tasks": 2
    },
    {
      "name": "celery@worker2",
      "status": "online",
      "active_tasks": 1
    }
  ]
}
```

---

### GET /workers/active
Get all active tasks across workers

**Response (200 OK):**
```json
{
  "active_task_count": 3,
  "tasks": [
    {
      "worker": "celery@worker1",
      "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "task_name": "tasks.scraping.scrape_retailer",
      "args": [],
      "kwargs": {"retailer": "amazon"}
    },
    {
      "worker": "celery@worker1",
      "task_id": "8c6976e5-b5410ff7-8f7ae-1c0e9bedf8b3",
      "task_name": "tasks.data.process_prices",
      "args": [],
      "kwargs": {}
    },
    {
      "worker": "celery@worker2",
      "task_id": "0b8c2567-4372-11e7-b114-b82a72d1a78c",
      "task_name": "tasks.integration.fetch_news",
      "args": [],
      "kwargs": {"page_size": 100}
    }
  ]
}
```

---

### POST /workers/shutdown
Gracefully shutdown all workers

**Response (200 OK):**
```json
{
  "status": "shutdown_initiated"
}
```

⚠️ **Warning:** This will stop all worker processes. They will need to be restarted.

---

## ⚡ Shortcut Endpoints (Quick Submit)

### POST /tasks/scrape-retailer
Quick scrape a retailer

**Query Parameters:**
- `retailer` (string, required): amazon, flipkart, ebay
- `priority` (int, optional): 1-10 (default: 10)

**Request:**
```bash
POST /tasks/scrape-retailer?retailer=amazon&priority=10
```

**Response:**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "submitted"
}
```

---

### POST /tasks/batch-scrape
Quick batch scrape

**Query Parameters:**
- `all_retailers` (boolean, optional): true/false (default: true)

**Request:**
```bash
POST /tasks/batch-scrape?all_retailers=true
```

---

### POST /tasks/process-prices
Quick price processing

**Request:**
```bash
POST /tasks/process-prices
```

---

### POST /tasks/fetch-news
Quick news fetch

**Query Parameters:**
- `page_size` (int, optional): 1-100 (default: 100)

**Request:**
```bash
POST /tasks/fetch-news?page_size=50
```

---

### POST /tasks/send-notification
Quick send notification

**Query Parameters:**
- `notification_type` (string, required): email, sms, or push
- `recipient` (string, required): email address, phone, or user ID
- `message` (string, required): notification message

**Request:**
```bash
POST /tasks/send-notification \
  ?notification_type=email \
  &recipient=user@example.com \
  &message=Your%20product%20price%20dropped
```

**Response:**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "submitted"
}
```

---

## 📝 Data Models

### TaskRequest
```json
{
  "task_name": "string (required)",
  "args": ["array of arguments (optional)"],
  "kwargs": {"object with keyword arguments (optional)"}
}
```

### TaskResponse
```json
{
  "task_id": "string (Celery task ID)",
  "status": "string (PENDING|STARTED|SUCCESS|FAILURE|RETRY|REVOKED)",
  "result": "object or null",
  "error": "string or null (only if FAILURE or RETRY)"
}
```

---

## 🔄 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid task name or parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Scheduled task 'name' not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error description"
}
```

### 503 Service Unavailable
```json
{
  "status": "unhealthy",
  "error": "No workers available"
}
```

---

## 🔐 Authentication

Currently no authentication required. For production, add:
- API key validation
- JWT tokens
- OAuth 2.0

---

## 🎯 Rate Limits

- No rate limits configured by default
- Configure per-queue limits as needed
- Flower dashboard available for monitoring

---

## 📊 Common Workflows

### Complete Pipeline
```bash
# 1. Submit batch scrape
curl -X POST http://localhost:8009/tasks/batch-scrape

# 2. Wait for completion (poll every 5 seconds)
curl http://localhost:8009/task/{task_id}

# 3. Submit price processing
curl -X POST http://localhost:8009/tasks/process-prices

# 4. Submit deduplication
curl -X POST http://localhost:8009/task/submit \
  -d '{"task_name": "tasks.data.deduplicate_products"}'
```

### Monitoring Active Work
```bash
# Check active tasks
curl http://localhost:8009/workers/active | jq '.tasks | length'

# Get worker stats
curl http://localhost:8009/stats | jq '.workers'

# View scheduled tasks
curl http://localhost:8009/schedule | jq '.tasks | length'
```

---

## 📚 Related Services

- **API Gateway:** http://localhost:8000
- **Flower Dashboard:** http://localhost:5555
- **Data Pipeline:** http://localhost:8006
- **Scraper Optimization:** http://localhost:8007
- **Multi-Source Integration:** http://localhost:8008
