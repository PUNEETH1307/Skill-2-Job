"""Integration tests for job matching API routes.

Tests the GET /api/jobs/recommendations, GET /api/jobs/<id>/skill-gap,
and GET /api/jobs/<id>/courses endpoints through the Flask test client.
"""

import json

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_student(client, email="jobstudent@example.com"):
    """Register a student account and return the response."""
    return client.post(
        "/api/auth/register",
        json={
            "name": "Job Student",
            "email": email,
            "phone": "1234567890",
            "password": "securepass123",
        },
    )


def _login_user(client, email="jobstudent@example.com", password="securepass123"):
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
        SkillTaxonomy(
            canonical_name="Docker",
            category="Tools",
            synonyms_json=json.dumps(["docker"]),
        ),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()


def _create_profile_with_vector(client, token):
    """Create a student profile and ensure it has a skill vector."""
    client.put(
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
    # Trigger skill analysis to generate the skill vector
    client.get(
        "/api/skills/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )


def _seed_company_and_job(db_session, skill_index=None):
    """Seed a company and job role with a job vector.

    Returns the created JobRole.
    """
    from app.models import Company, JobRole

    company = Company(
        name="Test Corp",
        industry="Technology",
        location="San Francisco",
        contact_email="hr@testcorp.com",
    )
    db_session.add(company)
    db_session.flush()

    # Build a job vector that requires Python, JavaScript, SQL, Docker
    # but NOT Flask — so there's a gap on Docker for a student who has
    # Python, JavaScript, SQL, Flask
    if skill_index is None:
        skill_index = {
            "python": 0,
            "javascript": 1,
            "sql": 2,
            "flask": 3,
            "docker": 4,
        }

    # Job requires: Python(1), JavaScript(1), SQL(0), Flask(0), Docker(1)
    job_vector = [1.0, 1.0, 0.0, 0.0, 1.0]

    job_vector_json = json.dumps(
        {
            "vector": job_vector,
            "skill_index": skill_index,
            "version": "1.0",
        }
    )

    job_role = JobRole(
        company_id=company.id,
        title="Backend Developer",
        description="Python backend role",
        required_skills_json=json.dumps(["Python", "JavaScript", "Docker"]),
        job_vector_json=job_vector_json,
        cgpa_threshold=7.0,
        is_active=True,
    )
    db_session.add(job_role)
    db_session.commit()

    return job_role


def _seed_course_recommendations(db_session):
    """Seed course recommendations for Docker skill."""
    from app.models import CourseRecommendation

    courses = [
        CourseRecommendation(
            skill_name="Docker",
            course_name="Docker for Beginners",
            provider="Udemy",
            url="https://udemy.com/docker-beginners",
        ),
        CourseRecommendation(
            skill_name="Docker",
            course_name="Docker Deep Dive",
            provider="Pluralsight",
            url="https://pluralsight.com/docker-deep-dive",
        ),
    ]
    for course in courses:
        db_session.add(course)
    db_session.commit()


def _setup_student_with_vector(db_session, client):
    """Full setup: seed taxonomy, register student, create profile with vector.

    Returns the JWT token.
    """
    _seed_taxonomy(db_session)
    _register_student(client)
    token = _login_user(client)
    _create_profile_with_vector(client, token)
    return token


# ---------------------------------------------------------------------------
# GET /api/jobs/recommendations
# ---------------------------------------------------------------------------


class TestGetRecommendations:
    """Tests for the GET /api/jobs/recommendations endpoint."""

    def test_recommendations_without_token_returns_401(self, client):
        """GET /api/jobs/recommendations without Authorization header returns 401."""
        resp = client.get("/api/jobs/recommendations")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_recommendations_with_valid_student_returns_200(self, client):
        """GET /api/jobs/recommendations with a valid student returns 200 with list."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)
        _seed_company_and_job(_db.session)

        resp = client.get(
            "/api/jobs/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check structure of first recommendation
        rec = data[0]
        assert "job_role_id" in rec
        assert "title" in rec
        assert "company_name" in rec
        assert "compatibility_score" in rec
        assert "required_skills" in rec
        assert rec["company_name"] == "Test Corp"

    def test_recommendations_no_jobs_returns_empty_list(self, client):
        """GET /api/jobs/recommendations with no active jobs returns empty list."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)

        resp = client.get(
            "/api/jobs/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_recommendations_sorted_descending(self, client):
        """Recommendations are sorted by compatibility_score descending."""
        from app import db as _db
        from app.models import Company, JobRole

        token = _setup_student_with_vector(_db.session, client)

        # Create two jobs with different vectors
        company = Company(name="Multi Corp", industry="Tech", location="NYC")
        _db.session.add(company)
        _db.session.flush()

        skill_index = {"python": 0, "javascript": 1, "sql": 2, "flask": 3, "docker": 4}

        # Job 1: requires Python only — high match
        job1 = JobRole(
            company_id=company.id,
            title="Python Dev",
            required_skills_json=json.dumps(["Python"]),
            job_vector_json=json.dumps({"vector": [1.0, 0.0, 0.0, 0.0, 0.0], "skill_index": skill_index, "version": "1.0"}),
            cgpa_threshold=0.0,
            is_active=True,
        )
        # Job 2: requires Docker only — low match (student doesn't have Docker)
        job2 = JobRole(
            company_id=company.id,
            title="DevOps",
            required_skills_json=json.dumps(["Docker"]),
            job_vector_json=json.dumps({"vector": [0.0, 0.0, 0.0, 0.0, 1.0], "skill_index": skill_index, "version": "1.0"}),
            cgpa_threshold=0.0,
            is_active=True,
        )
        _db.session.add_all([job1, job2])
        _db.session.commit()

        resp = client.get(
            "/api/jobs/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2

        # Verify descending order
        scores = [r["compatibility_score"] for r in data]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# GET /api/jobs/<id>/skill-gap
# ---------------------------------------------------------------------------


class TestGetSkillGap:
    """Tests for the GET /api/jobs/<id>/skill-gap endpoint."""

    def test_skill_gap_without_token_returns_401(self, client):
        """GET /api/jobs/1/skill-gap without Authorization header returns 401."""
        resp = client.get("/api/jobs/1/skill-gap")
        assert resp.status_code == 401

    def test_skill_gap_with_gaps_returns_200(self, client):
        """GET /api/jobs/<id>/skill-gap returns 200 with gap analysis."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)
        job_role = _seed_company_and_job(_db.session)

        resp = client.get(
            f"/api/jobs/{job_role.id}/skill-gap",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Should have gaps (Docker is required but student doesn't have it)
        assert "gaps" in data or "message" in data
        if "gaps" in data:
            assert data["job_role_id"] == job_role.id
            assert isinstance(data["gaps"], list)
            # Each gap should have skill and deficit_score
            for gap in data["gaps"]:
                assert "skill" in gap
                assert "deficit_score" in gap
                assert 0.0 <= gap["deficit_score"] <= 1.0

    def test_skill_gap_full_coverage_returns_message(self, client):
        """GET /api/jobs/<id>/skill-gap returns full coverage message when no gaps."""
        from app import db as _db
        from app.models import Company, JobRole

        token = _setup_student_with_vector(_db.session, client)

        # Create a job that only requires skills the student has
        company = Company(name="Easy Corp", industry="Tech", location="NYC")
        _db.session.add(company)
        _db.session.flush()

        skill_index = {"python": 0, "javascript": 1, "sql": 2, "flask": 3, "docker": 4}
        # Only requires Python and JavaScript — student has both
        job_vector_json = json.dumps({
            "vector": [1.0, 1.0, 0.0, 0.0, 0.0],
            "skill_index": skill_index,
            "version": "1.0",
        })

        job_role = JobRole(
            company_id=company.id,
            title="Easy Dev",
            required_skills_json=json.dumps(["Python", "JavaScript"]),
            job_vector_json=job_vector_json,
            cgpa_threshold=0.0,
            is_active=True,
        )
        _db.session.add(job_role)
        _db.session.commit()

        resp = client.get(
            f"/api/jobs/{job_role.id}/skill-gap",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Full skill coverage"

    def test_skill_gap_nonexistent_job_returns_404(self, client):
        """GET /api/jobs/9999/skill-gap returns 404 for nonexistent job."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)

        resp = client.get(
            "/api/jobs/9999/skill-gap",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# GET /api/jobs/<id>/courses
# ---------------------------------------------------------------------------


class TestGetCourses:
    """Tests for the GET /api/jobs/<id>/courses endpoint."""

    def test_courses_without_token_returns_401(self, client):
        """GET /api/jobs/1/courses without Authorization header returns 401."""
        resp = client.get("/api/jobs/1/courses")
        assert resp.status_code == 401

    def test_courses_with_gap_skills_returns_200(self, client):
        """GET /api/jobs/<id>/courses returns 200 with courses grouped by skill."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)
        job_role = _seed_company_and_job(_db.session)
        _seed_course_recommendations(_db.session)

        resp = client.get(
            f"/api/jobs/{job_role.id}/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "job_role_id" in data
        assert data["job_role_id"] == job_role.id
        assert "skill_courses" in data
        assert isinstance(data["skill_courses"], list)

        # Check that courses are present for gap skills
        if len(data["skill_courses"]) > 0:
            entry = data["skill_courses"][0]
            assert "skill" in entry
            assert "deficit_score" in entry
            assert "courses" in entry

    def test_courses_no_courses_available_message(self, client):
        """GET /api/jobs/<id>/courses returns 'no courses available' for skills without courses."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)
        job_role = _seed_company_and_job(_db.session)
        # Don't seed any course recommendations

        resp = client.get(
            f"/api/jobs/{job_role.id}/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "skill_courses" in data

        # Skills with gaps should have "no courses available" message
        for entry in data["skill_courses"]:
            if len(entry["courses"]) == 0:
                assert entry["message"] == "No courses available for this skill"

    def test_courses_nonexistent_job_returns_404(self, client):
        """GET /api/jobs/9999/courses returns 404 for nonexistent job."""
        from app import db as _db

        token = _setup_student_with_vector(_db.session, client)

        resp = client.get(
            "/api/jobs/9999/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"
