"""
Geolocation & Region Management Service
Complex region detection, regional data variants, dynamic pricing
Port: 8012
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from fastapi import FastAPI, HTTPException, Header, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncpg
from redis import asyncio as aioredis
import httpx
from geopy.geocoders import Nominatim
import geoip2.database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Geolocation & Region Management",
    description="Complex region detection, regional data variants, dynamic pricing",
    version="1.0.0"
)

# Configuration
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "admin",
    "password": "password",
    "database": "productdb"
}

REDIS_URL = "redis://redis:6379/4"
GEOIP_DB = os.getenv("GEOIP_DB", "/data/GeoLite2-City.mmdb")

# ============================================================================
# DATA MODELS
# ============================================================================

class CurrencyType(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    INR = "INR"
    CNY = "CNY"

class RegionType(str, Enum):
    """Region types"""
    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    CONTINENT = "continent"

class UserLocation(BaseModel):
    """User location from IP"""
    ip_address: str
    country: str
    country_code: str
    city: str
    region: str
    latitude: float
    longitude: float
    timezone: str

class Region(BaseModel):
    """Region information"""
    id: str
    name: str
    region_type: RegionType
    country_code: str
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    currency: CurrencyType
    language: str
    tax_rate: float
    shipping_cost: float
    enabled: bool

class RegionalProduct(BaseModel):
    """Product in specific region"""
    product_id: str
    region_id: str
    title: str
    price: float
    currency: str
    local_title: Optional[str] = None
    description: str
    availability: str
    stock_level: int
    fulfillment_center: Optional[str] = None

class RegionalPricing(BaseModel):
    """Regional pricing for product"""
    product_id: str
    region_id: str
    base_price: float
    regional_price: float
    currency: str
    markup_percentage: float
    effective_date: str
    expiry_date: Optional[str] = None

class UserRegionContext(BaseModel):
    """User's region context"""
    user_id: str
    detected_region_id: str
    detected_location: UserLocation
    primary_region: Region
    preferred_currency: str
    language: str
    tax_applicable: bool

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def get_db_pool():
    """Get database connection pool"""
    return await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)

async def get_redis_client():
    """Get Redis client"""
    return await aioredis.from_url(REDIS_URL)

# ============================================================================
# GEOLOCATION DETECTION
# ============================================================================

