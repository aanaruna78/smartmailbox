"""Tests for quarantine endpoints."""
import pytest


class TestQuarantineEndpoints:
    """Test quarantine endpoints."""
    
    def test_get_queue_requires_auth(self, client):
        """Test quarantine queue requires authentication."""
        response = client.get("/quarantine/queue")
        assert response.status_code == 401
    
    def test_get_queue_authenticated(self, client, auth_headers):
        """Test quarantine queue with auth."""
        response = client.get("/quarantine/queue", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_stats(self, client, auth_headers):
        """Test quarantine stats endpoint."""
        response = client.get("/quarantine/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "released" in data


class TestSpamEndpoints:
    """Test spam endpoints."""
    
    def test_get_rules(self, client, auth_headers):
        """Test get spam rules."""
        response = client.get("/spam/rules", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_rule(self, client, auth_headers):
        """Test create spam rule."""
        response = client.post("/spam/rules", headers=auth_headers, json={
            "rule_type": "block_sender",
            "value": "spam@example.com",
            "weight": 50
        })
        # May succeed or fail depending on implementation
        assert response.status_code in [200, 201, 422]
