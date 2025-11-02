#!/usr/bin/env python3
"""Quick import test"""
import sys
sys.path.insert(0, 'd:\\dev_packages\\test_model')

try:
    from app.core.config import settings
    print("✓ Config OK")
    print(f"  - hf_api_key exists: {hasattr(settings, 'hf_api_key')}")
except Exception as e:
    print(f"✗ Config FAILED: {e}")
    sys.exit(1)

try:
    from app.core.metrics import metrics
    print("✓ Metrics OK")
    print(f"  - metrics type: {type(metrics)}")
    print(f"  - has track_ai_inference: {hasattr(metrics, 'track_ai_inference')}")
except Exception as e:
    print(f"✗ Metrics FAILED: {e}")
    sys.exit(1)

try:
    from app.services.huggingface_client import HuggingFaceClient
    print("✓ HuggingFace client import OK")
except Exception as e:
    print(f"✗ HuggingFace FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All critical imports successful!")
