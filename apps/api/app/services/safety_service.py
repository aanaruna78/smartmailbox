from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.email import Email
from app.models.mailbox import Mailbox
from app.models.draft import Draft
from app.models.audit import AuditLog

# Restricted categories - emails with these tags cannot be auto-sent
RESTRICTED_CATEGORIES = ["legal", "financial", "hr", "compliance", "confidential"]

# Confidence threshold - drafts below this require approval
CONFIDENCE_THRESHOLD = 0.7


def check_rate_limit(db: Session, mailbox_id: int) -> tuple[bool, str]:
    """
    Check if the mailbox is within its rate limit.
    Returns (is_allowed, message).
    """
    from sqlalchemy import func
    
    mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id).first()
    if not mailbox:
        return False, "Mailbox not found"
    
    # Count emails sent in the last minute
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    # Use func.json_extract for SQLite, or cast for Postgres
    sent_count = db.query(AuditLog).filter(
        AuditLog.event_type == "email_sent",
        AuditLog.timestamp >= one_minute_ago,
        func.json_extract(AuditLog.details, '$.mailbox_id') == mailbox_id
    ).count()
    
    if sent_count >= mailbox.send_rate_limit:
        return False, f"Rate limit exceeded: {sent_count}/{mailbox.send_rate_limit} emails/min"
    
    return True, f"Rate OK: {sent_count}/{mailbox.send_rate_limit}"


def check_category_restriction(db: Session, email: Email) -> tuple[bool, str | None]:
    """
    Check if email has a restricted category tag.
    Returns (is_blocked, category_name).
    """
    for tag in email.tags:
        if tag.name.lower() in RESTRICTED_CATEGORIES:
            return True, tag.name
    return False, None


def requires_approval(draft: Draft) -> tuple[bool, str]:
    """
    Check if draft requires manual approval based on confidence score.
    Returns (requires_approval, reason).
    """
    if draft.confidence_score is None:
        return False, "No confidence score"
    
    if draft.confidence_score < CONFIDENCE_THRESHOLD:
        return True, f"Low confidence ({draft.confidence_score:.2f} < {CONFIDENCE_THRESHOLD})"
    
    return False, "Confidence OK"


def set_approval_status(db: Session, draft: Draft) -> str:
    """
    Evaluate and set the approval status for a draft.
    Returns the new status.
    """
    needs_approval, reason = requires_approval(draft)
    
    if needs_approval:
        draft.approval_status = "pending"
    else:
        draft.approval_status = "not_required"
    
    db.add(draft)
    db.commit()
    
    return draft.approval_status


def can_send(db: Session, email: Email, draft: Draft) -> tuple[bool, list[str]]:
    """
    Comprehensive check if an email can be sent.
    Returns (can_send, list of blocking reasons).
    """
    blockers = []
    
    # Rate limit check
    rate_ok, rate_msg = check_rate_limit(db, email.mailbox_id)
    if not rate_ok:
        blockers.append(rate_msg)
    
    # Category restriction check
    is_blocked, category = check_category_restriction(db, email)
    if is_blocked:
        blockers.append(f"Blocked category: {category}")
    
    # Approval check
    if draft.approval_status == "pending":
        blockers.append("Awaiting approval")
    elif draft.approval_status == "rejected":
        blockers.append("Draft was rejected")
    
    return len(blockers) == 0, blockers
