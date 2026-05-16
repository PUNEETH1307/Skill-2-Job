"""Resume Parser service for the Skill2Job Placement System.

Extracts structured profile data from uploaded resume files (PDF/DOCX)
using text extraction and NLP-based skill identification.
"""

import json
import logging
import os
import re

from app import db
from app.models import StudentProfile, User
from app.services.skill_analyzer import SkillAnalyzer

logger = logging.getLogger(__name__)

# Optional PDF extraction
try:
    import PyPDF2
    _HAS_PYPDF2 = True
except ImportError:
    _HAS_PYPDF2 = False

# Optional DOCX extraction
try:
    import docx
    _HAS_DOCX = True
except ImportError:
    _HAS_DOCX = False


class ResumeParser:
    """Extract structured profile data from resume files."""

    def __init__(self):
        self.skill_analyzer = SkillAnalyzer()

    def parse_resume(self, file_path: str) -> dict:
        """Parse a resume file and extract profile data.

        Args:
            file_path: Absolute path to the uploaded resume file.

        Returns:
            Dict with extracted profile fields:
            - name, institution, degree, branch, cgpa, graduation_year
            - skills (list), projects (list of dicts), certifications (list of dicts)
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif ext in ('.docx', '.doc'):
            text = self._extract_docx_text(file_path)
        else:
            text = ""

        if not text.strip():
            return self._empty_profile()

        return self._extract_profile_from_text(text)

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text content from a PDF file."""
        if not _HAS_PYPDF2:
            logger.warning("PyPDF2 not installed; cannot parse PDF resumes")
            return ""

        try:
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.exception("Failed to extract PDF text: %s", e)
            return ""

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text content from a DOCX file."""
        if not _HAS_DOCX:
            logger.warning("python-docx not installed; cannot parse DOCX resumes")
            return ""

        try:
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except Exception as e:
            logger.exception("Failed to extract DOCX text: %s", e)
            return ""

    def _extract_profile_from_text(self, text: str) -> dict:
        """Use NLP and regex patterns to extract structured data from resume text."""
        profile = self._empty_profile()

        # Extract skills using SkillAnalyzer
        try:
            extracted_skills = self.skill_analyzer.extract_skills(text)
            profile["skills"] = extracted_skills
        except Exception:
            logger.exception("Skill extraction failed during resume parsing")

        # Extract CGPA
        cgpa_match = re.search(
            r'(?:cgpa|gpa|c\.g\.p\.a|cumulative\s+gpa)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:/\s*10)?',
            text, re.IGNORECASE
        )
        if cgpa_match:
            try:
                cgpa = float(cgpa_match.group(1))
                if 0.0 <= cgpa <= 10.0:
                    profile["cgpa"] = cgpa
            except ValueError:
                pass

        # Extract graduation year
        year_match = re.search(
            r'(?:graduation|batch|passing|expected)\s*(?:year)?\s*[:\-]?\s*(20\d{2})',
            text, re.IGNORECASE
        )
        if year_match:
            profile["graduation_year"] = int(year_match.group(1))
        else:
            # Try to find any year between 2020-2030 near education context
            years = re.findall(r'\b(202[0-9]|2030)\b', text)
            if years:
                profile["graduation_year"] = int(max(years))

        # Extract degree
        degree_patterns = [
            r'\b(B\.?Tech|B\.?E|M\.?Tech|M\.?E|B\.?Sc|M\.?Sc|BCA|MCA|MBA|Ph\.?D|B\.?Com|M\.?Com)\b',
            r'\b(Bachelor\s+of\s+\w+|Master\s+of\s+\w+)\b',
        ]
        for pattern in degree_patterns:
            degree_match = re.search(pattern, text, re.IGNORECASE)
            if degree_match:
                profile["degree"] = degree_match.group(0).strip()
                break

        # Extract branch/specialization
        branch_patterns = [
            r'(?:Computer\s+Science(?:\s+(?:and|&)\s+Engineering)?)',
            r'(?:Information\s+Technology)',
            r'(?:Electronics(?:\s+(?:and|&)\s+Communication)?(?:\s+Engineering)?)',
            r'(?:Mechanical\s+Engineering)',
            r'(?:Electrical\s+Engineering)',
            r'(?:Civil\s+Engineering)',
            r'(?:Data\s+Science)',
            r'(?:Artificial\s+Intelligence)',
        ]
        for pattern in branch_patterns:
            branch_match = re.search(pattern, text, re.IGNORECASE)
            if branch_match:
                profile["branch"] = branch_match.group(0).strip()
                break

        # Extract institution (look for common patterns)
        institution_patterns = [
            r'(?:University|Institute|College|School)\s+of\s+[\w\s]+',
            r'(?:IIT|NIT|IIIT|VIT|SRM|BITS|MIT)\s*[\w\s]*',
        ]
        for pattern in institution_patterns:
            inst_match = re.search(pattern, text, re.IGNORECASE)
            if inst_match:
                profile["institution"] = inst_match.group(0).strip()[:255]
                break

        # Extract projects (look for project section)
        projects = self._extract_projects(text)
        if projects:
            profile["projects"] = projects

        # Extract certifications
        certifications = self._extract_certifications(text)
        if certifications:
            profile["certifications"] = certifications

        return profile

    def _extract_projects(self, text: str) -> list[dict]:
        """Extract project entries from resume text."""
        projects = []

        # Look for project section
        project_section = re.search(
            r'(?:projects?|academic\s+projects?|personal\s+projects?)\s*[:\-]?\s*\n(.*?)(?:\n(?:certification|education|experience|skill|achievement|award|hobby|reference)|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )

        if project_section:
            section_text = project_section.group(1)
            # Split by bullet points or numbered items
            items = re.split(r'\n\s*(?:[\u2022\u2023\u25E6\u2043\u2219•●○▪]|\d+[\.\)]|\-)\s*', section_text)

            for item in items:
                item = item.strip()
                if len(item) > 10:  # Minimum meaningful length
                    # First line is likely the title
                    lines = item.split('\n')
                    title = lines[0].strip()[:255]
                    description = ' '.join(lines[1:]).strip()[:500] if len(lines) > 1 else ''

                    # Try to extract technologies
                    tech_match = re.search(
                        r'(?:technologies?|tech\s+stack|built\s+with|using)\s*[:\-]?\s*(.+)',
                        item, re.IGNORECASE
                    )
                    technologies = tech_match.group(1).strip()[:500] if tech_match else ''

                    projects.append({
                        "title": title,
                        "description": description,
                        "technologies": technologies,
                    })

                    if len(projects) >= 5:  # Cap at 5 projects
                        break

        return projects

    def _extract_certifications(self, text: str) -> list[dict]:
        """Extract certification entries from resume text."""
        certifications = []

        # Look for certification section
        cert_section = re.search(
            r'(?:certifications?|certificates?|courses?\s+completed)\s*[:\-]?\s*\n(.*?)(?:\n(?:project|education|experience|skill|achievement|award|hobby|reference)|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )

        if cert_section:
            section_text = cert_section.group(1)
            items = re.split(r'\n\s*(?:[\u2022\u2023\u25E6\u2043\u2219•●○▪]|\d+[\.\)]|\-)\s*', section_text)

            for item in items:
                item = item.strip()
                if len(item) > 5:
                    # Try to extract issuer
                    issuer_match = re.search(
                        r'(?:by|from|issued\s+by|provider)\s*[:\-]?\s*(.+)',
                        item, re.IGNORECASE
                    )
                    issuer = issuer_match.group(1).strip()[:255] if issuer_match else ''
                    name = re.sub(r'(?:by|from|issued\s+by|provider)\s*[:\-]?\s*.+', '', item, flags=re.IGNORECASE).strip()[:255]

                    if name:
                        certifications.append({
                            "name": name,
                            "issuer": issuer,
                            "issue_date": "",
                        })

                    if len(certifications) >= 5:
                        break

        return certifications

    def _empty_profile(self) -> dict:
        """Return an empty profile structure."""
        return {
            "institution": "",
            "degree": "",
            "branch": "",
            "cgpa": None,
            "graduation_year": None,
            "skills": [],
            "projects": [],
            "certifications": [],
        }
