#!/bin/bash
# Robust startup script for the application

echo "🚀 Starting Cumpair Application..."

# Step 1: Apply all fixes
echo "🔧 Applying fixes..."
python /app/fix_all_issues.py

# Step 2: Run health check
echo "🏥 Running health check..."
python /app/simple_health_check.py

# Step 3: Start the application
echo "🌟 Starting FastAPI application..."
exec python main.py