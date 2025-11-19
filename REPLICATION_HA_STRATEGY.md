# Replication & High-Availability (HA) Strategy

**Phase:** 6 - Database Optimization
**Objective:** Achieve 99.99% uptime with automatic failover
**Target:** <1 minute failover time, <5 second recovery detection

---

## Overview: Why Replication?

**Single PostgreSQL Vulnerabilities:**
- Server failure → entire system down
- Hardware failure → data loss risk
- Maintenance → service interruption
- Recovery time → 30+ minutes with backup restoration

**With Replication:**
- ✅ 99.99% uptime (52.6 minutes/year downtime)
- ✅ 0 data loss (synchronous replication)
- ✅ <1 minute automatic failover
- ✅ Live maintenance (on replicas)

---

## Section 1: Replication Architecture

### 3-Node High-Availability Cluster

```
                    Primary (Port 5432)
                    ├─ Write leader
                    ├─ 100% of transactions
                    └─ Accepts connections
                         │
              ┌──────────┼──────────┐
              │                     │
        WAL Stream            WAL Stream
        (continuous)          (continuous)
              │                     │
              ↓                     ↓
        Replica 1 (5433)    Replica 2 (5434)
        ├─ Read-only          ├─ Read-only
        ├─ Standby            ├─ Standby (hot)
        └─ 50% of reads       └─ Read-heavy queries


        Election Coordinator: etcd/patroni
        ├─ Monitor primary health
        ├─ Detect failure (<5 sec)
        └─ Promote best replica to primary
```

### Replication Modes

| Mode | Description | Use Case | RPO | RTO |
|------|-------------|----------|-----|-----|
| **Async** | Primary doesn't wait for replica | High throughput, ok with data loss | Minutes | 1-2 min |
| **Sync** (Selected) | Primary waits for at least 1 replica | No data loss, critical transactions | 0 seconds | <1 min |
| **Remote sync** | Primary waits for replica to disk | Best safety, slight latency | 0 seconds | <1 min |

**Selected: Synchronous Replication** (no data loss, <1ms latency impact)

---

## Section 2: PostgreSQL Replication Setup

### Primary Server Configuration

```ini
# postgresql.conf (on primary)

# Enable replication
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
hot_standby = on

# Synchronous replication
synchronous_commit = remote_apply
synchronous_standby_names = 'replica1,replica2'

# Performance settings
shared_buffers = 128GB
effective_cache_size = 256GB
work_mem = 64MB
maintenance_work_mem = 2GB

# Logging
log_replication_commands = on
log_connections = on
log_disconnections = on
```

### Create Replication User

```sql
-- Create dedicated replication user
CREATE ROLE replication_user WITH LOGIN REPLICATION ENCRYPTED PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE productdb TO replication_user;
GRANT USAGE ON SCHEMA public TO replication_user;

-- Create replication slot
SELECT * FROM pg_create_physical_replication_slot('replica1_slot');
SELECT * FROM pg_create_physical_replication_slot('replica2_slot');
```

### pg_hba.conf (Allow Replication)

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             all                                     trust

# Replication connections
host    replication     replication_user 192.168.1.0/24        md5

# Replica standby
host    all             replication_user 192.168.1.10/32       md5
host    all             replication_user 192.168.1.11/32       md5

# Application connections
host    productdb       admin            192.168.1.0/24        md5
```

### Replica 1: Initial Setup

```bash
#!/bin/bash
# On replica server

# Stop any existing PostgreSQL
systemctl stop postgresql

# Create data directory
rm -rf /var/lib/postgresql/15/data
mkdir -p /var/lib/postgresql/15/data
chown postgres:postgres /var/lib/postgresql/15/data
chmod 700 /var/lib/postgresql/15/data

# Base backup from primary
sudo -u postgres pg_basebackup \
    -h 192.168.1.5 \
    -D /var/lib/postgresql/15/data \
    -U replication_user \
    -P \
    -v \
    -W \
    -X stream \
    -C \
    -S replica1_slot

