"""Job Role Knowledge Base for the AI Resume Generation feature.

Provides structured knowledge about common job roles, their required
skills, and associated keywords for relevance scoring and template
selection.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 10.1, 10.2, 10.3, 10.4
"""


class JobRoleKnowledgeBase:
    """Static knowledge base mapping job roles to skills and keywords."""

    JOB_ROLE_DATABASE: dict[str, dict] = {
        "full stack developer": {
            "keywords": ["frontend", "backend", "api", "database", "web", "fullstack", "full-stack"],
            "skills": ["JavaScript", "React", "Node.js", "Python", "SQL", "REST API", "HTML", "CSS"],
            "level_keywords": {
                "entry": ["aspiring", "eager to learn", "foundational knowledge"],
                "mid": ["experienced", "proficient", "hands-on experience"],
                "senior": ["expert", "architecting", "leading", "mentoring"],
            },
        },
        "data scientist": {
            "keywords": ["data", "analytics", "machine learning", "statistics", "modeling", "analysis"],
            "skills": ["Python", "Machine Learning", "Pandas", "NumPy", "SQL", "TensorFlow", "Statistics"],
            "level_keywords": {
                "entry": ["aspiring", "foundational understanding", "academic projects"],
                "mid": ["experienced", "applied", "production models"],
                "senior": ["expert", "research", "leading data teams"],
            },
        },
        "frontend developer": {
            "keywords": ["frontend", "ui", "ux", "web", "interface", "responsive", "design"],
            "skills": ["JavaScript", "React", "TypeScript", "HTML", "CSS", "Vue.js", "Angular"],
            "level_keywords": {
                "entry": ["aspiring", "creative", "foundational skills"],
                "mid": ["experienced", "proficient", "component architecture"],
                "senior": ["expert", "design systems", "leading frontend teams"],
            },
        },
        "backend developer": {
            "keywords": ["backend", "server", "api", "database", "microservices", "scalability"],
            "skills": ["Python", "Java", "Node.js", "SQL", "REST API", "Docker", "PostgreSQL"],
            "level_keywords": {
                "entry": ["aspiring", "eager to build", "foundational knowledge"],
                "mid": ["experienced", "proficient", "scalable systems"],
                "senior": ["expert", "architecting", "distributed systems", "mentoring"],
            },
        },
        "devops engineer": {
            "keywords": ["devops", "ci/cd", "cloud", "infrastructure", "automation", "deployment", "kubernetes"],
            "skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform", "Python", "Git"],
            "level_keywords": {
                "entry": ["aspiring", "learning automation", "foundational cloud knowledge"],
                "mid": ["experienced", "proficient", "pipeline management"],
                "senior": ["expert", "infrastructure architecture", "leading platform teams"],
            },
        },
        "machine learning engineer": {
            "keywords": ["machine learning", "ml", "deep learning", "ai", "neural networks", "model deployment"],
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "NumPy", "Scikit-learn", "Docker"],
            "level_keywords": {
                "entry": ["aspiring", "academic ML projects", "foundational understanding"],
                "mid": ["experienced", "production ML pipelines", "model optimization"],
                "senior": ["expert", "ML architecture", "research", "leading ML teams"],
            },
        },
    }

    def get_role_keywords(self, dream_job: str) -> list[str]:
        """Get keywords associated with a job role.

        Args:
            dream_job: The dream job title string.

        Returns:
            List of keywords for the matched role, or empty list if unknown.
        """
        matched_role = self.match_role(dream_job)
        if matched_role and matched_role in self.JOB_ROLE_DATABASE:
            return self.JOB_ROLE_DATABASE[matched_role]["keywords"]
        return []

    def get_role_skills(self, dream_job: str) -> list[str]:
        """Get expected skills for a job role.

        Args:
            dream_job: The dream job title string.

        Returns:
            List of expected skills for the matched role, or empty list if unknown.
        """
        matched_role = self.match_role(dream_job)
        if matched_role and matched_role in self.JOB_ROLE_DATABASE:
            return self.JOB_ROLE_DATABASE[matched_role]["skills"]
        return []

    def get_experience_level(self, expected_lpa: float | None) -> str:
        """Map expected LPA to experience level.

        Thresholds (Indian tech market):
        - entry: 0-6 LPA (or None)
        - mid: (6, 15] LPA
        - senior: >15 LPA

        Args:
            expected_lpa: Expected salary in Lakhs Per Annum, or None.

        Returns:
            One of "entry", "mid", "senior".
        """
        if expected_lpa is None:
            return "entry"

        if expected_lpa <= 6.0:
            return "entry"
        elif expected_lpa <= 15.0:
            return "mid"
        else:
            return "senior"

    def match_role(self, dream_job: str) -> str | None:
        """Fuzzy-match a dream job string to a known role category.

        Uses case-insensitive substring matching and token overlap
        to find the best matching role.

        Args:
            dream_job: The dream job title string.

        Returns:
            The matched role key from JOB_ROLE_DATABASE, or None if no match.
        """
        if not dream_job or not dream_job.strip():
            return None

        normalized = dream_job.strip().lower()

        # 1. Exact match
        if normalized in self.JOB_ROLE_DATABASE:
            return normalized

        # 2. Substring match: check if any known role is a substring of the input
        for role_key in self.JOB_ROLE_DATABASE:
            if role_key in normalized:
                return role_key

        # 3. Check if input is a substring of any known role
        for role_key in self.JOB_ROLE_DATABASE:
            if normalized in role_key:
                return role_key

        # 4. Token overlap: split both into tokens and find best overlap
        input_tokens = set(normalized.split())
        best_match = None
        best_overlap = 0

        for role_key in self.JOB_ROLE_DATABASE:
            role_tokens = set(role_key.split())
            overlap = len(input_tokens & role_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = role_key

        # Require at least one token overlap
        if best_overlap > 0:
            return best_match

        return None
