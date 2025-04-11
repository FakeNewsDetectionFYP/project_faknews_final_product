from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class ArticleBase(BaseModel):
    """Base schema for article data"""
    url: str
    title: Optional[str] = None
    source: Optional[str] = None

class ArticleCreate(ArticleBase):
    """Schema for creating a new article entry"""
    id: str
    processed_at: datetime
    analysis_results: Dict[str, Any]

class ArticleResponse(ArticleCreate):
    """Schema for article response data"""
    class Config:
        from_attributes = True 