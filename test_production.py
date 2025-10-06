#!/usr/bin/env python3
"""
Production Scraping Test Suite
Tests the deployed scraper on Fly.io with various scenarios
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Production URL
PROD_URL = "https://data-intelligence-agent.fly.dev"

# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Simple News Site",
        "url": "https://news.ycombinator.com",
        "query": "Extract top 3 stories with title and points",
        "timeout": 60
    },
    {
        "name": "E-commerce Product Page",
        "url": "https://www.amazon.com/dp/B08N5WRWNW",
        "query": "Extract product name, price, and rating",
        "timeout": 90
    },
    {
        "name": "Wikipedia Article",
        "url": "https://en.wikipedia.org/wiki/Web_scraping",
        "query": "Extract the first paragraph and list any mentioned technologies",
        "timeout": 60
    },
    {
        "name": "GitHub Repository",
        "url": "https://github.com/scrapy/scrapy",
        "query": "Extract repository name, description, and star count",
        "timeout": 60
    },
    {
        "name": "Simple Static Site",
        "url": "https://example.com",
        "query": "Extract the main heading and any paragraphs",
        "timeout": 30
    }
]


async def test_health_check():
    """Test if the production service is up"""
    print("\n" + "="*70)
    print("🏥 HEALTH CHECK")
    print("="*70)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(PROD_URL)
            
            if response.status_code == 200:
                print(f"✅ Service is UP - Status: {response.status_code}")
                print(f"   Response size: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️  Service returned status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Service is DOWN - Error: {e}")
        return False


async def test_scraping_endpoint(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single scraping request"""
    print(f"\n{'─'*70}")
    print(f"🧪 Testing: {test_case['name']}")
    print(f"   URL: {test_case['url']}")
    print(f"   Query: {test_case['query']}")
    print(f"{'─'*70}")
    
    start_time = time.time()
    result = {
        "name": test_case['name'],
        "url": test_case['url'],
        "success": False,
        "error": None,
        "duration": 0,
        "data": None
    }
    
    try:
        # Make request to production API
        async with httpx.AsyncClient(timeout=test_case.get('timeout', 60)) as client:
            response = await client.post(
                f"{PROD_URL}/api/chat",
                json={
                    "message": f"Scrape {test_case['url']} and {test_case['query']}"
                }
            )
            
            duration = time.time() - start_time
            result['duration'] = duration
            
            if response.status_code == 200:
                data = response.json()
                result['success'] = True
                result['data'] = data
                
                print(f"✅ SUCCESS ({duration:.2f}s)")
                print(f"   Response preview: {str(data)[:200]}...")
                
            else:
                result['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        result['duration'] = duration
        result['error'] = f"Timeout after {duration:.2f}s"
        print(f"⏱️  TIMEOUT after {duration:.2f}s")
        
    except Exception as e:
        duration = time.time() - start_time
        result['duration'] = duration
        result['error'] = str(e)
        print(f"❌ ERROR: {e}")
    
    return result


async def run_production_tests():
    """Run all production tests"""
    print("\n" + "="*70)
    print("🚀 PRODUCTION SCRAPING TEST SUITE")
    print("="*70)
    print(f"Target: {PROD_URL}")
    print(f"Tests: {len(TEST_CASES)}")
    
    # Health check first
    is_healthy = await test_health_check()
    if not is_healthy:
        print("\n❌ Service is not healthy. Aborting tests.")
        return
    
    # Run tests
    results = []
    for test_case in TEST_CASES:
        result = await test_scraping_endpoint(test_case)
        results.append(result)
        
        # Wait between tests to avoid overloading
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_duration = sum(r['duration'] for r in successful) / len(successful)
        print(f"⏱️  Avg Duration: {avg_duration:.2f}s")
    
    if failed:
        print("\n❌ Failed Tests:")
        for result in failed:
            print(f"   • {result['name']}: {result['error']}")
    
    # Detailed results
    print("\n" + "="*70)
    print("📋 DETAILED RESULTS")
    print("="*70)
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"\n{status} - {result['name']}")
        print(f"   Duration: {result['duration']:.2f}s")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    print("\n" + "="*70)
    
    # Save results to file
    with open('production_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n💾 Results saved to: production_test_results.json")


if __name__ == "__main__":
    asyncio.run(run_production_tests())

