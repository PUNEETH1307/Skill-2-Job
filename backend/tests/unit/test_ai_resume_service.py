"""Unit tests for the AIResumeService class.

Tests skill relevance scoring, career objective generation,
project description enhancement, and SpaCy fallback behavior.

Requirements: 2.1, 2.2, 2.5, 4.2, 4.3, 7.2
"""

import pytest
from unittest.mock import patch

from app.services.ai_resume_service import AIResumeService


@pytest.fixture
def service():
    return AIResumeService()


# -----------------------------------------------------------------------
# score_skill_relevance — known skill/role pairs (direct match)
# -----------------------------------------------------------------------

class TestScoreSkillRelevanceDirectMatch:
    """Validates: Requirement 2.2 — Direct match → score >= 0.6."""

    def test_react_full_stack_developer(self, service):
        score = service.score_skill_relevance("React", "Full Stack Developer")
        assert score >= 0.6

    def test_python_full_stack_developer(self, service):
        score = service.score_skill_relevance("Python", "Full Stack Developer")
        assert score >= 0.6

    def test_javascript_frontend_developer(self, service):
        score = service.score_skill_relevance("JavaScript", "Frontend Developer")
        assert score >= 0.6

    def test_docker_devops_engineer(self, service):
        score = service.score_skill_relevance("Docker", "DevOps Engineer")
        assert score >= 0.6

    def test_tensorflow_machine_learning_engineer(self, service):
        score = service.score_skill_relevance("TensorFlow", "Machine Learning Engineer")
        assert score >= 0.6

    def test_score_within_bounds(self, service):
        """Validates: Requirement 2.1 — Score in [0.0, 1.0]."""
        score = service.score_skill_relevance("React", "Full Stack Developer")
        assert 0.0 <= score <= 1.0


# -----------------------------------------------------------------------
# score_skill_relevance — irrelevant skills (low score)
# -----------------------------------------------------------------------

class TestScoreSkillRelevanceIrrelevant:
    """Validates: Requirement 2.1 — Irrelevant skills score low."""

    def test_tensorflow_full_stack_developer(self, service):
        score = service.score_skill_relevance("TensorFlow", "Full Stack Developer")
        assert score < 0.3

    def test_kubernetes_data_scientist(self, service):
        score = service.score_skill_relevance("Kubernetes", "Data Scientist")
        assert score < 0.3

    def test_empty_skill_returns_zero(self, service):
        score = service.score_skill_relevance("", "Full Stack Developer")
        assert score == 0.0

    def test_empty_dream_job_returns_zero(self, service):
        score = service.score_skill_relevance("React", "")
        assert score == 0.0


# -----------------------------------------------------------------------
# generate_career_objective — contains dream_job and skills
# -----------------------------------------------------------------------

class TestGenerateCareerObjective:
    """Validates: Requirements 4.2, 4.3."""

    def test_contains_dream_job(self, service):
        """Validates: Requirement 4.2 — Career objective contains dream_job."""
        result = service.generate_career_objective(
            dream_job="Full Stack Developer",
            degree="B.Tech",
            branch="Computer Science",
            skills=["React", "Python", "Node.js"],
            expected_lpa=5.0,
        )
        assert "Full Stack Developer" in result

    def test_contains_at_least_one_skill(self, service):
        """Validates: Requirement 4.3 — Career objective mentions at least one skill."""
        skills = ["React", "Python", "Node.js"]
        result = service.generate_career_objective(
            dream_job="Full Stack Developer",
            degree="B.Tech",
            branch="Computer Science",
            skills=skills,
            expected_lpa=5.0,
        )
        assert any(skill in result for skill in skills)

    def test_length_between_50_and_500(self, service):
        result = service.generate_career_objective(
            dream_job="Data Scientist",
            degree="M.Sc",
            branch="Statistics",
            skills=["Python", "Machine Learning", "Pandas"],
            expected_lpa=10.0,
        )
        assert 50 <= len(result) <= 500

    def test_empty_skills_still_produces_output(self, service):
        result = service.generate_career_objective(
            dream_job="Backend Developer",
            degree="B.Tech",
            branch="IT",
            skills=[],
            expected_lpa=None,
        )
        assert "Backend Developer" in result
        assert len(result) >= 50


