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

    # Web Scraping Configuration
    BROWSER_HEADLESS: bool = True
    BROWSER_TYPE: Literal["chromium", "firefox", "webkit"] = "chromium"
    ENABLE_STEALTH: bool = False  # Disabled due to playwright_stealth dependency issue
    # Use UndetectedAdapter instead for better bot detection bypass

    # Bright Data Residential Proxy Configuration
    PROXY_ENABLED: bool = False
    BRIGHTDATA_USERNAME: Optional[str] = None  # Format: customer-USER-zone-ZONE or customer-USER-zone-ZONE-session-SESSION_ID
    BRIGHTDATA_PASSWORD: Optional[str] = None
    BRIGHTDATA_HOST: str = "zproxy.lum-superproxy.io"  # Bright Data super proxy host
    BRIGHTDATA_PORT: int = 22225  # Default port for residential proxies
    PROXY_ROTATION: str = "request"  # "request" for new IP each time, "session" for sticky sessions

    # Performance
    CHUNK_TOKEN_THRESHOLD: int = 2000
    WORD_COUNT_THRESHOLD: int = 10

    # Caching
    CACHE_MODE: Literal["ENABLED", "DISABLED", "BYPASS"] = "BYPASS"

    # JS-Heavy Site Handling (Playwright Best Practices)
    ENABLE_FULL_PAGE_SCAN: bool = True  # Enable page scrolling for JS-heavy sites
    IMAGE_WAIT_ENABLED: bool = True  # Wait for images on e-commerce sites
    SCROLL_DELAY: float = 0.5  # Delay between scroll steps (seconds)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
