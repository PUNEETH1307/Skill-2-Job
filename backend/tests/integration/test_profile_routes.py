"""Integration tests for student profile API routes.

Tests the GET /api/profile and PUT /api/profile endpoints through
the Flask test client, covering authentication, authorization,
validation, and happy-path scenarios.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_student(client, email="student@example.com"):
    """Register a student account and return the response."""
    return client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "phone": "1234567890",
            "password": "securepass123",
        },
    )


def _login_user(client, email="student@example.com", password="securepass123"):
    """Login and return the JWT token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp.get_json()["token"]


def _create_admin_and_login(client):
    """Create an admin user directly in the database and return a login token."""
    import bcrypt
    from app import db as _db
    from app.models import User

    password_hash = bcrypt.hashpw(b"adminpass123", bcrypt.gensalt()).decode("utf-8")
    admin = User(
        name="Admin User",
        email="admin@example.com",
        phone="0000000000",
        password_hash=password_hash,
        role="admin",
        status="active",
    )
    _db.session.add(admin)
    _db.session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"},
    )
    return resp.get_json()["token"]


def _valid_profile_data(**overrides):
    """Return a valid profile payload with optional overrides."""
    data = {
        "institution": "Test University",
        "degree": "B.Tech",
        "branch": "Computer Science",
        "cgpa": 8.5,
        "graduation_year": 2025,
        "skills": ["Python", "JavaScript", "SQL"],
        "projects": [
            {
                "title": "Sample Project",
                "description": "A test project",
                "technologies": "Python, Flask",
            }
        ],
        "certifications": [
            {
                "name": "AWS Cloud Practitioner",
                "issuer": "Amazon",
                "issue_date": "2024-01-15",
            }
        ],
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# GET /api/profile
# ---------------------------------------------------------------------------


class TestGetProfile:
    """Tests for the GET /api/profile endpoint."""

    def test_get_profile_no_profile_returns_404(self, client):
        """GET /api/profile for a student with no profile returns 404."""
        _register_student(client)
        token = _login_user(client)

        resp = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_profile_with_profile_returns_200(self, client):
        """GET /api/profile after creating a profile returns 200 with data."""
        _register_student(client)
        token = _login_user(client)

        # Create a profile first
        client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=_valid_profile_data(),
        )

        resp = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["institution"] == "Test University"
        assert data["degree"] == "B.Tech"
        assert data["branch"] == "Computer Science"
        assert data["cgpa"] == 8.5
        assert len(data["projects"]) == 1
        assert len(data["certifications"]) == 1

    def test_get_profile_without_token_returns_401(self, client):
        """GET /api/profile without Authorization header returns 401."""
        resp = client.get("/api/profile")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_get_profile_with_admin_role_allowed_by_hierarchy(self, client):
        """GET /api/profile with an admin token is allowed (admin >= student in hierarchy)."""
        admin_token = _create_admin_and_login(client)

        resp = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Admin has higher privilege than student in the role hierarchy,
        # so access is granted. Returns 404 because admin has no profile.
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# PUT /api/profile
# ---------------------------------------------------------------------------


class TestUpdateProfile:
    """Tests for the PUT /api/profile endpoint."""

    def test_update_profile_valid_data_returns_200(self, client):
        """PUT /api/profile with valid data creates/updates profile and returns 200."""
        _register_student(client)
        token = _login_user(client)

        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=_valid_profile_data(),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["institution"] == "Test University"
        assert data["degree"] == "B.Tech"
        assert data["branch"] == "Computer Science"
        assert data["cgpa"] == 8.5
        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == "Sample Project"
        assert len(data["certifications"]) == 1
        assert data["certifications"][0]["name"] == "AWS Cloud Practitioner"

    def test_update_profile_invalid_cgpa_high_returns_400(self, client):
        """PUT /api/profile with CGPA > 10.0 returns 400."""
        _register_student(client)
        token = _login_user(client)

        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=_valid_profile_data(cgpa=11.0),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "cgpa" in data["error"]["fields"]

    def test_update_profile_invalid_cgpa_negative_returns_400(self, client):
        """PUT /api/profile with CGPA < 0.0 returns 400."""
        _register_student(client)
        token = _login_user(client)

        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=_valid_profile_data(cgpa=-1.0),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "cgpa" in data["error"]["fields"]

    def test_update_profile_missing_required_fields_returns_400(self, client):
        """PUT /api/profile with missing required fields returns 400."""
        _register_student(client)
        token = _login_user(client)

        # Send payload missing institution, degree, branch, cgpa
        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"graduation_year": 2025, "skills": ["Python"]},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        fields = data["error"]["fields"]
        assert "institution" in fields
        assert "degree" in fields
        assert "branch" in fields
        assert "cgpa" in fields

    def test_update_profile_without_token_returns_401(self, client):
        """PUT /api/profile without Authorization header returns 401."""
        resp = client.put("/api/profile", json=_valid_profile_data())
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_update_profile_with_admin_role_allowed_by_hierarchy(self, client):
        """PUT /api/profile with an admin token is allowed (admin >= student in hierarchy)."""
        admin_token = _create_admin_and_login(client)

        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=_valid_profile_data(),
        )
        # Admin has higher privilege than student, so access is granted
        assert resp.status_code == 200

    def test_update_profile_no_json_body_returns_400(self, client):
        """PUT /api/profile with no JSON body returns 400."""
        _register_student(client)
        token = _login_user(client)

        resp = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            content_type="text/plain",
            data="not json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
