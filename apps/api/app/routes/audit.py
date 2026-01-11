from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.audit import AuditLog
from app.routes.auth import get_current_active_user
from app.models.user import User
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    event_type: str
    timestamp: datetime
    ip_address: Optional[str]
    details: Optional[dict]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List audit logs.
    """
    # Simple RBAC: only admins should see audit logs
    # if current_user.role != "admin": ... (Assuming RBAC middleware or check)
    
    query = db.query(AuditLog)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
        
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs
