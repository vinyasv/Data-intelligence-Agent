#!/usr/bin/env python3
"""
Unit Tests for Extractor Alternative Data Sources

Tests JSON-LD, meta tag, and data attribute extraction.
"""
import json
from extractor import WebExtractor


def test_jsonld_extraction():
    """Test: Extract JSON-LD structured data"""
    print("\n" + "="*60)
    print("TEST 1: JSON-LD Extraction")
    print("="*60)

    extractor = WebExtractor()

    # Sample HTML with JSON-LD
    html = '''
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Wireless Mouse",
            "price": "29.99",
            "ratingValue": "4.5"
        }
        </script>
    </head>
    <body></body>
    </html>
    '''

    result = extractor._extract_jsonld(html)

    print(f"✓ Extracted JSON-LD: {result}")

    assert result is not None, "Should extract JSON-LD data"
    assert result.get("@type") == "Product", "Should identify Product type"
    assert result.get("name") == "Wireless Mouse", "Should extract name"

    print("✅ PASSED: JSON-LD extraction successful")
    return True


def test_jsonld_list_extraction():
    """Test: Extract JSON-LD with array of items"""
    print("\n" + "="*60)
    print("TEST 2: JSON-LD List Extraction")
    print("="*60)

    extractor = WebExtractor()

    # Sample HTML with JSON-LD array
    html = '''
    <html>
    <head>
        <script type="application/ld+json">
        [
            {
                "@type": "Article",
                "headline": "Test Article",
                "author": "John Doe"
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": []
            }
        ]
        </script>
    </head>
    <body></body>
    </html>
    '''

    result = extractor._extract_jsonld(html)

    print(f"✓ Extracted JSON-LD: {result}")

    assert result is not None, "Should extract from JSON-LD array"
    assert result.get("@type") == "Article", "Should find Article type in list"

    print("✅ PASSED: JSON-LD list extraction successful")
    return True


def test_meta_tag_extraction():
    """Test: Extract OpenGraph and meta tags"""
    print("\n" + "="*60)
    print("TEST 3: Meta Tag Extraction")
    print("="*60)

    extractor = WebExtractor()

    # Sample HTML with meta tags
    html = '''
    <html>
    <head>
        <meta property="og:title" content="Product Title">
        <meta property="og:description" content="Product Description">
        <meta property="og:price:amount" content="99.99">
        <meta name="description" content="Page description">
        <meta name="twitter:card" content="summary">
    </head>
    <body></body>
    </html>
    '''

    result = extractor._extract_meta_tags(html)

    print(f"✓ Extracted meta tags: {json.dumps(result, indent=2)}")

    assert result is not None, "Should extract meta tags"
    assert "og_title" in result, "Should extract OpenGraph title"
    assert "description" in result, "Should extract description"
    assert "twitter_card" in result, "Should extract Twitter card"

    print("✅ PASSED: Meta tag extraction successful")
    return True


def test_data_attribute_extraction():
    """Test: Extract data-* attributes"""
    print("\n" + "="*60)
    print("TEST 4: Data Attribute Extraction")
    print("="*60)

    extractor = WebExtractor()

    # Sample HTML with data attributes
    html = '''
    <html>
    <body>
        <div class="product"
             data-product-name="Laptop"
             data-product-price="1299.99"
             data-product-sku="LAP-001"
             data-price="1299.99"
             data-id="12345">
        </div>
    </body>
    </html>
    '''

    result = extractor._extract_data_attributes(html)

    print(f"✓ Extracted data attributes: {json.dumps(result, indent=2)}")

    assert result is not None, "Should extract data attributes"
    assert any("product" in key or "price" in key for key in result.keys()), \
        "Should extract product-related data attributes"

    print("✅ PASSED: Data attribute extraction successful")
    return True


def test_no_alternative_sources():
    """Test: Handle HTML with no alternative sources"""
    print("\n" + "="*60)
    print("TEST 5: No Alternative Sources")
    print("="*60)

    extractor = WebExtractor()

    # Plain HTML with no structured data
    html = '''
    <html>
    <head><title>Simple Page</title></head>
    <body><p>Just some text</p></body>
    </html>
    '''

    jsonld = extractor._extract_jsonld(html)
    meta = extractor._extract_meta_tags(html)
    data_attrs = extractor._extract_data_attributes(html)

    print(f"✓ JSON-LD: {jsonld}")
    print(f"✓ Meta tags: {meta}")
    print(f"✓ Data attrs: {data_attrs}")

    assert jsonld is None, "Should return None for no JSON-LD"
    # Meta and data attrs might return empty dict or None
    print("✅ PASSED: Correctly handles missing alternative sources")
    return True


def test_malformed_jsonld():
    """Test: Handle malformed JSON-LD gracefully"""
    print("\n" + "="*60)
    print("TEST 6: Malformed JSON-LD Handling")
    print("="*60)

    extractor = WebExtractor()

    # HTML with malformed JSON-LD
    html = '''
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Test",
            invalid json here
        }
        </script>
    </head>
    </html>
    '''

    result = extractor._extract_jsonld(html)

    print(f"✓ Malformed JSON-LD result: {result}")

    # Should return None or handle gracefully (no exception)
    print("✅ PASSED: Malformed JSON-LD handled gracefully")
    return True


def test_multiple_jsonld_scripts():
    """Test: Handle multiple JSON-LD scripts, prioritize relevant types"""
    print("\n" + "="*60)
    print("TEST 7: Multiple JSON-LD Scripts")
    print("="*60)

    extractor = WebExtractor()

    # HTML with multiple JSON-LD scripts
    html = '''
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@type": "Organization",
            "name": "Company Name"
        }
        </script>
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Main Product",
            "price": "49.99"
        }
        </script>
        <script type="application/ld+json">
        {
            "@type": "BreadcrumbList",
            "itemListElement": []
        }
        </script>
    </head>
    </html>
    '''

    result = extractor._extract_jsonld(html)

    print(f"✓ Extracted from multiple scripts: {result}")

    assert result is not None, "Should extract from one of the scripts"
    assert result.get("@type") in ["Product", "Organization"], \
        "Should prioritize relevant schema types"

    print("✅ PASSED: Multiple JSON-LD scripts handled correctly")
    return True


def main():
    """Run all extractor unit tests"""
    print("\n" + "="*70)
    print("🧪 EXTRACTOR ALTERNATIVE SOURCES UNIT TESTS")
    print("="*70)

    tests = [
        test_jsonld_extraction,
        test_jsonld_list_extraction,
        test_meta_tag_extraction,
        test_data_attribute_extraction,
        test_no_alternative_sources,
        test_malformed_jsonld,
        test_multiple_jsonld_scripts
    ]

    results = []
    for test in tests:
        try:
            success = test()
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
        print("🎉 All extractor tests passed!")
    else:
        print("⚠️  Some tests failed - review output above")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
