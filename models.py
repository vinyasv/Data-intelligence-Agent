from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class ExtractionResult(BaseModel):
    """
    Base model for extraction results
    """
    url: str
    query: str
    extracted_data: Dict[str, Any]
    extraction_strategy: str
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


class SchemaGenerationResult(BaseModel):
    """
    Result from schema generation
    """
    query: str
    pydantic_code: str
    json_schema: Dict[str, Any]
    model_name: str


# Custom Exceptions
class ExtractionError(Exception):
    """Raised when extraction fails"""
    pass


class SchemaGenerationError(Exception):
    """Raised when schema generation fails"""
    pass


class StrategyRoutingError(Exception):
    """Raised when strategy routing fails"""
    pass


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass
