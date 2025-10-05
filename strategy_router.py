"""
Strategy Router Module

Intelligently chooses between CSS and LLM extraction strategies based on:
- Query semantic requirements
- Schema complexity
- URL structure
"""
import re
from typing import Dict, Any, Optional, Literal
from enum import Enum

from anthropic import Anthropic

from config import settings
from models import StrategyRoutingError
from utils import logger


# Simple strategy container (replaces Crawl4AI strategy objects)
class Strategy:
    """Simple container for strategy information - used with Scrapy"""
    def __init__(self, strategy_type: str, schema: Dict[str, Any], query: Optional[str] = None):
        self.type = strategy_type
        self.schema = schema
        self.query = query


class StrategyType(str, Enum):
    """Extraction strategy types"""
    CSS = "css"
    LLM = "llm"


class StrategyRouter:
    """
    Routes extraction requests to optimal strategy (CSS vs LLM).
    """

    SEMANTIC_DETECTION_PROMPT = """Determine if this web scraping query requires semantic understanding (LLM) or can be done with simple CSS selectors.

Query: "{query}"

A query requires SEMANTIC UNDERSTANDING (LLM) if it involves ANY of:
- Sentiment analysis or opinion detection
- Summarization or generating summaries from content
- Categorization, classification, or grouping
- Filtering with conditions (e.g., "only products with rating > 4", "top mentions", "best rated", "only positive")
- Comparisons or calculations (greater than, less than, equal to, averages, etc.)
- Understanding relationships or context
- Interpretation or analysis of text
- Creating derived fields (summaries, categories, sentiment, etc.)

A query can use CSS SELECTORS ONLY if it:
- Extracts visible text/attributes that already exist on the page
- Gets simple data fields (titles, prices, dates, names, existing summaries)
- Requires NO interpretation, generation, or analysis

IMPORTANT: If the query asks for "summaries", "sentiment", "categories", etc., assume these need to be GENERATED unless explicitly stated as "existing" or "pre-written".

Answer with ONLY one word: "SEMANTIC" or "CSS"."""

    def __init__(self):
        """Initialize strategy router (Scrapy mode)"""
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def choose_strategy(
        self,
        url: str,
        query: str,
        json_schema: Dict[str, Any],
        prefer_css: bool = False
    ) -> tuple[StrategyType, Any]:
        """
        Choose optimal extraction strategy.

        Args:
            url: Target URL
            query: Natural language extraction query
            json_schema: Pydantic JSON schema
            prefer_css: Force CSS strategy (requires CSS selectors)

        Returns:
            Tuple of (strategy_type, strategy_instance)

        Raises:
            StrategyRoutingError: If strategy creation fails
        """
        try:
            logger.info(f"Routing strategy for query: {query[:100]}...")

            # Check if semantic analysis is required
            needs_semantic = self._is_semantic_query(query)

            # Check schema complexity
            is_complex = self._is_complex_schema(json_schema)

            # Decision logic
            if needs_semantic:
                logger.info("Detected semantic query → Using LLM strategy")
                return self._create_llm_strategy(json_schema, query)

            if is_complex:
                logger.info("Detected complex schema → Using LLM strategy")
                return self._create_llm_strategy(json_schema, query)

            # CSS strategy requires pre-defined selectors
            # For universal scraping, default to LLM
            if prefer_css:
                logger.warning("CSS strategy requested but requires manual selector configuration")
                logger.info("Falling back to LLM strategy for universal scraping")

            logger.info("Using LLM strategy (universal mode)")
            return self._create_llm_strategy(json_schema, query)

        except Exception as e:
            logger.error(f"Strategy routing failed: {str(e)}")
            raise StrategyRoutingError(f"Failed to route strategy: {str(e)}")

    def _is_semantic_query(self, query: str) -> bool:
        """
        Detect if query requires semantic understanding using LLM.

        Args:
            query: Natural language query

        Returns:
            True if semantic analysis is needed
        """
        try:
            # Use Claude to intelligently determine if query needs semantic understanding
            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use fast, cheap model for routing
                max_tokens=10,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": self.SEMANTIC_DETECTION_PROMPT.format(query=query)
                    }
                ]
            )

            decision = response.content[0].text.strip().upper()
            is_semantic = "SEMANTIC" in decision

            logger.debug(f"Query semantic analysis: '{query}' → {decision} → {is_semantic}")
            return is_semantic

        except Exception as e:
            logger.warning(f"Failed to detect semantic query, defaulting to True: {e}")
            # Default to semantic (LLM) on error to be safe
            return True

    def _is_complex_schema(self, json_schema: Dict[str, Any]) -> bool:
        """
        Detect if schema is complex (nested objects, unions, etc.).

        Args:
            json_schema: Pydantic JSON schema

        Returns:
            True if schema is complex
        """
        try:
            properties = json_schema.get("properties", {})

            # Check for nested objects
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type", "")

                # Array of objects
                if prop_type == "array":
                    items = prop_schema.get("items", {})
                    if items.get("type") == "object":
                        # Nested object arrays are complex
                        nested_props = items.get("properties", {})
                        if len(nested_props) > 5:
                            return True

                # Direct nested objects
                if prop_type == "object":
                    return True

                # Union types (anyOf, oneOf)
                if "anyOf" in prop_schema or "oneOf" in prop_schema:
                    return True

            # Check total field count
            if len(properties) > 10:
                return True

            return False

        except Exception as e:
            logger.warning(f"Error analyzing schema complexity: {e}")
            return False  # Default to simple

    def _create_llm_strategy(
        self,
        json_schema: Dict[str, Any],
        query: str
    ) -> tuple[StrategyType, Strategy]:
        """
        Create LLM extraction strategy.

        Args:
            json_schema: Pydantic JSON schema
            query: Natural language instruction

        Returns:
            Tuple of (StrategyType.LLM, Strategy instance)
        """
        strategy = Strategy(
            strategy_type="llm",
            schema=json_schema,
            query=query
        )

        logger.debug(f"Created LLM strategy with schema: {json_schema.get('title', 'Unknown')}")
        return (StrategyType.LLM, strategy)

    def _create_css_strategy(
        self,
        css_schema: Dict[str, Any]
    ) -> tuple[StrategyType, Strategy]:
        """
        Create CSS extraction strategy.

        NOTE: This requires a CSS schema with selectors, which is not
        automatically generated. Use this only when you have pre-defined
        CSS selectors for the target site.

        Args:
            css_schema: CSS extraction schema with selectors

        Returns:
            Tuple of (StrategyType.CSS, Strategy instance)

        Example css_schema:
        {
            "baseSelector": "div.product-card",
            "fields": [
                {"name": "title", "selector": "h3.title", "type": "text"},
                {"name": "price", "selector": "span.price", "type": "text"}
            ]
        }
        """
        strategy = Strategy(
            strategy_type="css",
            schema=css_schema,
            query=None
        )

        logger.debug(f"Created CSS strategy with baseSelector: {css_schema.get('baseSelector')}")
        return (StrategyType.CSS, strategy)


