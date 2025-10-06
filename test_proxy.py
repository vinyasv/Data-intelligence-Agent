#!/usr/bin/env python3
"""
Test Bright Data Proxy Connection

This script verifies the proxy is working by:
1. Making a request through the proxy
2. Checking what IP address is being used
3. Verifying proxy rotation
"""
import asyncio
from playwright.async_api import async_playwright
from config import settings

async def test_proxy():
    """Test proxy connection and rotation"""

    if not settings.PROXY_ENABLED:
        print("❌ Proxies are DISABLED")
        return

    print("🔍 Testing Bright Data Proxy Connection...")
    print(f"   Proxy: {settings.BRIGHTDATA_HOST}:{settings.BRIGHTDATA_PORT}")
    print(f"   Username: {settings.BRIGHTDATA_USERNAME}")
    print(f"   Rotation: {settings.PROXY_ROTATION}")
    print()

    async with async_playwright() as p:
        # Launch browser with proxy
        browser = await p.chromium.launch(
            proxy={
                "server": f"http://{settings.BRIGHTDATA_HOST}:{settings.BRIGHTDATA_PORT}",
                "username": settings.BRIGHTDATA_USERNAME,
                "password": settings.BRIGHTDATA_PASSWORD
            }
        )

        # Test 3 requests to verify rotation
        ips = []
        for i in range(3):
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            try:
                # Use ipinfo.io to check our IP
                await page.goto("https://ipinfo.io/json", timeout=30000)
                content = await page.content()

                # Extract IP from response
                import json
                data = json.loads(await page.text_content("pre"))
                ip = data.get("ip", "Unknown")
                city = data.get("city", "Unknown")
                region = data.get("region", "Unknown")
                country = data.get("country", "Unknown")
                org = data.get("org", "Unknown")

                ips.append(ip)

                print(f"Request {i+1}:")
                print(f"   IP: {ip}")
                print(f"   Location: {city}, {region}, {country}")
                print(f"   ISP: {org}")
                print()

            except Exception as e:
                print(f"❌ Request {i+1} failed: {e}")

            finally:
                await context.close()

        await browser.close()

        # Check rotation
        unique_ips = set(ips)
        print(f"📊 Results:")
        print(f"   Total requests: {len(ips)}")
        print(f"   Unique IPs: {len(unique_ips)}")

        if len(unique_ips) > 1:
            print(f"   ✅ Proxy rotation is WORKING!")
        elif len(unique_ips) == 1:
            print(f"   ⚠️  Same IP used (rotation might be disabled or session mode)")
        else:
            print(f"   ❌ No successful requests")

if __name__ == "__main__":
    asyncio.run(test_proxy())
