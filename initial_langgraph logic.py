# -*- coding: utf-8 -*-
"""initial_langgraph logic.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1g3iJIpa6o26bUmyJ3-n8iSxfiQVVOLIP

# News Article Analysis Architecture

This notebook is an architecture for reading and analyzing news articles using **OpenAI GPT**, **search API**, and custom agents (FakeNews, Credibility, Sentiment, Summary). It is orchestrated by a state machine so that each step is validated before proceeding to the next subagent.

## Workflow Overview

1. **Head Node**  
   - Decides whether to call the FakeNews, Credibility, and Sentiment agents, if any.  
   - Always calls the Summary Agent at the end.

2. **Router**  
   - Runs agents in a sequence:  
     1. FakeNews → 2. Credibility → 3. Sentiment → 4. Summary.  
   - Ends when all the necessary calls are complete.

3. **ValidatorAgent**  
   - Checks outputs from the FakeNews, Credibility, and Sentiment agents.  
   - If invalid, adapts and refines their prompts, then re-runs them.

## Agents

- **FakeNewsAgent**  
  - Extracts 10 factual claims from the article.  
  - Searches each claim with a search API, then parses the top link with BeautifulSoup.  
  - Asks GPT-4o-mini whether text supports each claim, then outputs "True" count and average score.

- **CredibilityAgent**  
  - Evaluates source reputation, title-content alignment, and title misleadingness.  
  - Outputs an overall credibility score.

- **SentimentAgent**  
  - Assesses sentiment (e.g., positive, negative, mixed) with a score range of 0–100.  
  - Returns justifications.

- **SummaryAgent**  
  - Produces 100-word summary.

## Database & I/O

- Checks if the article’s title exists in `articles_db.json` on Google Drive (make sure to change path).  
- If processed in the past, it loads stored results; otherwise, it runs the agents and saves new results.

## How to Use

1. **Set your API keys** (`OPENAI_API_KEY`, `SEARCH_API_KEY`).
2. **Change path if applicable** (`DB_FILE = "/content/drive/MyDrive/FYP_Agents/articles_db.json"`)
3. **Run the notebook** in .ipynb environment.  
4. **Check output logs** printed.  
5. **Results** are saved automatically to `articles_db.json`.  
6. A **Graphviz diagram** displays the node connections.

# Setup and Import
"""

!pip install openai langgraph
!pip install langchain_community

# remove if not using graph visualization
!apt-get update
!apt-get install -y graphviz libgraphviz-dev pkg-config
!pip install pygraphviz

import json
import openai
import os
import requests
from openai import OpenAI
from IPython.display import Image, display
from langchain_community.utilities import SearchApiAPIWrapper
from bs4 import BeautifulSoup

"""# API Configuration and  Article Sample"""

OPENAI_API_KEY = "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"  # Replace with your OpenAI key
SEARCH_API_KEY = "fao8F6mEtmqZmW2y6gj3saPV"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

