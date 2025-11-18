# Microservices Architecture Plan - Docker Optimization

## Problem Statement
Current monolithic web container has 19+ major systems starting simultaneously:
- **Restart time**: 2-3 minutes (everything re-downloads)
- **Memory bloat**: All models loaded even if not needed
- **Single point of failure**: One service crashes = entire container down

## Solution: Decomposed Microservices

### Dependency Graph

```
PostgreSQL (external)
Redis (external)
    ↓
    ├─→ API Gateway (orchestrator)
    │       ├─→ AI Models Service
    │       ├─→ HF Connector Service
    │       ├─→ Speech/Image Service
    │       ├─→ Feature Extraction Service
    │       └─→ Scrapy Wrapper Service
    │
    └─→ All external services call back to Gateway via HTTP
```

### New Container Architecture

| Service | Port | Purpose | Models/Load | Startup | Deps |
|---------|------|---------|------------|---------|------|
| **api-gateway** | 8000 | Route orchestration | None | 5s | FastAPI, Pydantic |
| **ai-models** | 8001 | YOLO, EfficientNet, CLIP | 2GB+ | 15s | TensorFlow, PyTorch, transformers |
| **hf-connector** | 8002 | HF models (text, sentiment, NER) | 1GB+ | 20s | transformers, torch |
| **speech-image** | 8003 | Voice STT, Image processing | 500MB | 10s | faster-whisper, easyocr, YOLO |
| **feature-extract** | 8004 | Embeddings, FAISS indexing | 300MB | 5s | sentence-transformers, faiss |
| **scrapy-wrapper** | 8005 | Scrapy service proxy | Minimal | 2s | httpx, pydantic |
| **worker** | N/A | Celery background jobs | Minimal | 3s | celery, redis |

### Container Specifications

#### 1. **Base Image** (Reusable foundation)
- Python 3.11-slim
- pip, setuptools, wheel (latest)
- Common requirements: fastapi, uvicorn, pydantic, sqlalchemy, redis, httpx
- Size: ~150MB

#### 2. **AI Models Service** (8001)
- Base: ai-models-base (includes TensorFlow, PyTorch)
- Models: YOLO, EfficientNet, CLIP (ViT-B/32)
- Sentence transformers (for text embeddings)
- Size: ~2.5GB
- Startup: 15s
- Health: `/api/models/health`
- Endpoints:
  - POST `/api/models/yolo-detect` - object detection
  - POST `/api/models/efficientnet-classify` - image classification
  - POST `/api/models/clip-encode-text` - text embedding
  - POST `/api/models/clip-encode-image` - image embedding

#### 3. **HuggingFace Connector** (8002)
- Base: Python 3.11 + transformers
- Models: text-generation, sentiment-analysis, zero-shot-classification, NER, image-captioning
- Size: ~1.2GB
- Startup: 20s
- Health: `/api/hf/health`
- Endpoints:
  - POST `/api/hf/generate` - text generation
  - POST `/api/hf/sentiment` - sentiment analysis
  - POST `/api/hf/classify` - zero-shot classification
  - POST `/api/hf/ner` - named entity recognition
  - POST `/api/hf/caption` - image captioning

#### 4. **Speech & Image Processing** (8003)
- Base: Python 3.11 + image libs
- Services: faster-whisper, EasyOCR, YOLO inference, image utils
- Size: ~800MB
- Startup: 10s
- Health: `/api/media/health`
- Endpoints:
  - POST `/api/media/voice-to-text` - speech recognition
  - POST `/api/media/ocr` - optical character recognition
  - POST `/api/media/process-image` - image preprocessing

#### 5. **Feature Extraction Service** (8004)
- Base: Python 3.11 + ML libs
- Services: sentence-transformers, FAISS, vector store
- Size: ~400MB
- Startup: 5s
- Health: `/api/features/health`
- Endpoints:
  - POST `/api/features/embed` - generate embeddings
  - POST `/api/features/index-add` - add to vector index
  - POST `/api/features/search` - search vector index

#### 6. **Scrapy Wrapper Service** (8005)
- Base: Python 3.11 minimal
- Proxy to existing Scrapy service on port 5000
- Size: ~50MB
- Startup: 2s
- Health: `/api/scrapy/health`
- Endpoints:
  - POST `/api/scrapy/search` - proxy to Scrapy
  - GET `/api/scrapy/retailers` - list retailers

