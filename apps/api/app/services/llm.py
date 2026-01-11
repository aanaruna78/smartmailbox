import asyncio
import logging
from typing import Optional, Dict, Any
from app.integrations.llm.base import BaseLLMProvider, LLMResponse
from app.integrations.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        # Default to OllamaProvider if none provided
        # In a real app, this would be configured via settings
        self.provider = provider or OllamaProvider()

    async def generate_draft(self, prompt: str, timeout: float = 30.0, params: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Generate text using the configured LLM provider with timeout and logging.
        """
        try:
            logger.info(f"Generating draft with model {getattr(self.provider, 'model', 'unknown')}")
            
            # Enforce overall operation timeout
            response = await asyncio.wait_for(
                self.provider.generate(prompt, params), 
                timeout=timeout
            )
            
            logger.info(f"Generated {response.tokens_used} tokens in {response.latency_ms:.2f}ms")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"LLM Generation timed out after {timeout}s")
            raise Exception("LLM Generation timed out. The model took too long to respond.")
            
        except Exception as e:
            logger.error(f"LLM Generation failed: {str(e)}")
            raise e
