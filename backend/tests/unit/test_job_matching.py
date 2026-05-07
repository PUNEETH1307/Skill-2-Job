"""Unit tests for the JobMatchingEngine service.

Tests cover compatibility scoring, skill gap computation,
job recommendations, and candidate shortlisting.
"""

import json

import numpy as np
import pytest

from app import db
from app.models import (
    Company,
    JobRole,
    SkillTaxonomy,
    StudentProfile,
    User,
)
from app.services.job_matching import JobMatchingEngine
from seed import seed_skill_taxonomy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine():
    """Provide a JobMatchingEngine instance."""
    return JobMatchingEngine()


@pytest.fixture()
def seeded_taxonomy(db_session):
    """Seed the skill taxonomy and return the session."""
    seed_skill_taxonomy()
    return db_session


@pytest.fixture()
def skill_index(seeded_taxonomy):
    """Build and return the skill_index dict from the seeded taxonomy."""
    taxonomy = (
        SkillTaxonomy.query
        .filter_by(is_deprecated=False)
        .order_by(SkillTaxonomy.id)
        .all()
    )
    return {
        skill.canonical_name.lower(): idx
        for idx, skill in enumerate(taxonomy)
    }


@pytest.fixture()
def taxonomy_size(seeded_taxonomy):
    """Return the number of non-deprecated skills in the taxonomy."""
    return SkillTaxonomy.query.filter_by(is_deprecated=False).count()


def _make_vector(skill_index: dict, taxonomy_size: int, skills: list[str]) -> np.ndarray:
    """Helper: build a binary vector from a list of skill names."""
    vec = np.zeros(taxonomy_size, dtype=float)
    for s in skills:
        idx = skill_index.get(s.lower())
        if idx is not None:
            vec[idx] = 1.0
    return vec


def _make_vector_json(vector: np.ndarray, skill_index: dict) -> str:
    """Helper: serialize a vector + skill_index to the expected JSON format."""
    return json.dumps({
        "vector": vector.tolist(),
        "skill_index": skill_index,
        "version": "1.0",
    })


def _create_user(session, name: str, email: str, role: str = "student") -> User:
    """Helper: create and persist a User."""
    user = User(
        name=name,
        email=email,
        password_hash="hashed",
        role=role,
        status="active",
    )
    session.add(user)
    session.flush()
    return user


def _create_profile(
    session,
    user: User,
    cgpa: float,
    skill_vector_json: str | None = None,
) -> StudentProfile:
    """Helper: create and persist a StudentProfile."""
    profile = StudentProfile(
        user_id=user.id,
        institution="Test University",
        degree="B.Tech",
        branch="CS",
        cgpa=cgpa,
        graduation_year=2025,
        skill_vector_json=skill_vector_json,
    )
    session.add(profile)
    session.flush()
    return profile


def _create_company(session, name: str = "TestCorp") -> Company:
    """Helper: create and persist a Company."""
    company = Company(name=name, industry="Tech", location="Remote")
    session.add(company)
    session.flush()
    return company


def _create_job_role(
    session,
    company: Company,
    title: str,
    required_skills: list[str],
    job_vector_json: str,
    cgpa_threshold: float = 0.0,
    is_active: bool = True,
) -> JobRole:
    """Helper: create and persist a JobRole."""
    job = JobRole(
        company_id=company.id,
        title=title,
        description=f"{title} role",
        required_skills_json=json.dumps(required_skills),
        job_vector_json=job_vector_json,
        cgpa_threshold=cgpa_threshold,
        is_active=is_active,
    )
    session.add(job)
    session.flush()
    return job


# ---------------------------------------------------------------------------
# compute_compatibility
# ---------------------------------------------------------------------------

