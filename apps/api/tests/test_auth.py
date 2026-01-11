"""Tests for authentication endpoints."""
import pytest


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/login", data={
            "username": "test@example.com",
            "password": "testpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with wrong password."""
        response = client.post("/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post("/login", data={
            "username": "nonexistent@example.com",
            "password": "password"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    def test_protected_route_without_auth(self, client):
        """Test protected route without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    def test_admin_route_as_user(self, client, auth_headers):
        """Test admin route with regular user."""
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 403
    
    def test_admin_route_as_admin(self, client, admin_auth_headers):
        """Test admin route with admin user."""
        response = client.get("/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
