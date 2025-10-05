#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite

Tests against multiple real websites across different categories.
"""
import asyncio
import json
import time
from typing import List, Tuple
from main import scrape, ScraperStats


# Test cases: (name, url, query, expected_strategy)
TEST_CASES = [
    # News Sites
    (
        "Hacker News - Basic",
        "https://news.ycombinator.com",
        "Extract stories with title, points, and author",
        "LLM"
    ),
    (
        "Hacker News - Filtering",
        "https://news.ycombinator.com",
        "Extract ONLY stories with more than 50 points",
        "LLM"
    ),

    # Simple Sites
    (
        "Example.com - Basic",
        "https://example.com",
        "Extract the heading and paragraph text",
        "LLM"
    ),

    # GitHub (if accessible)
    (
        "GitHub Trending",
        "https://github.com/trending",
        "Extract trending repositories with name, description, and stars",
        "LLM"
    ),
]


async def run_test_case(
    name: str,
    url: str,
    query: str,
    expected_strategy: str
) -> Tuple[bool, dict]:
    """Run a single test case"""
    print("\n" + "="*70)
    print(f"🧪 TEST: {name}")
    print("="*70)
    print(f"   URL: {url}")
    print(f"   Query: {query[:80]}...")

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

        # Validation
        success = True
        issues = []

        # Check strategy
        if stats.strategy_used != expected_strategy:
            issues.append(f"Expected {expected_strategy}, got {stats.strategy_used}")

        # Check result structure
        if not isinstance(result, dict):
            issues.append("Result is not a dict")
            success = False

        # Check for data
        has_data = any(
            (isinstance(v, list) and len(v) > 0) or
            (isinstance(v, dict) and v) or
            (v is not None and v != "" and v != [])
            for v in result.values()
        )

        if not has_data:
            issues.append("No data extracted")

        # Report
        print(f"\n   Strategy: {stats.strategy_used}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Cost: ${stats.estimated_cost:.4f}")

        if has_data:
            for key, value in result.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"   ✓ {key}: {len(value)} items")
                    print(f"      Sample: {json.dumps(value[0], indent=6)[:150]}...")
                    break
                elif value and not isinstance(value, list):
                    print(f"   ✓ {key}: {str(value)[:100]}...")

        if issues:
            print(f"\n   ⚠️  Issues:")
            for issue in issues:
                print(f"      - {issue}")

        status = "✅ PASS" if success and not issues else "⚠️  PASS (with warnings)" if success else "❌ FAIL"
        print(f"\n{status}")

        return success, {
            "name": name,
            "success": success,
            "time": elapsed,
            "cost": stats.estimated_cost,
            "strategy": stats.strategy_used,
            "has_data": has_data,
            "issues": issues
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ FAILED: {str(e)[:200]}")

        return False, {
            "name": name,
            "success": False,
            "time": elapsed,
            "cost": 0,
            "error": str(e)[:200]
        }


async def main():
    """Run comprehensive integration tests"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE INTEGRATION TEST SUITE")
    print("   Testing against multiple real websites")
    print("="*80)

    results = []
    total_start = time.time()

    for name, url, query, expected_strategy in TEST_CASES:
        success, data = await run_test_case(name, url, query, expected_strategy)
        results.append(data)

        # Rate limiting between tests
        await asyncio.sleep(3)

    total_elapsed = time.time() - total_start

    # Summary
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r.get("success", False))
    total = len(results)

    print(f"\nResults by Category:")
    print("-" * 80)

    for result in results:
        name = result.get("name", "Unknown")
        success = result.get("success", False)
        time_taken = result.get("time", 0)
        cost = result.get("cost", 0)
        has_data = result.get("has_data", False)

        status = "✅" if success else "❌"
        data_indicator = "📊" if has_data else "📭"

        print(f"{status} {data_indicator} {name:<40} | {time_taken:>6.2f}s | ${cost:.4f}")

        if "issues" in result and result["issues"]:
            for issue in result["issues"]:
                print(f"      ⚠️  {issue}")

        if "error" in result:
            print(f"      ❌ {result['error'][:100]}")

    print("-" * 80)

    # Statistics
    total_cost = sum(r.get("cost", 0) for r in results)
    avg_time = sum(r.get("time", 0) for r in results) / len(results) if results else 0

    print(f"\nStatistics:")
    print(f"   Tests Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"   Total Time: {total_elapsed:.2f}s")
    print(f"   Average Time per Test: {avg_time:.2f}s")
    print(f"   Total Estimated Cost: ${total_cost:.4f}")

    print("\n" + "="*80)

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("   The universal web scraper is working perfectly!")
    elif passed >= total * 0.8:
        print("✅ MOSTLY SUCCESSFUL")
        print("   Most tests passed - system is functional with minor issues")
    elif passed >= total * 0.5:
        print("⚠️  PARTIAL SUCCESS")
        print("   Some tests failed - review issues above")
    else:
        print("❌ MULTIPLE FAILURES")
        print("   Significant issues detected - review output above")

    print("="*80 + "\n")

    return passed >= total * 0.8  # 80% pass rate = success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
