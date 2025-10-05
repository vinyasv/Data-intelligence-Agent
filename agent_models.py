"""
Agent-specific Pydantic Models

Data structures for agent communication and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class IntentResult(BaseModel):
    """Result from intent understanding tool"""
    intent: Literal["search_needed", "url_provided", "clarification_needed", "refinement"]
    url: Optional[str] = None
    search_query: Optional[str] = None
    extraction_query: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class SearchResult(BaseModel):
    """Single web search result from Exa"""
    url: str
    title: str
    snippet: str = ""
    published_date: Optional[str] = None
    score: Optional[float] = None
    highlights: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response from web search tool"""
    success: bool
    query: str
    search_type: Optional[str] = None
    results: List[SearchResult] = Field(default_factory=list)
    cost: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ScrapeResponse(BaseModel):
    """Response from scrape tool"""
    success: bool
    url: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
