"""
Smart Wait Strategies for Different Website Types

Flexible, adaptive wait strategies that work on any site without hardcoded selectors.
Uses timeouts and network idle detection instead of fragile CSS selectors.
"""
from typing import List, Optional
from scrapy_playwright.page import PageMethod


# Domain categories for different wait strategies
E_COMMERCE_DOMAINS = [
    'nike.com', 'adidas.com', 'abercrombie.com', 'zara.com', 'hm.com',
    'amazon.com', 'urbanoutfitters.com', 'wayfair.com', 'etsy.com',
    'target.com', 'walmart.com', 'bestbuy.com', 'macys.com'
]

NEWS_CONTENT_DOMAINS = [
    'ycombinator.com', 'news.ycombinator.com', 'techcrunch.com',
    'theverge.com', 'reddit.com', 'medium.com'
]

SOCIAL_MEDIA_DOMAINS = [
    'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'linkedin.com'
]


def get_domain_category(domain: str) -> str:
    """Categorize domain to determine wait strategy"""
    domain_lower = domain.lower()
    if domain_lower.startswith('www.'):
        domain_lower = domain_lower[4:]
    
    # Check categories
    if any(d in domain_lower for d in E_COMMERCE_DOMAINS):
        return 'ecommerce'
    elif any(d in domain_lower for d in NEWS_CONTENT_DOMAINS):
        return 'news'
    elif any(d in domain_lower for d in SOCIAL_MEDIA_DOMAINS):
        return 'social'
    else:
        return 'general'


def get_playwright_methods(domain: str, query: str) -> List[PageMethod]:
    """
    Generate smart, adaptive Playwright page methods.
    
    NO HARDCODED SELECTORS - uses flexible timeouts and network detection.
    This works on ANY site without failing on missing selectors.
    
    Args:
        domain: The domain name (e.g., "nike.com")
        query: The extraction query (used for context)
    
    Returns:
        List of PageMethod objects for Scrapy-Playwright
    """
    category = get_domain_category(domain)
    methods = []
    
    # Strategy based on category
    if category == 'ecommerce':
        # E-commerce: Wait for network idle (JS-heavy, dynamic pricing)
        methods.append(
            PageMethod('wait_for_load_state', 'networkidle', timeout=10000)
        )
        # Additional buffer for lazy-loaded content
        methods.append(
            PageMethod('wait_for_timeout', 2000)
        )
        
    elif category == 'news':
        # News sites: Usually fast, minimal JS
        methods.append(
            PageMethod('wait_for_load_state', 'domcontentloaded', timeout=5000)
        )
        methods.append(
            PageMethod('wait_for_timeout', 1000)
        )
        
    elif category == 'social':
        # Social media: Heavy JS, infinite scroll
        methods.append(
            PageMethod('wait_for_load_state', 'networkidle', timeout=15000)
        )
        methods.append(
            PageMethod('wait_for_timeout', 3000)
        )
        
    else:
        # General: Balanced approach
        methods.append(
            PageMethod('wait_for_load_state', 'domcontentloaded', timeout=8000)
        )
        methods.append(
            PageMethod('wait_for_timeout', 1500)
        )
    
    # Scroll to trigger lazy loading if query suggests multiple items
    if any(keyword in query.lower() for keyword in ['all', 'list', 'multiple', 'first 5', 'top', 'products']):
        methods.append(
            PageMethod('evaluate', '''
                async () => {
                    // Smooth scroll to trigger lazy loading
                    window.scrollTo({top: document.body.scrollHeight / 2, behavior: 'smooth'});
                    await new Promise(r => setTimeout(r, 500));
                    window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                    await new Promise(r => setTimeout(r, 500));
                }
            ''')
        )
    
    # Remove annoying popups/modals that block content
    methods.append(
        PageMethod('evaluate', '''
            () => {
                // Remove common overlay/modal patterns
                const hideSelectors = [
                    '[class*="modal"]',
                    '[class*="popup"]',
                    '[class*="overlay"]',
                    '[id*="modal"]',
                    '[id*="popup"]',
                    '[class*="cookie"]',
                    '[id*="cookie"]'
                ];
                
                hideSelectors.forEach(sel => {
                    try {
                        document.querySelectorAll(sel).forEach(el => {
                            if (el && el.style) {
                                el.style.display = 'none';
                                el.style.visibility = 'hidden';
                            }
                        });
                    } catch(e) {}
                });
                
                // Also remove any element with z-index > 1000 (likely a modal)
                try {
                    document.querySelectorAll('*').forEach(el => {
                        const zIndex = parseInt(window.getComputedStyle(el).zIndex);
                        if (zIndex > 1000) {
                            el.style.display = 'none';
                        }
                    });
                } catch(e) {}
            }
        ''')
    )
    
    return methods


# Legacy function for backward compatibility
def get_playwright_page_methods(domain: str) -> List[PageMethod]:
    """Legacy function - calls new get_playwright_methods"""
    return get_playwright_methods(domain, "")


def get_wait_selector(domain: str) -> Optional[str]:
    """DEPRECATED - Returns None (we don't use hardcoded selectors anymore)"""
    return None


def is_js_heavy(domain: str) -> bool:
    """Check if domain is JS-heavy"""
    category = get_domain_category(domain)
    return category in ['ecommerce', 'social']