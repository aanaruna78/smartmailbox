from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.services.clustering_service import ClusteringService

router = APIRouter()


class SimilarEmailResponse(BaseModel):
    email_id: int
    subject: str
    sender: str
    similarity_score: float


class GroupSuggestionResponse(BaseModel):
    cluster_id: int
    topic: str
    email_count: int
    email_ids: List[int]
    sample_subjects: List[str]


@router.get("/similar/{email_id}", response_model=List[SimilarEmailResponse])
def find_similar_emails(
    email_id: int,
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find emails similar to the given email based on semantic similarity.
    """
    clustering_service = ClusteringService()
    similar = clustering_service.find_similar_emails(db, email_id, threshold, limit)
    
    return [
        SimilarEmailResponse(
            email_id=email.id,
            subject=email.subject or "",
            sender=email.sender or "",
            similarity_score=round(score, 3)
        )
        for email, score in similar
    ]


@router.get("/groups/suggest", response_model=List[GroupSuggestionResponse])
def suggest_groups(
    mailbox_id: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Suggest email groups based on topic clustering.
    Returns clusters of related emails with suggested topics.
    """
    clustering_service = ClusteringService()
    suggestions = clustering_service.suggest_groups(db, mailbox_id, limit)
    
    return [
        GroupSuggestionResponse(**suggestion)
        for suggestion in suggestions
    ]


@router.post("/groups/cluster")
def cluster_emails(
    email_ids: List[int],
    num_clusters: int = Query(5, ge=2, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cluster specific emails into topic groups.
    """
    if len(email_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 emails to cluster")
    
    clustering_service = ClusteringService()
    clusters = clustering_service.cluster_emails(db, email_ids, num_clusters)
    
    return {
        "num_clusters": len(clusters),
        "clusters": clusters
    }
