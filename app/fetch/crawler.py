"""
Web page fetching using Crawl4AI with stealth mode and optional browser profile
"""
import asyncio
import os
import random
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from urllib.parse import urlparse

# OPTIONAL: Skip these domains for automated fetch_page calls
# LinkedIn/Naukri are now allowed via scrape_job_for_recruiter tool
RESTRICTED_FETCH_DOMAINS = [
    # Removed: 'linkedin.com', 'naukri.com' - now allowed for authenticated scraping
]

# Stealth mode configuration
USE_STEALTH_MODE = os.getenv('USE_STEALTH_MODE', 'true').lower() == 'true'
USE_BROWSER_PROFILE = os.getenv('USE_BROWSER_PROFILE', 'false').lower() == 'true'
CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH', r"C:\Users\91787\AppData\Local\Google\Chrome\User Data")

# Random user agents (rotate to look more natural)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def should_skip_fetch(url: str) -> bool:
    """
    Check if URL should be skipped (LinkedIn, Naukri)
    These sites provide good snippets, don't need full fetch
    """
    try:
        domain = urlparse(url).netloc.lower()
        return any(domain.endswith(restricted) for restricted in RESTRICTED_FETCH_DOMAINS)
    except Exception:
        return False

def get_browser_config() -> Optional[BrowserConfig]:
    """
    Get browser configuration with stealth mode
    
    Returns:
        BrowserConfig with stealth settings, or None for default
    """
    if not USE_STEALTH_MODE and not USE_BROWSER_PROFILE:
        return None
    
    config_args = []
    
    if USE_STEALTH_MODE:
        # Stealth mode: Hide automation signals
        config_args.extend([
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            f'--user-agent={random.choice(USER_AGENTS)}'
        ])
    
    config = BrowserConfig(
        headless=not USE_BROWSER_PROFILE,  # Show browser if using profile
        extra_args=config_args,
        verbose=False
    )
    
    # Use real Chrome profile if enabled
    if USE_BROWSER_PROFILE:
        config.user_data_dir = CHROME_PROFILE_PATH
        print(f"[Stealth] Using Chrome profile: {CHROME_PROFILE_PATH}")
        print(f"[Stealth] WARNING: Close your Chrome browser before running!")
    
    return config

async def fetch_page(url: str) -> Optional[str]:
    """
    Fetch full page content using Crawl4AI with stealth mode
    
    IMPORTANT: Skips LinkedIn and Naukri (use snippets for those)
    
    Args:
        url: Page URL to fetch
    
    Returns:
        Clean text content or None if skipped/failed
    """
    
    # Check if domain is restricted
    if should_skip_fetch(url):
        print(f"[Fetch] Skipping restricted domain: {url}")
        return None
    
    try:
        # Add random delay to look more human (1-3 seconds)
        if USE_STEALTH_MODE:
            await asyncio.sleep(random.uniform(1.0, 3.0))
        
        browser_config = get_browser_config()
        
        # Create crawler with or without browser config
        if browser_config:
            async with AsyncWebCrawler(
                config=browser_config,
                verbose=False
            ) as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=False,
                    screenshot=False
                )
                
                if result.success:
                    content = result.markdown or result.cleaned_html or ""
                    print(f"[Fetch] Success: {url} ({len(content)} chars)")
                    return content
                else:
                    print(f"[Fetch] Failed: {url} - {result.error_message}")
                    return None
        else:
            # No browser config - use defaults
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=False,
                    screenshot=False
                )
                
                if result.success:
                    content = result.markdown or result.cleaned_html or ""
                    print(f"[Fetch] Success: {url} ({len(content)} chars)")
                    return content
                else:
                    print(f"[Fetch] Failed: {url} - {result.error_message}")
                    return None
                
    except Exception as e:
        print(f"[Fetch] Error: {url} - {e}")
        return None

async def fetch_pages_batch(urls: list[str], max_concurrent: int = 5) -> dict[str, Optional[str]]:
    """
    Fetch multiple pages concurrently (skips restricted domains)
    
    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
    
    Returns:
        Dict mapping URL to content (or None if failed/skipped)
    """
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_limit(url: str):
        async with semaphore:
            content = await fetch_page(url)
            return url, content
    
    tasks = [fetch_with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    return dict(results)

