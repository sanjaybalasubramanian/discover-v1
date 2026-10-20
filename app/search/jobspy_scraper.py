"""
JobSpy integration for direct job scraping from LinkedIn, Naukri, Indeed, Glassdoor, ZipRecruiter
"""
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd


class JobSpyScraper:
    """
    Scrape jobs from multiple sites with intelligent rate limiting
    """

    # Rate limit settings (requests per minute) - conservative for reliability
    RATE_LIMITS = {
        'linkedin': 30,      # 1 req per 2 sec
        'naukri': 30,        # 1 req per 2 sec
        'indeed': 120,       # No rate limit (best scraper)
        'glassdoor': 20,     # 1 req per 3 sec (aggressive blocking)
        'ziprecruiter': 30,  # 1 req per 2 sec
    }

    def __init__(self):
        self.last_request_time = {}
        self.retry_wait_time = 60  # Initial wait on 429

    def scrape_jobs(
        self,
        search_term: str,
        location: str,
        sites: List[str] = ["linkedin", "naukri", "indeed", "glassdoor"],
        results_wanted: int = 20,
        hours_old: int = 168,  # 7 days
        country: str = "India"
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from multiple sites with rate limiting

        Args:
            search_term: Job search query (e.g., "GenAI engineer")
            location: Job location
            sites: List of sites to scrape
            results_wanted: Max results per site
            hours_old: Filter jobs posted within N hours (default: 7 days)
            country: Country for Indeed

        Returns:
            List of job dictionaries
        """
        from jobspy import scrape_jobs as jobspy_scrape

        print(f"[JobSpy] Scraping {', '.join(sites)}")
        print(f"[JobSpy] Query: '{search_term}' in {location}")
        print(f"[JobSpy] Results wanted: {results_wanted} per site, within {hours_old}h")

        # Apply rate limiting before request
        self._wait_for_rate_limit(sites)

        # Try scraping with retries
        for attempt in range(3):
            try:
                jobs_df = jobspy_scrape(
                    site_name=sites,
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed=country,
                )

                if jobs_df is None or jobs_df.empty:
                    print("[JobSpy] No jobs found")
                    return []

                print(f"[JobSpy] ✓ Found {len(jobs_df)} jobs")

                # Convert to list of dicts
                jobs = self._convert_to_jobs(jobs_df)
                return jobs

            except Exception as e:
                error_str = str(e)

                # Check for rate limiting (429)
                if '429' in error_str or 'rate limit' in error_str.lower():
                    wait_time = self.retry_wait_time * (2 ** attempt)  # Exponential backoff
                    print(f"[JobSpy] ⚠ Rate limited (429). Waiting {wait_time}s before retry {attempt+1}/3")
                    time.sleep(wait_time)
                    continue

                # Other errors
                print(f"[JobSpy] ✗ Error on attempt {attempt+1}/3: {e}")

                if attempt < 2:
                    time.sleep(10)  # Short wait before retry
                    continue
                else:
                    print("[JobSpy] Max retries reached, skipping this search")
                    return []

        return []

    def _wait_for_rate_limit(self, sites: List[str]):
        """Apply rate limiting delays"""
        # Find the most restrictive rate limit
        min_delay = 0
        for site in sites:
            if site in self.RATE_LIMITS:
                rpm = self.RATE_LIMITS[site]
                delay = 60.0 / rpm  # Seconds between requests
                min_delay = max(min_delay, delay)

        # Check if we need to wait
        for site in sites:
            if site in self.last_request_time:
                elapsed = time.time() - self.last_request_time[site]
                if elapsed < min_delay:
                    wait = min_delay - elapsed
                    print(f"[JobSpy] Rate limiting: waiting {wait:.1f}s for {site}")
                    time.sleep(wait)

        # Update last request time
        current_time = time.time()
        for site in sites:
            self.last_request_time[site] = current_time

    def _convert_to_jobs(self, jobs_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to list of job dicts"""
        jobs = []

        for _, row in jobs_df.iterrows():
            # Format salary
            salary = self._format_salary(row)

            # Convert date_posted to date object
            date_posted = None
            if pd.notna(row.get('date_posted')):
                try:
                    date_posted = pd.to_datetime(row.get('date_posted')).date()
                except Exception:
                    pass

            job = {
                'site': row.get('site'),
                'title': row.get('title'),
                'company': row.get('company'),
                'location': row.get('location'),
                'date_posted': date_posted,
                'job_url': row.get('job_url'),
                'job_url_direct': row.get('job_url_direct'),
                'description': row.get('description'),
                'job_type': row.get('job_type'),  # fulltime, parttime, etc.
                'salary': salary,
                'is_remote': bool(row.get('is_remote')) if pd.notna(row.get('is_remote')) else False,
                'company_url': row.get('company_url'),
                'company_industry': row.get('company_industry'),
            }

            jobs.append(job)

        return jobs

    def _format_salary(self, row) -> Optional[str]:
        """Format salary info from row"""
        try:
            if pd.isna(row.get('min_amount')) and pd.isna(row.get('max_amount')):
                return None

            min_amt = row.get('min_amount')
            max_amt = row.get('max_amount')
            currency = row.get('currency', '₹')
            interval = row.get('interval', 'yearly')

            if pd.notna(min_amt) and pd.notna(max_amt):
                return f"{currency}{int(min_amt)}-{int(max_amt)}/{interval}"
            elif pd.notna(min_amt):
                return f"{currency}{int(min_amt)}+/{interval}"
            elif pd.notna(max_amt):
                return f"Up to {currency}{int(max_amt)}/{interval}"

            return None
        except Exception:
            return None


def build_jobspy_searches() -> List[Dict[str, Any]]:
    """
    Build JobSpy search configurations for Remote + Chennai

    Returns:
        List of search configuration dicts
    """
    from app.config import get_keywords
    keywords = get_keywords()

    searches = []
    roles = keywords['roles'][:5]  # Top 5 roles

    # Get sites from environment (default: linkedin, indeed, naukri, glassdoor)
    sites_str = os.getenv('JOBSPY_SITES', 'linkedin,indeed,naukri,glassdoor')
    sites = [s.strip() for s in sites_str.split(',') if s.strip()]

    print(f"[JobSpy] Using sites: {', '.join(sites)}")

    # Chennai jobs (top 3 roles)
    for role in roles[:3]:
        searches.append({
            'search_term': role,
            'location': 'Chennai, Tamil Nadu, India',
            'sites': sites,
            'results_wanted': int(os.getenv('JOBSPY_RESULTS_PER_SITE', '25')),
            'hours_old': int(os.getenv('JOBSPY_HOURS_OLD', '168')),
        })

    # Remote jobs (top 3 roles)
    for role in roles[:3]:
        searches.append({
            'search_term': f"{role} remote",
            'location': 'India',
            'sites': sites,
            'results_wanted': int(os.getenv('JOBSPY_RESULTS_PER_SITE', '25')),
            'hours_old': int(os.getenv('JOBSPY_HOURS_OLD', '168')),
        })

    return searches