@app.post("/location/detect")
async def detect_location(ip_address: str = Body(...)):
    """
    Detect user location from IP address

    Returns: Country, city, region, coordinates, timezone
    """
    try:
        # Check cache
        redis = await get_redis_client()
        cached = await redis.get(f"location:{ip_address}")
        if cached:
            logger.info(f"📍 Location cached: {ip_address}")
            await redis.close()
            return json.loads(cached)

        await redis.close()

        # Detect via GeoIP2
        location = _detect_geoip(ip_address)

        # Get timezone
        timezone = _get_timezone(location['latitude'], location['longitude'])
        location['timezone'] = timezone

        # Cache for 24 hours
        redis = await get_redis_client()
        await redis.setex(
            f"location:{ip_address}",
            86400,
            json.dumps(location)
        )
        await redis.close()

        logger.info(f"✅ Location detected: {ip_address} → {location['city']}, {location['country']}")

        return location

    except Exception as e:
        logger.error(f"Location detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _detect_geoip(ip_address: str) -> Dict[str, Any]:
    """Detect location via GeoIP2"""
    try:
        reader = geoip2.database.Reader(GEOIP_DB)
        response = reader.city(ip_address)

        return {
            "ip_address": ip_address,
            "country": response.country.name,
            "country_code": response.country.iso_code,
            "city": response.city.name or "Unknown",
            "region": response.subdivisions[0].name if response.subdivisions else "Unknown",
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
            "timezone": response.location.time_zone
        }

    except Exception as e:
        logger.error(f"GeoIP2 error: {e}")
        return {
            "ip_address": ip_address,
            "country": "Unknown",
            "country_code": "XX",
            "city": "Unknown",
            "region": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "UTC"
        }

def _get_timezone(latitude: float, longitude: float) -> str:
    """Get timezone from coordinates"""
    try:
        # In production, use TimezoneFinder or similar
        # For now, return UTC
        return "UTC"
    except Exception as e:
        logger.error(f"Timezone detection error: {e}")
        return "UTC"

# ============================================================================
# REGION MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/regions")
async def list_regions(region_type: Optional[RegionType] = None):
    """List all regions or filter by type"""
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            if region_type:
                rows = await conn.fetch("""
                    SELECT * FROM regions
                    WHERE region_type = $1 AND enabled = true
                    ORDER BY name
                """, region_type.value)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM regions
                    WHERE enabled = true
                    ORDER BY region_type, name
                """)

        await pool.close()

        regions = [
            Region(
                id=str(row['id']),
                name=row['name'],
                region_type=RegionType(row['region_type']),
                country_code=row['country_code'],
                city=row.get('city'),
                state=row.get('state'),
                latitude=row.get('latitude'),
                longitude=row.get('longitude'),
                currency=CurrencyType(row['currency']),
                language=row['language'],
                tax_rate=float(row['tax_rate']),
                shipping_cost=float(row['shipping_cost']),
                enabled=row['enabled']
            )
            for row in rows
        ]

        logger.info(f"📍 Retrieved {len(regions)} regions")

        return {"regions": regions, "count": len(regions)}

    except Exception as e:
        logger.error(f"List regions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/regions/{region_id}")
async def get_region(region_id: str):
    """Get region details"""
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM regions WHERE id = $1
            """, region_id)

        await pool.close()

        if not row:
            raise HTTPException(status_code=404, detail="Region not found")

        region = Region(
            id=str(row['id']),
            name=row['name'],
            region_type=RegionType(row['region_type']),
            country_code=row['country_code'],
            city=row.get('city'),
            state=row.get('state'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            currency=CurrencyType(row['currency']),
            language=row['language'],
            tax_rate=float(row['tax_rate']),
            shipping_cost=float(row['shipping_cost']),
            enabled=row['enabled']
        )

        logger.info(f"📍 Retrieved region: {region_id}")

        return region

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regions")
async def create_region(region: Region, authorization: Optional[str] = Header(None)):
    """Create new region (admin only)"""
    try:
        # Verify admin token (simplified)
        if not authorization:
            raise HTTPException(status_code=403, detail="Admin access required")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            region_id = await conn.fetchval("""
                INSERT INTO regions (
                    name, region_type, country_code, city, state,
                    latitude, longitude, currency, language, tax_rate,
                    shipping_cost, enabled
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, region.name, region.region_type.value, region.country_code,
                region.city, region.state, region.latitude, region.longitude,
                region.currency.value, region.language, region.tax_rate,
                region.shipping_cost, region.enabled)

        await pool.close()

        logger.info(f"✅ Region created: {region_id}")

        return {"id": str(region_id), "name": region.name}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/regions/{region_id}")
async def update_region(region_id: str, region: Region, authorization: Optional[str] = Header(None)):
    """Update region (admin only)"""
    try:
        if not authorization:
            raise HTTPException(status_code=403, detail="Admin access required")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE regions SET
                    name = $1, region_type = $2, country_code = $3,
                    city = $4, state = $5, latitude = $6, longitude = $7,
                    currency = $8, language = $9, tax_rate = $10,
                    shipping_cost = $11, enabled = $12
                WHERE id = $13
            """, region.name, region.region_type.value, region.country_code,
                region.city, region.state, region.latitude, region.longitude,
                region.currency.value, region.language, region.tax_rate,
                region.shipping_cost, region.enabled, region_id)

        await pool.close()

        logger.info(f"✅ Region updated: {region_id}")

        return {"id": region_id, "status": "updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REGIONAL PRODUCTS
# ============================================================================

@app.get("/regions/{region_id}/products")
async def get_regional_products(
    region_id: str,
    skip: int = 0,
    limit: int = 20
):
    """Get products available in region"""
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT p.*, rp.region_id, rp.local_title, rp.availability,
                       rp.stock_level, rp.fulfillment_center, r.currency
                FROM regional_products rp
                JOIN products p ON rp.product_id = p.id
                JOIN regions r ON rp.region_id = r.id
                WHERE rp.region_id = $1
                ORDER BY p.title
                LIMIT $2 OFFSET $3
            """, region_id, limit, skip)

        await pool.close()

        products = [
            RegionalProduct(
                product_id=str(row['product_id']),
                region_id=str(row['region_id']),
                title=row['title'],
                price=float(row['price']),
                currency=row['currency'],
                local_title=row['local_title'],
                description=row.get('description', ''),
                availability=row['availability'],
                stock_level=row['stock_level'],
                fulfillment_center=row['fulfillment_center']
            )
            for row in rows
        ]

        logger.info(f"📍 Retrieved {len(products)} products for region {region_id}")

        return {"products": products, "count": len(products), "region_id": region_id}

    except Exception as e:
        logger.error(f"Get regional products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regions/{region_id}/products")
async def add_product_to_region(
    region_id: str,
    product: RegionalProduct,
    authorization: Optional[str] = Header(None)
):
    """Add product to region (admin only)"""
    try:
        if not authorization:
            raise HTTPException(status_code=403, detail="Admin access required")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO regional_products (
                    region_id, product_id, local_title, availability,
                    stock_level, fulfillment_center
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (region_id, product_id) DO UPDATE SET
                    availability = EXCLUDED.availability,
                    stock_level = EXCLUDED.stock_level,
                    fulfillment_center = EXCLUDED.fulfillment_center
            """, region_id, product.product_id, product.local_title,
                product.availability, product.stock_level, product.fulfillment_center)

        await pool.close()

        logger.info(f"✅ Product added to region: {product.product_id} → {region_id}")

        return {"status": "added", "product_id": product.product_id, "region_id": region_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add product to region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REGIONAL PRICING
# ============================================================================

@app.get("/regions/{region_id}/pricing/{product_id}")
async def get_regional_pricing(region_id: str, product_id: str):
    """Get product pricing for specific region"""
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            pricing = await conn.fetchrow("""
                SELECT * FROM regional_pricing
                WHERE region_id = $1 AND product_id = $2
                AND expiry_date > NOW()
            """, region_id, product_id)

        await pool.close()

        if not pricing:
            raise HTTPException(status_code=404, detail="Regional pricing not found")

        result = RegionalPricing(
            product_id=str(pricing['product_id']),
            region_id=str(pricing['region_id']),
            base_price=float(pricing['base_price']),
            regional_price=float(pricing['regional_price']),
            currency=pricing['currency'],
            markup_percentage=float(pricing['markup_percentage']),
            effective_date=pricing['effective_date'].isoformat(),
            expiry_date=pricing['expiry_date'].isoformat() if pricing['expiry_date'] else None
        )

        logger.info(f"💰 Retrieved pricing: {product_id} in {region_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get regional pricing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regions/{region_id}/pricing")
async def set_regional_pricing(
    region_id: str,
    pricing: RegionalPricing,
    authorization: Optional[str] = Header(None)
):
    """
    Set dynamic regional pricing (admin only)

    Supports markup, discounts, dynamic pricing
    """
    try:
        if not authorization:
            raise HTTPException(status_code=403, detail="Admin access required")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO regional_pricing (
                    region_id, product_id, base_price, regional_price,
                    currency, markup_percentage, effective_date, expiry_date
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (region_id, product_id) DO UPDATE SET
                    regional_price = EXCLUDED.regional_price,
                    markup_percentage = EXCLUDED.markup_percentage,
                    effective_date = EXCLUDED.effective_date,
                    expiry_date = EXCLUDED.expiry_date
            """, region_id, pricing.product_id, pricing.base_price,
                pricing.regional_price, pricing.currency, pricing.markup_percentage,
                pricing.effective_date, pricing.expiry_date)

        await pool.close()

        logger.info(f"💰 Regional pricing set: {pricing.product_id} in {region_id}")

        return {
            "status": "set",
            "product_id": pricing.product_id,
            "region_id": region_id,
            "regional_price": pricing.regional_price
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set regional pricing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# USER REGION CONTEXT
# ============================================================================

@app.post("/user-context")
async def get_user_region_context(
    user_id: str = Body(...),
    ip_address: Optional[str] = Body(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get complete region context for user

    Combines geolocation + region + pricing + language
    """
    try:
        # Detect location from IP
        location = await detect_location(ip_address or "0.0.0.0")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Find matching region
            region = await conn.fetchrow("""
                SELECT * FROM regions
                WHERE country_code = $1 AND enabled = true
                ORDER BY region_type DESC
                LIMIT 1
            """, location['country_code'])

            if not region:
                # Fallback to global region
                region = await conn.fetchrow("""
                    SELECT * FROM regions
                    WHERE region_type = 'global'
                    LIMIT 1
                """)

        await pool.close()

        context = UserRegionContext(
            user_id=user_id,
            detected_region_id=str(region['id']) if region else "global",
            detected_location=UserLocation(**location),
            primary_region=Region(
                id=str(region['id']),
                name=region['name'],
                region_type=RegionType(region['region_type']),
                country_code=region['country_code'],
                city=region.get('city'),
                state=region.get('state'),
                latitude=region.get('latitude'),
                longitude=region.get('longitude'),
                currency=CurrencyType(region['currency']),
                language=region['language'],
                tax_rate=float(region['tax_rate']),
                shipping_cost=float(region['shipping_cost']),
                enabled=region['enabled']
            ) if region else None,
            preferred_currency=region['currency'] if region else "USD",
            language=region['language'] if region else "en",
            tax_applicable=True
        )

        # Cache context
        redis = await get_redis_client()
        await redis.setex(
            f"user_context:{user_id}",
            3600,
            context.json()
        )
        await redis.close()

        logger.info(f"👤 Retrieved region context for {user_id}")

        return context

    except Exception as e:
        logger.error(f"Get user context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Service health check"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await pool.close()

        redis = await get_redis_client()
        await redis.ping()
        await redis.close()

        return {
            "status": "healthy",
            "service": "geolocation-regions",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Geolocation & Region Management",
        "version": "1.0.0",
        "port": 8012,
        "endpoints": {
            "detect_location": "POST /location/detect",
            "regions": "GET /regions",
            "region_detail": "GET /regions/{region_id}",
            "create_region": "POST /regions",
            "update_region": "PUT /regions/{region_id}",
            "regional_products": "GET /regions/{region_id}/products",
            "add_product": "POST /regions/{region_id}/products",
            "regional_pricing": "GET /regions/{region_id}/pricing/{product_id}",
            "set_pricing": "POST /regions/{region_id}/pricing",
            "user_context": "POST /user-context"
        }
    }

if __name__ == "__main__":
    import uvicorn

    print(f"\n{'='*60}")
    print(f"📍 Geolocation & Region Management Service Starting")
    print(f"   Port: 8012")
    print(f"   Region detection, products, dynamic pricing")
    print(f"{'='*60}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,
        log_level="info"
    )
