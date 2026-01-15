import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.email import Email
from app.models.draft import Draft
from app.models.job import Job
from app.models.audit import AuditLog
from app.models.mailbox import Mailbox

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for calculating SLA and AI usage metrics.
    """
    
    def get_sla_metrics(
        self, 
        db: Session, 
        user_id: int,
        mailbox_id: Optional[int] = None,
        days: int = 7
    ) -> Dict:
        """
        Calculate SLA metrics: response times and backlog.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Base query for emails
        email_query = db.query(Email).filter(Email.received_at >= since)
        if mailbox_id:
            email_query = email_query.filter(Email.mailbox_id == mailbox_id)
        else:
            email_query = email_query.join(Mailbox).filter(Mailbox.user_id == user_id)
        
        # Total emails received
        total_received = email_query.count()
        
        # Unread/unanswered emails (backlog)
        backlog = email_query.filter(Email.is_read == False).count()
        
        # Calculate average response time from audit logs
        response_times = []
        sent_logs_query = db.query(AuditLog).filter(
            AuditLog.event_type == "email_sent",
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since
        )
        sent_logs = sent_logs_query.all()
        
        for log in sent_logs:
            if log.details and "reply_to_email_id" in log.details:
                original_email = db.query(Email).filter(
                    Email.id == log.details.get("reply_to_email_id")
                ).first()
                if original_email and original_email.received_at:
                    response_time = (log.timestamp - original_email.received_at).total_seconds() / 3600  # hours
                    response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Response time buckets
        under_1h = len([t for t in response_times if t < 1])
        under_4h = len([t for t in response_times if t < 4])
        under_24h = len([t for t in response_times if t < 24])
        
        # Overall stats from mailbox
        overall_total = db.query(func.sum(Mailbox.total_messages)).filter(Mailbox.user_id == user_id)
        overall_unread = db.query(func.sum(Mailbox.unread_messages)).filter(Mailbox.user_id == user_id)
        
        if mailbox_id:
            overall_total = overall_total.filter(Mailbox.id == mailbox_id)
            overall_unread = overall_unread.filter(Mailbox.id == mailbox_id)
            
        overall_total = overall_total.scalar() or 0
        overall_unread = overall_unread.scalar() or 0

        return {
            "period_days": days,
            "total_received": total_received,
            "backlog": backlog,
            "backlog_rate": round(backlog / total_received * 100, 1) if total_received > 0 else 0,
            "avg_response_time_hours": round(avg_response_time, 2),
            "responses_under_1h": under_1h,
            "responses_under_4h": under_4h,
            "responses_under_24h": under_24h,
            "total_responses": len(response_times),
            "overall_total": overall_total,
            "overall_unread": overall_unread
        }
    
    def get_ai_usage_metrics(
        self, 
        db: Session, 
        user_id: int,
        mailbox_id: Optional[int] = None,
        days: int = 7
    ) -> Dict:
        """
        Calculate AI usage metrics: generated vs sent, edit rate.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Count drafts generated
        draft_query = db.query(Draft).filter(Draft.created_at >= since)
        if mailbox_id:
            draft_query = draft_query.join(Email).filter(Email.mailbox_id == mailbox_id)
        else:
            draft_query = draft_query.join(Email).join(Mailbox).filter(Mailbox.user_id == user_id)
        
        total_generated = draft_query.count()
        accepted_drafts = draft_query.filter(Draft.is_accepted == True).count()
        
        # Count emails sent from drafts (via audit log)
        sent_query = db.query(AuditLog).filter(
            AuditLog.event_type == "email_sent",
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since
        )
        total_sent = sent_query.count()
        
        # Calculate acceptance rate
        acceptance_rate = (accepted_drafts / total_generated * 100) if total_generated > 0 else 0
        
        # Jobs metrics
        job_query = db.query(Job).filter(
            Job.type == "generate_draft",
            Job.created_at >= since
        )
        total_jobs = job_query.count()
        completed_jobs = job_query.filter(Job.status == "completed").count()
        failed_jobs = job_query.filter(Job.status == "failed").count()
        
        # Estimate edit rate (drafts that were modified after generation)
        # This is a simplified estimate based on version count if available
        edited_drafts = draft_query.filter(Draft.updated_at > Draft.created_at).count()
        edit_rate = (edited_drafts / total_generated * 100) if total_generated > 0 else 0
        
        return {
            "period_days": days,
            "total_drafts_generated": total_generated,
            "drafts_accepted": accepted_drafts,
            "acceptance_rate": round(acceptance_rate, 1),
            "total_emails_sent": total_sent,
            "edit_rate": round(edit_rate, 1),
            "generation_jobs": {
                "total": total_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "success_rate": round(completed_jobs / total_jobs * 100, 1) if total_jobs > 0 else 0
            }
        }
    
    def get_dashboard_summary(
        self, 
        db: Session, 
        user_id: int,
        mailbox_id: Optional[int] = None,
        days: int = 7
    ) -> Dict:
        """
        Get combined analytics summary for dashboard.
        """
        sla = self.get_sla_metrics(db, user_id, mailbox_id, days)
        ai = self.get_ai_usage_metrics(db, user_id, mailbox_id, days)
        
        return {
            "period_days": days,
            "sla": sla,
            "ai_usage": ai,
            "highlights": {
                "backlog_status": "good" if sla["backlog_rate"] < 20 else "warning" if sla["backlog_rate"] < 50 else "critical",
                "response_time_status": "good" if sla["avg_response_time_hours"] < 4 else "warning" if sla["avg_response_time_hours"] < 24 else "critical",
                "ai_adoption": "high" if ai["acceptance_rate"] > 70 else "medium" if ai["acceptance_rate"] > 40 else "low"
            }
        }
