# Cumpair Architecture

## Overview

Cumpair is a hybrid AI-powered product analysis and price comparison system designed for efficient cloud + local deployment.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD CORE (DigitalOcean)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌───────────────────────────┐        │
│  │   HAProxy    │ ──────▶ │     FastAPI (Web)         │        │
│  │   (Ingress)  │         │  ┌─────────────────────┐  │        │
│  │              │         │  │  /api/v1/search     │  │        │
│  │  - TLS       │         │  │  /api/v1/analyze    │  │        │
│  │  - Rate Limit│         │  │  /api/v1/health     │  │        │
│  │  - IP Filter │         │  │  /api/v1/metrics    │  │        │
│  └──────────────┘         │  └─────────────────────┘  │        │
│         │                 └──────────┬─────────────────┘        │
│         │                            │                          │
│         └────────────────────────────┘                          │
│                                      │                          │
│         ┌────────────────────────────┴────────────────┐         │
│         │                                              │         │
│  ┌──────▼──────┐  ┌────────────┐  ┌─────────────────┐│         │
│  │  Postgres   │  │   Redis    │  │ Celery Workers  ││         │
│  │  (Neon)     │  │  (Upstash) │  │                 ││         │
│  │             │  │            │  │ - Cleanup       ││         │
│  │ - Products  │  │ - Cache    │  │ - Re-scrape     ││         │
│  │ - Prices    │  │ - Queue    │  │ - Analytics     ││         │
│  │ - Analytics │  │ - Sessions │  │                 ││         │
│  └─────────────┘  └────────────┘  └─────────────────┘│         │
│                                                        │         │
│  ┌────────────────────┐  ┌──────────────────────────┐ │         │
│  │   Prometheus       │  │   Grafana Cloud         │ │         │
│  │   (Metrics)        │  │   (Dashboards)          │ │         │
│  └────────────────────┘  └──────────────────────────┘ │         │
│                                                        │         │
└────────────────────────────────────────────────────────┘         │
                               ▲                                   │
                               │ HTTPS (secure push)               │
                               │                                   │
┌──────────────────────────────┴───────────────────────────────────┐
│                     LOCAL NODE (Developer Machine)               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Playwright Scrapers                        │ │
│  │                                                             │ │
│  │  - Amazon, eBay, Walmart, Best Buy parsers                │ │
│  │  - Proxy rotation                                          │ │
│  │  - Anti-detection (random delays, user agents)            │ │
│  │  - Headless browser management                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                Local AI (Optional)                         │ │
│  │                                                             │ │
│  │  - YOLOv8 (Object Detection)                              │ │
│  │  - CLIP (Image Search)                                     │ │
│  │  - EfficientNet (Spec Extraction)                         │ │
│  │  OR: Call Groq API for cloud inference                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Key Principles

### 1. **Hybrid Architecture**
- **Cloud Core**: Handles persistent state, public API, ingress, and monitoring
- **Local Compute**: Runs resource-intensive scrapers and optional AI inference
- **Benefit**: Saves cloud costs while keeping heavy computation local

### 2. **Single Source of Truth**
- Postgres (in cloud) is authoritative for all data
- Local machines only push results and maintain ephemeral caches
- All state changes flow through cloud API

### 3. **Secure Ingress**
- HAProxy is the ONLY publicly exposed service
- All other services behind HAProxy on private network
- TLS termination at ingress
- IP whitelisting for admin/stats endpoints
- Rate limiting per IP/API key

### 4. **Graceful Degradation**
- AI features fallback to simpler heuristics if models unavailable
- External cloud inference (Groq) as backup
- Confidence scores indicate when manual verification needed

## Services

### Cloud Services

#### HAProxy (Ingress Controller)
- **Purpose**: TLS termination, routing, rate limiting, security
- **Port**: 80 (HTTP), 443 (HTTPS), 8404 (stats)
- **Features**: IP filtering, rate limiting, backend health checks
- **Config**: `/configs/haproxy.cfg.template`

