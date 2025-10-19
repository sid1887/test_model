#!/bin/bash

echo "=== PHASE 2: STEP 2 - BASIC ROUTE INTEGRATION ==="

# Install critical missing packages first
echo "Installing critical packages..."
pip install aiofiles==23.2.0 asyncpg==0.29.0 python-dotenv==1.0.0 uvicorn==0.24.0 fastapi==0.104.1 sqlalchemy==2.0.23 psycopg2-binary==2.9.9

# Backup previous main.py
echo "Backing up previous main.py..."
cp /app/main.py /app/main.py.phase1 || echo "No previous main.py to backup"

# Create enhanced main.py with basic database routes and CRUD operations
echo "Creating enhanced main.py with basic routes..."
cat > /app/main.py << 'MAIN_EOF'
"""
Phase 2 Step 2: Enhanced FastAPI application with basic routes and database connectivity
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json

# Database imports with try/catch for graceful degradation
try:
    import asyncpg
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Database packages not available - running in limited mode")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("SQLAlchemy not available - using basic database operations")

# Create the FastAPI app
app = FastAPI(
    title="Test Model API",
    description="Enhanced API with database connectivity and basic CRUD operations",
    version="2.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/cumpair_db")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Global database connection
db_pool = None

async def get_database_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None and DATABASE_AVAILABLE:
        try:
            # Parse database URL for asyncpg
            url_parts = DATABASE_URL.replace("postgresql://", "").split("@")
            if len(url_parts) == 2:
                user_pass, host_db = url_parts
                user, password = user_pass.split(":")
                host_port, database = host_db.split("/")
                host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
                
                db_pool = await asyncpg.create_pool(
                    user=user,
                    password=password,
                    database=database,
                    host=host,
                    port=int(port),
                    min_size=1,
                    max_size=10
                )
                print(f"Database pool created successfully")
        except Exception as e:
            print(f"Failed to create database pool: {e}")
            db_pool = None
    return db_pool

async def execute_query(query: str, *args):
    """Execute a database query safely"""
    pool = await get_database_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        async with pool.acquire() as connection:
            if args:
                result = await connection.fetch(query, *args)
            else:
                result = await connection.fetch(query)
            return [dict(row) for row in result]
    except Exception as e:
        print(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# === HEALTH AND STATUS ENDPOINTS ===

@app.get("/health")
async def health_check():
    """Legacy health check endpoint"""
    return {
        "status": "healthy",
        "message": "Web service is running",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "phase": "2.1 - Basic Routes Integration"
    }

@app.get("/api/v1/health")
async def api_health_check():
    """Standard API health check with service checks"""
    database_status = "unknown"
    
    if DATABASE_AVAILABLE:
        try:
            pool = await get_database_pool()
            if pool:
                async with pool.acquire() as connection:
                    await connection.fetchval("SELECT 1")
                database_status = "healthy"
        except Exception as e:
            database_status = f"error: {str(e)}"
    else:
        database_status = "not_available"
    
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": database_status,
            "redis": "not_checked",
            "ai_services": "not_enabled"
        },
        "features": {
            "database_connectivity": DATABASE_AVAILABLE,
            "sqlalchemy_support": SQLALCHEMY_AVAILABLE,
            "ai_features": False
        }
    }

@app.get("/api/v1/status")
async def api_status():
    """Detailed API status with feature flags"""
    return {
        "api_version": "2.1.0",
        "status": "operational",
        "phase": "Basic Routes Integration",
        "features": {
            "health_checks": True,
            "database_connectivity": DATABASE_AVAILABLE,
            "basic_crud": True,
            "data_validation": True,
            "ai_features": False,
            "file_uploads": False,
            "analysis_routes": False
        },
        "endpoints": {
            "health": ["GET /health", "GET /api/v1/health"],
            "status": ["GET /api/v1/status"],
            "database": ["GET /api/v1/db/test", "GET /api/v1/db/tables"],
            "basic": ["GET /api/v1/test", "GET /"]
        }
    }

# === BASIC ENDPOINTS ===

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Test Model API - Phase 2.1 (Basic Routes Integration)",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "/api/v1/status",
        "redoc": "/redoc",
        "features": ["health_checks", "database_connectivity", "basic_crud"]
    }

@app.get("/api/v1/test")
async def test_endpoint():
    """Enhanced test endpoint"""
    return {
        "test": "success",
        "message": "API v1 is responding correctly",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "database_available": DATABASE_AVAILABLE
    }

# === DATABASE CONNECTIVITY ROUTES ===

@app.get("/api/v1/db/test")
async def test_database():
    """Test database connectivity"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database packages not installed")
    
    try:
        result = await execute_query("SELECT NOW() as current_time, version() as db_version")
        return {
            "status": "success",
            "message": "Database connection successful",
            "database_time": result[0]["current_time"],
            "database_version": result[0]["db_version"],
            "connection_pool": "active" if db_pool else "not_created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database test failed: {str(e)}")

