"""Unit tests for the StudentProfile service.

Covers profile CRUD, validation, nested projects/certifications,
dream_job/expected_lpa handling, and edge cases.
"""

import json

import pytest

from app import db
from app.models import User, StudentProfile, Project, Certification
from app.services import profile_service


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _create_user(db_session, **overrides):
    """Insert a minimal User row and return it."""
    defaults = {
        "name": "Test Student",
        "email": "student@example.com",
        "password_hash": "fakehash",
        "role": "student",
        "status": "active",
    }
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    return user


def _valid_profile_data(**overrides):
    """Return a valid profile data dict with optional overrides."""
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
    defaults.update(overrides)
    return defaults


# -----------------------------------------------------------------------
# Create new profile
# -----------------------------------------------------------------------

class TestCreateProfile:
    def test_create_new_profile_with_valid_data(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data()

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["user_id"] == user.id
        assert result["institution"] == "Test University"
        assert result["degree"] == "B.Tech"
        assert result["branch"] == "Computer Science"
        assert result["cgpa"] == 8.5
        assert result["graduation_year"] == 2025
        assert json.loads(result["skills_json"]) == ["Python", "JavaScript", "SQL"]
        assert len(result["projects"]) == 1
        assert result["projects"][0]["title"] == "Sample Project"
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "AWS Cloud Practitioner"

    def test_create_profile_without_optional_fields(self, app, db_session):
        user = _create_user(db_session)
        data = {
            "institution": "MIT",
            "degree": "M.Sc",
            "branch": "Physics",
            "cgpa": 9.0,
        }

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["user_id"] == user.id
        assert result["institution"] == "MIT"
        assert result["graduation_year"] is None
        assert result["skills_json"] is None
        assert result["projects"] == []
        assert result["certifications"] == []


# -----------------------------------------------------------------------
# Update existing profile
# -----------------------------------------------------------------------

class TestUpdateProfile:
    def test_update_existing_profile(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data()
        profile_service.create_or_update_profile(user.id, data)

        updated_data = _valid_profile_data(
            institution="Updated University",
            cgpa=9.5,
            skills=["Python", "Go"],
            projects=[{"title": "New Project", "description": "Updated"}],
            certifications=[{"name": "GCP Associate", "issuer": "Google"}],
        )
        result = profile_service.create_or_update_profile(user.id, updated_data)

        assert result["institution"] == "Updated University"
        assert result["cgpa"] == 9.5
        assert json.loads(result["skills_json"]) == ["Python", "Go"]
        assert len(result["projects"]) == 1
        assert result["projects"][0]["title"] == "New Project"
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "GCP Associate"

    def test_update_replaces_projects_and_certifications(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(
            projects=[
                {"title": "Proj A", "description": "A"},
                {"title": "Proj B", "description": "B"},
            ],
            certifications=[
                {"name": "Cert X", "issuer": "X"},
                {"name": "Cert Y", "issuer": "Y"},
            ],
        )
        profile_service.create_or_update_profile(user.id, data)

        # Update with fewer entries — old ones should be gone
        updated = _valid_profile_data(
            projects=[{"title": "Proj C"}],
            certifications=[{"name": "Cert Z"}],
        )
        result = profile_service.create_or_update_profile(user.id, updated)

        assert len(result["projects"]) == 1
        assert result["projects"][0]["title"] == "Proj C"
        assert len(result["certifications"]) == 1
        assert result["certifications"][0]["name"] == "Cert Z"


# -----------------------------------------------------------------------
# Get profile
# -----------------------------------------------------------------------

class TestGetProfile:
    def test_get_existing_profile(self, app, db_session):
        user = _create_user(db_session)
        profile_service.create_or_update_profile(user.id, _valid_profile_data())

        result = profile_service.get_profile(user.id)

        assert result is not None
        assert result["user_id"] == user.id
        assert result["institution"] == "Test University"
        assert len(result["projects"]) == 1
        assert len(result["certifications"]) == 1

    def test_get_nonexistent_profile_returns_none(self, app, db_session):
        result = profile_service.get_profile(99999)
        assert result is None


# -----------------------------------------------------------------------
# Validation: missing required fields
# -----------------------------------------------------------------------

class TestValidationMissingFields:
    @pytest.mark.parametrize("missing_field", ["institution", "degree", "branch", "cgpa"])
    def test_missing_required_field(self, app, db_session, missing_field):
        user = _create_user(db_session)
        data = _valid_profile_data()
        data.pop(missing_field)

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert isinstance(errors, dict)
        assert missing_field in errors

    def test_empty_string_institution(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(institution="   ")

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert "institution" in errors

    def test_multiple_missing_fields(self, app, db_session):
        user = _create_user(db_session)
        data = {"graduation_year": 2025}

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert "institution" in errors
        assert "degree" in errors
        assert "branch" in errors
        assert "cgpa" in errors


# -----------------------------------------------------------------------
# Validation: CGPA out of range
# -----------------------------------------------------------------------

class TestValidationCGPA:
    def test_cgpa_below_zero(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(cgpa=-0.1)

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert "cgpa" in errors

    def test_cgpa_above_ten(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(cgpa=10.1)

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert "cgpa" in errors

    def test_cgpa_non_numeric(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(cgpa="not-a-number")

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert "cgpa" in errors

    def test_cgpa_boundary_zero(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(cgpa=0.0)

        result = profile_service.create_or_update_profile(user.id, data)
        assert result["cgpa"] == 0.0

    def test_cgpa_boundary_ten(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(cgpa=10.0)

        result = profile_service.create_or_update_profile(user.id, data)
        assert result["cgpa"] == 10.0


# -----------------------------------------------------------------------
# Profile with projects and certifications
# -----------------------------------------------------------------------

class TestProfileWithNestedEntries:
    def test_profile_with_multiple_projects(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(
            projects=[
                {"title": "Project 1", "description": "Desc 1", "technologies": "Python"},
                {"title": "Project 2", "description": "Desc 2", "technologies": "Java"},
                {"title": "Project 3", "description": "Desc 3", "technologies": "Go"},
            ]
        )

        result = profile_service.create_or_update_profile(user.id, data)

        assert len(result["projects"]) == 3
        titles = [p["title"] for p in result["projects"]]
        assert "Project 1" in titles
        assert "Project 2" in titles
        assert "Project 3" in titles

    def test_profile_with_multiple_certifications(self, app, db_session):
        user = _create_user(db_session)
        data = _valid_profile_data(
            certifications=[
                {"name": "Cert A", "issuer": "Org A", "issue_date": "2024-01-01"},
                {"name": "Cert B", "issuer": "Org B"},
            ]
        )

        result = profile_service.create_or_update_profile(user.id, data)

        assert len(result["certifications"]) == 2
        names = [c["name"] for c in result["certifications"]]
        assert "Cert A" in names
        assert "Cert B" in names


# -----------------------------------------------------------------------
# Add project to existing profile
# -----------------------------------------------------------------------

class TestAddProject:
    def test_add_project_to_existing_profile(self, app, db_session):
        user = _create_user(db_session)
        profile_service.create_or_update_profile(user.id, _valid_profile_data())
        profile = StudentProfile.query.filter_by(user_id=user.id).first()

        result = profile_service.add_project(
            profile.id,
            {"title": "Extra Project", "description": "Added later", "technologies": "Rust"},
        )

        assert result["title"] == "Extra Project"
        assert result["description"] == "Added later"
        assert result["technologies"] == "Rust"
        assert result["profile_id"] == profile.id

    def test_add_project_to_nonexistent_profile(self, app, db_session):
        with pytest.raises(ValueError, match="Profile not found"):
            profile_service.add_project(99999, {"title": "Orphan"})

    def test_add_project_missing_title(self, app, db_session):
        user = _create_user(db_session)
        profile_service.create_or_update_profile(user.id, _valid_profile_data())
        profile = StudentProfile.query.filter_by(user_id=user.id).first()

        with pytest.raises(ValueError):
            profile_service.add_project(profile.id, {"description": "No title"})


# -----------------------------------------------------------------------
# Add certification to existing profile
# -----------------------------------------------------------------------

class TestAddCertification:
    def test_add_certification_to_existing_profile(self, app, db_session):
        user = _create_user(db_session)
        profile_service.create_or_update_profile(user.id, _valid_profile_data())
        profile = StudentProfile.query.filter_by(user_id=user.id).first()

        result = profile_service.add_certification(
            profile.id,
            {"name": "Extra Cert", "issuer": "TestOrg", "issue_date": "2024-06-01"},
        )

        assert result["name"] == "Extra Cert"
        assert result["issuer"] == "TestOrg"
        assert result["issue_date"] == "2024-06-01"
        assert result["profile_id"] == profile.id

    def test_add_certification_to_nonexistent_profile(self, app, db_session):
        with pytest.raises(ValueError, match="Profile not found"):
            profile_service.add_certification(99999, {"name": "Orphan Cert"})

    def test_add_certification_missing_name(self, app, db_session):
        user = _create_user(db_session)
        profile_service.create_or_update_profile(user.id, _valid_profile_data())
        profile = StudentProfile.query.filter_by(user_id=user.id).first()

        with pytest.raises(ValueError):
            profile_service.add_certification(profile.id, {"issuer": "No name"})


# -----------------------------------------------------------------------
# Validation: dream_job field
# -----------------------------------------------------------------------

class TestDreamJobValidation:
    def test_dream_job_whitespace_stripped(self, app, db_session):
        """Requirement 1.1: leading/trailing whitespace is stripped."""
        user = _create_user(db_session)
        data = _valid_profile_data(dream_job="  Full Stack Developer  ")

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["dream_job"] == "Full Stack Developer"

    def test_dream_job_max_length_enforced(self, app, db_session):
        """Requirement 1.1: max 150 characters enforced (truncated)."""
        user = _create_user(db_session)
        long_job = "A" * 200
        data = _valid_profile_data(dream_job=long_job)

        result = profile_service.create_or_update_profile(user.id, data)

        assert len(result["dream_job"]) == 150

    def test_dream_job_exactly_150_chars_accepted(self, app, db_session):
        """Boundary: exactly 150 characters is accepted without truncation."""
        user = _create_user(db_session)
        exact_job = "B" * 150
        data = _valid_profile_data(dream_job=exact_job)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["dream_job"] == exact_job
        assert len(result["dream_job"]) == 150

    def test_dream_job_none_stores_none(self, app, db_session):
        """dream_job can be explicitly set to None."""
        user = _create_user(db_session)
        data = _valid_profile_data(dream_job=None)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["dream_job"] is None

    def test_dream_job_empty_string_stores_empty(self, app, db_session):
        """dream_job can be set to empty string (stripped)."""
        user = _create_user(db_session)
        data = _valid_profile_data(dream_job="   ")

        result = profile_service.create_or_update_profile(user.id, data)

        # After stripping whitespace, empty string is stored
        assert result["dream_job"] == ""

    def test_omitting_dream_job_preserves_existing(self, app, db_session):
        """Requirement 1.4: omitting dream_job does not overwrite existing value."""
        user = _create_user(db_session)
        # First, set dream_job
        data = _valid_profile_data(dream_job="Data Scientist")
        profile_service.create_or_update_profile(user.id, data)

        # Update without dream_job key
        update_data = _valid_profile_data()
        # Ensure dream_job key is NOT in the update payload
        update_data.pop("dream_job", None)
        result = profile_service.create_or_update_profile(user.id, update_data)

        assert result["dream_job"] == "Data Scientist"


# -----------------------------------------------------------------------
# Validation: expected_lpa field
# -----------------------------------------------------------------------

class TestExpectedLpaValidation:
    def test_expected_lpa_valid_value_accepted(self, app, db_session):
        """Requirement 1.2: valid float in [0.0, 100.0] is accepted."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=8.5)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["expected_lpa"] == 8.5

    def test_expected_lpa_zero_accepted(self, app, db_session):
        """Boundary: 0.0 is valid."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=0.0)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["expected_lpa"] == 0.0

    def test_expected_lpa_hundred_accepted(self, app, db_session):
        """Boundary: 100.0 is valid."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=100.0)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["expected_lpa"] == 100.0

    def test_expected_lpa_negative_rejected(self, app, db_session):
        """Requirement 1.3: negative value rejected with field-level error."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=-1.0)

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert isinstance(errors, dict)
        assert "expected_lpa" in errors

    def test_expected_lpa_above_hundred_rejected(self, app, db_session):
        """Requirement 1.3: value > 100.0 rejected with field-level error."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=100.1)

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert isinstance(errors, dict)
        assert "expected_lpa" in errors

    def test_expected_lpa_non_numeric_rejected(self, app, db_session):
        """Requirement 1.2: non-numeric value rejected with field-level error."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa="not-a-number")

        with pytest.raises(ValueError) as exc_info:
            profile_service.create_or_update_profile(user.id, data)

        errors = exc_info.value.args[0]
        assert isinstance(errors, dict)
        assert "expected_lpa" in errors

    def test_expected_lpa_none_stores_none(self, app, db_session):
        """expected_lpa can be explicitly set to None."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa=None)

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["expected_lpa"] is None

    def test_omitting_expected_lpa_preserves_existing(self, app, db_session):
        """Requirement 1.4: omitting expected_lpa does not overwrite existing value."""
        user = _create_user(db_session)
        # First, set expected_lpa
        data = _valid_profile_data(expected_lpa=12.0)
        profile_service.create_or_update_profile(user.id, data)

        # Update without expected_lpa key
        update_data = _valid_profile_data()
        update_data.pop("expected_lpa", None)
        result = profile_service.create_or_update_profile(user.id, update_data)

        assert result["expected_lpa"] == 12.0

    def test_expected_lpa_string_numeric_accepted(self, app, db_session):
        """String that can be converted to float is accepted."""
        user = _create_user(db_session)
        data = _valid_profile_data(expected_lpa="15.5")

        result = profile_service.create_or_update_profile(user.id, data)

        assert result["expected_lpa"] == 15.5
