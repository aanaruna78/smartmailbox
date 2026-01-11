import sys
import os
import json

# Adjust path to find app
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.services.smtp import SMTPService
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db, Base
from app.models.email import Email, EmailState
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.attachment import Attachment
from app.models.draft import Draft
from app.models.thread import Thread
from app.models.tag import Tag
from app.core.config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

# Setup SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Mock SMTP
def mock_send_email(self, to_email, subject, body_html=None, body_text=None):
    print(f"MOCK SMTP SENT: To={to_email}, Subject={subject}")
    return True

SMTPService.send_email = mock_send_email

client = TestClient(app)

# Mock User
from app.routes.auth import get_current_active_user
def mock_get_current_active_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    db.close()
    return user

app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

def seed_data():
    db = TestingSessionLocal()
    # Create User
    if not db.query(User).filter_by(email="test@example.com").first():
        user = User(email="test@example.com", is_active=True, role="admin", hashed_password="fake")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create Mailbox
        mailbox = Mailbox(user_id=user.id, email_address="test@example.com")
        db.add(mailbox)
        db.commit()
        db.refresh(mailbox)
        
        # Create Email
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

def verify_send():
    seed_data()
    print("Verifying Send Pipeline...")
    
    # 1. List emails
    res = client.get("/emails/")
    if res.status_code != 200:
        print("Failed to list emails", res.text)
        return
    
    emails = res.json()['items']
    if not emails:
        print("No emails found to test reply.")
        return
    
    target_email = emails[0]
    target_id = target_email['id']
    print(f"Targeting Email ID: {target_id}")

    # 2. calling send endpoint
    payload = {
        "recipient": "recipient@example.com",
        "subject": "Re: Test Subject",
        "body_text": "This is a test reply via verification script."
    }
    
    print("Sending reply...")
    res = client.post(f"/emails/{target_id}/send", json=payload)
    
    if res.status_code == 200:
        print("[OK] Send Endpoint Success:", res.json())
        data = res.json()
        new_sent_id = data.get('sent_email_id')
        
        # 3. Verify Original Email State
        print("Verifying original email state...")
        res_detail = client.get(f"/emails/{target_id}")
        state = res_detail.json().get('state')
        if state == 'replied':
            print("[OK] Original Email State Updated to 'replied'")
        else:
            print(f"[FAIL] Original Email State Mismatch: {state}")

        # 4. Verify Sent Email Exists
        print(f"Verifying sent email ID {new_sent_id}...")
        res_sent = client.get(f"/emails/{new_sent_id}")
        if res_sent.status_code == 200:
            print("[OK] Sent Email Record Found")
            folder = res_sent.json().get('folder')
            if folder == 'Sent':
                print("[OK] Sent Email Folder is 'Sent'")
            else:
                 print(f"[FAIL] Sent Email Folder Mismatch: {folder}")
        else:
            print("[FAIL] Sent Email Record Not Found via API")

    else:
        print("[FAIL] Send Endpoint Failed:", res.text)

if __name__ == "__main__":
    verify_send()
