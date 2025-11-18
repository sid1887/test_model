#!/usr/bin/env python3
"""
Comprehensive Test Orchestration Suite
Runs all tests with detailed reporting and actionable results
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class TestOrchestrator:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.summary = []

    def run_command(self, cmd, name, description):
        """Run command and capture output"""
        print(f"\n{'='*70}")
        print(f"📋 {name}")
        print(f"   {description}")
        print(f"{'='*70}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            status = "✓ PASSED" if result.returncode == 0 else "✗ FAILED"
            print(f"{status} | Return code: {result.returncode}")

            if result.stdout:
                print("\nOutput:")
                print(result.stdout[:2000])  # Truncate long output

            if result.stderr:
                print("\nErrors:")
                print(result.stderr[:1000])

            self.results[name] = {
                'status': 'PASSED' if result.returncode == 0 else 'FAILED',
                'returncode': result.returncode,
                'timestamp': datetime.now().isoformat()
            }

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("✗ TIMEOUT (exceeded 120 seconds)")
            self.results[name] = {'status': 'TIMEOUT'}
            return False
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.results[name] = {'status': 'ERROR', 'error': str(e)}
            return False

    def print_summary(self):
        """Print comprehensive test summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print(f"\n\n{'='*70}")
        print("📊 TEST EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"Total time: {elapsed:.1f}s")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        passed = sum(1 for r in self.results.values() if r['status'] == 'PASSED')
        total = len(self.results)

        print(f"\nResults: {passed}/{total} tests passed")

        print("\nDetailed Results:")
        for name, result in self.results.items():
            status_icon = "✓" if result['status'] == 'PASSED' else "✗"
            print(f"  {status_icon} {name}: {result['status']}")

        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")

        return passed == total

    def run_all_tests(self):
        """Run complete test suite"""
        print("\n🚀 Starting Comprehensive Test Suite")
        print(f"Workspace: {Path.cwd()}")

        # Test 1: System Integration
        self.run_command(
            "python test_full_system.py",
            "System Integration",
            "Verify all subsystems operational and integrated"
        )

        # Test 2: Retailer Performance
        self.run_command(
            "python test_retailers.py",
            "Retailer Performance",
            "Analyze individual retailer success rates and response times"
        )

        # Test 3: Bulk & Performance
        self.run_command(
            "python test_bulk_performance.py",
            "Bulk Processing & Performance",
            "Test bulk search, caching, and multi-retailer advanced filtering"
        )

        # Test 4: Multimodal Capabilities
        self.run_command(
            "python test_multimodal.py",
            "Multimodal Search Capabilities",
            "Verify image search, voice search, and endpoint readiness"
        )

        # Print final summary
        success = self.print_summary()
        return 0 if success else 1

def create_quick_start_script():
    """Create a quick reference guide"""
    guide = """
# QUICK START REFERENCE

## Run All Tests
```bash
python run_all_tests.py
```

## Run Individual Tests
```bash
python test_full_system.py         # Complete system validation
python test_retailers.py           # Retailer performance analysis
python test_bulk_performance.py    # Bulk search and caching
python test_multimodal.py          # Image/voice search capabilities
```

## Check Service Status
```bash
# Web Service (Port 8000)
curl http://localhost:8000/api/v1/health

# Scrapy Service (Port 5000)
curl http://localhost:5000/health

# Wrapper (Port 7000)
curl http://localhost:7000/health
```

## Search Examples
```bash
# Basic search
curl -X POST http://localhost:7000/api/search \\
  -H "Content-Type: application/json" \\
  -d '{"query":"laptop","retailers":["amazon"]}'

# Advanced filtering
curl -X POST http://localhost:7000/api/search/advanced \\
  -H "Content-Type: application/json" \\
  -d '{"query":"phone","retailers":["amazon","walmart"],"min_price":100,"max_price":500}'

# Bulk search
curl -X POST http://localhost:5000/api/search/bulk \\
  -H "Content-Type: application/json" \\
  -d '{"queries":["laptop","phone"],"sites":["amazon","walmart"]}'
```

## Debug Issues
```bash
# View web service logs
docker logs test_model-web-1 -f --tail 100

# View scrapy service logs
docker logs test_model-scrapy_scraper-1 -f --tail 100

# Check Redis cache
redis-cli
  > KEYS *
  > GET cache:laptop:amazon
  > FLUSHALL  (clear all cache)

# Check database
psql -h localhost -U postgres -d cumpair
  > SELECT * FROM products LIMIT 10;
```

## Known Issues & Solutions
See DEBUGGING_GUIDE.md for:
- Cache hit detection (currently 0%)
- Multi-retailer advanced filtering (returns 500)
- Retailer coverage optimization (14/17 returning 0)

## System Architecture
```
Frontend
  ↓
FastAPI Web Service (8000)
  ├→ CLIP Image Analysis
  ├→ EasyOCR Text Recognition
  ├→ Voice STT
  └→ Integration Wrapper (7000)
       ├→ Caching Layer (Redis)
       ├→ Price Filtering
       └→ Scrapy Service (5000)
            └→ 17 Retailers
```

## Performance Targets
| Metric | Current | Target |
|--------|---------|--------|
| Single search | 2-8s | <3s |
| Multi-retailer (3) | 4.7s | <5s |
| Cache hit response | N/A | <0.5s |
| Bulk job queueing | 0.1s | <0.2s |
| Retailer coverage | 3/17 | 8+/17 |

## Next Priorities
1. Fix cache hit detection (debug: DEBUGGING_GUIDE.md Issue 1)
2. Fix multi-retailer advanced filtering (debug: DEBUGGING_GUIDE.md Issue 2)
3. Optimize CSS selectors for remaining 14 retailers
4. Implement Selenium/Playwright for JS-heavy sites
5. Integrate 2Captcha for CAPTCHA-protected sites
"""

    with open('QUICK_START.md', 'w') as f:
        f.write(guide)
    print("✓ Created QUICK_START.md")

if __name__ == '__main__':
    # Create quick start guide
    create_quick_start_script()

    # Run test orchestrator
    orchestrator = TestOrchestrator()
    exit_code = orchestrator.run_all_tests()
    sys.exit(exit_code)
