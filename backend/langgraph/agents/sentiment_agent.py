"""
SentimentAgent - Analyzes the sentiment and bias of a news article
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

class SentimentAgent:
    """
    Agent that analyzes the sentiment of the article.
    Based on the prompt from initial_langgraph logic.py.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Analyze the sentiment of the article"""
        logger.info("SentimentAgent: Analyzing sentiment")
        
        # Get article content
        article_text = state.get("article_content", "")
        
        # Check if we need to use a mock implementation
        use_mock = os.environ.get("USE_MOCK_APIS", "true").lower() == "true"
        
        if use_mock:
            logger.info("Using mock implementation for SentimentAgent")
            await asyncio.sleep(1)  # Simulate processing time
            
            # Return sentiment analysis results with mock data
            state["sentiment_result"] = {
                "polarity": -0.2,  # Negative
                "subjectivity": 0.6,  # Somewhat subjective
                "emotional_tone": "slightly negative",
                "bias_assessment": "moderate bias detected",
                "justification": "The article uses language that suggests skepticism toward certain policies.",
                "detailed_justification": [
                    "Uses skeptical framing of policy decisions",
                    "Includes phrases that suggest doubt about motivations",
                    "Emphasizes negative consequences over potential benefits"
                ],
                "key_phrases": [
                    "controversial policy",
                    "critics argue",
                    "remains to be seen"
                ],
                "sentiment_score": 40  # On a 0-100 scale
            }
        else:
            # Use the prompt from initial_langgraph logic.py with enhancements for more detailed output
            system_prompt = """
You are SentimentAgent, specializing in granular sentiment analysis of newspaper articles.
Perform a thorough analysis of the article's sentiment covering:
1. Overall sentiment label (e.g. "negative," "positive," or "mixed").
2. Sentiment score (0–100, where 0 is extremely negative, 50 is neutral, 100 is extremely positive).
3. Provide detailed justification for your analysis.
4. Identify key phrases that support your assessment.
5. Assess the level of subjectivity/objectivity (0-100, where 0 is completely objective, 100 is highly subjective).

