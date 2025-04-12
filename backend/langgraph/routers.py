"""
Router functions for the LangGraph workflow
"""

import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from .types import AnalysisState

async def router(state: AnalysisState) -> str:
    """
    Determines the next agent to call based on the state.
    
    Default sequence: fake_news → credibility → sentiment → summary
    """
    logger.info("Router: Deciding next step")
    
    # Check if we need to run the fake news agent
    if state.get("call_fake_news", False) and "fake_news_result" not in state:
        return "fake_news"
    
    # Check if we need to run the credibility agent
    if state.get("call_credibility", False) and "credibility_result" not in state:
        return "credibility"
    
    # Check if we need to run the sentiment agent
    if state.get("call_sentiment", False) and "sentiment_result" not in state:
        return "sentiment"
    
    # Always run the summary agent if not already run
    if "summary_result" not in state:
        return "summary"
    
    # All agents have completed
    return "end"

async def validation_router(state: AnalysisState) -> str:
    """
    Determines whether to continue or rerun an agent based on validation.
    """
    logger.info("Validation Router: Checking validation status")
    
    if not state.get("validation_passed", False):
        # If validation failed, rerun the last agent
        return state.get("last_agent_run", "end")
    
    # Continue with the main router if validation passed
    return "continue" 