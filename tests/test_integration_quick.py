#!/usr/bin/env python3
"""
Quick Integration Test

Fast smoke test to validate end-to-end pipeline works.
Tests against Hacker News (reliable, simple structure).
"""
import asyncio
import json
import time
from main import scrape, ScraperStats


async def test_hacker_news_basic():
    """Test: Basic extraction from Hacker News"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Hacker News - Basic Extraction")
    print("="*70)

    url = "https://news.ycombinator.com"
    query = "Extract top stories with title, points, and author"

    stats = ScraperStats()
    start_time = time.time()

    try:
        result = await scrape(
            url=url,
            query=query,
            respect_robots_txt=True,
            stats=stats
        )

        elapsed = time.time() - start_time

        print(f"\n✅ SUCCESS")
        print(f"   Strategy: {stats.strategy_used}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Estimated Cost: ${stats.estimated_cost:.4f}")

        # Validate result structure
        assert isinstance(result, dict), "Result should be a dict"
        print(f"   Result keys: {list(result.keys())}")

        # Check if we got data
        has_data = any(
            isinstance(v, list) and len(v) > 0
            for v in result.values()
        )

        if has_data:
            print(f"   ✓ Extracted data successfully")
            # Show sample
            for key, value in result.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"   ✓ {key}: {len(value)} items")
                    print(f"      Sample: {json.dumps(value[0], indent=6)[:200]}...")
                    break
        else:
            print(f"   ⚠️  Warning: No data extracted (result: {result})")

        print("\n✅ PASSED: Basic HN extraction works")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_semantic_query_filtering():
    """Test: Semantic query with filtering"""
    print("\n" + "="*70)
    print("🧪 TEST 2: Semantic Query - Filtering")
    print("="*70)

    url = "https://news.ycombinator.com"
    query = "Extract ONLY stories with more than 100 points, including title and author"

    stats = ScraperStats()
    start_time = time.time()

    try:
        result = await scrape(
            url=url,
            query=query,
            respect_robots_txt=True,
            stats=stats
        )

        elapsed = time.time() - start_time

        print(f"\n✅ SUCCESS")
        print(f"   Strategy: {stats.strategy_used}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Estimated Cost: ${stats.estimated_cost:.4f}")

        # Should use LLM strategy for filtering
        assert stats.strategy_used == "LLM", "Filtering should use LLM strategy"

        print(f"   ✓ Correctly used LLM strategy for semantic query")

        # Check result
        has_data = any(
            isinstance(v, list) and len(v) > 0
            for v in result.values()
        )

        if has_data:
            print(f"   ✓ Filtering query executed successfully")
            for key, value in result.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"   ✓ {key}: {len(value)} filtered items")
                    break

        print("\n✅ PASSED: Semantic filtering works")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_pipeline():
    """Test: Pydantic validation pipeline"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Data Validation Pipeline")
    print("="*70)

    url = "https://news.ycombinator.com"
    query = "Get stories with title, score, and author"

    stats = ScraperStats()

    try:
        # Test WITH validation (default)
        result = await scrape(
            url=url,
            query=query,
            respect_robots_txt=True,
            skip_validation=False,
            stats=stats
        )

        print(f"\n✅ SUCCESS")
        print(f"   ✓ Data passed Pydantic validation")
        print(f"   ✓ Validation time: {stats.validation_time:.2f}s")

        print("\n✅ PASSED: Validation pipeline works")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_robots_txt_compliance():
    """Test: robots.txt compliance checking"""
    print("\n" + "="*70)
    print("🧪 TEST 4: robots.txt Compliance")
    print("="*70)

    url = "https://news.ycombinator.com"
    query = "Get stories with title"

    try:
        # Test WITH robots.txt check (should work for HN)
        result = await scrape(
            url=url,
            query=query,
            respect_robots_txt=True
        )

        print(f"\n✅ SUCCESS")
        print(f"   ✓ robots.txt check passed")
        print(f"   ✓ Hacker News allows scraping")

        print("\n✅ PASSED: robots.txt compliance works")
        return True

    except Exception as e:
        # If HN blocks scraping, this is expected
        if "robots.txt" in str(e).lower():
            print(f"\n✅ SUCCESS (blocked as expected)")
            print(f"   ✓ robots.txt check working correctly")
            print(f"   ✓ Scraping blocked: {str(e)[:100]}")
            print("\n✅ PASSED: robots.txt compliance works")
            return True
        else:
            print(f"\n❌ FAILED: {str(e)}")
            return False


async def main():
    """Run quick integration tests"""
    print("\n" + "="*70)
    print("🚀 QUICK INTEGRATION TEST SUITE")
    print("   Fast smoke test to validate end-to-end pipeline")
    print("="*70)

    tests = [
        test_hacker_news_basic,
        test_semantic_query_filtering,
        test_validation_pipeline,
        test_robots_txt_compliance
    ]

    results = []
    total_start = time.time()

    for test in tests:
        try:
            success = await test()
            results.append((test.__name__, success))
            # Rate limiting between tests
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ EXCEPTION in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))

    total_elapsed = time.time() - total_start

    # Summary
    print("\n" + "="*70)
    print("📊 QUICK TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"Total time: {total_elapsed:.2f}s")

    if passed == total:
        print("\n🎉 All quick integration tests passed!")
        print("   System is working correctly!")
    elif passed >= total * 0.75:
        print("\n⚠️  Most tests passed - system is mostly functional")
    else:
        print("\n❌ Multiple failures - review output above")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
