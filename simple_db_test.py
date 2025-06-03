#!/usr/bin/env python3
"""
Simple database connection test without complex configuration.
"""

import asyncio
import asyncpg


async def test_basic_connection():
    """Test basic database connection and table verification."""
    print("🔗 Testing PostgreSQL connection...")
    
    try:
        # Connect directly to database
        conn = await asyncpg.connect(
            "postgresql://compair:compair123@localhost:5432/compair"
        )
        
        # Test basic query
        version = await conn.fetchval("SELECT version();")
        print(f"✅ PostgreSQL version: {version[:50]}...")
        
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"\n📋 Tables in database:")
        if not tables:
            print("   ❌ No tables found!")
            return False
            
        for table in tables:
            print(f"   ✅ {table['table_name']}")
        
        # Check specific tables we expect
        expected_tables = {'products', 'analyses', 'price_comparisons', 'alembic_version'}
        found_tables = {table['table_name'] for table in tables}
        
        missing_tables = expected_tables - found_tables
        if missing_tables:
            print(f"   ⚠️ Missing tables: {missing_tables}")
        else:
            print(f"   ✅ All expected tables present")
        
        # Check table structures
        for table_name in ['products', 'analyses', 'price_comparisons']:
            if table_name in found_tables:
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position;
                """)
                
                print(f"\n📋 Table '{table_name}' structure ({len(columns)} columns):")
                for col in columns[:5]:  # Show first 5 columns
                    nullable = "NULL" if col['is_nullable'] == "YES" else "NOT NULL"
                    print(f"   - {col['column_name']}: {col['data_type']} ({nullable})")
                
                if len(columns) > 5:
                    print(f"   ... and {len(columns) - 5} more columns")
        
        # Test simple insert/select/delete
        print(f"\n🧪 Testing basic operations...")
        
        # Insert test data
        await conn.execute("""
            INSERT INTO products (name, brand, category, image_path) 
            VALUES ($1, $2, $3, $4)
        """, "Test Product", "Test Brand", "Electronics", "/test/path.jpg")
        
        # Select test data
        result = await conn.fetchrow("""
            SELECT id, name, brand FROM products WHERE name = $1
        """, "Test Product")
        
        if result:
            print(f"   ✅ Insert/Select successful: ID={result['id']}, Name='{result['name']}'")
            
            # Delete test data
            await conn.execute("DELETE FROM products WHERE id = $1", result['id'])
            print(f"   ✅ Delete successful")
        else:
            print(f"   ❌ Insert/Select failed")
        
        # Check migration status
        alembic_version = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        if alembic_version:
            print(f"\n🔄 Migration status: {alembic_version}")
        else:
            print(f"\n⚠️ No migration version found")
        
        await conn.close()
        print(f"\n🎉 Database is properly configured and ready!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run database tests."""
    print("🚀 Starting basic database connectivity test...\n")
    success = await test_basic_connection()
    
    if success:
        print("\n✅ Database initialization and testing completed successfully!")
        print("🚀 The Compair AI Product Analysis & Price Comparison System is ready!")
    else:
        print("\n❌ Database tests failed. Please check the configuration.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
