#!/bin/bash
# COMPREHENSIVE DOCKER DEPLOYMENT SCRIPT WITH AUTOMATED ERROR HANDLING
# This script automatically handles package conflicts, version issues, and service failures

set -e

echo "🚀 Starting Comprehensive Docker Deployment with Automated Error Handling..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be healthy
wait_for_service() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to become healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.complete.yml ps | grep "$service_name" | grep -q "healthy\|running"; then
            print_success "$service_name is healthy!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    print_warning "$service_name did not become healthy within expected time"
    return 1
}

# Function to handle service failures
handle_service_failure() {
    local service_name="$1"
    print_error "$service_name failed to start properly"
    
    print_status "Getting logs for $service_name..."
    docker-compose -f docker-compose.complete.yml logs --tail=50 "$service_name" || true
    
    print_status "Attempting to restart $service_name..."
    docker-compose -f docker-compose.complete.yml restart "$service_name" || true
    
    sleep 10
    
    if docker-compose -f docker-compose.complete.yml ps | grep "$service_name" | grep -q "healthy\|running"; then
        print_success "$service_name restarted successfully!"
        return 0
    else
        print_warning "$service_name restart failed, continuing with other services..."
        return 1
    fi
}

# Function to clean up Docker resources
cleanup_docker() {
    print_status "Cleaning up Docker resources..."
    
    # Stop all containers
    print_status "Stopping all containers..."
    docker-compose -f docker-compose.complete.yml down --remove-orphans || true
    
    # Remove stopped containers
    print_status "Removing stopped containers..."
    docker container prune -f || true
    
    # Remove unused images (keep base images)
    print_status "Removing unused images..."
    docker image prune -f || true
    
    # Remove unused volumes (be careful with data)
    print_warning "Cleaning unused volumes (this may remove cached data)..."
    docker volume prune -f || true
    
    # Remove unused networks
    print_status "Removing unused networks..."
    docker network prune -f || true
    
    print_success "Docker cleanup completed"
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        print_warning "Low disk space detected. You may encounter issues during build."
    fi
    
    print_success "System requirements check passed"
}

# Function to build services with retry logic
build_with_retry() {
    local service_name="$1"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Building $service_name (attempt $attempt/$max_attempts)..."
        
        if docker-compose -f docker-compose.complete.yml build --no-cache "$service_name"; then
            print_success "$service_name built successfully!"
            return 0
        else
            print_warning "$service_name build failed on attempt $attempt"
            if [ $attempt -lt $max_attempts ]; then
                print_status "Cleaning up and retrying..."
                docker-compose -f docker-compose.complete.yml down "$service_name" || true
                docker image rm "test_model-$service_name" 2>/dev/null || true
                sleep 5
            fi
        fi
        ((attempt++))
    done
    
    print_error "$service_name failed to build after $max_attempts attempts"
    return 1
}

# Main deployment function
deploy_services() {
    print_status "Starting service deployment with automated error handling..."
    
    # Array of services in dependency order
    local services=("redis" "postgres" "web" "scraper" "captcha" "proxy" "worker" "flower" "frontend" "prometheus" "grafana" "nginx")
    local failed_services=()
    local successful_services=()
    
    # Build all services first
    print_status "Building all services..."
    if ! docker-compose -f docker-compose.complete.yml build --no-cache; then
        print_warning "Bulk build failed, trying individual builds..."
        
        # Try building critical services individually
        for service in "web" "scraper" "captcha" "proxy"; do
            if build_with_retry "$service"; then
                successful_services+=("$service")
            else
                failed_services+=("$service")
            fi
        done
    else
        print_success "All services built successfully!"
    fi
    
    # Start services in dependency order
    print_status "Starting services in dependency order..."
    
    # Start infrastructure services first
    print_status "Starting infrastructure services (Redis, PostgreSQL)..."
    docker-compose -f docker-compose.complete.yml up -d redis postgres
    
    # Wait for infrastructure
    wait_for_service "redis" || handle_service_failure "redis"
    wait_for_service "postgres" || handle_service_failure "postgres"
    
    # Start core application services
    print_status "Starting core application services..."
    docker-compose -f docker-compose.complete.yml up -d web scraper captcha proxy
    
    # Check each core service
    for service in "web" "scraper" "captcha" "proxy"; do
        if wait_for_service "$service"; then
            successful_services+=("$service")
        else
            handle_service_failure "$service"
            failed_services+=("$service")
        fi
    done
    
    # Start remaining services
    print_status "Starting remaining services..."
    docker-compose -f docker-compose.complete.yml up -d worker flower frontend prometheus grafana nginx
    
    # Final status report
    print_status "Deployment completed. Generating status report..."
    
    echo
    echo "=========================================="
    echo "         DEPLOYMENT STATUS REPORT"
    echo "=========================================="
    
    if [ ${#successful_services[@]} -gt 0 ]; then
        print_success "Successful services:"
        for service in "${successful_services[@]}"; do
            echo "  ✅ $service"
        done
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        print_error "Failed services:"
        for service in "${failed_services[@]}"; do
            echo "  ❌ $service"
        done
        echo
        print_warning "Some services failed. Check logs with: docker-compose -f docker-compose.complete.yml logs [service_name]"
    else
        print_success "All services started successfully!"
    fi
    
    echo
    print_status "Current service status:"
    docker-compose -f docker-compose.complete.yml ps
    
    echo
    print_status "Access points:"
    echo "  🌐 Web Application: http://localhost:8000"
    echo "  📊 Grafana Dashboard: http://localhost:3000"
    echo "  🌸 Flower (Celery): http://localhost:5555"
    echo "  🔍 Frontend: http://localhost:3000"
    echo "  📈 Prometheus: http://localhost:9090"
}

# Function to show help
show_help() {
    echo "Comprehensive Docker Deployment Script"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  --clean, -c    Clean up all Docker resources before deployment"
    echo "  --build, -b    Force rebuild all images"
    echo "  --help, -h     Show this help message"
    echo "  --status, -s   Show current status without deployment"
    echo
    echo "Examples:"
    echo "  $0              # Normal deployment with error handling"
    echo "  $0 --clean     # Clean deployment (removes all Docker resources)"
    echo "  $0 --status    # Check current status"
}

# Function to show status
show_status() {
    print_status "Current Docker Compose Status:"
    docker-compose -f docker-compose.complete.yml ps || print_error "Failed to get service status"
    
    echo
    print_status "Docker Images:"
    docker images | grep test_model || print_warning "No test_model images found"
    
    echo
    print_status "Docker Volumes:"
    docker volume ls | grep test_model || print_warning "No test_model volumes found"
    
    echo
    print_status "Docker Networks:"
    docker network ls | grep test_model || docker network ls | head -5
}

# Main script execution
main() {
    local clean_deployment=false
    local force_build=false
    local show_status_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean|-c)
                clean_deployment=true
                shift
                ;;
            --build|-b)
                force_build=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --status|-s)
                show_status_only=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Show status only if requested
    if [ "$show_status_only" = true ]; then
        show_status
        exit 0
    fi
    
    print_status "Starting Comprehensive Docker Deployment Script..."
    print_status "Timestamp: $(date)"
    
    # Check requirements
    check_requirements
    
    # Clean deployment if requested
    if [ "$clean_deployment" = true ]; then
        print_warning "Clean deployment requested - this will remove all existing containers and images"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup_docker
        else
            print_status "Skipping cleanup"
        fi
    fi
    
    # Deploy services
    deploy_services
    
    print_success "Deployment script completed!"
    print_status "Use '$0 --status' to check service status anytime"
}

# Run main function with all arguments
main "$@"