Return JSON in this format:
{
  "sentimentLabel": "negative",
  "sentimentScore": 30,
  "subjectivityScore": 65,
  "justification": ["Reason 1", "Reason 2", "Reason 3"],
  "keyPhrases": ["phrase 1", "phrase 2", "phrase 3"],
  "biasAssessment": "Description of any detected bias"
}
"""
            # Add article information
            final_prompt = f"{system_prompt}\n\nArticle Text:\n{article_text}"
            
            try:
                # Import OpenAI
                from openai import AsyncOpenAI
                
                # Initialize OpenAI client
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if not openai_api_key:
                    logger.warning("No OpenAI API key found in environment variables, using mock data")
                    # Fall back to mock implementation
                    state["sentiment_result"] = {
                        "polarity": -0.2,  # Negative
                        "subjectivity": 0.6,  # Somewhat subjective
                        "emotional_tone": "slightly negative",
                        "bias_assessment": "moderate bias detected",
                        "justification": "The article uses language that suggests skepticism toward certain policies.",
                        "detailed_justification": [
                            "Uses skeptical framing of policy decisions",
                            "Includes phrases that suggest doubt about motivations",
                            "Emphasizes negative consequences over potential benefits"
                        ],
                        "key_phrases": [
                            "controversial policy",
                            "critics argue",
                            "remains to be seen"
                        ],
                        "sentiment_score": 40  # On a 0-100 scale
                    }
                else:
                    # Use OpenAI to analyze sentiment
                    logger.info("Calling OpenAI for sentiment analysis")
                    client = AsyncOpenAI(api_key=openai_api_key)
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": final_prompt},
                            {"role": "user", "content": "Please return valid JSON."}
                        ],
                        temperature=0.3
                    )
                    
                    # Get the raw response
                    raw_output = response.choices[0].message.content.strip()
                    logger.info(f"Raw sentiment output: {raw_output}")
                    
                    # Process the raw output to get the JSON
                    try:
                        # Remove potential code fences
                        if raw_output.startswith("```") and raw_output.endswith("```"):
                            raw_output = raw_output[3:-3]
                        if raw_output.startswith("json"):
                            raw_output = raw_output[4:]
                        
                        sentiment_data = json.loads(raw_output)
                        
                        # Transform to match the expected output format of the original agent
                        sentiment_score = sentiment_data.get("sentimentScore", 50)
                        sentiment_label = sentiment_data.get("sentimentLabel", "neutral")
                        
                        # Get detailed reasoning and key phrases
                        justification = sentiment_data.get("justification", [])
                        key_phrases = sentiment_data.get("keyPhrases", [])
                        subjectivity_score = sentiment_data.get("subjectivityScore", 50) / 100.0
                        bias_assessment = sentiment_data.get("biasAssessment", f"{sentiment_label} tone detected")
                        
                        # Convert to original format
                        # Map sentiment_label to polarity value
                        polarity_map = {
                            "very positive": 0.8,
                            "positive": 0.5,
                            "slightly positive": 0.2,
                            "neutral": 0.0,
                            "slightly negative": -0.2,
                            "negative": -0.5,
                            "very negative": -0.8,
                            "mixed": 0.0  # Default for mixed
                        }
                        
                        # Get closest polarity value or default to 0
                        polarity = polarity_map.get(sentiment_label.lower(), 0.0)
                        
                        # Normalize sentiment score to 0-1 range
                        normalized_score = sentiment_score / 100.0
                        
                        # Create justification string from array
                        if isinstance(justification, list):
                            justification_text = ". ".join(justification)
                        else:
                            justification_text = str(justification)
                        
                        # Create comprehensive result with all details
                        state["sentiment_result"] = {
                            "polarity": polarity,
                            "subjectivity": subjectivity_score,
                            "emotional_tone": sentiment_label,
                            "bias_assessment": bias_assessment,
                            "justification": justification_text,
                            # Additional detailed fields
                            "detailed_justification": justification if isinstance(justification, list) else [justification_text],
                            "key_phrases": key_phrases if isinstance(key_phrases, list) else [],
                            "sentiment_score": sentiment_score
                        }
                        
                        # Also store the raw output for validation
                        state["sentiment_raw_output"] = raw_output
                    
                    except Exception as e:
                        logger.error(f"Error processing sentiment response: {e}")
                        # Fall back to mock implementation on error
                        state["sentiment_result"] = {
                            "polarity": -0.2,  # Default to slightly negative
                            "subjectivity": 0.6,  # Somewhat subjective
                            "emotional_tone": "neutral",
                            "bias_assessment": "error in processing",
                            "justification": f"Error during sentiment analysis: {str(e)}",
                            "detailed_justification": [f"Error during sentiment analysis: {str(e)}"],
                            "key_phrases": [],
                            "sentiment_score": 50
                        }
            
            except Exception as e:
                logger.error(f"Error in sentiment analysis: {e}")
                # Fall back to mock implementation on error
                state["sentiment_result"] = {
                    "polarity": -0.2,  # Negative
                    "subjectivity": 0.6,  # Somewhat subjective
                    "emotional_tone": "slightly negative",
                    "bias_assessment": "moderate bias detected",
                    "justification": "The article uses language that suggests skepticism toward certain policies.",
                    "detailed_justification": [
                        "Uses skeptical framing of policy decisions",
                        "Includes phrases that suggest doubt about motivations",
                        "Emphasizes negative consequences over potential benefits"
                    ],
                    "key_phrases": [
                        "controversial policy",
                        "critics argue",
                        "remains to be seen"
                    ],
                    "sentiment_score": 40  # On a 0-100 scale
                }
        
        # Update state tracking
        state["last_agent_run"] = "sentiment"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("sentiment")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["sentiment"] = state["agent_invocation_counts"].get("sentiment", 0) + 1
        
        return state 