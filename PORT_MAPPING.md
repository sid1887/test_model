# Port Configuration Reference

**Phase 2 Consolidation: Centralized Port Management**

This document serves as the single source of truth for all service ports, container networking, and environment variable configuration across the Cumpair system.

---

## Service Port Allocation

| Service | Default Port | Environment Variable | Config Setting | Status |
|---------|-------------|---------------------|----------------|--------|
| **FastAPI (Web)** | 8000 | `PORT` or `API_PORT` | `settings.api_port` | ✅ Configured |
| **Scraper (Node.js)** | 3001 | `PORT` or `SCRAPER_PORT` | `settings.scraper_port` | ✅ Configured |
| **Captcha Service** | 9001 | `PORT` or `CAPTCHA_PORT` | `settings.captcha_service_url` | ✅ Configured |
| **Redis** | 6379 | `REDIS_PORT` | `settings.redis_url` | ✅ Configured |
| **PostgreSQL** | 5432 | `POSTGRES_PORT` | `settings.database_url` | ✅ Configured |
| **Celery Worker** | - | (no direct port) | Uses `REDIS_URL` | ✅ Configured |
| **Captcha Redis** | 6380 | (mapped in docker-compose) | - | ✅ Configured |
| **HAProxy (HTTP)** | 80 | `HAPROXY_HTTP_PORT` | - | Production only |
| **HAProxy (HTTPS)** | 443 | `HAPROXY_HTTPS_PORT` | - | Production only |
| **HAProxy (Stats)** | 8404 | `HAPROXY_STATS_PORT` | - | Production only |

---

## Configuration Priority

**Port resolution order (highest to lowest priority):**

1. **Environment Variables** (`.env`, docker-compose `environment`, shell export)
2. **Python Config Settings** (`app/core/config.py` → reads from `.env` via Pydantic)
3. **Hardcoded Defaults** (fallback if env vars not set)

### Python Services (FastAPI, Celery Worker)

Configuration file: `app/core/config.py`

```python
class Settings(BaseSettings):
    # Centralized port configuration
    api_port: int = 8000                                  # Default: 8000
    scraper_port: int = 3001                              # Default: 3001
    
    # Service URLs (default to localhost for local dev)
    scraper_service_url: str = "http://localhost:3001"
    captcha_service_url: str = "http://localhost:9001"
    
    # Redis (port embedded in URL)
    redis_url: str = "redis://localhost:6379"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # PostgreSQL (port embedded in URL)
    database_url: str = "postgresql://compair:compair123@localhost:5432/compair"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Environment variable mapping:**
- `API_PORT` → `settings.api_port`
- `SCRAPER_PORT` → `settings.scraper_port`
- `REDIS_URL` → `settings.redis_url`
- `DATABASE_URL` → `settings.database_url`

### Node.js Services (Scraper)

Configuration file: `scraper/server.js`

```javascript
const PORT = process.env.SCRAPER_PORT || process.env.PORT || 3001;
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';
```

### Flask Services (Captcha Service)

Configuration file: `captcha-service/app.py`

```python
# Redis configuration
redis_client = redis.from_url(os.getenv('REDIS_URL'))  # If REDIS_URL provided
# Fallback:
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', '6379'))
)

# Flask port
port = int(os.getenv('CAPTCHA_PORT') or os.getenv('PORT') or 9001)
app.run(host='0.0.0.0', port=port)
```

---

## Docker Compose Configuration

### Development (`docker-compose.dev.yml`)

```yaml
services:
  postgres:
    ports:
      - "5432:5432"                    # Fixed host:container mapping

  redis:
    ports:
      - "${REDIS_PORT:-6379}:${REDIS_PORT:-6379}"

  web:
    ports:
      - "${API_PORT:-8000}:${API_PORT:-8000}"
    environment:
      PORT: "${API_PORT:-8000}"
      DATABASE_URL: "postgresql://${POSTGRES_USER:-compair}:${POSTGRES_PASSWORD:-compair123}@postgres:5432/${POSTGRES_DB:-compair}"
      REDIS_URL: "redis://redis:${REDIS_PORT:-6379}"
      SCRAPER_SERVICE_URL: "http://scraper:${SCRAPER_PORT:-3001}"

  scraper:
    ports:
      - "${SCRAPER_PORT:-3001}:${SCRAPER_PORT:-3001}"
    environment:
      PORT: "${SCRAPER_PORT:-3001}"
      REDIS_HOST: "redis"
      REDIS_PORT: "${REDIS_PORT:-6379}"
      REDIS_URL: "redis://redis:${REDIS_PORT:-6379}"
      PYTHON_SERVICE_URL: "http://web:${API_PORT:-8000}"
```

### Production (`docker-compose.prod.yml`)

**Note:** Production uses HAProxy ingress. Services are accessed via HAProxy reverse proxy, not direct port exposure.

```yaml
services:
  haproxy:
    ports:
      - "${HAPROXY_HTTP_PORT:-80}:80"
      - "${HAPROXY_HTTPS_PORT:-443}:443"
      - "${HAPROXY_STATS_PORT:-8404}:8404"
```

Internal service ports remain the same but are not exposed to host (accessed via internal `cumpair` network).

---

## Environment Variable Reference

### `.env` Template

```bash
# API Service
API_PORT=8000

# Scraper Service
SCRAPER_PORT=3001

# Captcha Service
CAPTCHA_PORT=9001

# Redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# PostgreSQL
POSTGRES_PORT=5432
POSTGRES_DB=compair
POSTGRES_USER=compair
POSTGRES_PASSWORD=compair123
DATABASE_URL=postgresql://compair:compair123@postgres:5432/compair

