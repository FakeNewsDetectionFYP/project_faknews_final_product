# LangGraph News Analysis System

This module implements a LangGraph-based system for analyzing news articles. It uses a graph-based workflow where specialized agents process different aspects of the article.

## Directory Structure

- `agents/` - Individual agent implementations
- `types.py` - Type definitions for the workflow state
- `routers.py` - Router functions that guide the workflow execution
- `utility.py` - Utility functions for article fetching and workflow creation
- `workflow.py` - Main entry point that re-exports components for backward compatibility

## Agents

The system includes the following agents:

1. **Head Node** - Determines which other agents to call based on article content
2. **Fake News Agent** - Analyzes articles for potentially false claims
3. **Credibility Agent** - Evaluates source credibility and content alignment
4. **Sentiment Agent** - Analyzes sentiment and bias in articles
5. **Summary Agent** - Generates concise article summaries
6. **Validator Agent** - Validates outputs from other agents

## Usage

The main entry point for the system is the `process_article` function:

```python
from backend.langgraph import process_article
import asyncio

# Process an article
result = asyncio.run(process_article(
    "https://example.com/news/article",
    title="Optional title if not available from URL",
    source="Optional source name if not available from URL"
))

# Access analysis results
print(result["summary_result"])  # Article summary
print(result["fake_news_result"])  # Fake news detection
print(result["credibility_result"])  # Credibility evaluation
print(result["sentiment_result"])  # Sentiment analysis
```

## Fallback Mechanism

If LangGraph cannot be imported due to dependency conflicts, the system will automatically fall back to a sequential processing approach, ensuring that analysis can still be performed.

## Dependency Issues

There may be compatibility issues between LangGraph and LangChain versions. The system will log appropriate warnings if it encounters such issues. Consider using compatible versions in your requirements.txt file:

```
langchain>=0.0.335
langgraph>=0.0.25
langchain-core>=0.1.0
```

## API Note

All public functions are re-exported through the workflow.py file to maintain backward compatibility. 