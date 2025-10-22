# Runtime Fixes Applied - October 20, 2025

## 🎯 Mission Accomplished!

After 25+ rebuild cycles, we successfully identified and fixed all runtime issues using a debug container approach.

---

## 🔧 Issues Fixed

### 1. **TensorFlow 2.19.x Broken Installation**
**Problem:** TensorFlow 2.19.1 had missing `tensorflow.python` module causing:
```python
ModuleNotFoundError: No module named 'tensorflow.python'
```

**Solution:**
- Updated `requirements.txt`: `tensorflow>=2.13.0,<2.19.0`
- Updated `tf-keras>=2.17.0,<2.19.0` to match TensorFlow version
- This installs TensorFlow 2.18.1 which works correctly

**Files Changed:**
- `requirements.txt` (line 86-88)

---

### 2. **Transformers Pipeline Import Failure**
**Problem:** Even with `accelerate` and `safetensors` installed, pipeline import failed due to broken TensorFlow.

**Root Cause:** The transformers library imports TensorFlow during pipeline initialization, and the broken TensorFlow 2.19.1 caused cascading failures.

**Solution:** Fixed by downgrading TensorFlow to 2.18.1 (see issue #1)

**Verification:**
```bash
✅ TensorFlow 2.18.1 working
✅ Pipeline import SUCCESS
✅ All AI models loading correctly
```

---

### 3. **Missing price_comparison_service Import**
**Problem:**
```python
ImportError: cannot import name 'price_comparison_service' from 'app.services.price_comparison'
```

**Root Cause:** The service was named `cumpair_price_engine` but routes expected `price_comparison_service`.

**Solution:** Added backward compatibility alias in `app/services/price_comparison.py`:
```python
# Global instance
cumpair_price_engine = CumpairPriceEngine()

# Alias for backward compatibility
price_comparison_service = cumpair_price_engine
```

**Files Changed:**
- `app/services/price_comparison.py` (line 627-628)

---

### 4. **Prometheus Metrics Duplicate Registration**
**Problem:**
```python
ValueError: Duplicated timeseries in CollectorRegistry: {'cumpair_requests', 'cumpair_requests_created', 'cumpair_requests_total'}
```

**Root Cause:** Metrics module imported multiple times during startup causing duplicate registration attempts.

**Solution:** Added helper functions to get existing metrics or create new ones in `app/api/routes/metrics.py`:
```python
def get_or_create_counter(name, doc, labels):
    """Get existing counter or create new one"""
    try:
        return Counter(name, doc, labels)
    except ValueError:
        # Metric already registered, get it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        raise

def get_or_create_histogram(name, doc, labels):
    """Get existing histogram or create new one"""
    try:
        return Histogram(name, doc, labels)
    except ValueError:
        # Metric already registered, get it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        raise

def get_or_create_gauge(name, doc, labels=None):
    """Get existing gauge or create new one"""
    try:
        return Gauge(name, doc, labels) if labels else Gauge(name, doc)
    except ValueError:
        # Metric already registered, get it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        raise
```

All metric definitions updated to use these helpers.

**Files Changed:**
- `app/api/routes/metrics.py` (lines 13-46, and all metric definitions)

---

## 🚀 Verification Steps

1. **Start container in debug mode:**
   ```bash
   docker-compose run --entrypoint /bin/bash web
   ```

2. **Inside container:**
   ```bash
   # Uninstall broken TensorFlow
   pip uninstall -y tensorflow
   
   # Install working version
   pip install --no-cache-dir "tensorflow>=2.13.0,<2.19.0" "numpy>=1.24.0,<2.0.0"
   
   # Test imports
   python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__} working')"
   python -c "from transformers import pipeline; print('Pipeline import SUCCESS')"
   
   # Start app
   python main.py
   ```

3. **Results:**
   ```
   ✅ TensorFlow 2.18.1 working!
   ✅ Transformers pipeline SUCCESS!
   ✅ All AI models loaded (YOLO, CLIP, EfficientNet, Sentiment)
   ✅ EasyOCR initialized
   ✅ CLIP search with 41 products loaded
   ✅ Server running on http://0.0.0.0:8000
   ✅ Health endpoint responding: 200 OK
   ```

4. **Save working container:**
   ```bash
   exit
   docker commit $(docker ps -lq) test_model-web:working
   ```

---

## 📦 Package Versions (Verified Working)

```
numpy==1.26.4                    # NumPy 2.x breaks TensorFlow 2.18
tensorflow==2.18.1               # 2.19.x broken, 2.18.x works
tf-keras==2.18.0                 # Must match TensorFlow version
transformers==4.57.1             # Latest version works with 2.18.1
accelerate==1.10.1               # Required for transformers.pipeline
safetensors==0.6.2               # Required for transformers.pipeline
torch==2.4.1                     # CPU-only mode
```

---

## 🎓 Lessons Learned

1. **NumPy 2.x Incompatibility:** TensorFlow 2.18 and earlier require NumPy 1.x
2. **TensorFlow 2.19.x Broken:** Missing `tensorflow.python` module - avoid this version
3. **Debug Mode Best Practice:** Use `docker-compose run --entrypoint /bin/bash` to test packages before rebuild
4. **Prometheus Registry:** Metrics need duplicate registration protection for multiple imports
5. **Service Name Consistency:** Ensure import names match actual service variable names

---

## 🔄 Next Steps for Fresh Rebuild

When ready for a clean rebuild:

```bash
# Stop all services
docker-compose down

# Clean build with fixed requirements
docker-compose build --no-cache web

# Start services
docker-compose up -d

# Verify logs
docker logs -f test_model-web-1
```

Should complete without errors and start successfully!

---

## 📊 Final Status

- **Container Status:** ✅ Running (saved as `test_model-web:working`)
- **AI Models:** ✅ All loaded (YOLO, CLIP, EfficientNet, Sentiment, EasyOCR)
- **API Health:** ✅ Responding on http://localhost:8000/api/v1/health
- **Database:** ✅ PostgreSQL connected
- **Cache:** ✅ Redis connected
- **Metrics:** ✅ Prometheus endpoint working

**Total Image Size:** 37.6GB (CPU-only mode with all ML models)

---

## 🙏 Success Attribution

After extensive debugging and 25+ rebuild cycles, we:
1. Identified TensorFlow 2.19.x as fundamentally broken
2. Found NumPy 2.x incompatibility
3. Fixed import naming mismatches
4. Resolved Prometheus metric registration conflicts
5. Validated all fixes in running container before rebuild

**All changes applied to source code - ready for production rebuild!** 🎉
