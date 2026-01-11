from sqlalchemy import Column, Integer, String, Text, Float, JSON, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), index=True)
    
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True) # Hypothetical score from LLM or heuristic
    generation_metadata = Column(JSON, nullable=True) # tokens, model name, etc.
    
    is_accepted = Column(Boolean, default=False)
    approval_status = Column(String, default="not_required")  # pending, approved, rejected, not_required
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    email = relationship("Email", back_populates="drafts")
