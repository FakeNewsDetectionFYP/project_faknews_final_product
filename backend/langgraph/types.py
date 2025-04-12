"""
Type definitions for the LangGraph workflow
"""

from typing import Dict, Any, List, TypedDict, Optional

class AnalysisState(TypedDict, total=False):
    """
    Type definition for the state used in the LangGraph workflow.
    
    This state is passed between agents and tracks the analysis process.
    """
    article_content: str
    article_title: str
    article_url: str
    article_source: Optional[str]
    fake_news_result: Dict
    credibility_result: Dict
    sentiment_result: Dict
    summary_result: str
    agents_called: List[str]
    agent_invocation_counts: Dict[str, int]
    last_agent_run: str
    validation_passed: bool
    refined_prompts: Dict[str, str]
    call_fake_news: bool
    call_credibility: bool
    call_sentiment: bool
    call_summary: bool 