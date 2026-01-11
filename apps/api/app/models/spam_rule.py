from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum


class RuleType(str, enum.Enum):
    ALLOW_SENDER = "allow_sender"
    BLOCK_SENDER = "block_sender"
    ALLOW_DOMAIN = "allow_domain"
    BLOCK_DOMAIN = "block_domain"
    SPAM_KEYWORD = "spam_keyword"
    SAFE_KEYWORD = "safe_keyword"


class SpamRule(Base):
    """
    Configurable spam filter rules.
    """
    __tablename__ = "spam_rules"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_id = Column(Integer, ForeignKey("mailboxes.id"), nullable=True)  # null = global rule
    
    rule_type = Column(Enum(RuleType), nullable=False)
    value = Column(String, nullable=False)  # email, domain, or keyword
    weight = Column(Integer, default=0)  # Score adjustment (+/- points)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    mailbox = relationship("Mailbox", foreign_keys=[mailbox_id])
    creator = relationship("User", foreign_keys=[created_by])


class SpamLabel(str, enum.Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    SPAM = "spam"
