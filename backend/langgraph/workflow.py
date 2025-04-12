"""
Entry point for the LangGraph workflow

This file simply re-exports the necessary components from the 
refactored modules for backward compatibility.
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Re-export the types
from .types import AnalysisState

# Re-export the agents
from .agents import (
    FakeNewsAgent,
    CredibilityAgent,
    SentimentAgent,
    SummaryAgent,
    ValidatorAgent,
    HeadNode
)

# Re-export the router functions
from .routers import router, validation_router

# Re-export utility functions
from .utility import (
    fetch_article_content,
    create_workflow,
    process_article
) 