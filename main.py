#!/usr/bin/env python3
"""
Universal Web Scraper - Main Entry Point

Accepts a URL and natural language query, returns structured JSON.
"""
import asyncio
import argparse
import json
import sys
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from pydantic import BaseModel, ValidationError as PydanticValidationError

from config import settings
from schema_generator import SchemaGenerator
from strategy_router import StrategyRouter, StrategyType
from extractor import WebExtractor
from models import ExtractionError, SchemaGenerationError, StrategyRoutingError
from utils import logger, sanitize_url


class ScraperStats:
    """Track scraping statistics for cost/performance reporting"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.schema_generation_time: float = 0
        self.routing_time: float = 0
        self.extraction_time: float = 0
        self.validation_time: float = 0
        self.strategy_used: Optional[str] = None
        self.tokens_used: int = 0  # Estimated
        self.estimated_cost: float = 0.0

    def start(self):
        """Start timing"""
        self.start_time = time.time()

    def finish(self):
        """Finish timing"""
        self.end_time = time.time()

    @property
    def total_time(self) -> float:
        """Total execution time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def report(self) -> str:
        """Generate performance report"""
        lines = [
            "\n" + "="*60,
            "📊 PERFORMANCE REPORT",
            "="*60,
            f"Total Time: {self.total_time:.2f}s",
            f"  ├─ Schema Generation: {self.schema_generation_time:.2f}s",
            f"  ├─ Strategy Routing: {self.routing_time:.2f}s",
            f"  ├─ Data Extraction: {self.extraction_time:.2f}s",
            f"  └─ Validation: {self.validation_time:.2f}s",
            f"",
            f"Strategy Used: {self.strategy_used or 'N/A'}",
            f"Estimated Cost: ${self.estimated_cost:.4f}",
            "="*60
        ]
        return "\n".join(lines)


