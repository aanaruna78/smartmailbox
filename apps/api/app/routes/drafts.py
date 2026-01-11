from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.draft import Draft
from app.models.user import User
from app.schemas.draft import DraftUpdate, DraftResponse
from app.routes.auth import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.get("/{draft_id}", response_model=DraftResponse)
def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    draft = db.query(Draft).join(Draft.email).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    # Check ownership (Mailbox -> User)
    if draft.email.mailbox.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this draft")
        
    return draft

@router.put("/{draft_id}", response_model=DraftResponse)
def update_draft(
    draft_id: int,
    draft_in: DraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    draft = db.query(Draft).join(Draft.email).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.email.mailbox.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this draft")
        
    if draft_in.content is not None:
        draft.content = draft_in.content
    if draft_in.is_accepted is not None:
        draft.is_accepted = draft_in.is_accepted
        
    db.commit()
    db.refresh(draft)
    return draft
