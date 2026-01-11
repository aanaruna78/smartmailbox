from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit import AuditLog

async def create_audit_log(
    db: Session,
    event_type: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None
):
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    db.add(log_entry)
    db.commit()
    return log_entry
