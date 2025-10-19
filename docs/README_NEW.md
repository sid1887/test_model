# 🔍 Cumpair

**AI-Powered Product Analysis & Price Comparison System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)

Cumpair is a hybrid cloud + local system that combines AI-powered product recognition with intelligent price comparison across multiple e-commerce platforms. Designed for efficient deployment using GitHub Education credits and sustainable monetization through affiliate marketing and B2B API licensing.

---

## 🌟 Key Features

### 🖼️ AI-Powered Analysis
- **YOLOv8** object detection for product identification
- **CLIP** for semantic image search
- **EfficientNet** for specification extraction
- Graceful fallback to cloud inference (Groq API)

### 🕷️ Adaptive Web Scraping
- Multi-site support (Amazon, eBay, Walmart, Best Buy, etc.)
- Proxy rotation and anti-detection
- Headless browser automation with Playwright
- Smart retry and error handling

### 💰 Monetization Ready
- **Affiliate marketing** (B2C) - Track clicks and conversions
- **White-label API** (B2B) - CrytoLens-powered licensing
- **Data analytics** (B2B Premium) - Merchant insights and reports

### 🏗️ Production Architecture
- **HAProxy** ingress with TLS termination
- **FastAPI** for high-performance async API
- **Celery** for distributed background tasks
- **Postgres** + **Redis** for reliable data storage
- **Prometheus** + **Grafana** for observability

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git
- 4GB+ RAM available

### Option 1: Automated Setup (Recommended)

```powershell
# Windows
.\quickstart.ps1

# Linux/Mac
bash quickstart.sh
```

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/cumpair.git
cd cumpair

# 2. Create environment file
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, database URLs, etc.)

# 3. Start development environment
docker-compose -f docker-compose.dev.yml up --build

# 4. Run database migrations
docker-compose -f docker-compose.dev.yml exec web alembic upgrade head
```

### Verify Installation

```bash
# Check all services are running
docker-compose -f docker-compose.dev.yml ps

# Test API health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"1.0.0","timestamp":"..."}
```

---

## 📍 Access Points

Once running, access these endpoints:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | Main API endpoint |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Health Check** | http://localhost:8000/api/v1/health | Service health status |
| **Scraper** | http://localhost:3001 | Scraper service |
| **HAProxy Stats** | http://localhost:8404/stats | HAProxy statistics (prod only) |

---

## 📖 Documentation

- **[Architecture Overview](docs/architecture.md)** - System design and data flow
- **[Deployment Guide](docs/deploy.md)** - Production deployment to DigitalOcean
- **[API Reference](http://localhost:8000/docs)** - Interactive API documentation
- **[Developer Handoff](HANDOFF.md)** - Complete Year-1 growth plan

---

## 🏗️ Project Structure

```
cumpair/
├── app/                       # FastAPI application
│   ├── api/routes/           # API endpoints
│   ├── core/                 # Core utilities (config, database)
│   ├── models/               # Database models
│   └── services/             # Business logic (AI, scraping)
├── scraper/                   # Node.js scraper service
│   ├── src/                  # Scraper source code
│   └── Dockerfile            # Scraper container
├── docker/                    # Docker configuration
│   └── entrypoints/          # Service startup scripts
├── configs/                   # Configuration templates
│   └── haproxy.cfg.template  # HAProxy config
├── docs/                      # Documentation
├── monitoring/                # Prometheus & Grafana configs
├── docker-compose.dev.yml     # Development environment
├── docker-compose.prod.yml    # Production environment
├── Dockerfile                 # Main application container
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 🔧 Development Workflow

### Working with Services

```bash
# View logs for all services
docker-compose -f docker-compose.dev.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs -f web

# Restart a service
docker-compose -f docker-compose.dev.yml restart web

# Rebuild after code changes
docker-compose -f docker-compose.dev.yml up --build web

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

### Database Migrations

```bash
# Create new migration
docker-compose -f docker-compose.dev.yml exec web alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose -f docker-compose.dev.yml exec web alembic upgrade head

