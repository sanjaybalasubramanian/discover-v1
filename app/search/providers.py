"""
Search providers and router
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from ddgs import DDGS

class SearchResult:
    """Search result data class"""
    def __init__(self, title: str, url: str, snippet: str, date: str = None):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.date = date
    
    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'date': self.date
        }

class SearchError(Exception):
    """Search provider error"""
    def __init__(self, message: str, provider: str, is_quota_error: bool = False):
        super().__init__(message)
        self.provider = provider
        self.is_quota_error = is_quota_error

class DuckDuckGoSearch:
    """DuckDuckGo search using ddgs library (free, unlimited)"""
    
    name = 'duckduckgo'
    
    def search(self, query: str, max_results: int = 10, date_filter: str = None) -> List[SearchResult]:
        """
        Search DuckDuckGo using ddgs library
        date_filter: 'd' for day, 'w' for week, 'm' for month
        """
        try:
            # Map date_filter to timelimit param
            timelimit = None
            if date_filter:
                mapping = {'d': 'd', 'w': 'w', 'm': 'm'}
                timelimit = mapping.get(date_filter)
            
            # Use DDGS library
            results = []
            search_results = DDGS().text(query, max_results=max_results, timelimit=timelimit)
            
            for item in search_results:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('href', ''),
                    snippet=item.get('body', ''),
                    date=None
                ))
            
            return results
            
        except Exception as e:
            # Return empty list if no results found (not an error)
            if 'No results found' in str(e):
                return []
            raise SearchError(f"DuckDuckGo search failed: {str(e)}", 'duckduckgo')


class SerperSearch:
    """Serper.dev Google Search API"""
    
    name = 'serper'
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str, max_results: int = 10, date_filter: str = None) -> List[SearchResult]:
        """Search using Serper API"""
        
        payload = {
            'q': query,
            'num': max_results,
            'gl': 'in'  # India
        }
        
        if date_filter:
            # Map to Google's date filter format
            mapping = {'d': 'qdr:d', 'w': 'qdr:w', 'm': 'qdr:m'}
            payload['tbs'] = mapping.get(date_filter, 'qdr:d2')
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://google.serper.dev/search',
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('organic', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    date=item.get('date')
                ))
            
            return results
            
        except requests.exceptions.HTTPError as e:
            is_quota = e.response.status_code == 429
            raise SearchError(f"Serper search failed: {str(e)}", 'serper', is_quota)
        except Exception as e:
            raise SearchError(f"Serper search failed: {str(e)}", 'serper')


class FirecrawlSearch:
    """Firecrawl Search API"""
    
    name = 'firecrawl'
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str, max_results: int = 10, date_filter: str = None) -> List[SearchResult]:
        """Search using Firecrawl API"""
        
        payload = {
            'query': query,
            'limit': max_results
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://api.firecrawl.dev/v1/search',
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Firecrawl returns results in 'data' array
            for item in data.get('data', [])[:max_results]:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('description', ''),
                    date=None
                ))
            
            return results
            
        except requests.exceptions.HTTPError as e:
            is_quota = e.response.status_code == 429
            raise SearchError(f"Firecrawl search failed: {str(e)}", 'firecrawl', is_quota)
        except Exception as e:
            raise SearchError(f"Firecrawl search failed: {str(e)}", 'firecrawl')

