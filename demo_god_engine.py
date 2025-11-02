"""
🔥 GOD ENGINE DEMO - Complete System Demonstration
Shows all features working together
"""

import asyncio
import httpx
import time
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def demo_unified_search():
    """Demo: Unified Search with AI Enrichment"""
    print("\n" + "="*80)
    print("🔥 DEMO 1: UNIFIED SEARCH - God Engine")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.time()
        
        response = await client.get(
            f"{BASE_URL}/api/v2/search",
            params={
                "q": "iPhone 15 Pro Max",
                "limit": 10,
                "use_cache": True,
                "use_vector": True,
                "enrich": True
            }
        )
        
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Search completed in {latency:.1f}ms")
            print(f"📊 Results: {len(data['results'])} products")
            print(f"💾 Cache Hit: {data['metadata'].get('cache_hit', False)}")
            print(f"🤖 AI Enriched: {data['metadata'].get('enriched', False)}")
            print(f"📡 Vector Search: {data['metadata'].get('vector_search_used', False)}")
            
            if data['results']:
                print(f"\n📦 Top Product:")
                product = data['results'][0]
                print(f"   Name: {product.get('name', 'N/A')}")
                print(f"   Price: ${product.get('current_price', 0):.2f}")
                print(f"   Retailer: {product.get('retailer', 'N/A')}")
            
            if "query_analysis" in data['metadata']:
                analysis = data['metadata']['query_analysis']
                print(f"\n🤖 AI Analysis:")
                print(f"   Sentiment: {analysis.get('sentiment', {}).get('label', 'N/A')}")
                print(f"   Category: {analysis.get('category', {}).get('labels', ['N/A'])[0] if analysis.get('category') else 'N/A'}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False


async def demo_streaming_search():
    """Demo: SSE Streaming Search with Ghost Results"""
    print("\n" + "="*80)
    print("🔥 DEMO 2: STREAMING SEARCH - Ghost → Real → Enriched")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "GET",
            f"{BASE_URL}/api/v2/search/stream",
            params={"q": "MacBook Pro", "limit": 5}
        ) as response:
            
            if response.status_code == 200:
                print("\n📡 Streaming results:")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        phase = data.get('phase')
                        
                        if phase == 'ghost':
                            print(f"   👻 Ghost results: {len(data.get('results', []))} placeholders")
                        elif phase == 'real':
                            print(f"   ✅ Real results: {len(data.get('results', []))} products")
                        elif phase == 'enriched':
                            print(f"   🤖 AI enrichment complete")
                        elif phase == 'realtime':
                            print(f"   📡 Real-time data loaded")
                        elif phase == 'complete':
                            print(f"   🎉 Stream complete!")
                
                return True
            else:
                print(f"❌ Streaming failed: {response.status_code}")
                return False


async def demo_service_health():
    """Demo: Service Health Monitoring"""
    print("\n" + "="*80)
    print("🔥 DEMO 3: SERVICE HEALTH MONITORING")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/health/services")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 System Status: {data.get('status', 'unknown').upper()}")
            print(f"⏱️  Response Time: {data.get('response_time_ms', 0):.1f}ms")
            
            services = data.get('services', {})
            healthy_count = sum(1 for s in services.values() if s.get('healthy'))
            total_count = len(services)
            
            print(f"\n🏥 Services: {healthy_count}/{total_count} healthy")
            
            for name, service in services.items():
                status = "✅" if service.get('healthy') else "❌"
                latency = service.get('latency_ms', 0)
                print(f"   {status} {name}: {latency:.1f}ms")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False


async def demo_cache_performance():
    """Demo: Multi-Tier Cache Performance"""
    print("\n" + "="*80)
    print("🔥 DEMO 4: CACHE PERFORMANCE TEST")
    print("="*80)
    
    query = "test_cache_performance"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # First request (cold - no cache)
        start1 = time.time()
        response1 = await client.get(
            f"{BASE_URL}/api/v2/search",
            params={"q": query, "limit": 5, "use_cache": True}
        )
        latency1 = (time.time() - start1) * 1000
        
        # Second request (warm - L2 cache)
        await asyncio.sleep(0.1)
        
        start2 = time.time()
        response2 = await client.get(
            f"{BASE_URL}/api/v2/search",
            params={"q": query, "limit": 5, "use_cache": True}
        )
        latency2 = (time.time() - start2) * 1000
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"\n📊 Cache Performance:")
            print(f"   1st Request (cold): {latency1:.1f}ms - Cache Hit: {data1['metadata'].get('cache_hit', False)}")
            print(f"   2nd Request (warm): {latency2:.1f}ms - Cache Hit: {data2['metadata'].get('cache_hit', False)}")
            print(f"   🚀 Speed Improvement: {((latency1 - latency2) / latency1 * 100):.1f}%")
            
            return True
        else:
            print(f"❌ Cache test failed")
            return False


async def demo_metrics():
    """Demo: Prometheus Metrics"""
    print("\n" + "="*80)
    print("🔥 DEMO 5: PROMETHEUS METRICS")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/metrics")
        
        if response.status_code == 200:
            metrics_text = response.text
            
            # Parse some key metrics
            lines = metrics_text.split('\n')
            
            print(f"\n📊 System Metrics:")
            
            for line in lines:
                if line.startswith('http_requests_total'):
                    print(f"   {line}")
                elif line.startswith('cache_hits_total'):
                    print(f"   {line}")
                elif line.startswith('cache_misses_total'):
                    print(f"   {line}")
                elif line.startswith('scrape_requests_total'):
                    print(f"   {line}")
                elif line.startswith('ai_inference_total'):
                    print(f"   {line}")
            
            print(f"\n✅ Metrics endpoint operational")
            return True
        else:
            print(f"❌ Metrics failed: {response.status_code}")
            return False


async def run_all_demos():
    """Run all demonstrations"""
    print("\n" + "🔥"*40)
    print("CUMPAIR GOD ENGINE - COMPLETE SYSTEM DEMONSTRATION")
    print("🔥"*40)
    
    print(f"\n⚙️  Testing against: {BASE_URL}")
    print(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    demos = [
        ("Service Health", demo_service_health),
        ("Unified Search", demo_unified_search),
        ("Streaming Search", demo_streaming_search),
        ("Cache Performance", demo_cache_performance),
        ("Metrics", demo_metrics)
    ]
    
    results = []
    
    for name, demo_func in demos:
        try:
            result = await demo_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            results.append((name, False))
        
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMONSTRATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\n🎯 Success Rate: {passed}/{total} ({(passed/total*100):.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL DEMONSTRATIONS PASSED!")
        print("🔥 GOD ENGINE IS FULLY OPERATIONAL!")
    else:
        print(f"\n⚠️  {total - passed} demonstration(s) failed")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(run_all_demos())
