from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.models.admin_settings import LLMSettings, PromptTemplate, PolicyRule

router = APIRouter()


# =========== LLM Settings ===========

class LLMSettingsResponse(BaseModel):
    id: int
    model_provider: str
    model_name: str
    temperature: str
    max_tokens: int
    api_base_url: Optional[str]
    is_active: bool


class LLMSettingsUpdate(BaseModel):
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    api_base_url: Optional[str] = None


@router.get("/llm", response_model=LLMSettingsResponse)
def get_llm_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current LLM settings."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db.query(LLMSettings).filter(LLMSettings.is_active == True).first()
    if not settings:
        # Create default settings
        settings = LLMSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.put("/llm", response_model=LLMSettingsResponse)
def update_llm_settings(
    update: LLMSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update LLM settings."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = db.query(LLMSettings).filter(LLMSettings.is_active == True).first()
    if not settings:
        settings = LLMSettings()
        db.add(settings)
    
    for key, value in update.dict(exclude_unset=True).items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings


# =========== Prompt Templates ===========

class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt_template: Optional[str]
    version: int
    is_active: bool


class PromptTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None


class PromptTemplateUpdate(BaseModel):
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None


@router.get("/prompts", response_model=List[PromptTemplateResponse])
def list_prompt_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all prompt templates."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return db.query(PromptTemplate).filter(PromptTemplate.is_active == True).all()


@router.post("/prompts", response_model=PromptTemplateResponse)
def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new prompt template."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = db.query(PromptTemplate).filter(PromptTemplate.name == template.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    new_template = PromptTemplate(**template.dict())
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template


@router.put("/prompts/{template_id}", response_model=PromptTemplateResponse)
def update_prompt_template(
    template_id: int,
    update: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update prompt template (increments version)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in update.dict(exclude_unset=True).items():
        setattr(template, key, value)
    
    template.version += 1
    db.commit()
    db.refresh(template)
    return template


# =========== Policy Rules ===========

class PolicyRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    rule_type: str
    config: dict
    severity: str
    is_active: bool


class PolicyRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str  # block_phrase, require_phrase, length_limit, tone_check
    config: dict
    severity: str = "warning"


@router.get("/policies", response_model=List[PolicyRuleResponse])
def list_policy_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all policy rules."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return db.query(PolicyRule).filter(PolicyRule.is_active == True).all()


@router.post("/policies", response_model=PolicyRuleResponse)
def create_policy_rule(
    rule: PolicyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new policy rule."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_rule = PolicyRule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.delete("/policies/{rule_id}")
def delete_policy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete policy rule."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = False
    db.commit()
    return {"message": "Rule deleted"}
