"""
Scrapy Settings Configuration
Optimized for single-page extraction with Playwright
"""
from config import settings as app_settings

# Basic Spider Settings
BOT_NAME = 'universal_scraper'
SPIDER_MODULES = ['scrapers']
NEWSPIDER_MODULE = 'scrapers'

# Obey robots.txt
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 1  # Single page at a time (by design)
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_ITEMS = 1

# Download delay (seconds)
DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 30

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Playwright Configuration
PLAYWRIGHT_BROWSER_TYPE = app_settings.BROWSER_TYPE or 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': app_settings.BROWSER_HEADLESS,
    'args': [
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--ignore-certificate-errors',  # Required for proxy HTTPS
    ]
}

# Page timeout
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

# Abort non-essential requests (speed optimization)
PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type in [
    'stylesheet',  # CSS
    'font',        # Fonts
    'media',       # Videos
    # NOTE: Keep 'image' if extracting image data
]

# Max contexts and pages
PLAYWRIGHT_MAX_CONTEXTS = 2
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1

# Download handlers
DOWNLOAD_HANDLERS = {
    'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
}

# User Agent Rotation
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'middlewares.stealth_middleware.RandomUserAgentMiddleware': 400,
}

# Pipelines
ITEM_PIPELINES = {
    'pipelines.validation_pipeline.ValidationPipeline': 300,
}

# Proxy configuration (BrightData)
if app_settings.PROXY_ENABLED and app_settings.BRIGHTDATA_USERNAME and app_settings.BRIGHTDATA_PASSWORD:
    PROXY_ENABLED = True
    # Add to Playwright launch options
    PLAYWRIGHT_CONTEXTS = {
        'default': {
            'proxy': {
                'server': f'http://{app_settings.BRIGHTDATA_HOST}:{app_settings.BRIGHTDATA_PORT}',
                'username': app_settings.BRIGHTDATA_USERNAME,
                'password': app_settings.BRIGHTDATA_PASSWORD,
            }
        }
    }

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# Telnet console (disable for production)
TELNETCONSOLE_ENABLED = False

# HTTP cache (optional - for development)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'


def get_settings_dict():
    """Return settings as dictionary for CrawlerRunner"""
    settings_dict = {
        'BOT_NAME': BOT_NAME,
        'ROBOTSTXT_OBEY': ROBOTSTXT_OBEY,
        'CONCURRENT_REQUESTS': CONCURRENT_REQUESTS,
        'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
        'DOWNLOAD_TIMEOUT': DOWNLOAD_TIMEOUT,
        'RETRY_ENABLED': RETRY_ENABLED,
        'RETRY_TIMES': RETRY_TIMES,
        'RETRY_HTTP_CODES': RETRY_HTTP_CODES,
        'PLAYWRIGHT_BROWSER_TYPE': PLAYWRIGHT_BROWSER_TYPE,
        'PLAYWRIGHT_LAUNCH_OPTIONS': PLAYWRIGHT_LAUNCH_OPTIONS,
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT,
        'PLAYWRIGHT_ABORT_REQUEST': PLAYWRIGHT_ABORT_REQUEST,
        'PLAYWRIGHT_MAX_CONTEXTS': PLAYWRIGHT_MAX_CONTEXTS,
        'PLAYWRIGHT_MAX_PAGES_PER_CONTEXT': PLAYWRIGHT_MAX_PAGES_PER_CONTEXT,
        'DOWNLOAD_HANDLERS': DOWNLOAD_HANDLERS,
        'DOWNLOADER_MIDDLEWARES': DOWNLOADER_MIDDLEWARES,
        'ITEM_PIPELINES': ITEM_PIPELINES,
        'LOG_LEVEL': LOG_LEVEL,
        'LOG_FORMAT': LOG_FORMAT,
        'TELNETCONSOLE_ENABLED': TELNETCONSOLE_ENABLED,
    }
    
    # Add proxy configuration if enabled
    if app_settings.PROXY_ENABLED and app_settings.BRIGHTDATA_USERNAME and app_settings.BRIGHTDATA_PASSWORD:
        settings_dict['PLAYWRIGHT_CONTEXTS'] = {
            'default': {
                'proxy': {
                    'server': f'http://{app_settings.BRIGHTDATA_HOST}:{app_settings.BRIGHTDATA_PORT}',
                    'username': app_settings.BRIGHTDATA_USERNAME,
                    'password': app_settings.BRIGHTDATA_PASSWORD,
                },
                'ignore_https_errors': True  # Required for proxies with HTTPS
            }
        }
    
    return settings_dict
