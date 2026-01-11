from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.job import Job
from app.models.mailbox import Mailbox
from app.models.email import Email
from app.models.attachment import Attachment
from app.integrations.imap.client import IMAPClient
from app.core.security.encryption import decrypt_password
from datetime import datetime
import logging
import os
import uuid

from app.models.draft import Draft
from app.services.llm import LLMService
from app.services.prompts.builder import PromptBuilder
import asyncio

logger = logging.getLogger(__name__)

STORAGE_DIR = "d:/projects/smartmailbox/storage/attachments" # Ideally from config

def process_sync_email_job(job_id: int):
    """
    Worker function to sync emails for a specific mailbox defined in the job payload.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.attempts += 1
        db.commit()

        mailbox_id = job.payload.get("mailbox_id")
        mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id).first()
        if not mailbox:
            raise Exception(f"Mailbox {mailbox_id} not found")

        # Decrypt password
        try:
            password = decrypt_password(mailbox.hashed_password)
        except Exception as e:
            raise Exception("Failed to decrypt mailbox password")

        # Connect IMAP
        with IMAPClient(mailbox.imap_host, mailbox.imap_port, mailbox.email_address, password) as client:
            # Sync Logic (simplified for now: fetch last 10)
            # In a real system, we would track the last synced UID per folder
            emails_data = client.fetch_emails("INBOX", limit=5)
            
            synced_count = 0
            for email_data in emails_data:
                # Check duplication by Message-ID
                existing = db.query(Email).filter(Email.message_id == email_data["message_id"]).first()
                if existing:
                    continue
                
                # Create Email
                new_email = Email(
                    mailbox_id=mailbox.id,
                    message_id=email_data["message_id"],
                    sender=email_data["sender"],
                    recipients=email_data["recipients"],
                    subject=email_data["subject"],
                    body_text=email_data["body_text"],
                    body_html=email_data["body_html"],
                    received_at=email_data["received_at"],
                    folder=email_data["folder"]
                )
                db.add(new_email)
                db.flush() # Get ID
                
                # Handle Attachments
                for att_data in email_data.get("attachments", []):
                    # Save file to disk
                    if not os.path.exists(STORAGE_DIR):
                        os.makedirs(STORAGE_DIR, exist_ok=True)
                    
                    unique_filename = f"{uuid.uuid4()}_{att_data['filename']}"
                    file_path = os.path.join(STORAGE_DIR, unique_filename)
                    
                    with open(file_path, "wb") as f:
                        f.write(att_data["content"])
                        
                    # Create Attachment Record
                    attachment = Attachment(
                        email_id=new_email.id,
                        filename=att_data["filename"],
                        content_type=att_data["content_type"],
                        size=att_data["size"],
                        storage_path=file_path
                    )
                    db.add(attachment)
                
                synced_count += 1
            
            job.result = {"synced_count": synced_count}
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            # Update Mailbox Status
            mailbox.sync_status = "idle"
            mailbox.last_synced_at = datetime.utcnow()
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            
            # Update Mailbox Status on Failure
            # We need to re-query mailbox if session was rolled back or if we want to be safe, 
            # but here our session is still open. 
            # Ideally we handle this carefully.
            try:
                if 'mailbox' in locals() and mailbox:
                    mailbox.sync_status = "failed"
            except:
                pass
                
            db.commit()
            db.commit()
    finally:
        db.close()

def generate_draft_job(job_id: int):
    """
    Worker function to generate a draft reply for an email using LLM.
    """
    db = SessionLocal()
    llm_service = LLMService()
    prompt_builder = PromptBuilder()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.attempts += 1
        db.commit()

        email_id = job.payload.get("email_id")
        instructions = job.payload.get("instructions", "")
        tone = job.payload.get("tone", "professional")
        
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise Exception(f"Email {email_id} not found")

        # Build Prompt
        prompt = prompt_builder.build_draft_prompt(
            target_email=email,
            instructions=instructions,
            tone=tone
        )

        # Call LLM (Async in Sync Context)
        try:
            # We use a new event loop or run_until_complete if we are in a thread
            # Since this is a worker likely running in a process/thread, asyncio.run should work 
            # if no other loop is running.
            response = asyncio.run(llm_service.generate_draft(prompt, timeout=60.0))
        except RuntimeError:
            # If a loop is already running (e.g. if worker is async), await directly? 
            # But this function is defined as sync `def`. 
            # Assuming standard sync worker (like generic rq/celery).
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(llm_service.generate_draft(prompt, timeout=60.0))
            loop.close()

        # Save Draft
        draft = Draft(
            email_id=email.id,
            content=response.text,
            confidence_score=0.9, # Placeholder or from response if available
            generation_metadata={
                "tokens": response.tokens_used,
                "latency_ms": response.latency_ms,
                "model": response.model_name
            },
            is_accepted=False
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        job.result = {
            "draft_id": draft.id, 
            "content_preview": response.text[:50] + "..."
        }
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

from app.services.smtp import SMTPService
from app.models.email import EmailState
from app.models.audit import AuditLog
import time

def process_send_email_job(job_id: int):
    """
    Worker function to send an email via SMTP with retry logic.
    """
    db = SessionLocal()
    smtp_service = SMTPService()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.attempts += 1
        db.commit()

        email_id = job.payload.get("email_id")
        recipient = job.payload.get("recipient")
        subject = job.payload.get("subject")
        body_html = job.payload.get("body_html")
        body_text = job.payload.get("body_text")
        user_id = job.payload.get("user_id")

        original_email = db.query(Email).filter(Email.id == email_id).first()
        if not original_email:
            raise Exception(f"Original email {email_id} not found")

        # Retry Logic
        max_retries = 3
        sent = False
        last_error = None
        
        for attempt in range(max_retries):
            sent = smtp_service.send_email(
                to_email=recipient,
                subject=subject,
                body_html=body_html,
                body_text=body_text
            )
            if sent:
                break
            else:
                last_error = "SMTP send failed"
                time.sleep(2 * (attempt + 1)) 

        if not sent:
            raise Exception(f"Failed to send email after {max_retries} attempts: {last_error}")

        # Update Original State
        original_email.state = EmailState.REPLIED
        db.add(original_email)

        # Create Sent Message Record
        sent_email = Email(
            mailbox_id=original_email.mailbox_id,
            thread_id=original_email.thread_id,
            message_id=f"sent-{datetime.utcnow().timestamp()}@smartmailbox.local",
            sender=original_email.mailbox.email_address, 
            recipients=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            folder="Sent",
            is_read=True,
            state=EmailState.CLOSED,
            received_at=datetime.utcnow()
        )
        db.add(sent_email)
        db.flush() 

        # Audit Log
        if user_id:
            mailbox_id = job.payload.get("mailbox_id")
            audit = AuditLog(
                user_id=user_id,
                event_type="email_sent",
                details={
                    "original_email_id": email_id,
                    "recipient": recipient,
                    "subject": subject,
                    "job_id": job_id,
                    "mailbox_id": mailbox_id
                }
            )
            db.add(audit)

        job.result = {"sent_email_id": sent_email.id}
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

def process_bulk_draft_orchestrator(job_id: int):
    """
    Worker function to orchestrate bulk draft generation.
    Spawns individual generate_draft_job for each email.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()

        email_ids = job.payload.get("email_ids", [])
        instructions = job.payload.get("instructions", "")
        tone = job.payload.get("tone", "professional")
        user_id = job.payload.get("user_id")

        spawned_job_ids = []

        for email_id in email_ids:
            # Create a sub-job for each email
            sub_job = Job(
                type="generate_draft",
                status="pending",
                payload={
                    "email_id": email_id,
                    "instructions": instructions,
                    "tone": tone,
                    "parent_job_id": job_id # Optional tracking
                },
                created_at=datetime.utcnow(),
                attempts=0
            )
            db.add(sub_job)
            db.commit()
            db.refresh(sub_job)
            spawned_job_ids.append(sub_job.id)

        job.result = {"spawned_jobs": spawned_job_ids, "count": len(spawned_job_ids)}
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def generate_embedding_job(job_id: int):
    """
    Worker function to generate embeddings for an email.
    Job payload: { email_id: int } or { thread_id: int }
    """
    from app.services.embedding_service import EmbeddingService
    from app.models.email import Email
    from app.models.thread import Thread
    
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        email_id = job.payload.get("email_id")
        thread_id = job.payload.get("thread_id")
        
        if email_id:
            email = db.query(Email).filter(Email.id == email_id).first()
            if email:
                embedding = embedding_service.embed_email(db, email)
                job.result = {"embedding_id": embedding.id, "dimension": embedding.dimension}
        
        elif thread_id:
            thread = db.query(Thread).filter(Thread.id == thread_id).first()
            if thread:
                embedding = embedding_service.embed_thread(db, thread)
                job.result = {"embedding_id": embedding.id, "dimension": embedding.dimension}
        
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Embedding generation failed for job {job_id}: {e}")
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