class TestComputeCompatibility:
    """Tests for JobMatchingEngine.compute_compatibility."""

    def test_known_vectors(self, engine):
        """Cosine similarity of known vectors matches expected value."""
        a = np.array([1.0, 0.0, 1.0, 0.0])
        b = np.array([1.0, 1.0, 0.0, 0.0])
        # cos(a, b) = (1*1 + 0*1 + 1*0 + 0*0) / (sqrt(2) * sqrt(2)) = 1/2 = 0.5
        score = engine.compute_compatibility(a, b)
        assert abs(score - 0.5) < 1e-6

    def test_zero_vector_returns_zero(self, engine):
        """If either vector is all zeros, return 0.0."""
        a = np.array([1.0, 1.0, 0.0])
        zero = np.array([0.0, 0.0, 0.0])

        assert engine.compute_compatibility(a, zero) == 0.0
        assert engine.compute_compatibility(zero, a) == 0.0
        assert engine.compute_compatibility(zero, zero) == 0.0

    def test_identical_vectors_return_one(self, engine):
        """Identical non-zero vectors produce a score of 1.0."""
        a = np.array([1.0, 0.0, 1.0, 1.0])
        score = engine.compute_compatibility(a, a)
        assert abs(score - 1.0) < 1e-6

    def test_orthogonal_vectors_return_zero(self, engine):
        """Orthogonal vectors produce a score of 0.0."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        score = engine.compute_compatibility(a, b)
        assert abs(score - 0.0) < 1e-6

    def test_result_in_range(self, engine):
        """Score is always in [0.0, 1.0]."""
        a = np.array([0.5, 0.3, 0.8])
        b = np.array([0.2, 0.9, 0.1])
        score = engine.compute_compatibility(a, b)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# compute_skill_gap
# ---------------------------------------------------------------------------

class TestComputeSkillGap:
    """Tests for JobMatchingEngine.compute_skill_gap."""

    def test_gaps_detected(self, engine, skill_index, taxonomy_size):
        """Skills required by the job but missing from the student are reported."""
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Docker", "AWS"])

        gaps = engine.compute_skill_gap(student_vec, job_vec, skill_index)

        gap_skills = {g["skill"] for g in gaps}
        assert "docker" in gap_skills
        assert "aws" in gap_skills
        # Python is present in both — should NOT be a gap
        assert "python" not in gap_skills

    def test_deficit_scores_in_range(self, engine, skill_index, taxonomy_size):
        """All deficit scores are in [0.0, 1.0]."""
        student_vec = _make_vector(skill_index, taxonomy_size, [])
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python", "React", "MySQL"])

        gaps = engine.compute_skill_gap(student_vec, job_vec, skill_index)

        for gap in gaps:
            assert 0.0 <= gap["deficit_score"] <= 1.0

    def test_sorted_by_deficit_descending(self, engine):
        """Gaps are sorted by deficit_score in descending order."""
        # Use a small custom index for clarity
        idx = {"a": 0, "b": 1, "c": 2}
        student = np.array([0.0, 0.0, 0.0])
        job = np.array([0.8, 1.0, 0.5])

        gaps = engine.compute_skill_gap(student, job, idx)

        scores = [g["deficit_score"] for g in gaps]
        assert scores == sorted(scores, reverse=True)

    def test_full_coverage_returns_empty(self, engine, skill_index, taxonomy_size):
        """When the student has all required skills, the gap list is empty."""
        skills = ["Python", "React", "MySQL"]
        student_vec = _make_vector(skill_index, taxonomy_size, skills)
        job_vec = _make_vector(skill_index, taxonomy_size, skills)

        gaps = engine.compute_skill_gap(student_vec, job_vec, skill_index)
        assert gaps == []

    def test_student_superset_returns_empty(self, engine, skill_index, taxonomy_size):
        """Student has more skills than required — no gaps."""
        student_vec = _make_vector(
            skill_index, taxonomy_size, ["Python", "React", "MySQL", "Docker"]
        )
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python", "React"])

        gaps = engine.compute_skill_gap(student_vec, job_vec, skill_index)
        assert gaps == []


# ---------------------------------------------------------------------------
# get_recommendations
# ---------------------------------------------------------------------------

class TestGetRecommendations:
    """Tests for JobMatchingEngine.get_recommendations."""

    def test_returns_sorted_results(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Recommendations are sorted by compatibility_score descending."""
        session = seeded_taxonomy

        # Create student
        user = _create_user(session, "Alice", "alice@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Flask"])
        _create_profile(
            session, user, cgpa=8.0,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        # Create company and jobs
        company = _create_company(session, "TechCo")

        # Job 1: high match (Python + Flask)
        job1_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Flask"])
        _create_job_role(
            session, company, "Backend Dev",
            ["Python", "Flask"], _make_vector_json(job1_vec, skill_index),
        )

        # Job 2: partial match (Python + Docker)
        job2_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Docker"])
        _create_job_role(
            session, company, "DevOps Eng",
            ["Python", "Docker"], _make_vector_json(job2_vec, skill_index),
        )

        # Job 3: no match (Go + Kubernetes)
        job3_vec = _make_vector(skill_index, taxonomy_size, ["Go", "Kubernetes"])
        _create_job_role(
            session, company, "Infra Eng",
            ["Go", "Kubernetes"], _make_vector_json(job3_vec, skill_index),
        )

        session.commit()

        recs = engine.get_recommendations(user.id)

        assert len(recs) >= 2
        # Scores should be in non-increasing order
        scores = [r["compatibility_score"] for r in recs]
        assert scores == sorted(scores, reverse=True)

        # First result should be the perfect match
        assert recs[0]["title"] == "Backend Dev"
        assert recs[0]["compatibility_score"] == 100.0

    def test_filters_by_cgpa_eligibility(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Jobs with CGPA threshold above the student's CGPA are excluded."""
        session = seeded_taxonomy

        user = _create_user(session, "Bob", "bob@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=6.5,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        company = _create_company(session, "HighBar Inc")

        # Job with threshold 7.0 — student (6.5) should NOT qualify
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_job_role(
            session, company, "Senior Dev",
            ["Python"], _make_vector_json(job_vec, skill_index),
            cgpa_threshold=7.0,
        )

        # Job with threshold 6.0 — student (6.5) qualifies
        _create_job_role(
            session, company, "Junior Dev",
            ["Python"], _make_vector_json(job_vec, skill_index),
            cgpa_threshold=6.0,
        )

        session.commit()

        recs = engine.get_recommendations(user.id)

        titles = [r["title"] for r in recs]
        assert "Junior Dev" in titles
        assert "Senior Dev" not in titles

    def test_empty_when_no_active_jobs(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Returns empty list when no active job roles exist."""
        session = seeded_taxonomy

        user = _create_user(session, "Carol", "carol@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=8.0,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        company = _create_company(session, "InactiveCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_job_role(
            session, company, "Inactive Job",
            ["Python"], _make_vector_json(job_vec, skill_index),
            is_active=False,
        )

        session.commit()

        recs = engine.get_recommendations(user.id)
        assert recs == []

    def test_result_dict_keys(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Each recommendation dict has the expected keys."""
        session = seeded_taxonomy

        user = _create_user(session, "Dave", "dave@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=8.0,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        company = _create_company(session, "KeyCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_job_role(
            session, company, "Py Dev",
            ["Python"], _make_vector_json(job_vec, skill_index),
        )

        session.commit()

        recs = engine.get_recommendations(user.id)
        assert len(recs) == 1

        rec = recs[0]
        assert "job_role_id" in rec
        assert "title" in rec
        assert "company_name" in rec
        assert "compatibility_score" in rec
        assert "required_skills" in rec
        assert rec["company_name"] == "KeyCo"

    def test_score_is_percentage(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Compatibility score is expressed as a percentage (0-100)."""
        session = seeded_taxonomy

        user = _create_user(session, "Eve", "eve@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Flask"])
        _create_profile(
            session, user, cgpa=9.0,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        company = _create_company(session, "PctCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Flask"])
        _create_job_role(
            session, company, "Perfect Match",
            ["Python", "Flask"], _make_vector_json(job_vec, skill_index),
        )

        session.commit()

        recs = engine.get_recommendations(user.id)
        assert recs[0]["compatibility_score"] == 100.0

    def test_respects_limit(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Only returns up to `limit` results."""
        session = seeded_taxonomy

        user = _create_user(session, "Frank", "frank@test.com")
        student_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=9.0,
            skill_vector_json=_make_vector_json(student_vec, skill_index),
        )

        company = _create_company(session, "ManyCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        for i in range(5):
            _create_job_role(
                session, company, f"Job {i}",
                ["Python"], _make_vector_json(job_vec, skill_index),
            )

        session.commit()

        recs = engine.get_recommendations(user.id, limit=3)
        assert len(recs) == 3


# ---------------------------------------------------------------------------
# shortlist_candidates
# ---------------------------------------------------------------------------

class TestShortlistCandidates:
    """Tests for JobMatchingEngine.shortlist_candidates."""

    def test_returns_sorted_candidates(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Candidates are sorted by compatibility_score descending."""
        session = seeded_taxonomy

        company = _create_company(session, "SortCo")
        job_vec = _make_vector(
            skill_index, taxonomy_size, ["Python", "Flask", "MySQL"]
        )
        job = _create_job_role(
            session, company, "Full Stack",
            ["Python", "Flask", "MySQL"],
            _make_vector_json(job_vec, skill_index),
            cgpa_threshold=6.0,
        )

        # Student A: matches all 3 skills
        user_a = _create_user(session, "Alice A", "alice_a@test.com")
        vec_a = _make_vector(
            skill_index, taxonomy_size, ["Python", "Flask", "MySQL"]
        )
        _create_profile(
            session, user_a, cgpa=8.0,
            skill_vector_json=_make_vector_json(vec_a, skill_index),
        )

        # Student B: matches 1 skill
        user_b = _create_user(session, "Bob B", "bob_b@test.com")
        vec_b = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user_b, cgpa=7.0,
            skill_vector_json=_make_vector_json(vec_b, skill_index),
        )

        # Student C: matches 2 skills
        user_c = _create_user(session, "Carol C", "carol_c@test.com")
        vec_c = _make_vector(skill_index, taxonomy_size, ["Python", "Flask"])
        _create_profile(
            session, user_c, cgpa=7.5,
            skill_vector_json=_make_vector_json(vec_c, skill_index),
        )

        session.commit()

        candidates = engine.shortlist_candidates(job.id)

        assert len(candidates) == 3
        scores = [c["compatibility_score"] for c in candidates]
        assert scores == sorted(scores, reverse=True)
        # Alice should be first (perfect match)
        assert candidates[0]["name"] == "Alice A"

    def test_filters_by_cgpa(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Students below the CGPA threshold are excluded."""
        session = seeded_taxonomy

        company = _create_company(session, "FilterCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        job = _create_job_role(
            session, company, "Strict Job",
            ["Python"], _make_vector_json(job_vec, skill_index),
            cgpa_threshold=8.0,
        )

        # Student with CGPA 9.0 — eligible
        user_high = _create_user(session, "High GPA", "high@test.com")
        vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user_high, cgpa=9.0,
            skill_vector_json=_make_vector_json(vec, skill_index),
        )

        # Student with CGPA 6.0 — not eligible
        user_low = _create_user(session, "Low GPA", "low@test.com")
        _create_profile(
            session, user_low, cgpa=6.0,
            skill_vector_json=_make_vector_json(vec, skill_index),
        )

        session.commit()

        candidates = engine.shortlist_candidates(job.id)

        names = [c["name"] for c in candidates]
        assert "High GPA" in names
        assert "Low GPA" not in names

    def test_candidate_dict_keys(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Each candidate dict has the expected keys."""
        session = seeded_taxonomy

        company = _create_company(session, "KeysCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python", "Docker"])
        job = _create_job_role(
            session, company, "Key Job",
            ["Python", "Docker"], _make_vector_json(job_vec, skill_index),
        )

        user = _create_user(session, "Key Student", "keys@test.com")
        vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=8.0,
            skill_vector_json=_make_vector_json(vec, skill_index),
        )

        session.commit()

        candidates = engine.shortlist_candidates(job.id)
        assert len(candidates) == 1

        c = candidates[0]
        assert "profile_id" in c
        assert "name" in c
        assert "cgpa" in c
        assert "compatibility_score" in c
        assert "matched_skills" in c
        assert "missing_skills" in c

    def test_matched_and_missing_skills(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Matched and missing skills are correctly identified."""
        session = seeded_taxonomy

        company = _create_company(session, "SkillCo")
        job_vec = _make_vector(
            skill_index, taxonomy_size, ["Python", "Docker", "AWS"]
        )
        job = _create_job_role(
            session, company, "Cloud Dev",
            ["Python", "Docker", "AWS"],
            _make_vector_json(job_vec, skill_index),
        )

        user = _create_user(session, "Partial", "partial@test.com")
        vec = _make_vector(skill_index, taxonomy_size, ["Python", "Docker"])
        _create_profile(
            session, user, cgpa=8.0,
            skill_vector_json=_make_vector_json(vec, skill_index),
        )

        session.commit()

        candidates = engine.shortlist_candidates(job.id)
        assert len(candidates) == 1

        c = candidates[0]
        assert "Python" in c["matched_skills"]
        assert "Docker" in c["matched_skills"]
        assert "AWS" in c["missing_skills"]

    def test_empty_when_no_eligible(
        self, engine, seeded_taxonomy, skill_index, taxonomy_size
    ):
        """Returns empty list when no students meet eligibility."""
        session = seeded_taxonomy

        company = _create_company(session, "EmptyCo")
        job_vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        job = _create_job_role(
            session, company, "Elite Job",
            ["Python"], _make_vector_json(job_vec, skill_index),
            cgpa_threshold=10.0,
        )

        user = _create_user(session, "Average", "avg@test.com")
        vec = _make_vector(skill_index, taxonomy_size, ["Python"])
        _create_profile(
            session, user, cgpa=7.0,
            skill_vector_json=_make_vector_json(vec, skill_index),
        )

        session.commit()

        candidates = engine.shortlist_candidates(job.id)
        assert candidates == []
