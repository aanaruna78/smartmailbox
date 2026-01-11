from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Embedding(Base):
    """
    Stores vector embeddings for emails and threads.
    The embedding vector is stored as a binary blob (pickled numpy array).
    For production, consider using pgvector extension for Postgres.
    """
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to email or thread
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=True, index=True)
    
    # Embedding metadata
    model_name = Column(String, nullable=False)  # e.g., "text-embedding-ada-002", "all-MiniLM-L6-v2"
    dimension = Column(Integer, nullable=False)  # e.g., 384, 1536
    
    # The embedding vector (stored as binary for SQLite/Postgres compatibility)
    # For production with similarity search, use pgvector
    vector = Column(LargeBinary, nullable=False)
    
    # Source text hash for cache invalidation
    content_hash = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", foreign_keys=[email_id])
    thread = relationship("Thread", foreign_keys=[thread_id])
