# Cumpair - Open-Source AI Product Analysis & Price Comparison System

🔍 **Cumpair** is a comprehensive AI-powered system that analyzes product images and compares prices across multiple e-commerce platforms using advanced computer vision and adaptive web scraping techniques.

## 🚀 Features

### 🖼️ AI-Powered Image Analysis
- **YOLOv8 Object Detection**: Automatically detect and identify products in images
- **EfficientNet Specification Extraction**: Extract product specifications and features
- **Smart Cropping**: Automatically crop detected products for better analysis
- **Duplicate Detection**: Hash-based image deduplication

### 🌐 Adaptive Web Scraping
- **Multi-Layer Strategy**: Direct API → HTML Parsing → Headless Browser
- **Anti-Block System**: Proxy rotation, CAPTCHA solving, fingerprint evasion
- **Platform Support**: Amazon, eBay, Walmart, Best Buy, Target, and more
- **Failure Learning**: Adaptive system that learns from blocking patterns

### 💰 Price Comparison
- **Real-time Scraping**: Fresh price data from multiple sources
- **Price History**: Track price changes over time
- **Smart Ranking**: Intelligent filtering and ranking of results
- **Statistics**: Comprehensive price analytics and trends

### 🔧 Production-Ready Architecture
- **FastAPI Backend**: High-performance async API
- **Celery Workers**: Distributed background task processing
- **PostgreSQL**: Robust data storage with relationships
- **Redis**: Caching and task queue management
- **Docker**: Containerized deployment
- **Monitoring**: Prometheus + Grafana observability

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   FastAPI   │───▶│ Celery Queue │───▶│ Image Analysis  │
│   Gateway   │    │   (Redis)    │    │   (YOLOv8)     │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                     │
       │                   ▼                     ▼
       │           ┌─────────────────┐    ┌─────────────┐
       │           │ Adaptive        │    │ PostgreSQL │
       │           │ Scraping Engine │    │ Database   │
       │           └─────────────────┘    └─────────────┘
       │                   │                     ▲
       ▼                   ▼                     │
┌─────────────┐    ┌─────────────────┐          │
│ Redis Cache │    │ Proxy Manager   │──────────┘
└─────────────┘    │ (Rota + Free)   │
                   └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- 4GB+ RAM recommended

### 1. Clone and Setup
```bash
git clone <repository-url>
cd compair
```

### 2. Environment Configuration
Create a `.env` file:
```env
# Database
DATABASE_URL=postgresql://compair:compair123@postgres:5432/compair

# Redis
REDIS_URL=redis://redis:6379

# Proxy Service
ROTA_URL=http://rota:8000

# Security
SECRET_KEY=your-super-secret-key-change-this

# File Uploads
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads

# AI Models
YOLO_MODEL_PATH=models/yolov8n.pt
EFFICIENTNET_MODEL_PATH=models/spec_extractor.h5
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8000/api/v1/health
```

### 4. Access the Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring (Grafana)**: http://localhost:3000 (admin/admin)
- **Task Monitor (Flower)**: http://localhost:5555
- **Metrics (Prometheus)**: http://localhost:9090

## 📖 API Usage

### Upload and Analyze Product Image
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@product_image.jpg" \
  -F "full_analysis=true"
```

### Get Analysis Results
```bash
curl "http://localhost:8000/api/v1/analyze/1"
```

### Compare Prices
```bash
curl "http://localhost:8000/api/v1/compare/1"
```

### Refresh Price Data
```bash
curl -X POST "http://localhost:8000/api/v1/compare/1/refresh"
```

## 🛠️ Development Setup

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn main:app --reload

# Start Celery worker (separate terminal)
celery -A app.worker worker --loglevel=info

# Start Celery flower monitoring
celery -A app.worker flower
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

## 🔧 Configuration

### Supported Platforms
- Amazon
- eBay  
- Walmart
- Best Buy
- Target
- (Easily extensible)

### AI Models
- **Object Detection**: YOLOv8n (default) - lightweight and fast
- **Specification Extraction**: EfficientNet-B0 - customizable for specific domains
- **CAPTCHA Solving**: Tesseract OCR + CNN fallback

### Scraping Strategies
1. **Direct API**: Fastest, tries to discover and use platform APIs
2. **HTML Parsing**: Standard requests-based scraping with proxy rotation
3. **Headless Browser**: Playwright-based for complex sites with JavaScript

## 📊 Monitoring & Metrics

### Prometheus Metrics
- Request counts and latencies
- Analysis success/failure rates
- Scraping performance by platform
- Active Celery tasks
- Database connection health

### Grafana Dashboards
- System overview
- API performance
- Scraping success rates
- Task queue status
- Error tracking

## 🔒 Security Features

### Anti-Detection
- User-Agent rotation
- Proxy rotation (Rota integration)
- Request timing randomization
- Browser fingerprint masking

### Data Security
- Input validation and sanitization
- File type restrictions
- Size limits
- SQL injection protection

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up --scale worker=4 -d
```

### Environment Variables (Production)
```env
DEBUG=false
DATABASE_URL=postgresql://user:pass@db:5432/compair
REDIS_URL=redis://redis:6379
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [Playwright](https://playwright.dev/) for browser automation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Rota](https://github.com/alpkeskin/rota) for proxy management

## 📧 Support

For support, please open an issue on GitHub or contact the development team.

---

**Note**: This system is designed for educational and research purposes. Please ensure compliance with the terms of service of any websites you scrape and respect rate limits and robots.txt files.