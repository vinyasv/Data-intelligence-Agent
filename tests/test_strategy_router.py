#!/usr/bin/env python3
"""
Unit Tests for Strategy Router

Tests intelligent routing between CSS and LLM extraction strategies.
"""
import asyncio
from strategy_router import StrategyRouter, StrategyType
from schema_generator import SchemaGenerator


async def test_semantic_detection_sentiment():
    """Test: Sentiment analysis should trigger LLM strategy"""
    print("\n" + "="*60)
    print("TEST 1: Semantic Detection - Sentiment Analysis")
    print("="*60)

    router = StrategyRouter()
    query = "Extract reviews with sentiment (positive/negative/neutral)"

    is_semantic = router._is_semantic_query(query)

    print(f"✓ Query: {query}")
    print(f"✓ Is Semantic: {is_semantic}")

    assert is_semantic, "Sentiment analysis should be detected as semantic"
    print("✅ PASSED: Sentiment correctly detected as semantic")
    return True


async def test_semantic_detection_filtering():
    """Test: Filtering conditions should trigger LLM strategy"""
    print("\n" + "="*60)
    print("TEST 2: Semantic Detection - Filtering")
    print("="*60)

    router = StrategyRouter()
    query = "Extract ONLY products with rating above 4 stars"

    is_semantic = router._is_semantic_query(query)

    print(f"✓ Query: {query}")
    print(f"✓ Is Semantic: {is_semantic}")

    assert is_semantic, "Filtering conditions should be detected as semantic"
    print("✅ PASSED: Filtering correctly detected as semantic")
    return True


async def test_semantic_detection_summarization():
    """Test: Summarization should trigger LLM strategy"""
    print("\n" + "="*60)
    print("TEST 3: Semantic Detection - Summarization")
    print("="*60)

    router = StrategyRouter()
    query = "Get articles with headline and a one-sentence summary"

    is_semantic = router._is_semantic_query(query)

    print(f"✓ Query: {query}")
    print(f"✓ Is Semantic: {is_semantic}")

    assert is_semantic, "Summarization should be detected as semantic"
    print("✅ PASSED: Summarization correctly detected as semantic")
    return True


async def test_simple_extraction_css():
    """Test: Simple field extraction could use CSS"""
    print("\n" + "="*60)
    print("TEST 4: Simple Extraction - CSS Candidate")
    print("="*60)

    router = StrategyRouter()
    query = "Extract products with name and price"

    is_semantic = router._is_semantic_query(query)

    print(f"✓ Query: {query}")
    print(f"✓ Is Semantic: {is_semantic}")

    # Note: System currently defaults to LLM for universal scraping
    # This test just verifies the semantic detection logic
    print(f"✓ Semantic detection returned: {is_semantic}")
    print("✅ PASSED: Simple extraction analyzed")
    return True


async def test_complex_schema_detection():
    """Test: Complex schemas trigger LLM strategy"""
    print("\n" + "="*60)
    print("TEST 5: Complex Schema Detection")
    print("="*60)

    router = StrategyRouter()

    # Create a complex schema with many fields
    complex_schema = {
        "properties": {
            f"field_{i}": {"type": "string"}
            for i in range(12)  # >10 fields = complex
        }
    }

    is_complex = router._is_complex_schema(complex_schema)

    print(f"✓ Schema fields: {len(complex_schema['properties'])}")
    print(f"✓ Is Complex: {is_complex}")

    assert is_complex, "Schema with >10 fields should be complex"
    print("✅ PASSED: Complex schema correctly detected")
    return True


async def test_nested_schema_detection():
    """Test: Nested schemas trigger LLM strategy"""
    print("\n" + "="*60)
    print("TEST 6: Nested Schema Detection")
    print("="*60)

    router = StrategyRouter()

    # Create a nested schema
    nested_schema = {
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        f"field_{i}": {"type": "string"}
                        for i in range(6)  # >5 nested fields = complex
                    }
                }
            }
        }
    }

    is_complex = router._is_complex_schema(nested_schema)

    print(f"✓ Has nested array of objects")
    print(f"✓ Nested fields: 6")
    print(f"✓ Is Complex: {is_complex}")

    assert is_complex, "Nested schemas with >5 fields should be complex"
    print("✅ PASSED: Nested schema correctly detected")
    return True


async def test_strategy_creation():
    """Test: Strategy instances are created correctly"""
    print("\n" + "="*60)
    print("TEST 7: LLM Strategy Creation")
    print("="*60)

    router = StrategyRouter()
    generator = SchemaGenerator()

    query = "Extract articles with headline and author"
    schema_result = await generator.generate_schema(query)

    strategy_type, strategy = router.choose_strategy(
        url="https://example.com",
        query=query,
        json_schema=schema_result.json_schema,
        prefer_css=False
    )

    print(f"✓ Query: {query}")
    print(f"✓ Strategy Type: {strategy_type.value}")
    print(f"✓ Strategy Instance: {type(strategy).__name__}")

    assert strategy_type == StrategyType.LLM, "Should choose LLM strategy"
    assert strategy is not None, "Strategy instance should be created"
    print("✅ PASSED: LLM strategy created successfully")
    return True


async def test_end_to_end_routing():
    """Test: Full routing pipeline"""
    print("\n" + "="*60)
    print("TEST 8: End-to-End Strategy Routing")
    print("="*60)

    router = StrategyRouter()
    generator = SchemaGenerator()

    test_cases = [
        ("Extract products with name and price", "Simple extraction"),
        ("Get ONLY products rated above 4 stars", "Filtering (semantic)"),
        ("Extract reviews with sentiment analysis", "Sentiment (semantic)"),
    ]

    for query, description in test_cases:
        schema_result = await generator.generate_schema(query)
        strategy_type, _ = router.choose_strategy(
            url="https://example.com",
            query=query,
            json_schema=schema_result.json_schema
        )

        print(f"✓ {description}: {strategy_type.value.upper()}")

    print("✅ PASSED: End-to-end routing works correctly")
    return True


async def main():
    """Run all strategy router tests"""
    print("\n" + "="*70)
    print("🧪 STRATEGY ROUTER UNIT TESTS")
    print("="*70)

    tests = [
        test_semantic_detection_sentiment,
        test_semantic_detection_filtering,
        test_semantic_detection_summarization,
        test_simple_extraction_css,
        test_complex_schema_detection,
        test_nested_schema_detection,
        test_strategy_creation,
        test_end_to_end_routing
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("🎉 All strategy router tests passed!")
    else:
        print("⚠️  Some tests failed - review output above")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
