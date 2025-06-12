#!/bin/bash
# Health check script for Cumpair Docker containers

check_database() {
    echo "Checking Cumpair database connection..."
    if pg_isready -h postgres -p 5432 -U compair; then
        echo "PostgreSQL is healthy"
        return 0
    else
        echo "PostgreSQL is not responding"
        return 1
    fi
}

check_redis() {
    echo "Checking Redis connection..."
    if redis-cli -h redis -p 6379 ping | grep -q PONG; then
        echo "Redis is healthy"
        return 0
    else
        echo "Redis is not responding"
        return 1
    fi
}

check_cumpair_web() {
    echo "Checking Cumpair web application..."
    if curl -f -s http://web:8000/health > /dev/null; then
        echo "Cumpair web application is healthy"
        return 0
    else
        echo "Cumpair web application is not responding"
        return 1
    fi
}

check_celery_worker() {
    echo "Checking Celery worker..."
    if docker ps | grep -q "cumpair.*worker"; then
        echo "Celery worker is running"
        return 0
    else
        echo "Celery worker not found (may not be enabled)"
        return 0  # Non-critical
    fi
}

# Main health check
main() {
    echo "Cumpair Docker Environment Health Check"
    echo "=========================================="
    
    local exit_code=0
    
    check_database || exit_code=1
    check_redis || exit_code=1
    check_cumpair_web || exit_code=1
    check_celery_worker
    
    if [ $exit_code -eq 0 ]; then
        echo "All critical Cumpair services are healthy"
    else
        echo "Some critical Cumpair services are unhealthy"
    fi
    
    exit $exit_code
}

main "$@"
