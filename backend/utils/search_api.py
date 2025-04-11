"""
Google Search API for real search functionality
"""

import aiohttp
import logging
import json
from typing import List, Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class SearchAPI:
    """
    Client for Google Custom Search API.
    
    This class provides methods to search the web using Google's Custom Search API.
    """
    
    def __init__(self, api_key: str, cx: Optional[str] = None):
        """
        Initialize the SearchAPI with API credentials.
        
        Args:
            api_key: Google API key
            cx: Optional Custom Search Engine ID (if not provided, will be read from env)
        """
        self.api_key = api_key
        self.cx = cx
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        logger.info("SearchAPI initialized with real Google Search API")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a search query and return results.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
        
        Returns:
            List of search result objects
        """
        if not self.api_key:
            logger.error("No API key provided for Google Search")
            return [{"title": "Error", "snippet": "No API key provided for Google Search"}]
        
        # Cap num_results at 10 (Google's maximum per request)
        num_results = min(num_results, 10)
        
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.cx,
            'num': num_results
        }
        
        try:
            logger.info(f"Searching for: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Search API error: {response.status} - {error_text}")
                        return [{"title": "Error", "snippet": f"API error: {response.status}"}]
                    
                    data = await response.json()
                    
                    if 'items' not in data:
                        logger.warning(f"No search results for query: {query}")
                        return []
                    
                    # Extract relevant information from each result
                    results = []
                    for item in data['items']:
                        result = {
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': item.get('displayLink', '')
                        }
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error during Google search: {str(e)}")
            return [{"title": "Error", "snippet": f"Search error: {str(e)}"}]
            
    async def search_text_only(self, query: str, num_results: int = 5) -> List[str]:
        """
        Perform a search and return only the text snippets.
        This is useful for providing context to LLMs.
        
        Args:
            query: The search query string
            num_results: Number of results to return
            
        Returns:
            List of text snippets
        """
        results = await self.search(query, num_results)
        snippets = []
        
        for result in results:
            if 'snippet' in result:
                snippets.append(f"{result.get('title', '')}: {result.get('snippet', '')}")
        
        return snippets 