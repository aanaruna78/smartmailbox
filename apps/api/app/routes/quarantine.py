from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.models.quarantine import QuarantineEntry
from app.services.quarantine_service import QuarantineService

router = APIRouter()


class QuarantineEntryResponse(BaseModel):
    id: int
    email_id: int
    mailbox_id: int
    spam_score: int
    spam_label: str
    reasons: Optional[str]
    status: str
    quarantined_at: str
    resolved_at: Optional[str]


class QuarantineStatsResponse(BaseModel):
    total: int
    pending: int
    released: int
    confirmed_spam: int
    deleted: int
    avg_score: float
    by_label: dict


class ReleaseRequest(BaseModel):
    notes: str = ""
    add_to_allowlist: bool = False


class ConfirmSpamRequest(BaseModel):
    notes: str = ""
    add_to_blocklist: bool = False


@router.get("/queue", response_model=List[QuarantineEntryResponse])
def get_quarantine_queue(
    mailbox_id: Optional[int] = None,
    status: str = Query("quarantined"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get quarantine queue."""
    service = QuarantineService()
    entries = service.get_quarantine_queue(db, mailbox_id, status)
    
    return [
        QuarantineEntryResponse(
            id=e.id,
            email_id=e.email_id,
            mailbox_id=e.mailbox_id,
            spam_score=e.spam_score,
            spam_label=e.spam_label,
            reasons=e.reasons,
            status=e.status,
            quarantined_at=str(e.quarantined_at),
            resolved_at=str(e.resolved_at) if e.resolved_at else None
        )
        for e in entries
    ]


@router.get("/stats", response_model=QuarantineStatsResponse)
def get_quarantine_stats(
    mailbox_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get quarantine statistics."""
    service = QuarantineService()
    stats = service.get_statistics(db, mailbox_id, days)
    return QuarantineStatsResponse(**stats)


@router.post("/{entry_id}/release")
def release_from_quarantine(
    entry_id: int,
    request: ReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Release email from quarantine. Optionally add sender to allowlist."""
    service = QuarantineService()
    
    try:
        entry = service.release_email(
            db=db,
            entry_id=entry_id,
            user_id=current_user.id,
            notes=request.notes,
            add_to_allowlist=request.add_to_allowlist
        )
        return {
            "message": "Email released from quarantine",
            "entry_id": entry.id,
            "email_id": entry.email_id,
            "added_to_allowlist": request.add_to_allowlist
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/confirm-spam")
def confirm_spam(
    entry_id: int,
    request: ConfirmSpamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Confirm email is spam. Optionally add sender to blocklist."""
    service = QuarantineService()
    
    try:
        entry = service.confirm_spam(
            db=db,
            entry_id=entry_id,
            user_id=current_user.id,
            notes=request.notes,
            add_to_blocklist=request.add_to_blocklist
        )
        return {
            "message": "Confirmed as spam",
            "entry_id": entry.id,
            "email_id": entry.email_id,
            "added_to_blocklist": request.add_to_blocklist
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
def delete_quarantined(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Permanently delete quarantined email."""
    service = QuarantineService()
    
    try:
        service.delete_quarantined(db, entry_id, current_user.id)
        return {"message": "Email deleted", "entry_id": entry_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
