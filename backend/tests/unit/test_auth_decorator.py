"""Unit tests for the @jwt_required and @role_required auth decorators.

Each test creates a minimal Flask test app with routes protected by the
decorators, then exercises them via the Flask test client.
"""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from app import create_app, db as _db
from app.services.auth_service import _token_blacklist


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(app, user_id=1, role="student", expired=False):
    """Create a JWT for testing purposes."""
    secret = app.config["JWT_SECRET_KEY"]
    if expired:
        exp = datetime.now(timezone.utc) - timedelta(seconds=1)
    else:
        exp = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {"user_id": user_id, "role": role, "exp": exp}
    return pyjwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def decorator_app():
    """Create a small Flask app with routes that use the auth decorators."""
    app = create_app("testing")

    # Import decorators inside the fixture so the app context is available
    from app.utils.auth_decorator import jwt_required, role_required

    @app.route("/protected")
    @jwt_required
    def protected():
        from flask import g, jsonify
        return jsonify({"user": g.current_user})

    @app.route("/admin-only")
    @jwt_required
    @role_required("admin")
    def admin_only():
        from flask import g, jsonify
        return jsonify({"user": g.current_user, "message": "admin access granted"})

    @app.route("/officer-only")
    @jwt_required
    @role_required("placement_officer")
    def officer_only():
        from flask import g, jsonify
        return jsonify({"user": g.current_user, "message": "officer access granted"})

    return app


@pytest.fixture()
def client(decorator_app):
    """Flask test client bound to the decorator test app."""
    with decorator_app.test_client() as c:
        with decorator_app.app_context():
            _db.create_all()
            yield c
            _db.session.remove()
            _db.drop_all()


@pytest.fixture(autouse=True)
def clear_blacklist():
    """Ensure the token blacklist is empty before each test."""
    _token_blacklist.clear()
    yield
    _token_blacklist.clear()


# ---------------------------------------------------------------------------
# @jwt_required tests
# ---------------------------------------------------------------------------

class TestJwtRequired:
    """Tests for the @jwt_required decorator."""

    def test_valid_token_sets_current_user(self, client, decorator_app):
        """A valid Bearer token should set g.current_user and allow access."""
        token = _make_token(decorator_app, user_id=42, role="student")
        resp = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["user_id"] == 42
        assert data["user"]["role"] == "student"

    def test_missing_authorization_header_returns_401(self, client):
        """A request without an Authorization header should get 401."""
        resp = client.get("/protected")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "Missing" in data["error"]["message"]

    def test_non_bearer_scheme_returns_401(self, client):
        """An Authorization header that doesn't start with 'Bearer ' should get 401."""
        resp = client.get(
            "/protected", headers={"Authorization": "Basic abc123"}
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_invalid_token_returns_401(self, client):
        """A malformed JWT should get 401."""
        resp = client.get(
            "/protected",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "Invalid token" in data["error"]["message"]

    def test_expired_token_returns_401(self, client, decorator_app):
        """An expired JWT should get 401."""
        token = _make_token(decorator_app, expired=True)
        resp = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "expired" in data["error"]["message"].lower()

    def test_blacklisted_token_returns_401(self, client, decorator_app):
        """A token that has been logged out (blacklisted) should get 401."""
        token = _make_token(decorator_app)
        _token_blacklist.add(token)
        resp = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"


# ---------------------------------------------------------------------------
# @role_required tests
# ---------------------------------------------------------------------------

class TestRoleRequired:
    """Tests for the @role_required decorator (stacked after @jwt_required)."""

    def test_admin_can_access_admin_route(self, client, decorator_app):
        """An admin token should pass @role_required('admin')."""
        token = _make_token(decorator_app, role="admin")
        resp = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "admin access granted"

    def test_student_blocked_from_admin_route(self, client, decorator_app):
        """A student token should be rejected by @role_required('admin')."""
        token = _make_token(decorator_app, role="student")
        resp = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
        assert "Insufficient permissions" in data["error"]["message"]

    def test_officer_blocked_from_admin_route(self, client, decorator_app):
        """A placement_officer token should be rejected by @role_required('admin')."""
        token = _make_token(decorator_app, role="placement_officer")
        resp = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"

    def test_officer_can_access_officer_route(self, client, decorator_app):
        """A placement_officer token should pass @role_required('placement_officer')."""
        token = _make_token(decorator_app, role="placement_officer")
        resp = client.get(
            "/officer-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "officer access granted"

    def test_admin_can_access_officer_route(self, client, decorator_app):
        """An admin token should also pass @role_required('placement_officer') due to hierarchy."""
        token = _make_token(decorator_app, role="admin")
        resp = client.get(
            "/officer-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    def test_student_blocked_from_officer_route(self, client, decorator_app):
        """A student token should be rejected by @role_required('placement_officer')."""
        token = _make_token(decorator_app, role="student")
        resp = client.get(
            "/officer-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
