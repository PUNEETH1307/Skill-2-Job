"""Skill Analyzer service for the Skill2Job Placement System.

Provides NLP-based skill extraction, normalization, categorization,
and vector generation for student profiles and job roles.

Uses SpaCy for tokenization when available, falling back to simple
string-based matching otherwise.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

import json
import re

import numpy as np

from app import db
from app.models import SkillTaxonomy, UncategorizedSkill, StudentProfile

# ---------------------------------------------------------------------------
# Optional SpaCy loading
# ---------------------------------------------------------------------------

_nlp = None

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    # SpaCy not installed or model not available — fall back to simple
    # string-based tokenization.
    pass


class SkillAnalyzer:
    """Extract, normalize, categorize, and vectorize skills.

    The analyzer works against the ``SkillTaxonomy`` table for canonical
    skill names and synonym resolution.  When SpaCy is available it is
    used for richer tokenization; otherwise a simple regex/split
    approach is used.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_skills(self, profile_text: str) -> list[str]:
        """Extract known skill terms from free-text profile content.

        The *profile_text* is expected to be a concatenation of the
        student's skills list and project descriptions.

        Steps:
            1. Tokenize the text (split by commas, newlines, semicolons,
               pipes, and similar delimiters).
            2. For each token, attempt to normalize against the taxonomy.
            3. Return a deduplicated list of canonical skill names found.

        Args:
            profile_text: Raw text containing skill mentions.

        Returns:
            List of canonical skill names found in the text.
        """
        if not profile_text or not profile_text.strip():
            return []

        tokens = self._tokenize(profile_text)
        found: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            canonical = self.normalize_skill(token)
            # Check if the canonical name actually exists in the taxonomy
            match = SkillTaxonomy.query.filter(
                db.func.lower(SkillTaxonomy.canonical_name) == canonical.lower()
            ).first()
            if match and not match.is_deprecated:
                if match.canonical_name not in seen:
                    found.append(match.canonical_name)
                    seen.add(match.canonical_name)

        return found

    def normalize_skill(self, skill_term: str) -> str:
        """Map a skill term to its canonical name using the taxonomy.

        Lookup order:
            1. Exact match on ``canonical_name`` (case-insensitive).
            2. Search ``synonyms_json`` fields for a match (case-insensitive).
            3. Return the original term (stripped) if no match is found.

        Args:
            skill_term: The raw skill term to normalize.

        Returns:
            The canonical skill name, or the original term if unrecognized.
        """
        term = skill_term.strip()
        if not term:
            return term

        # 1. Exact match on canonical_name (case-insensitive)
        match = SkillTaxonomy.query.filter(
            db.func.lower(SkillTaxonomy.canonical_name) == term.lower()
        ).first()
        if match:
            return match.canonical_name

        # 2. Search synonyms_json for a match
        all_skills = SkillTaxonomy.query.all()
        for skill in all_skills:
            if skill.synonyms_json:
                try:
                    synonyms = json.loads(skill.synonyms_json)
                except (json.JSONDecodeError, TypeError):
                    continue
                for synonym in synonyms:
                    if synonym.strip().lower() == term.lower():
                        return skill.canonical_name

        # 3. No match — return original term
        return term

    def categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """Group normalized skills by their taxonomy category.

        Args:
            skills: List of skill names (should be canonical names).

        Returns:
            Dict mapping category names to lists of skill names, e.g.
            ``{"Programming Languages": ["Python", "Java"], ...}``.
        """
        categories: dict[str, list[str]] = {}

        for skill_name in skills:
            entry = SkillTaxonomy.query.filter(
                db.func.lower(SkillTaxonomy.canonical_name) == skill_name.lower()
            ).first()
            if entry and entry.category:
                categories.setdefault(entry.category, []).append(entry.canonical_name)

        return categories

    def generate_skill_vector(self, skills: list[str]) -> np.ndarray:
        """Build a binary vector over the full skill taxonomy vocabulary.

        The vector dimension equals the number of non-deprecated skills in
        the taxonomy, sorted by ``id``.  For each input skill, the
        corresponding index is set to ``1.0``.

        Args:
            skills: List of skill names to encode.

        Returns:
            A 1-D numpy array of floats (0.0 or 1.0).
        """
        return self._build_vector(skills)

    def generate_job_requirement_vector(self, required_skills: list[str]) -> np.ndarray:
        """Build a binary vector for a job role's required skills.

        Works identically to :meth:`generate_skill_vector`.

        Args:
            required_skills: List of required skill names.

        Returns:
            A 1-D numpy array of floats (0.0 or 1.0).
        """
        return self._build_vector(required_skills)

    def flag_unknown_skill(self, skill_term: str) -> None:
        """Flag an unrecognized skill term for admin review.

        If the term already exists in ``UncategorizedSkill``, its
        ``occurrence_count`` is incremented.  Otherwise a new row is
        created with ``occurrence_count=1``.

        Args:
            skill_term: The unknown skill term to flag.
        """
        term = skill_term.strip()
        if not term:
            return

        existing = UncategorizedSkill.query.filter(
            db.func.lower(UncategorizedSkill.term) == term.lower()
        ).first()

        if existing:
            existing.occurrence_count += 1
        else:
            entry = UncategorizedSkill(term=term, occurrence_count=1)
            db.session.add(entry)

        db.session.commit()

    def analyze_and_store(self, profile: StudentProfile) -> dict:
        """Run full skill analysis on a student profile and persist results.

        When the taxonomy is empty or skills are not recognized, falls back
        to using the raw skills_json directly so students always see their skills.

        Args:
            profile: The StudentProfile instance to analyze.

        Returns:
            Dict with ``skills``, ``categories``, and ``vector_stored``.
        """
        # Build profile text
        parts: list[str] = []

        raw_skills_list: list[str] = []
        if profile.skills_json:
            try:
                skills_list = json.loads(profile.skills_json)
                if isinstance(skills_list, list):
                    raw_skills_list = [str(s).strip() for s in skills_list if str(s).strip()]
                    parts.append(", ".join(raw_skills_list))
            except (json.JSONDecodeError, TypeError):
                pass

        for project in profile.projects:
            if project.description:
                parts.append(project.description)
            if project.technologies:
                parts.append(project.technologies)

        profile_text = "\n".join(parts)

        # Extract skills via taxonomy matching
        extracted = self.extract_skills(profile_text)

        # ── Fallback: if taxonomy is empty or no skills matched, use raw list ──
        if not extracted and raw_skills_list:
            extracted = raw_skills_list

        # Flag unknown terms (only when taxonomy has entries)
        taxonomy_count = SkillTaxonomy.query.filter_by(is_deprecated=False).count()
        if taxonomy_count > 0:
            tokens = self._tokenize(profile_text)
            for token in tokens:
                normalized = self.normalize_skill(token)
                match = SkillTaxonomy.query.filter(
                    db.func.lower(SkillTaxonomy.canonical_name) == normalized.lower()
                ).first()
                if not match and normalized:
                    self.flag_unknown_skill(normalized)

        # Generate vector (will be all-zeros if taxonomy is empty — that's OK)
        vector = self.generate_skill_vector(extracted)

        # Build skill index
        taxonomy = (
            SkillTaxonomy.query
            .filter_by(is_deprecated=False)
            .order_by(SkillTaxonomy.id)
            .all()
        )
        skill_index = {
            skill.canonical_name.lower(): idx
            for idx, skill in enumerate(taxonomy)
        }

        # Store on profile
        vector_data = {
            "vector": vector.tolist(),
            "skill_index": skill_index,
            "version": "1.0",
        }
        profile.skill_vector_json = json.dumps(vector_data)
        db.session.commit()

        # Categorize — fallback to 'Skills' bucket if taxonomy empty
        categories = self.categorize_skills(extracted)
        if not categories and extracted:
            categories = {"Skills": extracted}

        return {
            "skills": extracted,
            "categories": categories,
            "vector_stored": True,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into candidate skill terms.

        Uses SpaCy when available for richer tokenization, otherwise
        splits on common delimiters (commas, newlines, semicolons, pipes).

        Returns:
            List of stripped, non-empty token strings.
        """
        if _nlp is not None:
            doc = _nlp(text)
            # Use noun chunks and individual tokens
            candidates: list[str] = []
            for chunk in doc.noun_chunks:
                candidates.append(chunk.text.strip())
            for token in doc:
                if not token.is_stop and not token.is_punct and len(token.text.strip()) > 1:
                    candidates.append(token.text.strip())
            return [c for c in candidates if c]

        # Fallback: split on delimiters
        raw_tokens = re.split(r"[,\n;|]+", text)
        tokens: list[str] = []
        for raw in raw_tokens:
            stripped = raw.strip()
            if stripped:
                tokens.append(stripped)
        return tokens

    def _build_vector(self, skills: list[str]) -> np.ndarray:
        """Build a binary vector from a list of skill names.

        Args:
            skills: Skill names to encode (will be normalized).

        Returns:
            1-D numpy float array with dimension = taxonomy size.
        """
        taxonomy = (
            SkillTaxonomy.query
            .filter_by(is_deprecated=False)
            .order_by(SkillTaxonomy.id)
            .all()
        )

        vector = np.zeros(len(taxonomy), dtype=float)

        # Build a lookup: canonical_name (lower) -> index
        name_to_idx: dict[str, int] = {}
        for idx, skill in enumerate(taxonomy):
            name_to_idx[skill.canonical_name.lower()] = idx

        for skill_name in skills:
            canonical = self.normalize_skill(skill_name)
            key = canonical.lower()
            if key in name_to_idx:
                vector[name_to_idx[key]] = 1.0

        return vector
