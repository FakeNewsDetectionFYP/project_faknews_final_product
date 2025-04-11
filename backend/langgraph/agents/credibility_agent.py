"""
CredibilityAgent - Evaluates the credibility of a news article
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class CredibilityAgent:
    """
    Agent that evaluates the source credibility, title, and content alignment.
    Based on the prompt from initial_langgraph logic.py.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Evaluate the credibility of the article"""
        logger.info("CredibilityAgent: Evaluating credibility")
        
        # Get article content and title
        article_text = state.get("article_content", "")
        article_title = state.get("article_title", "Untitled Article")
        
        # Check if we need to use a mock implementation
        use_mock = os.environ.get("USE_MOCK_APIS", "true").lower() == "true"
        
        if use_mock:
            logger.info("Using mock implementation for CredibilityAgent")
            await asyncio.sleep(1)  # Simulate processing time
            
            # Return credibility results with mock data
            state["credibility_result"] = {
                "source_reputation": 0.75,
                "title_content_alignment": 0.9,
                "overall_credibility": 0.82,
                "evaluation": "This article appears to be from a credible source with good title-content alignment.",
                "sourceReputationReasoning": "The source has a generally good reputation for factual reporting.",
                "titleContentReasoning": "The title accurately reflects the main content of the article.",
                "misleadingTitlesReasoning": "The title is not misleading and represents the article's content well.",
                "overallConclusion": "This article appears to be from a credible source with good title-content alignment."
            }
        else:
            # Use the prompt from initial_langgraph logic.py 
            system_prompt = """
You are the CredibilityAgent. Evaluate the news article's credibility:
1) Source Reputation (0–100)
2) Title vs Content (0–100)
3) How misleading is the title? (0–100, 0=very misleading, 100=not misleading)
Then compute an average, and provide reasoning.

Return JSON like:
{
  "sourceReputationScore": 80,
  "sourceReputationReasoning": "...",
  "titleContentScore": 60,
  "titleContentReasoning": "...",
  "misleadingTitlesScore": 70,
  "misleadingTitlesReasoning": "...",
  "averageScore": 70,
  "overallConclusion": "..."
}
"""
            # Add article information
            final_prompt = f"{system_prompt}\n\nArticle Title: {article_title}\nArticle Text: {article_text}"
            
            try:
                # Import OpenAI
                from openai import AsyncOpenAI
                
                # Initialize OpenAI client
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if not openai_api_key:
                    logger.warning("No OpenAI API key found in environment variables, using mock data")
                    # Fall back to mock implementation
                    state["credibility_result"] = {
                        "source_reputation": 0.75,
                        "title_content_alignment": 0.9,
                        "overall_credibility": 0.82,
                        "evaluation": "This article appears to be from a credible source with good title-content alignment.",
                        "sourceReputationReasoning": "The source has a generally good reputation for factual reporting.",
                        "titleContentReasoning": "The title accurately reflects the main content of the article.",
                        "misleadingTitlesReasoning": "The title is not misleading and represents the article's content well.",
                        "overallConclusion": "This article appears to be from a credible source with good title-content alignment."
                    }
                else:
                    # Use OpenAI to evaluate credibility
                    logger.info("Calling OpenAI for credibility analysis")
                    client = AsyncOpenAI(api_key=openai_api_key)
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": final_prompt},
                            {"role": "user", "content": "Assess now in JSON."}
                        ],
                        temperature=0.3
                    )
                    
                    # Get the raw response
                    raw_output = response.choices[0].message.content.strip()
                    logger.info(f"Raw credibility output: {raw_output}")
                    
                    # Process the raw output to get the JSON
                    try:
                        # Remove potential code fences
                        if raw_output.startswith("```") and raw_output.endswith("```"):
                            raw_output = raw_output[3:-3]
                        if raw_output.startswith("json"):
                            raw_output = raw_output[4:]
                        
                        credibility_data = json.loads(raw_output)
                        
                        # Transform to match the expected output format of the original agent
                        overall_score = credibility_data.get("averageScore", 70) / 100.0  # Convert to 0-1 scale
                        
                        source_score = credibility_data.get("sourceReputationScore", 70) / 100.0
                        title_content_score = credibility_data.get("titleContentScore", 70) / 100.0
                        misleading_title_score = credibility_data.get("misleadingTitlesScore", 70) / 100.0
                        
                        # Get all the reasoning fields
                        source_reasoning = credibility_data.get("sourceReputationReasoning", "No reasoning provided")
                        title_content_reasoning = credibility_data.get("titleContentReasoning", "No reasoning provided")
                        misleading_title_reasoning = credibility_data.get("misleadingTitlesReasoning", "No reasoning provided") 
                        overall_conclusion = credibility_data.get("overallConclusion", "No conclusion provided")
                        
                        # Create a comprehensive result that includes all the reasoning
                        state["credibility_result"] = {
                            "source_reputation": source_score,
                            "title_content_alignment": title_content_score,
                            "overall_credibility": overall_score,
                            "evaluation": overall_conclusion,
                            # Include the detailed reasoning fields
                            "sourceReputationReasoning": source_reasoning,
                            "titleContentReasoning": title_content_reasoning,
                            "misleadingTitlesReasoning": misleading_title_reasoning,
                            "overallConclusion": overall_conclusion,
                            # Add raw scores for frontend display
                            "sourceReputationScore": credibility_data.get("sourceReputationScore", 70),
                            "titleContentScore": credibility_data.get("titleContentScore", 70),
                            "misleadingTitlesScore": credibility_data.get("misleadingTitlesScore", 70)
                        }
                        
                        # Also store the raw output for validation
                        state["credibility_raw_output"] = raw_output
                    
                    except Exception as e:
                        logger.error(f"Error processing credibility response: {e}")
                        # Fall back to mock implementation on error
                        state["credibility_result"] = {
                            "source_reputation": 0.75,
                            "title_content_alignment": 0.9,
                            "overall_credibility": 0.82,
                            "evaluation": "This article appears to be from a credible source with good title-content alignment.",
                            "sourceReputationReasoning": "The source has a generally good reputation for factual reporting.",
                            "titleContentReasoning": "The title accurately reflects the main content of the article.",
                            "misleadingTitlesReasoning": "The title is not misleading and represents the article's content well.",
                            "overallConclusion": "This article appears to be from a credible source with good title-content alignment."
                        }
            
            except Exception as e:
                logger.error(f"Error in credibility analysis: {e}")
                # Fall back to mock implementation on error
                state["credibility_result"] = {
                    "source_reputation": 0.75,
                    "title_content_alignment": 0.9,
                    "overall_credibility": 0.82,
                    "evaluation": "This article appears to be from a credible source with good title-content alignment.",
                    "sourceReputationReasoning": "The source has a generally good reputation for factual reporting.",
                    "titleContentReasoning": "The title accurately reflects the main content of the article.",
                    "misleadingTitlesReasoning": "The title is not misleading and represents the article's content well.",
                    "overallConclusion": "This article appears to be from a credible source with good title-content alignment."
                }
        
        # Update state tracking
        state["last_agent_run"] = "credibility"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("credibility")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["credibility"] = state["agent_invocation_counts"].get("credibility", 0) + 1
        
        return state 