article_data = {
    "title": "The US firms backing Trump's fight over trade....",
    "content": (
        """“
     Head to the grocery store in the US and the shelves are stocked with jars of St Dalfour strawberry spread and Bonne Maman raspberry preserves - some of the more than $200m (£154m) in jams that Europe sends to America each year.
But try looking for American-made jelly in Europe, and you're likely to come up short.
The US exports less than $300,000 in jam each year to the bloc.
It's an imbalance that US company JM Smucker, one of the biggest sellers of such products in America, blames on a 24%-plus import tax its fruit spreads face in the EU.
"The miniscule value of US exports to the European Union is entirely attributable to the high EU tariff," the company wrote in a letter to the White House this month, asking the Trump administration to address the issue as it prepares to levy "reciprocal" tariffs on America's biggest trading partners.
"Reciprocal US tariffs on EU jams and jellies would serve to level the playing field," the company said, noting that the highest US jam tariff is currently just 4.5%.
Globally, Trump's push to deploy tariffs against close trading partners - many of which have average tariff levels similar to America's - has generated anger and bafflement, while drawing warnings from economists about higher prices and other potential economic pain.
Some businesses in the US have echoed those concerns, but Trump's calls for tariffs are also channelling longstanding frustrations many firms feel about foreign competition and policies they face abroad.
Smucker's letter was one of hundreds submitted to the White House, seeking to influence the next set of tariffs, expected to be unveiled on 2 April.

Apple farmers raised the big disparity in import duties their fruit faces in countries such as India (50%), Thailand (40%) and Brazil (10%), as well as sanitary rules in countries such as Australia they said unfairly block their exports.
Streaming businesses flagged digital taxes in Canada and Turkey that they said "unfairly target and discriminate" against US companies.
The oil and natural gas lobby criticised regulations in Mexico that require partnership with the state-owned oil company and other policies.
The White House itself spotlighted uneven ethanol tariffs in Brazil (18%, compared with 2.5% in the US), car tariffs in Europe (10%, compared with 2.5% in the US) and motorcycles in India (until a few years ago, 100% vs 2.4% in the US).
Trump has suggested that his plan for reciprocal tariffs will help remedy such grievances, pumping up his announcement as "Liberation Day".
But even the businesses seeking action on their own issues have expressed hesitation about the president's tariff-first, ask-questions-later strategy, which risks retaliation and a wider trade war.
With 2 April looming, there remains widespread uncertainty about the goals and scope of White House plans, especially as Trump launches a broadside of other duties.
"We're going to be nice," he said this week, at the same time as he announced potentially devastating tariffs on foreign cars and car parts. "I think people will be pleasantly surprised."

India has already said it would lower its tariffs on motorcycles - an apparent bet that Trump's tariffs are a strategy designed to gain leverage for trade talks.
But analysts warned that those hoping that Trump plans to use his reciprocal tariffs to negotiate changes elsewhere may be disappointed, as the president has also indicated he could be satisfied by simply hitting back.
"Some days it's about revenge and just equalising things and other days it's about lowering tariffs and then other days, third days, it's about bringing manufacturing to the United States," said William Reinsch, senior adviser at the Center for Strategic and International Studies, a Washington thinktank.
"He's used them all at different times - there's not a single thread here that you can rely on."

The mismatch between the blunt tool of tariffs and the more niche issues firms want the White House to champion has led to a delicate dance, as businesses suggest tariffs in their own interest, while also hoping to avoid the repercussions of the kind of sweeping duties that Trump has suggested might be on the table.
For example, steel manufacturer NorthStar BlueScope Steel, which employs 700 people in the US melting steel from recycled metal, urged Trump to expand tariffs on steel and aluminium to parts.
At the same time, however, it asked for an exemption for the raw materials it needs, such as scrap metal.
Likewise, the lobby group for JM Smucker and other big food manufacturers, the Consumer Brands Association, warned against "overly broad and sweeping tariffs" that might end up making it more expensive for its members to import ingredients like cocoa, which are not made in the US.
"I don't necessarily want the current administration to say, well, we'll impose a tariff," Tom Madrecki, the group's vice president of supply chain resiliency, said at a recent forum about tariffs, hosted by Farmers for Free Trade.
"It's this careful balance between yes, I want you to take an America First trade policy and action to counter unfair trade policies abroad ... but maybe not quite in that way."
Wilbur Ross, who served as Trump's commerce secretary in his first term, said he thought business worries would dissipate as Trump's plans become clear, calling 2 April a "big step".
But he noted that the president saw little downside to using tariffs, viewing them as either a source of new revenue, or a way to reduce imports and encourage more manufacturing.
"He's very committed," he said. "People should have known that something like this was coming because he's been talking about it for many, many years."
Republicans, traditionally the pro-trade party, have stayed supportive of Trump's strategy, even as tariff announcements have been blamed for the recent stock market sell-off and weakness in recent surveys of business and consumer confidence.
At a recent hearing on trade, Representative Jodey Arrington, a Republican who represents Texas, acknowledged that there might be "some pain associated on the front end" but maintained Trump's focus on the issue would create opportunities for his constituents in the end.
"It just seems to me that it's un-American to not fight for our American manufacturers, producers and workers to simply have an even playing field," he said.
"We're simply attempting ... to reset those relationships such that we're playing by the same set of rules," he added. "Then everyone wins."
"""
    ),
    "source": "BBC News",
    "url": "https://www.bbc.com/news/articles/c04z0ydvql2o",
    "date": "2025-03-29"
}

