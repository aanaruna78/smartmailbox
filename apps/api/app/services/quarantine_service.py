import json
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.email import Email
from app.models.quarantine import QuarantineEntry
from app.models.tag import Tag
from app.models.spam_rule import RuleType
from app.services.spam_filter_service import SpamFilterService

logger = logging.getLogger(__name__)


class QuarantineService:
    """
    Service for managing quarantine workflow with full audit trail.
    """
    
    def __init__(self):
        self.spam_service = SpamFilterService()
    
    def quarantine_email(
        self, 
        db: Session, 
        email: Email,
        user_id: Optional[int] = None,
        auto: bool = True
    ) -> QuarantineEntry:
        """
        Move email to quarantine with full tracking.
        """
        # Get spam analysis
        analysis = self.spam_service.analyze_email(db, email)
        
        # Create quarantine entry
        entry = QuarantineEntry(
            email_id=email.id,
            mailbox_id=email.mailbox_id,
            spam_score=analysis["score"],
            spam_label=analysis["label"],
            reasons=json.dumps(analysis["reasons"]),
            status="quarantined",
            quarantined_by=user_id
        )
        db.add(entry)
        
        # Update email folder
        email.folder = "QUARANTINE"
        email.is_flagged = True
        
        # Add spam tag
        spam_tag = db.query(Tag).filter(Tag.name == "spam").first()
        if not spam_tag:
            spam_tag = Tag(name="spam", color="#ff4444")
            db.add(spam_tag)
            db.flush()
        
        if spam_tag not in email.tags:
            email.tags.append(spam_tag)
        
        db.commit()
        
        logger.info(f"Quarantined email {email.id} (score: {analysis['score']}, auto: {auto})")
        return entry
    
    def release_email(
        self, 
        db: Session, 
        entry_id: int,
        user_id: int,
        notes: str = "",
        add_to_allowlist: bool = False
    ) -> QuarantineEntry:
        """
        Release email from quarantine back to inbox.
        Optionally add sender to allowlist.
        """
        entry = db.query(QuarantineEntry).filter(QuarantineEntry.id == entry_id).first()
        if not entry:
            raise ValueError("Quarantine entry not found")
        
        if entry.status != "quarantined":
            raise ValueError("Entry already resolved")
        
        email = db.query(Email).filter(Email.id == entry.email_id).first()
        if not email:
            raise ValueError("Email not found")
        
        # Update entry
        entry.status = "released"
        entry.resolved_at = datetime.utcnow()
        entry.resolved_by = user_id
        entry.resolution_notes = notes
        
        # Update email
        email.folder = "INBOX"
        email.is_flagged = False
        
        # Remove spam tag
        spam_tag = db.query(Tag).filter(Tag.name == "spam").first()
        if spam_tag and spam_tag in email.tags:
            email.tags.remove(spam_tag)
        
        # Add sender to allowlist if requested
        if add_to_allowlist and email.sender:
            self.spam_service.add_rule(
                db=db,
                rule_type=RuleType.ALLOW_SENDER,
                value=email.sender,
                mailbox_id=email.mailbox_id,
                user_id=user_id
            )
        
        db.commit()
        
        logger.info(f"Released email {email.id} from quarantine (by user {user_id})")
        return entry
    
    def confirm_spam(
        self, 
        db: Session, 
        entry_id: int,
        user_id: int,
        notes: str = "",
        add_to_blocklist: bool = False
    ) -> QuarantineEntry:
        """
        Confirm email is spam. Keep in quarantine and optionally add sender to blocklist.
        """
        entry = db.query(QuarantineEntry).filter(QuarantineEntry.id == entry_id).first()
        if not entry:
            raise ValueError("Quarantine entry not found")
        
        email = db.query(Email).filter(Email.id == entry.email_id).first()
        
        # Update entry
        entry.status = "confirmed_spam"
        entry.resolved_at = datetime.utcnow()
        entry.resolved_by = user_id
        entry.resolution_notes = notes
        
        # Add sender to blocklist if requested
        if add_to_blocklist and email and email.sender:
            self.spam_service.add_rule(
                db=db,
                rule_type=RuleType.BLOCK_SENDER,
                value=email.sender,
                mailbox_id=email.mailbox_id,
                user_id=user_id
            )
        
        db.commit()
        
        logger.info(f"Confirmed spam for email {entry.email_id} (by user {user_id})")
        return entry
    
    def delete_quarantined(
        self, 
        db: Session, 
        entry_id: int,
        user_id: int
    ) -> None:
        """
        Permanently delete quarantined email.
        """
        entry = db.query(QuarantineEntry).filter(QuarantineEntry.id == entry_id).first()
        if not entry:
            raise ValueError("Quarantine entry not found")
        
        email = db.query(Email).filter(Email.id == entry.email_id).first()
        
        # Update entry status
        entry.status = "deleted"
        entry.resolved_at = datetime.utcnow()
        entry.resolved_by = user_id
        
        # Delete email
        if email:
            db.delete(email)
        
        db.commit()
        
        logger.info(f"Deleted quarantined email {entry.email_id} (by user {user_id})")
    
    def get_quarantine_queue(
        self, 
        db: Session, 
        mailbox_id: Optional[int] = None,
        status: str = "quarantined"
    ) -> List[QuarantineEntry]:
        """
        Get quarantine queue.
        """
        query = db.query(QuarantineEntry).filter(QuarantineEntry.status == status)
        if mailbox_id:
            query = query.filter(QuarantineEntry.mailbox_id == mailbox_id)
        return query.order_by(QuarantineEntry.quarantined_at.desc()).all()
    
    def get_statistics(
        self, 
        db: Session, 
        mailbox_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        Get quarantine statistics.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(QuarantineEntry).filter(QuarantineEntry.quarantined_at >= since)
        if mailbox_id:
            query = query.filter(QuarantineEntry.mailbox_id == mailbox_id)
        
        entries = query.all()
        
        stats = {
            "total": len(entries),
            "pending": 0,
            "released": 0,
            "confirmed_spam": 0,
            "deleted": 0,
            "avg_score": 0,
            "by_label": {"clean": 0, "suspicious": 0, "spam": 0}
        }
        
        total_score = 0
        for entry in entries:
            if entry.status == "quarantined":
                stats["pending"] += 1
            elif entry.status == "released":
                stats["released"] += 1
            elif entry.status == "confirmed_spam":
                stats["confirmed_spam"] += 1
            elif entry.status == "deleted":
                stats["deleted"] += 1
            
            total_score += entry.spam_score
            if entry.spam_label in stats["by_label"]:
                stats["by_label"][entry.spam_label] += 1
        
        if entries:
            stats["avg_score"] = round(total_score / len(entries), 1)
        
        return stats
