"""
Utility functions for the LangGraph workflow
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from .types import AnalysisState

# Import agents
from .agents import (
    HeadNode,
    FakeNewsAgent,
    CredibilityAgent,
    SentimentAgent,
    SummaryAgent,
    ValidatorAgent
)

# Mock OpenAI client for development
try:
    from utils.mock_openai import MockOpenAI
    from utils.mock_search import MockSearchAPI
except ImportError:
    # Fallback for when imports fail
    class MockOpenAI:
        async def chat_create(self, *args, **kwargs):
            return {"choices": [{"message": {"content": "Mock response from OpenAI"}}]}
            
    class MockSearchAPI:
        async def search(self, *args, **kwargs):
            return ["Mock search result 1", "Mock search result 2"]

# Use real or mock clients based on environment
if os.environ.get("USE_MOCK_APIS", "true").lower() == "true":
    logger.info("Using MOCK APIs for development")
    openai_client = MockOpenAI()
    search_api = MockSearchAPI()
else:
    logger.info("Using REAL APIs")
    
    # Initialize OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("No OpenAI API key found in environment variables")
    
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    
    # Initialize Google Search API
    search_api_key = os.environ.get("SEARCH_API_KEY")
    search_engine_cx = os.environ.get("SEARCH_ENGINE_CX")
    
    if not search_api_key:
        logger.warning("No Search API key found in environment variables")
    
    try:
        from utils.search_api import SearchAPI
        search_api = SearchAPI(api_key=search_api_key, cx=search_engine_cx)
    except ImportError as e:
        logger.error(f"Failed to import SearchAPI: {str(e)}")
        # Fallback if import fails
        class SearchAPI:
            def __init__(self, api_key=None, cx=None):
                self.api_key = api_key
                self.cx = cx
                
            async def search(self, *args, **kwargs):
                return ["Unable to import real search API"]
        search_api = SearchAPI(api_key=search_api_key, cx=search_engine_cx)

async def fetch_article_content(url: str) -> Dict[str, Any]:
    """Fetch article content from URL"""
    logger.info(f"Fetching article content from: {url}")
    
    # In a production implementation, this would use a more robust scraper
    try:
        # Basic article fetching
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article: {response.status}")
                    # Fall back to mock content
                    return create_mock_content(url)
                    
                html = await response.text()
                
                # Extract article information using a very basic approach
                # In a real implementation, you would use something more robust
                # like newspaper3k, trafilatura, or a specialized scraping library
                title = extract_title(html) or "Unknown Title"
                content = extract_content(html) or f"Failed to extract content from {url}"
                source = extract_source(url)
                
                return {
                    "title": title,
                    "content": content,
                    "source": source,
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
    except Exception as e:
        logger.error(f"Error fetching article: {str(e)}")
        # Fall back to mock content
        return create_mock_content(url)

def create_mock_content(url: str) -> Dict[str, Any]:
    """Create mock content based on URL if fetching fails"""
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        # Generate a title based on the URL path
        if path and path != "/":
            # Convert path to title format (e.g., "/world-news/article" -> "World News Article")
            path_parts = path.strip('/').replace('-', ' ').replace('/', ' ').split()
            title_parts = [part.capitalize() for part in path_parts]
            mock_title = " ".join(title_parts) if title_parts else "Mock Article"
        else:
            mock_title = "Mock Article Title"
            
        # Extract source from domain
        source_name = domain.replace("www.", "")
        for tld in [".com", ".org", ".net", ".co.uk", ".gov"]:
            source_name = source_name.replace(tld, "")
        source_name = source_name.split(".")[-1].capitalize()
        if not source_name:
            source_name = "Mock News Source"
            
    except Exception as e:
        logger.error(f"Error parsing URL: {str(e)}")
        mock_title = "Mock Article Title"
        source_name = "Mock News Source"
    
    # Mock article data with URL-based customization
    return {
        "title": mock_title,
        "content": f"This is a mock article content from {source_name} about {mock_title.lower()}. It would normally contain the full text of the news article that would be processed by our agents. The article was originally found at {url}.",
        "source": source_name,
        "url": url,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

def extract_title(html: str) -> Optional[str]:
    """Extract title from HTML - basic implementation"""
    import re
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        return title_match.group(1).strip()
    return None

def extract_content(html: str) -> Optional[str]:
    """Extract content from HTML - basic implementation"""
    import re
    
    # Try to find article content in common containers
    content_tags = [
        r'<article[^>]*>(.*?)</article>',
        r'<div class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
        r'<div id="[^"]*article[^"]*"[^>]*>(.*?)</div>',
        r'<div class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div class="[^"]*body[^"]*"[^>]*>(.*?)</div>'
    ]
    
    for pattern in content_tags:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            # Clean up the HTML to get just text
            content = match.group(1)
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', ' ', content)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            return content
    
    # Fallback to extracting paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
    if paragraphs:
        # Clean and join paragraphs
        cleaned_paragraphs = []
        for p in paragraphs:
            # Remove HTML tags
            p = re.sub(r'<[^>]+>', '', p)
            # Remove extra whitespace
            p = re.sub(r'\s+', ' ', p).strip()
            if len(p) > 30:  # Only include substantial paragraphs
                cleaned_paragraphs.append(p)
        
        return '\n\n'.join(cleaned_paragraphs)
    
    return None

def extract_source(url: str) -> str:
    """Extract source name from URL"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. and get the base domain
        source = domain.replace('www.', '')
        # Remove TLD
        source = source.split('.')[0]
        return source.capitalize()
    except Exception:
        return "Unknown Source"

