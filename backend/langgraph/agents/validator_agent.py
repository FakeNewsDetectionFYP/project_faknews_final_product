"""
ValidatorAgent - Validates the output of other agents
"""

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import the AnalysisState type
from ..types import AnalysisState

class ValidatorAgent:
    """
    Agent that validates the output of other agents.
    """
    async def __call__(self, state: AnalysisState) -> AnalysisState:
        """Validate agent outputs and refine prompts if needed"""
        logger.info(f"ValidatorAgent: Validating output from {state['last_agent_run']}")
        
        # In real implementation, this would:
        # 1. Check if the agent output is valid and complete
        # 2. Refine prompts if necessary
        
        # Mock implementation for development
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Always pass validation in mock mode
        state["validation_passed"] = True
        
        return state 