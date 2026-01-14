import httpx
import time
import os
from typing import Optional, Dict, Any
from app.integrations.llm.base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider for text generation."""

    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": params.get("temperature", 0.7) if params else 0.7,
                "maxOutputTokens": params.get("max_tokens", 1024) if params else 1024,
            },
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                # Extract text from Gemini response
                text = ""
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")

                # Get token usage if available
                usage = data.get("usageMetadata", {})
                tokens = usage.get("candidatesTokenCount", 0) + usage.get(
                    "promptTokenCount", 0
                )

                latency = (time.time() - start_time) * 1000

                return LLMResponse(
                    text=text,
                    tokens_used=tokens,
                    latency_ms=latency,
                    model_name=self.model,
                )
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else str(e)
                raise Exception(f"Gemini API error: {error_detail}")
            except Exception as e:
                raise e

    async def stream(self, prompt: str, params: Optional[Dict[str, Any]] = None):
        """Gemini streaming generation - yields text chunks."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": params.get("temperature", 0.7) if params else 0.7,
                "maxOutputTokens": params.get("max_tokens", 1024) if params else 1024,
            },
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=30.0) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    import json

                    try:
                        data = json.loads(line)
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                yield parts[0].get("text", "")
                    except json.JSONDecodeError:
                        continue
