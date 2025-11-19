# ALL DOCKER BUILD COMMANDS - Copy & Paste Ready

## Step 0: Setup (Run Once)
```
docker network create backend
docker system prune -a --volumes -f
```

## Step 1: Redis
```
docker build -f docker/Dockerfile.redis -t cumpair-redis:latest .
docker run -d --name cumpair-redis -p 6379:6379 --network backend cumpair-redis:latest
docker logs cumpair-redis -f
```

## Step 2: PostgreSQL
```
docker build -f docker/Dockerfile.postgres -t cumpair-postgres:latest .
docker run -d --name cumpair-postgres -p 5432:5432 --network backend -e POSTGRES_PASSWORD=admin cumpair-postgres:latest
docker logs cumpair-postgres -f
```

## Step 3: Prometheus
```
docker build -f docker/Dockerfile.prometheus -t cumpair-prometheus:latest .
docker run -d --name cumpair-prometheus -p 9090:9090 --network backend cumpair-prometheus:latest
docker logs cumpair-prometheus -f
```

## Step 4: Grafana
```
docker build -f docker/Dockerfile.grafana -t cumpair-grafana:latest .
docker run -d --name cumpair-grafana -p 3000:3000 --network backend -e GF_SECURITY_ADMIN_PASSWORD=admin cumpair-grafana:latest
docker logs cumpair-grafana -f
```

## Step 5: Frontend (React/Vite)
```
cd frontend
docker build -f Dockerfile -t cumpair-frontend:latest .
docker run -d --name cumpair-frontend -p 3001:3001 --network backend cumpair-frontend:latest
docker logs cumpair-frontend -f
```

## Step 6: API Gateway
```
cd ..
docker build -f docker/Dockerfile.api-gateway -t cumpair-api-gateway:latest .
docker run -d --name cumpair-api-gateway -p 8000:8000 --network backend cumpair-api-gateway:latest
docker logs cumpair-api-gateway -f
```

## Step 7: Search Service
```
docker build -f docker/Dockerfile.search-discovery -t cumpair-search:latest .
docker run -d --name cumpair-search -p 8010:8010 --network backend cumpair-search:latest
docker logs cumpair-search -f
```

## Step 8: Real-Time Service
```
docker build -f docker/Dockerfile.realtime -t cumpair-realtime:latest .
docker run -d --name cumpair-realtime -p 8013:8013 --network backend cumpair-realtime:latest
docker logs cumpair-realtime -f
```

## Step 9: ML Engine
```
docker build -f docker/Dockerfile.ml-engine -t cumpair-ml:latest .
docker run -d --name cumpair-ml -p 8014:8014 --network backend cumpair-ml:latest
docker logs cumpair-ml -f
```

## Step 10: Elasticsearch Service
```
docker build -f docker/Dockerfile.elasticsearch-service -t cumpair-elasticsearch:latest .
docker run -d --name cumpair-elasticsearch -p 8015:8015 --network backend cumpair-elasticsearch:latest
docker logs cumpair-elasticsearch -f
```

## Step 11: Event Bus Service
```
docker build -f docker/Dockerfile.event-bus -t cumpair-events:latest .
docker run -d --name cumpair-events -p 8016:8016 --network backend cumpair-events:latest
docker logs cumpair-events -f
```

## Quick Check All Running
```
docker ps
```

## Stop All
```
docker stop $(docker ps -q)
```

## Remove All
```
docker rm $(docker ps -aq)
```

## View Logs
```
docker logs cumpair-frontend -f
docker logs cumpair-api-gateway -f
docker logs cumpair-redis -f
docker logs cumpair-prometheus -f
docker logs cumpair-grafana -f
```

## Access Points
- Frontend: http://localhost:3001
- API Gateway: http://localhost:8000
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Elasticsearch: http://localhost:9200
