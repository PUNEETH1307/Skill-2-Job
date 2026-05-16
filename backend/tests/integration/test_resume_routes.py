"""Integration tests for resume generation API routes.

Tests the POST /api/resume/generate and GET /api/resume/download endpoints
through the Flask test client, covering authentication, validation, and
happy-path scenarios.
"""

import json

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


def _create_complete_profile(client, token):
    """Create a complete student profile with all required fields."""
    return client.put(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
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
        },
    )


def _create_incomplete_profile(client, token):
    """Create a profile missing required fields (no skills)."""
    return client.put(
        "/api/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "institution": "Test University",
            "degree": "B.Tech",
            "branch": "Computer Science",
            "cgpa": 7.0,
            "graduation_year": 2025,
            "skills": [],
            "projects": [],
            "certifications": [],
        },
    )


# ---------------------------------------------------------------------------
# POST /api/resume/generate
# ---------------------------------------------------------------------------


class TestGenerateResume:
    """Tests for the POST /api/resume/generate endpoint."""

    def test_generate_resume_complete_profile_returns_200(self, client):
        """POST /api/resume/generate with a complete profile returns 200."""
        _register_student(client)
        token = _login_user(client)
        _create_complete_profile(client, token)

        resp = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Resume generated successfully"

    def test_generate_resume_incomplete_profile_returns_400(self, client):
        """POST /api/resume/generate with missing fields returns 400 with error."""
        _register_student(client)
        token = _login_user(client)
        _create_incomplete_profile(client, token)

        resp = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "missing" in data["error"]["message"].lower()
        assert data["error"]["fields"]["missing_fields"] == ["skills"]

    def test_generate_resume_no_profile_returns_400(self, client):
        """POST /api/resume/generate with no profile at all returns 400."""
        _register_student(client)
        token = _login_user(client)

        resp = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_generate_resume_without_token_returns_401(self, client):
        """POST /api/resume/generate without Authorization header returns 401."""
        resp = client.post("/api/resume/generate")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"


# ---------------------------------------------------------------------------
# GET /api/resume/download
# ---------------------------------------------------------------------------


class TestDownloadResume:
    """Tests for the GET /api/resume/download endpoint."""

    def test_download_resume_complete_profile_returns_pdf(self, client):
        """GET /api/resume/download with a complete profile returns PDF content."""
        _register_student(client)
        token = _login_user(client)
        _create_complete_profile(client, token)

        resp = client.get(
            "/api/resume/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        # Check Content-Disposition header for attachment download
        content_disp = resp.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp
        assert "Resume_Test_Student_" in content_disp
        assert content_disp.endswith(".pdf")
        # Verify the response body starts with PDF magic bytes
        assert resp.data[:5] == b"%PDF-"

    def test_download_resume_without_token_returns_401(self, client):
        """GET /api/resume/download without Authorization header returns 401."""
        resp = client.get("/api/resume/download")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_download_resume_no_profile_returns_400(self, client):
        """GET /api/resume/download with no profile returns 400."""
        _register_student(client)
        token = _login_user(client)

        resp = client.get(
            "/api/resume/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_download_resume_incomplete_profile_returns_400(self, client):
        """GET /api/resume/download with incomplete profile returns 400."""
        _register_student(client)
        token = _login_user(client)
        _create_incomplete_profile(client, token)

        resp = client.get(
            "/api/resume/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
