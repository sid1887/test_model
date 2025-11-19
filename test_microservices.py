#!/usr/bin/env python3
"""
Test microservices health and endpoints
"""
import requests
import time
import sys

SERVICES = {
    "api-gateway": "http://localhost:8000/api/v1/health",
    "ai-models": "http://localhost:8001/api/models/health",
    "hf-connector": "http://localhost:8002/api/hf/health",
    "speech-image": "http://localhost:8003/api/media/health",
    "feature-extract": "http://localhost:8004/api/features/health",
    "scrapy-wrapper": "http://localhost:8005/api/proxy/health",
}

def test_services(max_retries=3, timeout=5):
    """Test all services are healthy"""
    print("=" * 60)
    print("MICROSERVICES HEALTH CHECK")
    print("=" * 60)

    all_healthy = True
    for service_name, health_url in SERVICES.items():
        healthy = False
        for attempt in range(max_retries):
            try:
                resp = requests.get(health_url, timeout=timeout)
                if resp.status_code == 200:
                    print(f"✓ {service_name:20} HEALTHY (200 OK)")
                    healthy = True
                    break
                else:
                    print(f"✗ {service_name:20} HTTP {resp.status_code}")
            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    print(f"✗ {service_name:20} Connection refused (not running?)")
                time.sleep(1)
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    print(f"✗ {service_name:20} Timeout")
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"✗ {service_name:20} Error: {e}")

        if not healthy:
            all_healthy = False

    print("=" * 60)
    if all_healthy:
        print("✓ ALL SERVICES HEALTHY!")
        return 0
    else:
        print("✗ Some services not healthy")
        return 1

def test_gateway_routes():
    """Test API gateway can route to all services"""
    print("\n" + "=" * 60)
    print("GATEWAY ROUTING TEST")
    print("=" * 60)

    routes = {
        "/api/v1/models/detect": "POST",
        "/api/v1/hf/sentiment": "POST",
        "/api/v1/media/ocr": "POST",
        "/api/v1/features/embed": "POST",
        "/api/v1/proxy/search": "GET",
    }

    for route, method in routes.items():
        try:
            if method == "GET":
                resp = requests.get(f"http://localhost:8000{route}", timeout=5)
            else:
                resp = requests.post(f"http://localhost:8000{route}", json={}, timeout=5)

            status = "✓" if resp.status_code < 500 else "✗"
            print(f"{status} {method:4} {route:30} → {resp.status_code}")
        except Exception as e:
            print(f"✗ {method:4} {route:30} → ERROR: {e}")

if __name__ == "__main__":
    health_status = test_services()
    test_gateway_routes()
    sys.exit(health_status)
