"""Resume generator service for the Skill2Job Placement System.

Produces professional PDF resumes from student profile data using
ReportLab. Validates that required profile fields are present before
generation and provides a standardised download filename.

When a student has set a dream_job, the generator uses AIResumeService
to produce tailored content. Falls back to template-based generation
when dream_job is absent or AI generation fails.
"""

import json
import logging
import re
from datetime import date
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from app import db
from app.models import StudentProfile, User

logger = logging.getLogger(__name__)


class ResumeGenerator:
    """Generate professional PDF resumes from student profile data.

    Usage::

        gen = ResumeGenerator()
        valid, missing = gen.validate_profile(profile_dict)
        pdf_bytes = gen.generate_resume(student_id)
        filename = gen.get_download_filename("John Doe")
    """

    # Required fields for resume generation
    REQUIRED_FIELDS = {
        "name": "name",
        "institution": "institution",
        "degree": "degree",
        "branch": "branch",
        "skills_json": "skills",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_profile(self, profile: dict) -> tuple[bool, list[str]]:
        """Check whether a profile dict has all required fields.

        Args:
            profile: A dict containing profile data. Expected keys include
                ``name`` (from User), ``institution``, ``degree``, and
                ``skills_json`` (a non-empty JSON array string or list).

        Returns:
            A tuple ``(valid, missing_fields)`` where *valid* is ``True``
            when all required fields are present and *missing_fields* is a
            list of human-readable names for any absent fields.
        """
        missing: list[str] = []

        for field_key, display_name in self.REQUIRED_FIELDS.items():
            value = profile.get(field_key)

            if field_key == "skills_json":
                # skills_json must be a non-empty JSON array
                if not self._has_valid_skills(value):
                    missing.append(display_name)
            else:
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing.append(display_name)

        return (len(missing) == 0, missing)

    def generate_resume(self, student_id: int) -> bytes:
        """Generate a PDF resume for the given student.

        Fetches the latest profile from the database, validates required
        fields, and builds a professional PDF document.

        Args:
            student_id: The ``User.id`` of the student.

        Returns:
            Raw PDF bytes.

        Raises:
            ValueError: If the student has no profile or the profile is
                missing required fields.
        """
        # 1. Fetch profile and user
        profile = StudentProfile.query.filter_by(user_id=student_id).first()
        if profile is None:
            raise ValueError("Student profile not found")

        user = db.session.get(User, student_id)
        if user is None:
            raise ValueError("User not found")

        # 2. Build a combined dict for validation
        profile_dict = profile.to_dict()
        profile_dict["name"] = user.name
        profile_dict["email"] = user.email
        profile_dict["phone"] = user.phone

        # 3. Validate
        valid, missing = self.validate_profile(profile_dict)
        if not valid:
            raise ValueError(f"Profile is missing required fields: {', '.join(missing)}")

        # 4. Build PDF — use AI content when dream_job is set
        if profile.dream_job and profile.dream_job.strip():
            try:
                from app.services.ai_resume_service import AIResumeService
                ai_service = AIResumeService()
                ai_content = ai_service.generate_ai_content(profile, user)
                return self._build_pdf_with_ai_content(profile_dict, profile, ai_content)
            except Exception:
                logger.exception(
                    "AIResumeService failed for user_id=%s; falling back to "
                    "template-based generation",
                    student_id,
                )

        return self._build_pdf(profile_dict, profile)

    def get_download_filename(self, student_name: str) -> str:
        """Return a standardised download filename for the resume.

        Format: ``Resume_{Name}_{YYYY-MM-DD}.pdf`` with spaces replaced
        by underscores.

        Args:
            student_name: The student's full name.

        Returns:
            The formatted filename string.
        """
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", student_name.strip())
        safe_name = re.sub(r"_+", "_", safe_name).strip("_") or "Student"
        today = date.today().isoformat()
        return f"Resume_{safe_name}_{today}.pdf"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _has_valid_skills(value) -> bool:
        """Return True if *value* represents a non-empty skills list."""
        if value is None:
            return False

        if isinstance(value, list):
            return len(value) > 0

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return False
            try:
                parsed = json.loads(value)
                return isinstance(parsed, list) and len(parsed) > 0
            except (json.JSONDecodeError, TypeError):
                return False

        return False

    def _build_pdf(self, profile_dict: dict, profile: StudentProfile) -> bytes:
        """Construct the PDF document and return its bytes."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        elements: list = []

        # Custom styles
        title_style = ParagraphStyle(
            "ResumeTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=4,
            textColor=colors.HexColor("#1a237e"),
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1a237e"),
            spaceBefore=12,
            spaceAfter=4,
        )
        body_style = styles["Normal"]
        body_style.fontSize = 10
        body_style.leading = 14
        body_style.spaceAfter = 3
        muted_style = ParagraphStyle(
            "Muted",
            parent=body_style,
            textColor=colors.HexColor("#4b5563"),
        )
        bullet_style = ParagraphStyle(
            "ResumeBullet",
            parent=body_style,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )

        # --- Personal Info ---
        elements.append(Paragraph(self._safe_text(profile_dict.get("name", "")), title_style))

        contact_parts: list[str] = []
        if profile_dict.get("email"):
            contact_parts.append(profile_dict["email"])
        if profile_dict.get("phone"):
            contact_parts.append(profile_dict["phone"])
        if contact_parts:
            elements.append(Paragraph(self._safe_text(" | ".join(contact_parts)), muted_style))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
        elements.append(Spacer(1, 6))

        # --- Career Summary ---
        skills = self._parse_skills(profile_dict.get("skills_json"))
        elements.append(Paragraph("Career Summary", section_style))
        elements.append(Paragraph(self._safe_text(self._build_summary(profile_dict, skills)), body_style))

        # --- Academic Details ---
        elements.append(Paragraph("Academic Details", section_style))
        academic_data = []
        if profile_dict.get("institution"):
            academic_data.append(["Institution", self._safe_text(profile_dict["institution"])])
        if profile_dict.get("degree"):
            academic_data.append(["Degree", self._safe_text(profile_dict["degree"])])
        if profile_dict.get("branch"):
            academic_data.append(["Branch", self._safe_text(profile_dict["branch"])])
        if profile_dict.get("cgpa") is not None:
            academic_data.append(["CGPA", str(profile_dict["cgpa"])])
        if profile_dict.get("graduation_year") is not None:
            academic_data.append(["Graduation Year", str(profile_dict["graduation_year"])])

        if academic_data:
            table = Table(academic_data, colWidths=[1.8 * inch, 4.5 * inch])
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#374151")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(table)

        # --- Technical Skills ---
        elements.append(Paragraph("Technical Skills", section_style))
        if skills:
            for label, grouped_skills in self._group_skills(skills).items():
                elements.append(
                    Paragraph(
                        f"<b>{self._safe_text(label)}:</b> {self._safe_text(', '.join(grouped_skills))}",
                        body_style,
                    )
                )

        # --- Projects ---
        projects = profile.projects if profile.projects else []
        if projects:
            elements.append(Paragraph("Projects", section_style))
            for proj in projects:
                block = []
                proj_title = f"<b>{self._safe_text(proj.title)}</b>"
                if proj.technologies:
                    proj_title += f" <i>({self._safe_text(proj.technologies)})</i>"
                block.append(Paragraph(proj_title, body_style))
                if proj.description:
                    for point in self._split_points(proj.description):
                        block.append(Paragraph(f"- {self._safe_text(point)}", bullet_style))
                block.append(Spacer(1, 4))
                elements.append(KeepTogether(block))

        # --- Certifications ---
        certifications = profile.certifications if profile.certifications else []
        if certifications:
            elements.append(Paragraph("Certifications", section_style))
            for cert in certifications:
                cert_text = f"<b>{self._safe_text(cert.name)}</b>"
                if cert.issuer:
                    cert_text += f" - {self._safe_text(cert.issuer)}"
                if cert.issue_date:
                    cert_text += f" ({cert.issue_date.isoformat()})"
                elements.append(Paragraph(cert_text, body_style))
                elements.append(Spacer(1, 2))

        doc.build(elements)
        return buffer.getvalue()

    def _build_pdf_with_ai_content(self, profile_dict: dict, profile: StudentProfile, ai_content) -> bytes:
        """Build PDF using AI-generated sections.

        Renders AI-generated career objective, professional summary,
        prioritized skills, and enhanced project descriptions.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        elements: list = []

        # Custom styles
        title_style = ParagraphStyle(
            "ResumeTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=4,
            textColor=colors.HexColor("#1a237e"),
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1a237e"),
            spaceBefore=12,
            spaceAfter=4,
        )
        body_style = styles["Normal"]
        body_style.fontSize = 10
        body_style.leading = 14
        body_style.spaceAfter = 3
        muted_style = ParagraphStyle(
            "Muted",
            parent=body_style,
            textColor=colors.HexColor("#4b5563"),
        )
        bullet_style = ParagraphStyle(
            "ResumeBullet",
            parent=body_style,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )

        # --- Personal Info ---
        elements.append(Paragraph(self._safe_text(profile_dict.get("name", "")), title_style))

        contact_parts: list[str] = []
        if profile_dict.get("email"):
            contact_parts.append(profile_dict["email"])
        if profile_dict.get("phone"):
            contact_parts.append(profile_dict["phone"])
        if contact_parts:
            elements.append(Paragraph(self._safe_text(" | ".join(contact_parts)), muted_style))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
        elements.append(Spacer(1, 6))

        # --- Career Objective (AI-generated) ---
        elements.append(Paragraph("Career Objective", section_style))
        elements.append(Paragraph(self._safe_text(ai_content.career_objective), body_style))

        # --- Professional Summary (AI-generated) ---
        elements.append(Paragraph("Professional Summary", section_style))
        elements.append(Paragraph(self._safe_text(ai_content.professional_summary), body_style))

        # --- Academic Details ---
        elements.append(Paragraph("Academic Details", section_style))
        academic_data = []
        if profile_dict.get("institution"):
            academic_data.append(["Institution", self._safe_text(profile_dict["institution"])])
        if profile_dict.get("degree"):
            academic_data.append(["Degree", self._safe_text(profile_dict["degree"])])
        if profile_dict.get("branch"):
            academic_data.append(["Branch", self._safe_text(profile_dict["branch"])])
        if profile_dict.get("cgpa") is not None:
            academic_data.append(["CGPA", str(profile_dict["cgpa"])])
        if profile_dict.get("graduation_year") is not None:
            academic_data.append(["Graduation Year", str(profile_dict["graduation_year"])])

        if academic_data:
            table = Table(academic_data, colWidths=[1.8 * inch, 4.5 * inch])
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#374151")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(table)

        # --- Technical Skills (AI-prioritized) ---
        elements.append(Paragraph("Technical Skills", section_style))
        if ai_content.skill_categories:
            for label, grouped_skills in ai_content.skill_categories.items():
                elements.append(
                    Paragraph(
                        f"<b>{self._safe_text(label)}:</b> {self._safe_text(', '.join(grouped_skills))}",
                        body_style,
                    )
                )

        # --- Projects (AI-enhanced descriptions) ---
        if ai_content.project_descriptions:
            elements.append(Paragraph("Projects", section_style))
            for proj_desc in ai_content.project_descriptions:
                block = []
                proj_title = f"<b>{self._safe_text(proj_desc.get('title', ''))}</b>"
                if proj_desc.get("technologies"):
                    proj_title += f" <i>({self._safe_text(proj_desc['technologies'])})</i>"
                block.append(Paragraph(proj_title, body_style))
                if proj_desc.get("description"):
                    for point in self._split_points(proj_desc["description"]):
                        block.append(Paragraph(f"- {self._safe_text(point)}", bullet_style))
                if proj_desc.get("relevance_note"):
                    block.append(
                        Paragraph(
                            f"<i>{self._safe_text(proj_desc['relevance_note'])}</i>",
                            muted_style,
                        )
                    )
                block.append(Spacer(1, 4))
                elements.append(KeepTogether(block))

        # --- Certifications ---
        certifications = profile.certifications if profile.certifications else []
        if certifications:
            elements.append(Paragraph("Certifications", section_style))
            for cert in certifications:
                cert_text = f"<b>{self._safe_text(cert.name)}</b>"
                if cert.issuer:
                    cert_text += f" - {self._safe_text(cert.issuer)}"
                if cert.issue_date:
                    cert_text += f" ({cert.issue_date.isoformat()})"
                elements.append(Paragraph(cert_text, body_style))
                elements.append(Spacer(1, 2))

        doc.build(elements)
        return buffer.getvalue()

    @staticmethod
    def _parse_skills(value) -> list[str]:
        """Parse skills from a JSON string or list."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(skill).strip() for skill in value if str(skill).strip()]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(skill).strip() for skill in parsed if str(skill).strip()]
            except (json.JSONDecodeError, TypeError):
                pass
        return []

    @staticmethod
    def _safe_text(value) -> str:
        """Escape user-controlled text before inserting it into ReportLab markup."""
        return escape(str(value or ""), quote=True)

    @staticmethod
    def _split_points(text: str) -> list[str]:
        """Turn project text into compact resume bullets."""
        parts = re.split(r"(?:\r?\n|[.;]\s+)", text.strip())
        return [part.strip(" -") for part in parts if part.strip(" -")]

    @staticmethod
    def _build_summary(profile: dict, skills: list[str]) -> str:
        """Create a short profile summary for the generated resume."""
        degree = profile.get("degree") or "student"
        branch = profile.get("branch") or "engineering"
        top_skills = ", ".join(skills[:5]) if skills else "industry-relevant technologies"
        return (
            f"{degree} candidate specializing in {branch} with practical exposure "
            f"to {top_skills}. Interested in applying technical skills through "
            "projects, internships, and campus placement opportunities."
        )

    @staticmethod
    def _group_skills(skills: list[str]) -> dict[str, list[str]]:
        """Group common skills into resume-friendly categories."""
        category_keywords = {
            "Programming": {"python", "java", "javascript", "typescript", "c", "c++", "c#", "php"},
            "Web & Backend": {"react", "flask", "django", "node", "express", "html", "css", "api", "rest"},
            "Database": {"sql", "mysql", "postgresql", "mongodb", "sqlite", "database"},
            "AI & Data": {"machine learning", "ml", "ai", "nlp", "pandas", "numpy", "tensorflow", "scikit-learn"},
            "Tools": {"git", "github", "docker", "linux", "aws", "azure", "figma"},
        }
        grouped: dict[str, list[str]] = {}
        others: list[str] = []

        for skill in skills:
            normalized = skill.lower()
            matched_label = None
            for label, keywords in category_keywords.items():
                if normalized in keywords or any(keyword in normalized for keyword in keywords):
                    matched_label = label
                    break
            if matched_label:
                grouped.setdefault(matched_label, []).append(skill)
            else:
                others.append(skill)

        if others:
            grouped["Other"] = others
        return grouped
