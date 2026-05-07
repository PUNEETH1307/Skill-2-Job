"""Integration tests for dashboard API routes.

Tests the /api/dashboard/student, /api/dashboard/coordinator, and
/api/dashboard/admin endpoints through the Flask test client.

Requirements: 9.4, 9.5
"""

import bcrypt
import pytest

from app import db
from app.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_user(role, email, password="securepass123"):
    """Create a user with the given role directly in the DB."""
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    user = User(
        name=f"{role.capitalize()} User",
        email=email,
        phone="1234567890",
        password_hash=password_hash,
        role=role,
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email, password="securepass123"):
    """Login and return the JWT token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp.get_json()["token"]


def _auth_header(token):
    """Return an Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def _create_student_token(client):
    """Create a student user and return a JWT token."""
    _create_user("student", "student@example.com")
    return _login(client, "student@example.com")


def _create_coordinator_token(client):
    """Create a placement_officer user and return a JWT token."""
    _create_user("placement_officer", "coordinator@example.com")
    return _login(client, "coordinator@example.com")


def _create_admin_token(client):
    """Create an admin user and return a JWT token."""
    _create_user("admin", "admin@example.com")
    return _login(client, "admin@example.com")


# ---------------------------------------------------------------------------
# GET /api/dashboard/student
# ---------------------------------------------------------------------------


class TestStudentDashboard:
    """Tests for the student dashboard endpoint."""

    def test_authenticated_student_returns_200(self, client):
        """GET /api/dashboard/student with valid student token returns 200."""
        token = _create_student_token(client)
        resp = client.get("/api/dashboard/student", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_response_shape(self, client):
        """GET /api/dashboard/student returns expected response keys."""
        token = _create_student_token(client)
        resp = client.get("/api/dashboard/student", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()

        # Verify expected top-level keys
        assert "profile_completeness" in data
        assert "skill_count" in data
        assert "skill_breakdown" in data
        assert "matched_job_count" in data
        assert "top_recommendations" in data

        # Verify types
        assert isinstance(data["profile_completeness"], int)
        assert isinstance(data["skill_count"], int)
        assert isinstance(data["skill_breakdown"], dict)
        assert isinstance(data["matched_job_count"], int)
        assert isinstance(data["top_recommendations"], list)

    def test_new_student_has_zero_completeness(self, client):
        """A student with no profile data has profile_completeness of 0."""
        token = _create_student_token(client)
        resp = client.get("/api/dashboard/student", headers=_auth_header(token))
        data = resp.get_json()
        assert data["profile_completeness"] == 0
        assert data["skill_count"] == 0
        assert data["matched_job_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/dashboard/coordinator
# ---------------------------------------------------------------------------


class TestCoordinatorDashboard:
    """Tests for the coordinator dashboard endpoint."""

    def test_authenticated_coordinator_returns_200(self, client):
        """GET /api/dashboard/coordinator with valid placement_officer token returns 200."""
        token = _create_coordinator_token(client)
        resp = client.get(
            "/api/dashboard/coordinator", headers=_auth_header(token)
        )
        assert resp.status_code == 200

    def test_response_shape(self, client):
        """GET /api/dashboard/coordinator returns expected response keys."""
        token = _create_coordinator_token(client)
        resp = client.get(
            "/api/dashboard/coordinator", headers=_auth_header(token)
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Verify expected top-level keys
        assert "placement_overview" in data
        assert "active_job_count" in data
        assert "shortlisted_count" in data
        assert "recent_shortlists" in data
        assert "top_skills_demand" in data

        # Verify nested placement_overview shape
        overview = data["placement_overview"]
        assert "total_students" in overview
        assert "placed_students" in overview
        assert "total_companies" in overview
        assert "placement_percentage" in overview

        # Verify types
        assert isinstance(data["active_job_count"], int)
        assert isinstance(data["shortlisted_count"], int)
        assert isinstance(data["recent_shortlists"], list)
        assert isinstance(data["top_skills_demand"], list)


# ---------------------------------------------------------------------------
# GET /api/dashboard/admin
# ---------------------------------------------------------------------------


class TestAdminDashboard:
    """Tests for the admin dashboard endpoint."""

    def test_authenticated_admin_returns_200(self, client):
        """GET /api/dashboard/admin with valid admin token returns 200."""
        token = _create_admin_token(client)
        resp = client.get("/api/dashboard/admin", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_response_shape(self, client):
        """GET /api/dashboard/admin returns expected response keys."""
        token = _create_admin_token(client)
        resp = client.get("/api/dashboard/admin", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()

        # Verify expected top-level keys
        assert "user_counts" in data
        assert "taxonomy_health" in data
        assert "placement_overview" in data

        # Verify nested user_counts shape
        user_counts = data["user_counts"]
        assert "by_role" in user_counts
        assert "by_status" in user_counts
        assert "total" in user_counts
        assert isinstance(user_counts["by_role"], dict)
        assert isinstance(user_counts["by_status"], dict)
        assert isinstance(user_counts["total"], int)

        # Verify nested taxonomy_health shape
        taxonomy = data["taxonomy_health"]
        assert "total_skills" in taxonomy
        assert "deprecated_skills" in taxonomy
        assert "uncategorized_pending" in taxonomy

        # Verify nested placement_overview shape
        overview = data["placement_overview"]
        assert "total_students" in overview
        assert "placed_students" in overview
        assert "total_companies" in overview
        assert "placement_percentage" in overview


# ---------------------------------------------------------------------------
# Authentication and Authorization
# ---------------------------------------------------------------------------


class TestDashboardAuth:
    """Tests for authentication and authorization on dashboard routes."""

    def test_unauthenticated_student_endpoint_returns_401(self, client):
        """GET /api/dashboard/student without token returns 401."""
        resp = client.get("/api/dashboard/student")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_unauthenticated_coordinator_endpoint_returns_401(self, client):
        """GET /api/dashboard/coordinator without token returns 401."""
        resp = client.get("/api/dashboard/coordinator")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_unauthenticated_admin_endpoint_returns_401(self, client):
        """GET /api/dashboard/admin without token returns 401."""
        resp = client.get("/api/dashboard/admin")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_student_requesting_coordinator_endpoint_returns_403(self, client):
        """A student accessing /api/dashboard/coordinator returns 403."""
        token = _create_student_token(client)
        resp = client.get(
            "/api/dashboard/coordinator", headers=_auth_header(token)
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"

    def test_student_requesting_admin_endpoint_returns_403(self, client):
        """A student accessing /api/dashboard/admin returns 403."""
        token = _create_student_token(client)
        resp = client.get("/api/dashboard/admin", headers=_auth_header(token))
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"

    def test_placement_officer_requesting_admin_endpoint_returns_403(self, client):
        """A placement_officer accessing /api/dashboard/admin returns 403."""
        token = _create_coordinator_token(client)
        resp = client.get("/api/dashboard/admin", headers=_auth_header(token))
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"

    def test_invalid_token_returns_401(self, client):
        """An invalid JWT token returns 401."""
        resp = client.get(
            "/api/dashboard/student",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
