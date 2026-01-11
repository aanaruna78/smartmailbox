from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class LLMSettings(Base):
    """
    Global LLM configuration settings.
    """
    __tablename__ = "llm_settings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Model configuration
    model_provider = Column(String, default="ollama")  # ollama, openai, anthropic
    model_name = Column(String, default="llama3.2")
    temperature = Column(String, default="0.7")
    max_tokens = Column(Integer, default=2048)
    
    # API configuration
    api_base_url = Column(String, nullable=True)
    api_key_encrypted = Column(String, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptTemplate(Base):
    """
    Customizable prompt templates.
    """
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String, unique=True, nullable=False)  # draft_reply, summarize, classify
    description = Column(Text, nullable=True)
    
    # Template content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=True)
    
    # Version control
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyRule(Base):
    """
    Content policy rules for LLM output filtering.
    """
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Rule type
    rule_type = Column(String, nullable=False)  # block_phrase, require_phrase, length_limit, tone_check
    
    # Rule configuration (JSON for flexibility)
    config = Column(JSON, nullable=False)
    # Examples:
    # block_phrase: {"phrases": ["confidential", "secret"]}
    # require_phrase: {"phrases": ["Best regards"]}
    # length_limit: {"min": 50, "max": 500}
    # tone_check: {"blocked_tones": ["aggressive", "informal"]}
    
    # Severity: warning or block
    severity = Column(String, default="warning")  # warning, block
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
