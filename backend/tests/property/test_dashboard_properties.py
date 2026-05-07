"""Property-based tests for the DashboardService.

Uses Hypothesis to verify universal correctness properties across
randomly generated database states.

Location: backend/tests/property/test_dashboard_properties.py
"""

import json

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app import db
from app.models import (
    User,
    StudentProfile,
    Project,
    Certification,
    Shortlist,
)
from app.services.dashboard_service import DashboardService


# -----------------------------------------------------------------------
# Strategies
# -----------------------------------------------------------------------

# Strategy for optional string fields (either None or a non-empty string)
optional_string = st.one_of(st.none(), st.text(min_size=1, max_size=50).filter(lambda s: s.strip()))

# Strategy for optional CGPA (either None or a float in [0, 10])
optional_cgpa = st.one_of(st.none(), st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))

# Strategy for optional graduation year (either None or a reasonable year)
optional_graduation_year = st.one_of(st.none(), st.integers(min_value=2000, max_value=2035))

# Strategy for optional skills_json (either None, empty string, or a JSON list of skill names)
skill_names = st.lists(
    st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
    min_size=0,
    max_size=10,
)
optional_skills_json = st.one_of(
    st.none(),
    st.just(""),
    skill_names.map(lambda skills: json.dumps(skills)),
)

# Strategy for whether to add projects (0 or more)
project_count = st.integers(min_value=0, max_value=3)

# Strategy for whether to add certifications (0 or more)
certification_count = st.integers(min_value=0, max_value=3)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

_user_counter = 0


def _make_user(session):
    """Create a unique User for each test example."""
    global _user_counter
    _user_counter += 1
    user = User(
        name=f"PropTestUser{_user_counter}",
        email=f"proptest{_user_counter}@example.com",
        password_hash="fakehash",
        role="student",
        status="active",
    )
    session.add(user)
    session.flush()
    return user


# -----------------------------------------------------------------------
# Property 1: Profile completeness is bounded
# Feature: role-based-dashboards, Property 1: Profile completeness is bounded
# -----------------------------------------------------------------------


