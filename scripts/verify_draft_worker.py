import sys
import os
import datetime
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.db.session import SessionLocal, engine
from app.models.job import Job
from app.models.email import Email
from app.models.mailbox import Mailbox
from app.models.user import User
from app.models.draft import Draft
from app.services.workers import generate_draft_job

def verify_worker():
    print("--- Verifying Draft Worker ---")
    db = SessionLocal()
    
    try:
        # 1. Setup Data
        print("1. Setting up test data...")
        # Create Dummy User & Mailbox if not exists
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            user = User(email="test@example.com", hashed_password="pw", is_active=True)
            db.add(user)
            db.commit()
            
        mailbox = db.query(Mailbox).filter(Mailbox.email_address == "worker_test@example.com").first()
        if not mailbox:
            mailbox = Mailbox(
                user_id=user.id,
                email_address="worker_test@example.com",
                hashed_password=b"mock",
                imap_host="imap.test",
                imap_port=993,
                smtp_host="smtp.test",
                smtp_port=587
            )
            db.add(mailbox)
            db.commit()
            
        # Create Email
        email = Email(
            mailbox_id=mailbox.id,
            message_id="worker_test_msg_id",
            sender="boss@corp.com",
            subject="Urgent Task",
            body_text="Please do this ASAP.",
            received_at=datetime.datetime.utcnow(),
            folder="INBOX"
        )
        db.add(email)
        db.commit()
        db.refresh(email)
        print(f"   Created Email ID: {email.id}")

        # 2. Create Job
        print("\n2. Creating Job...")
        job = Job(
            type="generate_draft",
            payload={
                "email_id": email.id,
                "instructions": "Say I'm on it",
                "tone": "urgent"
            },
            status="pending",
            created_at=datetime.datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"   Created Job ID: {job.id}")

        # 3. Run Worker
        print("\n3. Running Worker Function...")
        
        # Patch LLMService in the worker module to avoid real calls
        from unittest.mock import patch, AsyncMock
        from app.integrations.llm.base import LLMResponse
        
        mock_response = LLMResponse(
            text="Draft: I'm on it. Best, Boss.",
            tokens_used=10,
            latency_ms=123.45,
            model_name="mock-model"
        )
        
        # We need to patch where it is used. It is used in app.services.workers.
        # But `generate_draft_job` instantiates `LLMService` inside the function locally: `llm_service = LLMService()`
        # So we patch `app.services.workers.LLMService` class.
        
        with patch("app.services.workers.LLMService") as MockServiceClass:
            # The instance returned by constructor
            mock_instance = MockServiceClass.return_value
            # The async method on that instance
            mock_instance.generate_draft = AsyncMock(return_value=mock_response)
            
            generate_draft_job(job.id)
        
        # 4. Check Result
        db.refresh(job)
        print(f"\n4. Job Status: {job.status}")
        
        if job.status == "completed":
            draft_id = job.result.get("draft_id")
            draft = db.query(Draft).filter(Draft.id == draft_id).first()
            if draft:
                print(f"✅ Success! Draft Created: {draft.id}")
                print(f"   Content: {draft.content[:50]}...")
            else:
                print("❌ Job completed but Draft not found.")
        else:
            print(f"❌ Job Failed: {job.error}")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
    finally:
        # Cleanup (Optional, skipped for now to allow inspection)
        db.close()

if __name__ == "__main__":
    verify_worker()
