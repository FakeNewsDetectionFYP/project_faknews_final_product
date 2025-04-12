# LangGraph Agents

This directory contains the agent classes used in the LangGraph workflow for news article analysis.

## Agent Overview

- `head_node.py` - Decision agent that determines which other agents to call
- `fake_news_agent.py` - Analyzes articles for potentially false claims
- `credibility_agent.py` - Evaluates source credibility and content alignment
- `sentiment_agent.py` - Analyzes sentiment and bias in the article
- `summary_agent.py` - Generates concise summaries of articles
- `validator_agent.py` - Validates outputs from other agents

## Refactoring Notes

These agent classes were previously part of a monolithic `workflow.py` file and have been refactored into separate modules to improve maintainability. Each agent maintains the same functionality but is now in its own file with proper imports and dependencies.

## Dependency Issues

There may be dependency conflicts between LangGraph and LangChain versions. If you encounter issues, consider updating the versions in your requirements.txt file. The system will gracefully fallback to a sequential processing mode if LangGraph cannot be imported.

Recommended compatible versions:
```
langchain>=0.0.335
langgraph>=0.0.25
langchain-core>=0.1.0
```

## Usage

Agents are imported and used through the main workflow entry point. You typically don't need to instantiate them directly. 