# Displays article title and content snippet for validation
print(f"Article Title: {article_data['title']}")
print("Content Snippet:", article_data['content'][:100] + "...")

"""# Drive Integration and Database Configuration"""

from google.colab import drive
drive.mount('/content/drive')

DB_FILE = "/content/drive/MyDrive/FYP_Agents/articles_db.json"

"""# Article Database Utilities

Reades, writes, and searches articles stored JSON file
"""

def load_articles_db():
    """Loads existing articles from the JSON file, returning an empty list if none is found."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_articles_db(articles):
    """Saves the updated list of articles back to the JSON file."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def find_article_by_title_in_db(new_title, articles_db):
    """Returns the matching article dict if `new_title` (case-insensitive) matches an existing title, else None."""
    for art in articles_db:
        if art.get("title", "").strip().lower() == new_title.strip().lower():
            return art
    return None

def fetch_analysis_if_same_title(new_article):
    """Returns `analysis_results` if an article with the same title exists, otherwise None."""
    articles_db = load_articles_db()
    match = find_article_by_title_in_db(new_article["title"], articles_db)
    if match is not None:
        print("Found an article with the same title in DB. Skipping re-analysis.\n")
        return match["analysis_results"]
    return None

"""# HEAD Node and Router

Coordinates subagent calls based on LLM decisions and orchestrates the pipeline flow.
"""

def head_node(state):
    """
    Determines which subagents need to be invoked based on the article content by calling GPT.
    Updates the state with flags indicating whether to run FakeNews, Credibility, and Sentiment checks.
    Always sets 'need_summary' to True.
    """
    print("[HEAD NODE] Deciding which subagents to call...")
    article_text = state.get("article_content", "")

    system_prompt = """
You are the HEAD agent. You must decide whether to call three agents:
- FakeNews
- Credibility
- Sentiment

In almost all cases, each agent should be called (call=true).
Only set call=false if there is a clear, specific reason the agent is absolutely unnecessary.

Return ONLY valid JSON of this exact structure:
{
  "fake_news": {
    "call": true/false,
    "reason": "short reason"
  },
  "credibility": {
    "call": true/false,
    "reason": "short reason"
  },
  "sentiment": {
    "call": true/false,
    "reason": "short reason"
  }
}
No extra keys, no code fences, no additional text.
"""

    user_prompt = f"""Article Content:
{article_text}

Return only the JSON object."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        raw_json_str = response.choices[0].message.content.strip()
        print("[HEAD NODE] GPT decision raw JSON:", raw_json_str)
    except Exception as e:
        print("[HEAD NODE] GPT call failed:", e)
        raw_json_str = """{
  "fake_news": {"call": true, "reason": "Fallback"},
  "credibility": {"call": true, "reason": "Fallback"},
  "sentiment": {"call": true, "reason": "Fallback"}
}"""

    try:
        decisions = json.loads(raw_json_str)
    except:
        decisions = {
            "fake_news": {"call": True, "reason": "ParseError"},
            "credibility": {"call": True, "reason": "ParseError"},
            "sentiment": {"call": True, "reason": "ParseError"},
        }

    # Update state with subagent flags
    state["need_fake_news_check"] = decisions["fake_news"].get("call", False)
    state["need_credibility_check"] = decisions["credibility"].get("call", False)
    state["need_sentiment_check"] = decisions["sentiment"].get("call", False)
    state["need_summary"] = True  # Always do summary

    state["agents_to_be_called"] = decisions
    return state

def router(state):
    """
    Routes subagent execution in the fixed order: FakeNews -> Credibility -> Sentiment -> Summary.
    Terminates once all four checks have run.
    """
    print("[ROUTER] Checking what to run next...")
    if "agents_called" not in state:
        state["agents_called"] = []
    if "agent_invocation_counts" not in state:
        state["agent_invocation_counts"] = {}

    def run_next(agent_name):
        print(f"[ROUTER] -> Next agent: {agent_name}")
        state["agent_invocation_counts"][agent_name] = (
            state["agent_invocation_counts"].get(agent_name, 0) + 1
        )
        state["agents_called"].append(agent_name)
        return agent_name

    if state.get("need_fake_news_check", False) and "fake_news_result" not in state:
        return run_next("FakeNewsAgent")

    if state.get("need_credibility_check", False) and "credibility_result" not in state:
        return run_next("CredibilityAgent")

    if state.get("need_sentiment_check", False) and "sentiment_result" not in state:
        return run_next("SentimentAgent")

    if state.get("need_summary", False) and "summary_result" not in state:
        return run_next("SummaryAgent")

    print("[ROUTER] All four agents have finished. Ending pipeline.")
    return "end"

"""# FakeNewsAgent, CredibilityAgent, and SentimentAgent

