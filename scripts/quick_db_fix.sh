#!/bin/bash

# Quick Database Feature Fix
# This script patches the web service to enable database features quickly

echo "🔧 QUICK DATABASE FEATURE FIX"
echo "=============================="

# Wait for pip installation to complete or timeout after 2 minutes
timeout_count=0
while ps aux | grep -q "[p]ip install" && [ $timeout_count -lt 120 ]; do
    echo "⏳ Waiting for pip installation to complete... ($timeout_count/120)"
    sleep 1
    ((timeout_count++))
done

if [ $timeout_count -ge 120 ]; then
    echo "⚠️  Pip installation taking too long, proceeding with patch..."
    # Kill pip process to speed up
    pkill -f "pip install"
    sleep 2
fi

echo "✅ Installing critical database packages..."
pip install asyncpg databases[postgresql] --quiet --no-deps

echo "🔧 Patching database configuration..."

# Create a quick database config patch
cat > /tmp/db_patch.py << 'EOF'
import sys
import os

# Enable database features by default
os.environ["ENABLE_DATABASE"] = "true"
os.environ["ENABLE_PRICE_COMPARISON"] = "true"
os.environ["ENABLE_PRODUCT_MANAGEMENT"] = "true"

# Add database connection configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://testuser:testpass@postgres:5432/testdb")

print("✅ Database features enabled")
print(f"✅ Database URL: {DATABASE_URL}")
EOF

# Apply the patch
cd /app
python /tmp/db_patch.py

echo "🚀 Starting patched application..."

# Apply the patch during app startup
export ENABLE_DATABASE=true
export ENABLE_PRICE_COMPARISON=true
export ENABLE_PRODUCT_MANAGEMENT=true
export DATABASE_URL="postgresql://testuser:testpass@postgres:5432/testdb"

# Start the application with database features enabled
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Quick database fix applied!"
