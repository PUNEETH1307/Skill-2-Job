"""Unit tests for SQLAlchemy models."""

import pytest
from datetime import date

from app.models import (
    User,
    StudentProfile,
    Project,
    Certification,
    Company,
    JobRole,
    Shortlist,
    SkillTaxonomy,
    UncategorizedSkill,
    CourseRecommendation,
    PlacementRecord,
)


@pytest.mark.unit
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db_session):
        user = User(name="Alice", email="alice@example.com", password_hash="hashed", role="student", status="active")
        db_session.add(user)
        db_session.commit()

        fetched = User.query.filter_by(email="alice@example.com").first()
        assert fetched is not None
        assert fetched.name == "Alice"
        assert fetched.role == "student"

    def test_user_email_unique(self, db_session):
        u1 = User(name="A", email="dup@example.com", password_hash="h1", role="student", status="active")
        u2 = User(name="B", email="dup@example.com", password_hash="h2", role="admin", status="active")
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_to_dict(self, db_session):
        user = User(name="Bob", email="bob@example.com", password_hash="hashed", role="admin", status="active")
        db_session.add(user)
        db_session.commit()

        d = user.to_dict()
        assert d["name"] == "Bob"
        assert d["email"] == "bob@example.com"
        assert d["role"] == "admin"
        assert "password_hash" not in d

    def test_user_repr(self, db_session):
        user = User(name="C", email="c@example.com", password_hash="h", role="student", status="active")
        db_session.add(user)
        db_session.commit()
        assert "c@example.com" in repr(user)


@pytest.mark.unit
class TestStudentProfileModel:
    """Tests for the StudentProfile model."""

    def _create_user(self, db_session, email="student@example.com"):
        user = User(name="Student", email=email, password_hash="h", role="student", status="active")
        db_session.add(user)
        db_session.commit()
        return user

    def test_create_profile(self, db_session):
        user = self._create_user(db_session)
        profile = StudentProfile(
            user_id=user.id, institution="MIT", degree="B.Tech",
            branch="CS", cgpa=9.0, graduation_year=2025,
        )
        db_session.add(profile)
        db_session.commit()

        assert profile.id is not None
        assert profile.user_id == user.id

    def test_user_profile_relationship(self, db_session):
        user = self._create_user(db_session)
        profile = StudentProfile(user_id=user.id, institution="MIT", degree="B.Tech", branch="CS", cgpa=8.5)
        db_session.add(profile)
        db_session.commit()

        assert user.profile is not None
        assert user.profile.id == profile.id
        assert profile.user.id == user.id

    def test_profile_with_projects_and_certs(self, db_session):
        user = self._create_user(db_session)
        profile = StudentProfile(user_id=user.id, institution="MIT", degree="B.Tech", branch="CS", cgpa=8.0)
        db_session.add(profile)
        db_session.commit()

        project = Project(profile_id=profile.id, title="My Project", description="Desc", technologies="Python, Flask")
        cert = Certification(profile_id=profile.id, name="AWS", issuer="Amazon", issue_date=date(2024, 1, 15))
        db_session.add_all([project, cert])
        db_session.commit()

        d = profile.to_dict()
        assert len(d["projects"]) == 1
        assert len(d["certifications"]) == 1
        assert d["projects"][0]["title"] == "My Project"
        assert d["certifications"][0]["name"] == "AWS"


@pytest.mark.unit
class TestCompanyAndJobRoleModels:
    """Tests for Company and JobRole models."""

    def test_create_company_with_job_roles(self, db_session):
        company = Company(name="TechCorp", industry="IT", location="NYC", contact_email="hr@tech.com")
        db_session.add(company)
        db_session.commit()

        job = JobRole(
            company_id=company.id, title="SWE", description="Dev role",
            required_skills_json='["Python", "Flask"]', is_active=True, cgpa_threshold=7.0,
        )
        db_session.add(job)
        db_session.commit()

        assert len(company.job_roles) == 1
        assert job.company.name == "TechCorp"

    def test_job_role_to_dict(self, db_session):
        company = Company(name="Corp", industry="IT", location="LA")
        db_session.add(company)
        db_session.commit()

        job = JobRole(company_id=company.id, title="DE", is_active=False, cgpa_threshold=8.0)
        db_session.add(job)
        db_session.commit()

        d = job.to_dict()
        assert d["title"] == "DE"
        assert d["is_active"] is False
        assert d["cgpa_threshold"] == 8.0