class TestProfileCompletenessBounded:
    """**Validates: Requirements 1.1**

    For any StudentProfile with any combination of filled and empty fields,
    the computed profile_completeness value SHALL be an integer in [0, 100].
    """

    @given(
        institution=optional_string,
        degree=optional_string,
        branch=optional_string,
        cgpa=optional_cgpa,
        graduation_year=optional_graduation_year,
        skills_json=optional_skills_json,
        num_projects=project_count,
        num_certifications=certification_count,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_profile_completeness_is_bounded(
        self,
        app,
        db_session,
        institution,
        degree,
        branch,
        cgpa,
        graduation_year,
        skills_json,
        num_projects,
        num_certifications,
    ):
        """profile_completeness is always an integer in [0, 100] for any
        combination of filled/empty profile fields."""
        user = _make_user(db_session)

        profile = StudentProfile(
            user_id=user.id,
            institution=institution,
            degree=degree,
            branch=branch,
            cgpa=cgpa,
            graduation_year=graduation_year,
            skills_json=skills_json,
        )
        db_session.add(profile)
        db_session.flush()

        # Add projects
        for i in range(num_projects):
            project = Project(profile_id=profile.id, title=f"Project {i}")
            db_session.add(project)

        # Add certifications
        for i in range(num_certifications):
            cert = Certification(profile_id=profile.id, name=f"Cert {i}")
            db_session.add(cert)

        db_session.flush()

        service = DashboardService()
        result = service.get_student_summary(user.id)

        completeness = result["profile_completeness"]

        # Property: completeness is an integer
        assert isinstance(completeness, int), (
            f"Expected int, got {type(completeness).__name__}: {completeness}"
        )

        # Property: completeness is in [0, 100]
        assert 0 <= completeness <= 100, (
            f"Expected 0 <= completeness <= 100, got {completeness}"
        )


# -----------------------------------------------------------------------
# Shared taxonomy data for Property 2
# -----------------------------------------------------------------------

from app.models import SkillTaxonomy
from app.services.skill_analyzer import SkillAnalyzer

# Known skills grouped by category for seeding the taxonomy
_TAXONOMY_SKILLS = {
    "Programming Languages": ["Python", "Java", "JavaScript", "C++", "Go", "Ruby"],
    "Frameworks": ["Flask", "Django", "React", "Angular", "Spring"],
    "Databases": ["MySQL", "PostgreSQL", "MongoDB", "Redis"],
    "Tools": ["Git", "Docker", "Kubernetes", "Jenkins"],
    "Cloud": ["AWS", "Azure", "GCP"],
}

# Flat list of all canonical skill names
_ALL_SKILL_NAMES = [
    name for names in _TAXONOMY_SKILLS.values() for name in names
]

# Strategy: pick a random non-empty subset of known taxonomy skills
taxonomy_skill_subset = st.lists(
    st.sampled_from(_ALL_SKILL_NAMES),
    min_size=1,
    max_size=len(_ALL_SKILL_NAMES),
    unique=True,
)


def _seed_taxonomy(session):
    """Insert the known skill taxonomy into the database (idempotent).

    Hypothesis calls the test body many times within a single pytest
    function invocation (same db_session), so we guard against
    duplicate inserts by checking whether the table already has rows.
    """
    existing = SkillTaxonomy.query.first()
    if existing is not None:
        return
    for category, skills in _TAXONOMY_SKILLS.items():
        for skill_name in skills:
            entry = SkillTaxonomy(
                canonical_name=skill_name,
                category=category,
                is_deprecated=False,
            )
            session.add(entry)
    session.flush()


# -----------------------------------------------------------------------
# Property 2: Skill breakdown consistency
# Feature: role-based-dashboards, Property 2: Skill breakdown consistency
# -----------------------------------------------------------------------


class TestSkillBreakdownConsistency:
    """**Validates: Requirements 1.2, 3.1**

    For any student profile with a non-empty skills list drawn from the
    taxonomy, the skill_breakdown dictionary's values SHALL each equal
    the actual count of the student's skills in that category, and the
    sum of all category counts SHALL equal skill_count.
    """

    @given(skills=taxonomy_skill_subset)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_skill_breakdown_consistency(self, app, db_session, skills):
        """skill_breakdown category counts match SkillAnalyzer ground truth
        and their sum equals skill_count."""
        # Seed taxonomy
        _seed_taxonomy(db_session)

        # Create user and profile with the generated skills
        user = _make_user(db_session)
        profile = StudentProfile(
            user_id=user.id,
            skills_json=json.dumps(skills),
        )
        db_session.add(profile)
        db_session.flush()

        service = DashboardService()
        result = service.get_student_summary(user.id)

        skill_count = result["skill_count"]
        skill_breakdown = result["skill_breakdown"]

        # Property: sum of all category counts equals skill_count
        assert sum(skill_breakdown.values()) == skill_count, (
            f"Sum of breakdown values {sum(skill_breakdown.values())} "
            f"!= skill_count {skill_count}; breakdown={skill_breakdown}, "
            f"skills={skills}"
        )

        # Property: each category count matches SkillAnalyzer ground truth
        analyzer = SkillAnalyzer()
        expected_categories = analyzer.categorize_skills(skills)

        for category, expected_skills in expected_categories.items():
            assert category in skill_breakdown, (
                f"Category {category!r} missing from skill_breakdown; "
                f"expected skills: {expected_skills}"
            )
            assert skill_breakdown[category] == len(expected_skills), (
                f"Category {category!r}: breakdown has {skill_breakdown[category]} "
                f"but expected {len(expected_skills)} skills: {expected_skills}"
            )

        # Also verify no extra categories in breakdown
        for category in skill_breakdown:
            assert category in expected_categories, (
                f"Unexpected category {category!r} in skill_breakdown "
                f"not present in SkillAnalyzer output"
            )


# -----------------------------------------------------------------------
# Additional imports for Property 3
# -----------------------------------------------------------------------

from app.models import Company, JobRole


# -----------------------------------------------------------------------
# Strategies for Property 3
# -----------------------------------------------------------------------

# Strategy for student CGPA (float in [0, 10])
student_cgpa = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)

# Strategy for a single job role's attributes
job_role_data = st.fixed_dictionaries({
    "is_active": st.booleans(),
    "cgpa_threshold": st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    "has_vector": st.booleans(),
})

# Strategy for a list of job roles (0 to 8 roles)
job_role_list = st.lists(job_role_data, min_size=0, max_size=8)


# -----------------------------------------------------------------------
# Property 3: Matched job count equals eligible active jobs
# Feature: role-based-dashboards, Property 3: Matched job count equals eligible active jobs
# -----------------------------------------------------------------------


