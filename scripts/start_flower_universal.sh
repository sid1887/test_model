#!/bin/bash
set -e

echo "Starting Flower with Universal Package Installer"

# Copy the universal installer to the container
cp /app/universal_package_installer.py /tmp/universal_package_installer.py
chmod +x /tmp/universal_package_installer.py

# Run universal package installer for flower service
echo "Installing packages for flower service..."
python3 /tmp/universal_package_installer.py --service flower --requirements /app/requirements.txt

# Change to app directory
cd /app

# Set environment variables
export PYTHONPATH=/app:$PYTHONPATH
export ENVIRONMENT=production

echo "Starting Celery Flower..."
exec celery -A app.worker flower --port=5555 --url_prefix=flower