#### 7. **API Gateway** (8000)
- Base: Python 3.11 + FastAPI
- Routes requests to all 5 microservices
- Cache layer for service responses
- Error handling & fallbacks
- Size: ~100MB
- Startup: 5s
- Health: `/api/v1/health` (also checks all downstream services)
- All existing API routes:
  - /api/v1/scrapy/* → scrapy-wrapper (8005)
  - /api/v1/ai/* → ai-models (8001)
  - /api/v1/analyze → ai-models (8001) or hf-connector (8002)
  - /api/v1/voice/* → speech-image (8003)
  - /api/v1/image/* → speech-image (8003)
  - /api/v1/health/* → all services

#### 8. **Celery Worker** (Background jobs)
- Base: Python 3.11 minimal
- Services: Celery worker, Redis client
- Size: ~100MB
- Startup: 3s
- Health: via Redis
- Tasks: async search, bulk operations, data pipeline

### File Structure

```
docker/
├── Dockerfile.base               # Common base image
├── Dockerfile.api-gateway        # API Gateway (routes & orchestration)
├── Dockerfile.ai-models          # YOLO, EfficientNet, CLIP
├── Dockerfile.hf-connector       # HuggingFace services
├── Dockerfile.speech-image       # Voice STT, Image processing
├── Dockerfile.feature-extract    # Embeddings & FAISS
├── Dockerfile.scrapy-wrapper     # Scrapy proxy
├── Dockerfile.worker             # Celery worker

services/
├── gateway/
│   ├── main.py                   # FastAPI app (orchestrator)
│   ├── routes/
│   │   ├── health.py            # Health check all services
│   │   ├── proxy.py             # Proxy logic for each service
│   │   └── routes.py            # All existing routes (call downstream)
│   └── requirements.txt
├── ai-models/
│   ├── main.py                   # FastAPI + model loading
│   ├── models.py                # Model inference functions
│   └── requirements.txt
├── hf-connector/
│   ├── main.py                   # FastAPI + HF initialization
│   ├── models.py                # HF model functions
│   └── requirements.txt
└── [similar for other services]

docker-compose.services.yml       # Define all 8 services
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  # External services (unchanged)
  postgres:
    image: ankane/pgvector:latest
    ports: ["5432:5432"]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  scrapy_scraper:
    image: test_model-scrapy_scraper
    ports: ["5000:5000"]
  
  captcha:
    image: test_model-captcha
    ports: ["9001:9001"]

  # New microservices
  ai-models:
    build:
      context: .
      dockerfile: docker/Dockerfile.ai-models
    ports: ["8001:8001"]
    environment:
      - SERVICE_PORT=8001
      - CUDA=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/models/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  hf-connector:
    build:
      context: .
      dockerfile: docker/Dockerfile.hf-connector
    ports: ["8002:8002"]
    environment:
      - SERVICE_PORT=8002
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/hf/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  speech-image:
    build:
      context: .
      dockerfile: docker/Dockerfile.speech-image
    ports: ["8003:8003"]
    environment:
      - SERVICE_PORT=8003
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/api/media/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  feature-extract:
    build:
      context: .
      dockerfile: docker/Dockerfile.feature-extract
    ports: ["8004:8004"]
    environment:
      - SERVICE_PORT=8004
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/api/features/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  scrapy-wrapper:
    build:
      context: .
      dockerfile: docker/Dockerfile.scrapy-wrapper
    ports: ["8005:8005"]
    environment:
      - SERVICE_PORT=8005
      - SCRAPY_SERVICE_URL=http://scrapy_scraper:5000
    depends_on:
      - scrapy_scraper
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/api/scrapy/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  api-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.api-gateway
    ports: ["8000:8000"]
    environment:
      - SERVICE_PORT=8000
      - AI_MODELS_URL=http://ai-models:8001
      - HF_CONNECTOR_URL=http://hf-connector:8002
      - SPEECH_IMAGE_URL=http://speech-image:8003
      - FEATURE_EXTRACT_URL=http://feature-extract:8004
      - SCRAPY_WRAPPER_URL=http://scrapy-wrapper:8005
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cumpair
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - ai-models
      - hf-connector
      - speech-image
      - feature-extract
      - scrapy-wrapper
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cumpair
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

### Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Restart time** | 2-3 min | 30-45 sec |
| **Develop ai-models** | Rebuild all 19 systems | 15s rebuild ai-models only |
| **Memory per container** | 4GB+ | 300-800MB each |
| **Partial failure** | Container down | One service fails, others continue |
| **Scaling** | N/A | Scale individual services |
| **Cache efficiency** | Re-downloads all models | Models cached per container |
| **Dependency updates** | Full rebuild | Update one service only |

### Implementation Plan

**Phase 1: Setup** (30 min)
- [ ] Create base Dockerfile
- [ ] Create 7 service Dockerfiles
- [ ] Create service entrypoints (main.py for each)
- [ ] Update docker-compose.yml

**Phase 2: Build** (45 min)
- [ ] Build all images locally
- [ ] Test each container starts independently
- [ ] Verify health checks work

**Phase 3: Test** (30 min)
- [ ] Test service-to-service communication
- [ ] Test all API endpoints through gateway
- [ ] Load test with cache

**Phase 4: Cleanup** (5 min)
- [ ] Stop old web container
- [ ] Remove old monolithic image

### Estimated Total Build Time

- Base image: 2 min
- AI Models: 5 min (model downloads cached)
- HF Connector: 3 min (model downloads cached)
- Speech/Image: 2 min
- Feature Extract: 1 min
- Scrapy Wrapper: 30s
- API Gateway: 1 min
- Worker: 30s
- **Total**: ~15 minutes (one-time, then cached forever)

### Rebuild Time After Code Changes

- Change in gateway code: 1 min rebuild
- Change in AI models code: 15s rebuild
- Change in HF connector code: 20s rebuild
- All models cached, no re-download

### Important Notes

1. **No losing functionality**: Every endpoint from original app is preserved
2. **Better resilience**: Services can fail independently
3. **Faster development**: Change one service, rebuild in seconds
4. **Easy debugging**: Logs per service, health checks per service
5. **Future scaling**: Can run multiple instances of each service

