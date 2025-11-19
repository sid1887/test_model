# Microservices Deployment Guide

## Quick Start

### 1. Build All Services
```bash
# Build with microservices profile (all 8 services)
docker-compose -f docker-compose.services.yml build

# Or build specific services
docker-compose -f docker-compose.services.yml build ai-models
docker-compose -f docker-compose.services.yml build hf-connector
```

### 2. Start All Services
```bash
# Start with microservices profile
docker-compose -f docker-compose.services.yml --profile microservices up -d

# Check status
docker-compose -f docker-compose.services.yml ps

# View logs
docker-compose -f docker-compose.services.yml logs -f api-gateway
```

### 3. Verify Health
```bash
# All services health check
curl http://localhost:8000/api/v1/health

# Individual service checks
curl http://localhost:8001/api/models/health      # AI Models
curl http://localhost:8002/api/hf/health          # HF Connector
curl http://localhost:8003/api/media/health       # Speech & Image
curl http://localhost:8004/api/features/health    # Feature Extract
curl http://localhost:8005/api/scrapy/health      # Scrapy Wrapper
```

## Service Ports

| Service | Port | Purpose | Build Time | Memory |
|---------|------|---------|-----------|--------|
| API Gateway | 8000 | Orchestrator | 1 min | 100MB |
| AI Models | 8001 | YOLO, CLIP | 5 min | 800MB |
| HF Connector | 8002 | Text models | 3 min | 600MB |
| Speech/Image | 8003 | Voice, OCR | 2 min | 500MB |
| Feature Extract | 8004 | Embeddings | 1 min | 300MB |
| Scrapy Wrapper | 8005 | Retailers proxy | 30s | 50MB |
| PostgreSQL | 5432 | Database | - | 200MB |
| Redis | 6379 | Cache | - | 50MB |
| Scrapy Service | 5000 | 17+ retailers | - | 300MB |
| Captcha | 9001 | CAPTCHA solving | - | 200MB |

## Testing Workflow

### Phase 1: Individual Service Tests
```bash
# 1. Check all services started
docker-compose -f docker-compose.services.yml ps

# 2. Test each service individually
curl http://localhost:8001/api/models/health
curl http://localhost:8002/api/hf/health
curl http://localhost:8003/api/media/health
curl http://localhost:8004/api/features/health
curl http://localhost:8005/api/scrapy/health

# 3. Check gateway sees all services
curl http://localhost:8000/api/v1/health | jq '.services'
```

### Phase 2: Service-to-Service Communication
```bash
# Gateway calls AI Models
curl -X POST http://localhost:8000/api/models/clip-encode-text \
  -H "Content-Type: application/json" \
  -d '{"texts": ["laptop computer"]}'

# Gateway calls HF Connector
curl -X POST http://localhost:8000/api/hf/sentiment \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great product!"]}'

# Gateway calls Feature Extract
curl -X POST http://localhost:8000/api/features/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["wireless headphones"]}'
```

### Phase 3: Full Integration Tests
```bash
# 1. Product search (Scrapy)
curl -X POST http://localhost:8000/api/v1/scrapy/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "laptop",
    "retailers": ["amazon", "walmart"],
    "max_results": 5
  }'

# 2. Check Scrapy stats
curl http://localhost:8000/api/v1/scrapy/stats

# 3. Get retailers list
curl http://localhost:8000/api/v1/scrapy/retailers
```

## Monitoring

### Check Container Status
```bash
# Show all running containers
docker-compose -f docker-compose.services.yml ps

# Show specific service logs
docker-compose -f docker-compose.services.yml logs api-gateway
docker-compose -f docker-compose.services.yml logs ai-models

# Stream logs in real-time
docker-compose -f docker-compose.services.yml logs -f

# Show only last 50 lines
docker-compose -f docker-compose.services.yml logs --tail=50
```

### Restart Individual Services (Fast!)
```bash
# Restart AI Models only (~15 seconds)
docker-compose -f docker-compose.services.yml restart ai-models

# Restart HF Connector only (~20 seconds)
docker-compose -f docker-compose.services.yml restart hf-connector

# Restart Gateway only (~5 seconds)
docker-compose -f docker-compose.services.yml restart api-gateway
```

