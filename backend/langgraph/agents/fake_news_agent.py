"""
FakeNewsAgent - Analyzes an article for potentially false claims
"""

import asyncio
import logging
import os
import json
import re
import aiohttp
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
            extract_prompt = f"""
            You are an assistant that extracts exactly 2 factual claims from this article.
            Return them as a valid JSON array of 2 strings (no commentary, code fences, or backticks).

            Article Title: {article_title}
            Article Text: {article_content}
            """
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": extract_prompt},
                    {"role": "user", "content": "List 2 claims in a JSON array now."}
                ],
                temperature=0.3
            )
            
            raw_claims = response.choices[0].message.content.strip()
            # Clean up potential code fences
            raw_claims = self._remove_code_fences(raw_claims)
            logger.info(f"Raw claims extraction output: {raw_claims}")
                
            try:
                claims = json.loads(raw_claims)
                if not isinstance(claims, list):
                    raise ValueError("Parsed JSON is not a valid list.")
            except Exception as e:
                logger.error(f"JSON parse error on extracted claims: {e}")
                claims = []
                
            claims = claims[:10]  # Ensure we have at most 10 claims
            
        except Exception as e:
            logger.error(f"Error extracting claims with OpenAI: {e}")
            claims = []
            
        if not claims:
            logger.warning("No claims extracted, falling back to mock data")
            return await self._mock_implementation(state)

        # 2. Analyze each claim using search and verification
        search_api_key = os.environ.get("SEARCH_API_KEY")
        if not search_api_key:
            logger.warning("No Search API key found, using simplified claim verification")
            all_claims = await self._analyze_claims_simplified(claims, client)
        else:
            # Setup search tool
            try:
                # Replace SearchApiAPIWrapper with custom Google Search implementation
                search_engine_cx = os.environ.get("SEARCH_ENGINE_CX")
                if not search_engine_cx:
                    logger.warning("No Search Engine CX found, using simplified claim verification")
                    all_claims = await self._analyze_claims_simplified(claims, client)
                else:
                    all_claims = await self._analyze_claims_with_google_search(claims, client, search_api_key, search_engine_cx)
            except Exception as e:
                logger.error(f"Error setting up search: {e}")
                all_claims = await self._analyze_claims_simplified(claims, client)
            
        # 3. Calculate results format matching the original
        found_count = sum(1 for claim in all_claims if claim.get("found", False))
        average_score = (found_count / len(claims)) * 100 if claims else 0
        
        # Map to the expected format of the original code
        verified_claims = []
        unverified_claims = []
        for claim_data in all_claims:
            result = {
                "claim": claim_data["claim"],
                "is_verified": claim_data.get("found", False),
                "analysis": claim_data.get("reason", "No analysis provided")
            }
            if result["is_verified"]:
                verified_claims.append(result)
            else:
                unverified_claims.append(result)
        
        # Return fake news detection results with detailed claim analysis
        # Format in original JSON structure
        state["fake_news_result"] = {
            "claims_analyzed": len(all_claims),
            "claims_verified": len(verified_claims),
            "verification_score": average_score / 100,  # Convert to 0-1 range
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

    async def _analyze_claims_with_google_search(self, claims, client, api_key, cx):
        """Analyze claims with Google Custom Search"""
        all_claims = []
        
        # Import the search API
        try:
            from utils.search_api import SearchAPI
            search_api = SearchAPI(api_key=api_key, cx=cx)
        except ImportError as e:
            logger.error(f"Error importing SearchAPI: {e}")
            return await self._analyze_claims_simplified(claims, client)
            
        for claim in claims:
            logger.info(f"Analyzing claim: {claim}")
            try:
                # Use the SearchAPI to get results
                search_results = await search_api.search(claim, num_results=3)
                external_text = ""
                
                if search_results:
                    links_fetched = 0
                    for item in search_results:
                        link_url = item.get('link')
                        if link_url and link_url.startswith("http"):
                            logger.info(f"Fetching content from: {link_url}")
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(link_url, timeout=10) as link_resp:
                                        if link_resp.status == 200:
                                            html_content = await link_resp.text()
                                            page_text = self._extract_text_from_html(html_content, link_url)
                                            if page_text:
                                                external_text += f"\n\n[SOURCE: {link_url}]\n{page_text}"
                                                links_fetched += 1
                                                # Get only one link per claim
                                                if links_fetched >= 1:
                                                    break
                            except Exception as e:
                                logger.error(f"Error fetching link: {e}")
                
                # If we couldn't fetch any content, add some basic info from search results
                if not external_text and search_results:
                    for item in search_results:
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')
                        if snippet:
                            external_text += f"\n\n[SOURCE: {item.get('link', 'Unknown')}]\n{title}: {snippet}"
                
                # Verify the claim against external text
                if external_text:
                    verification = await self._check_claim_with_gpt(claim, external_text, client)
                    all_claims.append(verification)
                else:
                    all_claims.append({
                        "claim": claim,
                        "found": False,
                        "reason": "No relevant search results found to verify this claim",
                        "score": 0
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing claim with search: {e}")
                all_claims.append({
                    "claim": claim,
                    "found": False,
                    "reason": f"Error during verification: {str(e)}",
                    "score": 0
                })
                
        return all_claims
        
    async def _analyze_claims_simplified(self, claims, client):
        """Simplified claim analysis without web search"""
        all_claims = []
        for claim in claims:
            result = await self._analyze_claim(claim, client)
            all_claims.append({
                "claim": claim,
                "found": result.get("is_verified", False),
                "reason": result.get("analysis", "No analysis provided"),
                "score": 100 if result.get("is_verified", False) else 0
            })
        return all_claims
    
    async def _check_claim_with_gpt(self, claim, external_text, client):
        """
        Checks if the external_text supports the given claim. Returns claim verification data.
        """
        system_prompt = f"""
You are a fact-checking assistant. You have:
1) A claim: {claim}
2) External text from search results:

{external_text}

Does this text SUPPORT the claim or NOT?
Return ONLY JSON:
{{
  "supports": true/false,
  "reason": "short explanation"
}}
No extra text, no code fences.
"""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Return your JSON verdict."}
                ],
                temperature=0.3
            )
            
            raw_response = response.choices[0].message.content.strip()
            # Clean up potential code fences
            raw_response = self._remove_code_fences(raw_response)
            logger.info(f"Raw response: {raw_response}")
            
            try:
                # Parse the response - ensure json is imported
                result = json.loads(raw_response)
                supports = result.get("supports", False)
                reason = result.get("reason", "No reason provided")
                
                return {
                    "claim": claim,
                    "found": supports,
                    "reason": reason,
                    "score": 100 if supports else 0
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from GPT response: {e}")
                logger.error(f"Raw response was: {raw_response}")
                # Fallback result
                return {
                    "claim": claim,
                    "found": False,
                    "reason": f"Error parsing response: {raw_response}",
                    "score": 0
                }
                
        except Exception as e:
            logger.error(f"Error in claim verification with GPT: {e}")
            return {
                "claim": claim,
                "found": False,
                "reason": f"Error during verification: {str(e)}",
                "score": 0
            }
            
    def _extract_text_from_html(self, html_str, link_url):
        """
        Uses BeautifulSoup to parse <p> content from HTML and returns extracted text.
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_str, "html.parser")
            paragraphs = soup.find_all("p")
            text_content = "\n".join(p.get_text() for p in paragraphs if p.get_text())
            logger.info(f"Extracted text length: {len(text_content)} from {link_url}")
            return text_content
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""
            
    def _remove_code_fences(self, text):
        """
        Removes Markdown code fences (e.g., ```json) from GPT output.
        """
        t = text.strip()
        t = re.sub(r"^```[a-zA-Z]*", "", t)
        t = re.sub(r"```$", "", t)
        return t.strip()

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