class TestMatchedJobCountEqualsEligibleActiveJobs:
    """**Validates: Requirements 1.3**

    For any student with a given CGPA and any set of active job roles
    with varying CGPA thresholds, the matched_job_count SHALL equal the
    number of active job roles where the student's CGPA meets or exceeds
    the job's cgpa_threshold and the job has a valid job vector.
    """

    @given(cgpa=student_cgpa, jobs=job_role_list)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_matched_job_count_equals_eligible_active_jobs(
        self,
        app,
        db_session,
        cgpa,
        jobs,
    ):
        """matched_job_count equals the independently computed count of
        active jobs where student CGPA >= threshold and job has a valid vector."""
        # Clear any pre-existing job roles from prior Hypothesis examples
        # so the service only sees the jobs we create for this example.
        JobRole.query.delete()
        db_session.flush()

        # Create user and profile with the generated CGPA
        user = _make_user(db_session)
        profile = StudentProfile(
            user_id=user.id,
            cgpa=cgpa,
        )
        db_session.add(profile)
        db_session.flush()

        # Create a company to attach job roles to
        company = Company(name=f"TestCompany_{user.id}")
        db_session.add(company)
        db_session.flush()

        # Create job roles with the generated attributes
        for job_data in jobs:
            # Use a dummy vector JSON string when has_vector is True, None otherwise
            vector_json = json.dumps([0.1, 0.2, 0.3]) if job_data["has_vector"] else None

            job_role = JobRole(
                company_id=company.id,
                title=f"Role_{user.id}",
                is_active=job_data["is_active"],
                cgpa_threshold=job_data["cgpa_threshold"],
                job_vector_json=vector_json,
            )
            db_session.add(job_role)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_student_summary(user.id)

        # Independently compute the expected matched job count
        expected_count = 0
        for job_data in jobs:
            if (
                job_data["is_active"]
                and job_data["has_vector"]
                and cgpa >= job_data["cgpa_threshold"]
            ):
                expected_count += 1

        # Property: matched_job_count equals the expected count
        assert result["matched_job_count"] == expected_count, (
            f"matched_job_count={result['matched_job_count']} != "
            f"expected={expected_count}; cgpa={cgpa}, jobs={jobs}"
        )


# -----------------------------------------------------------------------
# Strategies for Property 4
# -----------------------------------------------------------------------

# Number of taxonomy skills (matches _ALL_SKILL_NAMES length)
_NUM_TAXONOMY_SKILLS = len(_ALL_SKILL_NAMES)

# Strategy for a binary skill vector component (0.0 or 1.0)
binary_component = st.sampled_from([0.0, 1.0])

# Strategy for a student skill vector (binary vector over taxonomy)
student_skill_vector = st.lists(
    binary_component,
    min_size=_NUM_TAXONOMY_SKILLS,
    max_size=_NUM_TAXONOMY_SKILLS,
)

# Strategy for a job role with a vector and CGPA threshold
job_role_with_vector = st.fixed_dictionaries({
    "vector": st.lists(
        binary_component,
        min_size=_NUM_TAXONOMY_SKILLS,
        max_size=_NUM_TAXONOMY_SKILLS,
    ),
    "cgpa_threshold": st.floats(
        min_value=0.0, max_value=10.0,
        allow_nan=False, allow_infinity=False,
    ),
})

# Strategy for a list of job roles (0 to 8 roles, all active with vectors)
job_roles_with_vectors = st.lists(job_role_with_vector, min_size=0, max_size=8)


# -----------------------------------------------------------------------
# Property 4: Top recommendations are sorted and limited
# Feature: role-based-dashboards, Property 4: Top recommendations are sorted and limited
# -----------------------------------------------------------------------


class TestTopRecommendationsSortedAndLimited:
    """**Validates: Requirements 1.4**

    For any non-empty set of job recommendations for a student, the
    `top_recommendations` list SHALL contain at most 3 items, and the
    items SHALL be sorted by `compatibility_score` in descending order.
    """

    @given(
        student_vector=student_skill_vector,
        student_cgpa=st.floats(
            min_value=0.0, max_value=10.0,
            allow_nan=False, allow_infinity=False,
        ),
        jobs=job_roles_with_vectors,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_top_recommendations_sorted_and_limited(
        self,
        app,
        db_session,
        student_vector,
        student_cgpa,
        jobs,
    ):
        """top_recommendations has at most 3 items and is sorted by
        compatibility_score in descending order."""
        # Seed taxonomy so vectors have the right dimension
        _seed_taxonomy(db_session)

        # Clear any pre-existing job roles from prior Hypothesis examples
        JobRole.query.delete()
        db_session.flush()

        # Build the skill_index from the seeded taxonomy
        taxonomy_entries = (
            SkillTaxonomy.query
            .filter_by(is_deprecated=False)
            .order_by(SkillTaxonomy.id)
            .all()
        )
        skill_index = {
            entry.canonical_name.lower(): idx
            for idx, entry in enumerate(taxonomy_entries)
        }

        # Create user and profile with a skill vector
        user = _make_user(db_session)
        vector_data = json.dumps({
            "vector": student_vector,
            "skill_index": skill_index,
            "version": "1.0",
        })
        profile = StudentProfile(
            user_id=user.id,
            cgpa=student_cgpa,
            skill_vector_json=vector_data,
        )
        db_session.add(profile)
        db_session.flush()

        # Create a company for the job roles
        company = Company(name=f"PropTestCompany_{user.id}")
        db_session.add(company)
        db_session.flush()

        # Create active job roles with vectors
        for i, job_data in enumerate(jobs):
            job_vector_data = json.dumps({
                "vector": job_data["vector"],
                "skill_index": skill_index,
                "version": "1.0",
            })
            job_role = JobRole(
                company_id=company.id,
                title=f"Role_{user.id}_{i}",
                is_active=True,
                cgpa_threshold=job_data["cgpa_threshold"],
                job_vector_json=job_vector_data,
            )
            db_session.add(job_role)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_student_summary(user.id)

        top_recs = result["top_recommendations"]

        # Property: at most 3 items
        assert len(top_recs) <= 3, (
            f"Expected at most 3 recommendations, got {len(top_recs)}"
        )

        # Property: sorted by compatibility_score descending
        scores = [rec["compatibility_score"] for rec in top_recs]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Recommendations not sorted descending: "
                f"score[{i}]={scores[i]} < score[{i+1}]={scores[i+1]}; "
                f"all scores={scores}"
            )


