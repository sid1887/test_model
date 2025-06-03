"""
Utility script to rebuild CLIP search index from existing products in the database
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_session_maker
from app.models.product import Product
from app.models.analysis import Analysis  # Import Analysis model to resolve relationship
from app.services.clip_search import clip_service
from sqlalchemy import select


async def rebuild_clip_index():
    """Rebuild CLIP search index from all products in database"""
    try:
        print("🔄 Rebuilding CLIP search index...")
        
        # Initialize CLIP service
        await clip_service.initialize()
        print("✅ CLIP service initialized")
        
        # Get all products from database
        async with async_session_maker() as session:
            stmt = select(Product).where(Product.is_processed == True)
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            print(f"📊 Found {len(products)} processed products")
            
            if not products:
                print("⚠️ No processed products found to index")
                return
            
            # Add each product to CLIP index
            indexed_count = 0
            for product in products:
                try:
                    # Check if image file exists
                    if not os.path.exists(product.image_path):
                        print(f"⚠️ Image not found for product {product.id}: {product.image_path}")
                        continue
                    
                    # Add to CLIP index
                    await clip_service.add_product_to_index(
                        product_id=product.id,
                        image_path=product.image_path,
                        title=product.name or f"Product {product.id}",
                        description=f"{product.brand or ''} {product.category or ''}".strip()
                    )
                    
                    indexed_count += 1
                    print(f"✅ Indexed product {product.id}: {product.name}")
                    
                except Exception as e:
                    print(f"❌ Failed to index product {product.id}: {e}")
            
            # Save indexes to disk
            if indexed_count > 0:
                await clip_service.save_indexes()
                print(f"💾 Saved CLIP indexes with {indexed_count} products")
            else:
                print("⚠️ No products were successfully indexed")
        
        print("🎉 CLIP index rebuild completed!")
        
    except Exception as e:
        print(f"❌ Failed to rebuild CLIP index: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(rebuild_clip_index())
