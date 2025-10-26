# 🚀 Complete Build & Test Guide

## 📋 Table of Contents
1. [Quick Start - Full Stack](#quick-start---full-stack)
2. [Individual Service Build Commands](#individual-service-build-commands)
3. [Environment Setup](#environment-setup)
4. [Testing Commands](#testing-commands)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start - Full Stack

### Complete Build & Deploy (All Services)
```bash
# Navigate to project root
cd d:\dev_packages\test_model

# Step 1: Clean up old containers
docker-compose down -v

# Step 2: Build all services from scratch
docker-compose build --no-cache

# Step 3: Start all core services (web, redis, postgres)
docker-compose up -d

# Step 4: Verify services are healthy
docker-compose ps
docker logs test_model-web-1
```

---

## 🏗️ Individual Service Build Commands

### 1. **Backend Web Service**
```bash
# Build backend only
docker-compose build web

# Start backend
docker-compose up -d web

# View logs
docker logs -f test_model-web-1

# Stop backend
docker-compose stop web
```

### 2. **Frontend React Service**
```bash
# Build frontend only
docker-compose build frontend

# Start frontend (with profile)
docker-compose --profile frontend up -d frontend

# View logs
docker logs -f test_model-frontend-1

# Stop frontend
docker-compose --profile frontend stop frontend

# Rebuild with no cache (for TypeScript errors)
docker-compose build --no-cache frontend
```

### 3. **Celery Worker**
```bash
# Build worker
docker-compose build worker

# Start worker (requires profile)
docker-compose --profile worker up -d worker

# View logs
docker logs -f test_model-worker-1

# Scale to 2 workers
docker-compose --profile worker up -d --scale worker=2

# Stop all workers
docker-compose --profile worker stop worker
```

### 4. **Flower Monitoring (Celery Dashboard)**
```bash
# Build Flower
docker-compose build flower

# Start Flower with worker profile
docker-compose --profile worker up -d flower

# Access at: http://localhost:5555

# View logs
docker logs -f test_model-flower-1

# Stop Flower
docker-compose --profile worker stop flower
```

### 5. **Node.js Scraper Service**
```bash
# Build scraper
docker-compose build scraper

# Start scraper (requires profile)
docker-compose --profile scraper up -d scraper

# View logs
docker logs -f test_model-scraper-1

# Stop scraper
docker-compose --profile scraper stop scraper
```

### 6. **Database Services**
```bash
# Start only database services
docker-compose up -d postgres redis

# Verify databases are healthy
docker-compose ps

# View PostgreSQL logs
docker logs -f test_model-postgres-1

# View Redis logs
docker logs -f test_model-redis-1
```

### 7. **Monitoring Stack (Prometheus + Grafana)**
```bash
# Build monitoring services
docker-compose build prometheus grafana

# Start monitoring (requires profile)
docker-compose --profile monitor up -d prometheus grafana

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3002 (admin/admin)

# View logs
docker logs -f test_model-prometheus-1
docker logs -f test_model-grafana-1

# Stop monitoring
docker-compose --profile monitor stop prometheus grafana
```

---

## ⚙️ Environment Setup

### 1. **Set Environment Variables (Windows PowerShell)**
```powershell
# Set for current session
$env:VITE_API_URL = "http://localhost:8000"
$env:VITE_SERVICE_NAME = "cumpair"
$env:DEBUG = "false"
$env:LOG_LEVEL = "INFO"

# Or create .env file
@"
VITE_API_URL=http://localhost:8000
VITE_SERVICE_NAME=cumpair
VITE_DEMO_MODE=false
DEBUG=false
LOG_LEVEL=INFO
SENDGRID_API_KEY=your-key-here
TWILIO_ACCOUNT_SID=your-sid-here
TWILIO_AUTH_TOKEN=your-token-here
"@ | Out-File -Encoding UTF8 .env
```

### 2. **Notification Provider Configuration**
```powershell
# Set SendGrid API Key
$env:SENDGRID_API_KEY = "your-sendgrid-key"

# Set Twilio credentials
$env:TWILIO_ACCOUNT_SID = "your-account-sid"
$env:TWILIO_AUTH_TOKEN = "your-auth-token"

# Set Firebase credentials (path to JSON file)
$env:FIREBASE_CREDENTIALS_PATH = "./firebase-credentials.json"
```

---

## 🧪 Testing Commands

### Health Checks
```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# Check frontend (through Docker)
docker exec test_model-frontend-1 curl -s http://localhost:3000 | head -20

# Check Redis
docker exec test_model-redis-1 redis-cli ping

# Check PostgreSQL
docker exec test_model-postgres-1 psql -U compair -d compair -c "SELECT version();"

# Check scraper
curl http://localhost:3001/health

# Check Celery worker status
docker exec test_model-worker-1 celery -A app.worker inspect active

# Check Flower
curl http://localhost:5555/
```

### API Testing

#### 1. **Test Metrics Endpoint**
```bash
# Get Prometheus metrics
curl http://localhost:8000/api/metrics

# Get health metrics
curl http://localhost:8000/api/metrics/health

# Get debug metrics
curl http://localhost:8000/api/metrics/debug
```

#### 2. **Test Price Alerts API**
```bash
# Create alert
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "target_price": 29.99,
    "operator": "<=",
    "channels": ["email"],
    "frequency": "immediate",
    "priority": "normal"
  }'

# Get alerts
curl http://localhost:8000/api/alerts

# Get alert by ID
curl http://localhost:8000/api/alerts/1

# Update alert
curl -X PUT http://localhost:8000/api/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{"target_price": 25.99}'

# Delete alert
curl -X DELETE http://localhost:8000/api/alerts/1

# Pause alert
curl -X PATCH http://localhost:8000/api/alerts/1/pause

# Resume alert
curl -X PATCH http://localhost:8000/api/alerts/1/resume
```

#### 3. **Test Smart Lists API**
```bash
# Create list
curl -X POST http://localhost:8000/api/lists \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Budget Electronics",
    "description": "Items under $100",
    "user_id": 1
  }'

# Get lists
curl http://localhost:8000/api/lists

# Get list details
curl http://localhost:8000/api/lists/1

# Add item to list
curl -X POST http://localhost:8000/api/lists/1/items \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "desired_price": 49.99}'

# Get list items
curl http://localhost:8000/api/lists/1/items

# Start comparison
curl -X POST http://localhost:8000/api/lists/1/compare \
  -H "Content-Type: application/json" \
  -d '{}'

# Get comparison results
curl http://localhost:8000/api/lists/1/compare/results
```

#### 4. **Test Analytics API**
```bash
# Get overview
curl http://localhost:8000/api/analytics/overview

# Get price trends
curl "http://localhost:8000/api/analytics/trends?product_id=1&days=30"

# Get sentiment analysis
curl "http://localhost:8000/api/analytics/sentiment?product_id=1"

# Get retailer comparison
curl "http://localhost:8000/api/analytics/retailers"

# Get forecast
curl "http://localhost:8000/api/analytics/forecast?product_id=1&days=7"
```

#### 5. **Test Notifications API**
```bash
# Send email notification
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "user@example.com",
    "subject": "Price Alert",
    "message": "Your watched item dropped to $25.99"
  }'

# Send SMS notification
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "recipient": "+1234567890",
    "message": "Price alert: Your item is now $25.99"
  }'

# Send push notification
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "push",
    "recipient": "device-token-123",
    "title": "Price Alert",
    "body": "Your item dropped to $25.99"
  }'

# Get notification history
curl http://localhost:8000/api/notifications/history
```

### Database Testing
```bash
# Connect to PostgreSQL
docker exec -it test_model-postgres-1 psql -U compair -d compair

# List tables
\dt

# Check alerts table
SELECT * FROM alert LIMIT 5;

# Check smart lists
SELECT * FROM smart_list LIMIT 5;

# Check notifications
SELECT * FROM notification LIMIT 5;

# Exit
\q
```

### Frontend Testing
```bash
# Check frontend compilation errors
docker logs test_model-frontend-1

# Access frontend
# Browser: http://localhost:8080

# Clear cache and rebuild
docker-compose --profile frontend down frontend
docker-compose build --no-cache frontend
docker-compose --profile frontend up -d frontend
```

---

## 🚢 Full Test Scenario

### Complete End-to-End Test
```bash
# 1. Clean slate
docker-compose down -v

# 2. Build all services
docker-compose build --no-cache

# 3. Start core services
docker-compose up -d postgres redis web

# 4. Wait for services to be healthy (30-60 seconds)
sleep 60

# 5. Test backend health
curl http://localhost:8000/api/v1/health

# 6. Create test alert
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "target_price": 29.99, "operator": "<=", "channels": ["email"], "frequency": "immediate", "priority": "normal"}'

# 7. Get metrics
curl http://localhost:8000/api/metrics | head -20

# 8. Start worker (optional, for background tasks)
docker-compose --profile worker up -d worker

# 9. Start frontend
docker-compose --profile frontend up -d frontend

# 10. Access in browser
# http://localhost:8080 (frontend)
# http://localhost:8000/api/v1/health (backend)
# http://localhost:5555 (Flower, after starting worker)

echo "✅ All services running!"
docker-compose ps
```

---

## 🐛 Troubleshooting

### Issue: Module not found errors in frontend
**Solution:**
```bash
# Restart TypeScript server
docker logs -f test_model-frontend-1

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose --profile frontend down frontend
docker-compose --profile frontend up -d frontend
```

### Issue: Database connection error
**Solution:**
```bash
# Check PostgreSQL health
docker-compose ps postgres

# Verify connection
docker exec test_model-postgres-1 pg_isready -U compair

# Restart database
docker-compose restart postgres
```

### Issue: Redis connection failed
**Solution:**
```bash
# Check Redis health
docker-compose ps redis

# Verify connection
docker exec test_model-redis-1 redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Issue: Worker tasks not processing
**Solution:**
```bash
# Check worker status
docker logs -f test_model-worker-1

# Verify Celery connection
docker exec test_model-worker-1 celery -A app.worker inspect active

# Restart worker
docker-compose --profile worker restart worker
```

### Issue: Frontend shows blank page
**Solution:**
```bash
# Check frontend logs
docker logs test_model-frontend-1

# Check API URL in environment
docker exec test_model-frontend-1 env | grep VITE_API_URL

# Verify backend is running
curl http://localhost:8000/api/v1/health

# Rebuild frontend
docker-compose build --no-cache frontend
```

### View All Logs
```bash
# View logs for all services
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f frontend
docker-compose logs -f worker

# View last 100 lines
docker logs --tail 100 test_model-web-1
```

---

## 📊 Service URLs

| Service | URL | Port | Notes |
|---------|-----|------|-------|
| Backend API | http://localhost:8000 | 8000 | FastAPI |
| Frontend | http://localhost:8080 | 8080 | React/Vite |
| PostgreSQL | localhost:5432 | 5432 | Database |
| Redis | localhost:6379 | 6379 | Cache/Broker |
| Flower | http://localhost:5555 | 5555 | Celery Dashboard |
| Prometheus | http://localhost:9090 | 9090 | Metrics |
| Grafana | http://localhost:3002 | 3002 | Dashboard (admin/admin) |
| Scraper | http://localhost:3001 | 3001 | Node.js Service |

---

## ✅ Checklist Before Going Live

- [ ] All services build without errors
- [ ] All services start and show healthy in `docker-compose ps`
- [ ] Backend health check passes: `curl http://localhost:8000/api/v1/health`
- [ ] Frontend loads: `http://localhost:8080`
- [ ] Database migrations run: `docker exec test_model-web-1 alembic upgrade head`
- [ ] Create test alert via API
- [ ] View metrics: `curl http://localhost:8000/api/metrics`
- [ ] Start worker and verify in Flower: `http://localhost:5555`
- [ ] Test notification endpoints
- [ ] Frontend TypeScript errors resolved
- [ ] All environment variables set correctly

---

## 🎉 Ready to Deploy!

Once all checks pass, you're ready for:
1. Full production build
2. Load testing
3. End-to-end feature testing
4. Deployment to production environment