# Rollback one migration
docker-compose -f docker-compose.dev.yml exec web alembic downgrade -1

# Check current version
docker-compose -f docker-compose.dev.yml exec web alembic current
```

### Running Tests

```bash
# Run all tests
docker-compose -f docker-compose.dev.yml exec web pytest

# Run specific test file
docker-compose -f docker-compose.dev.yml exec web pytest tests/test_api.py

# Run with coverage
docker-compose -f docker-compose.dev.yml exec web pytest --cov=app tests/
```

---

## 🚢 Production Deployment

See **[docs/deploy.md](docs/deploy.md)** for complete production deployment guide.

### Quick Production Start

```bash
# 1. Configure production environment
cp .env.example .env
nano .env  # Set ENVIRONMENT=production, secure SECRET_KEY, etc.

# 2. Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 3. Run migrations
docker-compose -f docker-compose.prod.yml exec web alembic upgrade head

# 4. Check service health
docker-compose -f docker-compose.prod.yml ps
curl https://api.cumpair.tech/api/v1/health
```

---

## 🔑 Environment Variables

Key variables to configure in `.env`:

```bash
# Core Settings
ENVIRONMENT=development          # development, staging, production
DEBUG=true                       # false in production
SECRET_KEY=your-32-char-key      # MUST change in production!

# Database (use Neon in production)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (use Upstash in production)
REDIS_URL=redis://host:6379

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Monetization (when ready)
CRYPTOLENS_API_KEY=              # For API licensing
STRIPE_SECRET_KEY=               # For payments
```

See `.env.example` for complete list.

---

## 💡 API Usage Examples

### Search Products

```bash
curl -X GET "http://localhost:8000/api/v1/search?q=iPhone+15&limit=10" \
  -H "Content-Type: application/json"
```

### Image-Based Search

```bash
curl -X POST "http://localhost:8000/api/v1/image-search" \
  -F "file=@product_image.jpg"
```

### Analyze Product Image

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@product_image.jpg" \
  -F "full_analysis=true"
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI, Pydantic, Uvicorn |
| **Database** | PostgreSQL (Neon), Alembic |
| **Cache/Queue** | Redis (Upstash), Celery |
| **AI/ML** | YOLOv8, CLIP, EfficientNet, Groq |
| **Scraping** | Playwright, Puppeteer, Cheerio |
| **Ingress** | HAProxy, Nginx |
| **Monitoring** | Prometheus, Grafana |
| **Container** | Docker, Docker Compose |
| **Frontend** | React, Vite, TailwindCSS |

---

## 📊 Monitoring

### Metrics Collection

Cumpair exposes Prometheus metrics at `/metrics`:

- **API**: Request rate, latency, error rate
- **Scraper**: Success/fail rates, site-specific metrics
- **Celery**: Queue length, task duration
- **System**: CPU, memory, disk usage

### Dashboards

Access Grafana dashboards for:
- System overview
- API performance
- Scraping health
- Business metrics (searches, clicks, conversions)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection
- [OpenAI CLIP](https://github.com/openai/CLIP) - Image-text matching
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Playwright](https://playwright.dev/) - Browser automation

---

## 📧 Support

- **Documentation**: Check `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/cumpair/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cumpair/discussions)

---

## 🗺️ Roadmap

### Year 1 (Current)
- [x] Core API and database setup
- [x] AI model integration (YOLO, CLIP)
- [x] Basic scraper implementation
- [x] Docker containerization
- [ ] HAProxy ingress in production
- [ ] Frontend MVP
- [ ] Affiliate link integration
- [ ] White-label API with CrytoLens

### Year 2 (Planned)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-region deployment
- [ ] API rate limiting and quotas
- [ ] Premium data exports

---

**Built with ❤️ for developers and price-conscious shoppers**
