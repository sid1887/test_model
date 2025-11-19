# Performance Testing Suite: Locust Load Tests

**Phase:** 6 - Database Optimization
**Objective:** Validate 9x latency improvement and 5x throughput increase
**Target:** Test 10,000+ concurrent users, measure baseline vs optimized

---

## Overview: Testing Strategy

```
Phase 6 Optimization Claims:
├─ 9x latency improvement (450ms → 50ms P99)
├─ 5x throughput increase (500 → 2,500 req/sec)
├─ 80%+ cache hit rate
├─ 8-10x database throughput
└─ 99.99% uptime

Validation Method: Locust Load Testing
├─ Ramp up from 10 to 10,000 concurrent users
├─ Run for 30 minutes
├─ Measure latency, throughput, errors
├─ Compare to baseline
└─ Generate performance report
```

---

## Section 1: Locust Installation & Setup

### Install Locust

```bash
pip install locust
pip install locust-kubernetes    # For distributed testing
```

### Project Structure

```
tests/
├── locustfile.py               # Main test suite
├── tasks.py                    # User behavior tasks
├── payloads.py                 # Test data
└── reports/
    ├── baseline-report.html    # Baseline performance
    ├── optimized-report.html   # After optimization
    └── comparison.csv          # Side-by-side metrics
```

---

## Section 2: Locust Test File (locustfile.py)

```python
from locust import HttpUser, TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import time

# Test data
SEARCH_QUERIES = [
    "laptop", "phone", "tablet", "camera", "headphones",
    "monitor", "keyboard", "mouse", "desk", "chair"
]

PRODUCT_IDS = [str(i) for i in range(1, 10001)]

USER_IDS = [str(i) for i in range(1, 1001)]

REGIONS = ["US", "UK", "EU", "APAC", "LATAM"]


class SearchTasks(TaskSet):
    """Tasks for search service (8010)"""

    @task(10)
    def search_products(self):
        """Full-text search"""
        query = random.choice(SEARCH_QUERIES)
        start_time = time.time()

        with self.client.get(
            f"/api/search?q={query}",
            catch_response=True
        ) as response:
            elapsed_time = (time.time() - start_time) * 1000  # ms

            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)
    def semantic_search(self):
        """Semantic search with embeddings"""
        query = random.choice(SEARCH_QUERIES)

        with self.client.get(
            f"/api/search/semantic?q={query}&limit=20",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(8)
    def autocomplete(self):
        """Autocomplete queries"""
        query_prefix = random.choice(SEARCH_QUERIES)[:3]

        with self.client.get(
            f"/api/search/autocomplete?prefix={query_prefix}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def trending_products(self):
        """Get trending products"""
        with self.client.get(
            f"/api/search/trending",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def faceted_search(self):
        """Faceted search with filters"""
        query = random.choice(SEARCH_QUERIES)

        with self.client.get(
            f"/api/search/faceted?q={query}&category=electronics&price_min=100&price_max=500",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class UserTasks(TaskSet):
    """Tasks for user service (8011)"""

    @task(10)
    def get_user_profile(self):
        """Get user profile"""
        user_id = random.choice(USER_IDS)

        with self.client.get(
            f"/api/users/{user_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(8)
    def get_wishlist(self):
        """Get user wishlist"""
        user_id = random.choice(USER_IDS)

        with self.client.get(
            f"/api/users/{user_id}/wishlist",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)
    def add_to_wishlist(self):
        """Add product to wishlist"""
        user_id = random.choice(USER_IDS)
        product_id = random.choice(PRODUCT_IDS)

        with self.client.post(
            f"/api/users/{user_id}/wishlist",
            json={"product_id": product_id},
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def get_recommendations(self):
        """Get personalized recommendations"""
        user_id = random.choice(USER_IDS)

        with self.client.get(
            f"/api/users/{user_id}/recommendations",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(4)
    def get_purchase_history(self):
        """Get user purchase history"""
        user_id = random.choice(USER_IDS)

        with self.client.get(
            f"/api/users/{user_id}/purchases",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class GeolocationTasks(TaskSet):
    """Tasks for geolocation service (8012)"""

    @task(10)
    def get_region_products(self):
        """Get products for region"""
        region = random.choice(REGIONS)

        with self.client.get(
            f"/api/regions/{region}/products",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(8)
    def get_regional_pricing(self):
        """Get pricing for region"""
        product_id = random.choice(PRODUCT_IDS)
        region = random.choice(REGIONS)

        with self.client.get(
            f"/api/products/{product_id}/pricing/{region}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)
    def detect_location(self):
        """Detect user location"""
        with self.client.get(
            f"/api/location/detect",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(7)
    def search_by_region(self):
        """Search products in region"""
        region = random.choice(REGIONS)
        query = random.choice(SEARCH_QUERIES)

        with self.client.get(
            f"/api/regions/{region}/search?q={query}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class SearchServiceUser(FastHttpUser):
    """Search service load test user"""
    wait_time = between(0.5, 2.0)  # Wait 0.5-2s between requests
    tasks = [SearchTasks]
    host = "http://localhost:8010"


class UserServiceUser(FastHttpUser):
    """User service load test user"""
    wait_time = between(1, 3)
    tasks = [UserTasks]
    host = "http://localhost:8011"


class GeolocationServiceUser(FastHttpUser):
    """Geolocation service load test user"""
    wait_time = between(0.5, 2.0)
    tasks = [GeolocationTasks]
    host = "http://localhost:8012"


class CombinedServiceUser(FastHttpUser):
    """Combined workload across all services"""
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Initialize user"""
        self.service = random.choice(['search', 'user', 'geo'])

    @task(40)
    def search_tasks(self):
        """40% of traffic to search"""
        task = SearchTasks(self)
        task.search_products()

    @task(35)
    def user_tasks(self):
        """35% of traffic to user"""
        task = UserTasks(self)
        task.get_user_profile()

    @task(25)
    def geo_tasks(self):
        """25% of traffic to geo"""
        task = GeolocationTasks(self)
        task.get_region_products()

    host = "http://localhost"
```

