from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.routes.auth import get_current_active_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


class SLAMetricsResponse(BaseModel):
    period_days: int
    total_received: int
    backlog: int
    backlog_rate: float
    avg_response_time_hours: float
    responses_under_1h: int
    responses_under_4h: int
    responses_under_24h: int
    total_responses: int


class JobMetrics(BaseModel):
    total: int
    completed: int
    failed: int
    success_rate: float


class AIUsageMetricsResponse(BaseModel):
    period_days: int
    total_drafts_generated: int
    drafts_accepted: int
    acceptance_rate: float
    total_emails_sent: int
    edit_rate: float
    generation_jobs: JobMetrics


class HighlightsResponse(BaseModel):
    backlog_status: str
    response_time_status: str
    ai_adoption: str


class DashboardSummaryResponse(BaseModel):
    period_days: int
    sla: SLAMetricsResponse
    ai_usage: AIUsageMetricsResponse
    highlights: HighlightsResponse


@router.get("/sla", response_model=SLAMetricsResponse)
def get_sla_metrics(
    mailbox_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get SLA metrics: response times and backlog."""
    service = AnalyticsService()
    return service.get_sla_metrics(db, mailbox_id, days)


@router.get("/ai-usage", response_model=AIUsageMetricsResponse)
def get_ai_usage_metrics(
    mailbox_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get AI usage metrics: generated vs sent, edit rate."""
    service = AnalyticsService()
    return service.get_ai_usage_metrics(db, mailbox_id, days)


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    mailbox_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get combined analytics dashboard summary."""
    service = AnalyticsService()
    return service.get_dashboard_summary(db, mailbox_id, days)
