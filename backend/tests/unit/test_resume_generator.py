"""Unit tests for the ResumeGenerator service.

Covers profile validation, PDF generation, and download filename
formatting.
"""

import json
from datetime import date
from unittest.mock import patch

import pytest

from app import db
from app.models import User, StudentProfile, Project, Certification
from app.services.resume_generator import ResumeGenerator


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _create_user(db_session, **overrides):
    """Insert a minimal User row and return it."""
    defaults = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "1234567890",
        "password_hash": "fakehash",
        "role": "student",
        "status": "active",
    }
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    return user


def _create_full_profile(db_session, user):
    """Create a complete StudentProfile with projects and certifications."""
    profile = StudentProfile(
        user_id=user.id,
        institution="Test University",
        degree="B.Tech",
        branch="Computer Science",
        cgpa=8.5,
        graduation_year=2025,
        skills_json=json.dumps(["Python", "JavaScript", "SQL"]),
    )
    db_session.add(profile)
    db_session.flush()

    project = Project(
        profile_id=profile.id,
        title="Sample Project",
        description="A test project for unit testing",
        technologies="Python, Flask",
    )
    db_session.add(project)

    cert = Certification(
        profile_id=profile.id,
        name="AWS Cloud Practitioner",
        issuer="Amazon",
        issue_date=date(2024, 1, 15),
    )
    db_session.add(cert)

    db_session.commit()
    return profile


def _create_incomplete_profile(db_session, user, **overrides):
    """Create a StudentProfile missing some fields."""
    defaults = {
        "user_id": user.id,
        "institution": None,
        "degree": None,
        "branch": None,
        "cgpa": None,
        "graduation_year": None,
        "skills_json": None,
    }
    defaults.update(overrides)
    profile = StudentProfile(**defaults)
    db_session.add(profile)
    db_session.commit()
    return profile


# -----------------------------------------------------------------------
# validate_profile — complete profile
# -----------------------------------------------------------------------

class TestValidateProfileComplete:
    def test_complete_profile_is_valid(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "institution": "Test University",
            "degree": "B.Tech",
            "skills_json": json.dumps(["Python", "JavaScript"]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is True
        assert missing == []

    def test_complete_profile_with_skills_as_list(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "institution": "Test University",
            "degree": "B.Tech",
            "skills_json": ["Python", "JavaScript"],
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is True
        assert missing == []


# -----------------------------------------------------------------------
# validate_profile — missing fields
# -----------------------------------------------------------------------

class TestValidateProfileMissing:
    def test_missing_name(self):
        gen = ResumeGenerator()
        profile = {
            "institution": "Test University",
            "degree": "B.Tech",
            "skills_json": json.dumps(["Python"]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "name" in missing

    def test_missing_institution(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "degree": "B.Tech",
            "skills_json": json.dumps(["Python"]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "institution" in missing

    def test_missing_degree(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "institution": "Test University",
            "skills_json": json.dumps(["Python"]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "degree" in missing

    def test_missing_skills(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "institution": "Test University",
            "degree": "B.Tech",
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "skills" in missing

    def test_empty_skills_json(self):
        gen = ResumeGenerator()
        profile = {
            "name": "Jane Doe",
            "institution": "Test University",
            "degree": "B.Tech",
            "skills_json": json.dumps([]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "skills" in missing

    def test_multiple_missing_fields(self):
        gen = ResumeGenerator()
        profile = {}

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "name" in missing
        assert "institution" in missing
        assert "degree" in missing
        assert "skills" in missing
        assert len(missing) == 4

    def test_empty_string_name(self):
        gen = ResumeGenerator()
        profile = {
            "name": "   ",
            "institution": "Test University",
            "degree": "B.Tech",
            "skills_json": json.dumps(["Python"]),
        }

        valid, missing = gen.validate_profile(profile)

        assert valid is False
        assert "name" in missing


# -----------------------------------------------------------------------
# generate_resume — complete profile produces PDF
# -----------------------------------------------------------------------

class TestGenerateResume:
    def test_generate_resume_returns_pdf_bytes(self, app, db_session):
        user = _create_user(db_session)
        _create_full_profile(db_session, user)

        gen = ResumeGenerator()
        pdf_bytes = gen.generate_resume(user.id)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 100

    def test_generate_resume_with_incomplete_profile_raises(self, app, db_session):
        user = _create_user(db_session)
        _create_incomplete_profile(db_session, user)

        gen = ResumeGenerator()

        with pytest.raises(ValueError, match="missing required fields"):
            gen.generate_resume(user.id)

    def test_generate_resume_no_profile_raises(self, app, db_session):
        user = _create_user(db_session)

        gen = ResumeGenerator()

        with pytest.raises(ValueError, match="Student profile not found"):
            gen.generate_resume(user.id)

    def test_generate_resume_missing_skills_raises(self, app, db_session):
        user = _create_user(db_session)
        _create_incomplete_profile(
            db_session,
            user,
            institution="Test University",
            degree="B.Tech",
            skills_json=None,
        )

        gen = ResumeGenerator()

        with pytest.raises(ValueError, match="missing required fields"):
            gen.generate_resume(user.id)

    def test_generate_resume_with_no_projects_or_certs(self, app, db_session):
        user = _create_user(db_session)
        profile = StudentProfile(
            user_id=user.id,
            institution="Test University",
            degree="B.Tech",
            branch="CS",
            cgpa=9.0,
            skills_json=json.dumps(["Python"]),
        )
        db_session.add(profile)
        db_session.commit()

        gen = ResumeGenerator()
        pdf_bytes = gen.generate_resume(user.id)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"


# -----------------------------------------------------------------------
# get_download_filename
# -----------------------------------------------------------------------

class TestGetDownloadFilename:
    def test_filename_format(self):
        gen = ResumeGenerator()
        today = date.today().isoformat()

        filename = gen.get_download_filename("Jane Doe")

        assert filename == f"Resume_Jane_Doe_{today}.pdf"

    def test_filename_replaces_spaces(self):
        gen = ResumeGenerator()

        filename = gen.get_download_filename("John Michael Smith")

        assert "John_Michael_Smith" in filename
        assert " " not in filename

    def test_filename_ends_with_pdf(self):
        gen = ResumeGenerator()

        filename = gen.get_download_filename("Test")

        assert filename.endswith(".pdf")

    def test_filename_starts_with_resume(self):
        gen = ResumeGenerator()

        filename = gen.get_download_filename("Test")

        assert filename.startswith("Resume_")

    @patch("app.services.resume_generator.date")
    def test_filename_uses_current_date(self, mock_date):
        mock_date.today.return_value = date(2025, 6, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        gen = ResumeGenerator()
        filename = gen.get_download_filename("Jane Doe")

        assert "2025-06-15" in filename