# Convenience functions
_router = StrategyRouter()


def choose_strategy(
    url: str,
    query: str,
    json_schema: Dict[str, Any],
    prefer_css: bool = False
) -> tuple[StrategyType, Any]:
    """
    Choose optimal extraction strategy.

    Args:
        url: Target URL
        query: Natural language extraction query
        json_schema: Pydantic JSON schema
        prefer_css: Force CSS strategy (requires CSS selectors)

    Returns:
        Tuple of (strategy_type, strategy_instance)
    """
    return _router.choose_strategy(url, query, json_schema, prefer_css)


def create_llm_strategy(
    json_schema: Dict[str, Any],
    query: str
) -> tuple[StrategyType, Strategy]:
    """
    Create LLM extraction strategy directly.

    Args:
        json_schema: Pydantic JSON schema
        query: Natural language instruction

    Returns:
        Tuple of (StrategyType.LLM, Strategy instance)
    """
    return _router._create_llm_strategy(json_schema, query)


def create_css_strategy(
    css_schema: Dict[str, Any]
) -> tuple[StrategyType, Strategy]:
    """
    Create CSS extraction strategy directly.

    Args:
        css_schema: CSS extraction schema with selectors

    Returns:
        Tuple of (StrategyType.CSS, Strategy instance)
    """
    return _router._create_css_strategy(css_schema)
