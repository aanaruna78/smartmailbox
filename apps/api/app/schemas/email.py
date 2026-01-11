from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class AttachmentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    
    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True

class EmailBase(BaseModel):
    id: int
    mailbox_id: int
    message_id: str
    sender: str
    recipients: Optional[Any] = None # Or JSON
    subject: Optional[str] = None
    folder: str
    state: str = "open"
    is_read: bool
    is_flagged: bool
    received_at: datetime
    created_at: datetime
    assigned_user_id: Optional[int] = None
    
class EmailResponse(EmailBase):
    attachments: List[AttachmentResponse] = []
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

class EmailDetailResponse(EmailResponse):
    body_text: Optional[str] = None
    body_html: Optional[str] = None

class EmailListResponse(BaseModel):
    items: List[EmailResponse]
    total: int
    page: int
    size: int