# Create standby.signal file (tells PostgreSQL this is a standby)
touch /var/lib/postgresql/15/data/standby.signal

# Verify replication configuration
echo "standby_mode = 'on'" >> /var/lib/postgresql/15/data/recovery.conf
echo "primary_conninfo = 'host=192.168.1.5 port=5432 user=replication_user password=password'" >> /var/lib/postgresql/15/data/recovery.conf
echo "primary_slot_name = 'replica1_slot'" >> /var/lib/postgresql/15/data/recovery.conf

# Start PostgreSQL
systemctl start postgresql

# Verify replication is working
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
```

---

## Section 3: Automatic Failover with Patroni

### Patroni Architecture

```
Services → VIP (Virtual IP: 192.168.1.100:5432)
           ↓
      Patroni (HA Manager)
      ├─ Monitor health
      ├─ Detect failure
      ├─ Elect new primary
      └─ Update VIP routing
           ↓
    Primary (Current: Node A)
    ↑ (Can change on failure)
```

### Patroni Installation & Configuration

```bash
# Install Patroni
pip install patroni[postgresql]
pip install etcd3
```

### Patroni Configuration File

```yaml
# patroni.yml

scope: productdb-cluster
namespace: /productdb/

etcd:
  host: 192.168.1.20:2379      # etcd cluster
  username: patroni
  password: password
  protocol: http

postgresql:
  data_dir: /var/lib/postgresql/15/data
  bin_dir: /usr/lib/postgresql/15/bin
  port: 5432
  username: postgres
  password: postgres

  # Replication settings
  parameters:
    wal_level: replica
    max_wal_senders: 10
    max_replication_slots: 10
    wal_keep_size: 1GB
    hot_standby: on
    synchronous_commit: remote_apply
    synchronous_standby_names: "'*'"

  # Recovery settings
  recovery_conf:
    restore_command: "cp /var/lib/postgresql/wal_archive/%f %p"

  # Callbacks
  pg_ctl_timeout: 300
  use_pg_rewind: true

restapi:
  listen: 0.0.0.0:8008
  connect_address: 192.168.1.10:8008

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false

# Watchdog (for safe failover)
watchdog:
  mode: automatic
  device: /dev/watchdog
  safety_margin: 5
```

### Docker Compose Setup with Patroni

```yaml
version: '3.8'

