# Docker Services Inventory Report

## Summary
Total Services Identified: **16 unique services** across multiple docker-compose files

## Service Categories & Details

### **CORE INFRASTRUCTURE SERVICES** (4 services)
Services essential for the application's basic functionality:

1. **redis** - Redis cache and message broker
   - Image: `redis:7-alpine`
   - Port: `6379`
   - Purpose: Caching, Celery message broker
   - Health Check: ✅ Configured
   - Files: All main compose files

2. **postgres** - PostgreSQL database
   - Image: `postgres:15-alpine`
   - Port: `5432`
   - Purpose: Primary data storage
   - Health Check: ✅ Configured
   - Files: All main compose files

3. **web** - Main FastAPI backend application
   - Build: Custom (main Dockerfile)
   - Port: `8000`
   - Purpose: REST API server, core business logic
   - Health Check: ✅ Configured
   - Files: All main compose files

4. **nginx** - Reverse proxy and load balancer
   - Image: `nginx:alpine`
   - Ports: `80`, `443`
   - Purpose: Load balancing, SSL termination
   - Health Check: ✅ Configured
   - Files: docker-compose.complete.yml only

### **BACKGROUND PROCESSING SERVICES** (2 services)
Services for asynchronous task processing:

5. **worker** - Celery worker for background tasks
   - Build: Custom (main Dockerfile)
   - Purpose: Product analysis, scraping coordination
   - Profile: `worker` (optional in basic compose)
   - Files: All main compose files

6. **flower** - Celery monitoring dashboard
   - Build: Custom (main Dockerfile)
   - Port: `5555`
   - Purpose: Monitor Celery tasks and workers
   - Profile: `worker` (optional in basic compose)
   - Files: All main compose files

### **MICROSERVICES** (3 services)
Specialized services for specific functionality:

7. **scraper** - Node.js web scraping service
   - Build: Custom (`./scraper/Dockerfile`)
   - Port: `3001`
   - Purpose: Web scraping, product data extraction
   - Profile: `scraper` (optional in basic compose)
   - Health Check: ✅ Configured
   - Files: All main compose files

8. **captcha** - CAPTCHA solving service
   - Build: Custom (`./captcha-service/Dockerfile`)
   - Port: `9001`
   - Purpose: Automated CAPTCHA solving
   - Health Check: ✅ Configured
   - Files: docker-compose.complete.yml only

9. **proxy** - Proxy management service
   - Build: Custom (`./proxy-service/Dockerfile`)
   - Port: `8001`
   - Purpose: Proxy rotation and management
   - Health Check: ✅ Configured
   - Files: docker-compose.complete.yml only

### **FRONTEND SERVICES** (1 service)
User interface services:

10. **frontend** - React/Vite frontend application
    - Build: Custom (`./frontend/Dockerfile`)
    - Port: `8080` (maps to internal `3000`)
    - Purpose: Web user interface
    - Profile: `frontend` (optional in basic compose)
    - Health Check: ✅ Configured
    - Files: All main compose files

### **MONITORING & OBSERVABILITY SERVICES** (2 services)
Services for system monitoring and metrics:

11. **prometheus** - Metrics collection and storage
    - Image: `prom/prometheus:latest`
    - Port: `9090`
    - Purpose: Metrics collection, alerting
    - Profile: `monitor` (optional in basic compose)
    - Health Check: ✅ Configured
    - Files: All main compose files

12. **grafana** - Metrics visualization dashboard
    - Image: `grafana/grafana:latest`
    - Port: `3002` (maps to internal `3000`)
    - Purpose: Metrics visualization, dashboards
    - Profile: `monitor` (optional in basic compose)
    - Health Check: ✅ Configured
    - Files: All main compose files

### **SELF-HOSTED SERVICE VARIANTS** (4 services)
Standalone services with their own Redis instances:

13. **captcha-solver** - Standalone CAPTCHA service
    - Build: Custom (`./captcha-service/Dockerfile`)
    - Port: `9001`
    - Purpose: Independent CAPTCHA solving
    - Files: captcha-service/docker-compose.yml

14. **redis** (captcha-service) - Dedicated Redis for CAPTCHA service
    - Image: `redis:7-alpine`
    - Port: `6380`
    - Purpose: CAPTCHA service caching
    - Files: captcha-service/docker-compose.yml

15. **haproxy** - HAProxy load balancer for proxy service
    - Image: `haproxy:2.8`
    - Ports: `8080`, `8081`
    - Purpose: Proxy load balancing and stats
    - Health Check: ✅ Configured
    - Files: proxy-service/docker-compose.yml

