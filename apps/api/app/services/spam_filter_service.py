import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.email import Email
from app.models.tag import Tag
from app.models.spam_rule import SpamRule, RuleType, SpamLabel

logger = logging.getLogger(__name__)

# Default spam keywords (used if no custom rules)
DEFAULT_SPAM_KEYWORDS = [
    "winner", "lottery", "prize", "click here", "act now", "limited time",
    "free money", "no obligation", "risk free", "urgent", "congratulations",
    "million dollars", "inheritance", "wire transfer", "viagra", "casino"
]


class SpamFilterService:
    """
    Enhanced spam filter with configurable rules, allow/block lists,
    and proper labeling (clean/suspicious/spam).
    """
    
    # Thresholds for labeling
    SPAM_THRESHOLD = 60
    SUSPICIOUS_THRESHOLD = 30
    
    def __init__(self):
        pass
    
    def get_rules(self, db: Session, mailbox_id: Optional[int] = None) -> List[SpamRule]:
        """
        Get all active rules for a mailbox (including global rules).
        """
        query = db.query(SpamRule).filter(SpamRule.is_active == True)
        
        if mailbox_id:
            query = query.filter(
                (SpamRule.mailbox_id == mailbox_id) | (SpamRule.mailbox_id.is_(None))
            )
        else:
            query = query.filter(SpamRule.mailbox_id.is_(None))
        
        return query.all()
    
    def calculate_spam_score(
        self, 
        db: Session, 
        email: Email, 
        mailbox_id: Optional[int] = None
    ) -> Tuple[int, List[str]]:
        """
        Calculate spam score (0-100) with detailed reasons.
        Returns (score, list of reasons).
        """
        score = 0
        reasons = []
        
        sender = (email.sender or "").lower()
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        subject = (email.subject or "").lower()
        body = (email.body_text or "").lower()
        full_text = subject + " " + body
        
        # Get configurable rules
        rules = self.get_rules(db, mailbox_id or email.mailbox_id)
        
        # Process rules
        for rule in rules:
            value = rule.value.lower()
            
            if rule.rule_type == RuleType.ALLOW_SENDER:
                if value == sender:
                    score -= 100  # Whitelisted sender
                    reasons.append(f"Whitelisted sender: {value}")
                    
            elif rule.rule_type == RuleType.BLOCK_SENDER:
                if value == sender:
                    score += 100  # Blacklisted sender
                    reasons.append(f"Blocked sender: {value}")
                    
            elif rule.rule_type == RuleType.ALLOW_DOMAIN:
                if sender_domain == value:
                    score -= 50
                    reasons.append(f"Whitelisted domain: {value}")
                    
            elif rule.rule_type == RuleType.BLOCK_DOMAIN:
                if sender_domain == value:
                    score += 80
                    reasons.append(f"Blocked domain: {value}")
                    
            elif rule.rule_type == RuleType.SPAM_KEYWORD:
                if value in full_text:
                    weight = rule.weight if rule.weight > 0 else 10
                    score += weight
                    reasons.append(f"Spam keyword: '{value}' (+{weight})")
                    
            elif rule.rule_type == RuleType.SAFE_KEYWORD:
                if value in full_text:
                    weight = rule.weight if rule.weight > 0 else 10
                    score -= weight
                    reasons.append(f"Safe keyword: '{value}' (-{weight})")
        
        # Default keyword checks if no custom spam keywords
        spam_keyword_rules = [r for r in rules if r.rule_type == RuleType.SPAM_KEYWORD]
        if not spam_keyword_rules:
            for keyword in DEFAULT_SPAM_KEYWORDS:
                if keyword in full_text:
                    score += 8
                    reasons.append(f"Default spam keyword: '{keyword}'")
        
        # Heuristic checks
        if email.subject and email.subject.isupper() and len(email.subject) > 10:
            score += 15
            reasons.append("ALL CAPS subject")
        
        link_count = body.count("http")
        if link_count > 5:
            score += min(20, link_count * 3)
            reasons.append(f"Excessive links: {link_count}")
        
        exclaim_count = full_text.count("!")
        if exclaim_count > 5:
            score += min(15, exclaim_count * 2)
            reasons.append(f"Excessive exclamation marks: {exclaim_count}")
        
        # Clamp score
        score = max(0, min(100, score))
        
        return score, reasons
    
    def get_label(self, score: int) -> SpamLabel:
        """
        Get spam label based on score.
        """
        if score >= self.SPAM_THRESHOLD:
            return SpamLabel.SPAM
        elif score >= self.SUSPICIOUS_THRESHOLD:
            return SpamLabel.SUSPICIOUS
        else:
            return SpamLabel.CLEAN
    
    def analyze_email(
        self, 
        db: Session, 
        email: Email
    ) -> dict:
        """
        Full spam analysis with score, label, and reasons.
        """
        score, reasons = self.calculate_spam_score(db, email)
        label = self.get_label(score)
        
        return {
            "email_id": email.id,
            "score": score,
            "label": label.value,
            "reasons": reasons,
            "is_spam": label == SpamLabel.SPAM,
            "is_suspicious": label == SpamLabel.SUSPICIOUS
        }
    
    def quarantine_email(self, db: Session, email: Email, reason: str = "Spam detected") -> None:
        """Move email to quarantine folder."""
        email.folder = "QUARANTINE"
        email.is_flagged = True
        
        spam_tag = db.query(Tag).filter(Tag.name == "spam").first()
        if not spam_tag:
            spam_tag = Tag(name="spam", color="#ff4444")
            db.add(spam_tag)
            db.flush()
        
        if spam_tag not in email.tags:
            email.tags.append(spam_tag)
        
        db.commit()
        logger.info(f"Quarantined email {email.id}: {reason}")
    
    def release_from_quarantine(self, db: Session, email: Email) -> None:
        """Release email from quarantine."""
        email.folder = "INBOX"
        email.is_flagged = False
        
        spam_tag = db.query(Tag).filter(Tag.name == "spam").first()
        if spam_tag and spam_tag in email.tags:
            email.tags.remove(spam_tag)
        
        db.commit()
        logger.info(f"Released email {email.id} from quarantine")
    
    def add_rule(
        self, 
        db: Session, 
        rule_type: RuleType, 
        value: str,
        mailbox_id: Optional[int] = None,
        weight: int = 0,
        user_id: Optional[int] = None
    ) -> SpamRule:
        """Add a new spam rule."""
        rule = SpamRule(
            mailbox_id=mailbox_id,
            rule_type=rule_type,
            value=value.lower(),
            weight=weight,
            created_by=user_id
        )
        db.add(rule)
        db.commit()
        logger.info(f"Added spam rule: {rule_type.value} = {value}")
        return rule
    
    def get_quarantined_emails(self, db: Session, mailbox_id: Optional[int] = None) -> List[Email]:
        """Get all quarantined emails."""
        query = db.query(Email).filter(Email.folder == "QUARANTINE")
        if mailbox_id:
            query = query.filter(Email.mailbox_id == mailbox_id)
        return query.all()
