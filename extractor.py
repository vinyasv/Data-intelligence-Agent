"""
Extraction Orchestrator Module

Core extraction logic using Crawl4AI AsyncWebCrawler.
Handles both CSS and LLM extraction strategies with fallback.
Includes intelligent wait strategies and multi-source extraction.
"""
import json
import asyncio
import re
from typing import Dict, Any, Optional, Tuple, List
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from anthropic import Anthropic

from config import settings
from models import ExtractionResult, ExtractionError
from strategy_router import StrategyType
from utils import logger, sanitize_url


class WebExtractor:
    """
    Orchestrates web extraction using Crawl4AI with intelligent strategy routing.
    """

    def __init__(self, use_undetected=False):
        """
        Initialize web extractor with browser configuration.

        Args:
            use_undetected: Use UndetectedAdapter for sophisticated bot detection bypass
        """
        self.use_undetected = use_undetected

        self.browser_config = BrowserConfig(
            browser_type=settings.BROWSER_TYPE,
            headless=settings.BROWSER_HEADLESS,
            use_persistent_context=False,
            # Stealth mode - enables playwright-stealth
            enable_stealth=settings.ENABLE_STEALTH if not use_undetected else False,
            # Viewport
            viewport_width=1920,
            viewport_height=1080,
            # User agent randomization
            user_agent_mode="random" if not use_undetected else "",
            # Anti-detection
            ignore_https_errors=True,
            java_script_enabled=True,
            # Performance options
            text_mode=False,  # Enable images
            light_mode=False,  # Full features
        )

        # Create undetected adapter if needed
        self.crawler_strategy = None
        if use_undetected:
            try:
                from crawl4ai import UndetectedAdapter
                from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

                adapter = UndetectedAdapter()
                self.crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                    browser_config=self.browser_config,
                    browser_adapter=adapter
                )
                logger.info("🕵️  Using UndetectedAdapter for enhanced bot detection bypass")
            except ImportError as e:
                logger.warning(f"UndetectedAdapter not available: {e}")
                self.use_undetected = False

    async def extract(
        self,
        url: str,
        query: str,
        strategy_type: StrategyType,
        strategy: Any,
        max_retries: int = 3,
        timeout: int = 30000,
        use_smart_wait: bool = True
    ) -> ExtractionResult:
        """
        Extract data from URL using specified strategy with intelligent waiting.

        Args:
            url: Target URL to scrape
            query: Natural language extraction query
            strategy_type: Type of extraction strategy (CSS or LLM)
            strategy: Strategy instance (JsonCssExtractionStrategy or LLMExtractionStrategy)
            max_retries: Maximum number of retry attempts
            timeout: Timeout in milliseconds
            use_smart_wait: Use LLM-powered smart wait strategy

        Returns:
            ExtractionResult with extracted data

        Raises:
            ExtractionError: If extraction fails after all retries
        """
        url = sanitize_url(url)
        logger.info(f"Starting extraction from {url} using {strategy_type.value.upper()} strategy")

        # Determine optimal wait strategy based on content type
        # For JS-heavy sites, wait for network idle + delay
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()

        # Detect if site likely uses heavy JavaScript
        js_heavy_domains = ['abercrombie', 'nike', 'adidas', 'zara', 'hm.com', 'urbanoutfitters']
        is_js_heavy = any(d in domain for d in js_heavy_domains)

        if is_js_heavy:
            wait_until = "networkidle"  # Wait for network to be idle
            delay_html = 1.5  # Reduced from 3.0s - faster but still safe for JS
            logger.info(f"   Detected JS-heavy site, using networkidle + {delay_html}s delay")
        else:
            wait_until = "domcontentloaded"  # Standard wait
            delay_html = 0.5  # Reduced from 1.0s - faster for static content

        # Note: Content filters (fit_markdown) can remove critical data on e-commerce sites
        # (prices, images) because they have low text density. Disabling for universal scraping.
        # For production, could make this configurable per URL type.

        # Create crawler run configuration with proper Crawl4AI settings
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode[settings.CACHE_MODE],
            word_count_threshold=settings.WORD_COUNT_THRESHOLD,
            extraction_strategy=strategy,
            # Wait configuration
            wait_until=wait_until,  # "networkidle" or "domcontentloaded"
            page_timeout=timeout,
            delay_before_return_html=delay_html,  # Wait after page load
            # Rate limiting
            mean_delay=1.0,
            max_range=2.0,
            # User simulation for better evasion
            simulate_user=True if is_js_heavy else False,
            # Auto-handle popups/overlays
            magic=True if is_js_heavy else False,
            # Performance optimizations
            process_iframes=False,  # Skip iframe processing for speed
            remove_overlay_elements=True,  # Auto-remove popups/overlays
            excluded_tags=['script', 'style', 'noscript', 'svg'],  # Reduce HTML size
        )

        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Extraction attempt {attempt + 1}/{max_retries}")

                # Use crawler_strategy if UndetectedAdapter is configured
                crawler_kwargs = {"config": self.browser_config}
                if self.crawler_strategy:
                    crawler_kwargs["crawler_strategy"] = self.crawler_strategy

                async with AsyncWebCrawler(**crawler_kwargs) as crawler:
                    result = await crawler.arun(
                        url=url,
                        config=run_config
                    )

                    if not result.success:
                        error_msg = result.error_message or "Unknown error"
                        logger.warning(f"Crawl failed: {error_msg}")
                        last_error = error_msg

                        # Retry on failure
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            raise ExtractionError(f"Failed to crawl after {max_retries} attempts: {error_msg}")

                    # Parse extracted content
                    if not result.extracted_content:
                        logger.warning("No content extracted from main strategy")

                        # Try alternative sources (JSON-LD, meta tags, etc.)
                        if result.html:
                            logger.info("🔄 Attempting alternative extraction sources...")
                            alt_data = await self.extract_from_alternative_sources(
                                result.html, url, query
                            )

                            if alt_data:
                                logger.info("✅ Successfully extracted from alternative source!")
                                return ExtractionResult(
                                    url=url,
                                    query=query,
                                    extracted_data=alt_data,
                                    extraction_strategy=f"{strategy_type.value}_alternative",
                                    success=True
                                )

                        # If this was CSS strategy, it might have failed - return empty for fallback
                        if strategy_type == StrategyType.CSS:
                            return ExtractionResult(
                                url=url,
                                query=query,
                                extracted_data={},
                                extraction_strategy=strategy_type.value,
                                success=False,
                                error_message="CSS extraction returned no content"
                            )

                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise ExtractionError("No content extracted after all retries")

                    # Parse JSON content
                    try:
                        extracted_data = json.loads(result.extracted_content)
                        logger.info(f"📋 Parsed LLM response: {str(extracted_data)[:200]}...")

                        # Handle case where LLM returns a list instead of dict
                        # This happens when the schema has a single root array field
                        if isinstance(extracted_data, list) and len(extracted_data) > 0:
                            logger.info(f"   🔄 LLM returned list with {len(extracted_data)} items")

                            # If multiple dicts, try to find the one with actual data
                            if len(extracted_data) > 1 and all(isinstance(item, dict) for item in extracted_data):
                                # Find first non-empty dict
                                non_empty = None
                                for item in extracted_data:
                                    # Check if dict has any non-empty values
                                    has_data = any(
                                        (isinstance(v, list) and len(v) > 0) or
                                        (isinstance(v, dict) and v) or
                                        (v is not None and v != "" and v != [])
                                        for v in item.values()
                                    )
                                    if has_data:
                                        non_empty = item
                                        break

                                if non_empty:
                                    logger.info(f"   ✅ Found non-empty item in list")
                                    extracted_data = non_empty
                                else:
                                    # All empty, just take first
                                    extracted_data = extracted_data[0]
                            else:
                                # Single item or not all dicts, use default logic
                                extracted_data = extracted_data[0] if len(extracted_data) == 1 else {"items": extracted_data}

                            logger.info("   Converted list response to dict")

                        # Check if extracted data is empty (e.g., {products: []})
                        is_empty = False
                        if isinstance(extracted_data, dict):
                            # Handle empty dict case
                            if not extracted_data:
                                is_empty = True
                                logger.info("   ⚠️  LLM returned empty dict {}")
                            else:
                                # Check if all values are empty lists, None, or empty dicts
                                is_empty = all(
                                    (isinstance(v, list) and len(v) == 0) or v is None or v == {}
                                    for v in extracted_data.values()
                                )
                                if is_empty:
                                    logger.info(f"   ⚠️  LLM returned empty data: {extracted_data}")
                                    logger.info(f"   has_html={bool(result.html)}, html_length={len(result.html) if result.html else 0}")

                        if is_empty and result.html:
                            logger.warning("🔄 LLM extraction returned empty data, trying alternative sources...")
                            alt_data = await self.extract_from_alternative_sources(
                                result.html, url, query
                            )

                            if alt_data:
                                logger.info("✅ Successfully extracted from alternative source!")
                                logger.info(f"   📦 Alt data preview: {str(alt_data)[:200]}...")
                                extracted_data = alt_data
                            else:
                                logger.warning("❌ Alternative sources also returned empty")

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse extracted content as JSON: {e}")
                        logger.debug(f"Raw content: {result.extracted_content[:500]}")

                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise ExtractionError(f"Invalid JSON in extracted content: {e}")

                    # Success!
                    logger.info(f"Successfully extracted data from {url}")
                    logger.debug(f"Extracted {len(str(extracted_data))} characters")

                    return ExtractionResult(
                        url=url,
                        query=query,
                        extracted_data=extracted_data,
                        extraction_strategy=strategy_type.value,
                        success=True
                    )

            except Exception as e:
                last_error = str(e)
                logger.error(f"Extraction attempt {attempt + 1} failed: {last_error}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise ExtractionError(f"Extraction failed after {max_retries} attempts: {last_error}")

        # Should never reach here, but just in case
        raise ExtractionError(f"Extraction failed: {last_error}")

    async def extract_with_fallback(
        self,
        url: str,
        query: str,
        primary_strategy_type: StrategyType,
        primary_strategy: Any,
        fallback_strategy_type: Optional[StrategyType] = None,
        fallback_strategy: Optional[Any] = None
    ) -> ExtractionResult:
        """
        Extract data with automatic fallback to alternative strategy.

        Best practice: Try CSS first (fast, free), fallback to LLM if needed.

        Args:
            url: Target URL
            query: Natural language query
            primary_strategy_type: Primary strategy type
            primary_strategy: Primary strategy instance
            fallback_strategy_type: Fallback strategy type (optional)
            fallback_strategy: Fallback strategy instance (optional)

        Returns:
            ExtractionResult from successful strategy
        """
        logger.info(f"Attempting extraction with {primary_strategy_type.value.upper()} strategy")

        try:
            result = await self.extract(url, query, primary_strategy_type, primary_strategy)

            # Check if extraction was successful
            if result.success and result.extracted_data:
                return result

            # If primary failed and we have fallback
            if fallback_strategy and fallback_strategy_type:
                logger.warning(f"{primary_strategy_type.value.upper()} extraction failed or returned empty data")
                logger.info(f"Falling back to {fallback_strategy_type.value.upper()} strategy")

                return await self.extract(url, query, fallback_strategy_type, fallback_strategy)

            return result

        except ExtractionError as e:
            # If primary failed and we have fallback
            if fallback_strategy and fallback_strategy_type:
                logger.warning(f"{primary_strategy_type.value.upper()} extraction failed: {str(e)}")
                logger.info(f"Falling back to {fallback_strategy_type.value.upper()} strategy")

                return await self.extract(url, query, fallback_strategy_type, fallback_strategy)

            # No fallback available
            raise

    async def extract_from_alternative_sources(
        self,
        html_content: str,
        url: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract data from alternative sources when main extraction fails.
        Tries: JSON-LD, OpenGraph meta tags, data attributes.

        Args:
            html_content: Raw HTML content
            url: Target URL
            query: Natural language query

        Returns:
            Extracted data dict or None
        """
        logger.info("🔍 Trying alternative data sources...")

        # 1. Try JSON-LD structured data
        jsonld_data = self._extract_jsonld(html_content)
        if jsonld_data:
            logger.info("   ✅ Found JSON-LD data")
            return await self._convert_jsonld_with_llm(jsonld_data, query)

        # 2. Try OpenGraph/Twitter meta tags
        meta_data = self._extract_meta_tags(html_content)
        if meta_data:
            logger.info("   ✅ Found meta tag data")
            return await self._convert_meta_with_llm(meta_data, query)

        # 3. Try data attributes
        data_attrs = self._extract_data_attributes(html_content)
        if data_attrs:
            logger.info("   ✅ Found data attributes")
            return await self._convert_data_attrs_with_llm(data_attrs, query)

        logger.warning("   ❌ No alternative data sources found")
        return None

    def _extract_jsonld(self, html: str) -> Optional[Dict]:
        """Extract JSON-LD structured data from HTML"""
        try:
            # Find script tags with type="application/ld+json"
            pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

            logger.info(f"   🔎 Found {len(matches)} JSON-LD script tags")

            for i, match in enumerate(matches):
                try:
                    data = json.loads(match.strip())
                    # Look for Product or relevant schema types
                    if isinstance(data, dict):
                        schema_type = data.get("@type", "")
                        logger.info(f"      JSON-LD {i+1}: @type = {schema_type}")
                        if any(t in schema_type for t in ["Product", "Article", "JobPosting", "Review"]):
                            logger.info(f"      ✅ Found relevant schema type: {schema_type}")
                            return data
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                schema_type = item.get("@type", "")
                                logger.info(f"      JSON-LD {i+1}: @type = {schema_type}")
                                if any(t in schema_type for t in ["Product", "Article", "JobPosting"]):
                                    logger.info(f"      ✅ Found relevant schema type: {schema_type}")
                                    return item
                except json.JSONDecodeError as e:
                    logger.warning(f"      ⚠️  Failed to parse JSON-LD {i+1}: {e}")
                    continue

            logger.info("   ❌ No relevant JSON-LD schemas found")
            return None
        except Exception as e:
            logger.warning(f"JSON-LD extraction failed: {e}")
            return None

    def _extract_meta_tags(self, html: str) -> Optional[Dict]:
        """Extract OpenGraph and Twitter Card meta tags"""
        try:
            meta_data = {}

            # OpenGraph tags
            og_pattern = r'<meta[^>]*property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            og_matches = re.findall(og_pattern, html, re.IGNORECASE)
            for prop, content in og_matches:
                meta_data[f"og_{prop}"] = content

            # Twitter Card tags
            tw_pattern = r'<meta[^>]*name=["\']twitter:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            tw_matches = re.findall(tw_pattern, html, re.IGNORECASE)
            for prop, content in tw_matches:
                meta_data[f"twitter_{prop}"] = content

            # Standard meta tags
            meta_pattern = r'<meta[^>]*name=["\']([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            meta_matches = re.findall(meta_pattern, html, re.IGNORECASE)
            for name, content in meta_matches:
                if name.lower() in ["description", "keywords", "author", "price", "availability"]:
                    meta_data[name.lower()] = content

            if meta_data:
                logger.info(f"   🔎 Found {len(meta_data)} meta tags")
            else:
                logger.info("   ❌ No relevant meta tags found")

            return meta_data if meta_data else None
        except Exception as e:
            logger.warning(f"Meta tag extraction failed: {e}")
            return None

    def _extract_data_attributes(self, html: str) -> Optional[Dict]:
        """Extract data-* attributes from HTML"""
        try:
            data_attrs = {}

            # Common data attributes for products
            patterns = [
                (r'data-product-([^=]+)=["\']([^"\']+)["\']', "product_"),
                (r'data-price=["\']([^"\']+)["\']', "price"),
                (r'data-name=["\']([^"\']+)["\']', "name"),
                (r'data-id=["\']([^"\']+)["\']', "id"),
                (r'data-sku=["\']([^"\']+)["\']', "sku"),
            ]

            for pattern, prefix in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        key, value = match
                        data_attrs[f"{prefix}{key}"] = value
                    else:
                        data_attrs[prefix] = match

            if data_attrs:
                logger.info(f"   🔎 Found {len(data_attrs)} data attributes")
            else:
                logger.info("   ❌ No relevant data attributes found")

            return data_attrs if data_attrs else None
        except Exception as e:
            logger.warning(f"Data attribute extraction failed: {e}")
            return None

    async def _convert_jsonld_with_llm(self, jsonld: Dict, query: str) -> Dict:
        """Use Claude to convert JSON-LD to desired schema"""
        try:
            logger.info("   🤖 Converting JSON-LD with Claude...")
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            prompt = f"""Convert this JSON-LD structured data to match the user's query.

User Query: {query}

JSON-LD Data:
{json.dumps(jsonld, indent=2)}

Extract the requested fields and return ONLY valid JSON matching the query.
If a field is not available, omit it or use null."""

            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            converted = json.loads(result_text)
            logger.info(f"   ✅ JSON-LD conversion successful")
            return converted
        except Exception as e:
            logger.error(f"   ❌ JSON-LD conversion failed: {e}")
            return {"raw_jsonld": jsonld}

    async def _convert_meta_with_llm(self, meta_data: Dict, query: str) -> Dict:
        """Use Claude to convert meta tags to desired schema"""
        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            prompt = f"""Convert this meta tag data to match the user's query.

User Query: {query}

Meta Data:
{json.dumps(meta_data, indent=2)}

Extract the requested fields and return ONLY valid JSON matching the query."""

            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Meta conversion failed: {e}")
            return {"raw_meta": meta_data}

    async def _convert_data_attrs_with_llm(self, data_attrs: Dict, query: str) -> Dict:
        """Use Claude to convert data attributes to desired schema"""
        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            prompt = f"""Convert this data attribute data to match the user's query.

User Query: {query}

Data Attributes:
{json.dumps(data_attrs, indent=2)}

Extract the requested fields and return ONLY valid JSON matching the query."""

            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Data attr conversion failed: {e}")
            return {"raw_data_attrs": data_attrs}


# Convenience function
async def extract_from_url(
    url: str,
    query: str,
    strategy_type: StrategyType,
    strategy: Any
) -> Dict[str, Any]:
    """
    Extract data from URL using specified strategy.

    Args:
        url: Target URL
        query: Natural language query
        strategy_type: Strategy type (CSS or LLM)
        strategy: Strategy instance

    Returns:
        Extracted data dictionary
    """
    extractor = WebExtractor()
    result = await extractor.extract(url, query, strategy_type, strategy)

    if not result.success:
        raise ExtractionError(result.error_message or "Extraction failed")

    return result.extracted_data
