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

# Production URL (Web Unlocker-only endpoint)
PROD_URL = "https://data-intelligence-agent.fly.dev/api/scrape"

# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Simple Static Site",
        "url": "https://example.com",
        "query": "Extract the main heading text",
        "timeout": 60
    },
    {
        "name": "E-commerce - Abercrombie Product",
        "url": "https://www.abercrombie.com/shop/wd/p/premium-heavyweight-20-tee-58965824",
        "query": "Extract product name, price, and available colors",
        "timeout": 120
    },
    {
        "name": "E-commerce - Abercrombie Product List",
        "url": "https://www.abercrombie.com/shop/us/mens-tops",
        "query": "Extract first 5 products with name and price",
        "timeout": 120
    },
    {
        "name": "News Site - Hacker News",
        "url": "https://news.ycombinator.com",
        "query": "Extract top 5 stories with title and points",
        "timeout": 90
    },
    {
        "name": "News Site - BBC",
        "url": "https://www.bbc.com/news",
        "query": "Extract top 3 headlines",
        "timeout": 90
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
        # Make request to production API (Web Unlocker direct endpoint)
        async with httpx.AsyncClient(timeout=test_case.get('timeout', 60)) as client:
            response = await client.post(
                PROD_URL,
                json={
                    "url": test_case['url'],
                    "query": test_case['query']
                }
            )

            duration = time.time() - start_time
            result['duration'] = duration

            if response.status_code == 200:
                data = response.json()

                # Check if extraction succeeded
                if data.get("success"):
                    result['success'] = True
                    result['data'] = data['data']

                    print(f"✅ SUCCESS ({duration:.2f}s)")
                    print(f"   Data preview: {json.dumps(data['data'], indent=2)[:300]}...")
                else:
                    result['error'] = data.get('error', 'Unknown error')
                    print(f"❌ EXTRACTION FAILED")
                    print(f"   Error: {result['error']}")

            else:
                result['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ HTTP FAILED - Status: {response.status_code}")
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
    print("   Web Unlocker-Only Mode (No Playwright)")
    print("="*70)
    print(f"Target: {PROD_URL}")
    print(f"Tests: {len(TEST_CASES)}")

    # Run tests
    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}]")
        result = await test_scraping_endpoint(test_case)
        results.append(result)

        # Wait between tests to avoid rate limiting
        if i < len(TEST_CASES):
            print("\n⏸️  Waiting 5s before next test...")
            await asyncio.sleep(5)
    
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