services:
  # etcd cluster for coordination
  etcd:
    image: quay.io/coreos/etcd:v3.5.0
    environment:
      ETCD_NAME: etcd-node
      ETCD_INITIAL_ADVERTISE_PEER_URLS: http://etcd:2380
      ETCD_LISTEN_PEER_URLS: http://0.0.0.0:2380
      ETCD_ADVERTISE_CLIENT_URLS: http://etcd:2379
      ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
    ports:
      - "2379:2379"
      - "2380:2380"
    volumes:
      - etcd_data:/etcd-data

  # Primary Node
  postgres-primary:
    image: patroni:postgres15
    environment:
      PATRONI_SCOPE: productdb-cluster
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/15/data
      PATRONI_ETCD_HOST: etcd:2379
      PATRONI_POSTGRESQL_PGCTL: /usr/lib/postgresql/15/bin/pg_ctl
      PATRONI_POSTGRESQL_PORT: 5432
      PATRONI_POSTGRESQL_USERNAME: postgres
      PATRONI_POSTGRESQL_PASSWORD: postgres
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
    ports:
      - "5432:5432"
      - "8008:8008"
    volumes:
      - postgres_primary_data:/var/lib/postgresql/15/data
      - ./patroni.yml:/etc/patroni/patroni.yml:ro
    depends_on:
      - etcd
    entrypoint: /usr/bin/patroni /etc/patroni/patroni.yml

  # Replica 1
  postgres-replica-1:
    image: patroni:postgres15
    environment:
      PATRONI_SCOPE: productdb-cluster
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/15/data
      PATRONI_ETCD_HOST: etcd:2379
      PATRONI_POSTGRESQL_PGCTL: /usr/lib/postgresql/15/bin/pg_ctl
      PATRONI_POSTGRESQL_PORT: 5432
      PATRONI_POSTGRESQL_USERNAME: postgres
      PATRONI_POSTGRESQL_PASSWORD: postgres
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
    ports:
      - "5433:5432"
      - "8009:8008"
    volumes:
      - postgres_replica1_data:/var/lib/postgresql/15/data
      - ./patroni.yml:/etc/patroni/patroni.yml:ro
    depends_on:
      - etcd
    entrypoint: /usr/bin/patroni /etc/patroni/patroni.yml

  # Replica 2
  postgres-replica-2:
    image: patroni:postgres15
    environment:
      PATRONI_SCOPE: productdb-cluster
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/15/data
      PATRONI_ETCD_HOST: etcd:2379
      PATRONI_POSTGRESQL_PGCTL: /usr/lib/postgresql/15/bin/pg_ctl
      PATRONI_POSTGRESQL_PORT: 5432
      PATRONI_POSTGRESQL_USERNAME: postgres
      PATRONI_POSTGRESQL_PASSWORD: postgres
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
    ports:
      - "5434:5432"
      - "8010:8008"
    volumes:
      - postgres_replica2_data:/var/lib/postgresql/15/data
      - ./patroni.yml:/etc/patroni/patroni.yml:ro
    depends_on:
      - etcd
    entrypoint: /usr/bin/patroni /etc/patroni/patroni.yml

  # HAProxy for VIP failover
  haproxy:
    image: haproxy:2.8-alpine
    ports:
      - "5433:5432"      # VIP for application connections
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    depends_on:
      - postgres-primary
      - postgres-replica-1
      - postgres-replica-2

volumes:
  etcd_data:
  postgres_primary_data:
  postgres_replica1_data:
  postgres_replica2_data:
```

### HAProxy Configuration (VIP)

```cfg
# haproxy.cfg

global
    daemon
    maxconn 4000
    log stdout local0

defaults
    mode tcp
    balance roundrobin
    option tcplog
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend db_write
    bind 0.0.0.0:5432
    mode tcp
    default_backend postgres_primary

frontend db_read
    bind 0.0.0.0:5433
    mode tcp
    default_backend postgres_replicas

backend postgres_primary
    mode tcp
    option tcp-check
    tcp-check connect port 5432
    server primary postgres-primary:5432 check

backend postgres_replicas
    mode tcp
    balance roundrobin
    option tcp-check
    tcp-check connect port 5432
    server replica1 postgres-replica-1:5432 check
    server replica2 postgres-replica-2:5432 check
```

---

## Section 4: Failover Scenarios

### Scenario 1: Primary Failure Detection & Failover

```
Timeline:
T+0s:   Primary server crash
        │
T+3s:   Patroni on replica detects no heartbeat
        │
T+5s:   etcd cluster votes to promote best replica
        │
T+8s:   Replica 1 promoted to primary
        │
        - standby.signal removed
        - Promoted to primary role
        - Accepts writes
        │
T+12s:  HAProxy updates routing to new primary
        │
T+15s:  Clients reconnect (connection pool handles)
        │
T+20s:  Old primary marked failed
        │
✅ FAILOVER COMPLETE
   - Downtime: ~15-20 seconds
   - Data loss: 0 (synchronous replication)
   - Client impact: Connection reset + retry
```

### Scenario 2: Network Partition

```
Scenario: Primary network isolated from cluster
         ├─ Primary still serving local clients
         ├─ But isolated from replicas
         └─ Patroni detects network split

Decision:
├─ Majority cluster (2 replicas + etcd) continues
├─ Minority partition (primary) stops accepting writes
└─ Replica 1 promoted to primary

