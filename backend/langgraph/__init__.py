"""
LangGraph-based News Article Analysis System

This package provides a graph-based workflow for analyzing news articles using LLMs.
"""

# Re-export the main analysis function as the primary API
from .workflow import process_article

# Also expose important types if needed by other parts of the application
from .types import AnalysisState

# Version information
__version__ = "0.1.0"