# -----------------------------------------------------------------------
# Strategies for Property 10
# -----------------------------------------------------------------------

# Strategy for a single job recommendation dict
recommendation_strategy = st.fixed_dictionaries({
    "job_role_id": st.integers(min_value=1, max_value=10000),
    "title": st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    "company_name": st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    "compatibility_score": st.floats(
        min_value=0.0, max_value=100.0,
        allow_nan=False, allow_infinity=False,
    ),
})

# Strategy for a valid student dashboard response dict
student_dashboard_response = st.fixed_dictionaries({
    "profile_completeness": st.integers(min_value=0, max_value=100),
    "skill_count": st.integers(min_value=0, max_value=1000),
    "skill_breakdown": st.dictionaries(
        keys=st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
        values=st.integers(min_value=0, max_value=100),
        min_size=0,
        max_size=10,
    ),
    "matched_job_count": st.integers(min_value=0, max_value=10000),
    "top_recommendations": st.lists(
        recommendation_strategy,
        min_size=0,
        max_size=3,
    ),
})


# -----------------------------------------------------------------------
# Property 10: Student dashboard response round-trip serialization
# Feature: role-based-dashboards, Property 10: Student dashboard response round-trip serialization
# -----------------------------------------------------------------------


class TestStudentDashboardRoundTripSerialization:
    """**Validates: Requirements 11.1**

    For any valid student dashboard response dictionary (containing
    profile_completeness, skill_count, skill_breakdown, matched_job_count,
    and top_recommendations), serializing to JSON and deserializing back
    SHALL produce an equivalent data structure.
    """

    @given(response=student_dashboard_response)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_student_dashboard_round_trip_serialization(self, response):
        """JSON serialize → deserialize produces an equivalent data structure."""
        serialized = json.dumps(response)
        deserialized = json.loads(serialized)

        # Property: round-tripped dict is equivalent to the original
        assert deserialized == response, (
            f"Round-trip mismatch:\n"
            f"  original:     {response}\n"
            f"  deserialized: {deserialized}"
        )


# -----------------------------------------------------------------------
# Strategies for Property 5
# -----------------------------------------------------------------------

# Strategy for a single job role's active status
job_role_active_status = st.fixed_dictionaries({
    "is_active": st.booleans(),
})

# Strategy for a list of job roles (0 to 10 roles with varying active status)
job_role_active_list = st.lists(job_role_active_status, min_size=0, max_size=10)

# Strategy for number of shortlist records to create (0 to 10)
shortlist_count_strategy = st.integers(min_value=0, max_value=10)


# -----------------------------------------------------------------------
# Property 5: Coordinator counts match database state
# Feature: role-based-dashboards, Property 5: Coordinator counts match database state
# -----------------------------------------------------------------------


class TestCoordinatorCountsMatchDatabaseState:
    """**Validates: Requirements 4.2**

    For any database state with job roles and shortlist records, the
    coordinator dashboard's `active_job_count` SHALL equal the count of
    `JobRole` records where `is_active=True`, and `shortlisted_count`
    SHALL equal the total count of `Shortlist` records.
    """

    @given(jobs=job_role_active_list, num_shortlists=shortlist_count_strategy)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_coordinator_counts_match_database_state(
        self,
        app,
        db_session,
        jobs,
        num_shortlists,
    ):
        """active_job_count equals count of active JobRoles and
        shortlisted_count equals total Shortlist records."""
        # Clear any pre-existing job roles and shortlists from prior examples
        Shortlist.query.delete()
        JobRole.query.delete()
        db_session.flush()

        # Create a company to attach job roles to
        company = Company(name="CoordTestCompany")
        db_session.add(company)
        db_session.flush()

        # Create job roles with varying active status
        for i, job_data in enumerate(jobs):
            job_role = JobRole(
                company_id=company.id,
                title=f"CoordRole_{i}",
                is_active=job_data["is_active"],
            )
            db_session.add(job_role)

        db_session.flush()

        # Create a student user and profile for shortlist records
        user = _make_user(db_session)
        profile = StudentProfile(user_id=user.id)
        db_session.add(profile)
        db_session.flush()

        # We need a job role to attach shortlists to; create a dedicated one
        # (active status doesn't matter for shortlist counting)
        shortlist_job = JobRole(
            company_id=company.id,
            title="ShortlistTargetRole",
            is_active=True,
        )
        db_session.add(shortlist_job)
        db_session.flush()

        # Create shortlist records
        for i in range(num_shortlists):
            shortlist = Shortlist(
                profile_id=profile.id,
                job_role_id=shortlist_job.id,
                compatibility_score=75.0,
            )
            db_session.add(shortlist)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_coordinator_summary()

        # Independently compute expected counts
        # active_job_count: count of jobs with is_active=True
        # (includes the shortlist_job which is always active)
        expected_active_count = sum(
            1 for job_data in jobs if job_data["is_active"]
        ) + 1  # +1 for the shortlist_job which is always active

        expected_shortlist_count = num_shortlists

        # Property: active_job_count equals count of active JobRole records
        assert result["active_job_count"] == expected_active_count, (
            f"active_job_count={result['active_job_count']} != "
            f"expected={expected_active_count}; jobs={jobs}"
        )

        # Property: shortlisted_count equals total Shortlist records
        assert result["shortlisted_count"] == expected_shortlist_count, (
            f"shortlisted_count={result['shortlisted_count']} != "
            f"expected={expected_shortlist_count}; num_shortlists={num_shortlists}"
        )


