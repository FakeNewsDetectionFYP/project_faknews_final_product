"""
HeadNode - Decides which agents to call based on article content
"""

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class HeadNode:
    """
    Determines which agents to call based on article content.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Decide which agents to invoke based on the article"""
        logger.info("HeadNode: Deciding which agents to call")
        
        # In real implementation, this would use LLM to decide
        # which agents to call based on article content
        
        # Mock implementation for development
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # In most cases, we'll want to call all agents
        state["call_fake_news"] = True
        state["call_credibility"] = True
        state["call_sentiment"] = True
        state["call_summary"] = True  # Summary is always called
        
        return state 