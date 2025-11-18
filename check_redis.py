import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print("Redis connection:", r.ping())

keys = r.keys("cache:*")
print(f"Cache keys found: {len(keys)}")
for key in keys[:5]:
    print(f"  - {key}")

if not keys:
    print("\n⚠️ No cache keys found - something is wrong with caching")
else:
    print(f"\n✅ Cache keys being stored ({len(keys)} total)")
