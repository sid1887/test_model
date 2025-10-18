#!/bin/bash
# Quick start script for Cumpair development environment

set -e

echo "🚀 Starting Cumpair Development Environment"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build images
echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.dev.yml build

# Start services
echo ""
echo "🚢 Starting services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.dev.yml ps

# Run migrations
echo ""
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.dev.yml exec -T web alembic upgrade head || echo "⚠️  Migrations not configured or failed"

# Show access URLs
echo ""
echo "✅ Cumpair is ready!"
echo "===================="
echo "📍 Access points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/api/v1/health"
echo "   - Scraper: http://localhost:3001"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.dev.yml down"
echo "   - Restart service: docker-compose -f docker-compose.dev.yml restart [service]"
echo ""
echo "🎉 Happy coding!"