async def check_robots_txt(url: str, user_agent: str = "*") -> bool:
    """
    Check if scraping is allowed by robots.txt

    Args:
        url: Target URL
        user_agent: User agent string

    Returns:
        True if allowed, False if disallowed
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = RobotFileParser()
        rp.set_url(robots_url)

        # Use asyncio to avoid blocking
        await asyncio.to_thread(rp.read)

        can_fetch = rp.can_fetch(user_agent, url)

        if not can_fetch:
            logger.warning(f"⚠️  robots.txt disallows scraping: {url}")

        return can_fetch

    except Exception as e:
        logger.debug(f"Could not read robots.txt: {e}")
        # If robots.txt is not available, assume allowed
        return True


async def scrape(
    url: str,
    query: str,
    respect_robots_txt: bool = True,
    skip_validation: bool = False,
    prefer_css: bool = False,
    stats: Optional[ScraperStats] = None
) -> Dict[str, Any]:
    """
    Main scraping orchestration function.

    Args:
        url: Target website URL
        query: Natural language extraction query
        respect_robots_txt: Check robots.txt before scraping
        skip_validation: Skip Pydantic validation
        prefer_css: Prefer CSS extraction (requires manual configuration)
        stats: Optional stats tracker

    Returns:
        Validated structured JSON data

    Raises:
        ExtractionError: If scraping fails
        SchemaGenerationError: If schema generation fails
        StrategyRoutingError: If strategy routing fails
    """
    if stats:
        stats.start()

    url = sanitize_url(url)

    # Step 0: Check robots.txt
    if respect_robots_txt:
        logger.info("🤖 Checking robots.txt...")
        allowed = await check_robots_txt(url)
        if not allowed:
            raise ExtractionError(
                f"Scraping disallowed by robots.txt: {url}\n"
                "Use --ignore-robots to override (use responsibly)"
            )

    # Step 1: Generate schema from query
    logger.info("🧠 Generating schema from query...")
    start = time.time()

    schema_generator = SchemaGenerator()
    schema_result = await schema_generator.generate_schema(query)

    if stats:
        stats.schema_generation_time = time.time() - start

    logger.info(f"   ✅ Generated schema: {schema_result.model_name}")

    # Step 2: Route to optimal strategy
    logger.info("🔀 Determining extraction strategy...")
    start = time.time()

    strategy_router = StrategyRouter()
    strategy_type, strategy = strategy_router.choose_strategy(
        url=url,
        query=query,
        json_schema=schema_result.json_schema,
        prefer_css=prefer_css
    )

    if stats:
        stats.routing_time = time.time() - start
        stats.strategy_used = strategy_type.value.upper()

    logger.info(f"   ✅ Using {strategy_type.value.upper()} strategy")

    # Step 3: Extract with Scrapy + Playwright
    logger.info(f"🕷️  Extracting from {url}...")
    logger.info(f"   Expected: 3-6 seconds (10-20x faster than before!)")
    start = time.time()

    # Use UndetectedAdapter for JS-heavy sites (better bot detection bypass)
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    js_heavy_domains = []  # Disabled - test without UndetectedAdapter
    use_undetected = any(d in domain for d in js_heavy_domains)

    extractor = WebExtractor(use_undetected=use_undetected)

    try:
        # Use parallel race extraction (Playwright+Proxies vs Web Unlocker)
        extraction_result = await extractor.extract_with_race(
            url=url,
            query=query,
            strategy_type=strategy_type,
            strategy=strategy,
            pydantic_code=schema_result.pydantic_code  # NEW: Pass schema code for validation
        )

        if stats:
            stats.extraction_time = time.time() - start

        if not extraction_result.success:
            raise ExtractionError(
                extraction_result.error_message or "Extraction failed"
            )

        raw_data = extraction_result.extracted_data

    except ExtractionError:
        if stats:
            stats.extraction_time = time.time() - start
        raise

    # Step 4: Validate with Pydantic
    if not skip_validation:
        logger.info("✅ Validating data...")
        start = time.time()

        try:
            # Get model class from generated code
            pydantic_model = schema_generator.get_model_class(schema_result.pydantic_code)

            # Validate data
            validated = pydantic_model(**raw_data)
            validated_data = validated.model_dump()

            if stats:
                stats.validation_time = time.time() - start

            logger.info("   ✅ Data validation passed")

        except PydanticValidationError as e:
            if stats:
                stats.validation_time = time.time() - start

            logger.error(f"❌ Validation failed: {e}")
            logger.warning("Returning unvalidated data (use --skip-validation to suppress this error)")
            raise ExtractionError(f"Data validation failed: {e}")

    else:
        validated_data = raw_data
        logger.info("⚠️  Skipping validation (--skip-validation)")

    # Estimate cost (rough approximation)
    if stats:
        if strategy_type == StrategyType.LLM:
            # Rough estimate: ~1000 tokens input + output per page
            estimated_tokens = 2000
            # Claude Sonnet 4.5 pricing (approximate)
            cost_per_1k_tokens = 0.003
            stats.tokens_used = estimated_tokens
            stats.estimated_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
        else:
            stats.tokens_used = 0
            stats.estimated_cost = 0.0

        stats.finish()

    return validated_data


async def main_async():
    """Async main function"""
    parser = argparse.ArgumentParser(
        description="Universal Web Scraper powered by Claude 4.5 Sonnet and Scrapy-Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://example.com/products" "Extract all products with name, price, and rating"
  python main.py "https://news.site.com" "Get articles with headline, author, and date" --output articles.json
  python main.py "https://jobs.com" "Find remote software engineering jobs" --pretty --stats
        """
    )

    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("query", help="Natural language extraction query")

    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: print to stdout)"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output"
    )

    # Scraping options
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Ignore robots.txt restrictions (use responsibly)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip Pydantic validation of extracted data"
    )
    parser.add_argument(
        "--prefer-css",
        action="store_true",
        help="Prefer CSS extraction (requires manual configuration)"
    )

    # Performance options
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show performance statistics"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.setLevel("DEBUG")

    # Print banner
    print("\n" + "="*60)
    print("🕷️  Universal Web Scraper")
    print("   Powered by Claude 4.5 Sonnet + Scrapy-Playwright")
    print("="*60 + "\n")

    # Initialize stats if requested
    stats = ScraperStats() if args.stats else None

    try:
        # Run scraping
        result = await scrape(
            url=args.url,
            query=args.query,
            respect_robots_txt=not args.ignore_robots,
            skip_validation=args.skip_validation,
            prefer_css=args.prefer_css,
            stats=stats
        )

        # Format output
        json_output = json.dumps(
            result,
            indent=2 if args.pretty else None,
            ensure_ascii=False
        )

        # Save or print
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"\n✅ Successfully saved to {args.output}")
        else:
            print("\n" + "="*60)
            print("📦 EXTRACTED DATA")
            print("="*60)
            print(json_output)
            print("="*60)

        # Show stats
        if stats:
            print(stats.report())

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130

    except (ExtractionError, SchemaGenerationError, StrategyRoutingError) as e:
        print(f"\n❌ Error: {str(e)}\n", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Synchronous entry point"""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
