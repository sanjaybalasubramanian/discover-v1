"""
Search router with caching and failover
"""
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.search.providers import (
    DuckDuckGoSearch, SerperSearch, FirecrawlSearch, SearchResult, SearchError
)
from app.models.outreach import CacheSearch

class SearchRouter:
    """Routes searches through providers with caching and failover"""
    
    def __init__(self, db: Session, cache_enabled: bool = True):
        self.db = db
        self.cache_enabled = cache_enabled
        self.providers = []
        
        # Get configuration from environment
        search_provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo').lower()  # duckduckgo, firecrawl, or serper
        serper_key = os.getenv('SERPER_API_KEY')
        firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
        
        # Setup providers based on configuration
        if search_provider == 'duckduckgo':
            # DuckDuckGo as primary (free, unlimited, no rate limits)
            self.providers.append(DuckDuckGoSearch())
            print("[SearchRouter] Primary: DuckDuckGo (free, unlimited)")
            
            # Add Firecrawl and Serper as fallbacks if configured
            if firecrawl_key:
                self.providers.append(FirecrawlSearch(firecrawl_key))
                print("[SearchRouter] Fallback: Firecrawl")
            if serper_key:
                self.providers.append(SerperSearch(serper_key))
                print("[SearchRouter] Fallback: Serper")
                
        elif search_provider == 'firecrawl':
            # Firecrawl as primary, Serper as fallback
            if firecrawl_key:
                self.providers.append(FirecrawlSearch(firecrawl_key))
                print("[SearchRouter] Primary: Firecrawl")
            if serper_key:
                self.providers.append(SerperSearch(serper_key))
                print("[SearchRouter] Fallback: Serper")
            
            # DuckDuckGo as final fallback
            self.providers.append(DuckDuckGoSearch())
            print("[SearchRouter] Final fallback: DuckDuckGo")
            
        else:
            # Serper as primary (default), Firecrawl as fallback
            if serper_key:
                self.providers.append(SerperSearch(serper_key))
                print("[SearchRouter] Primary: Serper")
            if firecrawl_key:
                self.providers.append(FirecrawlSearch(firecrawl_key))
                print("[SearchRouter] Fallback: Firecrawl")
            
            # DuckDuckGo as final fallback
            self.providers.append(DuckDuckGoSearch())
            print("[SearchRouter] Final fallback: DuckDuckGo")

    
    def search(self, query: str, max_results: int = 10, date_filter: str = None) -> List[SearchResult]:
        """
        Search with caching and failover
        date_filter: 'd' for day, 'w' for week, 'm' for month
        """
        # Check cache first
        if self.cache_enabled:
            cached = self._get_from_cache(query, max_results, date_filter)
            if cached:
                print(f"[SearchRouter] Cache hit for: {query[:50]}...")
                return cached
        
        # Try each provider with failover
        errors = []
        
        for provider in self.providers:
            try:
                print(f"[SearchRouter] Trying {provider.name} for: {query[:50]}...")
                results = provider.search(query, max_results, date_filter)
                
                # Cache successful results
                if self.cache_enabled and results:
                    self._save_to_cache(query, max_results, date_filter, results)
                
                print(f"[SearchRouter] {provider.name} returned {len(results)} results")
                return results
                
            except SearchError as e:
                errors.append(e)
                print(f"[SearchRouter] {provider.name} failed: {e}")
                
                # Skip to next provider on quota error
                if e.is_quota_error:
                    continue
                
                # Also try next provider on other errors
                continue
        
        # All providers failed
        error_msg = "All search providers failed:\n" + "\n".join(
            f"{e.provider}: {str(e)}" for e in errors
        )
        raise Exception(error_msg)
    
    def _get_from_cache(self, query: str, max_results: int, date_filter: Optional[str]) -> Optional[List[SearchResult]]:
        """Get results from cache"""
        query_hash = self._hash_query(query, max_results, date_filter)
        
        cache_entry = self.db.query(CacheSearch).filter(
            CacheSearch.query_hash == query_hash,
            CacheSearch.expires_at > datetime.now()
        ).first()
        
        if cache_entry:
            results_data = json.loads(cache_entry.results)
            return [SearchResult(**r) for r in results_data]
        
        return None
    
    def _save_to_cache(self, query: str, max_results: int, date_filter: Optional[str], results: List[SearchResult]):
        """Save results to cache"""
        query_hash = self._hash_query(query, max_results, date_filter)
        expires_at = datetime.now() + timedelta(hours=24)
        
        results_json = json.dumps([r.to_dict() for r in results])
        
        cache_entry = self.db.query(CacheSearch).filter(
            CacheSearch.query_hash == query_hash
        ).first()
        
        if cache_entry:
            cache_entry.results = results_json
            cache_entry.expires_at = expires_at
        else:
            cache_entry = CacheSearch(
                query_hash=query_hash,
                results=results_json,
                expires_at=expires_at
            )
            self.db.add(cache_entry)
        
        self.db.commit()
    
    def _hash_query(self, query: str, max_results: int, date_filter: Optional[str]) -> str:
        """Hash query parameters for cache key"""
        key = json.dumps({
            'query': query,
            'max_results': max_results,
            'date_filter': date_filter
        })
        return hashlib.sha256(key.encode()).hexdigest()

def build_job_queries() -> List[str]:
    """Build search queries for job discovery"""
    from app.config import get_keywords
    keywords = get_keywords()
    
    queries = []
    roles = keywords['roles'][:3]  # Top 3 roles
    
    # Chennai queries
    for role in roles:
        queries.append(f'site:naukri.com "{role}" Chennai')
        queries.append(f'site:linkedin.com/jobs "{role}" Chennai')
    
    # Remote queries  
    for role in roles:
        queries.append(f'site:naukri.com "{role}" remote')
        queries.append(f'site:linkedin.com/jobs "{role}" remote')
    
    # LinkedIn recruiter posts (best for finding emails)
    queries.append('site:linkedin.com/posts "hiring" "AI engineer" Chennai "@"')
    queries.append('site:linkedin.com/posts "hiring" "GenAI" remote "@"')
    
    return queries

def build_contact_queries(company_name: str, domain: str) -> List[str]:
    """Build contact discovery queries for a company"""
    queries = []
    
    queries.append(f'"{company_name}" recruiter "@{domain}"')
    queries.append(f'"{company_name}" "talent acquisition" "@{domain}"')
    queries.append(f'site:{domain} careers contact')
    queries.append(f'site:{domain} jobs apply email')
    queries.append(f'site:linkedin.com/posts "{company_name}" hiring "@"')
    
    return queries
