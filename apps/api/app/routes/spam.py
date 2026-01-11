from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.models.email import Email
from app.models.spam_rule import SpamRule, RuleType, SpamLabel
from app.services.spam_filter_service import SpamFilterService

router = APIRouter()


class SpamAnalysisResponse(BaseModel):
    email_id: int
    score: int
    label: str
    reasons: List[str]
    is_spam: bool
    is_suspicious: bool


class QuarantinedEmailResponse(BaseModel):
    id: int
    subject: str
    sender: str
    received_at: Optional[str]


class RuleCreate(BaseModel):
    rule_type: str  # allow_sender, block_sender, allow_domain, block_domain, spam_keyword, safe_keyword
    value: str
    weight: int = 0
    mailbox_id: Optional[int] = None


class RuleResponse(BaseModel):
    id: int
    rule_type: str
    value: str
    weight: int
    mailbox_id: Optional[int]
    is_active: bool


@router.get("/analyze/{email_id}", response_model=SpamAnalysisResponse)
def analyze_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Full spam analysis with score, label, and detailed reasons.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    spam_service = SpamFilterService()
    result = spam_service.analyze_email(db, email)
    
    return SpamAnalysisResponse(**result)


@router.post("/scan/{mailbox_id}")
def scan_mailbox_for_spam(
    mailbox_id: int,
    auto_quarantine: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Scan all emails in a mailbox for spam.
    """
    spam_service = SpamFilterService()
    
    emails = db.query(Email).filter(
        Email.mailbox_id == mailbox_id,
        Email.folder == "INBOX"
    ).all()
    
    results = {"spam": [], "suspicious": [], "clean": 0}
    
    for email in emails:
        analysis = spam_service.analyze_email(db, email)
        
        if analysis["is_spam"]:
            results["spam"].append({"id": email.id, "score": analysis["score"]})
            if auto_quarantine:
                spam_service.quarantine_email(db, email, f"Score: {analysis['score']}")
        elif analysis["is_suspicious"]:
            results["suspicious"].append({"id": email.id, "score": analysis["score"]})
        else:
            results["clean"] += 1
    
    return {
        "scanned": len(emails),
        "spam_count": len(results["spam"]),
        "suspicious_count": len(results["suspicious"]),
        "clean_count": results["clean"],
        "spam": results["spam"],
        "suspicious": results["suspicious"],
        "auto_quarantine": auto_quarantine
    }


@router.get("/quarantine", response_model=List[QuarantinedEmailResponse])
def get_quarantine(
    mailbox_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all emails in quarantine."""
    spam_service = SpamFilterService()
    emails = spam_service.get_quarantined_emails(db, mailbox_id)
    
    return [
        QuarantinedEmailResponse(
            id=e.id,
            subject=e.subject or "",
            sender=e.sender or "",
            received_at=str(e.received_at) if e.received_at else None
        )
        for e in emails
    ]


@router.post("/quarantine/{email_id}")
def quarantine_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually quarantine an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    spam_service = SpamFilterService()
    spam_service.quarantine_email(db, email, "Manual quarantine")
    
    return {"message": "Email quarantined", "email_id": email_id}


@router.post("/release/{email_id}")
def release_from_quarantine(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Release an email from quarantine."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.folder != "QUARANTINE":
        raise HTTPException(status_code=400, detail="Email is not in quarantine")
    
    spam_service = SpamFilterService()
    spam_service.release_from_quarantine(db, email)
    
    return {"message": "Email released", "email_id": email_id}


# Rule management endpoints

@router.get("/rules", response_model=List[RuleResponse])
def list_rules(
    mailbox_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all spam rules."""
    spam_service = SpamFilterService()
    rules = spam_service.get_rules(db, mailbox_id)
    
    return [
        RuleResponse(
            id=r.id,
            rule_type=r.rule_type.value,
            value=r.value,
            weight=r.weight,
            mailbox_id=r.mailbox_id,
            is_active=r.is_active
        )
        for r in rules
    ]


@router.post("/rules", response_model=RuleResponse)
def add_rule(
    rule: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a new spam rule."""
    try:
        rule_type = RuleType(rule.rule_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid rule type: {rule.rule_type}")
    
    spam_service = SpamFilterService()
    new_rule = spam_service.add_rule(
        db=db,
        rule_type=rule_type,
        value=rule.value,
        mailbox_id=rule.mailbox_id,
        weight=rule.weight,
        user_id=current_user.id
    )
    
    return RuleResponse(
        id=new_rule.id,
        rule_type=new_rule.rule_type.value,
        value=new_rule.value,
        weight=new_rule.weight,
        mailbox_id=new_rule.mailbox_id,
        is_active=new_rule.is_active
    )


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a spam rule."""
    rule = db.query(SpamRule).filter(SpamRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Rule deleted", "rule_id": rule_id}
