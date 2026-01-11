"""Tests for spam filter service."""
import pytest
from unittest.mock import MagicMock


class TestSpamFilterService:
    """Test spam filter service."""
    
    def test_calculate_score_clean_email(self, db):
        """Test spam score for clean email."""
        from app.services.spam_filter_service import SpamFilterService
        
        service = SpamFilterService()
        
        # Mock email
        email = MagicMock()
        email.subject = "Meeting tomorrow"
        email.body_text = "Hi, let's meet tomorrow at 3pm. Best regards, John"
        email.sender = "john@company.com"
        email.mailbox_id = 1
        
        score, reasons = service.calculate_spam_score(db, email)
        
        assert score < 30  # Should be clean
        assert len(reasons) == 0 or all("spam" not in r.lower() for r in reasons)
    
    def test_calculate_score_spam_keywords(self, db):
        """Test spam score with spam keywords."""
        from app.services.spam_filter_service import SpamFilterService
        
        service = SpamFilterService()
        
        email = MagicMock()
        email.subject = "FREE MONEY - ACT NOW!!!"
        email.body_text = "Congratulations! You've won a lottery! Click here to claim your prize!"
        email.sender = "winner@spam.com"
        email.mailbox_id = 1
        
        score, reasons = service.calculate_spam_score(db, email)
        
        assert score >= 30  # Should be suspicious or spam
        assert len(reasons) > 0
    
    def test_get_label_clean(self, db):
        """Test label for low score."""
        from app.services.spam_filter_service import SpamFilterService
        
        service = SpamFilterService()
        
        assert service.get_label(10) == "clean"
        assert service.get_label(29) == "clean"
    
    def test_get_label_suspicious(self, db):
        """Test label for medium score."""
        from app.services.spam_filter_service import SpamFilterService
        
        service = SpamFilterService()
        
        assert service.get_label(30) == "suspicious"
        assert service.get_label(59) == "suspicious"
    
    def test_get_label_spam(self, db):
        """Test label for high score."""
        from app.services.spam_filter_service import SpamFilterService
        
        service = SpamFilterService()
        
        assert service.get_label(60) == "spam"
        assert service.get_label(100) == "spam"


class TestAnalyticsService:
    """Test analytics service."""
    
    def test_get_sla_metrics(self, db):
        """Test SLA metrics calculation."""
        from app.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        result = service.get_sla_metrics(db)
        
        assert "total_received" in result
        assert "backlog" in result
        assert "avg_response_time_hours" in result
    
    def test_get_ai_usage_metrics(self, db):
        """Test AI usage metrics calculation."""
        from app.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        result = service.get_ai_usage_metrics(db)
        
        assert "total_drafts_generated" in result
        assert "acceptance_rate" in result
        assert "edit_rate" in result
