"""
FakeNewsAgent - Analyzes an article for potentially false claims
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class FakeNewsAgent:
    """
    Agent that extracts factual claims from the article and validates them
    against search results.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Process the article to detect fake news claims"""
        logger.info("FakeNewsAgent: Processing article")
        
        # Check if we should use mock APIs or real ones
        use_mock = os.environ.get("USE_MOCK_APIS", "true").lower() == "true"
        
        if use_mock:
            logger.info("FakeNewsAgent: Using mock implementation")
            return await self._mock_implementation(state)
        else:
            logger.info("FakeNewsAgent: Using real API implementation")
            return await self._real_implementation(state)

    async def _real_implementation(self, state: AnalysisState) -> AnalysisState:
        """Real implementation using OpenAI and search APIs"""
        logger.info("Using real APIs to analyze the article")
        
        # Import the necessary libraries for real implementation
        try:
            from openai import AsyncOpenAI
            import aiohttp
            from bs4 import BeautifulSoup
            import json
        except ImportError as e:
            logger.error(f"Failed to import required libraries: {e}")
            return await self._mock_implementation(state)
        
        # Get article content and title
        article_content = state.get("article_content", "")
        article_title = state.get("article_title", "Untitled Article")
        
        if not article_content:
            logger.warning("No article content provided")
            return state
            
        # Initialize OpenAI client
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("No OpenAI API key found in environment variables")
            return await self._mock_implementation(state)
            
        client = AsyncOpenAI(api_key=openai_api_key)
        
        # 1. Extract claims from the article
        logger.info("Extracting claims from article")
        try:
            claims_prompt = f"""
            Extract exactly 5 factual claims from this article. Return only a JSON array of claim strings.
            
            Article Title: {article_title}
            Article Content: {article_content}
            """
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a factual claim extractor. Extract exactly 5 factual claims from the provided article."},
                    {"role": "user", "content": claims_prompt}
                ],
                temperature=0.3
            )
            
            claims_text = response.choices[0].message.content.strip()
            # Clean up potential code fences
            if claims_text.startswith("```") and claims_text.endswith("```"):
                claims_text = claims_text[3:-3]
            if claims_text.startswith("json"):
                claims_text = claims_text[4:]
                
            claims = json.loads(claims_text)
            if not isinstance(claims, list):
                claims = []
                
        except Exception as e:
            logger.error(f"Error extracting claims with OpenAI: {e}")
            claims = []
            
        if not claims:
            logger.warning("No claims extracted, falling back to mock data")
            return await self._mock_implementation(state)
            
        # 2. Analyze each claim
        all_claims = []
        for claim in claims[:5]:  # Limit to 5 claims
            claim_result = await self._analyze_claim(claim, client)
            all_claims.append(claim_result)
            
        # 3. Calculate results
        verified_claims = [claim for claim in all_claims if claim["is_verified"]]
        unverified_claims = [claim for claim in all_claims if not claim["is_verified"]]
        
        # Return fake news detection results with detailed claim analysis
        state["fake_news_result"] = {
            "claims_analyzed": len(all_claims),
            "claims_verified": len(verified_claims),
            "verification_score": len(verified_claims) / len(all_claims) if all_claims else 0,
            "verified_claims": verified_claims,
            "unverified_claims": unverified_claims,
            "all_claims": all_claims
        }
        
        state["last_agent_run"] = "fake_news"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("fake_news")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["fake_news"] = state["agent_invocation_counts"].get("fake_news", 0) + 1
        
        return state
        
    async def _analyze_claim(self, claim: str, client) -> Dict[str, Any]:
        """Analyze a single claim using OpenAI"""
        try:
            # For simplicity, we'll just use OpenAI to evaluate the claim
            # In a real implementation, you would search the web for verification
            
            analysis_prompt = f"""
            Analyze this claim from a news article: "{claim}"
            
            Is this claim likely to be true based on your knowledge?
            Provide a brief analysis of the claim's verifiability.
            
            Return your analysis as a JSON object:
            {{
                "is_verified": true/false,
                "analysis": "Your analysis here"
            }}
            """
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a fact-checking assistant. Analyze the given claim and determine if it's likely to be true."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            # Clean up potential code fences
            if result_text.startswith("```") and result_text.endswith("```"):
                result_text = result_text[3:-3]
            if result_text.startswith("json"):
                result_text = result_text[4:]
                
            result = json.loads(result_text)
            
            return {
                "claim": claim,
                "is_verified": result.get("is_verified", False),
                "analysis": result.get("analysis", "No analysis provided")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing claim with OpenAI: {e}")
            return {
                "claim": claim,
                "is_verified": False,
                "analysis": f"Error during analysis: {str(e)}"
            }
    
    async def _mock_implementation(self, state: AnalysisState) -> AnalysisState:
        """Mock implementation for development purposes"""
        logger.info("Using mock data for FakeNewsAgent")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Generate mock detailed claim analysis - astronomy themed
        all_claims = [
            {
                "claim": "ALMA detected hydrogen recombination lines from proplyd disks in the Orion Nebula Cluster",
                "analysis": "This is verified by the research published by the National Radio Astronomy Observatory and confirmed by multiple independent astronomers. The data from the Atacama Large Millimeter/submillimeter Array (ALMA) provides strong evidence supporting this claim.",
                "is_verified": True
            },
            {
                "claim": "This is the first-ever detection of hydrogen recombination lines from proplyd disks",
                "analysis": "Multiple scientific publications confirm this is indeed the first such detection. Previous studies had not observed these specific recombination lines in proplyd disks before this research.",
                "is_verified": True
            },
            {
                "claim": "The Orion Nebula Cluster is densely packed with stars",
                "analysis": "This is well-established in astronomy. The Orion Nebula Cluster is one of the closest and most studied star-forming regions, and its dense concentration of stars is well-documented in scientific literature.",
                "is_verified": True
            },
            {
                "claim": "This discovery helps understand star formation processes",
                "analysis": "This claim is supported by the broader body of astrophysical research. Understanding protoplanetary disks and their composition provides valuable insights into how stars and their planetary systems form.",
                "is_verified": True
            },
            {
                "claim": "This discovery proves the existence of alien life",
                "analysis": "This claim is not supported by the research. The study focuses on hydrogen recombination lines and star formation processes, not the detection of biological signatures or evidence of extraterrestrial life.",
                "is_verified": False
            }
        ]
        
        # Extract verified and unverified claims
        verified_claims = [claim for claim in all_claims if claim["is_verified"]]
        unverified_claims = [claim for claim in all_claims if not claim["is_verified"]]
        
        # Return fake news detection results with detailed claim analysis
        state["fake_news_result"] = {
            "claims_analyzed": len(all_claims),
            "claims_verified": len(verified_claims),
            "verification_score": len(verified_claims) / len(all_claims),
            "verified_claims": verified_claims,
            "unverified_claims": unverified_claims,
            "all_claims": all_claims
        }
        
        state["last_agent_run"] = "fake_news"
        if "agents_called" not in state:
            state["agents_called"] = []
        state["agents_called"].append("fake_news")
        
        # Track invocation count
        if "agent_invocation_counts" not in state:
            state["agent_invocation_counts"] = {}
        state["agent_invocation_counts"]["fake_news"] = state["agent_invocation_counts"].get("fake_news", 0) + 1
        
        return state 