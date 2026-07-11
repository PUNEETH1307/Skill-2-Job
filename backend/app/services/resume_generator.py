"""Resume generator — 6 professional templates.

Templates (3 without photo, 3 with photo placeholder):
  classic      - Traditional blue, clean layout          (no photo)
  modern       - Teal accent, bold dividers              (no photo)
  minimal      - Black & white, ultra clean              (no photo)
  sidebar      - Dark left sidebar + right content       (photo circle)
  executive    - Dark header banner, white name          (photo circle)
  photo_card   - Header block with photo area            (photo circle)
"""

import json
import logging
import os
import re
from datetime import date
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

from app import db
from app.models import StudentProfile, User

logger = logging.getLogger(__name__)
W, H = A4  # 595.27 x 841.89 pt

PALETTES = {
    "classic":    {"p": "#1a237e", "a": "#3949ab", "m": "#4b5563"},
    "modern":     {"p": "#0d9488", "a": "#0f766e", "m": "#374151"},
    "minimal":    {"p": "#111827", "a": "#374151", "m": "#6b7280"},
    "sidebar":    {"p": "#1e293b", "a": "#3b82f6", "m": "#64748b"},
    "executive":  {"p": "#7c3aed", "a": "#a78bfa", "m": "#6b7280"},
    "photo_card": {"p": "#b91c1c", "a": "#ef4444", "m": "#6b7280"},
}
VALID_TEMPLATES = list(PALETTES.keys())
HAS_PHOTO = {"sidebar", "executive", "photo_card"}


def _clean_text(value) -> str:
  if value is None:
    return ''
  return str(value).strip()


def _split_lines(value) -> list[str]:
  if value is None:
    return []
  if isinstance(value, list):
    return [str(item).strip() for item in value if str(item).strip()]
  if not isinstance(value, str):
    value = str(value)
  normalized = value.replace('\r', '\n')
  lines = []
  for line in normalized.split('\n'):
    stripped = line.strip().lstrip('•-').strip()
    if stripped:
      lines.append(stripped)
  if not lines and ',' in value:
    return [part.strip() for part in value.split(',') if part.strip()]
  return lines


def _split_commas(value) -> list[str]:
  if value is None:
    return []
  if isinstance(value, list):
    return [str(item).strip() for item in value if str(item).strip()]
  return [part.strip() for part in str(value).split(',') if part.strip()]


def _parse_projects(value) -> list[dict]:
  if not value:
    return []
  if isinstance(value, list):
    result = []
    for item in value:
      if isinstance(item, dict):
        result.append({
          'title': _clean_text(item.get('title')),
          'description': _clean_text(item.get('description')),
          'technologies': _clean_text(item.get('technologies')),
        })
      else:
        text = _clean_text(item)
        if text:
          result.append({'title': text, 'description': '', 'technologies': ''})
    return result

  blocks = [block.strip() for block in str(value).replace('\r', '\n').split('\n\n') if block.strip()]
  parsed = []
  for block in blocks:
    lines = [line.strip() for line in block.split('\n') if line.strip()]
    if not lines:
      continue
    title = lines[0].lstrip('•-').strip()
    description_lines = [line.lstrip('•-').strip() for line in lines[1:]]
    parsed.append({
      'title': title,
      'description': ' '.join(description_lines),
      'technologies': '',
    })
  return parsed


def _parse_certifications(value) -> list[dict]:
  items = _split_lines(value)
  return [{'name': item, 'issuer': '', 'issue_date': ''} for item in items]


def _coerce_links(value) -> dict:
  if not value:
    return {}
  if isinstance(value, dict):
    return {
      'linkedin': _clean_text(value.get('linkedin')),
      'github': _clean_text(value.get('github')),
      'portfolio': _clean_text(value.get('portfolio')),
    }
  return {}


def _safe_escape_lines(lines: list[str]) -> list[str]:
  return [escape(line) for line in lines if line]


def _truncate(text: str, limit: int = 220) -> str:
  text = _clean_text(text)
  if len(text) <= limit:
    return text
  return text[:limit - 3].rstrip() + '...'
 

