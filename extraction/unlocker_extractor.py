"""
Web Unlocker Extractor - HTTP-based extraction via Bright Data Web Unlocker API

This extractor bypasses bot detection using Web Unlocker API instead of browser automation.
Works in parallel with Playwright extraction for optimal speed/success ratio.
"""
import json
import httpx
from typing import Dict, Any, Optional
from anthropic import Anthropic

from config import settings
from utils import logger


class WebUnlockerExtractor:
    """
    HTTP-based extractor using Bright Data Web Unlocker API.

    Features:
    - Automatic CAPTCHA solving
    - Bot detection bypass
    - Proxy rotation
    - Returns raw HTML for LLM extraction
    """

    def __init__(
        self,
        anthropic_client: Anthropic,
        json_schema: Dict[str, Any],
        query: str
    ):
        self.client = anthropic_client
        self.json_schema = json_schema
        self.query = query
        self.model = settings.CLAUDE_MODEL

        # Web Unlocker config
        self.api_token = settings.UNLOCKER_API_TOKEN
        self.zone = settings.UNLOCKER_ZONE
        self.endpoint = settings.UNLOCKER_ENDPOINT
        self.timeout = settings.UNLOCKER_TIMEOUT

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from URL using Web Unlocker API.

        Args:
            url: Target URL to scrape

        Returns:
            Extracted data matching schema, or None if failed
        """
        if not self.api_token or not self.zone:
            logger.warning("Web Unlocker not configured - API token or zone missing")
            return None

        try:
            logger.info("🔓 Starting Web Unlocker extraction...")

            # Step 1: Fetch HTML via Web Unlocker API
            html = await self._fetch_via_unlocker(url)
            if not html:
                logger.error("   ❌ Web Unlocker returned empty content")
                return None

            logger.info(f"   ✅ Received HTML: {len(html)} bytes")

            # Step 2: Extract data using Claude (same as LLM strategy)
            extracted = await self._extract_with_llm(html)

            if extracted:
                logger.info("   ✅ Web Unlocker extraction successful")

            return extracted

        except Exception as e:
            logger.error(f"   ❌ Web Unlocker extraction failed: {e}")
            return None

    async def _fetch_via_unlocker(self, url: str) -> Optional[str]:
        """
        Fetch HTML via Web Unlocker API.

        Args:
            url: Target URL

        Returns:
            Raw HTML content
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "zone": self.zone,
                "url": url,
                "format": "raw"  # Get raw HTML
            }

            logger.debug(f"   POST {self.endpoint}")
            logger.debug(f"   Zone: {self.zone}")
            logger.debug(f"   URL: {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()

                # Web Unlocker returns HTML directly in response body
                return response.text

        except httpx.TimeoutException:
            logger.error(f"   ❌ Web Unlocker timeout ({self.timeout}s)")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"   ❌ Web Unlocker HTTP error: {e.response.status_code}")
            logger.error(f"   Response: {e.response.text[:200]}")
            return None

        except Exception as e:
            logger.error(f"   ❌ Web Unlocker request failed: {e}")
            return None

    async def _extract_with_llm(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from HTML using Claude.

        Args:
            html: Raw HTML content

        Returns:
            Extracted data matching schema
        """
        try:
            # Clean HTML for token optimization
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style tags
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()

            # Get clean text
            clean_text = soup.get_text(separator=' ', strip=True)

            # Limit to prevent token overflow
            max_chars = 30000  # ~7,500 tokens
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars]

            logger.debug(f"   🤖 Calling Claude for extraction...")
            logger.debug(f"   Text size: {len(clean_text)} chars (~{len(clean_text)//4} tokens)")

            prompt = f"""Extract data from this webpage based on the user's query.

User Query: {self.query}

Target JSON Schema:
{json.dumps(self.json_schema, indent=2)}

Webpage Content:
{clean_text}

Instructions:
1. Extract ONLY the fields specified in the schema
2. Return valid JSON matching the exact schema structure
3. If a field is missing, omit it or use null
4. Do not add extra fields or modify the schema

Return ONLY the JSON, no explanations."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text.strip()

            # Parse JSON response
            extracted = self._parse_json_response(result_text)

            logger.debug(f"   ✅ LLM extraction successful")
            return extracted

        except Exception as e:
            logger.error(f"   ❌ LLM extraction failed: {e}")
            return None

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"   ❌ JSON parsing failed: {e}")
            logger.error(f"   Response: {text[:500]}")
            return None
