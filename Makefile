# Cumpair - AI Product Analysis & Price Comparison System
# Makefile for easy service management

# Detect the operating system
ifeq ($(OS),Windows_NT)
    SHELL := powersh	@echo "   Scraper:      http://localhost:3001"ll.exe
    START_SCRIPT := .\scripts\start-all.ps1
    .SHELLFLAGS := -Command
else
    SHELL := /bin/bash
    START_SCRIPT := ./scripts/start-all.sh
endif

.PHONY: start stop logs restart status clean build test help

# Default target
all: help

## Development Commands

start: ## Start all services (core + worker + scraper + frontend)
ifeq ($(OS),Windows_NT)
	@Write-Host "Starting all Cumpair services..." -ForegroundColor Green
else
	@echo "🚀 Starting all Cumpair services..."
endif
	$(START_SCRIPT)

start-minimal: ## Start only core services (PostgreSQL, Redis, FastAPI)
ifeq ($(OS),Windows_NT)
	@Write-Host "Starting minimal Cumpair services (core only)..." -ForegroundColor Green
else
	@echo "🚀 Starting minimal Cumpair services (core only)..."
endif
ifeq ($(OS),Windows_NT)
	$(START_SCRIPT) -Minimal
else
	$(START_SCRIPT) --minimal
endif

start-core: ## Start core services only (alias for start-minimal)
	@$(MAKE) start-minimal

start-no-scraper: ## Start all services except scraper
ifeq ($(OS),Windows_NT)
	@Write-Host "Starting Cumpair services (no scraper)..." -ForegroundColor Green
	$(START_SCRIPT) -NoScraper
else
	@echo "🚀 Starting Cumpair services (no scraper)..."
	$(START_SCRIPT) --no-scraper
endif

start-no-monitor: ## Start all services except monitoring
ifeq ($(OS),Windows_NT)
	@Write-Host "Starting Cumpair services (no monitoring)..." -ForegroundColor Green
	$(START_SCRIPT) -NoMonitor
else
	@echo "🚀 Starting Cumpair services (no monitoring)..."
	$(START_SCRIPT) --no-monitor
endif

## Service Management

stop: ## Stop all services
ifeq ($(OS),Windows_NT)
	@Write-Host "Stopping all services..." -ForegroundColor Yellow
else
	@echo "🛑 Stopping all services..."
endif
	docker-compose down

restart: stop start ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

status: ## Show status of all services
ifeq ($(OS),Windows_NT)
	@Write-Host "Service Status:" -ForegroundColor Cyan
else
	@echo "📊 Service Status:"
endif
	docker-compose ps

health: ## Check health of all running services
ifeq ($(OS),Windows_NT)
	@Write-Host "Health Check:" -ForegroundColor Cyan
else
	@echo "🏥 Health Check:"
endif
	@docker ps --format "table {{.Names}}\t{{.Status}}" --filter "name=compair"

## Development Utilities

build: ## Build all Docker images
ifeq ($(OS),Windows_NT)
	@Write-Host "Building Docker images..." -ForegroundColor Green
else
	@echo "🔨 Building Docker images..."
endif
	docker-compose build

clean: ## Clean up Docker resources
ifeq ($(OS),Windows_NT)
	@Write-Host "Cleaning up Docker resources..." -ForegroundColor Yellow
else
	@echo "🧹 Cleaning up Docker resources..."
endif
	docker system prune -f

test: ## Run integration tests
ifeq ($(OS),Windows_NT)
	@Write-Host "Running integration tests..." -ForegroundColor Green
	pwsh -ExecutionPolicy Bypass -File ".\scripts\test-setup.ps1" -VerboseOutput
else
	@echo "🧪 Running integration tests..."
	./scripts/test-setup.sh
endif

## Quick Actions

dev: start-minimal ## Start development environment
ifeq ($(OS),Windows_NT)
	@Write-Host "Development environment ready!" -ForegroundColor Green
else
	@echo "💻 Development environment ready!"
endif

## Help

help: ## Show this help message
ifeq ($(OS),Windows_NT)
	@Write-Host "Cumpair - AI Product Analysis and Price Comparison System" -ForegroundColor Cyan
	@Write-Host ""
	@Write-Host "Available commands:" -ForegroundColor Yellow
	@Write-Host ""
	@Write-Host "Command              Description" -ForegroundColor Cyan
	@Write-Host "start                Start all services"
	@Write-Host "start-minimal        Start only core services"
	@Write-Host "start-core           Start core services only (alias)"
	@Write-Host "start-no-scraper     Start all services except scraper"
	@Write-Host "start-no-monitor     Start all services except monitoring"
	@Write-Host "stop                 Stop all services"
	@Write-Host "restart              Restart all services"
	@Write-Host "logs                 View service logs"
	@Write-Host "status               Show service status"
	@Write-Host "health               Check service health"
	@Write-Host "clean                Clean up Docker resources"
	@Write-Host "build                Build all Docker images"
	@Write-Host "test                 Run integration tests"
	@Write-Host "dev                  Start development environment"
	@Write-Host ""
	@Write-Host "Service URLs (when running):" -ForegroundColor Green
	@Write-Host "   Main App:     http://localhost:8000"
	@Write-Host "   API Docs:     http://localhost:8000/docs"
	@Write-Host "   Scraper:      http://localhost:3001"
	@Write-Host "   Frontend:     http://localhost:3001"
	@Write-Host "   Flower:       http://localhost:5555"
	@Write-Host "   Grafana:      http://localhost:3002"
	@Write-Host "   Prometheus:   http://localhost:9090"
	@Write-Host ""
	@Write-Host "Quick Examples:" -ForegroundColor Blue
	@Write-Host "   make start-minimal      # Start only core services"
	@Write-Host "   make start              # Start all services"
	@Write-Host "   make logs               # View all logs"
	@Write-Host "   make stop               # Stop everything"
	@Write-Host "   make test               # Run integration tests"
else
	@echo "Cumpair - AI Product Analysis and Price Comparison System"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m%-20s\033[0m %s\n", "Command", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "\033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "Service URLs (when running):"
	@echo "   Main App:     http://localhost:8000"
	@echo "   API Docs:     http://localhost:8000/docs"
	@echo "   Scraper:      http://localhost:3001"
	@echo "   Frontend:     http://localhost:3001"
	@echo "   Flower:       http://localhost:5555"
	@echo "   Grafana:      http://localhost:3002"
	@echo "   Prometheus:   http://localhost:9090"
endif
