"""Resume generator service for the Skill2Job Placement System.

Produces professional PDF resumes from student profile data using
ReportLab. Validates that required profile fields are present before
generation and provides a standardised download filename.
"""

import json
from datetime import date
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
)

from app import db
from app.models import StudentProfile, User


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

        # 4. Build PDF
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
        safe_name = student_name.replace(" ", "_")
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

        # --- Personal Info ---
        elements.append(Paragraph(profile_dict.get("name", ""), title_style))

        contact_parts: list[str] = []
        if profile_dict.get("email"):
            contact_parts.append(profile_dict["email"])
        if profile_dict.get("phone"):
            contact_parts.append(profile_dict["phone"])
        if contact_parts:
            elements.append(Paragraph(" | ".join(contact_parts), body_style))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
        elements.append(Spacer(1, 6))

        # --- Academic Details ---
        elements.append(Paragraph("Academic Details", section_style))
        academic_data = []
        if profile_dict.get("institution"):
            academic_data.append(["Institution", profile_dict["institution"]])
        if profile_dict.get("degree"):
            academic_data.append(["Degree", profile_dict["degree"]])
        if profile_dict.get("branch"):
            academic_data.append(["Branch", profile_dict["branch"]])
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
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(table)

        # --- Technical Skills ---
        elements.append(Paragraph("Technical Skills", section_style))
        skills = self._parse_skills(profile_dict.get("skills_json"))
        if skills:
            skills_text = ", ".join(skills)
            elements.append(Paragraph(skills_text, body_style))

        # --- Projects ---
        projects = profile.projects if profile.projects else []
        if projects:
            elements.append(Paragraph("Projects", section_style))
            for proj in projects:
                proj_title = f"<b>{proj.title}</b>"
                if proj.technologies:
                    proj_title += f" <i>({proj.technologies})</i>"
                elements.append(Paragraph(proj_title, body_style))
                if proj.description:
                    elements.append(Paragraph(proj.description, body_style))
                elements.append(Spacer(1, 4))

        # --- Certifications ---
        certifications = profile.certifications if profile.certifications else []
        if certifications:
            elements.append(Paragraph("Certifications", section_style))
            for cert in certifications:
                cert_text = f"<b>{cert.name}</b>"
                if cert.issuer:
                    cert_text += f" — {cert.issuer}"
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
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return []
