"""Integration tests for authentication API routes.

Tests the /api/auth/register, /api/auth/login, and /api/auth/logout
endpoints through the Flask test client.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_user(client, **overrides):
    """Register a user with sensible defaults, allowing field overrides."""
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "password": "securepass123",
    }
    payload.update(overrides)
    return client.post("/api/auth/register", json=payload)


def _login_user(client, email="test@example.com", password="securepass123"):
    """Login with the given credentials."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    """Tests for the registration endpoint."""

    def test_register_valid_data(self, client):
        """Registration with valid data returns 201 and user_id."""
        resp = _register_user(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert "user_id" in data
        assert data["message"] == "Registration successful"

    def test_register_duplicate_email(self, client):
        """Registering with an already-used email returns 409."""
        _register_user(client)
        resp = _register_user(client)
        assert resp.status_code == 409
        data = resp.get_json()
        assert data["error"]["code"] == "CONFLICT"

    def test_register_invalid_email(self, client):
        """Registration with a malformed email returns 400."""
        resp = _register_user(client, email="not-an-email")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_register_short_password(self, client):
        """Registration with a password shorter than 8 chars returns 400."""
        resp = _register_user(client, password="short")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_register_missing_name(self, client):
        """Registration without a name returns 400."""
        resp = client.post(
            "/api/auth/register",
            json={"email": "a@b.com", "password": "securepass123"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_register_missing_password(self, client):
        """Registration without a password returns 400."""
        resp = client.post(
            "/api/auth/register",
            json={"name": "Test", "email": "a@b.com"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    """Tests for the login endpoint."""

    def test_login_valid_credentials(self, client):
        """Login with correct credentials returns 200 and a JWT token."""
        _register_user(client)
        resp = _login_user(client)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client):
        """Login with wrong password returns 401 with generic message."""
        _register_user(client)
        resp = _login_user(client, password="wrongpassword")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert data["error"]["message"] == "Invalid credentials"

    def test_login_nonexistent_email(self, client):
        """Login with an unregistered email returns 401 with generic message."""
        resp = _login_user(client, email="nobody@example.com")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert data["error"]["message"] == "Invalid credentials"

    def test_login_missing_fields(self, client):
        """Login without required fields returns 400."""
        resp = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


class TestLogout:
    """Tests for the logout endpoint."""

    def test_logout_with_valid_token(self, client):
        """Logout with a valid JWT returns 200."""
        _register_user(client)
        login_resp = _login_user(client)
        token = login_resp.get_json()["token"]

        resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Logged out successfully"

    def test_logout_without_token(self, client):
        """Logout without an Authorization header returns 401."""
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_logout_invalidates_token(self, client):
        """After logout, the same token should be rejected."""
        _register_user(client)
        login_resp = _login_user(client)
        token = login_resp.get_json()["token"]

        # Logout
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try using the invalidated token
        resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
