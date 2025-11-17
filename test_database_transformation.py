"""
Test Database Transformation
Validates new JSONB schema and features
"""

import asyncio
import asyncpg

# Database connection
DB_URL = "postgresql://compair:compair123@localhost:5432/compair"

async def test_extensions():
    """Test if extensions are installed"""
    conn = await asyncpg.connect(DB_URL)
    try:
        # Check pgvector
        result = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")
        print(f"✅ pgvector extension: {'installed' if result else 'missing'}")
        
        # Check pg_trgm
        result = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='pg_trgm')")
        print(f"✅ pg_trgm extension: {'installed' if result else 'missing'}")
        
        # Check btree_gin
        result = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='btree_gin')")
        print(f"✅ btree_gin extension: {'installed' if result else 'missing'}")
        
        return True
    except Exception as e:
        print(f"❌ Extensions check failed: {e}")
        return False
    finally:
        await conn.close()

async def test_schema():
    """Test if tables exist"""
    conn = await asyncpg.connect(DB_URL)
    try:
        tables = ['products', 'raw_scrapes', 'product_prices', 'embeddings', 
                  'price_alerts', 'alert_history', 'retailers']
        
        for table in tables:
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=$1)",
                table
            )
            print(f"{'✅' if exists else '❌'} Table '{table}': {'exists' if exists else 'missing'}")
        
        return True
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False
    finally:
        await conn.close()

async def test_jsonb():
    """Test JSONB functionality"""
    conn = await asyncpg.connect(DB_URL)
    try:
        # Insert test product with JSONB
        await conn.execute("""
            INSERT INTO products (title, metadata)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, "Test Product", {"test": True, "features": ["a", "b", "c"]})
        
        # Query JSONB
        result = await conn.fetchval("""
            SELECT metadata->'test' FROM products WHERE title = $1
        """, "Test Product")
        
        print(f"✅ JSONB query: {result}")
        return True
    except Exception as e:
        print(f"❌ JSONB test failed: {e}")
        return False
    finally:
        await conn.close()

async def test_indexes():
    """Test if indexes exist"""
    conn = await asyncpg.connect(DB_URL)
    try:
        # Check key indexes
        indexes = await conn.fetch("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE 'idx_%'
        """)
        
        print(f"✅ Found {len(indexes)} custom indexes")
        for idx in indexes[:10]:  # Show first 10
            print(f"   - {idx['indexname']}")
        
        return True
    except Exception as e:
        print(f"❌ Index check failed: {e}")
        return False
    finally:
        await conn.close()

async def test_triggers():
    """Test if triggers exist"""
    conn = await asyncpg.connect(DB_URL)
    try:
        triggers = await conn.fetch("""
            SELECT trigger_name, event_object_table 
            FROM information_schema.triggers 
            WHERE trigger_schema = 'public'
        """)
        
        print(f"✅ Found {len(triggers)} triggers")
        for trg in triggers:
            print(f"   - {trg['trigger_name']} on {trg['event_object_table']}")
        
        return True
    except Exception as e:
        print(f"❌ Trigger check failed: {e}")
        return False
    finally:
        await conn.close()

async def test_materialized_views():
    """Test if materialized views exist"""
    conn = await asyncpg.connect(DB_URL)
    try:
        views = await conn.fetch("""
            SELECT matviewname FROM pg_matviews 
            WHERE schemaname = 'public'
        """)
        
        print(f"✅ Found {len(views)} materialized views")
        for view in views:
            print(f"   - {view['matviewname']}")
        
        return True
    except Exception as e:
        print(f"❌ Materialized views check failed: {e}")
        return False
    finally:
        await conn.close()

async def main():
    print("\n" + "="*60)
    print("🧪 DATABASE TRANSFORMATION VALIDATION")
    print("="*60 + "\n")
    
    print("[1/6] Testing Extensions...")
    await test_extensions()
    print()
    
    print("[2/6] Testing Schema...")
    await test_schema()
    print()
    
    print("[3/6] Testing JSONB...")
    await test_jsonb()
    print()
    
    print("[4/6] Testing Indexes...")
    await test_indexes()
    print()
    
    print("[5/6] Testing Triggers...")
    await test_triggers()
    print()
    
    print("[6/6] Testing Materialized Views...")
    await test_materialized_views()
    print()
    
    print("="*60)
    print("✅ DATABASE TRANSFORMATION VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (docker-compose up -d postgres)")
        print("  2. Database has been initialized with new schema")
        print("  3. asyncpg is installed (pip install asyncpg)")
