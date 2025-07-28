#!/bin/bash
set -e

echo "Starting Web Service with Universal Package Installer"

# Copy the universal installer to the container
cp /app/universal_package_installer.py /tmp/universal_package_installer.py
chmod +x /tmp/universal_package_installer.py

# Copy products.py to ensure it's available
if [ -f "/app/products.py" ]; then
    echo "Copying products.py to API routes..."
    mkdir -p /app/app/api/routes/
    cp /app/products.py /app/app/api/routes/products.py
    echo "products.py copied successfully"
fi

# Run universal package installer for web service
echo "Installing packages for web service..."
python3 /tmp/universal_package_installer.py --service web --requirements /app/requirements.txt

# Apply patches if they exist
if [ -f "/app/fix_proxymanager_complete.sh" ]; then
    echo "Applying ProxyManager patch..."
    chmod +x /app/fix_proxymanager_complete.sh
    /app/fix_proxymanager_complete.sh
fi

if [ -f "/app/fix_ai_models_syntax.sh" ]; then
    echo "Applying AI models syntax patch..."
    chmod +x /app/fix_ai_models_syntax.sh
    /app/fix_ai_models_syntax.sh
fi

# Change to app directory
cd /app

# Set environment variables
export PYTHONPATH=/app:$PYTHONPATH
export ENVIRONMENT=production

echo "Starting FastAPI web server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