16. **proxy-manager-api** - Standalone proxy management API
    - Build: Custom (`./proxy-service/Dockerfile`)
    - Port: `8001`
    - Purpose: Independent proxy management
    - Files: proxy-service/docker-compose.yml

17. **redis** (proxy-service) - Dedicated Redis for proxy service
    - Image: `redis:7-alpine`
    - Port: `6380`
    - Purpose: Proxy service caching
    - Files: proxy-service/docker-compose.yml

## Docker Compose File Analysis

### **docker-compose.yml** (Main/Basic Configuration)
- **Services**: 9 services (redis, postgres, web, worker, flower, scraper, frontend, prometheus, grafana)
- **Profiles Used**: worker, scraper, frontend, monitor
- **Purpose**: Development and basic production deployment
- **Security Level**: Basic

### **docker-compose.complete.yml** (Production Configuration)
- **Services**: 12 services (all main services + captcha, proxy, nginx)
- **Profiles Used**: None (all services enabled)
- **Purpose**: Full production deployment with all features
- **Security Level**: Advanced (secrets, network segmentation, resource limits)
- **Features**: Resource limits, secrets management, network segmentation, enhanced health checks

### **docker-compose.secure.yml**
- **Status**: Empty file
- **Purpose**: Likely placeholder for security-focused configuration

### **captcha-service/docker-compose.yml** (Standalone CAPTCHA)
- **Services**: 2 services (captcha-solver, redis)
- **Purpose**: Independent CAPTCHA service deployment
- **Port**: 9001 (CAPTCHA), 6380 (Redis)

### **proxy-service/docker-compose.yml** (Standalone Proxy)
- **Services**: 3 services (haproxy, redis, proxy-manager-api)
- **Purpose**: Independent proxy management service
- **Ports**: 8080, 8081 (HAProxy), 8001 (API), 6380 (Redis)

## Service Dependencies & Startup Order

### **Tier 1 - Infrastructure** (Start First)
1. redis
2. postgres

### **Tier 2 - Core Application** (Start After Tier 1)
1. web (depends on redis, postgres)

### **Tier 3 - Background Processing** (Start After Tier 2)
1. worker (depends on web, redis, postgres)
2. flower (depends on worker)

### **Tier 4 - Microservices** (Start After Tier 1)
1. scraper (depends on redis)
2. captcha (depends on redis)
3. proxy (depends on redis)

### **Tier 5 - Frontend & Proxy** (Start After Tier 2-4)
1. frontend (depends on web, scraper)
2. nginx (depends on web, frontend)

### **Tier 6 - Monitoring** (Start After Core Services)
1. prometheus
2. grafana (depends on prometheus)

## Resource Requirements Summary

### **High Resource Services** (4GB+ Memory)
- frontend: 6GB memory, 2 CPUs (complete.yml)
- web: 4GB memory, 2 CPUs (complete.yml)

### **Medium Resource Services** (1-3GB Memory)
- worker: 3GB memory, 2 CPUs
- scraper: 3GB memory, 1.5 CPUs
- postgres: 2GB memory, 1 CPU

### **Light Resource Services** (<1GB Memory)
- redis: 1GB memory, 0.5 CPUs
- captcha: 1GB memory, 1 CPU
- proxy: 512MB memory, 0.5 CPUs
- flower: 512MB memory, 0.5 CPUs
- prometheus: 1GB memory, 1 CPU
- grafana: 512MB memory, 0.5 CPUs
- nginx: 256MB memory, 0.5 CPUs

## Health Check Coverage
✅ **Services with Health Checks**: 14/17 services
❌ **Services without Health Checks**: worker, proxy-manager-api, redis (proxy-service)

## Security Features (docker-compose.complete.yml)
- **Secrets Management**: postgres_password, grafana_password
- **Network Segmentation**: frontend, backend (internal), monitoring
- **Resource Limits**: All services have memory/CPU limits
- **Restart Policies**: unless-stopped for all services

## Recommendations

### **For Development**
- Use `docker-compose.yml` with selective profiles
- Start with: `docker-compose --profile worker up`

### **For Production**
- Use `docker-compose.complete.yml`
- Ensure secrets are properly configured
- Monitor resource usage and adjust limits as needed

### **For Testing Individual Services**
- Use service-specific compose files in subdirectories
- Test CAPTCHA service: `cd captcha-service && docker-compose up`
- Test proxy service: `cd proxy-service && docker-compose up`

---
**Report Generated**: $(Get-Date)
**Total Services Analyzed**: 17 services across 5 docker-compose files