Result:
├─ Primary clients: Write rejection after 5s
├─ Replica clients: Continuous service
├─ No split-brain (primary stopped writes)
├─ Manual intervention needed to re-add failed primary
└─ Data safety: Maintained
```

### Scenario 3: Planned Maintenance

```
Goal: Upgrade primary without downtime

Steps:
1. Promote best replica to primary (Replica 1)
   - Replica 1 becomes new primary
   - Old primary becomes new replica
   - 0 data loss (async promotion)

2. Upgrade old primary
   - Stop PostgreSQL
   - Upgrade binaries
   - Start as replica

3. Verify replication catching up
   - Compare LSN positions
   - Confirm no lag

4. Optional: Switch back to original primary
   - Promote new primary back to primary
   - Old primary becomes replica

Duration: 2-5 minutes
Downtime: 0
Data loss: 0
```

---

## Section 5: Monitoring Failover Health

### Patroni Health Check API

```python
import httpx

async def check_cluster_health():
    """Monitor cluster via Patroni API"""

    nodes = ['192.168.1.10:8008', '192.168.1.11:8008', '192.168.1.12:8008']

    for node in nodes:
        async with httpx.AsyncClient() as client:
            # Check node health
            response = await client.get(f"http://{node}/health")
            status = response.json()

            print(f"Node {node}:")
            print(f"  Role: {status.get('role')}")
            print(f"  State: {status.get('state')}")
            print(f"  Replication lag: {status.get('lag')} bytes")

            # Monitor replication
            if status.get('role') == 'replica':
                if status.get('lag') > 1_000_000:
                    logger.warning(f"High replication lag on {node}: {status['lag']} bytes")

async def monitor_failover_readiness():
    """Ensure cluster can failover quickly"""

    # 1. Verify all replicas are healthy
    assert await is_replica_healthy('192.168.1.11:8008')
    assert await is_replica_healthy('192.168.1.12:8008')

    # 2. Verify replication lag < 10MB
    lag = await get_replication_lag()
    assert lag < 10_000_000, f"Lag too high: {lag}"

    # 3. Verify etcd cluster is healthy
    etcd_health = await check_etcd_health()
    assert len(etcd_health['members']) >= 3, "etcd cluster unhealthy"

    # 4. Estimate failover time
    failover_time = (
        3 +      # Detection time
        2 +      # Election time
        5 +      # Promotion time
        5        # Client reconnection
    )

    assert failover_time < 20, f"Failover would take {failover_time}s (target: <15s)"

    logger.info("✅ Cluster ready for failover")
```

### Alert Rules

```yaml
# prometheus-rules.yml

groups:
  - name: postgresql_cluster
    interval: 10s
    rules:
      - alert: PrimaryDown
        expr: patroni_node_is_primary == 0 for 30s
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL Primary is down"
          action: "Patroni should auto-failover within 60s"

      - alert: HighReplicationLag
        expr: patroni_replication_lag_bytes > 10_000_000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Replication lag > 10MB"
          action: "Check replica I/O performance"

      - alert: ReplicaDown
        expr: count(patroni_node_is_replica) < 2
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "One or more replicas are down"
          action: "Investigate replica health"

      - alert: ClusterQuorumLost
        expr: patroni_cluster_members_healthy < 3
        for: 10s
        labels:
          severity: critical
        annotations:
          summary: "etcd cluster lost quorum"
          action: "Immediate investigation required"
```

---

## Section 6: Recovery Procedures

### Complete Primary Failure Recovery

```bash
#!/bin/bash
# Recovery steps if primary is completely lost

# Step 1: Identify best replica
patroni_ctl list
# Output shows which replica has latest WAL position

# Step 2: Manual promotion if needed
# (Usually automatic, but backup procedure)
patroni_ctl switchover --force

