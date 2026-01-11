from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.job import Job
from app.schemas.job import JobResponse
from app.routes.auth import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=list[JobResponse])
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List recent background jobs.
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve the status and result of a specific background job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job

from app.schemas.bulk_action import BulkDraftRequest
from datetime import datetime

@router.post("/bulk-draft", response_model=dict)
def create_bulk_draft_job(
    request: BulkDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enqueue a job to generate drafts for multiple emails.
    """
    job = Job(
        type="bulk_draft_orchestrator",
        status="pending",
        payload={
            "email_ids": request.email_ids,
            "instructions": request.instructions,
            "tone": request.tone,
            "user_id": current_user.id
        },
        created_at=datetime.utcnow(),
        attempts=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {"message": "Bulk draft generation queued", "job_id": job.id}
