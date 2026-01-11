import sys
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add the apps/api directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.db.session import SessionLocal
from app.models.job import Job
from app.models.mailbox import Mailbox
from app.models.email import Email
from app.services.workers import process_sync_email_job
from app.core.security.encryption import encrypt_password

load_dotenv()

def main():
    print("--- Verifying Sync Worker ---")
    
    db = SessionLocal()
    try:
        # 1. Setup a Test Mailbox (Reuse existing or create new)
        # Assuming you have one from previous manual tests or we create one here for safety
        email_address = os.getenv("TEST_EMAIL_ADDRESS")
        password = os.getenv("TEST_EMAIL_PASSWORD")
        host = os.getenv("TEST_IMAP_HOST", "imap.gmail.com")
        
        if not email_address or not password:
            print("Skipping: Please set TEST_EMAIL_ADDRESS and TEST_EMAIL_PASSWORD env vars")
            return

        print(f"Using mailbox: {email_address}")
        
        # Check if mailbox exists
        mailbox = db.query(Mailbox).filter(Mailbox.email_address == email_address).first()
        if not mailbox:
            print("Creating test mailbox in DB...")
            mailbox = Mailbox(
                email_address=email_address,
                hashed_password=encrypt_password(password), # Encrypt!
                provider="custom",
                imap_host=host,
                imap_port=993,
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                user_id=1 # Assuming admin user exists via seed
            )
            db.add(mailbox)
            db.commit()
            db.refresh(mailbox)
        
        # 2. Create a Sync Job
        print("Creating sync_email job...")
        job = Job(
            type="sync_email",
            status="pending",
            payload={"mailbox_id": mailbox.id},
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"Job ID: {job.id}")
        
        # 3. Trigger Worker Manually
        print("Triggering worker process...")
        process_sync_email_job(job.id)
        
        # 4. Verify Job Status
        db.refresh(job)
        print(f"Job Status: {job.status}")
        print(f"Job Result: {job.result}")
        print(f"Job Error: {job.error}")
        
        if job.status == "completed":
            count = job.result.get("synced_count", 0)
            print(f"Synced {count} emails.")
            
            # Verify Emails in DB
            emails = db.query(Email).filter(Email.mailbox_id == mailbox.id).order_by(Email.received_at.desc()).limit(count).all()
            for e in emails:
                print(f" - Saved Email: {e.subject} (Attachments: {len(e.attachments)})")
                for att in e.attachments:
                    print(f"   - Attachment: {att.filename} ({att.size} bytes) @ {att.storage_path}")
        else:
            print("❌ Job Failed!")

    finally:
        db.close()

if __name__ == "__main__":
    main()
