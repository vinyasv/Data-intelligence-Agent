from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    """
    Configuration settings for Universal Web Scraper

    Environment variables can be set in .env file or system environment
    """

    # API Keys
    ANTHROPIC_API_KEY: str
    EXA_API_KEY: Optional[str] = None  # Required for agent mode web search

    # Claude Configuration
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.0

    # Agent Mode Configuration
    AGENT_MODE: bool = False  # Enable conversational agent interface
    INTENT_MODEL: str = "claude-3-5-haiku-20241022"  # Fast model for intent classification
    MAX_CONVERSATION_HISTORY: int = 20  # Maximum messages to retain in context
    WEB_SEARCH_MAX_RESULTS: int = 5  # Default number of search results
    EXA_SEARCH_TYPE: Literal["auto", "neural", "keyword"] = "auto"  # Exa search mode

    # Crawl4AI Configuration
    BROWSER_HEADLESS: bool = True
    BROWSER_TYPE: Literal["chromium", "firefox", "webkit"] = "chromium"
    ENABLE_STEALTH: bool = False  # Disabled due to playwright_stealth dependency issue
    # Use UndetectedAdapter instead for better bot detection bypass

    # Performance
    CHUNK_TOKEN_THRESHOLD: int = 2000
    WORD_COUNT_THRESHOLD: int = 10

    # Caching
    CACHE_MODE: Literal["ENABLED", "DISABLED", "BYPASS"] = "BYPASS"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
