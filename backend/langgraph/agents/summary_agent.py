"""
SummaryAgent - Generates a concise summary of a news article
"""

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class SummaryAgent:
    """
    Agent that generates a concise summary of the article.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Generate a summary of the article"""
        logger.info("SummaryAgent: Generating summary")
        
        # In a real implementation, this would:
        # 1. Use OpenAI to generate a concise summary
        
        # Mock implementation for development
        await asyncio.sleep(1)  # Simulate processing time
        
        # Return article summary
        state["summary_result"] = "This article discusses how US companies, including JM Smucker, are supporting Trump's trade policies that aim to address tariff imbalances. It highlights examples like the 24% EU tariff on jam compared to 4.5% in the US. While some businesses welcome the focus on trade inequities, many are concerned about Trump's broad tariff approach, fearing retaliation and economic disruption."
        
        state["last_agent_run"] = "summary"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("summary")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["summary"] = state["agent_invocation_counts"].get("summary", 0) + 1
        
        return state 