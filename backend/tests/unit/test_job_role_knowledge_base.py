"""Unit tests for the JobRoleKnowledgeBase class.

Tests experience level mapping, role keyword/skill retrieval,
and fuzzy role matching.

Requirements: 3.1, 3.2, 3.3, 3.4, 10.1, 10.2, 10.3, 10.4
"""

import pytest

from app.services.job_role_knowledge_base import JobRoleKnowledgeBase


@pytest.fixture
def kb():
    return JobRoleKnowledgeBase()


# -----------------------------------------------------------------------
# get_experience_level
# -----------------------------------------------------------------------

class TestGetExperienceLevel:
    def test_none_returns_entry(self, kb):
        assert kb.get_experience_level(None) == "entry"

    def test_zero_returns_entry(self, kb):
        assert kb.get_experience_level(0.0) == "entry"

    def test_six_returns_entry(self, kb):
        assert kb.get_experience_level(6.0) == "entry"

    def test_just_above_six_returns_mid(self, kb):
        assert kb.get_experience_level(6.1) == "mid"

    def test_fifteen_returns_mid(self, kb):
        assert kb.get_experience_level(15.0) == "mid"

    def test_just_above_fifteen_returns_senior(self, kb):
        assert kb.get_experience_level(15.1) == "senior"

    def test_hundred_returns_senior(self, kb):
        assert kb.get_experience_level(100.0) == "senior"


# -----------------------------------------------------------------------
# get_role_keywords
# -----------------------------------------------------------------------

class TestGetRoleKeywords:
    def test_known_role_returns_non_empty(self, kb):
        keywords = kb.get_role_keywords("full stack developer")
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_data_scientist_returns_keywords(self, kb):
        keywords = kb.get_role_keywords("data scientist")
        assert "data" in keywords

    def test_unknown_role_returns_empty(self, kb):
        keywords = kb.get_role_keywords("underwater basket weaver")
        assert keywords == []

    def test_empty_string_returns_empty(self, kb):
        keywords = kb.get_role_keywords("")
        assert keywords == []


# -----------------------------------------------------------------------
# get_role_skills
# -----------------------------------------------------------------------

class TestGetRoleSkills:
    def test_known_role_returns_non_empty(self, kb):
        skills = kb.get_role_skills("frontend developer")
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_backend_developer_has_python(self, kb):
        skills = kb.get_role_skills("backend developer")
        assert "Python" in skills

    def test_unknown_role_returns_empty(self, kb):
        skills = kb.get_role_skills("space cowboy")
        assert skills == []


# -----------------------------------------------------------------------
# match_role
# -----------------------------------------------------------------------

class TestMatchRole:
    def test_exact_match(self, kb):
        assert kb.match_role("full stack developer") == "full stack developer"

    def test_case_insensitive_match(self, kb):
        assert kb.match_role("Full Stack Developer") == "full stack developer"

    def test_case_insensitive_data_scientist(self, kb):
        assert kb.match_role("DATA SCIENTIST") == "data scientist"

    def test_substring_match(self, kb):
        result = kb.match_role("senior full stack developer")
        assert result == "full stack developer"

    def test_token_overlap_match(self, kb):
        result = kb.match_role("frontend engineer")
        assert result == "frontend developer"

    def test_unknown_role_returns_none(self, kb):
        result = kb.match_role("underwater basket weaver")
        assert result is None

    def test_empty_string_returns_none(self, kb):
        assert kb.match_role("") is None

    def test_whitespace_only_returns_none(self, kb):
        assert kb.match_role("   ") is None
