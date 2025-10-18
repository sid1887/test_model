#!/bin/bash
set -e

echo "$(date +"%Y-%m-%d %H:%M:%S") - STARTUP: Manual startup procedure initiated..."

# Install critical packages directly
echo "$(date +"%Y-%m-%d %H:%M:%S") - STARTUP: Installing critical packages directly..."
pip install asyncpg aiofiles python-dotenv

# Start the application
echo "$(date +"%Y-%m-%d %H:%M:%S") - STARTUP: Starting web service..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
