from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum

# We need to import Tag and email_tags to ensure they are registered OR just import the association table module if circular deps issues arise. 
# For now, let's defer import or assume they are available to Base metadata via import in main.
# To allow string based relationship "Tag" to work, we don't strictly need to import it here if we use string names 
# and ensure all models are imported in main.py before create_all.
from app.models.tag import Tag, email_tags # But explicit import is safer for code analysis
from app.models.draft import Draft

class EmailState(str, enum.Enum):
    OPEN = "open"
    REPLIED = "replied"
    CLOSED = "closed"

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_id = Column(Integer, ForeignKey("mailboxes.id"), nullable=False)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=True)
    
    message_id = Column(String, unique=True, index=True) # Message-ID header
    
    sender = Column(String, index=True)
    recipients = Column(JSON) # To, CC, BCC combined or separate structure
    subject = Column(String)
    
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    
    folder = Column(String, default="INBOX") # INBOX, SENT, TRASH, etc.
    is_read = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    state = Column(Enum(EmailState), default=EmailState.OPEN)
    
    received_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    mailbox = relationship("Mailbox", back_populates="emails")
    assigned_user = relationship("User")
    thread = relationship("Thread", back_populates="emails")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="email_tags", backref="emails")
    drafts = relationship("Draft", back_populates="email", cascade="all, delete-orphan")

