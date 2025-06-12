# 🔍 CUMPAIR - COMPLETE PORT ALLOCATION SUMMARY

## 📊 **MAIN SERVICES PORTS**

### Core Backend Services
- **FastAPI Main App**: `8000` ✅
  - Main web application
  - API endpoints (`/api/v1/*`)
  - Documentation at `/docs`
  - Health check at `/api/v1/health`

- **PostgreSQL Database**: `5432` ✅
  - Main database for products, analyses, price history
  - Connection: `postgresql://compair:compair123@localhost:5432/compair`

- **Redis Cache**: `6379` ✅
  - Caching, Celery task queue, session storage
  - Connection: `redis://localhost:6379`

### Scraper Services
- **Node.js Scraper API**: `3000` ✅ (Docker) / `3001` ⚠️ (Direct run)
  - NEW ISSUE DETECTED: **PORT CONFLICT!**
  - Docker uses port 3000
  - Direct server.js uses port 3001
  - **RESOLUTION NEEDED**: Standardize to port 3001

### Frontend Service
- **Vite Dev Server**: `8080` ✅
  - React/TypeScript frontend
  - Development server
  - **ISSUE**: Should proxy to backend on port 8000

### Monitoring & Background Services
- **Celery Flower**: `5555` ✅
  - Task monitoring UI
  - Background job monitoring

- **Prometheus**: `9090` ✅
  - Metrics collection

- **Grafana**: `3002` ✅ (Docker) / `3000` ⚠️ (Default Grafana)
  - **POTENTIAL CONFLICT**: Grafana default is 3000
  - Docker correctly maps to 3002

## 🚨 **DETECTED PORT CONFLICTS & ISSUES**

### 1. **CRITICAL: Scraper Service Port Mismatch**
```
Docker Compose: scraper:3000 -> 3000:3000
Direct Run:     server.js uses PORT 3001
API Calls:      /api/routes/comparison.py expects port 3001
```
**Impact**: Backend cannot connect to scraper service
**Fix**: Standardize all scraper references to port 3001

### 2. **Frontend API Proxy Configuration**
```
Frontend Vite: port 8080
Backend API:   port 8000
```
**Status**: Needs proxy configuration for `/api/*` calls

### 3. **Additional Services (Optional)**
- **CAPTCHA Service**: `9001` ✅
- **Proxy Manager**: `8001` ✅  
- **HAProxy Stats**: `8081` ✅
- **Redis (CAPTCHA)**: `6380` ✅

## 🔧 **REQUIRED FIXES**

### Fix 1: Standardize Scraper to Port 3001
1. Update docker-compose.yml scraper port mapping
2. Update all backend API calls to use port 3001
3. Ensure scraper server.js uses consistent port

### Fix 2: Configure Frontend Proxy
1. Update vite.config.ts with API proxy
2. Ensure frontend calls hit localhost:8000/api/*

### Fix 3: Verify Port Availability
1. Check no other services using these ports
2. Update all documentation to match

## 📋 **STARTUP ORDER**
1. **Database**: PostgreSQL (5432) & Redis (6379)
2. **Backend**: FastAPI (8000)
3. **Scraper**: Node.js service (3001)
4. **Frontend**: Vite dev server (8080)
5. **Optional**: Monitoring services

## 🧪 **VERIFICATION COMMANDS**
```powershell
# Check port availability
netstat -an | findstr ":8000 :3001 :8080 :5432 :6379"

# Test service endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:3001/health
curl http://localhost:8080
```

## ⚠️ **NEXT ACTIONS REQUIRED**
1. Fix scraper port configuration 
2. Test frontend-backend connectivity
3. Verify all services start without conflicts
4. Update all documentation with correct ports