Subagents for verifying factual claims, evaluating credibility, and analyzing sentiment in articles.
"""

class FakeNewsAgent:
    """
    FakeNewsAgent:
    1) Extracts up to 10 factual claims from the article text using GPT.
    2) Uses SearchApi to find relevant pages for each claim.
    3) Fetches top link content with BeautifulSoup.
    4) Calls GPT to check if external text confirms each claim.
    5) Summarizes results with foundCount and averageScore.
    """

    def __call__(self, state):

        print("\n=== [FakeNewsAgent] START ===\n")

        # 1) Obtain the article text and title from state
        article_text = state["article_content"]
        article_title = state.get("article_title", "Untitled Article")
        state["last_agent_run"] = "FakeNewsAgent"

        print("[FakeNewsAgent] Article length:", len(article_text))
        print("[FakeNewsAgent] Article Title:", article_title)

        # 2) Extract up to 10 claims via GPT
        print("\n[FakeNewsAgent] STEP A: Extracting 10 claims from article...")
        extract_prompt = f"""
You are an assistant that extracts exactly 10 factual claims from this article.
Return them as a valid JSON array of 10 strings (no commentary, code fences, or backticks).

Article Title: {article_title}
Article Text: {article_text}
"""
        messages_extract = [
            {"role": "system", "content": extract_prompt},
            {"role": "user", "content": "List 10 claims in a JSON array now."},
        ]
        try:
            extract_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_extract
            )
            raw_claims = extract_resp.choices[0].message.content.strip()
        except Exception as e:
            print("[FakeNewsAgent] GPT call for claim extraction FAILED:", e)
            raw_claims = "[]"

        raw_claims = self.remove_code_fences(raw_claims)
        print("[FakeNewsAgent] Raw claims extraction output:\n", raw_claims)

        try:
            claims_list = json.loads(raw_claims)
            if not isinstance(claims_list, list):
                raise ValueError("Parsed JSON is not a valid list.")
        except Exception as e:
            print("[FakeNewsAgent] JSON parse error on extracted claims:", e)
            claims_list = []

        claims_list = claims_list[:10]
        if not claims_list:
            print("[FakeNewsAgent] No claims extracted. Storing empty result.")
            state["fake_news_result"] = {
                "results": [],
                "foundCount": 0,
                "averageScore": 0,
                "articleTitle": article_title,
                "totalClaims": 0
            }
            print("=== [FakeNewsAgent] END ===\n")
            return state

        print(f"[FakeNewsAgent] Successfully extracted {len(claims_list)} claims.")

        # 3) Search for each claim and parse HTML with BeautifulSoup
        print("\n[FakeNewsAgent] STEP B: Searching each claim & parsing HTML with BeautifulSoup.")
        search_tool = SearchApiAPIWrapper(searchapi_api_key=SEARCH_API_KEY)
        verification_data = []

        for idx, claim in enumerate(claims_list, start=1):
            print(f"\n[FakeNewsAgent] Claim #{idx}: {claim}")
            sr_results = search_tool.results(claim)
            external_text = ""
            if "organic_results" in sr_results:
                links_fetched = 0
                for item in sr_results["organic_results"]:
                    link_url = item.get("link")
                    if link_url and link_url.startswith("http"):
                        print(f"  -> Attempting to fetch link: {link_url}")
                        try:
                            resp = requests.get(link_url, timeout=10)
                            if resp.status_code == 200:
                                page_text = self.extract_text_from_html(resp.text, link_url)
                                if page_text:
                                    external_text += f"\n\n[SOURCE: {link_url}]\n{page_text}"
                                    links_fetched += 1
                                    # Currently fetching only one link per claim
                                    if links_fetched >= 1:
                                        break
                            else:
                                print(f"  -> HTTP {resp.status_code}. Skipping.")
                        except Exception as e:
                            print(f"  -> Error fetching link: {e}")
                    else:
                        print("  -> No valid link or link is not http.")
            else:
                print("  -> No organic_results in search.")

            # 4) Call GPT to see if external text confirms the claim
            found_bool = self.check_claim_with_gpt(claim, external_text)
            verification_data.append({
                "claim": claim,
                "found": found_bool
            })

        # 5) Summarize results; found => score=100
        print("\n[FakeNewsAgent] STEP C: Summarizing foundCount & averageScore.")
        results_list = []
        found_count = 0
        for item in verification_data:
            found = item["found"]
            score = 100 if found else 0
            results_list.append({
                "claim": item["claim"],
                "found": found,
                "score": score
            })
            if found:
                found_count += 1

        average_score = (found_count / 10) * 100
        final_json = {
            "results": results_list,
            "foundCount": found_count,
            "averageScore": average_score,
            "articleTitle": article_title,
            "totalClaims": len(claims_list)
        }
        state["fake_news_result"] = final_json

        print("\n=== [FakeNewsAgent] END ===\n")
        return state

    def check_claim_with_gpt(self, claim, external_text):
        """
        Checks if the external_text supports the given claim. Returns True if confirmed, else False.
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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Return your JSON verdict."},
        ]
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            raw_reply = response.choices[0].message.content.strip()
        except Exception as e:
            print("[FakeNewsAgent] GPT call failed for claim-checking:", e)
            return False

        raw_reply = self.remove_code_fences(raw_reply)
        print("[FakeNewsAgent] GPT raw claim-check reply:", raw_reply)

        try:
            data = json.loads(raw_reply)
            return bool(data.get("supports", False))
        except:
            print("[FakeNewsAgent] Failed to parse GPT's JSON. Defaulting to False.")
            return False

    def extract_text_from_html(self, html_str, link_url):
        """
        Uses BeautifulSoup to parse <p> content from HTML and returns extracted text.
        """
        soup = BeautifulSoup(html_str, "html.parser")
        paragraphs = soup.find_all("p")
        text_content = "\n".join(p.get_text() for p in paragraphs if p.get_text())
        print(f"  -> [HTML PARSER] Extracted text length: {len(text_content)} from {link_url}")
        return text_content

    def remove_code_fences(self, text: str):
        """
        Removes Markdown code fences (e.g., ```json) from GPT output.
        """
        import re
        t = text.strip()
        t = re.sub(r"^```[a-zA-Z]*", "", t)
        t = re.sub(r"```$", "", t)
        return t.strip()

