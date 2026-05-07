"""Integration tests for admin/placement officer API routes.

Tests company management and job role management endpoints
through the Flask test client.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import json

import bcrypt
import pytest

from app import db
from app.models import User, Company, JobRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_placement_officer(client):
    """Create a placement_officer user directly in the DB and return a JWT token."""
    password_hash = bcrypt.hashpw(b"officerpass123", bcrypt.gensalt()).decode("utf-8")
    user = User(
        name="Officer User",
        email="officer@example.com",
        phone="9876543210",
        password_hash=password_hash,
        role="placement_officer",
        status="active",
    )
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "officer@example.com", "password": "officerpass123"},
    )
    return resp.get_json()["token"]


def _create_student_user(client):
    """Register a student user and return a JWT token."""
    client.post(
        "/api/auth/register",
        json={
            "name": "Student User",
            "email": "student@example.com",
            "phone": "1111111111",
            "password": "studentpass123",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "student@example.com", "password": "studentpass123"},
    )
    return resp.get_json()["token"]


def _auth_header(token):
    """Return an Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def _create_company(client, token, **overrides):
    """Create a company via the API with sensible defaults."""
    payload = {
        "name": "Test Corp",
        "industry": "Technology",
        "location": "Bangalore",
        "contact_email": "hr@testcorp.com",
        "contact_phone": "5555555555",
    }
    payload.update(overrides)
    return client.post(
        "/api/admin/companies",
        json=payload,
        headers=_auth_header(token),
    )


def _create_job(client, token, company_id, **overrides):
    """Create a job role via the API with sensible defaults."""
    payload = {
        "company_id": company_id,
        "title": "Software Engineer",
        "description": "Full-stack development role",
        "required_skills": ["Python", "JavaScript"],
        "cgpa_threshold": 7.0,
        "academic_status": "active",
    }
    payload.update(overrides)
    return client.post(
        "/api/admin/jobs",
        json=payload,
        headers=_auth_header(token),
    )


# ---------------------------------------------------------------------------
# GET /api/admin/companies
# ---------------------------------------------------------------------------


