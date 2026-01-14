import httpx
import time
import os
from typing import Optional, Dict, Any
from app.integrations.llm.base import BaseLLMProvider, LLMResponse

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = "tinyllama"):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model

    async def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> LLMResponse:
        start_time = time.time()
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150,  # Limit output length for speed
                "temperature": 0.7
            },
            **(params or {})
        }
        
        import logging
        logger = logging.getLogger(__name__)
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to Ollama: {url} with model {self.model}")
                # 60 second timeout for the request itself
                response = await client.post(url, json=payload, timeout=60.0) 
                response.raise_for_status()
                data = response.json()
                
                text = data.get("response", "")
                tokens = data.get("eval_count", 0) 
                
                latency = (time.time() - start_time) * 1000
                logger.info(f"Ollama responded in {latency:.2f}ms (Status: {response.status_code})")
                
                return LLMResponse(
                    text=text,
                    tokens_used=tokens,
                    latency_ms=latency,
                    model_name=self.model
                )
            except Exception as e:
                logger.error(f"Ollama request failed: {str(e)}")
                raise e

    async def stream(self, prompt: str, params: Optional[Dict[str, Any]] = None):
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            **(params or {})
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    import json
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
