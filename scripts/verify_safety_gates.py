
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')))

# Set minimal environment
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///./test_safety.db"
if not os.getenv("REDIS_URL"):
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test_secret"
if not os.getenv("ENCRYPTION_KEY"):
    os.environ["ENCRYPTION_KEY"] = "test_encryption_key_must_be_32_bytes_long_exact!"

from app.db.session import SessionLocal, engine, Base
from app.models.email import Email, EmailState
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.job import Job
from app.models.draft import Draft
from app.models.tag import Tag
from app.models.audit import AuditLog
from app.models.attachment import Attachment
from app.models.thread import Thread
from app.services.safety_service import check_rate_limit, check_category_restriction, requires_approval
from datetime import datetime, timedelta

# Setup DB
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    
    # Create User
    user = User(email="test@example.com", hashed_password="pw", full_name="Test User", role="admin")
    db.add(user)
    db.flush()
    user_id = user.id
    
    # Create Mailbox with rate limit of 3 per minute
    mailbox = Mailbox(user_id=user_id, email_address="box@test.com", hashed_password="pw", 
                      imap_host="imap", imap_port=993, smtp_host="smtp", smtp_port=587,
                      send_rate_limit=3)
    db.add(mailbox)
    db.flush()
    mailbox_id = mailbox.id
    
    # Create Email
    email = Email(
        mailbox_id=mailbox_id,
        message_id="msg-1",
        sender="customer@example.com",
        subject="Test",
        body_text="Test body",
        received_at=None,
        folder="Inbox"
    )
    db.add(email)
    db.flush()
    email_id = email.id
    
    # Create Legal Tag
    legal_tag = Tag(name="legal", color="#ff0000")
    db.add(legal_tag)
    db.flush()
    
    # Create Tagged Email
    legal_email = Email(
        mailbox_id=mailbox_id,
        message_id="msg-legal",
        sender="legal@example.com",
        subject="Legal Matter",
        body_text="Legal content",
        received_at=None,
        folder="Inbox"
    )
    db.add(legal_email)
    db.flush()
    legal_email.tags.append(legal_tag)
    legal_email_id = legal_email.id
    
    # Create Draft with low confidence
    low_confidence_draft = Draft(
        email_id=email_id,
        content="This is a draft",
        confidence_score=0.5,
        approval_status="not_required"
    )
    db.add(low_confidence_draft)
    db.flush()
    draft_id = low_confidence_draft.id
    
    db.commit()
    db.close()
    return user_id, mailbox_id, email_id, legal_email_id, draft_id

def test_rate_limit(mailbox_id):
    print("\n=== Testing Rate Limiting ===")
    db = SessionLocal()
    
    # First check - should be allowed
    ok, msg = check_rate_limit(db, mailbox_id)
    print(f"Check 1: {msg} -> {'[OK]' if ok else '[BLOCKED]'}")
    
    # Simulate sending 3 emails
    for i in range(3):
        audit = AuditLog(
            user_id=1,
            event_type="email_sent",
            details={"mailbox_id": mailbox_id}
        )
        db.add(audit)
    db.commit()
    
    # Check again - should be blocked
    ok, msg = check_rate_limit(db, mailbox_id)
    print(f"Check after 3 sends: {msg} -> {'[OK]' if ok else '[BLOCKED]'}")
    
    if not ok:
        print("[OK] Rate limit correctly enforced")
    else:
        print("[FAIL] Rate limit not enforced")
    
    db.close()

def test_category_blocking(legal_email_id, normal_email_id):
    print("\n=== Testing Category Blocking ===")
    db = SessionLocal()
    
    # Check normal email
    normal_email = db.query(Email).filter(Email.id == normal_email_id).first()
    is_blocked, category = check_category_restriction(db, normal_email)
    print(f"Normal email: Blocked={is_blocked}, Category={category} -> {'[BLOCKED]' if is_blocked else '[OK]'}")
    
    # Check legal email
    legal_email = db.query(Email).filter(Email.id == legal_email_id).first()
    is_blocked, category = check_category_restriction(db, legal_email)
    print(f"Legal email: Blocked={is_blocked}, Category={category} -> {'[BLOCKED]' if is_blocked else '[OK]'}")
    
    if is_blocked:
        print("[OK] Category blocking correctly enforced")
    else:
        print("[FAIL] Category blocking not enforced")
    
    db.close()

def test_approval_workflow(draft_id):
    print("\n=== Testing Approval Workflow ===")
    db = SessionLocal()
    
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    needs_approval, reason = requires_approval(draft)
    print(f"Draft (confidence {draft.confidence_score}): {reason}")
    
    if needs_approval:
        print("[OK] Low confidence draft correctly flagged for approval")
    else:
        print("[FAIL] Low confidence draft not flagged")
    
    # Test high confidence
    draft.confidence_score = 0.9
    needs_approval, reason = requires_approval(draft)
    print(f"Draft (confidence {draft.confidence_score}): {reason}")
    
    if not needs_approval:
        print("[OK] High confidence draft correctly allowed")
    else:
        print("[FAIL] High confidence draft incorrectly flagged")
    
    db.close()

def main():
    # Clean up old test DB
    try:
        if os.path.exists("./test_safety.db"):
            os.remove("./test_safety.db")
    except:
        pass  # Ignore if locked
    
    print("Verifying Safety Gates...")
    
    user_id, mailbox_id, email_id, legal_email_id, draft_id = seed_data()
    
    test_rate_limit(mailbox_id)
    test_category_blocking(legal_email_id, email_id)
    test_approval_workflow(draft_id)
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()
