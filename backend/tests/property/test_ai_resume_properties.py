"""Property-based tests for the AIResumeService.

Uses Hypothesis to verify universal correctness properties across
randomly generated inputs.

Location: backend/tests/property/test_ai_resume_properties.py
"""

import json

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.services.ai_resume_service import AIResumeService
from app.services.job_role_knowledge_base import JobRoleKnowledgeBase


# -----------------------------------------------------------------------
# Shared data
# -----------------------------------------------------------------------

_kb = JobRoleKnowledgeBase()

# Build a flat list of (role_key, skill) pairs from the knowledge base
_ROLE_SKILL_PAIRS = []
for role_key, role_data in _kb.JOB_ROLE_DATABASE.items():
    for skill in role_data["skills"]:
        _ROLE_SKILL_PAIRS.append((role_key, skill))


# -----------------------------------------------------------------------
# Strategies
# -----------------------------------------------------------------------

# Strategy for non-empty printable strings (useful for dream_job, skills, etc.)
non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=80,
).filter(lambda s: s.strip())

# Strategy for skill lists (1 to 10 non-empty strings)
skill_list = st.lists(non_empty_text, min_size=1, max_size=10)

# Strategy for project-like dicts
project_dict = st.fixed_dictionaries({
    "title": non_empty_text,
    "description": st.text(min_size=0, max_size=200),
    "technologies": st.text(min_size=0, max_size=100),
})

# Strategy for lists of projects
project_list = st.lists(project_dict, min_size=0, max_size=5)


# -----------------------------------------------------------------------
# Property 1: Score Boundedness
# Feature: ai-resume-generation, Property 1: Score Boundedness
# -----------------------------------------------------------------------


