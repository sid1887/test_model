"""
Data Pipeline Microservice
Handles product linking, deduplication, data normalization, and price tracking
Integrates scraped data from multiple retailers into unified product catalog
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncpg
import logging
import json
from datetime import datetime, timedelta
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "database": os.getenv("DB_NAME", "cumpair"),
}

# ============================================================================
# MODELS
# ============================================================================

class ProductData(BaseModel):
    """Unified product data structure"""
    title: str
    category: str
    brand: Optional[str] = None
    description: Optional[str] = None
    main_image: Optional[str] = None
    canonical_sku: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class PriceSnapshot(BaseModel):
    """Price information from retailer"""
    product_id: str
    site_name: str
    site_product_id: str
    site_url: str
    price: float
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    in_stock: bool = True
    currency: str = "INR"
    scraped_data: Optional[Dict[str, Any]] = {}

class ProductLinkRequest(BaseModel):
    """Request to link/merge products"""
    products_to_merge: List[str]  # List of product IDs
    canonical_product_id: Optional[str] = None  # If provided, merge into this
    merge_metadata: bool = True

class DeduplicationRequest(BaseModel):
    """Request for product deduplication"""
    use_clip_embeddings: bool = True
    similarity_threshold: float = 0.85  # CLIP similarity threshold

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Data Pipeline Service",
    description="Product linking, deduplication, price tracking, data normalization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

async def get_db_pool():
    """Create database connection pool"""
    try:
        pool = await asyncpg.create_pool(**DB_CONFIG)
        logger.info("✅ Database pool created")
        return pool
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()

async def execute_query(query: str, *args):
    """Execute a database query"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_insert(query: str, *args):
    """Execute insert/update and return result"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        return await conn.fetch(query, *args)

# ============================================================================
# PHASE 2.1: PRODUCT DATA LINKING
# ============================================================================

@app.post("/api/products/link")
async def link_products(request: ProductLinkRequest):
    """
    Link multiple products into a single canonical product
    Merges metadata, maintains retailer URLs separately
    """
    try:
        # Get products to merge
        placeholders = ','.join(['$' + str(i+1) for i in range(len(request.products_to_merge))])
        query = f"""
            SELECT id, title, metadata, brand, category FROM products
            WHERE id IN ({placeholders})
        """
        products = await execute_query(query, *request.products_to_merge)

        if not products:
            raise HTTPException(status_code=404, detail="No products found to link")

        # Determine canonical product
        if request.canonical_product_id:
            canonical = next((p for p in products if str(p['id']) == request.canonical_product_id), None)
            if not canonical:
                raise HTTPException(status_code=404, detail="Canonical product not found")
        else:
            canonical = products[0]

        # Merge metadata
        merged_metadata = canonical['metadata'].copy() if canonical['metadata'] else {}
        if request.merge_metadata:
            for product in products[1:]:
                if product['metadata']:
                    for key, value in product['metadata'].items():
                        if key not in merged_metadata:
                            merged_metadata[key] = value

        # Update canonical product with merged metadata
        update_query = """
            UPDATE products
            SET metadata = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING id, title, metadata
        """
        result = await execute_insert(
            update_query,
            json.dumps(merged_metadata),
            canonical['id']
        )

        # Create version history for merged products
        for product in products[1:]:
            history_query = """
                INSERT INTO product_versions (original_id, canonical_id, merged_at)
                VALUES ($1, $2, NOW())
            """
            await execute_insert(history_query, product['id'], canonical['id'])

        logger.info(f"✅ Linked {len(products)} products -> {canonical['id']}")

        return {
            "status": "success",
            "canonical_product_id": str(canonical['id']),
            "products_merged": len(products),
            "merged_metadata": merged_metadata
        }
    except Exception as e:
        logger.error(f"❌ Product linking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/deduplicate-candidates")
async def get_dedup_candidates(limit: int = 100):
    """
    Get product candidates for deduplication
    Returns products with similar titles or metadata
    """
    try:
        query = """
            SELECT p1.id as product_1_id, p2.id as product_2_id,
                   p1.title as title_1, p2.title as title_2,
                   similarity(p1.title, p2.title) as title_similarity,
                   p1.category, p2.category
            FROM products p1
            JOIN products p2 ON p1.id < p2.id
            WHERE similarity(p1.title, p2.title) > 0.7
            AND p1.category = p2.category
            LIMIT $1
        """

        candidates = await execute_query(query, limit)

        return {
            "candidates_count": len(candidates),
            "candidates": candidates
        }
    except Exception as e:
        logger.error(f"❌ Dedup candidates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 2.2: PRICE TRACKING & HISTORY
# ============================================================================

@app.post("/api/prices/snapshot")
async def record_price_snapshot(price: PriceSnapshot):
    """
    Record a price snapshot for a product from a retailer
    """
    try:
        query = """
            INSERT INTO product_prices
            (product_id, site_name, site_product_id, site_url, price,
             original_price, discount_percent, in_stock, currency, scraped_data, scraped_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
            RETURNING id, scraped_at
        """

        result = await execute_insert(
            query,
            price.product_id,
            price.site_name,
            price.site_product_id,
            price.site_url,
            price.price,
            price.original_price,
            price.discount_percent,
            price.in_stock,
            price.currency,
            json.dumps(price.scraped_data) if price.scraped_data else "{}"
        )

        logger.info(f"✅ Price recorded: {price.product_id} @ {price.site_name}: {price.price}")

        return {
            "status": "success",
            "price_id": result[0]['id'],
            "recorded_at": result[0]['scraped_at']
        }
    except Exception as e:
        logger.error(f"❌ Price snapshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prices/product/{product_id}")
async def get_product_prices(product_id: str, days: int = 30):
    """
    Get price history for a product across all retailers
    """
    try:
        query = """
            SELECT site_name, price, original_price, discount_percent,
                   in_stock, scraped_at, currency
            FROM product_prices
            WHERE product_id = $1
            AND scraped_at > NOW() - INTERVAL '1 day' * $2
            ORDER BY scraped_at DESC
        """

        prices = await execute_query(query, product_id, days)

        if not prices:
            raise HTTPException(status_code=404, detail="No price history found")

        # Calculate statistics
        valid_prices = [p['price'] for p in prices if p['price']]
        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 0
        min_price = min(valid_prices) if valid_prices else 0
        max_price = max(valid_prices) if valid_prices else 0

        return {
            "product_id": product_id,
            "prices": prices,
            "statistics": {
                "average": float(avg_price),
                "minimum": float(min_price),
                "maximum": float(max_price),
                "count": len(prices)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Price history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prices/changes/{product_id}")
async def get_price_changes(product_id: str):
    """
    Detect and return significant price changes
    """
    try:
        query = """
            SELECT site_name,
                   LAG(price) OVER (PARTITION BY site_name ORDER BY scraped_at) as prev_price,
                   price as current_price,
                   ((price - LAG(price) OVER (PARTITION BY site_name ORDER BY scraped_at))
                    / LAG(price) OVER (PARTITION BY site_name ORDER BY scraped_at)) * 100 as percent_change,
                   scraped_at
            FROM product_prices
            WHERE product_id = $1
            ORDER BY site_name, scraped_at DESC
            LIMIT 100
        """

        changes = await execute_query(query, product_id)

        # Filter significant changes (>10%)
        significant = [c for c in changes if c['percent_change'] and abs(c['percent_change']) > 10]

        return {
            "product_id": product_id,
            "all_changes": changes,
            "significant_changes": significant,
            "total_significant": len(significant)
        }
    except Exception as e:
        logger.error(f"❌ Price changes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 2.3: NEWS & MARKET DATA INTEGRATION
# ============================================================================

@app.post("/api/news/ingest")
async def ingest_news(title: str, content: str, source: str, url: str,
                     category: str = "general", published_at: Optional[str] = None):
    """
    Ingest news article and store in database
    """
    try:
        query = """
            INSERT INTO news_articles
            (title, content, source, url, category, published_at, ingested_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            RETURNING id, ingested_at
        """

        pub_date = published_at if published_at else datetime.utcnow().isoformat()

        result = await execute_insert(
            query, title, content, source, url, category, pub_date
        )

        logger.info(f"✅ News ingested: {title[:50]}... from {source}")

        return {
            "status": "success",
            "article_id": result[0]['id'],
            "ingested_at": result[0]['ingested_at']
        }
    except Exception as e:
        logger.error(f"❌ News ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/product-mentions/{product_id}")
async def get_product_mentions(product_id: str):
    """
    Get news articles mentioning a specific product
    """
    try:
        query = """
            SELECT na.id, na.title, na.content, na.source, na.category,
                   na.published_at, nm.mention_type
            FROM news_articles na
            JOIN news_mentions nm ON na.id = nm.article_id
            WHERE nm.product_id = $1
            ORDER BY na.published_at DESC
            LIMIT 50
        """

        mentions = await execute_query(query, product_id)

        return {
            "product_id": product_id,
            "mention_count": len(mentions),
            "mentions": mentions
        }
    except Exception as e:
        logger.error(f"❌ Product mentions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 2.4: DATA NORMALIZATION & VALIDATION
# ============================================================================

@app.post("/api/products/normalize")
async def normalize_product_data(product_id: str):
    """
    Normalize product data: names, categories, units, currencies
    """
    try:
        # Get product
        query = "SELECT id, title, category, metadata FROM products WHERE id = $1"
        product = await execute_query(query, product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product = product[0]
        normalized_metadata = product['metadata'].copy() if product['metadata'] else {}

        # Normalize title
        normalized_title = product['title'].strip().title()

        # Normalize category (standardize to canonical hierarchy)
        category_map = {
            "electronics": "Electronics",
            "phones": "Electronics > Mobile Phones",
            "laptops": "Electronics > Computers",
            "kitchen": "Home & Kitchen",
        }

        normalized_category = category_map.get(
            product['category'].lower(),
            product['category']
        )

        # Update product
        update_query = """
            UPDATE products
            SET title = $1, category = $2, metadata = $3, updated_at = NOW()
            WHERE id = $4
            RETURNING id, title, category, metadata
        """

        result = await execute_insert(
            update_query,
            normalized_title,
            normalized_category,
            json.dumps(normalized_metadata),
            product_id
        )

        logger.info(f"✅ Product normalized: {product_id}")

        return {
            "status": "success",
            "product": result[0]
        }
    except Exception as e:
        logger.error(f"❌ Normalization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate/products")
async def validate_product_data(background_tasks: BackgroundTasks):
    """
    Validate all products for data quality issues
    """
    try:
        query = """
            SELECT id, title, main_image, description, metadata
            FROM products
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """

        products = await execute_query(query)

        validation_issues = []

        for product in products:
            issues = []

            # Check required fields
            if not product['title']:
                issues.append("missing_title")
            if not product['main_image']:
                issues.append("missing_image")
            if not product['description']:
                issues.append("missing_description")

            # Check outliers in price
            if product['metadata']:
                if 'avg_price' in product['metadata']:
                    price = product['metadata']['avg_price']
                    if price < 0 or price > 10000000:
                        issues.append("price_outlier")

            if issues:
                validation_issues.append({
                    "product_id": str(product['id']),
                    "issues": issues
                })

        logger.info(f"✅ Validation complete: {len(validation_issues)} issues found")

        return {
            "total_products": len(products),
            "with_issues": len(validation_issues),
            "issues": validation_issues
        }
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if not db_pool:
            return {"status": "unhealthy", "reason": "Database not initialized"}

        # Test database connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "reason": str(e)}

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    logger.info("""
    ╔════════════════════════════════════════════════╗
    ║     DATA PIPELINE MICROSERVICE STARTED         ║
    ║  Handles: Product Linking, Price Tracking,     ║
    ║  News Integration, Data Normalization          ║
    ╚════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006, workers=4)
