"""
Structured Data Extractor - Extract JSON-LD, OpenGraph, meta tags
FREE extraction (0 LLM tokens)
"""
import json
import re
from typing import Dict, Any, Optional

from utils import logger


class StructuredDataExtractor:
    """
    Extract structured data from HTML without using LLM.
    
    Sources:
    1. JSON-LD (schema.org)
    2. OpenGraph meta tags
    3. Twitter Card meta tags
    4. Standard meta tags
    5. Data attributes
    
    Cost: $0 (no LLM calls)
    """
    
    def extract_all(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract all available structured data.
        
        Returns:
            Combined structured data from all sources
        """
        data = {}
        
        # Try JSON-LD first (most reliable)
        jsonld = self.extract_jsonld(html)
        if jsonld:
            data['jsonld'] = jsonld
        
        # Try meta tags
        meta = self.extract_meta_tags(html)
        if meta:
            data['meta'] = meta
        
        # Try data attributes
        attrs = self.extract_data_attributes(html)
        if attrs:
            data['attributes'] = attrs
        
        return data if data else None
    
    def extract_jsonld(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD structured data.
        
        Common types: Product, Article, JobPosting, Review, Organization
        """
        try:
            pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            
            logger.debug(f"   Found {len(matches)} JSON-LD blocks")
            
            for i, match in enumerate(matches):
                try:
                    data = json.loads(match.strip())
                    
                    # Handle single object
                    if isinstance(data, dict):
                        schema_type = data.get('@type', '')
                        if self._is_relevant_schema(schema_type):
                            logger.debug(f"   ✅ Found relevant JSON-LD: {schema_type}")
                            return data
                    
                    # Handle array of objects
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                schema_type = item.get('@type', '')
                                if self._is_relevant_schema(schema_type):
                                    logger.debug(f"   ✅ Found relevant JSON-LD: {schema_type}")
                                    return item
                
                except json.JSONDecodeError:
                    logger.debug(f"   ⚠️  Failed to parse JSON-LD block {i+1}")
                    continue
            
            return None
        
        except Exception as e:
            logger.warning(f"JSON-LD extraction failed: {e}")
            return None
    
    def extract_meta_tags(self, html: str) -> Optional[Dict[str, str]]:
        """Extract OpenGraph, Twitter Card, and standard meta tags"""
        try:
            meta_data = {}
            
            # OpenGraph tags (og:title, og:description, og:image, etc.)
            og_pattern = r'<meta[^>]*property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            og_matches = re.findall(og_pattern, html, re.IGNORECASE)
            for prop, content in og_matches:
                meta_data[f'og_{prop}'] = content
            
            # Twitter Card tags
            tw_pattern = r'<meta[^>]*name=["\']twitter:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            tw_matches = re.findall(tw_pattern, html, re.IGNORECASE)
            for prop, content in tw_matches:
                meta_data[f'twitter_{prop}'] = content
            
            # Standard meta tags
            meta_pattern = r'<meta[^>]*name=["\']([^"\']+)["\'][^>]*content=["\']([^"\']+)["\'][^>]*>'
            meta_matches = re.findall(meta_pattern, html, re.IGNORECASE)
            for name, content in meta_matches:
                if name.lower() in ['description', 'keywords', 'author', 'price', 'availability']:
                    meta_data[name.lower()] = content
            
            logger.debug(f"   Found {len(meta_data)} meta tags")
            return meta_data if meta_data else None
        
        except Exception as e:
            logger.warning(f"Meta tag extraction failed: {e}")
            return None
    
    def extract_data_attributes(self, html: str) -> Optional[Dict[str, str]]:
        """Extract data-* attributes (common in e-commerce)"""
        try:
            data_attrs = {}
            
            patterns = [
                (r'data-product-([^=]+)=["\']([^"\']+)["\']', 'product_'),
                (r'data-price=["\']([^"\']+)["\']', 'price'),
                (r'data-name=["\']([^"\']+)["\']', 'name'),
                (r'data-id=["\']([^"\']+)["\']', 'id'),
                (r'data-sku=["\']([^"\']+)["\']', 'sku'),
            ]
            
            for pattern, prefix in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        key, value = match
                        data_attrs[f'{prefix}{key}'] = value
                    else:
                        data_attrs[prefix] = match
            
            logger.debug(f"   Found {len(data_attrs)} data attributes")
            return data_attrs if data_attrs else None
        
        except Exception as e:
            logger.warning(f"Data attribute extraction failed: {e}")
            return None
    
    def _is_relevant_schema(self, schema_type: str) -> bool:
        """Check if schema type is relevant for extraction"""
        relevant_types = [
            'Product', 'Article', 'NewsArticle', 'BlogPosting',
            'JobPosting', 'Review', 'Organization', 'Person',
            'Event', 'Recipe', 'Book', 'Movie'
        ]
        return any(t in schema_type for t in relevant_types)
