"""Unit tests for the DashboardService.

Covers get_student_summary with various profile states:
no profile, fully complete, partial, skills but no jobs, etc.
Also covers get_coordinator_summary and get_admin_summary.

Requirements: 1.1, 1.5, 1.6, 4.1, 4.2, 5.2, 7.1, 7.2
"""

import json
from datetime import datetime, timezone, timedelta

import pytest

from app import db
from app.models import (
    User,
    StudentProfile,
    JobRole,
    Company,
    Project,
    Certification,
    Shortlist,
    SkillTaxonomy,
    UncategorizedSkill,
)
from app.services.dashboard_service import DashboardService


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


def _create_profile(db_session, user_id, **overrides):
    """Insert a StudentProfile row and return it."""
    defaults = {
        "user_id": user_id,
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


def _create_company(db_session, name="TechCorp"):
    """Insert a Company row and return it."""
    company = Company(name=name)
    db_session.add(company)
    db_session.commit()
    return company


def _create_job_role(db_session, company_id, **overrides):
    """Insert a JobRole row and return it."""
    defaults = {
        "company_id": company_id,
        "title": "Software Engineer",
        "is_active": True,
        "cgpa_threshold": 7.0,
        "job_vector_json": json.dumps({"vector": [1.0, 0.0], "skill_index": {"python": 0}, "version": "1.0"}),
    }
    defaults.update(overrides)
    job = JobRole(**defaults)
    db_session.add(job)
    db_session.commit()
    return job


def _seed_taxonomy(db_session):
    """Seed basic skill taxonomy entries for categorization tests."""
    skills = [
        SkillTaxonomy(canonical_name="Python", category="Programming Languages"),
        SkillTaxonomy(canonical_name="JavaScript", category="Programming Languages"),
        SkillTaxonomy(canonical_name="Flask", category="Frameworks"),
        SkillTaxonomy(canonical_name="SQL", category="Databases"),
    ]
    for s in skills:
        db_session.add(s)
    db_session.commit()
    return skills


# -----------------------------------------------------------------------
# Tests: get_student_summary – no profile
# -----------------------------------------------------------------------

class TestStudentSummaryNoProfile:
    def test_no_profile_returns_zeroed_response(self, app, db_session):
        """Student with no profile gets completeness 0, empty skills, zero counts."""
        user = _create_user(db_session)
        service = DashboardService()

        result = service.get_student_summary(user.id)

        assert result["profile_completeness"] == 0
        assert result["skill_count"] == 0
        assert result["skill_breakdown"] == {}
        assert result["matched_job_count"] == 0
        assert result["top_recommendations"] == []

    def test_nonexistent_user_returns_zeroed_response(self, app, db_session):
        """Non-existent user ID returns zeroed-out response."""
        service = DashboardService()

        result = service.get_student_summary(99999)

        assert result["profile_completeness"] == 0
        assert result["skill_count"] == 0
        assert result["skill_breakdown"] == {}
        assert result["matched_job_count"] == 0
        assert result["top_recommendations"] == []


# -----------------------------------------------------------------------
# Tests: get_student_summary – profile completeness
# -----------------------------------------------------------------------

class TestStudentSummaryProfileCompleteness:
    def test_fully_complete_profile(self, app, db_session):
        """Profile with all 8 fields filled → 100%."""
        user = _create_user(db_session)
        profile = _create_profile(
            db_session,
            user.id,
            institution="MIT",
            degree="B.Tech",
            branch="CS",
            cgpa=9.0,
            graduation_year=2025,
            skills_json=json.dumps(["Python"]),
        )
        # Add project and certification
        project = Project(profile_id=profile.id, title="My Project")
        cert = Certification(profile_id=profile.id, name="AWS Cert")
        db_session.add_all([project, cert])
        db_session.commit()

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["profile_completeness"] == 100

    def test_partial_profile_correct_percentage(self, app, db_session):
        """Profile with 4 of 8 fields filled → 50%."""
        user = _create_user(db_session)
        _create_profile(
            db_session,
            user.id,
            institution="MIT",
            degree="B.Tech",
            branch="CS",
            cgpa=8.0,
        )

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["profile_completeness"] == 50

    def test_empty_profile_zero_completeness(self, app, db_session):
        """Profile with no fields filled → 0%."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id)

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["profile_completeness"] == 0


# -----------------------------------------------------------------------
# Tests: get_student_summary – skills
# -----------------------------------------------------------------------

class TestStudentSummarySkills:
    def test_skill_count_from_skills_json(self, app, db_session):
        """Skill count matches the number of skills in skills_json."""
        _seed_taxonomy(db_session)
        user = _create_user(db_session)
        _create_profile(
            db_session,
            user.id,
            skills_json=json.dumps(["Python", "JavaScript", "SQL"]),
        )

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["skill_count"] == 3

    def test_skill_breakdown_categories(self, app, db_session):
        """Skill breakdown groups skills by taxonomy category."""
        _seed_taxonomy(db_session)
        user = _create_user(db_session)
        _create_profile(
            db_session,
            user.id,
            skills_json=json.dumps(["Python", "JavaScript", "Flask", "SQL"]),
        )

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["skill_breakdown"]["Programming Languages"] == 2
        assert result["skill_breakdown"]["Frameworks"] == 1
        assert result["skill_breakdown"]["Databases"] == 1

    def test_no_skills_empty_breakdown(self, app, db_session):
        """Profile with no skills_json → empty breakdown."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id)

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["skill_count"] == 0
        assert result["skill_breakdown"] == {}


# -----------------------------------------------------------------------
# Tests: get_student_summary – matched job count
# -----------------------------------------------------------------------

class TestStudentSummaryMatchedJobs:
    def test_matched_job_count_with_eligible_jobs(self, app, db_session):
        """Student with CGPA 8.5 matches jobs with threshold <= 8.5."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id, cgpa=8.5)
        company = _create_company(db_session)
        _create_job_role(db_session, company.id, cgpa_threshold=7.0)
        _create_job_role(db_session, company.id, title="Data Analyst", cgpa_threshold=8.0)
        _create_job_role(db_session, company.id, title="Senior Dev", cgpa_threshold=9.0)

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["matched_job_count"] == 2

    def test_no_active_jobs_zero_count(self, app, db_session):
        """No active job roles → matched_job_count is 0."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id, cgpa=8.5)
        company = _create_company(db_session)
        _create_job_role(db_session, company.id, is_active=False)

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["matched_job_count"] == 0

    def test_jobs_without_vector_not_counted(self, app, db_session):
        """Jobs without job_vector_json are not counted."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id, cgpa=8.5)
        company = _create_company(db_session)
        _create_job_role(db_session, company.id, job_vector_json=None)

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["matched_job_count"] == 0

    def test_skills_but_no_active_jobs(self, app, db_session):
        """Student with skills but no active job roles → matched_job_count 0."""
        _seed_taxonomy(db_session)
        user = _create_user(db_session)
        _create_profile(
            db_session,
            user.id,
            cgpa=9.0,
            skills_json=json.dumps(["Python", "JavaScript"]),
        )

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert result["matched_job_count"] == 0
        assert result["skill_count"] == 2


# -----------------------------------------------------------------------
# Tests: get_student_summary – response shape
# -----------------------------------------------------------------------

class TestStudentSummaryResponseShape:
    def test_response_has_all_required_keys(self, app, db_session):
        """Response always contains all required keys."""
        user = _create_user(db_session)
        service = DashboardService()

        result = service.get_student_summary(user.id)

        assert "profile_completeness" in result
        assert "skill_count" in result
        assert "skill_breakdown" in result
        assert "matched_job_count" in result
        assert "top_recommendations" in result

    def test_profile_completeness_is_integer(self, app, db_session):
        """profile_completeness is always an integer."""
        user = _create_user(db_session)
        _create_profile(db_session, user.id, institution="MIT")

        service = DashboardService()
        result = service.get_student_summary(user.id)

        assert isinstance(result["profile_completeness"], int)


# -----------------------------------------------------------------------
# Tests: get_coordinator_summary – no shortlists
# -----------------------------------------------------------------------

class TestCoordinatorSummaryNoShortlists:
    def test_no_shortlists_returns_empty_recent_list(self, app, db_session):
        """Coordinator summary with no shortlists → empty recent_shortlists."""
        service = DashboardService()

        result = service.get_coordinator_summary()

        assert result["recent_shortlists"] == []
        assert result["shortlisted_count"] == 0

    def test_no_shortlists_active_jobs_still_counted(self, app, db_session):
        """Active jobs are counted even when no shortlists exist."""
        company = _create_company(db_session)
        _create_job_role(db_session, company.id, is_active=True)
        _create_job_role(db_session, company.id, title="Data Analyst", is_active=True)

        service = DashboardService()
        result = service.get_coordinator_summary()

        assert result["active_job_count"] == 2
        assert result["shortlisted_count"] == 0
        assert result["recent_shortlists"] == []

    def test_no_data_placement_overview_zeros(self, app, db_session):
        """With no data, placement overview returns zeros."""
        service = DashboardService()
        result = service.get_coordinator_summary()

        assert result["placement_overview"]["total_students"] == 0
        assert result["placement_overview"]["placed_students"] == 0
        assert result["placement_overview"]["total_companies"] == 0
        assert result["placement_overview"]["placement_percentage"] == 0.0


# -----------------------------------------------------------------------
# Tests: get_coordinator_summary – with shortlists
# -----------------------------------------------------------------------

class TestCoordinatorSummaryWithShortlists:
    def test_shortlisted_count_matches_records(self, app, db_session):
        """shortlisted_count equals total number of Shortlist records."""
        user1 = _create_user(db_session, email="s1@example.com", name="Alice")
        user2 = _create_user(db_session, email="s2@example.com", name="Bob")
        profile1 = _create_profile(db_session, user1.id)
        profile2 = _create_profile(db_session, user2.id)
        company = _create_company(db_session)
        job = _create_job_role(db_session, company.id)

        s1 = Shortlist(
            profile_id=profile1.id,
            job_role_id=job.id,
            compatibility_score=85.0,
            shortlisted_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )
        s2 = Shortlist(
            profile_id=profile2.id,
            job_role_id=job.id,
            compatibility_score=90.0,
            shortlisted_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        db_session.add_all([s1, s2])
        db_session.commit()

        service = DashboardService()
        result = service.get_coordinator_summary()

        assert result["shortlisted_count"] == 2

    def test_recent_shortlists_ordering(self, app, db_session):
        """recent_shortlists are sorted by shortlisted_at descending (most recent first)."""
        user1 = _create_user(db_session, email="s1@example.com", name="Alice")
        user2 = _create_user(db_session, email="s2@example.com", name="Bob")
        profile1 = _create_profile(db_session, user1.id)
        profile2 = _create_profile(db_session, user2.id)
        company = _create_company(db_session)
        job = _create_job_role(db_session, company.id)

        # Older shortlist
        s1 = Shortlist(
            profile_id=profile1.id,
            job_role_id=job.id,
            compatibility_score=85.0,
            shortlisted_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )
        # Newer shortlist
        s2 = Shortlist(
            profile_id=profile2.id,
            job_role_id=job.id,
            compatibility_score=90.0,
            shortlisted_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        db_session.add_all([s1, s2])
        db_session.commit()

        service = DashboardService()
        result = service.get_coordinator_summary()

        recent = result["recent_shortlists"]
        assert len(recent) == 2
        # Most recent first
        assert recent[0]["student_name"] == "Bob"
        assert recent[0]["compatibility_score"] == 90.0
        assert recent[1]["student_name"] == "Alice"
        assert recent[1]["compatibility_score"] == 85.0

    def test_recent_shortlists_limited_to_five(self, app, db_session):
        """recent_shortlists returns at most 5 records."""
        company = _create_company(db_session)
        job = _create_job_role(db_session, company.id)

        for i in range(7):
            user = _create_user(db_session, email=f"s{i}@example.com", name=f"Student{i}")
            profile = _create_profile(db_session, user.id)
            shortlist = Shortlist(
                profile_id=profile.id,
                job_role_id=job.id,
                compatibility_score=70.0 + i,
                shortlisted_at=datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
            )
            db_session.add(shortlist)
        db_session.commit()

        service = DashboardService()
        result = service.get_coordinator_summary()

        assert len(result["recent_shortlists"]) == 5
        assert result["shortlisted_count"] == 7

    def test_recent_shortlists_contain_expected_fields(self, app, db_session):
        """Each recent shortlist entry has student_name, job_title, company_name, compatibility_score, shortlisted_at."""
        user = _create_user(db_session, name="Alice")
        profile = _create_profile(db_session, user.id)
        company = _create_company(db_session, name="TechCorp")
        job = _create_job_role(db_session, company.id, title="Backend Dev")

        shortlist = Shortlist(
            profile_id=profile.id,
            job_role_id=job.id,
            compatibility_score=88.5,
            shortlisted_at=datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc),
        )
        db_session.add(shortlist)
        db_session.commit()

        service = DashboardService()
        result = service.get_coordinator_summary()

        recent = result["recent_shortlists"]
        assert len(recent) == 1
        entry = recent[0]
        assert entry["student_name"] == "Alice"
        assert entry["job_title"] == "Backend Dev"
        assert entry["company_name"] == "TechCorp"
        assert entry["compatibility_score"] == 88.5
        assert entry["shortlisted_at"] is not None


# -----------------------------------------------------------------------
# Tests: get_admin_summary – no users
# -----------------------------------------------------------------------

class TestAdminSummaryNoUsers:
    def test_no_users_all_counts_zero(self, app, db_session):
        """Admin summary with no users → all counts zero."""
        service = DashboardService()

        result = service.get_admin_summary()

        assert result["user_counts"]["by_role"] == {}
        assert result["user_counts"]["by_status"] == {}
        assert result["user_counts"]["total"] == 0

    def test_no_users_taxonomy_health_zeros(self, app, db_session):
        """Admin summary with no taxonomy data → all taxonomy counts zero."""
        service = DashboardService()

        result = service.get_admin_summary()

        assert result["taxonomy_health"]["total_skills"] == 0
        assert result["taxonomy_health"]["deprecated_skills"] == 0
        assert result["taxonomy_health"]["uncategorized_pending"] == 0

    def test_no_users_placement_overview_zeros(self, app, db_session):
        """Admin summary with no data → placement overview zeros."""
        service = DashboardService()

        result = service.get_admin_summary()

        assert result["placement_overview"]["total_students"] == 0
        assert result["placement_overview"]["placed_students"] == 0
        assert result["placement_overview"]["total_companies"] == 0
        assert result["placement_overview"]["placement_percentage"] == 0.0


# -----------------------------------------------------------------------
# Tests: get_admin_summary – mixed users
# -----------------------------------------------------------------------

class TestAdminSummaryMixedUsers:
    def test_user_counts_by_role(self, app, db_session):
        """User counts grouped by role are correct."""
        _create_user(db_session, email="s1@example.com", role="student")
        _create_user(db_session, email="s2@example.com", role="student")
        _create_user(db_session, email="po@example.com", role="placement_officer")
        _create_user(db_session, email="admin@example.com", role="admin")

        service = DashboardService()
        result = service.get_admin_summary()

        assert result["user_counts"]["by_role"]["student"] == 2
        assert result["user_counts"]["by_role"]["placement_officer"] == 1
        assert result["user_counts"]["by_role"]["admin"] == 1

    def test_user_counts_by_status(self, app, db_session):
        """User counts grouped by status are correct."""
        _create_user(db_session, email="s1@example.com", status="active")
        _create_user(db_session, email="s2@example.com", status="active")
        _create_user(db_session, email="s3@example.com", status="inactive")

        service = DashboardService()
        result = service.get_admin_summary()

        assert result["user_counts"]["by_status"]["active"] == 2
        assert result["user_counts"]["by_status"]["inactive"] == 1

    def test_user_counts_total(self, app, db_session):
        """Total user count matches sum of all users."""
        _create_user(db_session, email="s1@example.com", role="student")
        _create_user(db_session, email="s2@example.com", role="student")
        _create_user(db_session, email="po@example.com", role="placement_officer")

        service = DashboardService()
        result = service.get_admin_summary()

        assert result["user_counts"]["total"] == 3

    def test_taxonomy_health_with_mixed_skills(self, app, db_session):
        """Taxonomy health correctly counts active, deprecated, and uncategorized skills."""
        # Active skills
        db_session.add(SkillTaxonomy(canonical_name="Python", category="Programming", is_deprecated=False))
        db_session.add(SkillTaxonomy(canonical_name="JavaScript", category="Programming", is_deprecated=False))
        db_session.add(SkillTaxonomy(canonical_name="Flask", category="Frameworks", is_deprecated=False))
        # Deprecated skill
        db_session.add(SkillTaxonomy(canonical_name="COBOL", category="Legacy", is_deprecated=True))
        # Uncategorized pending review
        db_session.add(UncategorizedSkill(term="NewFramework", reviewed=False))
        db_session.add(UncategorizedSkill(term="AnotherSkill", reviewed=False))
        # Uncategorized already reviewed (should not count)
        db_session.add(UncategorizedSkill(term="ReviewedSkill", reviewed=True))
        db_session.commit()

        service = DashboardService()
        result = service.get_admin_summary()

        assert result["taxonomy_health"]["total_skills"] == 3
        assert result["taxonomy_health"]["deprecated_skills"] == 1
        assert result["taxonomy_health"]["uncategorized_pending"] == 2

    def test_admin_summary_response_has_all_keys(self, app, db_session):
        """Admin summary response contains all required top-level keys."""
        service = DashboardService()
        result = service.get_admin_summary()

        assert "user_counts" in result
        assert "taxonomy_health" in result
        assert "placement_overview" in result
        assert "by_role" in result["user_counts"]
        assert "by_status" in result["user_counts"]
        assert "total" in result["user_counts"]