ORIGINAL_PROMPTS = {
    "CredibilityAgent": """
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
""",
    "SentimentAgent": """
You are SentimentAgent, specializing in granular sentiment analysis of newspaper articles.
1. Overall sentiment label (e.g. “negative,” “positive,” or “mixed”).
2. Sentiment score (0–100).
3. Provide justification in JSON, citing key phrases.

Return JSON, e.g.:
{
  "sentimentLabel": "negative",
  "sentimentScore": 30,
  "justification": ["Phrase ...", "Phrase ..."]
}
"""
}

class CredibilityAgent:
    def __call__(self, state):
        print("\n=== CredibilityAgent Start ===\n")
        state["last_agent_run"] = "CredibilityAgent"
        article_text = state["article_content"]
        article_title = state.get("article_title", "Untitled Article")

        # Use refined prompt if available; otherwise, the original
        refined_prompts = state.get("refined_prompts", {})
        if "CredibilityAgent" in refined_prompts:
            system_prompt = refined_prompts["CredibilityAgent"]
            print("[CredibilityAgent] Using REFINED prompt from state.")
        else:
            system_prompt = ORIGINAL_PROMPTS["CredibilityAgent"]
            print("[CredibilityAgent] Using ORIGINAL prompt.")

        # Prepare the final prompt by appending article text and title
        final_prompt = f"{system_prompt}\n\nArticle Title: {article_title}\nArticle Text: {article_text}"

        print("[CredibilityAgent] Calling GPT for credibility analysis...")
        msgs = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": "Assess now in JSON."}
        ]
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs
        )
        out = resp.choices[0].message.content.strip()
        print("[CredibilityAgent] Raw output:", out)

        state["credibility_result"] = out
        print("=== CredibilityAgent End ===\n")
        return state

