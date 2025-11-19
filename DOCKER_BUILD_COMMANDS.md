# Complete Docker Build Commands - One at a Time

## Prerequisites (Run Once)
```powershell
# Create Docker network
docker network create backend

# Clean up old images/containers
docker system prune -a --volumes -f
```

## 1. API Gateway (Port 8000)
```powershell
docker build -f docker/Dockerfile.api-gateway -t cumpair-api-gateway:latest .
docker run -d --name cumpair-api-gateway -p 8000:8000 --network backend cumpair-api-gateway:latest
docker logs cumpair-api-gateway -f
curl http://localhost:8000/health
```

## 2. Search Service (Port 8010)
```powershell
docker build -f docker/Dockerfile.search-discovery -t cumpair-search:latest .
docker run -d --name cumpair-search -p 8010:8010 --network backend cumpair-search:latest
docker logs cumpair-search -f
curl http://localhost:8010/health
```

## 3. Real-Time Service (Port 8013)
```powershell
docker build -f docker/Dockerfile.realtime -t cumpair-realtime:latest .
docker run -d --name cumpair-realtime -p 8013:8013 --network backend cumpair-realtime:latest
docker logs cumpair-realtime -f
curl http://localhost:8013/health
```

## 4. ML Engine (Port 8014)
```powershell
docker build -f docker/Dockerfile.ml-engine -t cumpair-ml:latest .
docker run -d --name cumpair-ml -p 8014:8014 --network backend cumpair-ml:latest
docker logs cumpair-ml -f
curl http://localhost:8014/health
```

## 5. Elasticsearch Service (Port 8015)
```powershell
docker build -f docker/Dockerfile.elasticsearch-service -t cumpair-elasticsearch:latest .
docker run -d --name cumpair-elasticsearch -p 8015:8015 --network backend cumpair-elasticsearch:latest
docker logs cumpair-elasticsearch -f
curl http://localhost:8015/health
```

## 6. Event Bus Service (Port 8016)
```powershell
docker build -f docker/Dockerfile.event-bus -t cumpair-events:latest .
docker run -d --name cumpair-events -p 8016:8016 --network backend cumpair-events:latest
docker logs cumpair-events -f
curl http://localhost:8016/health
```

## Stop & Clean Commands
```powershell
# Stop single service
docker stop cumpair-api-gateway

# Stop all services
docker stop $(docker ps -q)

# Remove single container
docker rm cumpair-api-gateway

# Remove all cumpair containers
docker ps -a | Select-String cumpair | ForEach-Object { docker rm ($_ -split '\s+')[0] }

# View logs
docker logs cumpair-api-gateway -f

# Check all running services
docker ps

# Memory monitoring
docker stats --no-stream
```

## Complete Docker Compose (After all built)
```powershell
docker-compose -f docker-compose.phase7.yml up -d
docker-compose -f docker-compose.phase7.yml logs -f
docker-compose -f docker-compose.phase7.yml down
```

## Memory Check Before Each Build
```powershell
# Windows PowerShell
[Math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum / 1gb)

# Quick free space check
Get-Volume -DriveLetter D | Select-Object SizeRemaining

# Docker disk usage
docker system df
```

## Build Order Recommendation
1. ✅ **API Gateway** (8000) - Smallest, no ML deps
2. ⏳ **Search** (8010) - Medium
3. ⏳ **Real-Time** (8013) - Small
4. ⏳ **Elasticsearch** (8015) - Medium
5. ⏳ **Event Bus** (8016) - Small
6. ⏳ **ML Engine** (8014) - Largest, build last

Wait 1-2 minutes between builds for Docker to stabilize.
