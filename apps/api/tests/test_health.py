"""Tests for health check endpoints."""
import pytest


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns successfully."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_check(self, client):
        """Test full health check endpoint."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_liveness_probe(self, client):
        """Test liveness probe for K8s."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_readiness_probe(self, client):
        """Test readiness probe for K8s."""
        response = client.get("/health/ready")
        # May be 200 or 503 depending on DB state
        assert response.status_code in [200, 503]


class TestMetricsEndpoints:
    """Test metrics endpoints."""
    
    def test_system_metrics_requires_auth(self, client):
        """Test system metrics requires authentication."""
        response = client.get("/metrics/system")
        assert response.status_code == 401
    
    def test_system_metrics_authenticated(self, client, auth_headers):
        """Test system metrics with auth."""
        response = client.get("/metrics/system", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "jobs_total" in data
        assert "emails_total" in data
    
    def test_prometheus_metrics(self, client):
        """Test prometheus format metrics."""
        response = client.get("/metrics/prometheus")
        assert response.status_code == 200
        assert "smartmailbox_jobs_total" in response.text