# Celery (uses Redis)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# HAProxy (Production only)
HAPROXY_HTTP_PORT=80
HAPROXY_HTTPS_PORT=443
HAPROXY_STATS_PORT=8404

# Service URLs (for internal communication)
SCRAPER_SERVICE_URL=http://scraper:3001
CAPTCHA_SERVICE_URL=http://captcha-service:9001
PYTHON_SERVICE_URL=http://web:8000
```

---

## Entrypoint Scripts

### `docker/entrypoints/web-entrypoint.sh`

```bash
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export HOST=${HOST:-0.0.0.0}

# Wait for database (postgres on default port 5432)
pg_isready -h postgres -p 5432

# Start Uvicorn
exec uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS"
```

### `docker/entrypoints/scraper-entrypoint.sh`

```bash
export PORT=${PORT:-3001}
export NODE_ENV=${NODE_ENV:-production}

# Wait for Redis
nc -z $REDIS_HOST 6379

# Start Node.js scraper
exec node /app/server.js
```

### `docker/entrypoints/worker-entrypoint.sh`

```bash
# Celery worker (no direct port, uses Redis broker)
exec celery -A app.tasks worker \
    --loglevel=info \
    --concurrency=${CELERY_CONCURRENCY:-2}
```

---

## Network Topology

### Development (Direct Port Mapping)

```
Host Machine
├── localhost:8000 → web:8000 (FastAPI)
├── localhost:3001 → scraper:3001 (Node.js)
├── localhost:5432 → postgres:5432 (PostgreSQL)
├── localhost:6379 → redis:6379 (Redis)
└── localhost:9001 → captcha-service:9001 (Flask) [if running standalone]
```

### Production (HAProxy Ingress)

```
Host Machine
├── :80 (HTTP) → haproxy → web:8000 (FastAPI)
├── :443 (HTTPS) → haproxy → web:8000 (FastAPI)
└── :8404 → haproxy stats UI

Internal Network (cumpair)
├── web:8000 (FastAPI)
├── scraper:3001 (Node.js)
├── worker:- (Celery, no direct port)
├── postgres:5432 (PostgreSQL)
└── redis:6379 (Redis)
```

---

## Migration & Testing

### Verify Current Port Configuration

```powershell
# Check active ports on Windows
Get-NetTCPConnection -LocalPort 8000,3001,5432,6379,9001 | Select-Object LocalPort,State,OwningProcess

# Check environment variables
docker-compose -f docker-compose.dev.yml config
```

```bash
# On Linux/Mac
lsof -i :8000,3001,5432,6379,9001
netstat -tuln | grep -E '8000|3001|5432|6379|9001'

# Check docker-compose resolution
docker-compose -f docker-compose.dev.yml config
```

### Override Ports for Testing

Create `.env` file in project root:

```bash
API_PORT=8080
SCRAPER_PORT=3002
REDIS_PORT=6380
```

Then run:

```bash
docker-compose -f docker-compose.dev.yml up
```

Services will start on the overridden ports.

### Port Conflict Resolution

If ports are already in use:

1. **Identify conflicting process:**
   ```powershell
   # Windows
   Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
   ```
   
2. **Stop conflicting service or change port:**
   ```bash
   # Change port in .env
   echo "API_PORT=8080" >> .env
   ```

3. **Restart containers:**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up -d
   ```

---

## Best Practices

### ✅ DO:
- Use environment variables for all port configuration
- Document port changes in `.env.example`
- Use service names (e.g., `redis`, `postgres`) for inter-service communication in Docker
- Test with non-default ports before production deployment
- Keep internal Docker ports consistent; vary host-mapped ports if needed

### ❌ DON'T:
- Hardcode ports in application code
- Expose unnecessary ports to host in production
- Use `localhost` in Docker service-to-service communication (use service names)
- Forget to update healthcheck URLs when changing ports
- Map conflicting ports without checking availability

---

## Healthcheck Endpoints

| Service | Healthcheck URL | Expected Response |
|---------|----------------|-------------------|
| FastAPI | `http://localhost:8000/api/v1/health` | `200 OK` + JSON status |
| Scraper | `http://localhost:3001/health` | `200 OK` + JSON status |
| Captcha | `http://localhost:9001/health` | `200 OK` + JSON status |
| Redis | `redis-cli ping` → `PONG` | `PONG` |
| PostgreSQL | `pg_isready` | `accepting connections` |

---

## Troubleshooting

### Issue: Service can't connect to another service

**Symptom:** `Connection refused` or `getaddrinfo failed` errors

**Solution:**
- Use Docker service names (e.g., `redis`, `postgres`) instead of `localhost` in URLs
- Verify services are on the same Docker network
- Check `docker-compose logs <service>` for startup errors

### Issue: Port already in use

**Symptom:** `Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use`

**Solution:**
- Identify process: `lsof -i :8000` (Linux) or `Get-NetTCPConnection -LocalPort 8000` (Windows)
- Stop conflicting service or change port in `.env`
- Use `docker-compose down` to ensure clean shutdown before restart

### Issue: Environment variables not taking effect

**Symptom:** Service uses default port despite `.env` configuration

**Solution:**
- Verify `.env` is in the same directory as `docker-compose.yml`
- Restart containers: `docker-compose down && docker-compose up -d`
- Check resolved config: `docker-compose config` to see final values
- Ensure no shell environment variables are overriding `.env`

---

## References

- **Config Source:** `app/core/config.py`, `scraper/server.js`, `captcha-service/app.py`
- **Compose Files:** `docker-compose.dev.yml`, `docker-compose.prod.yml`
- **Entrypoints:** `docker/entrypoints/*.sh`
- **Archive Log:** `archive/ARCHIVE_LOG.md`

**Last Updated:** Phase 2 Consolidation (Port Audit Complete)
**Status:** ✅ All services configured with environment-based ports