# -----------------------------------------------------------------------
# generate_project_descriptions — preserves title and technologies
# -----------------------------------------------------------------------

class TestGenerateProjectDescriptions:
    """Validates: Requirement 7.2 — Project descriptions preserve title and technologies."""

    def test_preserves_title(self, service):
        projects = [
            {"title": "E-Commerce App", "description": "Online store", "technologies": "React, Node.js"}
        ]
        results = service.generate_project_descriptions(projects, "Full Stack Developer")
        assert results[0]["title"] == "E-Commerce App"

    def test_preserves_technologies(self, service):
        projects = [
            {"title": "ML Pipeline", "description": "Data processing", "technologies": "Python, TensorFlow"}
        ]
        results = service.generate_project_descriptions(projects, "Data Scientist")
        assert results[0]["technologies"] == "Python, TensorFlow"

    def test_output_length_equals_input_length(self, service):
        projects = [
            {"title": "Project A", "description": "Desc A", "technologies": "Tech A"},
            {"title": "Project B", "description": "Desc B", "technologies": "Tech B"},
            {"title": "Project C", "description": "Desc C", "technologies": "Tech C"},
        ]
        results = service.generate_project_descriptions(projects, "Frontend Developer")
        assert len(results) == len(projects)

    def test_empty_projects_returns_empty(self, service):
        results = service.generate_project_descriptions([], "Full Stack Developer")
        assert results == []

    def test_preserves_all_titles_and_technologies(self, service):
        projects = [
            {"title": "Chat App", "description": "Real-time messaging", "technologies": "Socket.io, React"},
            {"title": "Blog CMS", "description": "Content management", "technologies": "Django, PostgreSQL"},
        ]
        results = service.generate_project_descriptions(projects, "Backend Developer")
        for i, project in enumerate(projects):
            assert results[i]["title"] == project["title"]
            assert results[i]["technologies"] == project["technologies"]


# -----------------------------------------------------------------------
# Fallback behavior when SpaCy is unavailable
# -----------------------------------------------------------------------

class TestSpacyFallback:
    """Validates: Requirement 2.5 — Graceful fallback when SpaCy unavailable."""

    @patch("app.services.ai_resume_service._nlp", None)
    def test_score_skill_relevance_without_spacy(self, service):
        """Service still scores skills using keyword matching when SpaCy is unavailable."""
        score = service.score_skill_relevance("React", "Full Stack Developer")
        # Direct match still works without SpaCy — score should be >= 0.6
        assert score >= 0.6
        assert 0.0 <= score <= 1.0

    @patch("app.services.ai_resume_service._nlp", None)
    def test_irrelevant_skill_without_spacy(self, service):
        """Irrelevant skills still score low without SpaCy."""
        score = service.score_skill_relevance("TensorFlow", "Full Stack Developer")
        assert score < 0.3

    @patch("app.services.ai_resume_service._nlp", None)
    def test_career_objective_without_spacy(self, service):
        """Career objective generation works without SpaCy."""
        result = service.generate_career_objective(
            dream_job="Full Stack Developer",
            degree="B.Tech",
            branch="Computer Science",
            skills=["React", "Python"],
            expected_lpa=5.0,
        )
        assert "Full Stack Developer" in result
        assert len(result) >= 50

    @patch("app.services.ai_resume_service._nlp", None)
    def test_prioritize_skills_without_spacy(self, service):
        """Skill prioritization works without SpaCy."""
        skills = ["React", "TensorFlow", "Python"]
        result = service.prioritize_skills(skills, "Full Stack Developer")
        assert set(result) == set(skills)
        assert len(result) == len(skills)