@pytest.mark.unit
class TestShortlistModel:
    """Tests for the Shortlist model."""

    def test_create_shortlist(self, db_session):
        user = User(name="S", email="s@e.com", password_hash="h", role="student", status="active")
        db_session.add(user)
        db_session.commit()

        profile = StudentProfile(user_id=user.id, institution="U", degree="B", branch="C", cgpa=8.0)
        db_session.add(profile)
        db_session.commit()

        company = Company(name="C", industry="I", location="L")
        db_session.add(company)
        db_session.commit()

        job = JobRole(company_id=company.id, title="J", is_active=True)
        db_session.add(job)
        db_session.commit()

        shortlist = Shortlist(profile_id=profile.id, job_role_id=job.id, compatibility_score=0.92, status="shortlisted")
        db_session.add(shortlist)
        db_session.commit()

        d = shortlist.to_dict()
        assert d["compatibility_score"] == 0.92
        assert d["status"] == "shortlisted"


@pytest.mark.unit
class TestSkillTaxonomyModel:
    """Tests for the SkillTaxonomy model."""

    def test_create_skill(self, db_session):
        skill = SkillTaxonomy(canonical_name="Python", category="Programming Languages", synonyms_json='["py", "python3"]')
        db_session.add(skill)
        db_session.commit()

        fetched = SkillTaxonomy.query.filter_by(canonical_name="Python").first()
        assert fetched is not None
        assert fetched.is_deprecated is False

    def test_canonical_name_unique(self, db_session):
        s1 = SkillTaxonomy(canonical_name="React", category="Frameworks")
        s2 = SkillTaxonomy(canonical_name="React", category="Libraries")
        db_session.add(s1)
        db_session.commit()
        db_session.add(s2)
        with pytest.raises(Exception):
            db_session.commit()


@pytest.mark.unit
class TestPlacementRecordModel:
    """Tests for the PlacementRecord model."""

    def test_create_placement_record(self, db_session):
        user = User(name="P", email="p@e.com", password_hash="h", role="student", status="active")
        db_session.add(user)
        db_session.commit()

        profile = StudentProfile(user_id=user.id, institution="U", degree="B", branch="C", cgpa=8.0)
        db_session.add(profile)
        db_session.commit()

        company = Company(name="BigCo", industry="Tech", location="SF")
        db_session.add(company)
        db_session.commit()

        job = JobRole(company_id=company.id, title="Eng", is_active=True)
        db_session.add(job)
        db_session.commit()

        record = PlacementRecord(
            profile_id=profile.id, job_role_id=job.id, company_id=company.id,
            placement_date=date(2025, 6, 1), department="Engineering",
        )
        db_session.add(record)
        db_session.commit()

        d = record.to_dict()
        assert d["department"] == "Engineering"
        assert d["placement_date"] == "2025-06-01"
        assert record.profile.id == profile.id
        assert record.company.name == "BigCo"


@pytest.mark.unit
class TestCourseRecommendationModel:
    """Tests for the CourseRecommendation model."""

    def test_create_course(self, db_session):
        course = CourseRecommendation(
            skill_name="Docker", course_name="Docker Mastery",
            provider="Udemy", url="https://udemy.com/docker",
        )
        db_session.add(course)
        db_session.commit()

        d = course.to_dict()
        assert d["skill_name"] == "Docker"
        assert d["provider"] == "Udemy"


@pytest.mark.unit
class TestUncategorizedSkillModel:
    """Tests for the UncategorizedSkill model."""

    def test_create_uncategorized_skill(self, db_session):
        skill = UncategorizedSkill(term="golang", occurrence_count=5)
        db_session.add(skill)
        db_session.commit()

        d = skill.to_dict()
        assert d["term"] == "golang"
        assert d["occurrence_count"] == 5
        assert d["reviewed"] is False
