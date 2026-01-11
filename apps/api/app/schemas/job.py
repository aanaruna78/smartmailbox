from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class JobBase(BaseModel):
    type: str
    status: str
    error: Optional[str] = None

class JobCreate(JobBase):
    payload: Optional[Dict[str, Any]] = None

class JobResponse(JobBase):
    id: int
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int
    next_retry_at: Optional[datetime] = None

    class Config:
        from_attributes = True
