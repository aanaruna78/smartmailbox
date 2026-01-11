import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.integrations.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm import LLMService

# Mock Provider for testing without a running Ollama instance
class MockProvider(BaseLLMProvider):
    async def generate(self, prompt: str, params: dict = None) -> LLMResponse:
        # Simulate processing time
        await asyncio.sleep(0.5) 
        return LLMResponse(
            text="This is a generated draft response based on the prompt.",
            tokens_used=15,
            latency_ms=500.0,
            model_name="mock-model"
        )

class SlowProvider(BaseLLMProvider):
    async def generate(self, prompt: str, params: dict = None) -> LLMResponse:
        # Simulate very slow response
        await asyncio.sleep(2.0)
        return LLMResponse(text="Too late", model_name="slow")

async def test_llm_service():
    print("--- Verifying LLM Service ---")
    
    # 1. Test Successful Generation
    print("\n1. Testing Successful Generation...")
    service = LLMService(provider=MockProvider())
    try:
        resp = await service.generate_draft("Write an email", timeout=1.0)
        print(f"✅ Success! Response: {resp.text}")
        print(f"   Latency: {resp.latency_ms}ms")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 2. Test Timeout
    print("\n2. Testing Timeout handling...")
    slow_service = LLMService(provider=SlowProvider())
    try:
        await slow_service.generate_draft("Write an email", timeout=0.1)
        print("❌ Failed: Should have timed out but didn't.")
    except Exception as e:
        if "timed out" in str(e):
             print(f"✅ Success! Caught expected timeout error: {e}")
        else:
             print(f"❌ Failed: Caught unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_service())