class SentimentAgent:
    def __call__(self, state):
        print("\n=== SentimentAgent Start ===\n")
        state["last_agent_run"] = "SentimentAgent"
        article_text = state["article_content"]

        # Use refined prompt if available; otherwise, original
        refined_prompts = state.get("refined_prompts", {})
        if "SentimentAgent" in refined_prompts:
            system_prompt = refined_prompts["SentimentAgent"]
            print("[SentimentAgent] Using REFINED prompt from state.")
        else:
            system_prompt = ORIGINAL_PROMPTS["SentimentAgent"]
            print("[SentimentAgent] Using ORIGINAL prompt.")

        final_prompt = f"{system_prompt}\n\nArticle Text:\n{article_text}"

        print("[SentimentAgent] Calling GPT for sentiment analysis...")
        messages = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": "Please return valid JSON."},
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        result = response.choices[0].message.content.strip()
        print("[SentimentAgent] Raw output:", result)

        state["sentiment_result"] = result
        print("=== SentimentAgent End ===\n")
        return state

"""# Summary Agent

Generates a concise 100-word summary of the article.
"""

class SummaryAgent:
    """Summarizes the article in exactly 100 words."""
    def __call__(self, state):
        print("\n=== SummaryAgent Start ===\n")
        article_text = state["article_content"]

        system_prompt = (
            "You are a summary agent. Summarize the article in exactly 100 words. "
            "No more, no less. Maintain coherence."
        )

        user_prompt = f"Article text:\n\n{article_text}\n\nSummarize in exactly 100 words."

        print("[SummaryAgent] Calling GPT for 100-word summary...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        summary_100_words = response.choices[0].message.content.strip()

        state["summary_result"] = summary_100_words
        print("[SummaryAgent] Summary created.")
        print("=== SummaryAgent End ===\n")
        return state

"""# Validation Agent

Validates subagent outputs and refines prompts if needed.
"""

class ValidatorAgent:
    """Ensures subagent outputs adhere to the required formats; refines prompts on failure."""

    def __call__(self, state):
        print("\n=== ValidatorAgent Start ===\n")
        last_agent = state.get("last_agent_run", None)
        state["validation_passed"] = True  # Default to passing

        # Refines prompts only for CredibilityAgent or SentimentAgent
        if last_agent in ("FakeNewsAgent", "CredibilityAgent", "SentimentAgent"):
            validated_ok, failure_reason = self.validate_with_gpt(state, last_agent)
            state["validation_passed"] = validated_ok

            if not validated_ok:
                # Attempt to refine the prompt only for Credibility or Sentiment
                if last_agent in ("CredibilityAgent", "SentimentAgent"):
                    print(f"[ValidatorAgent] Attempting to refine the prompt for {last_agent}...")
                    original_prompt = ORIGINAL_PROMPTS[last_agent]
                    refined = self.create_refined_prompt(original_prompt, failure_reason)
                    # Store the refined prompt in state for subsequent usage
                    if "refined_prompts" not in state:
                        state["refined_prompts"] = {}
                    state["refined_prompts"][last_agent] = refined
        else:
            print("[ValidatorAgent] Last agent was not one of (FakeNews, Credibility, Sentiment). No validation needed.")

        print("\n=== ValidatorAgent End ===\n")
        return state

    def validate_with_gpt(self, state, subagent_name):
        """
        Checks if the subagent's output meets the expected JSON format.
        Returns (bool_passed, reason_string).
        """
        print(f"[ValidatorAgent] Validating output for {subagent_name}...")

        # Retrieve subagent output
        if subagent_name == "FakeNewsAgent":
            subagent_output = state.get("fake_news_result", {})
            instructions = "Extract 10 claims + produce foundCount, averageScore in JSON."
        elif subagent_name == "CredibilityAgent":
            subagent_output = state.get("credibility_result", "")
            instructions = "Return JSON with sourceReputationScore, titleContentScore, misleadingTitlesScore, averageScore..."
        else:  # "SentimentAgent"
            subagent_output = state.get("sentiment_result", "")
            instructions = "Return JSON with sentimentLabel, sentimentScore, justification..."

        # Convert to text if the output is a dictionary
        if isinstance(subagent_output, dict):
            subagent_output_str = json.dumps(subagent_output, ensure_ascii=False, indent=2)
        else:
            subagent_output_str = str(subagent_output)

        system_prompt = f"""
You are a lenient ValidatorAgent verifying the {subagent_name}'s output.
It should follow these instructions:
{instructions}

Only if the output is absurdly far from the requested content, fail.
Otherwise, pass.

Return ONLY JSON:
{{
  "validation_passed": true/false,
  "reason": "brief explanation"
}}
No extra text.
"""

        user_prompt = f"Subagent Output:\n{subagent_output_str}\n\n"

        print("[ValidatorAgent] GPT validation system_prompt:", system_prompt)
        print("[ValidatorAgent] GPT validation user_prompt:", user_prompt)

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            raw_reply = resp.choices[0].message.content.strip()
            print("[ValidatorAgent] GPT raw reply:", raw_reply)
        except Exception as e:
            print("[ValidatorAgent] GPT call failed:", e)
            return (False, "GPT call failed")

        raw_reply = self.remove_code_fences(raw_reply)

        try:
            data = json.loads(raw_reply)
            pass_bool = data.get("validation_passed", False)
            reason_str = data.get("reason", "")
            print(f"[ValidatorAgent] pass_bool={pass_bool}, reason={reason_str}")
            return (pass_bool, reason_str)
        except:
            print("[ValidatorAgent] JSON parse error on GPT reply.")
            return (False, "Parse Error in validator response")

    def create_refined_prompt(self, original_prompt, failure_reason):
        """
        Refines the original prompt to address the failure reason.
        """
        print("[ValidatorAgent] create_refined_prompt -> refining original prompt.")
        system_prompt = "You are a system that refines subagent prompts based on a failure reason."
        user_msg = f"""
Original Prompt:
{original_prompt}

Failure Reason:
{failure_reason}

Please provide an improved version of the prompt, addressing the issue.
Return plain text only, no JSON fences.
"""
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ]
            )
            refined_prompt = resp.choices[0].message.content.strip()
            refined_prompt = self.remove_code_fences(refined_prompt)
            print("[ValidatorAgent] Refined prompt generated:\n", refined_prompt)
            return refined_prompt
        except Exception as e:
            print("[ValidatorAgent] Failed to refine prompt:", e)
            # Fallback to original if refinement fails
            return original_prompt

    def remove_code_fences(self, text: str):
        """Removes Markdown code fences from GPT output."""
        import re
        t = text.strip()
        t = re.sub(r"^```[a-zA-Z]*", "", t)
        t = re.sub(r"```$", "", t)
        return t.strip()

