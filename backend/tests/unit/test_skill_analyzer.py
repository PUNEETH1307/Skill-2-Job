"""Unit tests for the SkillAnalyzer service.

Tests cover skill normalization, categorization, vector generation,
unknown skill flagging, and skill extraction from text.
"""

import json

import numpy as np
import pytest

from app import db
from app.models import SkillTaxonomy, UncategorizedSkill, StudentProfile, User
from app.services.skill_analyzer import SkillAnalyzer
from seed import seed_skill_taxonomy


@pytest.fixture()
def analyzer():
    """Provide a SkillAnalyzer instance."""
    return SkillAnalyzer()


@pytest.fixture()
def seeded_taxonomy(db_session):
    """Seed the skill taxonomy and return the session."""
    seed_skill_taxonomy()
    return db_session


# ---------------------------------------------------------------------------
# normalize_skill
# ---------------------------------------------------------------------------

class TestNormalizeSkill:
    """Tests for SkillAnalyzer.normalize_skill."""

    def test_canonical_name_exact_match(self, seeded_taxonomy, analyzer):
        """Normalizing a canonical name returns itself."""
        result = analyzer.normalize_skill("Python")
        assert result == "Python"

    def test_canonical_name_case_insensitive(self, seeded_taxonomy, analyzer):
        """Canonical name lookup is case-insensitive."""
        result = analyzer.normalize_skill("python")
        assert result == "Python"

    def test_synonym_resolves_to_canonical(self, seeded_taxonomy, analyzer):
        """A known synonym maps to the canonical name."""
        result = analyzer.normalize_skill("JS")
        assert result == "JavaScript"

    def test_synonym_case_insensitive(self, seeded_taxonomy, analyzer):
        """Synonym lookup is case-insensitive."""
        result = analyzer.normalize_skill("reactjs")
        assert result == "React"

    def test_unknown_term_returns_original(self, seeded_taxonomy, analyzer):
        """An unknown term is returned as-is (stripped)."""
        result = analyzer.normalize_skill("UnknownSkill123")
        assert result == "UnknownSkill123"

    def test_whitespace_stripped(self, seeded_taxonomy, analyzer):
        """Leading/trailing whitespace is stripped."""
        result = analyzer.normalize_skill("  Python  ")
        assert result == "Python"


# ---------------------------------------------------------------------------
# categorize_skills
# ---------------------------------------------------------------------------

class TestCategorizeSkills:
    """Tests for SkillAnalyzer.categorize_skills."""

    def test_groups_by_category(self, seeded_taxonomy, analyzer):
        """Skills are grouped into their taxonomy categories."""
        skills = ["Python", "React", "MySQL"]
        result = analyzer.categorize_skills(skills)

        assert "Programming Languages" in result
        assert "Python" in result["Programming Languages"]
        assert "Frameworks" in result
        assert "React" in result["Frameworks"]
        assert "Databases" in result
        assert "MySQL" in result["Databases"]

    def test_multiple_skills_same_category(self, seeded_taxonomy, analyzer):
        """Multiple skills in the same category are grouped together."""
        skills = ["Python", "JavaScript", "Java"]
        result = analyzer.categorize_skills(skills)

        assert "Programming Languages" in result
        assert len(result["Programming Languages"]) == 3

    def test_unknown_skill_not_categorized(self, seeded_taxonomy, analyzer):
        """Unknown skills are not included in any category."""
        skills = ["Python", "FakeSkill"]
        result = analyzer.categorize_skills(skills)

        all_skills = []
        for cat_skills in result.values():
            all_skills.extend(cat_skills)
        assert "FakeSkill" not in all_skills

    def test_empty_list(self, seeded_taxonomy, analyzer):
        """An empty skill list produces an empty dict."""
        result = analyzer.categorize_skills([])
        assert result == {}


# ---------------------------------------------------------------------------
# generate_skill_vector
# ---------------------------------------------------------------------------

class TestGenerateSkillVector:
    """Tests for SkillAnalyzer.generate_skill_vector."""

    def test_correct_dimension(self, seeded_taxonomy, analyzer):
        """Vector dimension equals the number of non-deprecated taxonomy entries."""
        taxonomy_size = SkillTaxonomy.query.filter_by(is_deprecated=False).count()
        vector = analyzer.generate_skill_vector(["Python"])
        assert len(vector) == taxonomy_size

    def test_correct_indices_set(self, seeded_taxonomy, analyzer):
        """Known skills set the correct indices to 1.0."""
        taxonomy = (
            SkillTaxonomy.query
            .filter_by(is_deprecated=False)
            .order_by(SkillTaxonomy.id)
            .all()
        )
        name_to_idx = {s.canonical_name.lower(): i for i, s in enumerate(taxonomy)}

        vector = analyzer.generate_skill_vector(["Python", "React"])

        assert vector[name_to_idx["python"]] == 1.0
        assert vector[name_to_idx["react"]] == 1.0
        # A skill not in the input should be 0.0
        assert vector[name_to_idx["java"]] == 0.0

    def test_returns_numpy_array(self, seeded_taxonomy, analyzer):
        """The result is a numpy ndarray."""
        vector = analyzer.generate_skill_vector(["Python"])
        assert isinstance(vector, np.ndarray)

    def test_empty_skills_all_zeros(self, seeded_taxonomy, analyzer):
        """An empty skill list produces an all-zero vector."""
        vector = analyzer.generate_skill_vector([])
        assert np.sum(vector) == 0.0

    def test_synonym_input_sets_correct_index(self, seeded_taxonomy, analyzer):
        """Passing a synonym normalizes it and sets the correct index."""
        taxonomy = (
            SkillTaxonomy.query
            .filter_by(is_deprecated=False)
            .order_by(SkillTaxonomy.id)
            .all()
        )
        name_to_idx = {s.canonical_name.lower(): i for i, s in enumerate(taxonomy)}

        vector = analyzer.generate_skill_vector(["JS"])  # synonym for JavaScript
        assert vector[name_to_idx["javascript"]] == 1.0


