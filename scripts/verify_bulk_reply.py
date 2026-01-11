
import sys
import os
import time
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')))

# Mock database url for testing if not set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# from app.db.base import Base # Possibly doesnt exist or in session.py
from app.db.session import SessionLocal, engine, Base
from app.models.email import Email, EmailState
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.job import Job
from app.models.attachment import Attachment
from app.models.draft import Draft
from app.models.thread import Thread
from app.models.tag import Tag
from app.services.workers import process_bulk_draft_orchestrator, generate_draft_job
from app.core.config import settings

from fastapi.testclient import TestClient
from app.main import app

# Setup DB
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
SessionLocal.configure(bind=engine)
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    # Create User
    user = User(email="test@example.com", hashed_password="pw", full_name="Test User", role="admin")
    db.add(user)
    db.flush()  # Flush to get user.id
    user_id = user.id
    
    # Create Mailbox
    mailbox = Mailbox(user_id=user_id, email_address="box@test.com", hashed_password="pw", imap_host="imap", imap_port=993, smtp_host="smtp", smtp_port=587)
    db.add(mailbox)
    db.flush()  # Flush to get mailbox.id
    mailbox_id = mailbox.id

    # Create Emails
    email_ids = []
    for i in range(3):
        email = Email(
            mailbox_id=mailbox_id,
            message_id=f"msg-{i}",
            sender="customer@example.com",
            subject=f"Inquiry {i}",
            body_text=f"Hello, I have a question about order #{100+i}. My name is John Doe.",
            received_at=None,
            folder="Inbox"
        )
        db.add(email)
        db.flush()
        email_ids.append(email.id)
    
    db.commit()
    db.close()
    return email_ids, user_id

def verify_bulk_reply():
    print("Verifying Bulk Reply Orchestration...")
    
    email_ids, user_id = seed_data()
    
    client = TestClient(app)
    
    # login
    # Simplified login bypass - we assume implementation works or we mock auth
    # But since we are calling worker directly, we just need API to create job.
    # We'll rely on the worker function test mostly.
    
    print("Testing Job Creation via API...")
    # Mock dependency overrides for auth if needed, or just insert job manually for unit test speed
    # Let's insert job manually to test just the worker logic first
    
    db = SessionLocal()
    job = Job(
        type="bulk_draft_orchestrator",
        status="pending",
        payload={
            "email_ids": email_ids,
            "instructions": "Reply politely",
            "tone": "friendly",
            "user_id": user_id
        },
        attempts=0
    )
    db.add(job)
    db.commit()
    
    print(f"[OK] Job created manually: {job.id}")
    
    print("Running Orchestrator Worker...")
    process_bulk_draft_orchestrator(job.id)
    
    db.refresh(job)
    print(f"Job Status: {job.status}")
    print(f"Job Result: {job.result}")
    
    if job.status == "completed" and job.result["count"] == 3:
        print("[OK] Orchestrator completed successfully")
    else:
        print("[FAIL] Orchestrator failed")
        return

    spawned_ids = job.result["spawned_jobs"]
    
    print("Verifying Sub-Jobs...")
    sub_jobs = db.query(Job).filter(Job.id.in_(spawned_ids)).all()
    if len(sub_jobs) == 3:
        print(f"[OK] 3 Sub-jobs found")
    else:
        print(f"[FAIL] Expected 3 sub-jobs, found {len(sub_jobs)}")
        
    print("Running One Sub-Job (Simulating LLM)...")
    # We won't call actual LLM, just check if function runs without crashing
    # We might need to mock LLM service
    import unittest.mock
    with unittest.mock.patch("app.services.llm.LLMService.generate_draft") as mock_llm:
        mock_llm.return_value.text = "Draft content"
        mock_llm.return_value.tokens_used = 10
        mock_llm.return_value.latency_ms = 100
        mock_llm.return_value.model_name = "test-model"
        
        # We need to make it async compatible for the worker
        async def async_mock(*args, **kwargs):
            return mock_llm.return_value
        
        mock_llm.side_effect = async_mock

        generate_draft_job(sub_jobs[0].id)
        
        db.refresh(sub_jobs[0])
        if sub_jobs[0].status == "completed":
             print(f"[OK] Sub-job {sub_jobs[0].id} completed")
             # Verify Draft
             draft = db.query(Draft).filter(Draft.email_id == sub_jobs[0].payload["email_id"]).first()
             if draft:
                 print(f"[OK] Draft created: {draft.id}")
             else:
                 print("[FAIL] Draft not created")
        else:
             print(f"[FAIL] Sub-job failed: {sub_jobs[0].error}")

if __name__ == "__main__":
    verify_bulk_reply()
