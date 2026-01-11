from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.draft import Draft
from app.routes.auth import get_current_active_user
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class DraftApprovalResponse(BaseModel):
    id: int
    email_id: int
    content: str
    confidence_score: Optional[float]
    approval_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/pending", response_model=List[DraftApprovalResponse])
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List drafts awaiting approval. Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    drafts = db.query(Draft).filter(Draft.approval_status == "pending").all()
    return drafts


@router.post("/{draft_id}/approve")
def approve_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve a draft for sending.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    
    if draft.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft is not pending approval")
    
    draft.approval_status = "approved"
    db.add(draft)
    db.commit()
    
    return {"message": "Draft approved", "draft_id": draft_id}


@router.post("/{draft_id}/reject")
def reject_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reject a draft.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    
    if draft.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft is not pending approval")
    
    draft.approval_status = "rejected"
    db.add(draft)
    db.commit()
    
    return {"message": "Draft rejected", "draft_id": draft_id}
