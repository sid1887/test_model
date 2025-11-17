"""
Product management API routes
Handles CRUD operations for products
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
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
                Product.title.ilike(f"%{search}%"),
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
                    "title": product.title,
                    "brand": product.brand,
                    "category": product.category,
                    "main_image": product.main_image,
                    "description": product.description,
                    "avg_price": float(product.avg_price) if product.avg_price else None,
                    "min_price": float(product.min_price) if product.min_price else None,
                    "max_price": float(product.max_price) if product.max_price else None,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None
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
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "main_image": product.main_image,
                "description": product.description,
                "avg_price": float(product.avg_price) if product.avg_price else None,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
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
            title=product_data.name,
            brand=product_data.brand,
            category=product_data.category,
            description=product_data.description,
            main_image=product_data.image_url,
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
                "title": new_product.title,
                "brand": new_product.brand,
                "category": new_product.category,
                "main_image": new_product.main_image,
                "description": new_product.description,
                "created_at": new_product.created_at.isoformat() if new_product.created_at else None,
                "updated_at": new_product.updated_at.isoformat() if new_product.updated_at else None
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
            product.title = product_data.name
        if product_data.brand is not None:
            product.brand = product_data.brand
        if product_data.category is not None:
            product.category = product_data.category
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.image_url is not None:
            product.main_image = product_data.image_url

        # Save changes
        await db.commit()
        await db.refresh(product)

        return {
            "success": True,
            "product": {
                "id": product.id,
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "main_image": product.main_image,
                "description": product.description,
                "avg_price": float(product.avg_price) if product.avg_price else None,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
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
            "title": product.title,
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

        return {
            "success": True,
            "stats": {
                "total_products": total_products,
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
