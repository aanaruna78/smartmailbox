import httpx
import time
from typing import Optional, Dict, Any
from app.integrations.llm.base import BaseLLMProvider, LLMResponse

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> LLMResponse:
        start_time = time.time()
        url = f"{self.base_url}/api/generate"
        
        # Merge default params with request params
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **(params or {})
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # 30 second timeout for the request itself, service layer can enforce overall timeout too
                response = await client.post(url, json=payload, timeout=60.0) 
                response.raise_for_status()
                data = response.json()
                
                text = data.get("response", "")
                tokens = data.get("eval_count", 0) 
                
                latency = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    text=text,
                    tokens_used=tokens,
                    latency_ms=latency,
                    model_name=self.model
                )
            except Exception as e:
                # In production, we might want to wrap this in a custom ProviderError
                raise e