# -----------------------------------------------------------------------
# Strategies for Property 6
# -----------------------------------------------------------------------

from datetime import datetime, timedelta

# Strategy for number of shortlist records to create (0 to 12, exceeding the limit of 5)
shortlist_record_count = st.integers(min_value=0, max_value=12)

# Strategy for a time offset in seconds (used to generate distinct timestamps)
time_offset_seconds = st.integers(min_value=0, max_value=100000)


# -----------------------------------------------------------------------
# Property 6: Recent shortlists are sorted and limited
# Feature: role-based-dashboards, Property 6: Recent shortlists are sorted and limited
# -----------------------------------------------------------------------


class TestRecentShortlistsSortedAndLimited:
    """**Validates: Requirements 5.1**

    For any set of shortlist records in the database, the coordinator
    dashboard's `recent_shortlists` SHALL contain at most 5 items, and
    the items SHALL be sorted by `shortlisted_at` in descending order
    (most recent first).
    """

    @given(
        num_shortlists=shortlist_record_count,
        offsets=st.lists(
            time_offset_seconds,
            min_size=12,
            max_size=12,
        ),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_recent_shortlists_sorted_and_limited(
        self,
        app,
        db_session,
        num_shortlists,
        offsets,
    ):
        """recent_shortlists has at most 5 items and is sorted by
        shortlisted_at in descending order."""
        # Clear any pre-existing shortlists and job roles from prior examples
        Shortlist.query.delete()
        JobRole.query.delete()
        db_session.flush()

        # Create a company for job roles
        company = Company(name="RecentShortlistTestCompany")
        db_session.add(company)
        db_session.flush()

        # Create a job role to attach shortlists to
        job_role = JobRole(
            company_id=company.id,
            title="RecentShortlistTestRole",
            is_active=True,
        )
        db_session.add(job_role)
        db_session.flush()

        # Create a student user and profile
        user = _make_user(db_session)
        profile = StudentProfile(user_id=user.id)
        db_session.add(profile)
        db_session.flush()

        # Base timestamp for generating shortlist records
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        # Create shortlist records with varying timestamps
        for i in range(num_shortlists):
            offset = offsets[i]
            shortlist = Shortlist(
                profile_id=profile.id,
                job_role_id=job_role.id,
                compatibility_score=75.0,
                shortlisted_at=base_time + timedelta(seconds=offset),
            )
            db_session.add(shortlist)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_coordinator_summary()

        recent = result["recent_shortlists"]

        # Property: at most 5 items
        assert len(recent) <= 5, (
            f"Expected at most 5 recent shortlists, got {len(recent)}"
        )

        # Property: number of items is min(num_shortlists, 5)
        expected_count = min(num_shortlists, 5)
        assert len(recent) == expected_count, (
            f"Expected {expected_count} recent shortlists, got {len(recent)}"
        )

        # Property: sorted by shortlisted_at descending (most recent first)
        timestamps = [item["shortlisted_at"] for item in recent]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1], (
                f"recent_shortlists not sorted descending: "
                f"timestamps[{i}]={timestamps[i]} < "
                f"timestamps[{i+1}]={timestamps[i+1]}; "
                f"all timestamps={timestamps}"
            )


# -----------------------------------------------------------------------
# Strategies for Property 7
# -----------------------------------------------------------------------

# Strategy for a list of skill names in a job role's required_skills_json
job_skills_list = st.lists(
    st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
    min_size=0,
    max_size=8,
)

# Strategy for a single active job role with varying required_skills_json
active_job_with_skills = st.fixed_dictionaries({
    "skills": job_skills_list,
})

