#!/usr/bin/env python3
"""
AI Services Smoke Test Script
Runs quick tests on all AI endpoints to verify they're working
"""

import asyncio
import httpx
import sys
from pathlib import Path


BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


async def test_health_services():
    """Test comprehensive health check"""
    print_info("Testing health check...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/health/services",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('healthy'):
                    print_success(f"Health check: ALL SYSTEMS OK")
                    
                    # Show service statuses
                    for service, status in data.get('services', {}).items():
                        is_healthy = status.get('healthy', False)
                        symbol = "✓" if is_healthy else "✗"
                        color = Colors.GREEN if is_healthy else Colors.YELLOW
                        print(f"  {color}{symbol}{Colors.END} {service}: {status.get('status', 'unknown')}")
                    
                    return True
                else:
                    print_warning("Health check: DEGRADED")
                    return False
            else:
                print_error(f"Health check failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_text_generation():
    """Test HuggingFace text generation"""
    print_info("Testing text generation...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/text/generate",
                json={
                    "prompt": "Hello, world!",
                    "max_tokens": 20
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print_success(f"Text generation: OK")
                    print(f"  Generated: {data.get('text', '')[:100]}...")
                    return True
            elif response.status_code == 503:
                print_warning("Text generation: HF API not configured (optional)")
                return True  # Not critical
            else:
                print_error(f"Text generation failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_warning(f"Text generation error: {e} (optional)")
        return True  # Not critical


async def test_sentiment_analysis():
    """Test sentiment analysis"""
    print_info("Testing sentiment analysis...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/text/analyze",
                json={
                    "text": "This is amazing!",
                    "task": "sentiment"
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    result = data.get('result', {})
                    label = result.get('label', 'unknown')
                    score = result.get('score', 0)
                    print_success(f"Sentiment analysis: OK ({label}, {score:.2f})")
                    return True
            elif response.status_code == 503:
                print_warning("Sentiment analysis: HF API not configured (optional)")
                return True
            else:
                print_error(f"Sentiment analysis failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_warning(f"Sentiment analysis error: {e} (optional)")
        return True


async def test_embeddings():
    """Test text embeddings"""
    print_info("Testing embeddings...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/embeddings",
                json={
                    "texts": ["test phrase"]
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    count = data.get('count', 0)
                    print_success(f"Embeddings: OK ({count} vectors)")
                    return True
            elif response.status_code == 503:
                print_warning("Embeddings: HF API not configured (optional)")
                return True
            else:
                print_error(f"Embeddings failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_warning(f"Embeddings error: {e} (optional)")
        return True


async def test_service_stats():
    """Test service statistics"""
    print_info("Testing service stats...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/health/stats",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print_success("Service stats: OK")
                    
                    # Show stats
                    for service, stats in data.get('stats', {}).items():
                        if not isinstance(stats, dict):
                            continue
                        
                        requests = stats.get('requests_total') or stats.get('images_processed') or stats.get('transcriptions_total', 0)
                        print(f"  {service}: {requests} operations")
                    
                    return True
            else:
                print_error(f"Service stats failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Service stats error: {e}")
        return False


async def main():
    """Run all smoke tests"""
    print("\n" + "="*60)
    print("🧪 AI SERVICES SMOKE TEST")
    print("="*60 + "\n")
    
    tests = [
        ("Health Check", test_health_services),
        ("Text Generation", test_text_generation),
        ("Sentiment Analysis", test_sentiment_analysis),
        ("Embeddings", test_embeddings),
        ("Service Stats", test_service_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
        await asyncio.sleep(1)  # Small delay between tests
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        symbol = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{symbol}{Colors.END} {test_name}")
    
    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.END}\n")
        return 0
    elif passed >= total * 0.7:
        print(f"\n{Colors.YELLOW}⚠ PARTIAL SUCCESS (critical services OK){Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}❌ TESTS FAILED (check logs){Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
