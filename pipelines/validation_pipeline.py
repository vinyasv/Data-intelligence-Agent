"""
Pydantic validation pipeline for Scrapy
"""
from pydantic import ValidationError as PydanticValidationError
from utils import logger


class ValidationPipeline:
    """
    Validate extracted data against Pydantic schema.
    
    If validation fails, logs error but doesn't block pipeline.
    """
    
    def process_item(self, item, spider):
        """Validate item against spider's Pydantic model"""
        if not hasattr(spider, 'pydantic_model') or not spider.pydantic_model:
            return item
        
        try:
            # Validate
            validated = spider.pydantic_model(**item['extracted_data'])
            item['extracted_data'] = validated.model_dump()
            logger.debug("✅ Validation passed")
        except PydanticValidationError as e:
            logger.warning(f"⚠️  Validation failed: {e}")
            # Don't block - return unvalidated data
        
        return item
