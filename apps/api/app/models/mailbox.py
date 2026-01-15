from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),  nullable=False)
    email_address = Column(String, unique=True, index=True, nullable=False)
    provider = Column(String, nullable=True) # gmail, outlook, custom
    
    # Credentials (should be encrypted in real app)
    imap_host = Column(String, nullable=True)
    imap_port = Column(Integer, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    hashed_password = Column(String, nullable=True) # or encrypted_password
    
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String, default="idle") # idle, syncing, failed
    send_rate_limit = Column(Integer, default=10)  # Max emails per minute
    
    # Overall metrics
    total_messages = Column(Integer, default=0)
    unread_messages = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="mailboxes")
    emails = relationship("Email", back_populates="mailbox")
    threads = relationship("Thread", back_populates="mailbox")
    threads = relationship("Thread", back_populates="mailbox")
