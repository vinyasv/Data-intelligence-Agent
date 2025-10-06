#!/usr/bin/env python3
"""
Test parallel race extraction
"""
import asyncio
import logging

# Set up logging to see race details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from main import scrape


async def test_race():
    """Test the race condition with a simple site"""

    print("\n" + "="*70)
    print("Testing Parallel Race Extraction")
    print("="*70)

    test_cases = [
        ("https://example.com", "Extract the main heading"),
        ("https://scrapeme.live/shop", "Get first 3 products with name and price"),
    ]

    for url, query in test_cases:
        print(f"\n🧪 Test: {url}")
        print(f"   Query: {query}")
        print("-" * 70)

        try:
            result = await scrape(
                url=url,
                query=query,
                respect_robots_txt=True,
                skip_validation=False,
                prefer_css=False
            )

            print(f"\n✅ SUCCESS!")
            print(f"   Result: {result}")

        except Exception as e:
            print(f"\n❌ FAILED: {e}")

        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_race())
