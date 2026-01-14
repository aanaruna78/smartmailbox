from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # 'admin', 'user'
    
    # Google OAuth tokens for Gmail API access
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    
    mailboxes = relationship("Mailbox", back_populates="user")