def validation_router(state):
    """
    Routes the pipeline based on validation status. If validation fails, re-run the last agent; otherwise proceed to Head.
    """
    print("[VALIDATION ROUTER] Checking validation_passed...")
    if not state.get("validation_passed", True):
        agent_to_retry = state.get("last_agent_run", "Head")
        print(f"[VALIDATION ROUTER] Validation failed. Re-run {agent_to_retry}.")
        return agent_to_retry
    else:
        print("[VALIDATION ROUTER] Validation passed. Proceed to Head.")
        return "Head"

"""# Workflow Assembly

"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class AnalysisState(TypedDict, total=False):
    # Defines the structure used throughout the workflow
    article_content: str
    article_title: str
    fake_news_result: dict
    credibility_result: str
    sentiment_result: str
    summary_result: str
    agents_called: list
    agent_invocation_counts: dict
    last_agent_run: str
    validation_passed: bool
    refined_prompts: dict

workflow = StateGraph(AnalysisState)

# Register each node in the workflow
workflow.add_node("Head", head_node)
workflow.add_node("FakeNewsAgent", FakeNewsAgent())
workflow.add_node("CredibilityAgent", CredibilityAgent())
workflow.add_node("SentimentAgent", SentimentAgent())
workflow.add_node("SummaryAgent", SummaryAgent())
workflow.add_node("ValidatorAgent", ValidatorAgent())

# Define the initial node
workflow.set_entry_point("Head")

# Connect Head node to subsequent agents or end the workflow
workflow.add_conditional_edges(
    "Head",
    router,
    {
        "FakeNewsAgent": "FakeNewsAgent",
        "CredibilityAgent": "CredibilityAgent",
        "SentimentAgent": "SentimentAgent",
        "SummaryAgent": "SummaryAgent",
        "end": END
    }
)

# Direct outputs of these agents to the ValidatorAgent
workflow.add_edge("FakeNewsAgent", "ValidatorAgent")
workflow.add_edge("CredibilityAgent", "ValidatorAgent")
workflow.add_edge("SentimentAgent", "ValidatorAgent")

# The SummaryAgent result flows directly back to Head
workflow.add_edge("SummaryAgent", "Head")

# Validation either retries the same agent or proceeds to Head
workflow.add_conditional_edges(
    "ValidatorAgent",
    validation_router,
    {
        "FakeNewsAgent": "FakeNewsAgent",
        "CredibilityAgent": "CredibilityAgent",
        "SentimentAgent": "SentimentAgent",
        "Head": "Head"
    }
)

app = workflow.compile()

def run_analysis_and_save(article_data):
    print("[MAIN] Invoking workflow...")
    initial_state = {
        "article_content": article_data["content"],
        "article_title": article_data["title"]
    }
    final_state = app.invoke(initial_state)

    print("\n[MAIN] Analysis Results:\n")

    # Display results from the FakeNewsAgent
    fn_raw = final_state.get("fake_news_result")
    print("=== Fake News Agent Output ===")
    if fn_raw:
        print(json.dumps(fn_raw, indent=2, ensure_ascii=False))
    else:
        print("(No Fake News data found.)")

    # Display credibility analysis results
    print("\n=== CredibilityAgent Output ===")
    print(final_state.get("credibility_result"))

    # Display sentiment analysis results
    print("\n=== SentimentAgent Output ===")
    print(final_state.get("sentiment_result"))

    # Display summary
    print("\n=== SummaryAgent Output ===")
    print(final_state.get("summary_result"))

    # Append analysis to the database
    articles_db = load_articles_db()
    new_record = {
        "title": article_data["title"],
        "content": article_data["content"],
        "analysis_results": {
            "fake_news_result": final_state.get("fake_news_result"),
            "credibility_result": final_state.get("credibility_result"),
            "sentiment_result": final_state.get("sentiment_result"),
            "summary_result": final_state.get("summary_result")
        }
    }
    articles_db.append(new_record)
    save_articles_db(articles_db)
    print("[MAIN] Saved new analysis to DB.\n")

    return final_state

"""# Execution"""

analysis_from_db = fetch_analysis_if_same_title(article_data)
if analysis_from_db:
    print("=== Loaded from DB ===")
    final_state = analysis_from_db
else:
    print("No article with the same title found. Proceed with new analysis...")
    final_state = run_analysis_and_save(article_data)

print("\nDone.\n")

"""# Graph Visualization"""

png_data = app.get_graph().draw_png()
display(Image(png_data))

