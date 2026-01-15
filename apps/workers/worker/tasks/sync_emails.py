import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.mailbox import Mailbox
from app.models.email import Email
from app.services.gmail_service import GmailService
from sqlalchemy import create_engine
import os

from concurrent.futures import ThreadPoolExecutor

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
    query = "label:INBOX"
    if mailbox.last_synced_at:
        # Fetch emails since last sync
        query += f" after:{int(mailbox.last_synced_at.timestamp())}"
    
    # Increase batch size to 100
    result = gmail.list_messages(max_results=100, q=query)
    messages = result.get('messages', [])
    
    if not messages:
        # Update overall stats even if no new messages
        stats = gmail.get_mailbox_stats()
        mailbox.total_messages = stats.get('total_messages', 0)
        mailbox.unread_messages = stats.get('unread_messages', 0)
        mailbox.last_synced_at = datetime.utcnow()
        db.commit()
        return

    # Check which messages are already in DB
    existing_ids = {id[0] for id in db.query(Email.message_id).filter(Email.mailbox_id == mailbox.id).all()}
    new_message_refs = [m for m in messages if m['id'] not in existing_ids]

    new_emails_count = 0
    if new_message_refs:
        # Fetch message details in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            full_messages = list(executor.map(lambda ref: gmail.get_message(ref['id']), new_message_refs))
            
        for full_msg in full_messages:
            if full_msg:
                # Basic date parsing
                try:
                    # In a real app we'd parse the 'Date' header properly
                    received_at = datetime.utcnow() 
                except:
                    received_at = datetime.utcnow()

                email = Email(
                    mailbox_id=mailbox.id,
                    message_id=full_msg['id'],
                    thread_id=full_msg['thread_id'],
                    sender=full_msg['sender'],
                    recipients=[full_msg['to']],
                    subject=full_msg['subject'],
                    body_text=full_msg['body'],
                    snippet=full_msg['snippet'],
                    # Map is_read from Gmail data
                    is_read='UNREAD' not in full_msg.get('labelIds', []),
                    received_at=received_at
                )
                db.add(email)
                new_emails_count += 1
    
    # Fetch overall stats
    stats = gmail.get_mailbox_stats()
    mailbox.total_messages = stats.get('total_messages', 0)
    mailbox.unread_messages = stats.get('unread_messages', 0)
    
    mailbox.last_synced_at = datetime.utcnow()
    db.commit()
    logger.info(f"Synced {new_emails_count} new emails for {mailbox.email_address}")
