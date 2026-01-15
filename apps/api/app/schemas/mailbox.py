from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class MailboxBase(BaseModel):
    email_address: EmailStr
    provider: Optional[str] = "custom"
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    is_active: Optional[bool] = True

class MailboxCreate(MailboxBase):
    password: Optional[str] = None  # To be hashed

class MailboxUpdate(BaseModel):
    email_address: Optional[EmailStr] = None
    provider: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class MailboxResponse(MailboxBase):
    id: int
    smtp_port: Optional[int] = None
    last_synced_at: Optional[datetime] = None
    sync_status: Optional[str] = "idle"
    total_messages: int = 0
    unread_messages: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MailboxConnectionTest(BaseModel):
    provider: Optional[str] = "custom"
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    email_address: EmailStr
    password: str