class TestScoreBoundedness:
    """**Validates: Requirement 2.1, Design Property 1**

    For any skill string and any dream job string, `score_skill_relevance`
    SHALL return a float in [0.0, 1.0].
    """

    @given(
        skill=st.text(min_size=0, max_size=100),
        dream_job=st.text(min_size=0, max_size=100),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_score_skill_relevance_is_bounded(self, app, skill, dream_job):
        """score_skill_relevance always returns a float in [0.0, 1.0]
        for any arbitrary skill and dream_job strings."""
        with app.app_context():
            service = AIResumeService()
            score = service.score_skill_relevance(skill, dream_job)

            # Property: score is a float
            assert isinstance(score, float), (
                f"Expected float, got {type(score).__name__}: {score}"
            )

            # Property: score is in [0.0, 1.0]
            assert 0.0 <= score <= 1.0, (
                f"Expected 0.0 <= score <= 1.0, got {score} "
                f"for skill={skill!r}, dream_job={dream_job!r}"
            )


# -----------------------------------------------------------------------
# Property 2: Direct Match Minimum Score
# Feature: ai-resume-generation, Property 2: Direct Match Minimum Score
# -----------------------------------------------------------------------


class TestDirectMatchMinimumScore:
    """**Validates: Requirement 2.2, Design Property 2**

    For any skill that appears in a known role's expected skills list,
    the score SHALL be at least 0.6.
    """

    @given(
        pair=st.sampled_from(_ROLE_SKILL_PAIRS),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_direct_match_scores_at_least_0_6(self, app, pair):
        """Skills in a role's expected skills list always score >= 0.6."""
        role_key, skill = pair
        with app.app_context():
            service = AIResumeService()
            score = service.score_skill_relevance(skill, role_key)

            assert score >= 0.6, (
                f"Expected score >= 0.6 for direct match, got {score} "
                f"for skill={skill!r}, dream_job={role_key!r}"
            )


# -----------------------------------------------------------------------
# Property 3: Experience Level Monotonicity
# Feature: ai-resume-generation, Property 3: Experience Level Monotonicity
# -----------------------------------------------------------------------

_LEVEL_ORDER = {"entry": 0, "mid": 1, "senior": 2}


class TestExperienceLevelMonotonicity:
    """**Validates: Requirements 3.2, 3.3, 3.4, 3.5, Design Property 3**

    For any two LPA values where lpa1 < lpa2, the experience level for
    lpa1 SHALL be <= the level for lpa2.
    """

    @given(
        lpa1=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        lpa2=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_experience_level_is_monotonically_non_decreasing(self, lpa1, lpa2):
        """For lpa1 < lpa2, level(lpa1) <= level(lpa2)."""
        from hypothesis import assume
        assume(lpa1 < lpa2)

        kb = JobRoleKnowledgeBase()
        level1 = kb.get_experience_level(lpa1)
        level2 = kb.get_experience_level(lpa2)

        assert level1 in _LEVEL_ORDER, f"Unknown level: {level1}"
        assert level2 in _LEVEL_ORDER, f"Unknown level: {level2}"

        assert _LEVEL_ORDER[level1] <= _LEVEL_ORDER[level2], (
            f"Monotonicity violated: level({lpa1})={level1} > level({lpa2})={level2}"
        )


# -----------------------------------------------------------------------
# Property 4, 5, 6: Career Objective Properties
# Feature: ai-resume-generation, Properties 4, 5, 6
# -----------------------------------------------------------------------


class TestCareerObjectiveProperties:
    """**Validates: Requirements 4.1, 4.2, 4.3, Design Properties 4, 5, 6**

    Property 4: Career objective length is between 50 and 500 characters.
    Property 5: Career objective contains the dream_job title.
    Property 6: Career objective mentions at least one skill from the input.
    """

    @given(
        dream_job=non_empty_text,
        degree=non_empty_text,
        branch=non_empty_text,
        skills=skill_list,
        expected_lpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_career_objective_length_bounds(self, app, dream_job, degree, branch, skills, expected_lpa):
        """Career objective is always between 50 and 500 characters."""
        with app.app_context():
            service = AIResumeService()
            objective = service.generate_career_objective(
                dream_job=dream_job,
                degree=degree,
                branch=branch,
                skills=skills,
                expected_lpa=expected_lpa,
            )

            assert 50 <= len(objective) <= 500, (
                f"Expected 50 <= len <= 500, got {len(objective)} "
                f"for dream_job={dream_job!r}"
            )

    @given(
        dream_job=non_empty_text,
        degree=non_empty_text,
        branch=non_empty_text,
        skills=skill_list,
        expected_lpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_career_objective_contains_dream_job(self, app, dream_job, degree, branch, skills, expected_lpa):
        """Career objective contains the dream_job title."""
        with app.app_context():
            service = AIResumeService()
            objective = service.generate_career_objective(
                dream_job=dream_job,
                degree=degree,
                branch=branch,
                skills=skills,
                expected_lpa=expected_lpa,
            )

            assert dream_job in objective, (
                f"Career objective does not contain dream_job={dream_job!r}. "
                f"Objective: {objective!r}"
            )

    @given(
        dream_job=non_empty_text,
        degree=non_empty_text,
        branch=non_empty_text,
        skills=skill_list,
        expected_lpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_career_objective_contains_at_least_one_skill(self, app, dream_job, degree, branch, skills, expected_lpa):
        """Career objective mentions at least one skill from the input list."""
        with app.app_context():
            service = AIResumeService()
            objective = service.generate_career_objective(
                dream_job=dream_job,
                degree=degree,
                branch=branch,
                skills=skills,
                expected_lpa=expected_lpa,
            )

            # At least one skill from the input should appear in the objective
            found = any(skill in objective for skill in skills)
            assert found, (
                f"No skill from {skills!r} found in career objective: {objective!r}"
            )


# -----------------------------------------------------------------------
# Property 8, 9: Skill Prioritization
# Feature: ai-resume-generation, Properties 8, 9
# -----------------------------------------------------------------------


class TestSkillPrioritization:
    """**Validates: Requirements 6.1, 6.2, 6.3, Design Properties 8, 9**

    Property 8: prioritize_skills returns a permutation of the input.
    Property 9: The output is ordered by descending relevance score.
    """

    @given(
        skills=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
            min_size=0,
            max_size=10,
        ),
        dream_job=st.text(min_size=0, max_size=80),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_prioritize_skills_is_permutation(self, app, skills, dream_job):
        """prioritize_skills returns a list with the same elements as input."""
        with app.app_context():
            service = AIResumeService()
            result = service.prioritize_skills(skills, dream_job)

            # Property: same length
            assert len(result) == len(skills), (
                f"Length mismatch: input={len(skills)}, output={len(result)}"
            )

            # Property: same elements (permutation)
            assert sorted(result) == sorted(skills), (
                f"Not a permutation. Input sorted: {sorted(skills)}, "
                f"Output sorted: {sorted(result)}"
            )

    @given(
        skills=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
            min_size=2,
            max_size=10,
        ),
        dream_job=non_empty_text,
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_prioritize_skills_ordering(self, app, skills, dream_job):
        """prioritize_skills output is ordered by descending relevance score."""
        with app.app_context():
            service = AIResumeService()
            result = service.prioritize_skills(skills, dream_job)

            # Compute scores for the output order
            scores = [service.score_skill_relevance(s, dream_job) for s in result]

            # Property: scores are non-increasing
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], (
                    f"Ordering violated at index {i}: "
                    f"score[{i}]={scores[i]} < score[{i+1}]={scores[i+1]}; "
                    f"skills={result}, scores={scores}"
                )


# -----------------------------------------------------------------------
# Property 10, 11: Project Description Preservation
# Feature: ai-resume-generation, Properties 10, 11
# -----------------------------------------------------------------------


class TestProjectDescriptionPreservation:
    """**Validates: Requirements 7.1, 7.2, Design Properties 10, 11**

    Property 10: Output list length equals input list length.
    Property 11: Original title and technologies are preserved.
    """

    @given(
        projects=project_list,
        dream_job=non_empty_text,
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_project_description_length_preservation(self, app, projects, dream_job):
        """Output list length equals input list length."""
        with app.app_context():
            service = AIResumeService()
            result = service.generate_project_descriptions(projects, dream_job)

            assert len(result) == len(projects), (
                f"Length mismatch: input={len(projects)}, output={len(result)}"
            )

    @given(
        projects=st.lists(project_dict, min_size=1, max_size=5),
        dream_job=non_empty_text,
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_project_description_content_preservation(self, app, projects, dream_job):
        """Original title and technologies are preserved in output."""
        with app.app_context():
            service = AIResumeService()
            result = service.generate_project_descriptions(projects, dream_job)

            for i, (inp, out) in enumerate(zip(projects, result)):
                assert out["title"] == inp["title"], (
                    f"Title mismatch at index {i}: "
                    f"input={inp['title']!r}, output={out['title']!r}"
                )
                assert out["technologies"] == inp["technologies"], (
                    f"Technologies mismatch at index {i}: "
                    f"input={inp['technologies']!r}, output={out['technologies']!r}"
                )


# -----------------------------------------------------------------------
# Property 12, 13: AI Content Completeness and Determinism
# Feature: ai-resume-generation, Properties 12, 13
# -----------------------------------------------------------------------


class TestAIContentCompletenessAndDeterminism:
    """**Validates: Requirements 9.2, 9.3, 9.4, Design Properties 12, 13**

    Property 12: For any valid profile with dream_job, output has non-empty
    career_objective, professional_summary, and valid experience_level.
    Property 13: Calling generate_ai_content twice with same inputs produces
    identical output.
    """

    @given(
        dream_job=non_empty_text,
        degree=non_empty_text,
        branch=non_empty_text,
        skills=skill_list,
        expected_lpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
        cgpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        ),
        graduation_year=st.one_of(st.none(), st.integers(min_value=2000, max_value=2035)),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_ai_content_completeness(
        self, app, db_session, dream_job, degree, branch, skills, expected_lpa, cgpa, graduation_year
    ):
        """AI content output has non-empty required fields and valid experience_level."""
        from app.models import User, StudentProfile

        with app.app_context():
            # Create a user and profile in the database
            user = User(
                name="PropTestUser",
                email=f"proptest_ai_{id(dream_job)}@example.com",
                password_hash="fakehash",
                role="student",
                status="active",
            )
            db_session.add(user)
            db_session.flush()

            profile = StudentProfile(
                user_id=user.id,
                dream_job=dream_job,
                expected_lpa=expected_lpa,
                degree=degree,
                branch=branch,
                skills_json=json.dumps(skills),
                cgpa=cgpa,
                graduation_year=graduation_year,
            )
            db_session.add(profile)
            db_session.flush()

            service = AIResumeService()
            content = service.generate_ai_content(profile, user)

            # Property 12: completeness
            assert content.career_objective, "career_objective is empty"
            assert content.professional_summary, "professional_summary is empty"
            assert content.experience_level in ("entry", "mid", "senior"), (
                f"Invalid experience_level: {content.experience_level!r}"
            )
            assert isinstance(content.prioritized_skills, list), (
                "prioritized_skills is not a list"
            )

    @given(
        dream_job=non_empty_text,
        degree=non_empty_text,
        branch=non_empty_text,
        skills=skill_list,
        expected_lpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
        cgpa=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        ),
        graduation_year=st.one_of(st.none(), st.integers(min_value=2000, max_value=2035)),
    )
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_ai_content_determinism(
        self, app, db_session, dream_job, degree, branch, skills, expected_lpa, cgpa, graduation_year
    ):
        """Calling generate_ai_content twice with same inputs produces identical output."""
        from app.models import User, StudentProfile

        with app.app_context():
            user = User(
                name="PropTestUser",
                email=f"proptest_det_{id(dream_job)}@example.com",
                password_hash="fakehash",
                role="student",
                status="active",
            )
            db_session.add(user)
            db_session.flush()

            profile = StudentProfile(
                user_id=user.id,
                dream_job=dream_job,
                expected_lpa=expected_lpa,
                degree=degree,
                branch=branch,
                skills_json=json.dumps(skills),
                cgpa=cgpa,
                graduation_year=graduation_year,
            )
            db_session.add(profile)
            db_session.flush()

            service = AIResumeService()
            content1 = service.generate_ai_content(profile, user)
            content2 = service.generate_ai_content(profile, user)

            # Property 13: determinism
            assert content1.career_objective == content2.career_objective, (
                f"career_objective differs between calls"
            )
            assert content1.professional_summary == content2.professional_summary, (
                f"professional_summary differs between calls"
            )
            assert content1.prioritized_skills == content2.prioritized_skills, (
                f"prioritized_skills differs between calls"
            )
            assert content1.experience_level == content2.experience_level, (
                f"experience_level differs between calls"
            )
            assert content1.project_descriptions == content2.project_descriptions, (
                f"project_descriptions differs between calls"
            )
