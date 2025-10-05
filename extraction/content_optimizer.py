"""
Content Optimizer - Reduces HTML tokens by 70-90%
"""
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import re

from utils import logger


class ContentOptimizer:
    """
    Optimizes HTML content before sending to LLM.
    
    Strategies:
    1. Remove non-content elements (nav, footer, ads)
    2. Extract main content area
    3. Convert to markdown (more concise)
    4. Remove excessive whitespace
    
    Target: 70-90% token reduction
    """
    
    # Elements to always remove
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'svg', 'iframe',
        'link', 'meta', 'head'
    ]
    
    # Selectors for non-content areas
    REMOVE_SELECTORS = [
        'nav', 'header', 'footer',
        '.navigation', '.nav', '.navbar',
        '.sidebar', '.side-bar', '.aside',
        '.advertisement', '.ad', '.ads',
        '.social-share', '.social-links',
        '.comments', '.comment-section',
        '.related-products', '.recommendations',
        '.newsletter', '.subscription',
        '.cookie-banner', '.cookie-notice',
    ]
    
    # Main content selectors (in priority order)
    CONTENT_SELECTORS = [
        'main',
        'article',
        '[role="main"]',
        '.main-content',
        '.content',
        '#main',
        '#content',
        '.product-info',
        '.product-details',
        '.pdp-main',
    ]
    
    def optimize(self, html: str, query: str) -> str:
        """
        Optimize HTML content for LLM extraction.
        
        Args:
            html: Raw HTML content
            query: Extraction query (for context)
        
        Returns:
            Optimized markdown content (70-90% smaller)
        """
        logger.debug("🔧 Optimizing content...")
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Step 1: Remove useless tags
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Step 2: Remove non-content areas
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()
        
        # Step 3: Extract main content area
        main_content = self._extract_main_content(soup)
        
        # Step 4: Convert to markdown (more concise)
        markdown = md(str(main_content), heading_style="ATX")
        
        # Step 5: Clean up markdown
        markdown = self._clean_markdown(markdown)
        
        logger.debug(f"   Original: {len(html)} bytes")
        logger.debug(f"   Optimized: {len(markdown)} bytes")
        logger.debug(f"   Reduction: {(1 - len(markdown)/len(html)) * 100:.1f}%")
        
        return markdown
    
    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract main content area from soup"""
        # Try content selectors in priority order
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                logger.debug(f"   Found main content: {selector}")
                return content
        
        # Fallback: Use entire body
        body = soup.find('body')
        if body:
            return body
        
        return soup
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown output"""
        # Remove excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove excessive spaces
        markdown = re.sub(r' {2,}', ' ', markdown)
        
        # Remove empty links
        markdown = re.sub(r'\[]\(.*?\)', '', markdown)
        
        # Strip leading/trailing whitespace
        markdown = markdown.strip()
        
        return markdown
