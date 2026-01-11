from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.db.session import get_db
from app.models.email import Email
from app.models.tag import Tag
from app.schemas.email import EmailResponse, EmailDetailResponse, EmailListResponse, TagResponse
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.services.llm import LLMService
from app.services.prompts.builder import PromptBuilder
from app.integrations.llm.base import LLMResponse
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

llm_service = LLMService() # Should be dependency injected in real app or via factory
prompt_builder = PromptBuilder()

@router.get("/", response_model=EmailListResponse)
def list_emails(
    page: int = 1,
    size: int = 20,
    mailbox_id: Optional[int] = None,
    folder: Optional[str] = None,
    is_read: Optional[bool] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List emails with pagination, filtering, and search.
    """
    skip = (page - 1) * size
    
    # Base query: join mailbox to ensure user owns it
    # But since we have user_id on mailbox, we can just filter by mailbox ownership if needed.
    # For now, let's filter where email.mailbox.user_id == current_user.id
    query = db.query(Email).join(Email.mailbox).filter(Email.mailbox.has(user_id=current_user.id))
    
    if mailbox_id:
        query = query.filter(Email.mailbox_id == mailbox_id)
    
    if folder:
        query = query.filter(Email.folder == folder)
        
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
        
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Email.subject.ilike(search),
                Email.sender.ilike(search),
                Email.body_text.ilike(search)
            )
        )
        
    total = query.count()
    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(size).all()
    
    return {
        "items": emails,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/{email_id}", response_model=EmailDetailResponse)
def get_email_detail(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get full email detail including body.
    """
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    return email

# Request Models
class AssignRequest(BaseModel):
    user_id: int

class TagRequest(BaseModel):
    name: str
    color: Optional[str] = "#2196f3"

@router.post("/{email_id}/assign", status_code=status.HTTP_200_OK)
def assign_email(
    email_id: int,
    body: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    email.assigned_user_id = body.user_id
    db.commit()
    return {"message": "Email assigned"}

@router.post("/{email_id}/tags", response_model=TagResponse)
def add_tag(
    email_id: int,
    body: TagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    # Check if tag exists (global tags for simplicity, or we could make them user specific)
    tag = db.query(Tag).filter(Tag.name == body.name).first()
    if not tag:
        tag = Tag(name=body.name, color=body.color)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
    if tag not in email.tags:
        email.tags.append(tag)
        db.commit()
        
    return tag

@router.delete("/{email_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
def remove_tag(
    email_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag and tag in email.tags:
        email.tags.remove(tag)
        db.commit()
        
    return {"message": "Tag removed"}

class DraftRequest(BaseModel):
    instructions: str
    tone: str = "professional"

@router.post("/{email_id}/draft", response_model=LLMResponse)
async def generate_draft_reply(
    email_id: int,
    body: DraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    # Build Prompt
    prompt = prompt_builder.build_draft_prompt(
        target_email=email,
        instructions=body.instructions,
        tone=body.tone
    )
    
    # Generate calls are async
    try:
        # Mocking for now if service fails (or use the real service which defaults to Ollama)
        # Note: In a real production environment, you might want to use a background task if it takes > 30s,
        # but for an interactive draft agent, synchronous (await) is usually expected UI behavior (with spinners).
        response = await llm_service.generate_draft(prompt, timeout=30.0)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.models.job import Job
from typing import List
from app.schemas.draft import DraftResponse as API_DraftResponse

@router.post("/{email_id}/draft-job", response_model=dict)
def enqueue_draft_generation(
    email_id: int,
    body: DraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    # Create Job
    job = Job(
        type="generate_draft",
        payload={
            "email_id": email.id,
            "instructions": body.instructions,
            "tone": body.tone
        },
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {"job_id": job.id, "status": "queued"}

@router.get("/{email_id}/drafts", response_model=List[API_DraftResponse])
def list_email_drafts(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    return email.drafts

# Send Logic
class SendEmailRequest(BaseModel):
    recipient: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None

from app.services.smtp import SMTPService
from app.models.audit import AuditLog
from app.models.email import EmailState

smtp_service = SMTPService()

@router.post("/{email_id}/send", status_code=status.HTTP_200_OK)
def send_email(
    email_id: int,
    body: SendEmailRequest,
    draft_id: int = None,  # Optional draft ID for safety checks
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from app.services.safety_service import check_rate_limit, check_category_restriction
    from app.models.draft import Draft
    
    # 1. Fetch original email to ensure access and context
    original_email = db.query(Email).join(Email.mailbox).filter(
        Email.id == email_id,
        Email.mailbox.has(user_id=current_user.id)
    ).first()
    
    if not original_email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # 2. Safety Gate: Rate Limit Check
    rate_ok, rate_msg = check_rate_limit(db, original_email.mailbox_id)
    if not rate_ok:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=rate_msg)
    
    # 3. Safety Gate: Category Restriction Check
    is_blocked, category = check_category_restriction(db, original_email)
    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Cannot send: email tagged as '{category}' (restricted category)"
        )
    
    # 4. Safety Gate: Approval Check (if draft_id provided)
    if draft_id:
        draft = db.query(Draft).filter(Draft.id == draft_id).first()
        if draft and draft.approval_status == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Draft requires approval before sending"
            )
        if draft and draft.approval_status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Draft was rejected and cannot be sent"
            )
        
    # 5. Create Job
    job = Job(
        type="send_email",
        payload={
            "email_id": email_id,
            "recipient": body.recipient,
            "subject": body.subject,
            "body_html": body.body_html,
            "body_text": body.body_text,
            "user_id": current_user.id,
            "mailbox_id": original_email.mailbox_id  # For audit tracking
        },
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {"message": "Email sending queued", "job_id": job.id}

