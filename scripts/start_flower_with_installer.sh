#!/bin/bash

# Enhanced Flower Startup with Automatic Package Installer
echo "🌸 STARTING FLOWER WITH AUTOMATIC PACKAGE INSTALLER"
echo "=================================================="

# Function to install missing packages automatically
install_missing_package() {
    local package=$1
    echo "📦 Installing missing package: $package"
    pip install --no-cache-dir "$package" || echo "⚠️ Failed to install $package, continuing..."
}

# Pre-install known required packages for flower
echo "📦 Pre-installing common flower packages..."
pip install --no-cache-dir structlog prometheus_client flower celery || echo "⚠️ Some pre-installs failed"

# Start flower with automatic error handling
echo "🔄 Starting Celery flower with auto-recovery..."
while true; do
    echo "⏰ $(date): Starting flower..."
    
    # Try to start flower and capture errors
    celery -A app.worker flower --port=5555 --url_prefix=flower 2>&1 | while read line; do
        echo "$line"
        
        # Check for missing module errors and auto-install
        if echo "$line" | grep -q "No module named"; then
            module=$(echo "$line" | sed -n "s/.*No module named '\([^']*\)'.*/\1/p")
            if [ ! -z "$module" ]; then
                install_missing_package "$module"
                echo "🔄 Restarting flower after installing $module..."
                pkill -f "celery.*flower" || true
                sleep 2
                break
            fi
        fi
        
        # Check for command not found errors
        if echo "$line" | grep -q "command not found\|No such file"; then
            echo "📦 Installing flower command..."
            install_missing_package "flower"
            echo "🔄 Restarting flower after installing flower..."
            pkill -f "celery.*flower" || true
            sleep 2
            break
        fi
        
        # Check for other import errors
        if echo "$line" | grep -q "ModuleNotFoundError\|ImportError"; then
            echo "⚠️ Import error detected, checking for auto-install..."
        fi
    done
    
    # If we get here, flower exited - wait and retry
    echo "⚠️ Flower exited, restarting in 5 seconds..."
    sleep 5
done