---

## Section 3: Load Profile Configurations

### Configuration 1: Baseline (Current Performance)

```bash
#!/bin/bash
# Run baseline test against un-optimized system

locust \
    -f locustfile.py \
    --headless \
    -u 1000 \
    -r 50 \
    -t 30m \
    --host=http://localhost:8010 \
    --csv=reports/baseline \
    --loglevel=INFO
```

**Expected Baseline Results:**
- Throughput: ~500 req/s
- P99 Latency: 450ms
- Error rate: 5-10%
- Cache hit ratio: 20%

### Configuration 2: Optimized (After Phase 6)

```bash
#!/bin/bash
# Run optimized test against optimized system

locust \
    -f locustfile.py \
    --headless \
    -u 10000 \
    -r 500 \
    -t 30m \
    --host=http://localhost \
    --csv=reports/optimized \
    --loglevel=INFO
```

**Expected Optimized Results:**
- Throughput: 2,500+ req/s
- P99 Latency: 50ms
- Error rate: <0.5%
- Cache hit ratio: 80%

### Configuration 3: Stress Test (Find Limits)

```bash
#!/bin/bash
# Stress test to find breaking point

locust \
    -f locustfile.py \
    --headless \
    -u 50000 \
    -r 5000 \
    -t 15m \
    --host=http://localhost \
    --csv=reports/stress \
    --loglevel=WARNING
```

**Purpose:** Identify maximum capacity before degradation

---

## Section 4: Performance Analysis Script

