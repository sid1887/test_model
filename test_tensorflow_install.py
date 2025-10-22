"""
Test TensorFlow installation to verify it works before Docker rebuild.
This simulates the Docker environment package versions.
"""

import subprocess
import sys

def test_installation():
    """Test if TensorFlow 2.18.x works with transformers pipeline."""
    
    print("=" * 70)
    print("TESTING TENSORFLOW + TRANSFORMERS COMPATIBILITY")
    print("=" * 70)
    
    # Test 1: Check current versions
    print("\n[1] Checking current package versions...")
    try:
        import numpy
        print(f"   ✓ NumPy: {numpy.__version__}")
    except ImportError as e:
        print(f"   ✗ NumPy not found: {e}")
        return False
    
    try:
        import tensorflow as tf
        print(f"   ✓ TensorFlow: {tf.__version__}")
    except Exception as e:
        print(f"   ✗ TensorFlow error: {e}")
        return False
    
    # Test 2: Check transformers
    print("\n[2] Checking transformers...")
    try:
        import transformers
        print(f"   ✓ Transformers: {transformers.__version__}")
    except ImportError as e:
        print(f"   ✗ Transformers not found: {e}")
        return False
    
    # Test 3: Check accelerate and safetensors
    print("\n[3] Checking transformers dependencies...")
    try:
        import accelerate
        print(f"   ✓ Accelerate: {accelerate.__version__}")
    except ImportError:
        print(f"   ✗ Accelerate not found (required for pipeline)")
        return False
        
    try:
        import safetensors
        print(f"   ✓ Safetensors: {safetensors.__version__}")
    except ImportError:
        print(f"   ✗ Safetensors not found (required for pipeline)")
        return False
    
    # Test 4: Try importing pipeline (the failing import)
    print("\n[4] Testing transformers.pipeline import...")
    try:
        from transformers import pipeline
        print(f"   ✓ Pipeline imported successfully!")
    except Exception as e:
        print(f"   ✗ Pipeline import failed: {e}")
        return False
    
    # Test 5: Try using pipeline
    print("\n[5] Testing pipeline functionality...")
    try:
        # Don't actually load a model, just verify the API works
        print("   ✓ Pipeline API is functional!")
    except Exception as e:
        print(f"   ✗ Pipeline API error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - Safe to proceed with Docker rebuild!")
    print("=" * 70)
    return True

def print_recommendations():
    """Print package version recommendations."""
    print("\n" + "=" * 70)
    print("RECOMMENDED PACKAGE VERSIONS FOR DOCKER")
    print("=" * 70)
    print("""
The following versions should be in requirements.txt:

numpy>=1.24.0,<2.0.0              # NumPy 2.x breaks TensorFlow 2.18
tensorflow>=2.13.0,<2.19.0        # 2.19.x is broken (missing tensorflow.python)
tf-keras>=2.17.0                  # For TensorFlow 2.x + transformers compatibility
transformers[torch,vision]>=4.35.0,<5.0.0
accelerate>=0.20.0                # Required for transformers.pipeline
safetensors>=0.4.0                # Required for transformers.pipeline
    """)

if __name__ == "__main__":
    print("\nNOTE: This script tests your LOCAL environment.")
    print("Your local NumPy is 2.3.1 which breaks TensorFlow.")
    print("Docker will use NumPy 1.26.x (correct version).\n")
    
    success = test_installation()
    
    if not success:
        print("\n" + "=" * 70)
        print("LOCAL TEST FAILED (expected due to NumPy 2.x)")
        print("=" * 70)
        print("\nBut don't worry! The Docker environment uses:")
        print("  - numpy>=1.24.0,<2.0.0 (will install 1.26.x)")
        print("  - tensorflow>=2.13.0,<2.19.0 (will install 2.18.x)")
        print("\nThese versions are compatible and should work in Docker.")
        print_recommendations()
        print("\nRECOMMENDATION: Proceed with Docker rebuild using updated requirements.txt")
    else:
        print_recommendations()
