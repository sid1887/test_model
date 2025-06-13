#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}▶️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Allow passing flags like --no-scraper, --no-monitor, --no-frontend, --no-worker
INCLUDE_SCRAPER=true
INCLUDE_MONITOR=true
INCLUDE_FRONTEND=true
INCLUDE_WORKER=true

# Parse flags
for arg in "$@"; do
  case $arg in
    --no-scraper) INCLUDE_SCRAPER=false ;;
    --no-monitor) INCLUDE_MONITOR=false ;;
    --no-frontend) INCLUDE_FRONTEND=false ;;
    --no-worker) INCLUDE_WORKER=false ;;
    --minimal) 
        INCLUDE_SCRAPER=false
        INCLUDE_MONITOR=false
        INCLUDE_FRONTEND=false
        INCLUDE_WORKER=false
        ;;
    --full)
        INCLUDE_SCRAPER=true
        INCLUDE_MONITOR=true
        INCLUDE_FRONTEND=true
        INCLUDE_WORKER=true
        ;;
  esac
done

# Build list of profiles
PROFILES=(core)
$INCLUDE_WORKER && PROFILES+=("worker")
$INCLUDE_SCRAPER && PROFILES+=("scraper")
$INCLUDE_FRONTEND && PROFILES+=("frontend")
$INCLUDE_MONITOR && PROFILES+=("monitor")

log_info "Starting Cumpair services with profiles: ${PROFILES[*]}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Run compose with selected profiles
log_info "Building and starting containers..."
docker-compose $(printf " --profile %s" "${PROFILES[@]}") up -d --build

# Wait for core services to be healthy
log_info "Waiting for core services to be ready..."

# Wait for PostgreSQL
echo -n "⏳ PostgreSQL: "
MAX_ATTEMPTS=30
ATTEMPT=0
until docker exec compair_postgres pg_isready -U compair > /dev/null 2>&1; do
  sleep 2
  ATTEMPT=$((ATTEMPT + 1))
  if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    log_error "PostgreSQL failed to start within $((MAX_ATTEMPTS * 2)) seconds"
    exit 1
  fi
  echo -n "."
done
log_success "PostgreSQL is ready!"

# Wait for Redis
echo -n "⏳ Redis: "
ATTEMPT=0
until docker exec compair_redis redis-cli ping > /dev/null 2>&1; do
  sleep 2
  ATTEMPT=$((ATTEMPT + 1))
  if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    log_error "Redis failed to start within $((MAX_ATTEMPTS * 2)) seconds"
    exit 1
  fi
  echo -n "."
done
log_success "Redis is ready!"

# Wait for main web service
if docker-compose ps | grep -q "compair_web"; then
    echo -n "⏳ FastAPI Web Service: "
    ATTEMPT=0
    until docker exec compair_web curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; do
      sleep 3
      ATTEMPT=$((ATTEMPT + 1))
      if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        log_warning "FastAPI web service health check failed - continuing anyway"
        break
      fi
      echo -n "."
    done
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        log_success "FastAPI web service is ready!"
    fi
fi

# Run database migrations
log_info "Applying database migrations..."
if docker exec compair_web alembic upgrade head; then
    log_success "Database migrations completed!"
else
    log_warning "Database migrations may have failed - check logs"
fi

# Check scraper service
if $INCLUDE_SCRAPER && docker-compose ps | grep -q "compair_scraper"; then
    echo -n "⏳ Scraper Service: "
    ATTEMPT=0
    until docker exec compair_scraper curl -f http://localhost:3001/health > /dev/null 2>&1; do
      sleep 2
      ATTEMPT=$((ATTEMPT + 1))
      if [ $ATTEMPT -ge 15 ]; then
        log_warning "Scraper service health check failed"
        break
      fi
      echo -n "."
    done
    if [ $ATTEMPT -lt 15 ]; then
        log_success "Scraper service is ready!"
    fi
fi

# Display service status
echo ""
log_success "🎉 Cumpair services are up and running!"
echo ""
log_info "📋 Service Status:"

# Core services
echo "🔗 Core Services:"
echo "   🗄️  PostgreSQL: http://localhost:5432"
echo "   📦 Redis: http://localhost:6379"
echo "   🌐 FastAPI Web: http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"

# Optional services
if $INCLUDE_WORKER; then
    echo "⚙️  Background Services:"
    echo "   🔄 Celery Worker: Running"
    if docker-compose ps | grep -q "compair_flower"; then
        echo "   📊 Flower Monitor: http://localhost:5555"
    fi
fi

if $INCLUDE_SCRAPER; then
    echo "🕷️  Scraping Services:"
    echo "   🌐 Node.js Scraper: http://localhost:3001"
fi

if $INCLUDE_FRONTEND; then
    echo "🎨 Frontend Services:"
    echo "   💻 Next.js App: http://localhost:3002"
fi

if $INCLUDE_MONITOR; then
    echo "📊 Monitoring Services:"
    echo "   📈 Prometheus: http://localhost:9090"
    echo "   📉 Grafana: http://localhost:3003 (admin/admin)"
fi

echo ""
log_info "💡 Usage Tips:"
echo "   make logs     - View all service logs"
echo "   make stop     - Stop all services"
echo "   make restart  - Restart all services"
echo ""
log_info "🚀 Ready to use! Visit http://localhost:8000 to get started."
