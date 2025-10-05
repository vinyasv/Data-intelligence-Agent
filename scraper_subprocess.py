#!/usr/bin/env python3
"""
Scraper Subprocess Wrapper

This script wraps the scraper functionality to run in a separate process,
avoiding event loop conflicts with the agent mode.

Usage:
    python scraper_subprocess.py '{"url": "...", "query": "...", "options": {...}}'

Input (JSON):
    {
        "url": "https://example.com",
        "query": "Extract products with name and price",
        "options": {
            "respect_robots_txt": true,
            "skip_validation": false,
            "prefer_css": false
        }
    }

Output (JSON):
    {
        "success": true,
        "data": {...},
        "error": null
    }
"""
import asyncio
import json
import sys
import traceback
from typing import Dict, Any

# Import scraper components
from main import scrape
from models import ExtractionError, SchemaGenerationError, StrategyRoutingError


async def run_scraper(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run scraper with provided input data.

    Args:
        input_data: Dictionary with url, query, and options

    Returns:
        Result dictionary with success, data, and error fields
    """
    try:
        url = input_data.get("url")
        query = input_data.get("query")
        options = input_data.get("options", {})

        if not url or not query:
            return {
                "success": False,
                "data": None,
                "error": "Missing required fields: url and query"
            }

        # Call scraper
        result = await scrape(
            url=url,
            query=query,
            respect_robots_txt=options.get("respect_robots_txt", True),
            skip_validation=options.get("skip_validation", False),
            prefer_css=options.get("prefer_css", False),
            stats=None
        )

        return {
            "success": True,
            "data": result,
            "error": None
        }

    except (ExtractionError, SchemaGenerationError, StrategyRoutingError) as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "error_type": type(e).__name__
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "UnexpectedError",
            "traceback": traceback.format_exc()
        }


def main():
    """Main entry point"""
    try:
        # Read input from command line argument or stdin
        if len(sys.argv) > 1:
            # Input from command line argument
            input_json = sys.argv[1]
        else:
            # Input from stdin
            input_json = sys.stdin.read()

        # Parse input
        input_data = json.loads(input_json)

        # Run scraper
        result = asyncio.run(run_scraper(input_data))

        # Output result as JSON
        print(json.dumps(result, ensure_ascii=False))

        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)

    except json.JSONDecodeError as e:
        error_result = {
            "success": False,
            "data": None,
            "error": f"Invalid JSON input: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    except Exception as e:
        error_result = {
            "success": False,
            "data": None,
            "error": f"Fatal error: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
