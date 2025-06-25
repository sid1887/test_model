#!/bin/bash

# Stop the web container first
docker stop test_model-web-1

# Create a minimal fix for main.py to disable problematic AI routes temporarily
cat > /tmp/minimal_fix.py << 'EOF'
# Fix main.py by commenting out problematic imports
try:
    with open('/app/main.py', 'r') as f:
        content = f.read()
    
    # Comment out the problematic AI imports
    content = content.replace(
        'from app.api.routes import analysis, analysis_new, comparison, health, price_comparison',
        'from app.api.routes import health  # analysis, analysis_new, comparison, price_comparison'
    )
    
    # Comment out the problematic route includes
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if 'app.include_router(analysis.router' in line or \
           'app.include_router(analysis_new.router' in line or \
           'app.include_router(comparison.router' in line or \
           'app.include_router(price_comparison.router' in line:
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open('/app/main.py', 'w') as f:
        f.write(content)
    print("Fixed main.py file")
except Exception as e:
    print(f"Error fixing main.py: {e}")

# Create a simple health route in case it doesn't exist
try:
    import os
    if not os.path.exists('/app/app/api/routes/health.py'):
        health_content = '''"""
Health check routes
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])

class HealthResponse(BaseModel):
    status: str
    message: str

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Web service is running"
    )
'''
        with open('/app/app/api/routes/health.py', 'w') as f:
            f.write(health_content)
        print("Created basic health.py file")
except Exception as e:
    print(f"Error creating health.py: {e}")
EOF

# Run the minimal fix
python /tmp/minimal_fix.py

# Install critical packages
pip install asyncpg==0.29.0 aiofiles==23.2.0 python-dotenv==1.0.0

# Clean up
rm /tmp/minimal_fix.py
