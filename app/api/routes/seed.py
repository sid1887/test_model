"""
Seed Data API Routes for Cumpair
Provides fallback product data when live scrapers are unavailable
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
import os

from app.core.monitoring import logger

router = APIRouter(prefix="/api/seed", tags=["seed"])

# Load seed data
SEED_DATA_PATH = Path(__file__).parent.parent.parent.parent / "backend" / "seed_data" / "products.json"

class SeedProduct(BaseModel):
    """Product model for seed data"""
    id: str
    title: str
    price: float
    oldPrice: Optional[float] = None
    currency: str
    store: str
    store_key: str
    image_url: str
    rating: float
    rating_count: int
    categories: List[str]
    location: str
    availability: str
    description: str
    url: str

class SeedProductResponse(BaseModel):
    """Response model for seed products"""
    products: List[SeedProduct]
    total: int
    page: int
    page_size: int
    demo_mode: bool
    last_updated: str
    stores: List[str]
    locations: List[str]

# Cache seed data in memory
_seed_cache = None
_cache_timestamp = None

def load_seed_data() -> Dict[str, Any]:
    """Load seed data from JSON file with caching"""
    global _seed_cache, _cache_timestamp
    
    # Check if cache is still valid (5 minute expiry)
    if _seed_cache and _cache_timestamp:
        age = (datetime.now() - _cache_timestamp).total_seconds()
        if age < 300:  # 5 minutes
            return _seed_cache
    
    try:
        with open(SEED_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _seed_cache = data
        _cache_timestamp = datetime.now()
        logger.info(f"✅ Loaded {len(data.get('products', []))} seed products from {SEED_DATA_PATH}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ Seed data file not found: {SEED_DATA_PATH}")
        return {"products": [], "metadata": {}}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing seed data JSON: {e}")
        return {"products": [], "metadata": {}}

@router.get("/products", response_model=SeedProductResponse)
async def get_seed_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    store: Optional[str] = Query(None, description="Filter by store key (amazon, flipkart, croma)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location (USA, India)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    currency: Optional[str] = Query(None, description="Currency (USD, INR)"),
    sort_by: Optional[str] = Query("rating", description="Sort by: price, rating, popularity"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc")
):
    """
    Get seed products with filtering, pagination, and sorting
    
    Returns demo product data from local JSON file when live scrapers are unavailable.
    This endpoint is used for development, testing, and offline demo mode.
    """
    data = load_seed_data()
    products = data.get("products", [])
    metadata = data.get("metadata", {})
    
    if not products:
        raise HTTPException(status_code=503, detail="Seed data not available")
    
    # Apply filters
    filtered = products
    
    if store:
        filtered = [p for p in filtered if p.get("store_key", "").lower() == store.lower()]
    
    if category:
        filtered = [p for p in filtered if category.lower() in [c.lower() for c in p.get("categories", [])]]
    
    if location:
        filtered = [p for p in filtered if p.get("location", "").lower() == location.lower()]
    
    if currency:
        filtered = [p for p in filtered if p.get("currency", "").lower() == currency.lower()]
    
    if min_price is not None:
        filtered = [p for p in filtered if p.get("price", 0) >= min_price]
    
    if max_price is not None:
        filtered = [p for p in filtered if p.get("price", 0) <= max_price]
    
    # Apply sorting
    reverse = (sort_order.lower() == "desc")
    
    if sort_by == "price":
        filtered.sort(key=lambda x: x.get("price", 0), reverse=reverse)
    elif sort_by == "rating":
        filtered.sort(key=lambda x: x.get("rating", 0), reverse=reverse)
    elif sort_by == "popularity":
        filtered.sort(key=lambda x: x.get("rating_count", 0), reverse=reverse)
    
    # Apply pagination
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    # Check demo mode from environment
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    return SeedProductResponse(
        products=paginated,
        total=total,
        page=page,
        page_size=page_size,
        demo_mode=demo_mode,
        last_updated=metadata.get("last_updated", "2025-01-15T00:00:00Z"),
        stores=metadata.get("stores", []),
        locations=metadata.get("locations", [])
    )

@router.get("/products/{product_id}")
async def get_seed_product(product_id: str):
    """Get a single seed product by ID"""
    data = load_seed_data()
    products = data.get("products", [])
    
    product = next((p for p in products if p.get("id") == product_id), None)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found in seed data")
    
    return {
        "product": product,
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true"
    }

@router.get("/stats")
async def get_seed_stats():
    """Get statistics about seed data"""
    data = load_seed_data()
    products = data.get("products", [])
    metadata = data.get("metadata", {})
    
    # Calculate stats
    stores = {}
    categories = {}
    currencies = {}
    locations = {}
    
    for product in products:
        # Count by store
        store = product.get("store", "Unknown")
        stores[store] = stores.get(store, 0) + 1
        
        # Count by categories
        for cat in product.get("categories", []):
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by currency
        currency = product.get("currency", "Unknown")
        currencies[currency] = currencies.get(currency, 0) + 1
        
        # Count by location
        location = product.get("location", "Unknown")
        locations[location] = locations.get(location, 0) + 1
    
    # Calculate price ranges by currency
    price_ranges = {}
    for currency in currencies.keys():
        currency_products = [p for p in products if p.get("currency") == currency]
        if currency_products:
            prices = [p.get("price", 0) for p in currency_products]
            price_ranges[currency] = {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            }
    
    return {
        "total_products": len(products),
        "stores": stores,
        "categories": categories,
        "currencies": currencies,
        "locations": locations,
        "price_ranges": price_ranges,
        "last_updated": metadata.get("last_updated", "2025-01-15T00:00:00Z"),
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true"
    }

@router.get("/retailers")
async def get_seed_retailers():
    """Get list of retailers from seed data"""
    data = load_seed_data()
    metadata = data.get("metadata", {})
    products = data.get("products", [])
    
    # Extract unique stores with their details
    stores_dict = {}
    for product in products:
        store_key = product.get("store_key")
        if store_key and store_key not in stores_dict:
            stores_dict[store_key] = {
                "key": store_key,
                "name": product.get("store"),
                "location": product.get("location"),
                "currency": product.get("currency"),
                "product_count": 0
            }
        if store_key:
            stores_dict[store_key]["product_count"] += 1
    
    retailers = list(stores_dict.values())
    
    return {
        "retailers": retailers,
        "total": len(retailers),
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true"
    }
