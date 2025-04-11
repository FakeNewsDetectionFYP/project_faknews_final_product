import json
import os
from typing import List, Optional, Dict, Any
import logging
from .models import ArticleCreate, ArticleResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple JSON file-based DB for development
DB_FILE = os.environ.get("DB_FILE", "articles_db.json")

def _load_db() -> List[Dict]:
    """Load articles from JSON file, create if not exists"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Initialize empty DB file
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
    except Exception as e:
        logger.error(f"Error loading database: {str(e)}")
        return []

def _save_db(articles: List[Dict]) -> bool:
    """Save articles to JSON file"""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving database: {str(e)}")
        return False

def normalize_url(url: str) -> str:
    """Normalize URL for comparison, removing query parameters and fragments"""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # Reconstruct URL without query parameters and fragments
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            '',  # params
            '',  # query
            ''   # fragment
        ))
        return normalized.rstrip('/')  # Remove trailing slash for consistency
    except Exception as e:
        logger.warning(f"Error normalizing URL {url}: {str(e)}")
        return url

def get_article_by_url(url: str) -> Optional[ArticleResponse]:
    """Get article by URL, with normalization for better matching"""
    articles = _load_db()
    normalized_url = normalize_url(url)
    
    # First try exact match
    for article in articles:
        if article.get("url") == url:
            return ArticleResponse(**article)
    
    # Then try normalized match
    for article in articles:
        if normalize_url(article.get("url", "")) == normalized_url:
            return ArticleResponse(**article)
    
    return None

def get_article_by_id(article_id: str) -> Optional[ArticleResponse]:
    """Get article by ID"""
    articles = _load_db()
    for article in articles:
        if article.get("id") == article_id:
            return ArticleResponse(**article)
    return None

def save_article(article: ArticleCreate) -> bool:
    """Save a new article or update existing one"""
    articles = _load_db()
    
    # Convert to dict for storage
    article_dict = article.model_dump()
    
    # Check if article already exists by URL (exact or normalized)
    normalized_url = normalize_url(article.url)
    found_at_index = None
    
    for i, existing in enumerate(articles):
        if existing.get("url") == article.url:
            found_at_index = i
            break
        
        if normalize_url(existing.get("url", "")) == normalized_url:
            found_at_index = i
            break
    
    if found_at_index is not None:
        # Update existing article
        articles[found_at_index] = article_dict
    else:
        # Add new article
        articles.append(article_dict)
    
    return _save_db(articles)

def get_articles(limit: int = 100, skip: int = 0) -> List[ArticleResponse]:
    """Get all articles with pagination"""
    articles = _load_db()
    # Sort by processed_at in descending order (newest first)
    articles.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
    return [ArticleResponse(**article) for article in articles[skip:skip+limit]]

def delete_article(article_id: str) -> bool:
    """Delete an article by ID"""
    articles = _load_db()
    original_count = len(articles)
    articles = [a for a in articles if a.get("id") != article_id]
    
    if len(articles) < original_count:
        return _save_db(articles)
    return False 