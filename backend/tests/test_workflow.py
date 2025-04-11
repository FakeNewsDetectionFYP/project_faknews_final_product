import pytest
import asyncio
import os
import sys
from typing import Dict, Any

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.workflow import (
    process_article,
    HeadNode,
    FakeNewsAgent,
    CredibilityAgent,
    SentimentAgent,
    SummaryAgent,
    router,
    validation_router
)

# Basic test URLs
TEST_URLS = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://fakesource.com/conspiracy-theory"
]

@pytest.mark.asyncio
async def test_process_article():
    """Test that the process_article function returns expected structure"""
    # Process a test article
    result = await process_article(TEST_URLS[0])
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "article_title" in result
    assert "article_url" in result
    
    # At least one agent should be called
    assert "agents_called" in result
    assert len(result["agents_called"]) > 0
    
    # Summary should always be generated
    assert "summary_result" in result

@pytest.mark.asyncio
async def test_head_node():
    """Test that the head node properly initializes agent calls"""
    # Create initial state
    state = {
        "article_content": "Test article content for testing purposes.",
        "article_title": "Test Article",
        "article_url": TEST_URLS[0]
    }
    
    # Run head node
    head_node = HeadNode()
    result = await head_node(state)
    
    # Verify it sets which agents to call
    assert "call_fake_news" in result
    assert "call_credibility" in result
    assert "call_sentiment" in result
    assert "call_summary" in result

@pytest.mark.asyncio
async def test_router():
    """Test that the router properly directs to the correct next agent"""
    # Test with empty state (should route to fake_news first)
    state = {
        "call_fake_news": True,
        "call_credibility": True,
        "call_sentiment": True,
        "call_summary": True
    }
    next_agent = await router(state)
    assert next_agent == "fake_news"
    
    # Test with fake_news completed (should route to credibility)
    state["fake_news_result"] = {"test": "result"}
    next_agent = await router(state)
    assert next_agent == "credibility"
    
    # Test with all but summary completed
    state["credibility_result"] = {"test": "result"}
    state["sentiment_result"] = {"test": "result"}
    next_agent = await router(state)
    assert next_agent == "summary"
    
    # Test with all completed (should end)
    state["summary_result"] = "Summary text"
    next_agent = await router(state)
    assert next_agent == "end"

@pytest.mark.asyncio
async def test_agents_individually():
    """Test each agent individually"""
    # Initial state
    base_state = {
        "article_content": "Test article content for testing purposes.",
        "article_title": "Test Article",
        "article_url": TEST_URLS[0],
        "agents_called": [],
        "agent_invocation_counts": {}
    }
    
    # Test FakeNewsAgent
    fake_news_agent = FakeNewsAgent()
    fake_news_result = await fake_news_agent(base_state.copy())
    assert "fake_news_result" in fake_news_result
    assert fake_news_result["last_agent_run"] == "fake_news"
    
    # Test CredibilityAgent
    credibility_agent = CredibilityAgent()
    credibility_result = await credibility_agent(base_state.copy())
    assert "credibility_result" in credibility_result
    assert credibility_result["last_agent_run"] == "credibility"
    
    # Test SentimentAgent
    sentiment_agent = SentimentAgent()
    sentiment_result = await sentiment_agent(base_state.copy())
    assert "sentiment_result" in sentiment_result
    assert sentiment_result["last_agent_run"] == "sentiment"
    
    # Test SummaryAgent
    summary_agent = SummaryAgent()
    summary_result = await summary_agent(base_state.copy())
    assert "summary_result" in summary_result
    assert summary_result["last_agent_run"] == "summary"

@pytest.mark.asyncio
async def test_validation_router():
    """Test that the validation router works correctly"""
    # Test with passing validation
    state = {"validation_passed": True, "last_agent_run": "fake_news"}
    result = await validation_router(state)
    assert result == "continue"
    
    # Test with failing validation
    state = {"validation_passed": False, "last_agent_run": "fake_news"}
    result = await validation_router(state)
    assert result == "fake_news"  # Should rerun the agent

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 