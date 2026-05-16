"""Unit tests for the ResumeGenerator service.

Covers profile validation, PDF generation, download filename
formatting, AI-enhanced PDF generation, and AIResumeService integration.
"""

import json
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app import db
from app.models import User, StudentProfile, Project, Certification
from app.services.resume_generator import ResumeGenerator
from app.services.ai_resume_service import AIResumeContent


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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
            "branch": "Computer Science",
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
        assert "branch" in missing
        assert "skills" in missing
        assert len(missing) == 5

    def test_empty_string_name(self):
        gen = ResumeGenerator()
        profile = {
            "name": "   ",
            "institution": "Test University",
            "degree": "B.Tech",
            "branch": "Computer Science",
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

    def test_filename_removes_unsafe_characters(self):
        gen = ResumeGenerator()

        filename = gen.get_download_filename("Jane / Doe <CSE>")

        assert filename.startswith("Resume_Jane_Doe_CSE_")
        assert "/" not in filename
        assert "<" not in filename

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


# -----------------------------------------------------------------------
# _build_pdf_with_ai_content — AI-enhanced PDF generation
# -----------------------------------------------------------------------

class TestBuildPdfWithAiContent:
    """Tests for the _build_pdf_with_ai_content method."""

    def _make_ai_content(self, **overrides):
        """Create a default AIResumeContent for testing."""
        defaults = {
            "career_objective": (
                "Motivated B.Tech graduate in Computer Science seeking a Full Stack Developer "
                "role to apply skills in React, Python, Node.js. Eager to contribute to "
                "innovative projects and grow professionally in a collaborative environment."
            ),
            "professional_summary": (
                "Technically proficient professional with expertise in React, Python, JavaScript "
                "with 2 projects demonstrating practical application maintaining a strong "
                "academic record (CGPA: 8.5). Passionate about Full Stack Developer and "
                "committed to delivering high-quality solutions that drive business value."
            ),
            "prioritized_skills": ["React", "Python", "JavaScript", "SQL"],
            "skill_categories": {
                "Programming Languages": ["Python", "JavaScript"],
                "Web & Frameworks": ["React"],
                "Databases": ["SQL"],
            },
            "project_descriptions": [
                {
                    "title": "E-Commerce App",
                    "description": "Built a full-stack e-commerce application with user auth",
                    "technologies": "React, Node.js",
                    "relevance_note": "Relevant to Full Stack Developer: demonstrates experience with frontend, backend.",
                },
            ],
            "experience_level": "mid",
        }
        defaults.update(overrides)
        return AIResumeContent(**defaults)

    def test_produces_valid_pdf(self, app, db_session):
        """_build_pdf_with_ai_content should produce valid PDF bytes."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content()
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 100

    def test_renders_career_objective(self, app, db_session):
        """PDF should contain the AI-generated career objective text."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content()
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        # PDF is binary but text content is embedded — verify it's non-trivial
        assert len(pdf_bytes) > 500

    def test_renders_with_empty_project_descriptions(self, app, db_session):
        """PDF should render correctly when project_descriptions is empty."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content(project_descriptions=[])
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_renders_with_empty_skill_categories(self, app, db_session):
        """PDF should render correctly when skill_categories is empty."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content(skill_categories={})
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_renders_project_relevance_notes(self, app, db_session):
        """PDF should render without error when projects have relevance notes."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content(
            project_descriptions=[
                {
                    "title": "ML Pipeline",
                    "description": "Built an ML pipeline for data processing",
                    "technologies": "Python, TensorFlow",
                    "relevance_note": "Relevant to Data Scientist: demonstrates ML experience.",
                },
                {
                    "title": "Blog App",
                    "description": "Simple blog application",
                    "technologies": "Flask, SQLite",
                    "relevance_note": "",
                },
            ]
        )
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_renders_certifications_from_profile(self, app, db_session):
        """PDF should include certifications from the profile object."""
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)

        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        ai_content = self._make_ai_content()
        gen = ResumeGenerator()

        pdf_bytes = gen._build_pdf_with_ai_content(profile_dict, profile, ai_content)

        # The profile has a certification, so the PDF should be larger
        assert len(pdf_bytes) > 500


# -----------------------------------------------------------------------
# ResumeGenerator AI integration — conditional AIResumeService invocation
# -----------------------------------------------------------------------

class TestResumeGeneratorAIIntegration:
    """Tests for AIResumeService integration in generate_resume.

    Validates Requirements 8.1, 8.2, 8.3, 9.1:
    - When dream_job is set, AIResumeService is invoked
    - When dream_job is None/empty, AIResumeService is NOT invoked
    - When AIResumeService raises, fallback to template-based generation
    """

    def _make_ai_content(self):
        """Create a mock AIResumeContent for testing."""
        return AIResumeContent(
            career_objective=(
                "Motivated B.Tech graduate in Computer Science seeking a Full Stack Developer "
                "role to apply skills in React, Python, Node.js. Eager to contribute to "
                "innovative projects and grow professionally in a collaborative environment."
            ),
            professional_summary=(
                "Technically proficient professional with expertise in React, Python, JavaScript "
                "with 2 projects demonstrating practical application maintaining a strong "
                "academic record (CGPA: 8.5). Passionate about Full Stack Developer."
            ),
            prioritized_skills=["React", "Python", "JavaScript", "SQL"],
            skill_categories={
                "Programming Languages": ["Python", "JavaScript"],
                "Web & Frameworks": ["React"],
                "Databases": ["SQL"],
            },
            project_descriptions=[
                {
                    "title": "Sample Project",
                    "description": "A test project for unit testing",
                    "technologies": "Python, Flask",
                    "relevance_note": "",
                },
            ],
            experience_level="entry",
        )

    def test_generate_resume_calls_ai_service_when_dream_job_set(self, app, db_session):
        """When dream_job is set, generate_resume should invoke AIResumeService.

        Validates: Requirement 9.1
        """
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)
        profile.dream_job = "Full Stack Developer"
        db_session.commit()

        ai_content = self._make_ai_content()

        with patch("app.services.ai_resume_service.AIResumeService") as MockAIService:
            mock_instance = MagicMock()
            mock_instance.generate_ai_content.return_value = ai_content
            MockAIService.return_value = mock_instance

            gen = ResumeGenerator()
            pdf_bytes = gen.generate_resume(user.id)

            # AIResumeService was instantiated and called
            MockAIService.assert_called_once()
            mock_instance.generate_ai_content.assert_called_once()

            # Still produces valid PDF
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_resume_does_not_call_ai_service_when_dream_job_none(self, app, db_session):
        """When dream_job is None, generate_resume should NOT invoke AIResumeService.

        Validates: Requirement 8.2
        """
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)
        # dream_job is None by default
        assert profile.dream_job is None
        db_session.commit()

        with patch("app.services.ai_resume_service.AIResumeService") as MockAIService:
            gen = ResumeGenerator()
            pdf_bytes = gen.generate_resume(user.id)

            # AIResumeService should NOT be instantiated
            MockAIService.assert_not_called()

            # Still produces valid PDF via template-based generation
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_resume_does_not_call_ai_service_when_dream_job_empty(self, app, db_session):
        """When dream_job is empty string, generate_resume should NOT invoke AIResumeService.

        Validates: Requirement 8.1
        """
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)
        profile.dream_job = "   "
        db_session.commit()

        with patch("app.services.ai_resume_service.AIResumeService") as MockAIService:
            gen = ResumeGenerator()
            pdf_bytes = gen.generate_resume(user.id)

            # AIResumeService should NOT be instantiated for whitespace-only dream_job
            MockAIService.assert_not_called()

            # Still produces valid PDF
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_resume_fallback_when_ai_service_raises(self, app, db_session):
        """When AIResumeService raises an exception, generate_resume falls back to template.

        Validates: Requirement 8.3
        """
        user = _create_user(db_session)
        profile = _create_full_profile(db_session, user)
        profile.dream_job = "Data Scientist"
        db_session.commit()

        with patch("app.services.ai_resume_service.AIResumeService") as MockAIService:
            mock_instance = MagicMock()
            mock_instance.generate_ai_content.side_effect = RuntimeError("AI service failure")
            MockAIService.return_value = mock_instance

            gen = ResumeGenerator()
            pdf_bytes = gen.generate_resume(user.id)

            # AIResumeService was called but raised
            MockAIService.assert_called_once()
            mock_instance.generate_ai_content.assert_called_once()

            # Resume is still generated (fallback to template-based)
            assert isinstance(pdf_bytes, bytes)
            assert pdf_bytes[:5] == b"%PDF-"
            assert len(pdf_bytes) > 100
