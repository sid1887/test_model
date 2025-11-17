#!/usr/bin/env python3
"""
Sync FAISS metadata to PostgreSQL database
Loads 41 products from FAISS indexes and inserts into products table
"""

import pickle
from pathlib import Path
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.product import Product
from app.core.config import settings

def sync_faiss_to_db():
    """Load FAISS metadata and sync to database"""
    
    print("🔄 Starting FAISS → PostgreSQL sync...")
    
    # Load metadata
    metadata_path = Path("/app/models/clip_indexes/metadata.pkl")
    if not metadata_path.exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return False
    
    try:
        with open(metadata_path, 'rb') as f:
            products_metadata = pickle.load(f)
        
        print(f"✅ Loaded {len(products_metadata)} products from FAISS metadata")
        
    except Exception as e:
        print(f"❌ Failed to load metadata: {e}")
        return False
    
    # Create database connection
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        print("✅ Connected to PostgreSQL")
        
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False
    
    # Insert products
    inserted_count = 0
    errors = 0
    
    # metadata is a dict with integer keys
    for idx, (key, meta) in enumerate(products_metadata.items(), 1):
        try:
            # Extract data from metadata
            if not isinstance(meta, dict):
                print(f"⏭️  {idx}/41: Skipping non-dict entry")
                continue
                
            title = meta.get('title', f'Product {idx}')
            description = meta.get('description', '')
            image_path = meta.get('image_path', '')
            product_id_meta = meta.get('product_id')
            
            # Check if product already exists
            existing = session.query(Product).filter(
                Product.title == title
            ).first()
            
            if existing:
                print(f"⏭️  Skipping {idx}/41: {title} (already exists)")
                continue
            
            # Create new product
            product = Product(
                id=uuid4(),  # Generate new UUID
                title=title,
                description=description,
                main_image=image_path,
                brand="Unknown",
                category="General",
                product_metadata={
                    'source': 'faiss_legacy',
                    'original_product_id': product_id_meta
                }
            )
            
            session.add(product)
            session.commit()
            
            inserted_count += 1
            print(f"✅ {idx}/41: Inserted '{title}'")
            
        except Exception as e:
            session.rollback()
            errors += 1
            print(f"❌ {idx}/41: Error - {e}")
    
    session.close()
    
    print(f"\n{'='*60}")
    print(f"✅ SYNC COMPLETE")
    print(f"{'='*60}")
    print(f"Inserted: {inserted_count} products")
    print(f"Errors: {errors}")
    print(f"Total in FAISS metadata: {len(products_metadata)}")
    
    if inserted_count > 0:
        print(f"\n🎉 Database now has {inserted_count} products!")
        print(f"Try search: curl 'http://localhost:8000/api/v2/search?q=phone'")
    
    return inserted_count > 0

if __name__ == "__main__":
    result = sync_faiss_to_db()
    sys.exit(0 if result else 1)
