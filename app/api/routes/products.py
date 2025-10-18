"""
Product management API routes
Handles CRUD operations for products
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.product import Product
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/products", tags=["products"])

# Pydantic models for requests/responses
class ProductCreate(BaseModel):
    """Product creation request"""
    name: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[dict] = None

class ProductUpdate(BaseModel):
    """Product update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    brand: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[dict] = None

@router.get("/")
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search products by name or description"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all managed products with optional filtering and pagination
    """
    try:
        logger.info(f"Listing products: skip={skip}, limit={limit}, category={category}, search={search}")
        
        # Build base query
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))
        
        # Apply category filter
        if category:
            stmt = stmt.where(Product.category.ilike(f"%{category}%"))
            count_stmt = count_stmt.where(Product.category.ilike(f"%{category}%"))
            
        # Apply search filter
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%")
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.offset(skip).limit(limit).order_by(Product.created_at.desc())
        
        result = await db.execute(stmt)
        products = result.scalars().all()
        
        return {
            "success": True,
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "brand": product.brand,
                    "category": product.category,
                    "is_processed": product.is_processed,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                    "specifications": product.specifications,
                    "image_path": product.image_path,
                    "detection_confidence": float(product.detection_confidence) if product.detection_confidence else None
                }
                for product in products
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
            "message": f"Retrieved {len(products)} products"
        }
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")

@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific product by ID
    """
    try:
        logger.info(f"Getting product: {product_id}")
        
        # Query product from database
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "is_processed": product.is_processed,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                "specifications": product.specifications,
                "image_path": product.image_path,
                "detection_confidence": float(product.detection_confidence) if product.detection_confidence else None
            },
            "message": f"Product {product_id} retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.post("/")
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new product
    """
    try:
        logger.info(f"Creating product: {product_data.name}")
        
        # Create product object
        new_product = Product(
            name=product_data.name,
            brand=product_data.brand,
            category=product_data.category,
            specifications=product_data.specifications or {},
            is_processed=False
        )
        
        # Add to database
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        
        return {
            "success": True,
            "product": {
                "id": new_product.id,
                "name": new_product.name,
                "brand": new_product.brand,
                "category": new_product.category,
                "is_processed": new_product.is_processed,
                "created_at": new_product.created_at.isoformat() if new_product.created_at else None,
                "updated_at": new_product.updated_at.isoformat() if new_product.updated_at else None,
                "specifications": new_product.specifications,
                "image_path": new_product.image_path
            },
            "message": f"Product {new_product.id} created successfully"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing product
    """
    try:
        logger.info(f"Updating product: {product_id}")
        
        # Find product
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        # Update fields if provided
        if product_data.name is not None:
            product.name = product_data.name
        if product_data.brand is not None:
            product.brand = product_data.brand
        if product_data.category is not None:
            product.category = product_data.category
        if product_data.specifications is not None:
            product.specifications = product_data.specifications
        
        # Save changes
        await db.commit()
        await db.refresh(product)
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "is_processed": product.is_processed,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                "specifications": product.specifications,
                "image_path": product.image_path
            },
            "message": f"Product {product_id} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a product
    """
    try:
        logger.info(f"Deleting product: {product_id}")
        
        # Find product
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
        # Store product data before deletion
        product_data = {
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category
        }
        
        # Remove product
        await db.delete(product)
        await db.commit()
        
        return {
            "success": True,
            "product": product_data,
            "message": f"Product {product_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

@router.get("/stats/summary")
async def get_product_stats(db: AsyncSession = Depends(get_db)):
    """
    Get product statistics and summary
    """
    try:
        logger.info("Getting product statistics")
        
        # Get total products count
        total_stmt = select(func.count(Product.id))
        total_result = await db.execute(total_stmt)
        total_products = total_result.scalar()
        
        # Get unique categories
        categories_stmt = select(Product.category).distinct().where(Product.category.isnot(None))
        categories_result = await db.execute(categories_stmt)
        categories = [cat for cat in categories_result.scalars().all() if cat]
        
        # Get unique brands
        brands_stmt = select(Product.brand).distinct().where(Product.brand.isnot(None))
        brands_result = await db.execute(brands_stmt)
        brands = [brand for brand in brands_result.scalars().all() if brand]
        
        # Get processed count
        processed_stmt = select(func.count(Product.id)).where(Product.is_processed == True)
        processed_result = await db.execute(processed_stmt)
        processed_count = processed_result.scalar()
        
        return {
            "success": True,
            "stats": {
                "total_products": total_products,
                "processed_products": processed_count,
                "unprocessed_products": total_products - processed_count,
                "categories": categories,
                "brands": brands,
                "category_count": len(categories),
                "brand_count": len(brands),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            },
            "message": "Product statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting product stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get product stats: {str(e)}")
