from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DraftBase(BaseModel):
    content: str
    is_accepted: bool = False

class DraftCreate(DraftBase):
    pass

class DraftUpdate(BaseModel):
    content: Optional[str] = None
    is_accepted: Optional[bool] = None

class DraftResponse(DraftBase):
    id: int
    email_id: int
    confidence_score: Optional[float] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
