from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Import our modules
from database.models import ArticleCreate, ArticleResponse
from database.crud import get_article_by_url, save_article, get_articles
from langgraph.workflow import process_article

app = FastAPI(title="News Processing API", description="API for processing news articles via LangGraph")

# CORS middleware setup for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API requests/responses
class ArticleRequest(BaseModel):
    url: str
    title: Optional[str] = None
    source: Optional[str] = None

class ProcessResponse(BaseModel):
    message: str
    article_id: Optional[str] = None
    cached: bool = False
    results: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "News Processing API is running"}

@app.post("/process", response_model=ProcessResponse)
async def process_news_article(article: ArticleRequest, background_tasks: BackgroundTasks):
    """
    Process a news article by URL. If already processed, returns cached results.
    Otherwise, queues processing in the background and returns a message.
    """
    # Check if this URL has already been processed
    existing_article = get_article_by_url(article.url)
    
    if existing_article:
        return ProcessResponse(
            message="Article already processed",
            article_id=existing_article.id,
            cached=True,
            results=existing_article.analysis_results
        )
    
    # Queue processing in background
    article_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(process_article_task, article, article_id)
    
    return ProcessResponse(
        message="Article processing started",
        article_id=article_id,
        cached=False
    )

@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """Get the processed results for a specific article by ID"""
    article = get_article_by_url(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.get("/articles", response_model=list[ArticleResponse])
async def list_articles():
    """List all processed articles"""
    return get_articles()

@app.get("/get_article")
async def get_article_by_url_param(url: str):
    """Get article data by URL parameter"""
    article = get_article_by_url(url)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"article": article}

# Background task for processing articles
async def process_article_task(article: ArticleRequest, article_id: str):
    """Background task to process an article with LangGraph"""
    try:
        # Process the article with our LangGraph workflow
        result = await process_article(article.url, article.title, article.source)
        
        # Save the results to our database
        article_data = ArticleCreate(
            id=article_id,
            url=article.url,
            title=result.get("article_title", article.title),
            source=article.source,
            processed_at=datetime.now(),
            analysis_results=result
        )
        save_article(article_data)
    except Exception as e:
        print(f"Error processing article {article_id}: {str(e)}")
        # In production, you'd want to log this to a monitoring system

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 