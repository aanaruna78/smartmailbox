from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.mailbox import Mailbox
from app.models.user import User
from app.schemas.mailbox import MailboxCreate, MailboxUpdate, MailboxResponse, MailboxConnectionTest
from app.core.security.deps import get_current_active_user
from app.services.audit import create_audit_log
from app.services.email import test_imap_connection, test_smtp_connection
from app.utils.error_mapping import map_connection_error
from app.core.security.encryption import encrypt_password, decrypt_password
from app.models.job import Job
from datetime import datetime

router = APIRouter()

@router.get("/mailboxes", response_model=List[MailboxResponse])
async def read_mailboxes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    mailboxes = db.query(Mailbox).filter(Mailbox.user_id == current_user.id).offset(skip).limit(limit).all()
    return mailboxes

@router.post("/mailboxes", response_model=MailboxResponse)
async def create_mailbox(
    request: Request,
    mailbox_in: MailboxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if email already exists
    existing_mailbox = db.query(Mailbox).filter(
        Mailbox.email_address == mailbox_in.email_address,
        Mailbox.user_id == current_user.id
    ).first()
    
    if existing_mailbox:
        raise HTTPException(status_code=400, detail="Mailbox with this email already exists")

    mailbox = Mailbox(
        user_id=current_user.id,
        email_address=mailbox_in.email_address,
        provider=mailbox_in.provider,
        imap_host=mailbox_in.imap_host,
        imap_port=mailbox_in.imap_port,
        smtp_host=mailbox_in.smtp_host,
        smtp_port=mailbox_in.smtp_port,
        hashed_password=encrypt_password(mailbox_in.password) if mailbox_in.password else None,
        is_active=mailbox_in.is_active
    )
    
    db.add(mailbox)
    db.commit()
    db.refresh(mailbox)
    
    await create_audit_log(db, "MAILBOX_CREATED", user_id=current_user.id, request=request, details={"mailbox_id": mailbox.id})
    return mailbox

@router.get("/mailboxes/{mailbox_id}", response_model=MailboxResponse)
async def read_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id, Mailbox.user_id == current_user.id).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    return mailbox

@router.put("/mailboxes/{mailbox_id}", response_model=MailboxResponse)
async def update_mailbox(
    request: Request,
    mailbox_id: int,
    mailbox_in: MailboxUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id, Mailbox.user_id == current_user.id).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
        
    update_data = mailbox_in.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = encrypt_password(update_data.pop("password"))
        
    for field, value in update_data.items():
        setattr(mailbox, field, value)
        
    db.commit()
    db.refresh(mailbox)
    
    await create_audit_log(db, "MAILBOX_UPDATED", user_id=current_user.id, request=request, details={"mailbox_id": mailbox.id})
    return mailbox

@router.delete("/mailboxes/{mailbox_id}")
async def delete_mailbox(
    request: Request,
    mailbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    mailbox = db.query(Mailbox).filter(Mailbox.id == mailbox_id, Mailbox.user_id == current_user.id).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
        
    if mailbox.provider == "gmail":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default Gmail mailbox cannot be deleted. It is managed via Google OAuth."
        )
        
    db.delete(mailbox)
    db.commit()
    
    await create_audit_log(db, "MAILBOX_DELETED", user_id=current_user.id, request=request, details={"mailbox_id": mailbox_id})
    return {"message": "Mailbox deleted successfully"}

@router.post("/mailboxes/test-connection")
async def test_connection(
    request: Request,
    connection_data: MailboxConnectionTest,
    current_user: User = Depends(get_current_active_user)
):
    results = {}
    
    # Test IMAP
    if connection_data.imap_host:
        imap_success, imap_message = test_imap_connection(
            host=connection_data.imap_host,
            port=connection_data.imap_port,
            username=connection_data.email_address,
            password=connection_data.password
        )
        results["imap"] = {"success": imap_success, "message": imap_message}
    
    # Test SMTP
    if connection_data.smtp_host:
        smtp_success, smtp_message = test_smtp_connection(
            host=connection_data.smtp_host,
            port=connection_data.smtp_port,
            username=connection_data.email_address,
            password=connection_data.password
        )
        results["smtp"] = {"success": smtp_success, "message": smtp_message}
        
    return results
