#!/bin/bash
set -e

echo "🚀 Starting Worker with Universal Package Installer"

# Copy the universal installer to the container
cp /app/universal_package_installer.py /tmp/universal_package_installer.py
chmod +x /tmp/universal_package_installer.py

# Run universal package installer for worker service
echo "� Installing packages for worker service..."
python3 /tmp/universal_package_installer.py --service worker --requirements /app/requirements.txt

# Change to app directory
cd /app

# Set environment variables
export PYTHONPATH=/app:$PYTHONPATH
export ENVIRONMENT=production

echo "🎯 Starting Celery worker..."
exec celery -A app.worker worker --loglevel=info --concurrency=2
