"""Smoke tests to verify the testing infrastructure works correctly."""

import pytest
from app import create_app


@pytest.mark.unit
class TestSmoke:
    """Basic smoke tests for app creation and test fixtures."""

    def test_app_creates_successfully(self):
        """The Flask app factory should return a valid app in testing mode."""
        app = create_app("testing")
        assert app is not None
        assert app.config["TESTING"] is True

    def test_app_uses_sqlite_in_memory(self):
        """The testing config should use an in-memory SQLite database."""
        app = create_app("testing")
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"

    def test_client_fixture(self, client):
        """The test client fixture should be usable for HTTP requests."""
        assert client is not None

    def test_db_session_fixture(self, db_session):
        """The db_session fixture should provide a working session."""
        assert db_session is not None

    def test_student_profile_factory(self, sample_student_profile_factory):
        """The student profile factory should produce valid default data."""
        profile = sample_student_profile_factory()
        assert profile["institution"] == "Test University"
        assert profile["cgpa"] == 8.5
        assert len(profile["skills"]) == 3

    def test_student_profile_factory_overrides(self, sample_student_profile_factory):
        """The student profile factory should accept field overrides."""
        profile = sample_student_profile_factory(cgpa=9.5, branch="ECE")
        assert profile["cgpa"] == 9.5
        assert profile["branch"] == "ECE"

    def test_job_role_factory(self, sample_job_role_factory):
        """The job role factory should produce valid default data."""
        job = sample_job_role_factory()
        assert job["title"] == "Software Engineer"
        assert job["cgpa_threshold"] == 7.0
        assert "Python" in job["required_skills"]

    def test_job_role_factory_overrides(self, sample_job_role_factory):
        """The job role factory should accept field overrides."""
        job = sample_job_role_factory(title="Data Scientist", cgpa_threshold=8.0)
        assert job["title"] == "Data Scientist"
        assert job["cgpa_threshold"] == 8.0
