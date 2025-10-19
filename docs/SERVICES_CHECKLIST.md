# 🔍 Cumpair - Required Services & Dependencies Checklist

## 🗄️ **Database Services** (REQUIRED)

### 1. PostgreSQL Database

- **Purpose**: Main database for storing products, analyses, price history

- **Status**: ✅ Currently Running (docker-compose)

- **Start Command**: `docker-compose up postgres -d`

- **Check Status**: `docker ps | findstr postgres`

- **Port**: 5432

- **Connection**: `postgresql://compair:compair123@localhost:5432/compair`

### 2. Redis Cache & Queue

- **Purpose**: Caching, Celery task queue, session storage

- **Status**: ✅ Currently Running (docker-compose)

- **Start Command**: `docker-compose up redis -d`

- **Check Status**: `docker ps | findstr redis`

- **Port**: 6379

- **Connection**: `redis://localhost:6379`

## 🤖 **AI & ML Services** (INTEGRATED)

### 3. YOLO Object Detection Model

- **Purpose**: Product detection in images

- **Status**: ✅ Loaded automatically on app startup

- **File**: `models/yolov8n.pt`

- **Memory**: ~50MB

### 4. CLIP Search Engine

- **Purpose**: Image-text similarity, semantic search

- **Status**: ✅ Loaded automatically on app startup

- **Indexes**:
  - `models/clip_indexes/image_index.faiss`
  - `models/clip_indexes/text_index.faiss`
  - `models/clip_indexes/metadata.pkl`

- **Memory**: ~500MB

### 5. EfficientNet Specification Model

- **Purpose**: Product specification extraction

- **Status**: ⚠️ Placeholder loaded (custom model needed)

- **File**: `models/spec_extractor.h5` (not found)

- **Note**: Using fallback placeholder

## 🌐 **Web Scraping Services** (OPTIONAL)

### 6. Node.js Scraper Microservice

- **Purpose**: Dedicated web scraping with anti-bot measures

- **Status**: ❌ Not Running (optional for demo)

- **Location**: `./scraper/`

- **Start Commands**:
  ```powershell
  cd scraper
  npm install  npm start
  ```

- **Port**: 3001

- **Integration**: CumpairScraperClient in main app

### 7. Playwright Browser Engine

- **Purpose**: Headless browser scraping fallback

- **Status**: ✅ Installed and ready

- **Install**: `playwright install chromium`

- **Usage**: Automatic when needed

## ⚙️ **Background Processing** (RECOMMENDED)

### 8. Celery Worker

- **Purpose**: Background tasks (image analysis, price updates)

- **Status**: ❌ Not Running (for full functionality)

- **Start Command**:
  ```powershell
  celery -A app.worker worker --loglevel=info
  ```

- **Dependencies**: Redis (already running)

### 9. Celery Flower (Optional)

- **Purpose**: Task monitoring and management UI

- **Status**: ❌ Not Running (optional)

- **Start Command**:
  ```powershell
  celery -A app.worker flower
  ```

- **Port**: 5555

- **UI**: http://localhost:5555

## 📊 **Monitoring Services** (OPTIONAL)

### 10. Prometheus (Optional)

- **Purpose**: Metrics collection

- **Status**: ❌ Not Running

- **Config**: `monitoring/prometheus.yml`

- **Port**: 9090

### 11. Grafana (Optional)

- **Purpose**: Metrics visualization dashboard

- **Status**: ❌ Not Running

- **Port**: 3000

## 🔧 **Development Tools**

### 12. Alembic Database Migrations

- **Purpose**: Database schema management

- **Status**: ✅ Applied (schema up to date)

- **Usage**: `alembic upgrade head` (already done)

### 13. FastAPI Main Application

- **Purpose**: Main web API server

- **Status**: ✅ Currently Running

- **Port**: 8000

- **URL**: http://localhost:8000

---

## 🚀 **QUICK START CHECKLIST**

### **Minimal Setup (Currently Running):**

- [x] PostgreSQL Database

- [x] Redis Cache

- [x] FastAPI Application

- [x] AI Models (YOLO, CLIP)

- [x] Database Schema

### **For Full Functionality:**

```text
powershell
# 1. Start background worker (new terminal)

celery -A app.worker worker --loglevel=info

# 2. Start scraper service (new terminal)

cd scraper
npm start

# 3. Start monitoring (optional, new terminal)

celery -A app.worker flower

```text

### **Current Status Summary:**

- 🟢 **Core Features**: Working (image analysis, basic price search)

- 🟡 **Background Tasks**: Limited (no Celery worker)

- 🟡 **Web Scraping**: Fallback only (no dedicated scraper)

- 🔴 **Advanced Features**: Monitoring not active

### **Service Dependencies:**

```text

FastAPI App (Port 8000)
├── PostgreSQL (Port 5432) ✅
├── Redis (Port 6379) ✅
├── AI Models ✅
│   ├── YOLO ✅
│   ├── CLIP ✅
│   └── EfficientNet ⚠️
├── Celery Worker ❌
├── Node.js Scraper (Port 3000) ❌
└── Monitoring
    ├── Flower (Port 5555) ❌
    ├── Prometheus (Port 9090) ❌
    └── Grafana (Port 3000) ❌

```text

## 🎯 **Recommendation for Next Steps:**

1. **Start Celery Worker** - For full async functionality

2. **Start Node.js Scraper** - For enhanced scraping capabilities

3. **Test Core Features** - Image upload, analysis, price search

4. **Optional Monitoring** - Flower for task monitoring

The application is already functional with the current setup! 🎉
