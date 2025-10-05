"""
LLM Extractor - Claude-powered extraction with token optimization
"""
import json
from typing import Dict, Any, Optional
from anthropic import Anthropic

from config import settings
from utils import logger


class ScrapyLLMExtractor:
    """
    LLM-based extraction with Claude.
    
    Features:
    - Dynamic schema support
    - Token-optimized prompts
    - Structured data conversion (minimal tokens)
    - Fallback handling
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
    
    async def extract(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from content using LLM.
        
        Args:
            content: Optimized HTML or markdown content
        
        Returns:
            Extracted data matching schema
        """
        try:
            logger.debug(f"🤖 Calling Claude for extraction...")
            logger.debug(f"   Content size: {len(content)} bytes (~{len(content)//4} tokens)")
            
            prompt = self._build_extraction_prompt(content)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text.strip()
            
            # Extract JSON from response
            extracted = self._parse_json_response(result_text)
            
            logger.debug(f"   ✅ Extraction successful")
            return extracted
        
        except Exception as e:
            logger.error(f"   ❌ LLM extraction failed: {e}")
            return None
    
    async def convert_structured_data(
        self, 
        structured_data: Dict[str, Any],
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert structured data (JSON-LD, meta tags) to schema format.
        
        This is MUCH cheaper than extracting from raw HTML:
        - Input: ~500 tokens (just the structured data)
        - Output: ~200 tokens
        - Total: ~700 tokens vs 8,000 tokens (90% cheaper!)
        """
        try:
            logger.debug(f"🔄 Converting structured data...")
            
            prompt = f"""Convert this structured data to match the user's query.

User Query: {query}

Structured Data:
{json.dumps(structured_data, indent=2)}

Target JSON Schema:
{json.dumps(self.json_schema, indent=2)}

Extract the requested fields and return ONLY valid JSON matching the target schema.
If a field is not available, omit it or use null."""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            extracted = self._parse_json_response(result_text)
            
            logger.debug(f"   ✅ Conversion successful")
            return extracted
        
        except Exception as e:
            logger.error(f"   ❌ Structured data conversion failed: {e}")
            return None
    
    def _build_extraction_prompt(self, content: str) -> str:
        """Build extraction prompt with schema"""
        return f"""Extract data from this page according to the schema.

Query: {self.query}

JSON Schema:
{json.dumps(self.json_schema, indent=2)}

Page Content:
{content}

Return ONLY valid JSON matching the schema above. Do not include explanations."""
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        # Remove markdown code blocks if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw response: {text[:200]}...")
            return None
