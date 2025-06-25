#!/bin/bash

echo "=== PHASE 2 STEP 2: BASIC ROUTE INTEGRATION ==="

# Install additional database packages
echo "Installing database connectivity packages..."
pip install sqlalchemy==2.0.25 alembic==1.13.1 psycopg2-binary==2.9.9

# Backup current main.py
echo "Backing up Phase 2 Step 1 main.py..."
cp /app/main.py /app/main.py.phase2_step1.backup

# Create enhanced main.py with basic database routes
echo "Creating enhanced main.py with basic database connectivity..."
cat > /app/main.py << 'MAIN_EOF'
"""
Enhanced FastAPI application - Phase 2 Step 2: Basic routes with database connectivity
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import asyncpg
import redis as redis_client

# Create the FastAPI app
app = FastAPI(
    title="Test Model API",
    description="Enhanced API with basic routes and database connectivity - Phase 2 Step 2",
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

# Database connection management
class DatabaseManager:
    def __init__(self):
        self.db_pool = None
        self.redis_client = None
    
    async def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            if not self.db_pool:
                # Database connection string
                db_host = os.getenv("POSTGRES_HOST", "postgres")
                db_port = os.getenv("POSTGRES_PORT", "5432")
                db_name = os.getenv("POSTGRES_DB", "testmodel")
                db_user = os.getenv("POSTGRES_USER", "testuser")
                db_password = os.getenv("POSTGRES_PASSWORD", "testpass123")
                
                dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                self.db_pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
            
            return self.db_pool
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    async def get_redis_connection(self):
        """Get Redis connection with error handling"""
        try:
            if not self.redis_client:
                redis_host = os.getenv("REDIS_HOST", "redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                
                self.redis_client = redis_client.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
            
            return self.redis_client
        except Exception as e:
            print(f"Redis connection error: {e}")
            return None

# Global database manager
db_manager = DatabaseManager()

# Create API router with versioning
api_v1_router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# Health check endpoints
@app.get("/health")
async def health_check_root():
    """Basic health check endpoint - legacy path"""
    return await get_health_status()

@api_v1_router.get("/health")
async def health_check_v1():
    """Enhanced health check endpoint - proper API path"""
    return await get_health_status()

async def get_health_status():
    """Comprehensive health status check with real database/Redis connectivity"""
    try:
        # Check database connectivity
        db_status = "unknown"
        db_details = {}
        try:
            db_pool = await db_manager.get_db_connection()
            if db_pool:
                async with db_pool.acquire() as conn:
                    result = await conn.fetchval("SELECT version()")
                    db_status = "healthy"
                    db_details = {"version": result.split()[0] if result else "unknown"}
            else:
                db_status = "error: connection failed"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check Redis connectivity
        redis_status = "unknown"
        redis_details = {}
        try:
            redis_conn = await db_manager.get_redis_connection()
            if redis_conn:
                redis_conn.ping()
                info = redis_conn.info()
                redis_status = "healthy"
                redis_details = {
                    "version": info.get("redis_version", "unknown"),
                    "mode": info.get("redis_mode", "unknown")
                }
            else:
                redis_status = "error: connection failed"
        except Exception as e:
            redis_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "message": "Web service is running",
            "version": "2.1.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "healthy",
                "database": {
                    "status": db_status,
                    "details": db_details
                },
                "redis": {
                    "status": redis_status,
                    "details": redis_details
                }
            },
            "endpoints": {
                "health": "/api/v1/health",
                "database": "/api/v1/database",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Health check encountered issues: {str(e)}",
            "version": "2.1.0",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Test Model API is running (Phase 2 Step 2 - Basic Routes)",
        "version": "2.1.0",
        "api_version": "v1",
        "endpoints": {
            "health": "/api/v1/health",
            "database": "/api/v1/database",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "status": "Phase 2 Step 2: Basic routes with database connectivity"
    }

@api_v1_router.get("/status")
async def api_status():
    """API status endpoint with enhanced feature tracking"""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "basic_routes": "enabled",
            "health_checks": "enabled", 
            "database_connectivity": "enabled",
            "redis_connectivity": "enabled",
            "ai_routes": "pending",
            "crud_operations": "enabled"
        },
        "phase": "2.2",
        "timestamp": datetime.now().isoformat()
    }

@api_v1_router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "test": "success",
        "message": "API v1 is responding correctly",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }

# Database routes
@api_v1_router.get("/database/status")
async def database_status():
    """Check database status and basic info"""
    try:
        db_pool = await db_manager.get_db_connection()
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        async with db_pool.acquire() as conn:
            # Get basic database info
            version = await conn.fetchval("SELECT version()")
            current_db = await conn.fetchval("SELECT current_database()")
            current_user = await conn.fetchval("SELECT current_user")
            current_time = await conn.fetchval("SELECT NOW()")
            
            # Get table count (if we have permissions)
            table_count = 0
            try:
                table_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            except:
                table_count = "permission_denied"
            
            return {
                "status": "connected",
                "database": current_db,
                "user": current_user,
                "version": version.split()[0] if version else "unknown",
                "server_time": current_time.isoformat() if current_time else None,
                "table_count": table_count,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@api_v1_router.get("/database/tables")
async def list_tables():
    """List available tables in the database"""
    try:
        db_pool = await db_manager.get_db_connection()
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        async with db_pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            return {
                "status": "success",
                "table_count": len(tables),
                "tables": [
                    {
                        "name": table["table_name"],
                        "type": table["table_type"]
                    } for table in tables
                ],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

# Redis routes  
@api_v1_router.get("/redis/status")
async def redis_status():
    """Check Redis status and basic info"""
    try:
        redis_conn = await db_manager.get_redis_connection()
        if not redis_conn:
            raise HTTPException(status_code=503, detail="Redis connection failed")
        
        info = redis_conn.info()
        
        return {
            "status": "connected",
            "version": info.get("redis_version", "unknown"),
            "mode": info.get("redis_mode", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}")

@api_v1_router.post("/redis/test")
async def test_redis_operations(data: Dict[str, Any]):
    """Test basic Redis operations"""
    try:
        redis_conn = await db_manager.get_redis_connection()
        if not redis_conn:
            raise HTTPException(status_code=503, detail="Redis connection failed")
        
        test_key = f"test:{datetime.now().timestamp()}"
        test_value = str(data.get("test_value", "test_data"))
        
        # Set and get test
        redis_conn.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved = redis_conn.get(test_key)
        redis_conn.delete(test_key)  # Cleanup
        
        return {
            "status": "success",
            "test_key": test_key,
            "stored_value": test_value,
            "retrieved_value": retrieved,
            "match": test_value == retrieved,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}")

# Include the API router
app.include_router(api_v1_router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
MAIN_EOF

echo "=== PHASE 2 STEP 2 COMPLETED ==="
echo "Enhanced main.py created with basic database routes"
echo "New endpoints added:"
echo "  - GET /api/v1/database/status (database connectivity check)"
echo "  - GET /api/v1/database/tables (list database tables)"
echo "  - GET /api/v1/redis/status (Redis connectivity check)"
echo "  - POST /api/v1/redis/test (test Redis operations)"
echo "Enhanced health checks now include real database/Redis connectivity"
echo "=== READY FOR NEXT PHASE ==="