# ---------------------------------------------------------------------------
# generate_job_requirement_vector
# ---------------------------------------------------------------------------

class TestGenerateJobRequirementVector:
    """Tests for SkillAnalyzer.generate_job_requirement_vector."""

    def test_same_as_skill_vector(self, seeded_taxonomy, analyzer):
        """Job requirement vector works identically to skill vector."""
        skills = ["Python", "Flask", "MySQL"]
        skill_vec = analyzer.generate_skill_vector(skills)
        job_vec = analyzer.generate_job_requirement_vector(skills)
        np.testing.assert_array_equal(skill_vec, job_vec)

    def test_correct_dimension(self, seeded_taxonomy, analyzer):
        """Vector dimension equals taxonomy size."""
        taxonomy_size = SkillTaxonomy.query.filter_by(is_deprecated=False).count()
        vector = analyzer.generate_job_requirement_vector(["Docker", "AWS"])
        assert len(vector) == taxonomy_size


# ---------------------------------------------------------------------------
# flag_unknown_skill
# ---------------------------------------------------------------------------

class TestFlagUnknownSkill:
    """Tests for SkillAnalyzer.flag_unknown_skill."""

    def test_creates_new_entry(self, seeded_taxonomy, analyzer):
        """Flagging a new term creates an UncategorizedSkill with count 1."""
        analyzer.flag_unknown_skill("BrandNewSkill")

        entry = UncategorizedSkill.query.filter_by(term="BrandNewSkill").first()
        assert entry is not None
        assert entry.occurrence_count == 1

    def test_increments_existing_entry(self, seeded_taxonomy, analyzer):
        """Flagging an existing term increments its occurrence_count."""
        analyzer.flag_unknown_skill("RepeatedSkill")
        analyzer.flag_unknown_skill("RepeatedSkill")

        entry = UncategorizedSkill.query.filter(
            db.func.lower(UncategorizedSkill.term) == "repeatedskill"
        ).first()
        assert entry is not None
        assert entry.occurrence_count == 2

    def test_empty_term_ignored(self, seeded_taxonomy, analyzer):
        """An empty or whitespace-only term is not flagged."""
        analyzer.flag_unknown_skill("   ")
        count = UncategorizedSkill.query.count()
        assert count == 0


# ---------------------------------------------------------------------------
# extract_skills
# ---------------------------------------------------------------------------

class TestExtractSkills:
    """Tests for SkillAnalyzer.extract_skills."""

    def test_finds_known_skills_in_text(self, seeded_taxonomy, analyzer):
        """Known skills are extracted from comma-separated text."""
        text = "Python, JavaScript, React, MySQL"
        result = analyzer.extract_skills(text)

        assert "Python" in result
        assert "JavaScript" in result
        assert "React" in result
        assert "MySQL" in result

    def test_resolves_synonyms_in_text(self, seeded_taxonomy, analyzer):
        """Synonyms in the text are resolved to canonical names."""
        text = "JS, reactjs, py"
        result = analyzer.extract_skills(text)

        assert "JavaScript" in result
        assert "React" in result
        assert "Python" in result

    def test_deduplicates_results(self, seeded_taxonomy, analyzer):
        """Duplicate mentions produce a single entry."""
        text = "Python, python, py"
        result = analyzer.extract_skills(text)

        assert result.count("Python") == 1

    def test_empty_text_returns_empty(self, seeded_taxonomy, analyzer):
        """Empty input returns an empty list."""
        result = analyzer.extract_skills("")
        assert result == []

    def test_ignores_unknown_terms(self, seeded_taxonomy, analyzer):
        """Unknown terms are not included in the result."""
        text = "Python, SomeRandomThing, JavaScript"
        result = analyzer.extract_skills(text)

        assert "Python" in result
        assert "JavaScript" in result
        assert "SomeRandomThing" not in result

    def test_multiline_text(self, seeded_taxonomy, analyzer):
        """Skills are extracted from multiline text."""
        text = "Python\nJavaScript\nDocker"
        result = analyzer.extract_skills(text)

        assert "Python" in result
        assert "JavaScript" in result
        assert "Docker" in result