#### FastAPI (Web Application)
- **Purpose**: Main API endpoints, business logic
- **Port**: 8000 (internal)
- **Endpoints**:
  - `POST /api/v1/auth/api-key` - API key validation
  - `GET /api/v1/search?q=...` - Product search
  - `POST /api/v1/image-search` - AI-powered image search
  - `POST /api/v1/scraper/result` - Internal scraper webhook
  - `GET /api/v1/health` - Health check
  - `GET /api/v1/metrics` - Prometheus metrics

#### Celery Workers
- **Purpose**: Background tasks (cleanup, re-scrape, analytics)
- **Concurrency**: 2 workers (adjustable)
- **Tasks**: Scheduled jobs, async processing

#### Postgres (Database)
- **Tables**: products, stores, prices, clicks, api_keys, scrape_jobs
- **Managed**: Use Neon or managed Postgres in production
- **Backups**: Automated daily snapshots

#### Redis
- **Purpose**: Cache, task queue, session storage
- **Managed**: Use Upstash in production for reliability

### Local Services

#### Scraper Service
- **Technology**: Node.js + Playwright
- **Features**: Multi-site support, proxy rotation, anti-detection
- **Push Results**: Secure POST to `/api/v1/scraper/result`

#### AI Models (Optional Local)
- **YOLOv8**: Object detection for product identification
- **CLIP**: Image-text similarity for search
- **EfficientNet**: Specification extraction
- **Fallback**: Groq API for cloud inference

## Data Flow

### 1. User Search Request
```
User → HAProxy → FastAPI → Postgres (cached results)
                         → Redis (fresh data check)
                         → Return results
```

### 2. Image Search Request
```
User → HAProxy → FastAPI → AI Service (CLIP)
                         → Postgres (find matches)
                         → Return ranked results
```

### 3. Scraping Flow
```
Cloud: Create scrape_job → Redis queue
Local: Poll queue → Playwright scraper → Extract data
       → POST /api/v1/scraper/result (with auth)
Cloud: Validate → Save to Postgres → Update cache
```

### 4. Analytics Generation
```
Celery (scheduled) → Aggregate data from Postgres
                   → Generate insights
                   → Store in analytics table
                   → Serve via API
```

## Security

### Network Isolation
- Public network: HAProxy only
- Private network: All backend services
- No direct database/Redis access from internet

### Authentication & Authorization
- API keys managed via CrytoLens
- JWT tokens for admin access
- IP whitelisting for sensitive endpoints
- Rate limiting per key/IP

### Data Protection
- TLS everywhere (production)
- Secrets via environment variables
- No hardcoded credentials
- Regular security audits

## Monitoring

### Metrics (Prometheus)
- API request rate/latency
- Error rates (4xx, 5xx)
- Scraper success/fail rates
- Database connection pool
- Redis queue length
- Memory/CPU usage

### Dashboards (Grafana)
- System overview
- API performance
- Scraping health
- Business metrics (searches, clicks, conversions)

### Alerts
- API error rate > 1% for 5 min
- Celery queue > 1000 jobs
- Disk usage > 80%
- Service health failing

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### CI/CD
```
GitHub PR → Lint & Test → Build Images → Push to Registry
         → Deploy to Staging → Manual Approval → Deploy to Production
```

## Scaling Strategy

### Year 1 (GitHub Education Credits)
- 1x DigitalOcean droplet (2GB RAM, $12/month)
- Managed Postgres (Neon free tier)
- Managed Redis (Upstash free tier)
- Local scraping (developer machine)

### Year 2+ (Revenue-funded)
- Scale droplets horizontally
- Add CDN (Cloudflare)
- Dedicated scraper VPS pool
- Load balancer for web workers

## Cost Optimization

- Use free tiers where possible (Neon, Upstash, Grafana Cloud)
- Keep heavy compute local (scraping, AI)
- Efficient caching strategy
- Optimize image sizes and build times
- Monitor and alert on resource usage
