# Database Sharding Strategy for Horizontal Scaling

**Phase:** 6 - Database Optimization
**Objective:** Design sharding architecture to scale to 100M+ products and 10M+ users
**Target Scale:** 10,000+ requests/second across all services

---

## Overview: Why Sharding?

PostgreSQL single-instance limits:
- **Disk I/O:** ~50,000 IOPS
- **CPU:** Limited to server cores
- **Memory:** 256-512GB practical limit
- **Replication:** Read replicas help but don't solve write scalability

Sharding enables:
- Linear write scalability (add more shards = more throughput)
- Geographic distribution (data closer to users)
- Workload isolation (hot data on separate shards)
- Failure isolation (one shard failure doesn't take down entire system)

---

## Section 1: Sharding Key Selection

### Shard Key Candidates

| Key | Pros | Cons | Recommendation |
|-----|------|------|-----------------|
| **user_id** | Perfect locality for user data; recommendations, wishlist, search history | Uneven distribution; hot users = hot shards; regional bias | ✅ **Primary** (60% benefit) |
| **region_id** | Geographic locality; compliance benefits | Heavy cross-shard for global search; recommendations sparse | ✅ **Secondary** (30% benefit) |
| **product_id** | Even distribution; consistent hashing | Zero locality; every query involves multiple shards | ❌ Not recommended |
| **user_id + region_id** | Combine benefits; locality + distribution | Complex routing; 4x shards needed; operational complexity | ⚠️ Consider Phase 7 |

### Selected Strategy: **User-Based Sharding (Primary) + Region-Based Sharding (Secondary)**

```
Primary Sharding Dimension: user_id
├─ Shard 0: Users 0x0000-0x3FFF (hash % 4)
├─ Shard 1: Users 0x4000-0x7FFF
├─ Shard 2: Users 0x8000-0xBFFF
└─ Shard 3: Users 0xC000-0xFFFF

Data Locality:
├─ Wishlist → User shard (100% local)
├─ Purchases → User shard (100% local)
├─ Search history → User shard (100% local)
├─ Recommendations → User shard (pre-computed, cross-shard aggregate)
├─ Products → All shards (replicated)
├─ Regional products → All shards (replicated)
└─ Regional pricing → All shards (replicated)
```

---

## Section 2: Shard Architecture Design

### Shard Ring Topology

```
                   Shard Ring (Consistent Hashing)

                 ┌──────────────────────┐
                 │   Hash Space (128)    │
              0 ─┤    user_id hash      │
                 │                      │
                 │  Shard 0: 0-31       │
            31 ──┤ (Primary writes)     │
                 │                      │
                 │  Shard 1: 32-63      │
            63 ──┤ (Primary writes)     │
                 │                      │
                 │  Shard 2: 64-95      │
            95 ──┤ (Primary writes)     │
                 │                      │
                 │  Shard 3: 96-127     │
           127 ──┤ (Primary writes)     │
                 └──────────────────────┘

Example:
user_id = "abc123def456"
hash = md5("abc123def456") % 128 = 45
→ Shard 1 (32-63)
```

### Sharding Configuration

```python
class ShardRouter:
    """Route queries to appropriate shard"""

    def __init__(self, num_shards: int = 4):
        self.num_shards = num_shards
        self.shards = [
            {
                'host': f'postgres-shard-{i}',
                'port': 5432,
                'database': 'productdb',
                'primary': f'postgres-shard-{i}:5432',
                'replicas': [
                    f'postgres-shard-{i}-replica-1:5432',
                    f'postgres-shard-{i}-replica-2:5432'
                ]
            }
            for i in range(num_shards)
        ]

    def get_shard_for_user(self, user_id: str) -> int:
        """Determine shard for user using consistent hashing"""
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        shard_id = hash_value % self.num_shards
        return shard_id

    def get_shard_for_product(self, product_id: str) -> List[int]:
        """Products replicated across all shards"""
        return list(range(self.num_shards))

    def get_shard_for_region(self, region_id: str) -> List[int]:
        """Regions replicated across all shards"""
        return list(range(self.num_shards))

    async def get_user_shard_connection(self, user_id: str):
        """Get connection to user's shard (for writes)"""
        shard_id = self.get_shard_for_user(user_id)
        shard_config = self.shards[shard_id]
        return await asyncpg.connect(
            host=shard_config['host'],
            port=shard_config['port'],
            database=shard_config['database']
        )

    async def get_read_connection(self, shard_id: int):
        """Get read connection (can use replica for read scaling)"""
        shard_config = self.shards[shard_id]
        # Round-robin replicas for read distribution
        replica = random.choice(shard_config['replicas'])
        return await asyncpg.connect(
            host=replica.split(':')[0],
            port=int(replica.split(':')[1]),
            database=shard_config['database']
        )

router = ShardRouter(num_shards=4)
```

---

## Section 3: Data Distribution

### Which Data Lives Where?

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PLACEMENT STRATEGY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ User-Specific Data (Sharded by user_id)                         │
│ ├─ users → Shard[user_id]        [PRIMARY WRITE SHARD]         │
│ ├─ wishlist → Shard[user_id]     [PRIMARY WRITE SHARD]         │
│ ├─ purchases → Shard[user_id]    [PRIMARY WRITE SHARD]         │
│ ├─ user_searches → Shard[user_id] [PRIMARY WRITE SHARD]        │
│ └─ recommendations → Shard[user_id] [PRE-COMPUTED]            │
│                                                                  │
│ Regional Data (Replicated to all shards)                        │
│ ├─ regions → ALL SHARDS          [READ-ONLY REPLICAS]         │
│ ├─ regional_products → ALL SHARDS [READ-ONLY REPLICAS]       │
│ └─ regional_pricing → ALL SHARDS  [READ-ONLY REPLICAS]       │
│                                                                  │
│ Product Catalog (Replicated to all shards)                      │
│ ├─ products → ALL SHARDS          [READ-ONLY REPLICAS]        │
│ ├─ product_embeddings → ALL SHARDS [READ-ONLY REPLICAS]      │
│ └─ search_history → Shard[user_id] [PRIMARY WRITE SHARD]     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Shard Content Example

```sql
-- Shard 0 (user_id hash % 4 = 0)
-- Contains users: 0x0000-0x3FFF

-- Tables present:
-- - users (filtered: WHERE user_id IN (shard's users))
-- - wishlist (filtered: WHERE user_id IN (shard's users))
-- - purchases (filtered: WHERE user_id IN (shard's users))
-- - user_searches (filtered: WHERE user_id IN (shard's users))
-- - search_history (filtered: WHERE user_id IN (shard's users))
-- - products (REPLICATED from all shards)
-- - product_embeddings (REPLICATED from all shards)
-- - regions (REPLICATED from all shards)
-- - regional_products (REPLICATED from all shards)
-- - regional_pricing (REPLICATED from all shards)
```

---

## Section 4: Query Routing Patterns

### Single-Shard Queries (Fast - Local to shard)

```python
async def get_user_profile(user_id: str):
    """Single-shard query (always local)"""
    shard_id = router.get_shard_for_user(user_id)
    conn = await router.get_user_shard_connection(user_id)

    return await conn.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )

# Latency: ~5-10ms (local to shard)

async def get_wishlist(user_id: str):
    """Single-shard query"""
    shard_id = router.get_shard_for_user(user_id)
    conn = await router.get_user_shard_connection(user_id)

    return await conn.fetch("""
        SELECT p.* FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = $1
    """, user_id)

# Latency: ~15-20ms (products table is replicated, so join is local)
```

### Multi-Shard Queries (Medium)

```python
async def get_trending_products():
    """Multi-shard aggregation query"""

    # Query all shards in parallel
    tasks = []
    for shard_id in range(router.num_shards):
        conn = await router.get_read_connection(shard_id)
        task = conn.fetch("""
            SELECT product_id, COUNT(*) as view_count
            FROM search_history
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY product_id
            LIMIT 100
        """)
        tasks.append(task)

    # Aggregate results from all shards
    all_results = await asyncio.gather(*tasks)

    # Merge and deduplicate
    merged = {}
    for results in all_results:
        for row in results:
            product_id = row['product_id']
            if product_id not in merged:
                merged[product_id] = 0
            merged[product_id] += row['view_count']

    # Sort and return top 20
    top_20 = sorted(
        merged.items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]

    return top_20

# Latency: ~50-100ms (parallel fan-out to 4 shards)
```

### Cross-Shard Join (Complex)

```python
async def get_user_recommendations(user_id: str):
    """Complex: user data from shard + product data from all shards"""

    # Step 1: Get user's purchase history (single shard)
    user_shard = router.get_shard_for_user(user_id)
    conn = await router.get_user_shard_connection(user_id)

    purchases = await conn.fetch("""
        SELECT product_id FROM purchases
        WHERE user_id = $1
        ORDER BY purchased_at DESC LIMIT 50
    """, user_id)

    # Step 2: Find similar products (can use any shard, products replicated)
    similar_products = await conn.fetch("""
        SELECT DISTINCT category FROM products
        WHERE id = ANY($1)
    """, [p['product_id'] for p in purchases])

    categories = [p['category'] for p in similar_products]

    # Step 3: Get recommendations (local shard has all data)
    recommendations = await conn.fetch("""
        SELECT * FROM products
        WHERE category = ANY($1)
        AND id NOT IN (SELECT product_id FROM purchases WHERE user_id = $2)
        ORDER BY rating DESC
        LIMIT 20
    """, categories, user_id)

    return recommendations

# Latency: ~30-50ms (1 shard read + product joins)
```

---

## Section 5: Replication Strategy

### Per-Shard Replication

```
Primary (Port 5432)
    ↓ (WAL stream)
    ├─ Replica 1 (Port 5433) - Read-only
    └─ Replica 2 (Port 5434) - Read-only (backup)
```

### Replication Configuration

```yaml
# docker-compose.sharding.yml
version: '3.8'

services:
  # Shard 0
  postgres-shard-0:
    image: postgres:15
    environment:
      POSTGRES_DB: productdb
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - shard0_data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c wal_level=replica -c max_wal_senders=3

  postgres-shard-0-replica-1:
    image: postgres:15
    environment:
      PGUSER: replication_user
      PGPASSWORD: replication_password
    volumes:
      - shard0_replica1_data:/var/lib/postgresql/data
    command: >
      bash -c "
      pg_basebackup -h postgres-shard-0 -D /var/lib/postgresql/data -U replication_user -v -P -W &&
      postgres -c hot_standby=on"

  postgres-shard-0-replica-2:
    image: postgres:15
    environment:
      PGUSER: replication_user
      PGPASSWORD: replication_password
    volumes:
      - shard0_replica2_data:/var/lib/postgresql/data
    command: >
      bash -c "
      pg_basebackup -h postgres-shard-0 -D /var/lib/postgresql/data -U replication_user -v -P -W &&
      postgres -c hot_standby=on"

  # Repeat for Shards 1, 2, 3...

volumes:
  shard0_data:
  shard0_replica1_data:
  shard0_replica2_data:
```

---

## Section 6: Handling Shard Addition/Removal

### Horizontal Scaling: Adding a Shard

**Scenario:** Grow from 4 shards to 5 shards

```python
async def add_shard(new_shard_id: int):
    """Add new shard to ring"""

    # 1. Create new shard database
    await initialize_shard(new_shard_id)

    # 2. Update router configuration
    router.num_shards = 5
    router.shards.append(new_shard_config)

    # 3. Identify affected users (hash % 5 != hash % 4)
    # Old mapping: user_id % 4 = shard
    # New mapping: user_id % 5 = shard

    for old_shard in range(4):
        affected_users = await get_users_in_shard(old_shard)

        for user in affected_users:
            new_shard = hash(user['id']) % 5

            if new_shard != old_shard:
                # User needs to move from old_shard to new_shard
                await migrate_user(user['id'], old_shard, new_shard)

    # 4. Verify all data migrated
    await verify_migration()

async def migrate_user(user_id: str, from_shard: int, to_shard: int):
    """Migrate user data between shards"""

    from_conn = await router.get_read_connection(from_shard)
    to_conn = await router.get_user_shard_connection_for_shard(user_id, to_shard)

    # Migrate all user tables
    tables = ['users', 'wishlist', 'purchases', 'user_searches', 'search_history']

    for table in tables:
        data = await from_conn.fetch(f"""
            SELECT * FROM {table}
            WHERE user_id = $1
        """, user_id)

        # Insert into new shard
        if data:
            await to_conn.executemany(f"""
                INSERT INTO {table} VALUES ({', '.join(['$' + str(i+1) for i in range(len(data[0]))])})
                ON CONFLICT DO NOTHING
            """, data)

    # Delete from old shard (after verification)
    await from_conn.execute(f"""
        DELETE FROM users WHERE id = $1
    """, user_id)
```

### Downtime: ~0ms (asynchronous migration)

---

## Section 7: Operational Considerations

### Monitoring Shard Health

```python
class ShardHealthMonitor:
    """Monitor shard status and load"""

    async def check_shard_health(self, shard_id: int):
        """Check if shard is responsive"""
        try:
            conn = await router.get_read_connection(shard_id)
            await conn.fetchval("SELECT 1")
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_shard_stats(self, shard_id: int):
        """Get shard statistics"""
        conn = await router.get_read_connection(shard_id)

        return {
            'user_count': await conn.fetchval("SELECT COUNT(*) FROM users"),
            'wishlist_items': await conn.fetchval("SELECT COUNT(*) FROM wishlist"),
            'purchases': await conn.fetchval("SELECT COUNT(*) FROM purchases"),
            'db_size_mb': await conn.fetchval(
                "SELECT pg_database_size('productdb') / 1024 / 1024"
            )
        }

    async def detect_shard_hotspots(self):
        """Identify imbalanced shards"""
        stats = {}
        for shard_id in range(router.num_shards):
            stats[shard_id] = await self.get_shard_stats(shard_id)

        avg_users = sum(s['user_count'] for s in stats.values()) / len(stats)

        hotspots = {
            shard_id: stats[shard_id]['user_count']
            for shard_id, data in stats.items()
            if data['user_count'] > avg_users * 1.5  # >50% above average
        }

        return hotspots if hotspots else None

monitor = ShardHealthMonitor()
```

### Backup Strategy Per Shard

```bash
#!/bin/bash
# Backup each shard independently

for shard_id in 0 1 2 3; do
    pg_dump \
        -h postgres-shard-$shard_id \
        -U admin \
        -d productdb \
        -Fc \
        -f "shard-$shard_id-$(date +%Y%m%d-%H%M%S).dump"

    # Upload to S3
    aws s3 cp "shard-$shard_id-*.dump" s3://backups/shards/
done
```

---

## Section 8: Expected Performance Scaling

### Throughput Scaling

| Metric | 1 Shard | 2 Shards | 4 Shards | 8 Shards |
|--------|---------|----------|----------|----------|
| Write Throughput | 1,000 req/s | 1,900 req/s | 3,800 req/s | 7,500 req/s |
| Read Throughput (2 replicas) | 2,000 req/s | 3,900 req/s | 7,800 req/s | 15,600 req/s |
| Max Concurrent Users | 10,000 | 20,000 | 40,000 | 80,000 |
| P99 Latency | 100ms | 110ms | 120ms | 140ms |

### Storage Scaling

| Metric | 1 Shard | 4 Shards |
|--------|---------|----------|
| Products (replicated) | 100GB | 400GB (4 copies) |
| User Data | 50GB | 12.5GB (each shard) |
| Total | 150GB | 450GB (with replication) |
| Cost | $5,000/mo | $3,000/mo (per TB cheaper) |

---

## Migration Path: From Single to Sharded

### Phase 1: Single PostgreSQL (Current)
- ✅ Simple
- ❌ Not scalable beyond 10K req/s

### Phase 2: Single Primary + Read Replicas (Phase 6)
- ✅ Read scaling to 20K req/s
- ❌ Writes still bottlenecked

### Phase 3: 4-Shard Cluster (Phase 7)
- ✅ Write scaling to ~4,000 req/s
- ✅ User data locality
- ⚠️ Cross-shard queries (20% of queries)

### Phase 4: Geo-Sharded (Phase 8)
- ✅ Regional shards
- ✅ Sub-100ms global latency
- ⚠️ Complex operational management

---

## Summary: Sharding Benefits vs. Costs

**Benefits:**
- ✅ Linear write scaling (1,000 → 8,000 req/s)
- ✅ Geographic data locality
- ✅ Failure isolation (one shard failure = 25% system impact)
- ✅ Independent backup/restore per shard

**Costs:**
- ❌ Operational complexity (manage 4+ databases)
- ❌ Cross-shard queries need application logic
- ❌ Data replication overhead (3x for replicated data)
- ❌ Shard migration complexity

**Recommendation:** Implement for Phase 7 when reaching 10K+ concurrent users or 5,000+ req/s.
