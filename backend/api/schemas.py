from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime

class ArticleRequest(BaseModel):
    """Request model for article processing"""
    url: HttpUrl
    title: Optional[str] = None
    source: Optional[str] = None

class ProcessResponse(BaseModel):
    """Response model for article processing request"""
    message: str
    article_id: Optional[str] = None
    cached: bool = False
    results: Optional[Dict[str, Any]] = None

class FakeNewsResult(BaseModel):
    """Model for fake news detection results"""
    claims_analyzed: int
    claims_verified: int
    verification_score: float = Field(ge=0.0, le=1.0)
    verified_claims: List[str] = []
    unverified_claims: List[str] = []

class CredibilityResult(BaseModel):
    """Model for credibility assessment results"""
    source_reputation: float = Field(ge=0.0, le=1.0)
    title_content_alignment: float = Field(ge=0.0, le=1.0)
    overall_credibility: float = Field(ge=0.0, le=1.0)
    evaluation: str

class SentimentResult(BaseModel):
    """Model for sentiment analysis results"""
    polarity: float = Field(ge=-1.0, le=1.0)
    subjectivity: float = Field(ge=0.0, le=1.0)
    emotional_tone: str
    bias_assessment: str
    justification: str

class AnalysisResult(BaseModel):
    """Complete analysis results model"""
    article_title: str
    article_url: HttpUrl
    article_source: Optional[str] = None
    summary_result: str
    fake_news_result: Optional[FakeNewsResult] = None
    credibility_result: Optional[CredibilityResult] = None
    sentiment_result: Optional[SentimentResult] = None
    agents_called: List[str]
    processed_at: datetime 