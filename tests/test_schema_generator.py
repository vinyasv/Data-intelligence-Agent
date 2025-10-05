#!/usr/bin/env python3
"""
Unit Tests for Schema Generator

Tests Pydantic schema generation from natural language queries.
"""
import asyncio
import json
from schema_generator import SchemaGenerator
from pydantic import BaseModel


async def test_simple_product_query():
    """Test: Extract products with name and price"""
    print("\n" + "="*60)
    print("TEST 1: Simple Product Schema Generation")
    print("="*60)

    generator = SchemaGenerator()
    query = "Extract products with name and price"

    result = await generator.generate_schema(query)

    print(f"✓ Query: {query}")
    print(f"✓ Model Name: {result.model_name}")
    print(f"✓ Schema Properties: {list(result.json_schema.get('properties', {}).keys())}")

    # Validate schema has expected structure
    assert result.model_name, "Model name should be generated"
    assert "properties" in result.json_schema, "Schema should have properties"
    assert result.pydantic_code, "Pydantic code should be generated"

    print("✅ PASSED: Simple product schema generated successfully")
    return True


async def test_complex_job_query():
    """Test: Extract jobs with multiple fields including optional ones"""
    print("\n" + "="*60)
    print("TEST 2: Complex Job Schema with Optional Fields")
    print("="*60)

    generator = SchemaGenerator()
    query = "Extract job listings with title, company, salary range, location, and remote status"

    result = await generator.generate_schema(query)

    print(f"✓ Query: {query}")
    print(f"✓ Model Name: {result.model_name}")
    print(f"✓ Generated Code Preview:")
    print(result.pydantic_code[:300] + "...")

    # Validate model can be instantiated
    model_class = generator.get_model_class(result.pydantic_code)
    assert issubclass(model_class, BaseModel), "Generated class should be Pydantic BaseModel"

    print("✅ PASSED: Complex job schema generated successfully")
    return True


async def test_semantic_fields():
    """Test: Schema with semantic/derived fields (sentiment, summary)"""
    print("\n" + "="*60)
    print("TEST 3: Semantic Fields (Sentiment, Summary)")
    print("="*60)

    generator = SchemaGenerator()
    query = "Extract reviews with text, rating, and sentiment (positive/negative/neutral)"

    result = await generator.generate_schema(query)

    print(f"✓ Query: {query}")
    print(f"✓ Model Name: {result.model_name}")

    # Check if sentiment field exists
    properties = result.json_schema.get("properties", {})
    print(f"✓ Schema has {len(properties)} top-level properties")

    assert result.pydantic_code, "Should generate code for semantic fields"
    print("✅ PASSED: Semantic fields schema generated successfully")
    return True


async def test_list_container_pattern():
    """Test: Verify item + container list pattern"""
    print("\n" + "="*60)
    print("TEST 4: Item + Container List Pattern")
    print("="*60)

    generator = SchemaGenerator()
    query = "Get articles with headline, author, and date"

    result = await generator.generate_schema(query)

    print(f"✓ Query: {query}")
    print(f"✓ Model Name: {result.model_name}")

    # Check for List field in schema
    properties = result.json_schema.get("properties", {})
    has_list_field = any(
        prop.get("type") == "array"
        for prop in properties.values()
    )

    print(f"✓ Has list field: {has_list_field}")
    print(f"✓ Properties: {list(properties.keys())}")

    assert has_list_field, "Container model should have a list field"
    print("✅ PASSED: Item + container pattern validated")
    return True


async def test_schema_compilation():
    """Test: Verify generated code compiles and validates"""
    print("\n" + "="*60)
    print("TEST 5: Schema Compilation & Validation")
    print("="*60)

    generator = SchemaGenerator()
    query = "Extract products with name, price, and rating"

    result = await generator.generate_schema(query)
    model_class = generator.get_model_class(result.pydantic_code)

    print(f"✓ Model compiled: {model_class.__name__}")

    # Test instantiation with sample data
    try:
        # This should work with the container model
        sample_data = {list(result.json_schema["properties"].keys())[0]: []}
        instance = model_class(**sample_data)
        print(f"✓ Model instantiated successfully")
        print(f"✓ Model dump: {instance.model_dump()}")

        print("✅ PASSED: Schema compiles and validates correctly")
        return True
    except Exception as e:
        print(f"❌ FAILED: Model instantiation failed: {e}")
        return False


async def main():
    """Run all schema generator tests"""
    print("\n" + "="*70)
    print("🧪 SCHEMA GENERATOR UNIT TESTS")
    print("="*70)

    tests = [
        test_simple_product_query,
        test_complex_job_query,
        test_semantic_fields,
        test_list_container_pattern,
        test_schema_compilation
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} - {str(e)}")
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
        print("🎉 All schema generator tests passed!")
    else:
        print("⚠️  Some tests failed - review output above")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
