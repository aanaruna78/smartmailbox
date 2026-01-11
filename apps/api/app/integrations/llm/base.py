from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, Dict, Any

class LLMResponse(BaseModel):
    text: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    model_name: str

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> LLMResponse:
        pass
