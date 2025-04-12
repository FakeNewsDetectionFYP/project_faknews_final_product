"""
SummaryAgent - Generates a concise summary of a news article
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class SummaryAgent:
    """
    Agent that generates a concise summary of the article.
    Based on the prompt from initial_langgraph logic.py.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Generate a summary of the article"""
        logger.info("SummaryAgent: Generating summary")
        
        # Get article content
        article_text = state.get("article_content", "")
        
        # Check if we need to use a mock implementation
        use_mock = os.environ.get("USE_MOCK_APIS", "true").lower() == "true"
        
        if use_mock:
            logger.info("Using mock implementation for SummaryAgent")
            await asyncio.sleep(1)  # Simulate processing time
            
            # Return article summary with mock data
            state["summary_result"] = "This article discusses how US companies, including JM Smucker, are supporting Trump's trade policies that aim to address tariff imbalances. It highlights examples like the 24% EU tariff on jam compared to 4.5% in the US. While some businesses welcome the focus on trade inequities, many are concerned about Trump's broad tariff approach, fearing retaliation and economic disruption."
        else:
            # Use the prompt from initial_langgraph logic.py
            system_prompt = (
                "You are a summary agent. Summarize the article in exactly 100 words. "
                "No more, no less. Maintain coherence."
            )
            
            user_prompt = f"Article text:\n\n{article_text}\n\nSummarize in exactly 100 words."
            
            try:
                # Import OpenAI
                from openai import AsyncOpenAI
                
                # Initialize OpenAI client
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if not openai_api_key:
                    logger.warning("No OpenAI API key found in environment variables, using mock data")
                    # Fall back to mock implementation
                    state["summary_result"] = "This article discusses how US companies, including JM Smucker, are supporting Trump's trade policies that aim to address tariff imbalances. It highlights examples like the 24% EU tariff on jam compared to 4.5% in the US. While some businesses welcome the focus on trade inequities, many are concerned about Trump's broad tariff approach, fearing retaliation and economic disruption."
                else:
                    # Use OpenAI to generate summary
                    logger.info("Calling OpenAI for article summary")
                    client = AsyncOpenAI(api_key=openai_api_key)
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3
                    )
                    
                    # Get the summary
                    summary = response.choices[0].message.content.strip()
                    logger.info(f"Generated summary: {summary}")
                    
                    # Store the summary
                    state["summary_result"] = summary
            
            except Exception as e:
                logger.error(f"Error in summary generation: {e}")
                # Fall back to mock implementation on error
                state["summary_result"] = "This article discusses how US companies, including JM Smucker, are supporting Trump's trade policies that aim to address tariff imbalances. It highlights examples like the 24% EU tariff on jam compared to 4.5% in the US. While some businesses welcome the focus on trade inequities, many are concerned about Trump's broad tariff approach, fearing retaliation and economic disruption."
        
        # Update state tracking
        state["last_agent_run"] = "summary"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("summary")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["summary"] = state["agent_invocation_counts"].get("summary", 0) + 1
        
        return state 