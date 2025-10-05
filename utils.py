import logging
import sys
from typing import Any, Dict
from datetime import datetime


# Configure logging
def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("universal_scraper")
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler if not already added
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Default logger instance (WARNING level to hide internal logs in CLI)
logger = setup_logging("WARNING")


def sanitize_url(url: str) -> str:
    """
    Sanitize and validate URL

    Args:
        url: Raw URL string

    Returns:
        Sanitized URL string
    """
    url = url.strip()

    # Add https:// if no protocol specified
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    return url


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime for logging/output

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with default

    Args:
        data: Dictionary to get value from
        key: Key to lookup
        default: Default value if key not found

    Returns:
        Value or default
    """
    return data.get(key, default)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to max length

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
