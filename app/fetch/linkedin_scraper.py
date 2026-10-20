"""
Simple LinkedIn/Naukri scraper with authenticated session
Uses your Chrome profile for LinkedIn login
"""
import asyncio
import random
from typing import Optional, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig
from bs4 import BeautifulSoup
import re

# Safety: Rate limiting
DELAY_BETWEEN_REQUESTS = (5, 10)  # Random 5-10 seconds
MAX_PAGES_PER_COMPANY = 3

# Chrome profile path (your logged-in session)
CHROME_PROFILE_PATH = r"C:\Users\91787\AppData\Local\Google\Chrome\User Data"


async def scrape_linkedin_job(job_url: str) -> Dict[str, Optional[str]]:
    """
    Scrape LinkedIn job post for recruiter contact info
    
    Uses your Chrome profile (must be logged into LinkedIn)
    
    Args:
        job_url: LinkedIn job URL (e.g., linkedin.com/jobs/view/12345)
    
    Returns:
        dict with 'name', 'email', 'title', 'source'
    """
    try:
        browser_config = BrowserConfig(
            headless=False,  # Show browser (looks more human)
            user_data_dir=CHROME_PROFILE_PATH,
            extra_args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        async with AsyncWebCrawler(browser_config=browser_config, verbose=False) as crawler:
            print(f"[LinkedIn] Scraping job: {job_url}")
            
            result = await crawler.arun(
                url=job_url,
                bypass_cache=True,
                wait_for="body"
            )
            
            if not result.success:
                print(f"[LinkedIn] Scrape failed: {result.error_message}")
                return {}
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract recruiter info from job poster section
            recruiter_data = {}
            
            # Try to find recruiter name
            name_elem = soup.select_one('.jobs-poster__name, .hirer-card__hirer-information-name')
            if name_elem:
                recruiter_data['name'] = name_elem.get_text(strip=True)
            
            # Try to find title
            title_elem = soup.select_one('.jobs-poster__job-title, .hirer-card__hirer-information-position')
            if title_elem:
                recruiter_data['title'] = title_elem.get_text(strip=True)
            
            # Look for email in page
            email_links = soup.select('a[href^="mailto:"]')
            if email_links:
                email = email_links[0]['href'].replace('mailto:', '').strip()
                recruiter_data['email'] = email
            else:
                # Try to find email in text content
                text_content = soup.get_text()
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text_content)
                if emails:
                    recruiter_data['email'] = emails[0]
            
            recruiter_data['source'] = 'linkedin_scrape'
            
            print(f"[LinkedIn] Found: {recruiter_data}")
            
            # Human-like delay
            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
            
            return recruiter_data
            
    except Exception as e:
        print(f"[LinkedIn] Scrape error: {e}")
        return {}


async def scrape_naukri_job(job_url: str) -> Dict[str, Optional[str]]:
    """
    Scrape Naukri job post for recruiter contact info
    
    Args:
        job_url: Naukri job URL
    
    Returns:
        dict with 'name', 'email', 'title', 'source'
    """
    try:
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            print(f"[Naukri] Scraping job: {job_url}")
            
            result = await crawler.arun(
                url=job_url,
                bypass_cache=True
            )
            
            if not result.success:
                print(f"[Naukri] Scrape failed: {result.error_message}")
                return {}
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            recruiter_data = {}
            
            # Extract recruiter name
            name_elem = soup.select_one('.recruiter-name, .rec-name')
            if name_elem:
                recruiter_data['name'] = name_elem.get_text(strip=True)
            
            # Look for email
            email_links = soup.select('a[href^="mailto:"]')
            if email_links:
                email = email_links[0]['href'].replace('mailto:', '').strip()
                recruiter_data['email'] = email
            else:
                # Try to find email in text
                text_content = soup.get_text()
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text_content)
                if emails:
                    recruiter_data['email'] = emails[0]
            
            recruiter_data['source'] = 'naukri_scrape'
            
            print(f"[Naukri] Found: {recruiter_data}")
            
            # Human-like delay
            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
            
            return recruiter_data
            
    except Exception as e:
        print(f"[Naukri] Scrape error: {e}")
        return {}


async def scrape_jobs_batch(job_urls: list[str], max_scrapes: int = MAX_PAGES_PER_COMPANY) -> list[dict]:
    """
    Scrape multiple job URLs (with limit for safety)
    
    Args:
        job_urls: List of LinkedIn/Naukri job URLs
        max_scrapes: Maximum number to scrape (default: 3)
    
    Returns:
        List of recruiter data dicts
    """
    results = []
    
    # Limit scraping to avoid detection
    urls_to_scrape = job_urls[:max_scrapes]
    
    for url in urls_to_scrape:
        if 'linkedin.com/jobs' in url:
            data = await scrape_linkedin_job(url)
        elif 'naukri.com' in url:
            data = await scrape_naukri_job(url)
        else:
            continue
        
        if data:
            results.append(data)
    
    return results

