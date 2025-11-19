#!/usr/bin/env python3
"""
Phase 7 Quick Start - One-Click Deployment Validation
Tests all services are working without Docker setup
"""

import asyncio
import httpx
import time
from datetime import datetime

# Service endpoints
SERVICES = {
    "Search (8010)": "http://localhost:8010",
    "Real-Time (8013)": "http://localhost:8013",
    "ML Engine (8014)": "http://localhost:8014",
    "Elasticsearch (8015)": "http://localhost:8015",
    "Event Bus (8016)": "http://localhost:8016",
}

async def test_service(name: str, url: str, endpoint: str = "/stats"):
    """Test single service"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{url}{endpoint}")
            if response.status_code == 200:
                return True, response.json()
            return False, f"Status {response.status_code}"
    except Exception as e:
        return False, str(e)

async def run_all_tests():
    """Run comprehensive validation"""
    print("=" * 70)
    print("PHASE 7 MICROSERVICES - QUICK START VALIDATION")
    print("=" * 70)
    print()

    # Test each service
    results = {}
    for name, url in SERVICES.items():
        print(f"Testing {name}...", end=" ", flush=True)
        success, data = await test_service(name, url)

        if success:
            print("✅ WORKING")
            results[name] = "✅"
        else:
            print("❌ FAILED")
            results[name] = "❌"
            print(f"  Error: {data}")

        await asyncio.sleep(0.5)

    print()
    print("=" * 70)
    print("SERVICE STATUS SUMMARY")
    print("=" * 70)

    total = len(results)
    working = sum(1 for v in results.values() if v == "✅")

    for name, status in results.items():
        print(f"{status} {name}")

    print()
    print(f"Overall: {working}/{total} services healthy")
    print()

    if working == total:
        print("🎉 All services operational!")
        print()
        print("Next steps:")
        print("  1. View Prometheus metrics: http://localhost:9090")
        print("  2. View Grafana dashboards: http://localhost:3000")
        print("  3. Test Search: curl 'http://localhost:8010/search?q=test'")
        print("  4. Test ML: curl 'http://localhost:8014/recommendations/trending'")
        print("  5. Test Events: curl -X POST 'http://localhost:8016/events/publish'")
        print()
    else:
        print("⚠️  Some services not responding")
        print("   Make sure Docker Compose is running:")
        print("   docker-compose -f docker-compose.phase7.yml up -d")
        print()

if __name__ == '__main__':
    print(f"\nStartup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    asyncio.run(run_all_tests())
