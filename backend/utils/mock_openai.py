"""
Mock OpenAI client for development and testing.
This allows testing without using real API keys.
"""
import json
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MockMessage:
    """Mock for OpenAI's message object"""
    def __init__(self, content: str):
        self.content = content

class MockChoice:
    """Mock for OpenAI's choice object"""
    def __init__(self, message_content: str):
        self.message = MockMessage(message_content)

class MockChatCompletionResponse:
    """Mock for OpenAI's chat completion response"""
    def __init__(self, message_content: str):
        self.choices = [MockChoice(message_content)]

class MockCompletions:
    """Mock for OpenAI's completions sub-client"""
    async def create(self, **kwargs):
        """Mock completions create method"""
        logger.info("MOCK OpenAI completion called")
        
        # Extract messages from kwargs
        messages = kwargs.get("messages", [])
        
        # Get the last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return MockChatCompletionResponse("No user message provided")
        
        user_message = user_messages[-1]["content"]
        
        # Get the system message if any
        system_messages = [m for m in messages if m.get("role") == "system"]
        system_instruction = system_messages[0]["content"] if system_messages else ""
        
        # Decide what to return based on the prompt content
        response = self._generate_mock_response(user_message, system_instruction)
        
        # Simulate API latency
        await asyncio.sleep(0.5)
        
        return MockChatCompletionResponse(response)
    
    def _generate_mock_response(self, prompt: str, system: str) -> str:
        """Generate appropriate mock responses based on the content of the prompt"""
        if "summarize" in prompt.lower() or "summary" in system.lower():
            return "This is a mock summary of the article. It discusses various points about the topic in a concise manner, highlighting the key facts and perspectives mentioned in the original text."
        
        if "sentiment" in prompt.lower() or "sentiment" in system.lower():
            return json.dumps({
                "sentiment": "negative",
                "polarity": -0.3,
                "subjectivity": 0.6,
                "justification": "The text contains critical language and challenging perspectives on the topic."
            })
            
        if "credibility" in prompt.lower() or "credibility" in system.lower():
            return json.dumps({
                "source_reputation": 0.75,
                "title_content_alignment": 0.9,
                "misleading_headline": False,
                "justification": "The source is generally reputable and the content matches the headline."
            })
            
        if "fake news" in prompt.lower() or "fake" in system.lower():
            return json.dumps({
                "claims_verified": 4,
                "claims_unverified": 1,
                "verification_score": 0.8,
                "justification": "Most claims appear to be supported by external sources."
            })
            
        if "HEAD agent" in system:
            return json.dumps({
                "fake_news": {"call": True, "reason": "Political content needs fact checking"},
                "credibility": {"call": True, "reason": "Source verification needed"},
                "sentiment": {"call": True, "reason": "Opinion-heavy content"}
            })
            
        if "validate" in prompt.lower() or "validator" in system.lower():
            return json.dumps({
                "validation": "pass",
                "reasoning": "The output meets the required criteria and appears complete."
            })
            
        # Default fallback response
        return "This is a mock response from the OpenAI API."

class MockChat:
    """Mock for OpenAI's chat sub-client"""
    def __init__(self):
        self.completions = MockCompletions()

class MockOpenAI:
    """Mock for OpenAI client"""
    def __init__(self, api_key=None):
        self.chat = MockChat()
        logger.info("Initialized MockOpenAI")
    
    # Add any other methods that need mocking here 