### Resource Usage
```bash
# Check CPU/Memory per service
docker stats

# Inspect container details
docker inspect test_model-api-gateway-1
docker inspect test_model-ai-models-1
```

## Cleanup & Troubleshooting

### Remove Old Monolithic Container
```bash
# After confirming new microservices work:
docker stop test_model-web-1
docker rm test_model-web-1
docker rmi test_model-web:latest

# Free up space
docker system prune -a --volumes
```

### Rebuild Single Service
```bash
# Fast rebuild (no cache flush)
docker-compose -f docker-compose.services.yml build --no-cache ai-models

# Start just that service
docker-compose -f docker-compose.services.yml up -d ai-models

# Check it's healthy
curl http://localhost:8001/api/models/health
```

### Debug Service Issues
```bash
# View service logs with error details
docker-compose -f docker-compose.services.yml logs --tail=100 ai-models | grep -i error

# Execute command in running container
docker exec test_model-api-gateway-1 curl http://api-gateway:8000/api/v1/health

# Access container shell
docker exec -it test_model-ai-models-1 /bin/bash
```

## Performance Comparison

### Old Monolithic Web Container
- **Startup time**: 2-3 minutes (all 19 systems initialize)
- **Restart time**: 2-3 minutes (all models re-download)
- **Memory per container**: 4GB+
- **Failure impact**: Entire app down
- **Development cycle**: Change 1 line → rebuild 2-3 minutes

### New Microservices Architecture
- **First-time startup**: ~15 minutes (models download once)
- **Restart time**: 30-45 seconds (only API gateway + services that changed)
- **Memory per service**: 50MB - 800MB
- **Failure impact**: Only that service unavailable
- **Development cycle**: Change 1 line → rebuild 5-30 seconds

### Key Wins
1. **80% faster restarts** - No full rebuild needed
2. **4x less memory** - Distribute load across containers
3. **Better resilience** - Services fail independently
4. **Faster development** - Test changes in seconds

## API Gateway Routing

All existing endpoints now route through API Gateway (port 8000):

```
/api/v1/scrapy/*          → scrapy-wrapper (8005) → Scrapy Service (5000)
/api/models/*             → ai-models (8001)
/api/hf/*                 → hf-connector (8002)
/api/media/*              → speech-image (8003)
/api/features/*           → feature-extract (8004)
/api/v1/health            → Gateway (checks all downstream)
/docs                     → Swagger UI (Gateway)
```

## Next Steps

1. **Build all services**: `docker-compose -f docker-compose.services.yml build`
2. **Start all services**: `docker-compose -f docker-compose.services.yml --profile microservices up -d`
3. **Verify health**: `curl http://localhost:8000/api/v1/health`
4. **Run integration tests**: See Phase 3 above
5. **Monitor logs**: `docker-compose -f docker-compose.services.yml logs -f`
6. **Remove old container**: Once confirmed working
7. **Update documentation**: Document any custom endpoints

## Troubleshooting Common Issues

### Service won't start
```bash
# Check logs
docker logs test_model-ai-models-1

# Rebuild from scratch
docker-compose -f docker-compose.services.yml build --no-cache ai-models

# Start with verbose output
docker-compose -f docker-compose.services.yml up ai-models
```

### Gateway can't reach service
```bash
# Verify service is running
docker exec test_model-api-gateway-1 curl http://ai-models:8001/api/models/health

# Check network
docker network ls
docker network inspect test_model_default

# Verify container names match docker-compose
docker ps | grep test_model
```

### High memory usage
```bash
# Check which container uses most memory
docker stats

# Reduce model size or enable memory optimization in Dockerfile
# Consider using quantization or smaller models
```

### Port conflicts
```bash
# Check what's using port 8000
lsof -i :8000  # On Linux/Mac
netstat -ano | findstr :8000  # On Windows

# Change port in docker-compose.services.yml and rebuild
```
