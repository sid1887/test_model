#!/usr/bin/env python3
"""
Test database connection and verify tables are created properly.
"""

import asyncio
import asyncpg
from sqlalchemy import text
from app.core.database import get_db_session, engine


async def test_raw_connection():
    """Test raw asyncpg connection."""
    print("🔗 Testing raw PostgreSQL connection...")
    
    try:
        conn = await asyncpg.connect(
            "postgresql://compair:compair123@localhost:5432/compair"
        )
        
        # Test basic query
        result = await conn.fetchval("SELECT version();")
        print(f"✅ PostgreSQL version: {result}")
        
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        
        print(f"📋 Tables in database:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Raw connection failed: {e}")
        return False


async def test_sqlalchemy_connection():
    """Test SQLAlchemy async connection."""
    print("\n🔗 Testing SQLAlchemy connection...")
    
    try:
        async with get_db_session() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ SQLAlchemy test query result: {row.test}")
            
            # Check each table structure
            for table_name in ['products', 'analyses', 'price_comparisons']:
                result = await session.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                print(f"\n📋 Table '{table_name}' structure:")
                for col in columns:
                    nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                    print(f"   - {col.column_name}: {col.data_type} ({nullable})")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False


async def test_model_operations():
    """Test basic model operations."""
    print("\n🧪 Testing model operations...")
    
    try:
        from app.models.product import Product
        from app.models.analysis import Analysis
        from app.models.price_comparison import PriceComparison
        
        async with get_db_session() as session:
            # Test creating a product
            test_product = Product(
                name="Test Product",
                brand="Test Brand", 
                category="Electronics",
                image_path="/test/path.jpg",
                image_hash="test_hash_123",
                specifications={"color": "black", "size": "medium"},
                detection_confidence=0.95,
                specification_confidence=0.88
            )
            
            session.add(test_product)
            await session.commit()
            await session.refresh(test_product)
            
            print(f"✅ Created test product with ID: {test_product.id}")
            
            # Test creating an analysis
            test_analysis = Analysis(
                product_id=test_product.id,
                analysis_type="vision",
                raw_results={"detected": "smartphone"},
                processed_results={"category": "electronics", "confidence": 0.95},
                confidence_score=0.95,
                processing_time=1.234,
                model_version="v1.0",
                status="completed"
            )
            
            session.add(test_analysis)
            await session.commit()
            await session.refresh(test_analysis)
            
            print(f"✅ Created test analysis with ID: {test_analysis.id}")
            
            # Test creating a price comparison
            test_price = PriceComparison(
                product_id=test_product.id,
                source_name="Test Store",
                source_url="https://test-store.com/product/123",
                title="Test Product - Test Store",
                price=299.99,
                currency="USD",
                in_stock=True,
                rating=4.5,
                review_count=150,
                confidence_score=0.92
            )
            
            session.add(test_price)
            await session.commit()
            await session.refresh(test_price)
            
            print(f"✅ Created test price comparison with ID: {test_price.id}")
            
            # Test relationships
            await session.refresh(test_product, ["analyses", "price_comparisons"])
            print(f"✅ Product has {len(test_product.analyses)} analysis(es)")
            print(f"✅ Product has {len(test_product.price_comparisons)} price comparison(s)")
            
            # Clean up test data
            await session.delete(test_price)
            await session.delete(test_analysis)
            await session.delete(test_product)
            await session.commit()
            
            print("🧹 Cleaned up test data")
        
        return True
        
    except Exception as e:
        print(f"❌ Model operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all database tests."""
    print("🚀 Starting database connectivity tests...\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Raw connection
    if await test_raw_connection():
        tests_passed += 1
    
    # Test 2: SQLAlchemy connection
    if await test_sqlalchemy_connection():
        tests_passed += 1
    
    # Test 3: Model operations
    if await test_model_operations():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All database tests passed! The system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    asyncio.run(main())
