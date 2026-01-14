import pytest
from unittest.mock import patch, MagicMock
from app.models.mailbox import Mailbox
from app.models.email import Email
from app.integrations.llm.base import LLMResponse
from datetime import datetime

@pytest.fixture
def test_mailbox(db, test_user):
    mailbox = Mailbox(
        user_id=test_user.id,
        email_address="test@example.com",
        imap_host="localhost",
        imap_port=993,
        smtp_host="localhost",
        smtp_port=587,
        is_active=True
    )
    db.add(mailbox)
    db.commit()
    db.refresh(mailbox)
    return mailbox

@pytest.fixture
def test_email(db, test_mailbox):
    email = Email(
        mailbox_id=test_mailbox.id,
        message_id="<test-msg-id@example.com>",
        sender="sender@example.com",
        recipients=["test@example.com"],
        subject="Integration Test Email",
        body_text="Dear user, this is a test email for AI drafting.",
        received_at=datetime.utcnow()
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

class TestInboxAI:
    def test_list_emails(self, client, auth_headers, test_email):
        response = client.get("/emails/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(item["subject"] == "Integration Test Email" for item in data["items"])

    def test_get_email_detail(self, client, auth_headers, test_email):
        response = client.get(f"/emails/{test_email.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Integration Test Email"
        assert data["body_text"] == "Dear user, this is a test email for AI drafting."

    @pytest.mark.asyncio
    @patch("app.integrations.llm.ollama.OllamaProvider.generate")
    async def test_generate_ai_draft(self, mock_generate, client, auth_headers, test_email):
        # Setup mock response
        mock_generate.return_value = LLMResponse(
            text="Mocked AI Reply: Thank you for your email.",
            tokens_used=10,
            latency_ms=100,
            model_name="llama3"
        )
        
        request_body = {
            "instructions": "Reply thanking them.",
            "tone": "friendly"
        }
        
        response = client.post(
            f"/emails/{test_email.id}/draft",
            json=request_body,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Mocked AI Reply" in data["text"]
        assert data["model_name"] == "llama3"

    def test_enqueue_draft_job(self, client, auth_headers, test_email):
        request_body = {
            "instructions": "Reply thanking them.",
            "tone": "professional"
        }
        
        response = client.post(
            f"/emails/{test_email.id}/draft-job",
            json=request_body,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
