import sys
import os
import json
import time

# Adjust path to find app
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.main import app
from app.db.session import get_db, Base
from app.models.email import Email, EmailState
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.job import Job
from app.models.attachment import Attachment
from app.models.draft import Draft
from app.models.thread import Thread
from app.models.tag import Tag
from app.core.config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from fastapi.testclient import TestClient

# ----------------- Mocks & Overrides -----------------

# 1. SQLite In-Memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# 2. Override get_db for API
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 3. Override SessionLocal for Worker (to share same DB)
import app.services.workers as workers_module
workers_module.SessionLocal = TestingSessionLocal

# 4. Mock SMTPService in workers module
class MockSMTPService:
    def send_email(self, to_email, subject, body_html=None, body_text=None):
        print(f"WORKER MOCK SMTP SENT: To={to_email}, Subject={subject}")
        return True

workers_module.SMTPService = MockSMTPService

# 5. Mock User for API
from app.routes.auth import get_current_active_user
def mock_get_current_active_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    db.close()
    return user

app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

client = TestClient(app)

# ----------------- Test -----------------

def seed_data():
    db = TestingSessionLocal()
    if not db.query(User).filter_by(email="test@example.com").first():
        user = User(email="test@example.com", is_active=True, role="admin", hashed_password="fake")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        mailbox = Mailbox(user_id=user.id, email_address="test@example.com")
        db.add(mailbox)
        db.commit()
        db.refresh(mailbox)
        
        email = Email(
            mailbox_id=mailbox.id,
            message_id="msg123",
            sender="sender@example.com",
            subject="Test Subject",
            body_text="Hello",
            received_at=datetime.utcnow(),
            state=EmailState.OPEN
        )
        db.add(email)
        db.commit()
    db.close()

def verify_worker_flow():
    seed_data()
    print("Verifying Worker Queue Flow...")
    
    # 1. Get Target Email ID
    res = client.get("/emails/")
    if res.status_code != 200:
        print("[FAIL] Failed to list emails")
        return
    emails = res.json()['items']
    if not emails:
        print("[FAIL] No emails found")
        return
    target_id = emails[0]['id']

    # 2. Call Send Endpoint (Should Enqueue)
    payload = {
        "recipient": "worker_recipient@example.com",
        "subject": "Worker Test",
        "body_text": "Async Body"
    }
    
    print("Enqueueing job...")
    res = client.post(f"/emails/{target_id}/send", json=payload)
    
    if res.status_code != 200:
        print("[FAIL] Enqueue failed:", res.text)
        return
        
    print(f"[OK] Enqueued: {res.json()}")
    job_id = res.json().get("job_id")
    
    if not job_id:
        print("[FAIL] No job_id returned")
        return

    # 3. Verify Job in DB is Pending
    db = TestingSessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if job.status != "pending":
         print(f"[FAIL] Job status is {job.status}, expected pending")
    else:
         print("[OK] Job is pending in DB")
    db.close()

    # 4. Simulate Worker Processing
    print("Running worker function manually...")
    from app.services.workers import process_send_email_job
    process_send_email_job(job_id)

    # 5. Verify Results
    db = TestingSessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if job.status == "completed":
        print("[OK] Job completed successfully")
        sent_id = job.result.get("sent_email_id")
        print(f"   Sent Email ID: {sent_id}")
    else:
        print(f"[FAIL] Job status is {job.status}, error: {job.error}")

    # Verify Email State
    original = db.query(Email).filter(Email.id == target_id).first()
    if original.state == EmailState.REPLIED:
        print("[OK] Original Email State is REPLIED")
    else:
        print(f"[FAIL] Original Email State is {original.state}")
        
    db.close()

if __name__ == "__main__":
    verify_worker_flow()
