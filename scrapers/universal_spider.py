"""
Universal Scrapy Spider with Playwright Support
Handles any URL + query with dynamic schema
"""
import scrapy
import json
from typing import Dict, Any, Optional, List
from scrapy_playwright.page import PageMethod
from urllib.parse import urlparse

from config import settings
from scrapers.wait_strategies import get_playwright_methods
from utils import logger


class UniversalSpider(scrapy.Spider):
    """
    Universal spider that works with any URL and dynamic schema.
    
    Supports:
    - Dynamic Pydantic schemas (generated at runtime)
    - JS-heavy sites with Playwright
    - Fallback extraction strategies
    """
    
    name = 'universal'
    
    # Scrapy settings (can be overridden)
    custom_settings = {
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type in [
            'stylesheet', 'font', 'media'  # Skip non-essential resources
        ],
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'CONCURRENT_REQUESTS': 1,  # Single page at a time
        'DOWNLOAD_DELAY': 1,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(
        self,
        url: str,
        query: str,
        json_schema: Dict[str, Any],
        pydantic_code: str,
        strategy_type: str,
        llm_extractor: Any = None,
        content_optimizer: Any = None,
        structured_extractor: Any = None,
        results_collector: Optional[List] = None,
        *args,
        **kwargs
    ):
        """
        Initialize spider with dynamic parameters.
        
        Args:
            url: Target URL to scrape
            query: Natural language extraction query
            json_schema: Dynamically generated Pydantic JSON schema
            pydantic_code: Pydantic model code (for validation)
            strategy_type: "llm" or "css"
            llm_extractor: LLM extractor instance
            content_optimizer: Content optimizer instance  
            structured_extractor: Structured data extractor instance
            results_collector: List to collect results (for async integration)
        """
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.query = query
        self.json_schema = json_schema
        self.pydantic_code = pydantic_code
        self.strategy_type = strategy_type
        self.results_collector = results_collector if results_collector is not None else []
        
        # Store extractors (will be injected from extractor.py)
        self.llm_extractor = llm_extractor
        self.content_optimizer = content_optimizer
        self.structured_extractor = structured_extractor
        
        # Compile Pydantic model for validation
        self.pydantic_model = self._compile_pydantic_model(pydantic_code)
        
        logger.info(f"🕷️  Universal Spider initialized")
        logger.info(f"   URL: {url}")
        logger.info(f"   Query: {query[:100]}...")
        logger.info(f"   Strategy: {strategy_type.upper()}")
    
    def start_requests(self):
        """Generate initial requests with Playwright configuration"""
        for url in self.start_urls:
            # Get domain-specific Playwright methods
            domain = urlparse(url).netloc
            playwright_methods = get_playwright_methods(domain, self.query)
            
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback,
                dont_filter=True,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': playwright_methods,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'load',  # or 'networkidle' for JS-heavy
                        'timeout': 30000,
                    },
                }
            )
    
    async def parse(self, response):
        """
        Main parsing logic with extraction hierarchy.
        
        For now: Basic LLM extraction
        Phase 2 will add: Structured data → Optimized content → Full extraction
        """
        url = response.url
        html = response.text
        
        logger.info(f"📄 Parsing {url}")
        logger.info(f"   HTML size: {len(html)} bytes")
        
        # PHASE 1: Basic extraction (we'll optimize in Phase 2)
        try:
            # Try structured data extraction if available
            if self.structured_extractor:
                logger.info("🔍 Checking structured data sources...")
                structured_data = self.structured_extractor.extract_all(html)
                
                if structured_data:
                    logger.info(f"✅ Found structured data: {list(structured_data.keys())}")
                    # Convert with LLM (minimal tokens)
                    if self.llm_extractor:
                        extracted = await self.llm_extractor.convert_structured_data(
                            structured_data, 
                            self.query
                        )
                        if extracted and not self._is_empty(extracted):
                            logger.info("🎉 Structured data extraction successful!")
                            yield self._format_result(extracted, url, "structured_data")
                            return
            
            # Try optimized extraction if available
            if self.content_optimizer and self.llm_extractor:
                logger.info("🔍 Optimized LLM extraction...")
                optimized_content = self.content_optimizer.optimize(html, self.query)
                logger.info(f"   Token reduction: {len(html)} → {len(optimized_content)} bytes")
                
                extracted = await self.llm_extractor.extract(optimized_content)
                if extracted and not self._is_empty(extracted):
                    logger.info("✅ Optimized LLM extraction successful!")
                    yield self._format_result(extracted, url, "llm_optimized")
                    return
            
            # Fallback: Basic extraction with full HTML
            if self.llm_extractor:
                logger.info("🔍 Full LLM extraction...")
                extracted = await self.llm_extractor.extract(html)
                
                if extracted and not self._is_empty(extracted):
                    logger.info("✅ Full LLM extraction successful!")
                    yield self._format_result(extracted, url, "llm_full")
                    return
            
            # All strategies failed
            logger.error("❌ All extraction strategies failed")
            yield self._format_result({}, url, "failed", success=False)
            
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            yield self._format_result(
                {}, 
                url, 
                "error", 
                success=False,
                error_message=str(e)
            )
    
    def errback(self, failure):
        """Handle request failures"""
        logger.error(f"❌ Request failed: {failure.request.url}")
        logger.error(f"   Error: {failure.value}")
        
        yield self._format_result(
            {},
            failure.request.url,
            "error",
            success=False,
            error_message=str(failure.value)
        )
    
    def _format_result(
        self, 
        data: Dict[str, Any], 
        url: str, 
        extraction_method: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format extraction result"""
        result = {
            'url': url,
            'query': self.query,
            'extracted_data': data,
            'extraction_strategy': f"{self.strategy_type}_{extraction_method}",
            'success': success,
            'error_message': error_message
        }
        
        # Add to results collector for async retrieval
        self.results_collector.append(result)
        
        return result
    
    def _is_empty(self, data: Dict[str, Any]) -> bool:
        """Check if extracted data is empty"""
        if not data:
            return True
        
        # Check if all values are empty lists, None, or empty dicts
        return all(
            (isinstance(v, list) and len(v) == 0) or 
            v is None or 
            v == {}
            for v in data.values()
        )
    
    def _compile_pydantic_model(self, pydantic_code: str):
        """Compile Pydantic model from code string"""
        from pydantic import BaseModel, Field
        from typing import List, Optional, Literal
        
        namespace = {
            'BaseModel': BaseModel,
            'Field': Field,
            'Optional': Optional,
            'List': List,
            'Literal': Literal,
        }
        
        try:
            exec(pydantic_code, namespace)
            
            # Get last defined model (container model)
            models = [
                obj for obj in namespace.values()
                if isinstance(obj, type) and issubclass(obj, BaseModel) and obj != BaseModel
            ]
            
            return models[-1] if models else None
        except Exception as e:
            logger.warning(f"Failed to compile Pydantic model: {e}")
            return None
