from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from datetime import datetime
from app.db.session import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True) # sync_email, send_email, etc.
    status = Column(String, default="pending", index=True) # pending, processing, completed, failed
    
    payload = Column(JSON)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    attempts = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
