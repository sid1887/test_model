import requests
import time

print("=== CACHE FIX TEST ===\n")

# First search
print("1. First search (no cache expected)")
start = time.time()
r1 = requests.post("http://localhost:8000/api/v1/scrapy/search",
    json={"query": "test_phone_cache", "retailers": ["amazon"]},
    timeout=120)
t1 = time.time() - start
d1 = r1.json()
print(f"   Status: {r1.status_code}")
print(f"   Time: {t1:.2f}s")
print(f"   Cached: {d1.get('cached', False)}")
print(f"   Source: {d1.get('source', 'unknown')}")

# Second search (identical) - should hit cache
time.sleep(0.5)
print("\n2. Second search (CACHE HIT expected)")
start = time.time()
r2 = requests.post("http://localhost:8000/api/v1/scrapy/search",
    json={"query": "test_phone_cache", "retailers": ["amazon"]},
    timeout=120)
t2 = time.time() - start
d2 = r2.json()
print(f"   Status: {r2.status_code}")
print(f"   Time: {t2:.2f}s")
print(f"   Cached: {d2.get('cached', False)}")
print(f"   Source: {d2.get('source', 'unknown')}")

# Verify caching worked
if d2.get("cached") and t2 < 1:
    print("\n✅ CACHE FIX WORKING!")
    print(f"   Speed improvement: {t1:.2f}s → {t2:.2f}s")
    print(f"   Speedup factor: {t1/t2:.1f}x")
else:
    print("\n⚠️ Cache may not be working properly")
    print(f"   First: {t1:.2f}s cached={d1.get('cached')}")
    print(f"   Second: {t2:.2f}s cached={d2.get('cached')}")
