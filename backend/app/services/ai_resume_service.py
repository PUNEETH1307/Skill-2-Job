"""AI Resume Service for the Skill2Job Placement System.

Provides NLP-based skill scoring, template-based content generation,
and intelligent resume content orchestration tailored to a student's
dream job and expected salary level.

Requirements: 2.1-2.5, 4.1-4.6, 5.1-5.3, 6.1-6.5, 7.1-7.4, 9.1-9.4
"""

import json
import logging
from dataclasses import dataclass, field

from app.services.job_role_knowledge_base import JobRoleKnowledgeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional SpaCy loading (reuse pattern from skill_analyzer.py)
# ---------------------------------------------------------------------------

_nlp = None

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    pass


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AIResumeContent:
    """Container for AI-generated resume content sections."""
    career_objective: str
    professional_summary: str
    prioritized_skills: list[str]
    skill_categories: dict[str, list[str]]
    project_descriptions: list[dict]
    experience_level: str  # "entry", "mid", "senior"


# ---------------------------------------------------------------------------
# AIResumeService
# ---------------------------------------------------------------------------

class AIResumeService:
    """AI-powered resume content generator using SpaCy and rule-based NLP."""

    def __init__(self):
        self.knowledge_base = JobRoleKnowledgeBase()

    def score_skill_relevance(self, skill: str, dream_job: str) -> float:
        """Score a skill's relevance to the dream job (0.0 to 1.0).

        Uses three scoring signals:
        1. Direct match: skill appears in the role's expected skills list (0.6 weight)
        2. Keyword overlap: skill tokens overlap with role keywords (0.25 weight)
        3. NLP similarity: SpaCy word vector cosine similarity (0.15 weight)

        Args:
            skill: The skill name to score.
            dream_job: The target job role.

        Returns:
            A float in [0.0, 1.0].
        """
        if not skill or not dream_job:
            return 0.0

        score = 0.0

        # Signal 1: Direct skill match (highest weight)
        role_skills = self.knowledge_base.get_role_skills(dream_job)
        if skill.lower() in [s.lower() for s in role_skills]:
            score += 0.6

        # Signal 2: Keyword overlap
        role_keywords = self.knowledge_base.get_role_keywords(dream_job)
        skill_tokens = set(skill.lower().split())
        keyword_set = set(k.lower() for k in role_keywords)
        overlap = skill_tokens & keyword_set
        if overlap and skill_tokens:
            score += 0.25 * (len(overlap) / len(skill_tokens))

        # Signal 3: NLP similarity (SpaCy vectors)
        if _nlp is not None:
            try:
                skill_doc = _nlp(skill.lower())
                job_doc = _nlp(dream_job.lower())
                if skill_doc.vector_norm and job_doc.vector_norm:
                    similarity = skill_doc.similarity(job_doc)
                    score += 0.15 * max(0.0, similarity)
            except Exception:
                pass

        return min(1.0, max(0.0, score))

    def prioritize_skills(self, skills: list[str], dream_job: str) -> list[str]:
        """Reorder skills by relevance to the dream job.

        Args:
            skills: List of skill names.
            dream_job: The target job role.

        Returns:
            A list containing the same elements, sorted by descending relevance.
            Returns original list unchanged if skills or dream_job is empty.
        """
        if not skills or not dream_job:
            return skills

        scored = [
            (skill, self.score_skill_relevance(skill, dream_job))
            for skill in skills
        ]

        # Stable sort: skills with equal relevance keep original order
        scored.sort(key=lambda x: x[1], reverse=True)

        return [skill for skill, _ in scored]

    def generate_career_objective(
        self,
        dream_job: str,
        degree: str,
        branch: str,
        skills: list[str],
        expected_lpa: float | None,
    ) -> str:
        """Generate a personalized career objective statement.

        Args:
            dream_job: The target job role.
            degree: The student's degree.
            branch: The student's branch/major.
            skills: List of student's skills.
            expected_lpa: Expected salary in LPA (or None).

        Returns:
            A career objective string between 50 and 500 characters.
        """
        level = self.knowledge_base.get_experience_level(expected_lpa)

        # Get top 3 relevant skills
        if skills:
            scored_skills = [
                (skill, self.score_skill_relevance(skill, dream_job))
                for skill in skills
            ]
            scored_skills.sort(key=lambda x: x[1], reverse=True)
            top_skills = [s[0] for s in scored_skills[:3]]
        else:
            top_skills = []

        templates = {
            "entry": (
                "Motivated {degree} graduate in {branch} seeking a {dream_job} role "
                "to apply skills in {skills_str}. Eager to contribute to innovative "
                "projects and grow professionally in a collaborative environment."
            ),
            "mid": (
                "Results-driven {degree} professional specializing in {branch} with "
                "hands-on experience in {skills_str}. Seeking a {dream_job} position "
                "to leverage technical expertise and deliver impactful solutions."
            ),
            "senior": (
                "Accomplished {degree} professional in {branch} with deep expertise "
                "in {skills_str}. Targeting a senior {dream_job} role to architect "
                "scalable solutions and mentor engineering teams."
            ),
        }

        template = templates.get(level, templates["entry"])
        skills_str = ", ".join(top_skills) if top_skills else "relevant technologies"

        result = template.format(
            degree=degree or "technology",
            branch=branch or "engineering",
            dream_job=dream_job,
            skills_str=skills_str,
        )

        # Ensure length bounds [50, 500]
        if len(result) < 50:
            result = result + " " + "Committed to continuous learning and professional development."
        if len(result) > 500:
            result = result[:497] + "..."

        return result

    def generate_professional_summary(
        self,
        dream_job: str,
        skills: list[str],
        projects: list,
        cgpa: float | None,
        graduation_year: int | None,
    ) -> str:
        """Generate a professional summary highlighting relevant experience.

        Args:
            dream_job: The target job role.
            skills: List of student's skills.
            projects: List of project objects or dicts.
            cgpa: Student's CGPA (or None).
            graduation_year: Expected graduation year (or None).

        Returns:
            A non-empty professional summary string.
        """
        # Get top relevant skills
        if skills:
            prioritized = self.prioritize_skills(skills, dream_job)
            top_skills = prioritized[:5]
        else:
            top_skills = []

        skills_str = ", ".join(top_skills) if top_skills else "various technologies"

        # Build project reference
        project_count = len(projects) if projects else 0
        project_ref = ""
        if project_count > 0:
            project_ref = f" with {project_count} project{'s' if project_count > 1 else ''} demonstrating practical application"

        # Build academic reference
        academic_ref = ""
        if cgpa is not None and cgpa >= 7.0:
            academic_ref = f" maintaining a strong academic record (CGPA: {cgpa})"

        # Build graduation reference
        grad_ref = ""
        if graduation_year is not None:
            grad_ref = f" (Class of {graduation_year})"

        summary = (
            f"Technically proficient professional with expertise in {skills_str}"
            f"{project_ref}{academic_ref}{grad_ref}. "
            f"Passionate about {dream_job} and committed to delivering high-quality solutions "
            f"that drive business value."
        )

        return summary

    def generate_project_descriptions(
        self,
        projects: list,
        dream_job: str,
    ) -> list[dict]:
        """Generate enhanced project descriptions aligned with dream job.

        Args:
            projects: List of project objects (with title, description, technologies attributes)
                      or dicts with those keys.
            dream_job: The target job role.

        Returns:
            List of dicts with keys: title, description, technologies, relevance_note.
            Output list length equals input list length.
        """
        if not projects:
            return []

        role_keywords = self.knowledge_base.get_role_keywords(dream_job)
        role_skills = self.knowledge_base.get_role_skills(dream_job)

        results = []
        for project in projects:
            # Support both objects and dicts
            if isinstance(project, dict):
                title = project.get("title", "")
                description = project.get("description", "") or ""
                technologies = project.get("technologies", "") or ""
            else:
                title = getattr(project, "title", "")
                description = getattr(project, "description", "") or ""
                technologies = getattr(project, "technologies", "") or ""

            # Determine relevance
            project_text = f"{title} {description} {technologies}".lower()
            project_tokens = set(project_text.split())

            keyword_set = set(k.lower() for k in role_keywords)
            skill_set = set(s.lower() for s in role_skills)

            keyword_overlap = project_tokens & keyword_set
            skill_overlap = project_tokens & skill_set

            # Generate relevance note
            relevance_note = ""
            if keyword_overlap or skill_overlap:
                relevant_terms = list(keyword_overlap | skill_overlap)[:3]
                relevance_note = (
                    f"Relevant to {dream_job}: demonstrates experience with "
                    f"{', '.join(relevant_terms)}."
                )

            # Enhanced description
            enhanced_description = description
            if not enhanced_description:
                enhanced_description = f"Project focused on {title}."

            results.append({
                "title": title,
                "description": enhanced_description,
                "technologies": technologies,
                "relevance_note": relevance_note,
            })

        return results

    def generate_ai_content(self, profile, user) -> AIResumeContent:
        """Main orchestrator for AI resume content generation.

        Args:
            profile: A StudentProfile instance with dream_job set.
            user: The User instance associated with the profile.

        Returns:
            A fully populated AIResumeContent instance.
        """
        dream_job = profile.dream_job
        expected_lpa = profile.expected_lpa

        # Parse skills
        skills = []
        if profile.skills_json:
            try:
                parsed = json.loads(profile.skills_json)
                if isinstance(parsed, list):
                    skills = [str(s).strip() for s in parsed if str(s).strip()]
            except (json.JSONDecodeError, TypeError):
                pass

        # Get experience level
        experience_level = self.knowledge_base.get_experience_level(expected_lpa)

        # Generate career objective
        career_objective = self.generate_career_objective(
            dream_job=dream_job,
            degree=profile.degree or "technology",
            branch=profile.branch or "engineering",
            skills=skills,
            expected_lpa=expected_lpa,
        )

        # Generate professional summary
        professional_summary = self.generate_professional_summary(
            dream_job=dream_job,
            skills=skills,
            projects=list(profile.projects) if profile.projects else [],
            cgpa=profile.cgpa,
            graduation_year=profile.graduation_year,
        )

        # Prioritize skills
        prioritized_skills = self.prioritize_skills(skills, dream_job)

        # Categorize skills
        skill_categories = self._categorize_skills(prioritized_skills, dream_job)

        # Generate project descriptions
        project_descriptions = self.generate_project_descriptions(
            projects=list(profile.projects) if profile.projects else [],
            dream_job=dream_job,
        )

        return AIResumeContent(
            career_objective=career_objective,
            professional_summary=professional_summary,
            prioritized_skills=prioritized_skills,
            skill_categories=skill_categories,
            project_descriptions=project_descriptions,
            experience_level=experience_level,
        )

    def _categorize_skills(self, skills: list[str], dream_job: str) -> dict[str, list[str]]:
        """Group skills into categories for resume display.

        Args:
            skills: List of skill names (already prioritized).
            dream_job: The target job role.

        Returns:
            Dict mapping category names to lists of skills.
        """
        category_keywords = {
            "Programming Languages": {"python", "java", "javascript", "typescript", "c", "c++", "c#", "php", "go", "rust"},
            "Web & Frameworks": {"react", "angular", "vue.js", "node.js", "flask", "django", "express", "html", "css"},
            "Data & ML": {"machine learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "statistics"},
            "Databases": {"sql", "mysql", "postgresql", "mongodb", "sqlite", "redis"},
            "DevOps & Cloud": {"docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "terraform", "linux", "git"},
        }

        grouped: dict[str, list[str]] = {}
        others: list[str] = []

        for skill in skills:
            normalized = skill.lower()
            matched_label = None
            for label, keywords in category_keywords.items():
                if normalized in keywords or any(kw in normalized for kw in keywords):
                    matched_label = label
                    break
            if matched_label:
                grouped.setdefault(matched_label, []).append(skill)
            else:
                others.append(skill)

        if others:
            grouped["Other"] = others

        return grouped