# Strategy for a list of active job roles (0 to 10)
active_jobs_with_skills_list = st.lists(active_job_with_skills, min_size=0, max_size=10)


# -----------------------------------------------------------------------
# Property 7: Top skills demand is sorted and limited
# Feature: role-based-dashboards, Property 7: Top skills demand is sorted and limited
# -----------------------------------------------------------------------


class TestTopSkillsDemandSortedAndLimited:
    """**Validates: Requirements 5.3**

    For any set of active job roles with `required_skills_json`, the
    coordinator dashboard's `top_skills_demand` SHALL contain at most
    5 items, and the items SHALL be sorted by `count` in descending order.
    """

    @given(jobs=active_jobs_with_skills_list)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_top_skills_demand_sorted_and_limited(
        self,
        app,
        db_session,
        jobs,
    ):
        """top_skills_demand has at most 5 items and is sorted by
        count in descending order."""
        # Clear any pre-existing job roles from prior Hypothesis examples
        Shortlist.query.delete()
        JobRole.query.delete()
        db_session.flush()

        # Create a company to attach job roles to
        company = Company(name="SkillsDemandTestCompany")
        db_session.add(company)
        db_session.flush()

        # Create active job roles with varying required_skills_json
        for i, job_data in enumerate(jobs):
            skills_json = json.dumps(job_data["skills"]) if job_data["skills"] else None
            job_role = JobRole(
                company_id=company.id,
                title=f"SkillsDemandRole_{i}",
                is_active=True,
                required_skills_json=skills_json,
            )
            db_session.add(job_role)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_coordinator_summary()

        top_skills = result["top_skills_demand"]

        # Property: at most 5 items
        assert len(top_skills) <= 5, (
            f"Expected at most 5 top skills, got {len(top_skills)}"
        )

        # Property: sorted by count in descending order
        counts = [item["count"] for item in top_skills]
        for i in range(len(counts) - 1):
            assert counts[i] >= counts[i + 1], (
                f"top_skills_demand not sorted descending: "
                f"counts[{i}]={counts[i]} < counts[{i+1}]={counts[i+1]}; "
                f"all counts={counts}"
            )


# -----------------------------------------------------------------------
# Strategies for Property 8
# -----------------------------------------------------------------------

# Strategy for user role
user_role_strategy = st.sampled_from(["student", "placement_officer", "admin"])

# Strategy for user status
user_status_strategy = st.sampled_from(["active", "inactive"])

# Strategy for a single user's attributes
user_data_strategy = st.fixed_dictionaries({
    "role": user_role_strategy,
    "status": user_status_strategy,
})

# Strategy for a list of users (0 to 15)
user_list_strategy = st.lists(user_data_strategy, min_size=0, max_size=15)


# -----------------------------------------------------------------------
# Property 8: User counts correctness with sum invariant
# Feature: role-based-dashboards, Property 8: User counts correctness with sum invariant
# -----------------------------------------------------------------------


class TestUserCountsSumInvariant:
    """**Validates: Requirements 7.1, 11.3**

    For any set of users in the database with varying roles and statuses,
    the admin dashboard's `user_counts.by_role` values SHALL each match
    the actual count of users with that role, `user_counts.by_status`
    values SHALL each match the actual count of users with that status,
    and the sum of `by_role` values SHALL equal `user_counts.total`.
    """

    @given(users=user_list_strategy)
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_user_counts_sum_invariant(
        self,
        app,
        db_session,
        users,
    ):
        """user_counts.by_role matches actual role counts, by_status matches
        actual status counts, and sum of by_role values equals total."""
        # Clear any pre-existing users from prior Hypothesis examples
        User.query.delete()
        db_session.flush()

        # Create users with the generated roles and statuses
        for i, user_data in enumerate(users):
            user = User(
                name=f"UserCountsTestUser_{i}",
                email=f"usercounts_test_{i}@example.com",
                password_hash="fakehash",
                role=user_data["role"],
                status=user_data["status"],
            )
            db_session.add(user)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_admin_summary()

        user_counts = result["user_counts"]
        by_role = user_counts["by_role"]
        by_status = user_counts["by_status"]
        total = user_counts["total"]

        # Independently compute expected counts
        from collections import Counter

        expected_by_role = Counter(u["role"] for u in users)
        expected_by_status = Counter(u["status"] for u in users)

        # Property: each by_role count matches actual count of users with that role
        for role, expected_count in expected_by_role.items():
            assert by_role.get(role, 0) == expected_count, (
                f"by_role[{role!r}]={by_role.get(role, 0)} != "
                f"expected={expected_count}; users={users}"
            )

        # Ensure no extra roles in by_role that aren't in our generated users
        for role, count in by_role.items():
            assert role in expected_by_role, (
                f"Unexpected role {role!r} in by_role with count={count}; "
                f"expected roles={dict(expected_by_role)}"
            )

        # Property: each by_status count matches actual count of users with that status
        for status, expected_count in expected_by_status.items():
            assert by_status.get(status, 0) == expected_count, (
                f"by_status[{status!r}]={by_status.get(status, 0)} != "
                f"expected={expected_count}; users={users}"
            )

        # Ensure no extra statuses in by_status that aren't in our generated users
        for status, count in by_status.items():
            assert status in expected_by_status, (
                f"Unexpected status {status!r} in by_status with count={count}; "
                f"expected statuses={dict(expected_by_status)}"
            )

        # Property: sum of by_role values equals total
        role_sum = sum(by_role.values())
        assert role_sum == total, (
            f"Sum of by_role values ({role_sum}) != total ({total}); "
            f"by_role={by_role}"
        )

        # Also verify total equals the number of users we created
        assert total == len(users), (
            f"total={total} != len(users)={len(users)}"
        )


