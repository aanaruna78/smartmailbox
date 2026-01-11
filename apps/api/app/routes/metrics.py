from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.models.job import Job
from app.models.email import Email
from app.models.audit import AuditLog

router = APIRouter()


class SystemMetrics(BaseModel):
    jobs_total: int
    jobs_pending: int
    jobs_completed: int
    jobs_failed: int
    emails_total: int
    emails_unread: int
    users_total: int
    audit_events_24h: int


class PerformanceMetrics(BaseModel):
    avg_job_duration_seconds: float
    jobs_per_hour: float
    emails_per_hour: float


@router.get("/system", response_model=SystemMetrics)
def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current system metrics."""
    jobs_total = db.query(Job).count()
    jobs_pending = db.query(Job).filter(Job.status == "pending").count()
    jobs_completed = db.query(Job).filter(Job.status == "completed").count()
    jobs_failed = db.query(Job).filter(Job.status == "failed").count()
    
    emails_total = db.query(Email).count()
    emails_unread = db.query(Email).filter(Email.is_read == False).count()
    
    users_total = db.query(User).count()
    
    since_24h = datetime.utcnow() - timedelta(hours=24)
    audit_events_24h = db.query(AuditLog).filter(AuditLog.timestamp >= since_24h).count()
    
    return SystemMetrics(
        jobs_total=jobs_total,
        jobs_pending=jobs_pending,
        jobs_completed=jobs_completed,
        jobs_failed=jobs_failed,
        emails_total=emails_total,
        emails_unread=emails_unread,
        users_total=users_total,
        audit_events_24h=audit_events_24h
    )


@router.get("/performance", response_model=PerformanceMetrics)
def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get performance metrics."""
    since_24h = datetime.utcnow() - timedelta(hours=24)
    
    # Average job duration
    completed_jobs = db.query(Job).filter(
        Job.status == "completed",
        Job.started_at.isnot(None),
        Job.completed_at.isnot(None),
        Job.completed_at >= since_24h
    ).all()
    
    avg_duration = 0.0
    if completed_jobs:
        durations = [(j.completed_at - j.started_at).total_seconds() for j in completed_jobs]
        avg_duration = sum(durations) / len(durations)
    
    # Jobs per hour
    jobs_24h = db.query(Job).filter(Job.created_at >= since_24h).count()
    jobs_per_hour = jobs_24h / 24
    
    # Emails per hour
    emails_24h = db.query(Email).filter(Email.received_at >= since_24h).count()
    emails_per_hour = emails_24h / 24
    
    return PerformanceMetrics(
        avg_job_duration_seconds=round(avg_duration, 2),
        jobs_per_hour=round(jobs_per_hour, 2),
        emails_per_hour=round(emails_per_hour, 2)
    )


@router.get("/prometheus")
def prometheus_metrics(db: Session = Depends(get_db)):
    """Prometheus-compatible metrics endpoint."""
    jobs_total = db.query(Job).count()
    jobs_pending = db.query(Job).filter(Job.status == "pending").count()
    jobs_completed = db.query(Job).filter(Job.status == "completed").count()
    jobs_failed = db.query(Job).filter(Job.status == "failed").count()
    emails_total = db.query(Email).count()
    
    metrics = f"""# HELP smartmailbox_jobs_total Total number of jobs
# TYPE smartmailbox_jobs_total counter
smartmailbox_jobs_total {jobs_total}

# HELP smartmailbox_jobs_pending Number of pending jobs
# TYPE smartmailbox_jobs_pending gauge
smartmailbox_jobs_pending {jobs_pending}

# HELP smartmailbox_jobs_completed Number of completed jobs
# TYPE smartmailbox_jobs_completed counter
smartmailbox_jobs_completed {jobs_completed}

# HELP smartmailbox_jobs_failed Number of failed jobs
# TYPE smartmailbox_jobs_failed counter
smartmailbox_jobs_failed {jobs_failed}

# HELP smartmailbox_emails_total Total number of emails
# TYPE smartmailbox_emails_total counter
smartmailbox_emails_total {emails_total}
"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=metrics, media_type="text/plain")