```python
# analyze_performance.py

import csv
import json
from datetime import datetime
from statistics import mean, median, stdev

def analyze_csv_report(filename):
    """Analyze Locust CSV report"""

    stats = {
        'total_requests': 0,
        'total_failures': 0,
        'endpoints': {},
        'latencies': [],
        'response_times': []
    }

    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            endpoint = row['Name']
            num_requests = int(row['# requests'])
            num_failures = int(row['# failures'])
            avg_response = float(row['Average Response Time'])
            p95_response = float(row['95%'])
            p99_response = float(row['99%'])

            stats['total_requests'] += num_requests
            stats['total_failures'] += num_failures

            stats['endpoints'][endpoint] = {
                'requests': num_requests,
                'failures': num_failures,
                'error_rate': num_failures / num_requests if num_requests > 0 else 0,
                'avg_latency_ms': avg_response,
                'p95_latency_ms': p95_response,
                'p99_latency_ms': p99_response
            }

            stats['response_times'].append(avg_response)

    stats['overall_error_rate'] = stats['total_failures'] / stats['total_requests']
    stats['avg_latency'] = mean(stats['response_times'])
    stats['median_latency'] = median(stats['response_times'])

    return stats

def compare_reports(baseline_file, optimized_file):
    """Compare baseline vs optimized performance"""

    baseline = analyze_csv_report(baseline_file)
    optimized = analyze_csv_report(optimized_file)

    print("=" * 80)
    print("PERFORMANCE COMPARISON: Baseline vs Optimized")
    print("=" * 80)

    print("\n📊 OVERALL METRICS:")
    print(f"  Total Requests:")
    print(f"    Baseline:  {baseline['total_requests']:,}")
    print(f"    Optimized: {optimized['total_requests']:,}")
    print(f"    Improvement: {(optimized['total_requests'] / baseline['total_requests']):.1f}x")

    print(f"\n  Error Rate:")
    print(f"    Baseline:  {baseline['overall_error_rate']:.2%}")
    print(f"    Optimized: {optimized['overall_error_rate']:.2%}")
    print(f"    Improvement: {baseline['overall_error_rate'] / optimized['overall_error_rate']:.1f}x better")

    print(f"\n  Average Latency:")
    print(f"    Baseline:  {baseline['avg_latency']:.0f}ms")
    print(f"    Optimized: {optimized['avg_latency']:.0f}ms")
    print(f"    Improvement: {baseline['avg_latency'] / optimized['avg_latency']:.1f}x faster")

    print("\n📍 ENDPOINT COMPARISON:")
    print(f"{'Endpoint':<40} {'Baseline P99':<15} {'Optimized P99':<15} {'Improvement':<15}")
    print("-" * 85)

    for endpoint in baseline['endpoints']:
        if endpoint in optimized['endpoints']:
            baseline_p99 = baseline['endpoints'][endpoint]['p99_latency_ms']
            optimized_p99 = optimized['endpoints'][endpoint]['p99_latency_ms']
            improvement = baseline_p99 / optimized_p99

            print(f"{endpoint:<40} {baseline_p99:<15.0f} {optimized_p99:<15.0f} {improvement:<15.1f}x")

    print("\n✅ VALIDATION RESULTS:")

    # Check 9x latency improvement
    latency_improvement = baseline['avg_latency'] / optimized['avg_latency']
    print(f"  Latency Improvement: {latency_improvement:.1f}x (Target: 9x) {'✅' if latency_improvement >= 8 else '❌'}")

    # Check 5x throughput increase
    throughput_improvement = optimized['total_requests'] / baseline['total_requests']
    print(f"  Throughput Improvement: {throughput_improvement:.1f}x (Target: 5x) {'✅' if throughput_improvement >= 5 else '❌'}")

    # Check error rate < 1%
    error_rate = optimized['overall_error_rate']
    print(f"  Error Rate: {error_rate:.2%} (Target: <1%) {'✅' if error_rate < 0.01 else '❌'}")

    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'baseline_stats': baseline,
        'optimized_stats': optimized,
        'improvements': {
            'latency_improvement': latency_improvement,
            'throughput_improvement': throughput_improvement,
            'error_rate': error_rate
        }
    }

    with open('reports/comparison-report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print("\n📄 Full report saved to reports/comparison-report.json")

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print("Usage: python analyze_performance.py <baseline.csv> <optimized.csv>")
        sys.exit(1)

    compare_reports(sys.argv[1], sys.argv[2])
```

---

## Section 5: Running the Tests

### Step 1: Baseline Test (Un-optimized)

```bash
# Terminal 1: Run baseline
./run_baseline.sh

# Monitor in real-time
# Open browser: http://localhost:8089
```

### Step 2: Implement Optimizations (Phase 6 Tasks 1-7)

```bash
# Apply all optimizations:
# - Indexes (INDEX_STRATEGY.sql)
# - Query optimization (QUERY_OPTIMIZATION_REPORT.md)
# - Caching (CACHING_ARCHITECTURE.md)
# - Connection pooling (CONNECTION_POOL_CONFIG.md)
# - Replication (REPLICATION_HA_STRATEGY.md)
# - Monitoring (MONITORING_OBSERVABILITY.md)
```

### Step 3: Optimized Test

```bash
# Terminal 2: Run optimized test
./run_optimized.sh

# Monitor in real-time
# Open browser: http://localhost:8089
```

### Step 4: Analyze Results

```bash
python analyze_performance.py \
    reports/baseline_stats.csv \
    reports/optimized_stats.csv
```

**Expected Output:**
```
================================================================================
PERFORMANCE COMPARISON: Baseline vs Optimized
================================================================================

📊 OVERALL METRICS:
  Total Requests:
    Baseline:  1,500,000
    Optimized: 7,500,000
    Improvement: 5.0x

  Error Rate:
    Baseline:  8.50%
    Optimized: 0.25%
    Improvement: 34.0x better

  Average Latency:
    Baseline:  450ms
    Optimized: 50ms
    Improvement: 9.0x faster

✅ VALIDATION RESULTS:
  Latency Improvement: 9.0x (Target: 9x) ✅
  Throughput Improvement: 5.0x (Target: 5x) ✅
  Error Rate: 0.25% (Target: <1%) ✅
```

---

## Section 6: Continuous Performance Testing

### Scheduled Tests (Cron)

```bash
# /etc/cron.d/performance-tests

# Weekly baseline test (Sunday 2 AM)
0 2 * * 0 /home/ubuntu/tests/run_weekly_baseline.sh

# Daily optimization verification (Daily 3 AM)
0 3 * * * /home/ubuntu/tests/run_daily_optimized.sh

# Stress test (Monthly 1st, 4 AM)
0 4 1 * * /home/ubuntu/tests/run_monthly_stress.sh
```

### CI/CD Integration

```yaml
# .github/workflows/performance-tests.yml

name: Performance Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services to be ready
        run: sleep 30

      - name: Run performance tests
        run: |
          pip install locust
          locust -f tests/locustfile.py \
            --headless \
            -u 10000 \
            -r 500 \
            -t 30m \
            --csv=test-results/optimized

      - name: Analyze results
        run: python tests/analyze_performance.py

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-results
          path: test-results/
```

---

## Section 7: Locust Web UI (Interactive)

```bash
# Run with web UI (interactive)
locust -f locustfile.py --host=http://localhost
```

**Then open:** http://localhost:8089

**Features:**
- Real-time graphs of requests/responses
- Response time distribution
- Failures/errors tracking
- Live worker coordination
- Pause/resume/stop tests
- Export reports

---

## Section 8: Expected Test Results

### Baseline (Before Optimization)

```
Total Requests: 1,500,000 (30 min test)
Throughput: 500 req/sec
Error Rate: 8.5%
Response Time Distribution:
  Min: 50ms
  Median: 300ms
  P95: 800ms
  P99: 1,200ms
  Max: 5,000ms

Endpoints Performance (Sample):
  GET /api/search: P99=1,200ms
  GET /api/users/{id}: P99=800ms
  GET /api/regions/{region}/products: P99=900ms
```

### Optimized (After Phase 6)

```
Total Requests: 7,500,000 (30 min test)
Throughput: 2,500 req/sec
Error Rate: 0.25%
Response Time Distribution:
  Min: 5ms
  Median: 30ms
  P95: 80ms
  P99: 150ms
  Max: 500ms

Endpoints Performance (Sample):
  GET /api/search: P99=150ms (8x faster)
  GET /api/users/{id}: P99=50ms (16x faster)
  GET /api/regions/{region}/products: P99=80ms (11x faster)
```

---

## Implementation Checklist

- [ ] Install Locust and dependencies
- [ ] Create locustfile.py with all service tasks
- [ ] Define realistic user behavior patterns
- [ ] Create baseline test configuration
- [ ] Create optimized test configuration
- [ ] Create stress test configuration
- [ ] Run 30-minute baseline test
- [ ] Document baseline metrics
- [ ] Implement all Phase 6 optimizations
- [ ] Run 30-minute optimized test
- [ ] Run analysis script
- [ ] Generate comparison report
- [ ] Verify 9x latency improvement ✅
- [ ] Verify 5x throughput increase ✅
- [ ] Verify <1% error rate ✅
- [ ] Setup weekly automated tests
- [ ] Setup CI/CD performance gate

---

## Performance Test Summary

**Objective:** Validate Phase 6 optimizations achieved target metrics
**Approach:** Locust-based load testing with before/after comparison
**Scope:** All 60+ endpoints across search, user, geolocation services
**Duration:** 30-minute load tests for statistical significance
**Metrics:** Latency (P50/P95/P99), throughput, error rate, cache hit ratio
**Success Criteria:** 9x latency improvement, 5x throughput, <1% errors

**Next Step:** Task 9 - Backup & Recovery Strategy
