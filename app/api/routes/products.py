"""
Product management API routes
Handles CRUD operations for products
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/products", tags=["products"])

# Mock product data for development
MOCK_PRODUCTS = [
    {
        "id": "1",
        "name": "Amazon Echo Dot (5th Gen)",
        "brand": "Amazon",
        "category": "Smart Speakers",
        "price": 49.99,
        "description": "Smart speaker with Alexa",
        "image_url": "https://example.com/echo-dot.jpg",
        "created_at": "2025-06-25T10:00:00Z",
        "updated_at": "2025-06-25T10:00:00Z"
    },
    {
        "id": "2", 
        "name": "Fire TV Stick 4K Max",
        "brand": "Amazon",
        "category": "Streaming Devices",
        "price": 54.99,
        "description": "Streaming device with 4K support",
        "image_url": "https://example.com/fire-tv.jpg",
        "created_at": "2025-06-25T10:00:00Z",
        "updated_at": "2025-06-25T10:00:00Z"
    }
]

@router.get("/")
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search products by name or description")
):
    """
    List all managed products with optional filtering and pagination
    """
    try:
        logger.info(f"Listing products: skip={skip}, limit={limit}, category={category}, search={search}")
        
        products = MOCK_PRODUCTS.copy()
        
        # Apply category filter
        if category:
            products = [p for p in products if p.get("category", "").lower() == category.lower()]
            
        # Apply search filter
        if search:
            search_lower = search.lower()
            products = [
                p for p in products 
                if search_lower in p.get("name", "").lower() 
                or search_lower in p.get("description", "").lower()
            ]
        
        # Apply pagination
        total = len(products)
        products = products[skip:skip + limit]
        
        return {
            "success": True,
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit,
            "message": f"Retrieved {len(products)} products"
        }
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")

@router.get("/{product_id}")
async def get_product(product_id: str):
    """
    Get a specific product by ID
    """
    try:
        logger.info(f"Getting product: {product_id}")
        
        # Find product in mock data
        product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        return {
            "success": True,
            "product": product,
            "message": f"Product {product_id} retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.post("/")
async def create_product(product_data: dict):
    """
    Create a new product
    """
    try:
        logger.info(f"Creating product: {product_data.get('name', 'Unknown')}")
        
        # Generate new product ID
        new_id = str(len(MOCK_PRODUCTS) + 1)
        
        # Create product object
        new_product = {
            "id": new_id,
            "name": product_data.get("name", ""),
            "brand": product_data.get("brand", ""),
            "category": product_data.get("category", ""),
            "price": product_data.get("price", 0.0),
            "description": product_data.get("description", ""),
            "image_url": product_data.get("image_url", ""),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Add to mock data (in real implementation, save to database)
        MOCK_PRODUCTS.append(new_product)
        
        return {
            "success": True,
            "product": new_product,
            "message": f"Product {new_id} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.put("/{product_id}")
async def update_product(product_id: str, product_data: dict):
    """
    Update an existing product
    """
    try:
        logger.info(f"Updating product: {product_id}")
        
        # Find product index
        product_index = next((i for i, p in enumerate(MOCK_PRODUCTS) if p["id"] == product_id), None)
        
        if product_index is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        # Update product
        MOCK_PRODUCTS[product_index].update(product_data)
        MOCK_PRODUCTS[product_index]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        return {
            "success": True,
            "product": MOCK_PRODUCTS[product_index],
            "message": f"Product {product_id} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """
    Delete a product
    """
    try:
        logger.info(f"Deleting product: {product_id}")
        
        # Find product index
        product_index = next((i for i, p in enumerate(MOCK_PRODUCTS) if p["id"] == product_id), None)
        
        if product_index is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        # Remove product
        deleted_product = MOCK_PRODUCTS.pop(product_index)
        
        return {
            "success": True,
            "product": deleted_product,
            "message": f"Product {product_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

@router.get("/stats/summary")
async def get_product_stats():
    """
    Get product statistics and summary
    """
    try:
        logger.info("Getting product statistics")
        
        total_products = len(MOCK_PRODUCTS)
        categories = list(set(p.get("category", "Unknown") for p in MOCK_PRODUCTS))
        brands = list(set(p.get("brand", "Unknown") for p in MOCK_PRODUCTS))
        avg_price = sum(p.get("price", 0) for p in MOCK_PRODUCTS) / max(total_products, 1)
        
        return {
            "success": True,
            "stats": {
                "total_products": total_products,
                "categories": categories,
                "brands": brands,
                "average_price": round(avg_price, 2),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            },
            "message": "Product statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting product stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get product stats: {str(e)}")
