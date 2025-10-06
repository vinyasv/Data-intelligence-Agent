#!/usr/bin/env python3
"""
Simple Production Test - Direct scraping without agent
"""
import asyncio
import sys
import subprocess
import json

# Test by calling the scraper subprocess directly with production environment
def test_simple_scrape():
    """Test basic scraping functionality"""
    print("="*70)
    print("🧪 SIMPLE PRODUCTION SCRAPING TEST")
    print("="*70)
    
    test_data = {
        "url": "https://example.com",
        "query": "Extract the heading and main text",
        "options": {
            "respect_robots_txt": True,
            "skip_validation": False,
            "prefer_css": False
        }
    }
    
    print(f"\n📍 Testing URL: {test_data['url']}")
    print(f"📝 Query: {test_data['query']}")
    print("\n⏳ Running scraper subprocess...\n")
    
    try:
        # Run scraper subprocess
        result = subprocess.run(
            ["python", "scraper_subprocess.py", json.dumps(test_data)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("📊 Exit Code:", result.returncode)
        print("\n" + "─"*70)
        print("📤 STDOUT:")
        print("─"*70)
        print(result.stdout)
        
        if result.stderr:
            print("\n" + "─"*70)
            print("⚠️  STDERR:")
            print("─"*70)
            print(result.stderr)
        
        # Parse result
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print("\n" + "="*70)
                print("✅ SCRAPING SUCCESSFUL")
                print("="*70)
                print(json.dumps(data, indent=2))
                return True
            except json.JSONDecodeError as e:
                print(f"\n❌ Failed to parse JSON: {e}")
                return False
        else:
            print("\n" + "="*70)
            print("❌ SCRAPING FAILED")
            print("="*70)
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ TIMEOUT: Scraper took longer than 60 seconds")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_scrape()
    sys.exit(0 if success else 1)

