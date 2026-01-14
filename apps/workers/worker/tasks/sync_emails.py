import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.mailbox import Mailbox
from app.models.email import Email
from app.services.gmail_service import GmailService
from sqlalchemy import create_engine
import os

logger = logging.getLogger(__name__)

def sync_all_mailboxes():
    db = SessionLocal()
    try:
        mailboxes = db.query(Mailbox).filter(Mailbox.is_active == True).all()
        for mailbox in mailboxes:
            sync_mailbox_delta(db, mailbox)
    finally:
        db.close()

def sync_mailbox_delta(db: Session, mailbox: Mailbox):
    # This requires user's google tokens. In a real app, we'd fetch them from the User model associated with mailbox.
    user = mailbox.user
    if not user or not user.google_access_token:
        return

    logger.info(f"Syncing delta for {mailbox.email_address}")
    
    gmail = GmailService(
        access_token=user.google_access_token,
        refresh_token=user.google_refresh_token
    )
    
    # Simple delta: items in INBOX
    # In a more advanced version, we'd use historyId
    query = "label:INBOX"
    if mailbox.last_synced_at:
        # Fetch emails since last sync
        query += f" after:{int(mailbox.last_synced_at.timestamp())}"
    
    messages = gmail.list_messages(max_results=50, q=query)
    
    new_emails_count = 0
    for msg_ref in messages:
        # Check if already in DB
        existing = db.query(Email).filter(Email.message_id == msg_ref['id']).first()
        if not existing:
            full_msg = gmail.get_message(msg_ref['id'])
            if full_msg:
                email = Email(
                    mailbox_id=mailbox.id,
                    message_id=full_msg['id'],
                    thread_id=full_msg['thread_id'],
                    sender=full_msg['sender'],
                    recipients=[full_msg['to']],
                    subject=full_msg['subject'],
                    body_text=full_msg['body'],
                    snippet=full_msg['snippet'],
                    # ... other fields
                    received_at=datetime.utcnow() # Should parse from headers in real app
                )
                db.add(email)
                new_emails_count += 1
    
    mailbox.last_synced_at = datetime.utcnow()
    db.commit()
    logger.info(f"Synced {new_emails_count} new emails for {mailbox.email_address}")