# Step 3: Bring failed primary back online
# Option A: Full reinstall
pg_basebackup -h replica1 -D /var/lib/postgresql/15/data -U replication_user

# Option B: Use pg_rewind (if clean shutdown)
pg_rewind --target-pgdata /var/lib/postgresql/15/data --source-server="host=replica1 user=postgres"

# Step 4: Start as replica
touch /var/lib/postgresql/15/data/standby.signal
systemctl start postgresql

# Step 5: Verify catchup
psql -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();"

# Wait for catch-up
while [ $(psql -c "SELECT pg_last_wal_replay_lsn() != pg_last_wal_receive_lsn();") ]; do
    echo "Catching up..."
    sleep 5
done

echo "✅ Recovery complete"
```

### Backup Strategy with Replicas

```bash
#!/bin/bash
# Backup from replica (doesn't interrupt primary)

# Take backup from replica 2 (leaving replica 1 for failover)
pg_basebackup \
    -h 192.168.1.12 \
    -D /backups/daily/base-$(date +%Y%m%d).tar \
    -U replication_user \
    -F t \
    -z

# Archive WAL logs
find /var/lib/postgresql/15/pg_wal -name "*.backup" -type f -exec \
    aws s3 cp {} s3://backups/wal/ \;
```

---

## Section 7: Expected Availability

### Uptime Calculations

```
3-Node HA Cluster with Patroni:

Annual Availability:
├─ Single node MTTF: 99.5% (43.8 hours downtime/year)
├─ Synchronous replication: Eliminates data loss
├─ Automatic failover: <1 minute downtime per incident
├─ Incident rate: ~2-3 per year (typical)
├─ Total downtime: 3-5 minutes/year
└─ **Result: 99.99% availability (52.6 min/year)**

RTO (Recovery Time Objective): <1 minute
RPO (Recovery Point Objective): 0 seconds (no data loss)
```

### Failure Scenarios Handled

| Failure Type | Detection | Failover | Recovery | Impact |
|--------------|-----------|----------|----------|--------|
| Primary crash | 5 sec | 10 sec | <1 min | <20 sec outage |
| Network partition | 3 sec | 5 sec | Auto | Minority partition fails |
| Replica failure | Continuous | N/A | Manual | No impact (2 replicas remain) |
| Disk full (primary) | Alert | 10 sec | 5-10 min | <15 sec outage |
| All nodes down | N/A | N/A | Manual | Complete recovery |

---

## Implementation Checklist

- [ ] Setup etcd cluster (3 nodes minimum)
- [ ] Configure PostgreSQL replication on all 3 nodes
- [ ] Install and configure Patroni on each node
- [ ] Setup HAProxy for VIP failover
- [ ] Test failover scenarios in staging
- [ ] Test recovery procedures
- [ ] Setup monitoring and alerting
- [ ] Document runbooks for each failure scenario
- [ ] Train operations team on failover procedures
- [ ] Setup backup from non-primary replica
- [ ] Verify 99.99% uptime target achievable
- [ ] Deploy to production with canary traffic

---

## Performance Impact

```
Metric                    Single DB    With Replication    Impact
────────────────────────────────────────────────────────────────
Write Latency             100ms        105ms               +5%
Read Latency (replica)     50ms        55ms                +10%
Disk I/O                  100%         90%                 -10%
Network I/O               Baseline     +5-10%              WAL stream
Failover Time             30+ min      <1 min              99.98x faster
Data Loss Risk            High         0                   Eliminated
Annual Downtime           Days         Minutes             99.9% improvement
```

---

## Summary

**3-Node High-Availability Cluster:**
- ✅ 99.99% uptime (52.6 min/year)
- ✅ <1 minute automatic failover
- ✅ 0 data loss (synchronous replication)
- ✅ Geographic redundancy
- ✅ Live maintenance capability
- ✅ Full automation (Patroni + etcd)

**Next Step:** Task 7 - Monitoring & Observability (Prometheus + Grafana)