@app.get("/api/v1/db/tables")
async def list_database_tables():
    """List all tables in the database"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database packages not installed")
    
    try:
        query = """
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        result = await execute_query(query)
        return {
            "status": "success",
            "tables": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@app.get("/api/v1/db/table/{table_name}/info")
async def get_table_info(table_name: str):
    """Get information about a specific table"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database packages not installed")
    
    try:
        # Get column information
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = $1
        ORDER BY ordinal_position
        """
        columns = await execute_query(query, table_name)
        
        if not columns:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        count_result = await execute_query(count_query)
        
        return {
            "status": "success",
            "table_name": table_name,
            "columns": columns,
            "row_count": count_result[0]["row_count"] if count_result else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}")

# === BASIC CRUD OPERATIONS ===

@app.get("/api/v1/db/table/{table_name}/data")
async def get_table_data(table_name: str, limit: int = 10, offset: int = 0):
    """Get data from a table with pagination"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database packages not installed")
    
    try:
        # Validate table exists
        table_check = await execute_query(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = $1",
            table_name
        )
        
        if not table_check:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get data with pagination
        query = f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2"
        data = await execute_query(query, limit, offset)
        
        return {
            "status": "success",
            "table_name": table_name,
            "data": data,
            "limit": limit,
            "offset": offset,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table data: {str(e)}")

# === DATA VALIDATION ENDPOINTS ===

@app.post("/api/v1/validate/json")
async def validate_json_data(data: dict):
    """Validate JSON data structure"""
    try:
        # Basic validation
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Data must be a JSON object")
        
        validation_result = {
            "status": "success",
            "message": "JSON data is valid",
            "data_type": type(data).__name__,
            "key_count": len(data.keys()),
            "keys": list(data.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")

# === SYSTEM INFO ENDPOINTS ===

@app.get("/api/v1/system/info")
async def get_system_info():
    """Get system information"""
    return {
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.name,
        "environment_variables": {
            "DATABASE_URL": "***configured***" if os.getenv("DATABASE_URL") else "not_set",
            "PORT": os.getenv("PORT", "8000"),
            "PYTHONPATH": "***set***" if os.getenv("PYTHONPATH") else "not_set"
        },
        "features": {
            "asyncpg": DATABASE_AVAILABLE,
            "sqlalchemy": SQLALCHEMY_AVAILABLE
        },
        "timestamp": datetime.now().isoformat()
    }

# === APPLICATION LIFECYCLE ===

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print("=== PHASE 2 STEP 2 APPLICATION STARTUP ===")
    print(f"API Version: 2.1.0")
    print(f"Database Available: {DATABASE_AVAILABLE}")
    print(f"SQLAlchemy Available: {SQLALCHEMY_AVAILABLE}")
    
    if DATABASE_AVAILABLE:
        try:
            await get_database_pool()
            print("Database connection pool initialized")
        except Exception as e:
            print(f"Database initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Database pool closed")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
MAIN_EOF

echo "=== PHASE 2 STEP 2 COMPLETED ==="
echo "Enhanced main.py created with basic routes and database connectivity"
echo "New features:"
echo "  - Database connectivity test endpoints"
echo "  - Basic CRUD operations for database tables"  
echo "  - Data validation endpoints"
echo "  - System information endpoints"
echo "  - Enhanced health checks with service status"
echo "Available endpoints:"
echo "  - GET /api/v1/health (enhanced health check)"
echo "  - GET /api/v1/status (detailed status with features)"
echo "  - GET /api/v1/db/test (database connectivity test)"
echo "  - GET /api/v1/db/tables (list database tables)"
echo "  - GET /api/v1/db/table/{name}/info (table information)"
echo "  - GET /api/v1/db/table/{name}/data (table data with pagination)"
echo "  - POST /api/v1/validate/json (JSON validation)"
echo "  - GET /api/v1/system/info (system information)"
echo "=== STARTING UVICORN ==="