async def create_workflow() -> Any:
    """
    Create the LangGraph workflow.
    
    This function creates and configures the LangGraph workflow 
    by setting up nodes and connections between agents.
    """
    try:
        # Try to import langgraph - this may fail if there are dependency conflicts
        try:
            import langgraph.graph as lg
        except ImportError as e:
            logger.warning(f"LangGraph import failed: {str(e)}")
            logger.warning("This is likely due to a dependency conflict between langgraph and langchain.")
            logger.warning("Consider updating your requirements.txt file with compatible versions.")
            return None
        
        # Initialize agents
        head_node = HeadNode()
        fake_news_agent = FakeNewsAgent()
        credibility_agent = CredibilityAgent()
        sentiment_agent = SentimentAgent()
        summary_agent = SummaryAgent()
        validator = ValidatorAgent()
        
        # Import routers
        from .routers import router, validation_router
        
        # Build the workflow graph
        builder = lg.StateGraph(AnalysisState)
        
        # Add nodes
        builder.add_node("head", head_node)
        builder.add_node("fake_news", fake_news_agent)
        builder.add_node("credibility", credibility_agent)
        builder.add_node("sentiment", sentiment_agent)
        builder.add_node("summary", summary_agent)
        builder.add_node("validator", validator)
        
        # Add edges
        builder.add_edge("head", router)
        builder.add_edge("fake_news", "validator")
        builder.add_edge("credibility", "validator")
        builder.add_edge("sentiment", "validator")
        builder.add_edge("summary", "validator")
        builder.add_edge("validator", validation_router)
        
        # Set the entry point
        builder.set_entry_point("head")
        
        # Compile the graph
        graph = builder.compile()
        return graph
    except Exception as e:
        logger.warning(f"Error creating LangGraph workflow: {str(e)}")
        logger.warning("Using mocked workflow instead")
        return None

async def process_article(url: str, title: Optional[str] = None, source: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a news article with our LangGraph workflow.
    
    This is the main entry point for the backend processing.
    """
    logger.info(f"Processing article from URL: {url}")
    
    try:
        # Fetch article content
        article_data = await fetch_article_content(url)
        
        # Use provided title/source if available
        if title:
            article_data["title"] = title
        if source:
            article_data["source"] = source
        
        # Initialize state
        state: AnalysisState = {
            "article_content": article_data["content"],
            "article_title": article_data["title"],
            "article_url": url,
            "article_source": article_data.get("source"),
            "agents_called": [],
            "agent_invocation_counts": {}
        }
        
        # Try to use LangGraph if available
        workflow = await create_workflow()
        
        if workflow:
            # Run the LangGraph workflow
            logger.info("Running LangGraph workflow")
            result = await workflow.ainvoke(state)
            return result
        else:
            # Fallback to sequential processing if LangGraph not available
            logger.info("Using sequential processing fallback")
            head_node = HeadNode()
            fake_news_agent = FakeNewsAgent()
            credibility_agent = CredibilityAgent()
            sentiment_agent = SentimentAgent()
            summary_agent = SummaryAgent()
            
            # Run head node to decide which agents to call
            state = await head_node(state)
            
            # Run each agent in sequence
            if state.get("call_fake_news", False):
                state = await fake_news_agent(state)
            
            if state.get("call_credibility", False):
                state = await credibility_agent(state)
            
            if state.get("call_sentiment", False):
                state = await sentiment_agent(state)
            
            # Always run summary agent
            state = await summary_agent(state)
            
            return state
    
    except Exception as e:
        logger.error(f"Error processing article: {str(e)}")
        return {
            "error": f"Processing failed: {str(e)}",
            "article_url": url,
            "article_title": title or "Unknown"
        } 