class ResumeGenerator:
  """Builds PDF resumes from student profiles.

  Supports 6 templates (see module docstring). Integrates with
  AIResumeService when a dream_job is set on the profile.
  """

  def __init__(self):
    self.styles = getSampleStyleSheet()

  # -------------------- Validation & helpers --------------------
  def validate_profile(self, profile: dict) -> tuple[bool, list]:
    """Validate a profile-like dict for required resume fields.

    Required: name, institution, degree, branch, skills
    """
    missing: list[str] = []
    # name may be in profile or provided via User
    name = profile.get('name')
    if not name or (isinstance(name, str) and not name.strip()):
      missing.append('name')

    for field in ('institution', 'degree', 'branch'):
      val = profile.get(field)
      if val is None or (isinstance(val, str) and not val.strip()):
        missing.append(field)

    # Skills may be stored as skills_json (string) or 'skills' list
    skills_present = False
    if 'skills' in profile and profile.get('skills'):
      skills_value = profile.get('skills')
      if isinstance(skills_value, list):
        skills_present = len(skills_value) > 0
      elif isinstance(skills_value, str):
        skills_present = bool(skills_value.strip())
      else:
        skills_present = bool(skills_value)
    else:
      sj = profile.get('skills_json')
      if sj:
        try:
          parsed = json.loads(sj) if isinstance(sj, str) else sj
          skills_present = isinstance(parsed, list) and len(parsed) > 0
        except Exception:
          skills_present = False

    if not skills_present:
      missing.append('skills')

    return (len(missing) == 0, missing)

  def get_download_filename(self, name: str) -> str:
    """Return a safe filename like Resume_First_Last_YYYY-MM-DD.pdf"""
    safe = re.sub(r"[^0-9A-Za-z _-]", "", name or "Student")
    safe = "_".join(safe.split())
    today = date.today().isoformat()
    return f"Resume_{safe}_{today}.pdf"

  def _build_resume_payload(self, profile_dict: dict, profile_obj, override: dict | None = None, ai_content=None) -> dict:
    override = override or {}
    user_name = profile_dict.get('name') or profile_dict.get('full_name') or ''

    summary = _clean_text(override.get('summary') or override.get('profile_summary'))
    if not summary and ai_content is not None:
      summary = _clean_text(getattr(ai_content, 'professional_summary', '') or getattr(ai_content, 'career_objective', ''))
    if not summary:
      dream_job = _clean_text(profile_dict.get('dream_job') or getattr(profile_obj, 'dream_job', ''))
      summary = (
        f"Final-year student seeking opportunities in {dream_job}."
        if dream_job else
        "Final-year Computer Science student with a strong interest in software development."
      )

    if override.get('education_entries'):
      education = override.get('education_entries')
    elif override.get('education'):
      education = []
      for block in _split_lines(override.get('education')):
        education.append({
          'title': block,
          'description': '',
          'meta': '',
        })
    else:
      education = []
      main_school = []
      if _clean_text(profile_dict.get('degree')):
        main_school.append(_clean_text(profile_dict.get('degree')))
      if _clean_text(profile_dict.get('institution')):
        main_school.append(_clean_text(profile_dict.get('institution')))
      if main_school:
        education.append({
          'title': ', '.join(main_school),
          'description': _clean_text(profile_dict.get('branch')),
          'meta': ' | '.join([part for part in [f"CGPA {profile_dict.get('cgpa')}" if profile_dict.get('cgpa') else '', str(profile_dict.get('graduation_year')) if profile_dict.get('graduation_year') else ''] if part]),
        })

      # Add any additional profile projects/certs as education notes only if nothing else is present

    skills_source = override.get('skills') or override.get('technical_skills') or profile_dict.get('skills')
    skills = _split_commas(skills_source)
    if not skills and profile_dict.get('skills_json'):
      try:
        parsed = json.loads(profile_dict['skills_json']) if isinstance(profile_dict['skills_json'], str) else profile_dict['skills_json']
        if isinstance(parsed, list):
          skills = _split_commas(parsed)
      except Exception:
        skills = []

    projects = _parse_projects(override.get('projects') or override.get('project_blocks') or getattr(profile_obj, 'projects', []))
    if not projects and getattr(profile_obj, 'projects', None):
      projects = [
        {
          'title': _clean_text(project.title),
          'description': _clean_text(project.description),
          'technologies': _clean_text(project.technologies),
        }
        for project in profile_obj.projects
      ]

    certifications = _parse_certifications(override.get('certifications') or override.get('certificates') or getattr(profile_obj, 'certifications', []))
    if not certifications and getattr(profile_obj, 'certifications', None):
      certifications = [
        {
          'name': _clean_text(cert.name),
          'issuer': _clean_text(cert.issuer),
          'issue_date': cert.issue_date.isoformat() if getattr(cert, 'issue_date', None) else '',
        }
        for cert in profile_obj.certifications
      ]

    courses = _split_lines(override.get('courses') or override.get('course_list') or profile_dict.get('courses') or profile_dict.get('course_list'))
    languages = _split_lines(override.get('languages') or profile_dict.get('languages'))
    links = _coerce_links(override.get('links') or profile_dict.get('links'))
    for key in ('linkedin', 'github', 'portfolio'):
      if not links.get(key):
        direct_value = _clean_text(override.get(key))
        if not direct_value:
          direct_value = _clean_text(profile_dict.get(key))
        if direct_value:
          links[key] = direct_value

    headline = _clean_text(override.get('headline'))
    if not headline:
      dream_job = _clean_text(profile_dict.get('dream_job') or getattr(profile_obj, 'dream_job', ''))
      headline = dream_job or 'Software Developer'

    return {
      'name': user_name,
      'email': _clean_text(profile_dict.get('email')),
      'phone': _clean_text(profile_dict.get('phone')),
      'headline': headline,
      'summary': summary,
      'education': education,
      'skills': skills,
      'projects': projects,
      'certifications': certifications,
      'courses': courses,
      'languages': languages,
      'links': links,
      'profile': profile_dict,
    }

  def _build_story(self, payload: dict, template_id: str) -> list:
    story = []
    palette = PALETTES.get(template_id, PALETTES['classic'])
    primary = colors.HexColor(palette['p'])
    accent = colors.HexColor(palette['a'])
    muted = colors.HexColor(palette['m'])

    styles = {
      'name': ParagraphStyle('Name', parent=self.styles['Heading1'], fontSize=20, textColor=primary, leading=22, spaceAfter=2),
      'headline': ParagraphStyle('Headline', parent=self.styles['Normal'], fontSize=10, textColor=accent, leading=12, spaceAfter=4),
      'section': ParagraphStyle('Section', parent=self.styles['Heading3'], fontSize=11, textColor=primary, spaceBefore=8, spaceAfter=4),
      'body': ParagraphStyle('Body', parent=self.styles['BodyText'], fontSize=9.2, leading=12, textColor=colors.HexColor('#1f2937')),
      'muted': ParagraphStyle('Muted', parent=self.styles['BodyText'], fontSize=8.5, leading=11, textColor=muted),
      'small': ParagraphStyle('Small', parent=self.styles['BodyText'], fontSize=8.2, leading=10, textColor=muted),
    }

    story.append(Paragraph(escape(payload['name'] or 'Student Name'), styles['name']))
    story.append(Paragraph(escape(payload['headline']), styles['headline']))

    contact_bits = [bit for bit in [payload.get('email'), payload.get('phone'), payload['links'].get('linkedin'), payload['links'].get('github'), payload['links'].get('portfolio')] if bit]
    if contact_bits:
      story.append(Paragraph(' | '.join(escape(bit) for bit in contact_bits), styles['small']))
    story.append(Spacer(1, 8))

    story.append(Paragraph('Profile', styles['section']))
    story.append(Paragraph(escape(payload['summary']), styles['body']))

    if payload['education']:
      story.append(Paragraph('Education', styles['section']))
      for item in payload['education']:
        title = item.get('title', '')
        desc = item.get('description', '')
        meta = item.get('meta', '')
        parts = [f"<b>{escape(title)}</b>"]
        if desc:
          parts.append(escape(desc))
        if meta:
          parts.append(f"<i>{escape(meta)}</i>")
        story.append(Paragraph('<br/>'.join(parts), styles['body']))
        story.append(Spacer(1, 2))

    if payload['skills']:
      story.append(Paragraph('Technical Skills', styles['section']))
      story.append(Paragraph(escape(', '.join(payload['skills'])), styles['body']))

    if payload['projects']:
      story.append(Paragraph('Projects', styles['section']))
      for project in payload['projects']:
        title = project.get('title', '')
        desc = project.get('description', '')
        techs = project.get('technologies', '')
        project_lines = [f"<b>{escape(title)}</b>"]
        if desc:
          project_lines.append(escape(desc))
        if techs:
          project_lines.append(f"<font color='{palette['m']}'><i>{escape(techs)}</i></font>")
        story.append(Paragraph('<br/>'.join(project_lines), styles['body']))
        story.append(Spacer(1, 2))

    if payload['certifications']:
      story.append(Paragraph('Certificates', styles['section']))
      for cert in payload['certifications']:
        cert_bits = [cert.get('name', '')]
        issuer = cert.get('issuer', '')
        if issuer:
          cert_bits.append(issuer)
        date_text = cert.get('issue_date', '')
        if date_text:
          cert_bits.append(date_text)
        story.append(Paragraph(escape(' | '.join([bit for bit in cert_bits if bit])), styles['body']))

    if payload['courses']:
      story.append(Paragraph('Courses', styles['section']))
      story.append(Paragraph(escape(' • '.join(payload['courses'])), styles['body']))

    if payload['languages']:
      story.append(Paragraph('Languages', styles['section']))
      story.append(Paragraph(escape(', '.join(payload['languages'])), styles['body']))

    return story

  def _build_pdf(self, payload: dict, template_id: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=32)
    story = self._build_story(payload, template_id)
    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf

  # -------------------- PDF builders --------------------
  def _build_pdf_with_ai_content(self, profile_dict: dict, profile_obj, ai_content) -> bytes:
    """Build a PDF using AI-driven content sections."""
    payload = self._build_resume_payload(
      profile_dict,
      profile_obj,
      override={
        'summary': getattr(ai_content, 'professional_summary', '') or getattr(ai_content, 'career_objective', ''),
        'skills': getattr(ai_content, 'prioritized_skills', []),
        'projects': getattr(ai_content, 'project_descriptions', []),
      },
      ai_content=ai_content,
    )
    return self._build_pdf(payload, 'modern')

  def _build_pdf_template(self, profile_dict: dict, profile_obj, template_id: str) -> bytes:
    """Build a template-based PDF (fallback or when no AI content)."""
    payload = self._build_resume_payload(profile_dict, profile_obj, override=profile_dict)
    return self._build_pdf(payload, template_id)

  # -------------------- Public API --------------------
  def generate_resume(self, user_id: int, template_id: str = 'classic', profile_override: dict | None = None) -> bytes:
    """Generate a PDF resume for a user id.

    - Loads profile and user
    - Optionally applies profile_override for missing fields
    - Validates required fields and raises ValueError with message
      starting with "Profile is missing required fields:" when missing
    - If `dream_job` is set and non-empty, attempts to call AIResumeService
      to get AI content; falls back to template generation if AI fails.
    """
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
      raise ValueError('Student profile not found')

    user = db.session.get(User, user_id)

    profile_dict = profile.to_dict()
    # attach user contact details
    if user:
      profile_dict['name'] = user.name
      profile_dict['email'] = user.email
      profile_dict['phone'] = user.phone

    # Apply overrides (profile_override expected as simple dict)
    if profile_override:
      for k, v in profile_override.items():
        profile_dict[k] = v

    valid, missing = self.validate_profile(profile_dict)
    if not valid:
      raise ValueError('Profile is missing required fields: ' + ','.join(missing))

    # Use AIResumeService when dream_job is set and non-blank
    dj = getattr(profile, 'dream_job', None)
    if dj and isinstance(dj, str) and dj.strip():
      try:
        from app.services.ai_resume_service import AIResumeService

        ai = AIResumeService()
        ai_content = ai.generate_ai_content(profile, user)
        return self._build_pdf_with_ai_content(profile_dict, profile, ai_content)
      except Exception:
        logger.exception('AIResumeService failed — falling back to template')
        # fallback to template below

    # Template-based generation
    if template_id not in VALID_TEMPLATES:
      template_id = 'classic'

    return self._build_pdf_template(profile_dict, profile, template_id)

