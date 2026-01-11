from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum


class QuarantineAction(str, enum.Enum):
    QUARANTINE = "quarantine"
    RELEASE = "release"
    CONFIRM_SPAM = "confirm_spam"
    DELETE = "delete"


class QuarantineEntry(Base):
    """
    Tracks quarantined emails with full audit trail.
    """
    __tablename__ = "quarantine_entries"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    mailbox_id = Column(Integer, ForeignKey("mailboxes.id"), nullable=False, index=True)
    
    # Spam analysis at quarantine time
    spam_score = Column(Integer, nullable=False)
    spam_label = Column(String, nullable=False)  # clean, suspicious, spam
    reasons = Column(Text, nullable=True)  # JSON string of reasons
    
    # Status
    status = Column(String, default="quarantined")  # quarantined, released, confirmed_spam, deleted
    
    # Timestamps
    quarantined_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Who took action
    quarantined_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Resolution notes
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    email = relationship("Email", foreign_keys=[email_id])
    mailbox = relationship("Mailbox", foreign_keys=[mailbox_id])
    quarantine_user = relationship("User", foreign_keys=[quarantined_by])
    resolver_user = relationship("User", foreign_keys=[resolved_by])
