"""
Mock Search API for development and testing.
This allows testing without using real API keys.
"""
import asyncio
import logging
import random
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Sample mock search results
MOCK_SEARCH_RESULTS = [
    {
        "title": "Understanding Tariffs and Trade Policy",
        "url": "https://example.com/tariffs-explained",
        "snippet": "Tariffs are taxes imposed on imported goods and services. They're often used as tools in international trade policy to protect domestic industries or to gain leverage in negotiations."
    },
    {
        "title": "EU-US Trade Relations: A Historical Perspective",
        "url": "https://example.com/eu-us-trade",
        "snippet": "The European Union and United States have a long history of trade disputes and resolutions. Average tariff levels between the two economies remain similar, despite specific disparities in sectors like agriculture."
    },
    {
        "title": "Impact of Tariffs on Consumer Goods",
        "url": "https://example.com/tariffs-impact",
        "snippet": "Economists warn that broad tariff increases could lead to higher prices for consumers and potential economic disruption. Some businesses have expressed concerns about retaliatory measures."
    },
    {
        "title": "Agriculture and Trade: Challenges and Opportunities",
        "url": "https://example.com/agriculture-trade",
        "snippet": "Agricultural products like jams face varying tariff rates globally. For instance, US jams entering the EU face tariffs exceeding 24%, while EU jams entering the US face tariffs of around 4.5%."
    },
    {
        "title": "Trump's Trade Policy and Business Reactions",
        "url": "https://example.com/trump-trade-policy",
        "snippet": "The administration's focus on trade imbalances has garnered both support and criticism from US businesses. Many companies appreciate attention to unfair trade practices while expressing concern about broader tariff implementations."
    }
]

class MockSearchResult:
    """Mock for a single search result"""
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.html_content = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><p>{snippet}</p><p>Additional mock content for {url}</p></body></html>"

class MockSearchAPI:
    """Mock Search API client"""
    def __init__(self, api_key=None):
        logger.info("Initialized MockSearchAPI")
    
    async def search(self, query: str, num_results: int = 3) -> List[MockSearchResult]:
        """
        Perform a mock search and return results
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of MockSearchResult objects
        """
        logger.info(f"MOCK Search API called with query: {query}")
        
        # Simulate API latency
        await asyncio.sleep(0.5)
        
        # Select a random subset of results
        selected_results = random.sample(
            MOCK_SEARCH_RESULTS, 
            min(num_results, len(MOCK_SEARCH_RESULTS))
        )
        
        return [
            MockSearchResult(
                title=result["title"],
                url=result["url"],
                snippet=result["snippet"]
            )
            for result in selected_results
        ]
    
    async def fetch_page_content(self, url: str) -> str:
        """
        Fetch the HTML content for a given URL
        
        Args:
            url: The URL to fetch
            
        Returns:
            Mock HTML content
        """
        logger.info(f"MOCK fetch page content for URL: {url}")
        
        # Simulate API latency
        await asyncio.sleep(0.7)
        
        # Find matching result or create a generic one
        for result in MOCK_SEARCH_RESULTS:
            if result["url"] == url:
                return f"<html><head><title>{result['title']}</title></head><body><h1>{result['title']}</h1><p>{result['snippet']}</p><p>Additional mock content for {url}</p></body></html>"
        
        # Generic response if URL not found
        return f"<html><head><title>Page at {url}</title></head><body><h1>Mock page for {url}</h1><p>This is mock content generated for testing purposes.</p></body></html>" 