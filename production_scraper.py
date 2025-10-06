#!/usr/bin/env python3
"""
Production Scraper - Web Unlocker Only

Bypasses Scrapy/Playwright for production deployment.
Uses only Bright Data Web Unlocker HTTP API.
"""
import asyncio
from typing import Dict, Any, Optional
from anthropic import Anthropic

from config import settings
from extraction.unlocker_extractor import WebUnlockerExtractor
from schema_generator import SchemaGenerator
from models import ExtractionResult
from utils import logger


async def production_scrape(
    url: str,
    query: str
) -> Dict[str, Any]:
    """
    Production-safe scraper using Web Unlocker only.

    Args:
        url: Target URL
        query: Natural language extraction query

    Returns:
        Extracted data dict
    """
    try:
        # Step 1: Generate schema
        logger.info("🔧 Generating schema...")
        schema_gen = SchemaGenerator()
        schema_result = await schema_gen.generate_schema(query)

        # Step 2: Extract using Web Unlocker
        logger.info("🔓 Extracting via Web Unlocker...")
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        extractor = WebUnlockerExtractor(
            anthropic_client=client,
            json_schema=schema_result.json_schema,
            query=query
        )

        extracted_data = await extractor.extract(url)

        if not extracted_data:
            raise Exception("Web Unlocker returned no data")

        logger.info("✅ Extraction successful")
        return extracted_data

    except Exception as e:
        logger.error(f"❌ Production scraper failed: {e}")
        raise
