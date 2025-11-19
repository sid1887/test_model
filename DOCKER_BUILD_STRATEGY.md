# Docker Build Strategy - One Service at a Time

**Important:** Build ONE service at a time to avoid crashing Docker system.

## Build Order (Priority)

1. ✅ **API Gateway** (Port 8000) - Central router, smallest, no ML deps
2. ⏳ **Search Service** (Port 8010) - Medium size, uses Redis + PostgreSQL
3. ⏳ **Real-Time Service** (Port 8013) - Small, WebSocket only
4. ⏳ **ML Engine** (Port 8014) - Large, requires torch, transformers
5. ⏳ **Elasticsearch Service** (Port 8015) - Medium, Python ES client only
6. ⏳ **Event Bus** (Port 8016) - Small, Redis Streams only

## Prerequisites Check

```bash
# 1. Check Docker memory allocation
docker stats --no-stream
# Should have at least 4GB free

# 2. Clean up before starting
docker system prune -a --volumes
docker network prune -f

# 3. Verify requirements.txt is complete
wc -l requirements.txt
# Should have 150+ packages
```

## Step 1: Build API Gateway (Port 8000)

```bash
# First, verify all dependencies needed for api_gateway.py
pip install -r requirements.txt

# Then build the Docker image (slow, ~5-10 minutes)
docker build -f docker/Dockerfile.api-gateway -t cumpair-api-gateway:latest .

# Run it
docker run -d \
  --name cumpair-api-gateway \
  -p 8000:8000 \
  --network backend \
  -e PYTHONUNBUFFERED=1 \
  cumpair-api-gateway:latest

# Check logs
docker logs cumpair-api-gateway -f

# Test it
curl http://localhost:8000/health
```

## Step 2: Build Search Service (Port 8010)

```bash
# After API Gateway is running and healthy...
docker build -f docker/Dockerfile.search-discovery -t cumpair-search:latest .

docker run -d \
  --name cumpair-search \
  -p 8010:8010 \
  --network backend \
  -e PYTHONUNBUFFERED=1 \
  cumpair-search:latest

# Test
curl http://localhost:8010/health
```

## Memory Management During Builds

```bash
# Monitor during build
watch -n 1 'docker stats --no-stream'

# If memory gets above 80%, STOP:
docker stop cumpair-api-gateway
docker system prune -a --volumes
# Then restart the build

# Each service should use:
# API Gateway: 300MB
# Search: 800MB
# Real-Time: 200MB
# ML Engine: 2-3GB (largest!)
# Elasticsearch: 500MB
# Event Bus: 200MB
```

## Building Each Service

### Prerequisites for Each Service

Before building each service, ensure:

```bash
# 1. Previous service is running and healthy
docker ps | grep cumpair-

# 2. Free memory available
free -h | grep -i mem

# 3. No dangling images/containers
docker system df

# 4. Network exists
docker network ls | grep backend
```

### Build Process Template

```bash
# For each service:
SERVICE_NAME="api-gateway"  # Change this

# 1. Build (slow)
docker build \
  -f docker/Dockerfile.${SERVICE_NAME} \
  -t cumpair-${SERVICE_NAME}:latest \
  --no-cache \
  .

# 2. Wait for build to complete (watch terminal)

# 3. Run
docker run -d \
  --name cumpair-${SERVICE_NAME} \
  -p 800X:800X \
  --network backend \
  -e PYTHONUNBUFFERED=1 \
  cumpair-${SERVICE_NAME}:latest

# 4. Check logs
docker logs cumpair-${SERVICE_NAME} -f

# 5. Verify health
curl http://localhost:800X/health

# 6. Once stable, stop and move to next service
docker stop cumpair-${SERVICE_NAME}
```

## Troubleshooting Docker Builds

### Docker stops responding

```bash
# 1. Check Docker daemon
docker ps
# If hangs, restart Docker:
sudo systemctl restart docker  # Linux
# OR Docker Desktop (Mac/Windows)

# 2. Check memory
docker stats --no-stream

# 3. Force cleanup
docker system prune -a --volumes --force
```

### Build gets stuck

```bash
# Kill the build
Ctrl+C

# Remove partially built image
docker image rm cumpair-service:latest

# Try again with more memory/resources
```

### Container won't start

```bash
# Check logs
docker logs cumpair-service

# Check if port is already in use
lsof -i :8000

# Remove old container
docker rm cumpair-service
docker rmi cumpair-service:latest

# Try again
```

### Out of memory errors

```bash
# Stop all running services
docker stop $(docker ps -q)

# Remove all stopped containers
docker container prune -f

# Remove dangling images
docker image prune -f

# Clean volumes
docker volume prune -f

# Wait a moment, check memory
sleep 10
free -h

# Start again
```

## Final Docker Compose (After all built)

Once all services are individually built and tested:

```bash
# Start all at once
docker-compose -f docker-compose.phase7.yml up -d

# Watch startup
docker-compose -f docker-compose.phase7.yml logs -f

# Check all services
docker ps

# Verify gateway
curl http://localhost:8000/health
```

## Success Checklist

- [ ] API Gateway runs and responds to /health
- [ ] Search Service healthy and responding
- [ ] Real-Time Service listening on WebSocket
- [ ] ML Engine initialized and ready
- [ ] Elasticsearch cluster healthy
- [ ] Event Bus listening for events
- [ ] All 5 services can communicate via Docker network
- [ ] Gateway health shows all services as "healthy"
- [ ] No Out of Memory errors in Docker
- [ ] Free disk space > 5GB

---

**Status:** Ready to start building!
**Start with:** API Gateway (smallest, no ML deps)
**Estimated time:** 30-60 minutes total (including waiting)