# -----------------------------------------------------------------------
# Strategies for Property 9
# -----------------------------------------------------------------------

from app.models import UncategorizedSkill

# Strategy for a single SkillTaxonomy entry's attributes
taxonomy_entry_strategy = st.fixed_dictionaries({
    "is_deprecated": st.booleans(),
})

# Strategy for a list of SkillTaxonomy entries (0 to 15)
taxonomy_list_strategy = st.lists(taxonomy_entry_strategy, min_size=0, max_size=15)

# Strategy for a single UncategorizedSkill entry's attributes
uncategorized_entry_strategy = st.fixed_dictionaries({
    "reviewed": st.booleans(),
})

# Strategy for a list of UncategorizedSkill entries (0 to 15)
uncategorized_list_strategy = st.lists(uncategorized_entry_strategy, min_size=0, max_size=15)


# -----------------------------------------------------------------------
# Property 9: Taxonomy health counts correctness
# Feature: role-based-dashboards, Property 9: Taxonomy health counts correctness
# -----------------------------------------------------------------------


class TestTaxonomyHealthCountsCorrectness:
    """**Validates: Requirements 7.2**

    For any set of `SkillTaxonomy` and `UncategorizedSkill` records, the
    admin dashboard's `taxonomy_health.total_skills` SHALL equal the count
    of non-deprecated taxonomy entries, `deprecated_skills` SHALL equal
    the count of deprecated entries, and `uncategorized_pending` SHALL
    equal the count of unreviewed `UncategorizedSkill` records.
    """

    @given(
        taxonomy_entries=taxonomy_list_strategy,
        uncategorized_entries=uncategorized_list_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_taxonomy_health_counts_correctness(
        self,
        app,
        db_session,
        taxonomy_entries,
        uncategorized_entries,
    ):
        """taxonomy_health.total_skills equals non-deprecated count,
        deprecated_skills equals deprecated count, and
        uncategorized_pending equals unreviewed UncategorizedSkill count."""
        # Clear any pre-existing taxonomy and uncategorized records
        SkillTaxonomy.query.delete()
        UncategorizedSkill.query.delete()
        db_session.flush()

        # Create SkillTaxonomy entries with varying is_deprecated status
        for i, entry_data in enumerate(taxonomy_entries):
            taxonomy_entry = SkillTaxonomy(
                canonical_name=f"TaxonomyHealthSkill_{i}",
                category="TestCategory",
                is_deprecated=entry_data["is_deprecated"],
            )
            db_session.add(taxonomy_entry)

        # Create UncategorizedSkill entries with varying reviewed status
        for i, entry_data in enumerate(uncategorized_entries):
            uncategorized_entry = UncategorizedSkill(
                term=f"UncategorizedTerm_{i}",
                reviewed=entry_data["reviewed"],
            )
            db_session.add(uncategorized_entry)

        db_session.flush()

        # Call the service
        service = DashboardService()
        result = service.get_admin_summary()

        taxonomy_health = result["taxonomy_health"]

        # Independently compute expected counts
        expected_total_skills = sum(
            1 for entry in taxonomy_entries if not entry["is_deprecated"]
        )
        expected_deprecated_skills = sum(
            1 for entry in taxonomy_entries if entry["is_deprecated"]
        )
        expected_uncategorized_pending = sum(
            1 for entry in uncategorized_entries if not entry["reviewed"]
        )

        # Property: total_skills equals count of non-deprecated SkillTaxonomy entries
        assert taxonomy_health["total_skills"] == expected_total_skills, (
            f"total_skills={taxonomy_health['total_skills']} != "
            f"expected={expected_total_skills}; "
            f"taxonomy_entries={taxonomy_entries}"
        )

        # Property: deprecated_skills equals count of deprecated SkillTaxonomy entries
        assert taxonomy_health["deprecated_skills"] == expected_deprecated_skills, (
            f"deprecated_skills={taxonomy_health['deprecated_skills']} != "
            f"expected={expected_deprecated_skills}; "
            f"taxonomy_entries={taxonomy_entries}"
        )

        # Property: uncategorized_pending equals count of unreviewed UncategorizedSkill records
        assert taxonomy_health["uncategorized_pending"] == expected_uncategorized_pending, (
            f"uncategorized_pending={taxonomy_health['uncategorized_pending']} != "
            f"expected={expected_uncategorized_pending}; "
            f"uncategorized_entries={uncategorized_entries}"
        )


# -----------------------------------------------------------------------
# Strategies for Property 11
# -----------------------------------------------------------------------

from app.models import PlacementRecord

# Strategy for number of students (some placed, some not)
num_students_strategy = st.integers(min_value=0, max_value=10)

# Strategy for number of companies
num_companies_strategy = st.integers(min_value=1, max_value=5)

# Strategy for number of placement records (0 to 8)
num_placements_strategy = st.integers(min_value=0, max_value=8)


# -----------------------------------------------------------------------
# Property 11: Dashboard placement overview matches analytics service
# Feature: role-based-dashboards, Property 11: Dashboard placement overview matches analytics service
# -----------------------------------------------------------------------


class TestDashboardPlacementOverviewMatchesAnalytics:
    """**Validates: Requirements 11.2**

    For any database state with placement records, the coordinator
    dashboard's `placement_overview` values (total_students, placed_students,
    total_companies, placement_percentage) SHALL be identical to the values
    returned by `AnalyticsService.get_overview_stats()` for the same
    database state.
    """

    @given(
        num_students=num_students_strategy,
        num_companies=num_companies_strategy,
        num_placements=num_placements_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_placement_overview_matches_analytics_service(
        self,
        app,
        db_session,
        num_students,
        num_companies,
        num_placements,
    ):
        """coordinator dashboard placement_overview is identical to
        AnalyticsService.get_overview_stats() for the same database state."""
        # Clear pre-existing records from prior Hypothesis examples
        PlacementRecord.query.delete()
        Shortlist.query.delete()
        JobRole.query.delete()
        StudentProfile.query.delete()
        User.query.delete()
        Company.query.delete()
        db_session.flush()

        # Create student users with profiles
        student_profiles = []
        for i in range(num_students):
            user = User(
                name=f"PlacementStudent_{i}",
                email=f"placement_student_{i}@example.com",
                password_hash="fakehash",
                role="student",
                status="active",
            )
            db_session.add(user)
            db_session.flush()

            profile = StudentProfile(user_id=user.id)
            db_session.add(profile)
            db_session.flush()
            student_profiles.append(profile)

        # Create companies
        companies = []
        for i in range(num_companies):
            company = Company(name=f"PlacementCompany_{i}")
            db_session.add(company)
            db_session.flush()
            companies.append(company)

        # Create a job role for placement records (need at least one)
        job_role = JobRole(
            company_id=companies[0].id,
            title="PlacementTestRole",
            is_active=True,
        )
        db_session.add(job_role)
        db_session.flush()

        # Create placement records, distributing across available students
        # Only place students if we have students available
        if num_students > 0 and num_placements > 0:
            # Place up to num_placements students (some may be placed multiple
            # times at different companies, which tests distinct counting)
            for i in range(num_placements):
                profile = student_profiles[i % num_students]
                company = companies[i % num_companies]
                placement = PlacementRecord(
                    profile_id=profile.id,
                    job_role_id=job_role.id,
                    company_id=company.id,
                    department="Engineering",
                )
                db_session.add(placement)

        db_session.flush()

        # Call the coordinator dashboard service
        service = DashboardService()
        coordinator_result = service.get_coordinator_summary()
        dashboard_overview = coordinator_result["placement_overview"]

        # Call the analytics service directly
        from app.services.analytics_service import AnalyticsService
        analytics_service = AnalyticsService()
        analytics_overview = analytics_service.get_overview_stats()

        # Property: dashboard placement_overview is identical to analytics service output
        assert dashboard_overview["total_students"] == analytics_overview["total_students"], (
            f"total_students mismatch: dashboard={dashboard_overview['total_students']} "
            f"!= analytics={analytics_overview['total_students']}"
        )

        assert dashboard_overview["placed_students"] == analytics_overview["placed_students"], (
            f"placed_students mismatch: dashboard={dashboard_overview['placed_students']} "
            f"!= analytics={analytics_overview['placed_students']}"
        )

        assert dashboard_overview["total_companies"] == analytics_overview["total_companies"], (
            f"total_companies mismatch: dashboard={dashboard_overview['total_companies']} "
            f"!= analytics={analytics_overview['total_companies']}"
        )

        assert dashboard_overview["placement_percentage"] == analytics_overview["placement_percentage"], (
            f"placement_percentage mismatch: dashboard={dashboard_overview['placement_percentage']} "
            f"!= analytics={analytics_overview['placement_percentage']}"
        )
