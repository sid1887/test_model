"""
Quick verification script to test all fixes are applied correctly
Run this before docker rebuild to ensure source code is ready
"""

import sys
import os

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {filepath}")
        return False

def check_file_contains(filepath, search_string, description):
    """Check if a file contains a specific string"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - STRING NOT FOUND")
                return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("=" * 70)
    print("PRE-REBUILD VERIFICATION")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Check 1: TensorFlow version constraint in requirements.txt
    print("[1] Checking TensorFlow version constraint...")
    all_passed &= check_file_contains(
        'requirements.txt',
        'tensorflow>=2.13.0,<2.19.0',
        '    TensorFlow version constraint correct (<2.19.0)'
    )
    
    # Check 2: tf-keras version constraint
    print("\n[2] Checking tf-keras version constraint...")
    all_passed &= check_file_contains(
        'requirements.txt',
        'tf-keras>=2.17.0,<2.19.0',
        '    tf-keras version constraint correct'
    )
    
    # Check 3: NumPy version constraint
    print("\n[3] Checking NumPy version constraint...")
    all_passed &= check_file_contains(
        'requirements.txt',
        'numpy>=1.24.0,<2.0.0',
        '    NumPy version constraint correct (<2.0.0)'
    )
    
    # Check 4: price_comparison_service alias
    print("\n[4] Checking price_comparison_service alias...")
    all_passed &= check_file_contains(
        'app/services/price_comparison.py',
        'price_comparison_service = cumpair_price_engine',
        '    price_comparison_service alias exists'
    )
    
    # Check 5: Metrics helper functions
    print("\n[5] Checking metrics duplicate registration fix...")
    all_passed &= check_file_contains(
        'app/api/routes/metrics.py',
        'def get_or_create_counter',
        '    get_or_create_counter helper function exists'
    )
    all_passed &= check_file_contains(
        'app/api/routes/metrics.py',
        'def get_or_create_histogram',
        '    get_or_create_histogram helper function exists'
    )
    all_passed &= check_file_contains(
        'app/api/routes/metrics.py',
        'def get_or_create_gauge',
        '    get_or_create_gauge helper function exists'
    )
    
    # Check 6: Metrics import in main.py
    print("\n[6] Checking main.py imports metrics...")
    all_passed &= check_file_contains(
        'main.py',
        'from app.api.routes import analysis, analysis_new, comparison, health, price_comparison, metrics',
        '    metrics imported in main.py'
    )
    all_passed &= check_file_contains(
        'main.py',
        'app.include_router(metrics.router',
        '    metrics router included'
    )
    
    # Check 7: Accelerate and safetensors in requirements
    print("\n[7] Checking transformers dependencies...")
    all_passed &= check_file_contains(
        'requirements.txt',
        'accelerate>=0.20.0',
        '    accelerate>=0.20.0 in requirements.txt'
    )
    all_passed &= check_file_contains(
        'requirements.txt',
        'safetensors>=0.4.0',
        '    safetensors>=0.4.0 in requirements.txt'
    )
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready for docker rebuild!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. docker-compose down")
        print("  2. docker-compose build --no-cache web")
        print("  3. docker-compose up -d")
        print("  4. docker logs -f test_model-web-1")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before rebuild")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
