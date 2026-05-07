"""Shared test fixtures for the Skill2Job Placement System.

Provides Flask app, database session, test client, and factory functions
for generating sample StudentProfile and JobRole data.
"""

import sys
import os
import pytest

# Ensure the backend directory is on the Python path so that
# ``from config import ...`` and ``from app import ...`` resolve correctly
# when pytest is executed from the backend/ directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app, db as _db
from app.services.auth_service import _token_blacklist


# ---------------------------------------------------------------------------
# Auto-clear token blacklist between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_token_blacklist():
    """Ensure the token blacklist is empty before and after each test."""
    _token_blacklist.clear()
    yield
    _token_blacklist.clear()


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing.

    The app is created once per test session for efficiency.
    """
    app = create_app("testing")
    yield app


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean database session for each test.

    Creates all tables before the test and drops them afterwards so every
    test starts with a blank database.
    """
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client for making HTTP requests."""
    with app.test_client() as test_client:
        with app.app_context():
            _db.create_all()
            yield test_client
            _db.session.remove()
            _db.drop_all()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_student_profile_factory():
    """Factory function that creates a StudentProfile dict with customizable fields.

    Usage::

        profile = sample_student_profile_factory()
        profile = sample_student_profile_factory(cgpa=9.0, skills=["Python", "Flask"])
    """

    def _factory(**overrides):
        defaults = {
            "institution": "Test University",
            "degree": "B.Tech",
            "branch": "Computer Science",
            "cgpa": 8.5,
            "graduation_year": 2025,
            "skills": ["Python", "JavaScript", "SQL"],
            "projects": [
                {
                    "title": "Sample Project",
                    "description": "A test project for unit testing",
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
        defaults.update(overrides)
        return defaults

    return _factory


@pytest.fixture()
def sample_job_role_factory():
    """Factory function that creates a JobRole dict with customizable fields.

    Usage::

        job = sample_job_role_factory()
        job = sample_job_role_factory(title="Data Scientist", required_skills=["Python", "ML"])
    """

    def _factory(**overrides):
        defaults = {
            "title": "Software Engineer",
            "description": "Full-stack development role",
            "required_skills": ["Python", "JavaScript", "SQL", "Flask"],
            "cgpa_threshold": 7.0,
            "academic_status": "active",
            "is_active": True,
        }
        defaults.update(overrides)
        return defaults

    return _factory
