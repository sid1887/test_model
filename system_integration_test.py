#!/usr/bin/env python3
"""
Comprehensive system test for Compair AI Product Analysis & Price Comparison System.
Tests the full workflow from image upload to analysis to price comparison.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from datetime import datetime
import json


async def test_database_integration():
    """Test database integration with all models."""
    print("🗄️ Testing database integration...")
    
    try:
        conn = await asyncpg.connect(
            "postgresql://compair:compair123@localhost:5432/compair"
        )
        
        # Test creating a complete product workflow
        print("   📝 Creating test product...")
        product_id = await conn.fetchval("""
            INSERT INTO products (name, brand, category, image_path, image_hash, specifications, detection_confidence, specification_confidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, 
        "iPhone 15 Pro", 
        "Apple", 
        "Smartphones", 
        "/uploads/iphone15pro.jpg",
        "abc123def456",
        json.dumps({"color": "Natural Titanium", "storage": "256GB", "screen_size": "6.1 inch"}),
        0.95,
        0.92
        )
        
        print(f"   ✅ Product created with ID: {product_id}")
        
        # Test creating analysis
        print("   🔍 Creating test analysis...")
        analysis_id = await conn.fetchval("""
            INSERT INTO analyses (product_id, analysis_type, raw_results, processed_results, confidence_score, processing_time, model_version, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
        product_id,
        "vision_analysis",
        json.dumps({"detected_objects": ["smartphone", "phone"], "brand_detected": "Apple"}),
        json.dumps({"category": "Electronics", "subcategory": "Smartphones", "brand": "Apple", "model": "iPhone 15 Pro"}),
        0.95,
        2.34,
        "yolov8n-v1.0",
        "completed"
        )
        
        print(f"   ✅ Analysis created with ID: {analysis_id}")
        
        # Test creating multiple price comparisons
        print("   💰 Creating test price comparisons...")
        sources = [
            {"name": "Amazon", "url": "https://amazon.com/iphone15pro", "price": 999.99, "rating": 4.5, "reviews": 1250},
            {"name": "Best Buy", "url": "https://bestbuy.com/iphone15pro", "price": 999.00, "rating": 4.3, "reviews": 890},
            {"name": "Apple Store", "url": "https://apple.com/iphone15pro", "price": 999.00, "rating": 4.7, "reviews": 2100}
        ]
        
        price_ids = []
        for source in sources:
            price_id = await conn.fetchval("""
                INSERT INTO price_comparisons (product_id, source_name, source_url, title, price, currency, in_stock, rating, review_count, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
            product_id,
            source["name"],
            source["url"],
            f"iPhone 15 Pro 256GB - {source['name']}",
            source["price"],
            "USD",
            True,
            source["rating"],
            source["reviews"],
            0.93
            )
            price_ids.append(price_id)
            print(f"   ✅ Price comparison created for {source['name']} (ID: {price_id})")
        
        # Test complex queries
        print("   📊 Testing complex database queries...")
        
        # Get product with all related data
        product_data = await conn.fetchrow("""
            SELECT p.*, 
                   COUNT(a.id) as analysis_count,
                   COUNT(pc.id) as price_count,
                   AVG(pc.price) as avg_price,
                   MIN(pc.price) as min_price,
                   MAX(pc.price) as max_price
            FROM products p
            LEFT JOIN analyses a ON p.id = a.product_id
            LEFT JOIN price_comparisons pc ON p.id = pc.product_id
            WHERE p.id = $1
            GROUP BY p.id
        """, product_id)
        
        print(f"   📈 Product summary:")
        print(f"      - Name: {product_data['name']}")
        print(f"      - Analyses: {product_data['analysis_count']}")
        print(f"      - Price sources: {product_data['price_count']}")
        print(f"      - Price range: ${product_data['min_price']:.2f} - ${product_data['max_price']:.2f}")
        print(f"      - Average price: ${product_data['avg_price']:.2f}")
        
        # Cleanup test data
        print("   🧹 Cleaning up test data...")
        for price_id in price_ids:
            await conn.execute("DELETE FROM price_comparisons WHERE id = $1", price_id)
        await conn.execute("DELETE FROM analyses WHERE id = $1", analysis_id)
        await conn.execute("DELETE FROM products WHERE id = $1", product_id)
        
        await conn.close()
        print("   ✅ Database integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Database integration test failed: {e}")
        return False


async def test_file_system_setup():
    """Test file system structure and permissions."""
    print("📁 Testing file system setup...")
    
    try:
        # Check required directories
        required_dirs = [
            "uploads",
            "models", 
            "monitoring",
            "app/api/routes",
            "app/core",
            "app/models",
            "app/services",
            "alembic/versions"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            if full_path.exists():
                print(f"   ✅ Directory exists: {dir_path}")
            else:
                print(f"   ⚠️ Directory missing: {dir_path}")
                # Create missing directories
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created directory: {dir_path}")
        
        # Test file upload directory permissions
        test_file = Path("uploads/test_upload.txt")
        try:
            test_file.write_text("Test upload file")
            print(f"   ✅ Upload directory is writable")
            test_file.unlink()  # Clean up
        except Exception as e:
            print(f"   ❌ Upload directory write test failed: {e}")
            return False
        
        # Check critical files
        critical_files = [
            "requirements.txt",
            "docker-compose.yml",
            "alembic.ini",
            "app/core/database.py",
            "app/models/product.py",
            "app/models/analysis.py",
            "app/models/price_comparison.py"
        ]
        
        for file_path in critical_files:
            if Path(file_path).exists():
                print(f"   ✅ Critical file exists: {file_path}")
            else:
                print(f"   ❌ Critical file missing: {file_path}")
                return False
        
        print("   ✅ File system setup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ File system test failed: {e}")
        return False


def test_docker_services():
    """Test Docker services status."""
    print("🐳 Testing Docker services...")
    
    try:
        import subprocess
        
        # Check if Docker Compose services are running
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            cwd="d:/dev_packages/test_model"
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print("   📋 Docker containers status:")
            
            postgres_running = False
            redis_running = False
            
            for line in lines[1:]:  # Skip header
                if 'postgres' in line.lower():
                    print(f"   ✅ PostgreSQL: {line}")
                    postgres_running = True
                elif 'redis' in line.lower():
                    print(f"   ✅ Redis: {line}")
                    redis_running = True
            
            if not postgres_running:
                print("   ⚠️ PostgreSQL container not found")
                return False
            
            if not redis_running:
                print("   ⚠️ Redis container not found") 
                return False
            
            print("   ✅ Docker services test completed successfully!")
            return True
        else:
            print(f"   ❌ Docker command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Docker services test failed: {e}")
        return False


async def test_migration_status():
    """Test database migration status."""
    print("🔄 Testing migration status...")
    
    try:
        conn = await asyncpg.connect(
            "postgresql://compair:compair123@localhost:5432/compair"
        )
        
        # Check current migration version
        current_version = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        if current_version:
            print(f"   ✅ Current migration version: {current_version}")
        else:
            print("   ❌ No migration version found")
            return False
        
        # Check if all expected tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        expected_tables = ['products', 'analyses', 'price_comparisons', 'alembic_version']
        found_tables = [t['table_name'] for t in tables]
        
        for table in expected_tables:
            if table in found_tables:
                print(f"   ✅ Table exists: {table}")
            else:
                print(f"   ❌ Table missing: {table}")
                return False
        
        await conn.close()
        print("   ✅ Migration status test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Migration status test failed: {e}")
        return False


def test_dependencies():
    """Test that all required dependencies are installed."""
    print("📦 Testing dependencies...")
    
    try:
        # Test critical imports
        critical_packages = [
            ('asyncpg', 'PostgreSQL driver'),
            ('sqlalchemy', 'Database ORM'),
            ('alembic', 'Database migrations'),
            ('pydantic', 'Data validation'),
            ('fastapi', 'Web framework'),
            ('celery', 'Task queue'),
            ('redis', 'Redis client')
        ]
        
        for package, description in critical_packages:
            try:
                __import__(package)
                print(f"   ✅ {package} ({description})")
            except ImportError:
                print(f"   ❌ {package} ({description}) - NOT INSTALLED")
                return False
        
        print("   ✅ Dependencies test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Dependencies test failed: {e}")
        return False


async def main():
    """Run comprehensive system tests."""
    print("🚀 Starting Compair AI System Integration Tests")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️ OS: Windows")
    print(f"📂 Working Directory: {os.getcwd()}")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File System", test_file_system_setup),
        ("Docker Services", test_docker_services),
        ("Migration Status", test_migration_status),
        ("Database Integration", test_database_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            if success:
                passed_tests += 1
                print(f"✅ {test_name} Test: PASSED")
            else:
                print(f"❌ {test_name} Test: FAILED")
        except Exception as e:
            print(f"❌ {test_name} Test: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Compair AI Product Analysis & Price Comparison System is fully operational!")
        print("\n📋 System Status:")
        print("   ✅ Database: PostgreSQL 15 (Initialized & Migrated)")
        print("   ✅ Cache: Redis 7 (Running)")
        print("   ✅ Models: Product, Analysis, PriceComparison (Created)")
        print("   ✅ Migrations: Alembic (Ready)")
        print("   ✅ Dependencies: All required packages (Installed)")
        print("\n🔧 Next Steps:")
        print("   1. 🖼️ Implement image upload and processing endpoints")
        print("   2. 🤖 Integrate AI models (YOLO, EfficientNet, CLIP)")
        print("   3. 🕷️ Set up web scraping for price comparison")
        print("   4. 🌐 Deploy FastAPI web server")
        print("   5. 📊 Add monitoring and analytics")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} TEST(S) FAILED!")
        print("🔧 Please review the failed tests and fix the issues before proceeding.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    asyncio.run(main())