class TestListCompanies:
    """Tests for listing companies."""

    def test_list_companies_empty(self, client):
        """GET /api/admin/companies returns 200 with empty list when no companies exist."""
        token = _create_placement_officer(client)
        resp = client.get("/api/admin/companies", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_companies_with_data(self, client):
        """GET /api/admin/companies returns 200 with company list."""
        token = _create_placement_officer(client)
        _create_company(client, token, name="Company A")
        _create_company(client, token, name="Company B")

        resp = client.get("/api/admin/companies", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        names = {c["name"] for c in data}
        assert names == {"Company A", "Company B"}


# ---------------------------------------------------------------------------
# POST /api/admin/companies
# ---------------------------------------------------------------------------


class TestCreateCompany:
    """Tests for creating companies."""

    def test_create_company_valid(self, client):
        """POST /api/admin/companies with valid data returns 201."""
        token = _create_placement_officer(client)
        resp = _create_company(client, token)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Test Corp"
        assert data["industry"] == "Technology"
        assert "id" in data

    def test_create_company_missing_name(self, client):
        """POST /api/admin/companies without name returns 400."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/companies",
            json={"industry": "Tech"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "name" in data["error"]["fields"]

    def test_create_company_empty_name(self, client):
        """POST /api/admin/companies with empty name returns 400."""
        token = _create_placement_officer(client)
        resp = _create_company(client, token, name="   ")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# PUT /api/admin/companies/<id>
# ---------------------------------------------------------------------------


class TestUpdateCompany:
    """Tests for updating companies."""

    def test_update_company_valid(self, client):
        """PUT /api/admin/companies/<id> with valid data returns 200."""
        token = _create_placement_officer(client)
        create_resp = _create_company(client, token)
        company_id = create_resp.get_json()["id"]

        resp = client.put(
            f"/api/admin/companies/{company_id}",
            json={"name": "Updated Corp", "location": "Mumbai"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "Updated Corp"
        assert data["location"] == "Mumbai"

    def test_update_company_not_found(self, client):
        """PUT /api/admin/companies/<id> for nonexistent company returns 404."""
        token = _create_placement_officer(client)
        resp = client.put(
            "/api/admin/companies/9999",
            json={"name": "Ghost Corp"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/admin/jobs
# ---------------------------------------------------------------------------


class TestCreateJob:
    """Tests for creating job roles."""

    def test_create_job_valid(self, client):
        """POST /api/admin/jobs with valid data returns 201."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        resp = _create_job(client, token, company_id)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Software Engineer"
        assert data["company_id"] == company_id
        assert "id" in data

    def test_create_job_stores_vector(self, client):
        """POST /api/admin/jobs stores job_vector_json with correct format."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        resp = _create_job(client, token, company_id, required_skills=["Python"])
        assert resp.status_code == 201
        data = resp.get_json()
        # job_vector_json should be stored (may be None if no taxonomy, but field should exist)
        assert "job_vector_json" in data

    def test_create_job_missing_title(self, client):
        """POST /api/admin/jobs without title returns 400."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        resp = client.post(
            "/api/admin/jobs",
            json={"company_id": company_id, "required_skills": ["Python"]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "title" in data["error"]["fields"]

    def test_create_job_missing_company_id(self, client):
        """POST /api/admin/jobs without company_id returns 400."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/jobs",
            json={"title": "Engineer"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "company_id" in data["error"]["fields"]

    def test_create_job_nonexistent_company(self, client):
        """POST /api/admin/jobs with invalid company_id returns 404."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/jobs",
            json={"company_id": 9999, "title": "Engineer", "required_skills": []},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/admin/jobs/<id>
# ---------------------------------------------------------------------------


class TestUpdateJob:
    """Tests for updating job roles."""

    def test_update_job_valid(self, client):
        """PUT /api/admin/jobs/<id> with valid data returns 200."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]
        job_resp = _create_job(client, token, company_id)
        job_id = job_resp.get_json()["id"]

        resp = client.put(
            f"/api/admin/jobs/{job_id}",
            json={"title": "Senior Engineer", "cgpa_threshold": 8.0},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["title"] == "Senior Engineer"
        assert data["cgpa_threshold"] == 8.0

    def test_update_job_not_found(self, client):
        """PUT /api/admin/jobs/<id> for nonexistent job returns 404."""
        token = _create_placement_officer(client)
        resp = client.put(
            "/api/admin/jobs/9999",
            json={"title": "Ghost Job"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/admin/jobs/<id>
# ---------------------------------------------------------------------------


class TestDeleteJob:
    """Tests for deleting job roles."""

    def test_delete_job_valid(self, client):
        """DELETE /api/admin/jobs/<id> returns 200 and removes the job."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]
        job_resp = _create_job(client, token, company_id)
        job_id = job_resp.get_json()["id"]

        resp = client.delete(
            f"/api/admin/jobs/{job_id}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Job role deleted successfully"

        # Verify it's gone
        assert db.session.get(JobRole, job_id) is None

    def test_delete_job_not_found(self, client):
        """DELETE /api/admin/jobs/<id> for nonexistent job returns 404."""
        token = _create_placement_officer(client)
        resp = client.delete(
            "/api/admin/jobs/9999",
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Access control tests
# ---------------------------------------------------------------------------


class TestAccessControl:
    """Tests for authentication and authorization on admin routes."""

    def test_no_token_returns_401(self, client):
        """Accessing admin routes without a token returns 401."""
        resp = client.get("/api/admin/companies")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_student_access_returns_403(self, client):
        """A student user accessing admin routes returns 403."""
        token = _create_student_user(client)
        resp = client.get("/api/admin/companies", headers=_auth_header(token))
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"

    def test_student_cannot_create_company(self, client):
        """A student user cannot create a company (403)."""
        token = _create_student_user(client)
        resp = client.post(
            "/api/admin/companies",
            json={"name": "Student Corp"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 403

    def test_student_cannot_create_job(self, client):
        """A student user cannot create a job role (403)."""
        token = _create_student_user(client)
        resp = client.post(
            "/api/admin/jobs",
            json={"company_id": 1, "title": "Hacker"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Shortlisting helpers
# ---------------------------------------------------------------------------


def _create_student_with_profile(client, name, email, password, cgpa, skills_json, skill_vector_json):
    """Create a student user with a profile directly in the DB and return the profile_id."""
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    user = User(
        name=name,
        email=email,
        phone="0000000000",
        password_hash=password_hash,
        role="student",
        status="active",
    )
    db.session.add(user)
    db.session.flush()

    from app.models import StudentProfile
    profile = StudentProfile(
        user_id=user.id,
        institution="Test University",
        degree="B.Tech",
        branch="Computer Science",
        cgpa=cgpa,
        graduation_year=2025,
        skills_json=skills_json,
        skill_vector_json=skill_vector_json,
    )
    db.session.add(profile)
    db.session.commit()
    return profile.id


def _create_job_with_vector(client, token, company_id, title, required_skills, cgpa_threshold, job_vector_json):
    """Create a job role directly in the DB with a pre-built vector."""
    job = JobRole(
        company_id=company_id,
        title=title,
        description="Test job",
        required_skills_json=json.dumps(required_skills),
        job_vector_json=job_vector_json,
        cgpa_threshold=cgpa_threshold,
        is_active=True,
    )
    db.session.add(job)
    db.session.commit()
    return job.id


# ---------------------------------------------------------------------------
# GET /api/admin/jobs/<id>/shortlist
# ---------------------------------------------------------------------------


class TestGetShortlist:
    """Tests for getting candidate shortlist for a job role."""

    def test_get_shortlist_no_candidates(self, client):
        """GET /api/admin/jobs/<id>/shortlist returns message when no eligible candidates."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        # Create a job with a vector but no students in the system
        vector_data = json.dumps({
            "vector": [1.0, 0.0, 0.0],
            "skill_index": {"python": 0, "javascript": 1, "sql": 2},
            "version": "1.0",
        })
        job_id = _create_job_with_vector(
            client, token, company_id, "Backend Dev", ["Python"], 7.0, vector_data
        )

        resp = client.get(
            f"/api/admin/jobs/{job_id}/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "No eligible candidates found"
        assert data["candidates"] == []

    def test_get_shortlist_with_candidates(self, client):
        """GET /api/admin/jobs/<id>/shortlist returns sorted candidates."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        skill_index = {"python": 0, "javascript": 1, "sql": 2}
        vector_data = json.dumps({
            "vector": [1.0, 1.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        job_id = _create_job_with_vector(
            client, token, company_id, "Full Stack Dev",
            ["Python", "JavaScript"], 6.0, vector_data
        )

        # Student A: has Python and JavaScript (perfect match)
        student_a_vector = json.dumps({
            "vector": [1.0, 1.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        _create_student_with_profile(
            client, "Alice", "alice@example.com", "password123",
            8.5, json.dumps(["Python", "JavaScript"]), student_a_vector
        )

        # Student B: has only Python (partial match)
        student_b_vector = json.dumps({
            "vector": [1.0, 0.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        _create_student_with_profile(
            client, "Bob", "bob@example.com", "password123",
            7.0, json.dumps(["Python"]), student_b_vector
        )

        resp = client.get(
            f"/api/admin/jobs/{job_id}/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        candidates = data["candidates"]
        assert len(candidates) == 2

        # Should be sorted by compatibility_score descending
        assert candidates[0]["compatibility_score"] >= candidates[1]["compatibility_score"]

        # Check candidate fields
        for c in candidates:
            assert "profile_id" in c
            assert "name" in c
            assert "cgpa" in c
            assert "compatibility_score" in c
            assert "matched_skills" in c
            assert "missing_skills" in c

    def test_get_shortlist_filters_by_cgpa(self, client):
        """GET /api/admin/jobs/<id>/shortlist excludes students below CGPA threshold."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        skill_index = {"python": 0, "javascript": 1}
        vector_data = json.dumps({
            "vector": [1.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        job_id = _create_job_with_vector(
            client, token, company_id, "Python Dev",
            ["Python"], 8.0, vector_data
        )

        # Student with CGPA 7.0 (below threshold of 8.0)
        student_vector = json.dumps({
            "vector": [1.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        _create_student_with_profile(
            client, "Low CGPA", "lowcgpa@example.com", "password123",
            7.0, json.dumps(["Python"]), student_vector
        )

        resp = client.get(
            f"/api/admin/jobs/{job_id}/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "No eligible candidates found"
        assert data["candidates"] == []

    def test_get_shortlist_job_not_found(self, client):
        """GET /api/admin/jobs/<id>/shortlist for nonexistent job returns 404."""
        token = _create_placement_officer(client)
        resp = client.get(
            "/api/admin/jobs/9999/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_get_shortlist_no_token_returns_401(self, client):
        """GET /api/admin/jobs/<id>/shortlist without token returns 401."""
        resp = client.get("/api/admin/jobs/1/shortlist")
        assert resp.status_code == 401

    def test_get_shortlist_student_returns_403(self, client):
        """GET /api/admin/jobs/<id>/shortlist as student returns 403."""
        token = _create_student_user(client)
        resp = client.get(
            "/api/admin/jobs/1/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/admin/jobs/<id>/shortlist
# ---------------------------------------------------------------------------


class TestCreateShortlist:
    """Tests for marking candidates as shortlisted."""

    def test_create_shortlist_valid(self, client):
        """POST /api/admin/jobs/<id>/shortlist creates Shortlist records."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        skill_index = {"python": 0, "javascript": 1}
        vector_data = json.dumps({
            "vector": [1.0, 1.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        job_id = _create_job_with_vector(
            client, token, company_id, "Dev Role",
            ["Python", "JavaScript"], 6.0, vector_data
        )

        student_vector = json.dumps({
            "vector": [1.0, 1.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        profile_id = _create_student_with_profile(
            client, "Charlie", "charlie@example.com", "password123",
            8.0, json.dumps(["Python", "JavaScript"]), student_vector
        )

        resp = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            json={"profile_ids": [profile_id]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["profile_id"] == profile_id
        assert data[0]["job_role_id"] == job_id
        assert data[0]["status"] == "Shortlisted"
        assert "compatibility_score" in data[0]

    def test_create_shortlist_avoids_duplicates(self, client):
        """POST /api/admin/jobs/<id>/shortlist skips already-shortlisted candidates."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        skill_index = {"python": 0}
        vector_data = json.dumps({
            "vector": [1.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        job_id = _create_job_with_vector(
            client, token, company_id, "Dev",
            ["Python"], 6.0, vector_data
        )

        student_vector = json.dumps({
            "vector": [1.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        profile_id = _create_student_with_profile(
            client, "Dupe", "dupe@example.com", "password123",
            8.0, json.dumps(["Python"]), student_vector
        )

        # First shortlist
        resp1 = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            json={"profile_ids": [profile_id]},
            headers=_auth_header(token),
        )
        assert resp1.status_code == 201
        assert len(resp1.get_json()) == 1

        # Second shortlist — should skip the duplicate
        resp2 = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            json={"profile_ids": [profile_id]},
            headers=_auth_header(token),
        )
        assert resp2.status_code == 201
        assert len(resp2.get_json()) == 0

    def test_create_shortlist_empty_profile_ids(self, client):
        """POST /api/admin/jobs/<id>/shortlist with empty list returns 400."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]
        job_resp = _create_job(client, token, company_id)
        job_id = job_resp.get_json()["id"]

        resp = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            json={"profile_ids": []},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_shortlist_missing_body(self, client):
        """POST /api/admin/jobs/<id>/shortlist without JSON body returns 400."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]
        job_resp = _create_job(client, token, company_id)
        job_id = job_resp.get_json()["id"]

        resp = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_create_shortlist_job_not_found(self, client):
        """POST /api/admin/jobs/<id>/shortlist for nonexistent job returns 404."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/jobs/9999/shortlist",
            json={"profile_ids": [1]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_create_shortlist_no_token_returns_401(self, client):
        """POST /api/admin/jobs/<id>/shortlist without token returns 401."""
        resp = client.post(
            "/api/admin/jobs/1/shortlist",
            json={"profile_ids": [1]},
        )
        assert resp.status_code == 401

    def test_create_shortlist_student_returns_403(self, client):
        """POST /api/admin/jobs/<id>/shortlist as student returns 403."""
        token = _create_student_user(client)
        resp = client.post(
            "/api/admin/jobs/1/shortlist",
            json={"profile_ids": [1]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 403

    def test_create_shortlist_skips_nonexistent_profiles(self, client):
        """POST /api/admin/jobs/<id>/shortlist skips profile_ids that don't exist."""
        token = _create_placement_officer(client)
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]
        job_resp = _create_job(client, token, company_id)
        job_id = job_resp.get_json()["id"]

        resp = client.post(
            f"/api/admin/jobs/{job_id}/shortlist",
            json={"profile_ids": [9999]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert len(data) == 0


# ---------------------------------------------------------------------------
# Helpers for admin user
# ---------------------------------------------------------------------------


def _create_admin_user(client):
    """Create an admin user directly in the DB and return a JWT token."""
    password_hash = bcrypt.hashpw(b"adminpass123", bcrypt.gensalt()).decode("utf-8")
    user = User(
        name="Admin User",
        email="admin@example.com",
        phone="1234567890",
        password_hash=password_hash,
        role="admin",
        status="active",
    )
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"},
    )
    return resp.get_json()["token"]


# ---------------------------------------------------------------------------
# GET /api/admin/analytics
# ---------------------------------------------------------------------------


class TestAnalytics:
    """Tests for placement analytics endpoint."""

    def test_analytics_empty_db(self, client):
        """GET /api/admin/analytics returns zeroed stats on empty DB."""
        token = _create_placement_officer(client)
        resp = client.get("/api/admin/analytics", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "overview" in data
        assert data["overview"]["total_students"] == 0
        assert data["overview"]["placed_students"] == 0
        assert data["overview"]["total_companies"] == 0
        assert data["overview"]["placement_percentage"] == 0.0
        assert data["department_breakdown"] == []
        assert data["company_breakdown"] == []
        assert data["skill_demand"] == []

    def test_analytics_with_data(self, client):
        """GET /api/admin/analytics returns correct stats with placement data."""
        token = _create_placement_officer(client)

        # Create a company
        company_resp = _create_company(client, token)
        company_id = company_resp.get_json()["id"]

        # Create a job
        job_resp = _create_job(client, token, company_id, required_skills=["Python", "SQL"])
        job_id = job_resp.get_json()["id"]

        # Create a student with profile
        skill_index = {"python": 0, "sql": 1}
        student_vector = json.dumps({
            "vector": [1.0, 1.0],
            "skill_index": skill_index,
            "version": "1.0",
        })
        profile_id = _create_student_with_profile(
            client, "Analytics Student", "analytics@example.com", "password123",
            8.0, json.dumps(["Python", "SQL"]), student_vector
        )

        # Create a placement record
        from app.models import PlacementRecord
        from datetime import date as date_type
        record = PlacementRecord(
            profile_id=profile_id,
            job_role_id=job_id,
            company_id=company_id,
            placement_date=date_type(2024, 6, 15),
            department="Computer Science",
        )
        db.session.add(record)
        db.session.commit()

        resp = client.get("/api/admin/analytics", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()

        # Overview should reflect the data
        assert data["overview"]["total_companies"] >= 1
        assert data["overview"]["placed_students"] >= 1

        # Department breakdown should have CS
        depts = {d["department"] for d in data["department_breakdown"]}
        assert "Computer Science" in depts

        # Company breakdown should have our company
        company_names = {c["company_name"] for c in data["company_breakdown"]}
        assert "Test Corp" in company_names

        # Skill demand should include Python and SQL
        skill_names = {s["skill"] for s in data["skill_demand"]}
        assert "Python" in skill_names
        assert "SQL" in skill_names

    def test_analytics_date_filter(self, client):
        """GET /api/admin/analytics with date range filters results."""
        token = _create_placement_officer(client)
        resp = client.get(
            "/api/admin/analytics?date_from=2024-01-01&date_to=2024-12-31",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    def test_analytics_invalid_date(self, client):
        """GET /api/admin/analytics with invalid date returns 400."""
        token = _create_placement_officer(client)
        resp = client.get(
            "/api/admin/analytics?date_from=not-a-date",
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_analytics_no_token_returns_401(self, client):
        """GET /api/admin/analytics without token returns 401."""
        resp = client.get("/api/admin/analytics")
        assert resp.status_code == 401

    def test_analytics_student_returns_403(self, client):
        """GET /api/admin/analytics as student returns 403."""
        token = _create_student_user(client)
        resp = client.get("/api/admin/analytics", headers=_auth_header(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------


class TestListUsers:
    """Tests for listing users (admin only)."""

    def test_list_users(self, client):
        """GET /api/admin/users returns paginated user list."""
        token = _create_admin_user(client)
        resp = client.get("/api/admin/users", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        # At least the admin user should be present
        assert data["total"] >= 1

    def test_list_users_search(self, client):
        """GET /api/admin/users with search filters by name/email."""
        token = _create_admin_user(client)
        resp = client.get(
            "/api/admin/users?search=admin",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for u in data["users"]:
            assert "admin" in u["name"].lower() or "admin" in u["email"].lower()

    def test_list_users_pagination(self, client):
        """GET /api/admin/users respects page and per_page params."""
        token = _create_admin_user(client)
        resp = client.get(
            "/api/admin/users?page=1&per_page=1",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["users"]) <= 1

    def test_list_users_officer_returns_403(self, client):
        """GET /api/admin/users as placement_officer returns 403."""
        token = _create_placement_officer(client)
        resp = client.get("/api/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_list_users_student_returns_403(self, client):
        """GET /api/admin/users as student returns 403."""
        token = _create_student_user(client)
        resp = client.get("/api/admin/users", headers=_auth_header(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/admin/users
# ---------------------------------------------------------------------------


class TestCreateUser:
    """Tests for creating users (admin only)."""

    def test_create_user_valid(self, client):
        """POST /api/admin/users with valid data returns 201."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "New Officer",
                "email": "newofficer@example.com",
                "password": "securepass123",
                "role": "placement_officer",
                "phone": "5555555555",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "New Officer"
        assert data["email"] == "newofficer@example.com"
        assert data["role"] == "placement_officer"
        assert data["status"] == "active"

    def test_create_user_missing_fields(self, client):
        """POST /api/admin/users with missing fields returns 400."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/users",
            json={"name": "Incomplete"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_user_duplicate_email(self, client):
        """POST /api/admin/users with existing email returns 409."""
        token = _create_admin_user(client)
        # admin@example.com already exists
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Duplicate",
                "email": "admin@example.com",
                "password": "securepass123",
                "role": "student",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 409

    def test_create_user_invalid_role(self, client):
        """POST /api/admin/users with invalid role returns 400."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Bad Role",
                "email": "badrole@example.com",
                "password": "securepass123",
                "role": "superadmin",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_create_user_short_password(self, client):
        """POST /api/admin/users with short password returns 400."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/users",
            json={
                "name": "Short Pass",
                "email": "shortpass@example.com",
                "password": "short",
                "role": "student",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/admin/users/<id>/status
# ---------------------------------------------------------------------------


class TestUpdateUserStatus:
    """Tests for activating/deactivating users (admin only)."""

    def test_deactivate_user(self, client):
        """PUT /api/admin/users/<id>/status deactivates a user."""
        token = _create_admin_user(client)
        # Create a student to deactivate
        client.post(
            "/api/admin/users",
            json={
                "name": "To Deactivate",
                "email": "deactivate@example.com",
                "password": "securepass123",
                "role": "student",
            },
            headers=_auth_header(token),
        )
        user = User.query.filter_by(email="deactivate@example.com").first()

        resp = client.put(
            f"/api/admin/users/{user.id}/status",
            json={"status": "inactive"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "inactive"

    def test_activate_user(self, client):
        """PUT /api/admin/users/<id>/status activates a user."""
        token = _create_admin_user(client)
        client.post(
            "/api/admin/users",
            json={
                "name": "To Activate",
                "email": "activate@example.com",
                "password": "securepass123",
                "role": "student",
            },
            headers=_auth_header(token),
        )
        user = User.query.filter_by(email="activate@example.com").first()
        user.status = "inactive"
        db.session.commit()

        resp = client.put(
            f"/api/admin/users/{user.id}/status",
            json={"status": "active"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "active"

    def test_update_status_invalid(self, client):
        """PUT /api/admin/users/<id>/status with invalid status returns 400."""
        token = _create_admin_user(client)
        client.post(
            "/api/admin/users",
            json={
                "name": "Bad Status",
                "email": "badstatus@example.com",
                "password": "securepass123",
                "role": "student",
            },
            headers=_auth_header(token),
        )
        user = User.query.filter_by(email="badstatus@example.com").first()

        resp = client.put(
            f"/api/admin/users/{user.id}/status",
            json={"status": "banned"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_update_status_not_found(self, client):
        """PUT /api/admin/users/<id>/status for nonexistent user returns 404."""
        token = _create_admin_user(client)
        resp = client.put(
            "/api/admin/users/9999/status",
            json={"status": "inactive"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Skill Taxonomy routes
# ---------------------------------------------------------------------------


class TestSkillTaxonomy:
    """Tests for skill taxonomy management (admin only)."""

    def test_list_taxonomy_empty(self, client):
        """GET /api/admin/skills/taxonomy returns empty list."""
        token = _create_admin_user(client)
        resp = client.get("/api/admin/skills/taxonomy", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_create_taxonomy_skill(self, client):
        """POST /api/admin/skills/taxonomy creates a skill entry."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/skills/taxonomy",
            json={
                "canonical_name": "Python",
                "category": "Programming Languages",
                "synonyms_json": ["python3", "py"],
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["canonical_name"] == "Python"
        assert data["category"] == "Programming Languages"
        assert data["is_deprecated"] is False

    def test_create_taxonomy_skill_missing_name(self, client):
        """POST /api/admin/skills/taxonomy without name returns 400."""
        token = _create_admin_user(client)
        resp = client.post(
            "/api/admin/skills/taxonomy",
            json={"category": "Frameworks"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_create_taxonomy_skill_duplicate(self, client):
        """POST /api/admin/skills/taxonomy with duplicate name returns 409."""
        token = _create_admin_user(client)
        client.post(
            "/api/admin/skills/taxonomy",
            json={"canonical_name": "React", "category": "Frameworks"},
            headers=_auth_header(token),
        )
        resp = client.post(
            "/api/admin/skills/taxonomy",
            json={"canonical_name": "React", "category": "Frameworks"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 409

    def test_update_taxonomy_skill(self, client):
        """PUT /api/admin/skills/taxonomy/<id> updates a skill."""
        token = _create_admin_user(client)
        create_resp = client.post(
            "/api/admin/skills/taxonomy",
            json={"canonical_name": "JS", "category": "Programming Languages"},
            headers=_auth_header(token),
        )
        skill_id = create_resp.get_json()["id"]

        resp = client.put(
            f"/api/admin/skills/taxonomy/{skill_id}",
            json={"canonical_name": "JavaScript", "category": "Programming Languages"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["canonical_name"] == "JavaScript"

    def test_update_taxonomy_skill_not_found(self, client):
        """PUT /api/admin/skills/taxonomy/<id> for nonexistent skill returns 404."""
        token = _create_admin_user(client)
        resp = client.put(
            "/api/admin/skills/taxonomy/9999",
            json={"canonical_name": "Ghost"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_delete_taxonomy_skill_soft(self, client):
        """DELETE /api/admin/skills/taxonomy/<id> marks skill as deprecated."""
        token = _create_admin_user(client)
        create_resp = client.post(
            "/api/admin/skills/taxonomy",
            json={"canonical_name": "COBOL", "category": "Programming Languages"},
            headers=_auth_header(token),
        )
        skill_id = create_resp.get_json()["id"]

        resp = client.delete(
            f"/api/admin/skills/taxonomy/{skill_id}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_deprecated"] is True

    def test_delete_taxonomy_skill_not_found(self, client):
        """DELETE /api/admin/skills/taxonomy/<id> for nonexistent skill returns 404."""
        token = _create_admin_user(client)
        resp = client.delete(
            "/api/admin/skills/taxonomy/9999",
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_taxonomy_officer_returns_403(self, client):
        """Placement officer cannot access taxonomy routes (403)."""
        token = _create_placement_officer(client)
        resp = client.get("/api/admin/skills/taxonomy", headers=_auth_header(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/skills/uncategorized
# ---------------------------------------------------------------------------


class TestUncategorizedSkills:
    """Tests for uncategorized skills endpoint."""

    def test_list_uncategorized_empty(self, client):
        """GET /api/admin/skills/uncategorized returns empty list."""
        token = _create_admin_user(client)
        resp = client.get("/api/admin/skills/uncategorized", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_uncategorized_with_data(self, client):
        """GET /api/admin/skills/uncategorized returns flagged skills."""
        token = _create_admin_user(client)
        from app.models import UncategorizedSkill
        skill = UncategorizedSkill(term="NewFramework", occurrence_count=5, reviewed=False)
        db.session.add(skill)
        db.session.commit()

        resp = client.get("/api/admin/skills/uncategorized", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["term"] == "NewFramework"
        assert data[0]["occurrence_count"] == 5


# ---------------------------------------------------------------------------
# POST /api/admin/courses
# ---------------------------------------------------------------------------


class TestCreateCourse:
    """Tests for course recommendation creation."""

    def test_create_course_valid(self, client):
        """POST /api/admin/courses with valid data returns 201."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/courses",
            json={
                "skill_name": "Python",
                "course_name": "Python for Beginners",
                "provider": "Coursera",
                "url": "https://coursera.org/python",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["skill_name"] == "Python"
        assert data["course_name"] == "Python for Beginners"
        assert data["provider"] == "Coursera"

    def test_create_course_missing_fields(self, client):
        """POST /api/admin/courses with missing fields returns 400."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/courses",
            json={"skill_name": "Python"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "course_name" in data["error"]["fields"]

    def test_create_course_no_body(self, client):
        """POST /api/admin/courses without JSON body returns 400."""
        token = _create_placement_officer(client)
        resp = client.post(
            "/api/admin/courses",
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_create_course_student_returns_403(self, client):
        """POST /api/admin/courses as student returns 403."""
        token = _create_student_user(client)
        resp = client.post(
            "/api/admin/courses",
            json={"skill_name": "Python", "course_name": "Test"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Error handler tests
# ---------------------------------------------------------------------------


class TestErrorHandlers:
    """Tests for global error handlers."""

    def test_404_returns_json(self, client):
        """Requesting a nonexistent route returns JSON 404."""
        resp = client.get("/api/nonexistent-route")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_405_method_not_allowed(self, client):
        """Using wrong HTTP method returns appropriate error."""
        # PATCH is not defined on /api/admin/companies
        token = _create_placement_officer(client)
        resp = client.patch(
            "/api/admin/companies",
            json={"name": "test"},
            headers=_auth_header(token),
        )
        # Flask returns 405 by default; our handler covers 400-503
        assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Sanitizer tests
# ---------------------------------------------------------------------------


class TestSanitizer:
    """Tests for input sanitization."""

    def test_xss_payload_stripped(self, client):
        """XSS payloads in company name are sanitized."""
        token = _create_placement_officer(client)
        resp = _create_company(
            client, token, name="<script>alert('xss')</script>Safe Corp"
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "<script>" not in data["name"]
        assert "Safe Corp" in data["name"]

    def test_sql_injection_stripped(self, client):
        """SQL injection patterns in company name are sanitized."""
        token = _create_placement_officer(client)
        resp = _create_company(
            client, token, name="Corp; DROP TABLE user;--"
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "DROP TABLE" not in data["name"]
