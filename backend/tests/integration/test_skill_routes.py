"""Integration tests for skill analysis API routes.

Tests the GET /api/skills/analysis endpoint through the Flask test
client, covering authentication, missing profile, and happy-path
scenarios.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_student(client, email="skillstudent@example.com"):
    """Register a student account and return the response."""
    return client.post(
        "/api/auth/register",
        json={
            "name": "Skill Student",
            "email": email,
            "phone": "1234567890",
            "password": "securepass123",
        },
    )


def _login_user(client, email="skillstudent@example.com", password="securepass123"):
    """Login and return the JWT token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp.get_json()["token"]


def _seed_taxonomy(db_session):
    """Seed a minimal skill taxonomy for testing."""
    from app.models import SkillTaxonomy

    skills = [
        SkillTaxonomy(
            canonical_name="Python",
            category="Programming Languages",
            synonyms_json=json.dumps(["python", "py"]),
        ),
        SkillTaxonomy(
            canonical_name="JavaScript",
            category="Programming Languages",
            synonyms_json=json.dumps(["javascript", "js"]),
        ),
        SkillTaxonomy(
            canonical_name="SQL",
            category="Databases",
            synonyms_json=json.dumps(["sql"]),
        ),
        SkillTaxonomy(
            canonical_name="Flask",
            category="Frameworks",
            synonyms_json=json.dumps(["flask"]),
        ),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()


def _create_profile(client, token):
    """Create a student profile with skills that match the seeded taxonomy."""
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
                    "title": "Web App",
                    "description": "Built with Flask and Python",
                    "technologies": "Python, Flask",
                }
            ],
            "certifications": [],
        },
    )


# ---------------------------------------------------------------------------
# GET /api/skills/analysis
# ---------------------------------------------------------------------------


class TestGetSkillAnalysis:
    """Tests for the GET /api/skills/analysis endpoint."""

    def test_analysis_without_token_returns_401(self, client):
        """GET /api/skills/analysis without Authorization header returns 401."""
        resp = client.get("/api/skills/analysis")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_analysis_no_profile_returns_404(self, client):
        """GET /api/skills/analysis for a student with no profile returns 404."""
        _register_student(client)
        token = _login_user(client)

        resp = client.get(
            "/api/skills/analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_analysis_with_profile_returns_200_with_categories(self, client):
        """GET /api/skills/analysis with a valid profile returns 200 with categorized skills."""
        from app import db as _db

        _seed_taxonomy(_db.session)
        _register_student(client)
        token = _login_user(client)
        _create_profile(client, token)

        resp = client.get(
            "/api/skills/analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Should have the expected keys
        assert "skills" in data
        assert "categories" in data
        assert "vector_stored" in data
        assert data["vector_stored"] is True

        # Categories should be a dict with at least one category
        assert isinstance(data["categories"], dict)
        assert len(data["categories"]) > 0

        # Skills should be a non-empty list
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0
