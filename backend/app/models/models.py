"""SQLAlchemy models for the Skill2Job Placement System.

Defines all database entities, relationships, indexes, and serialization
helpers used throughout the application.
"""

from datetime import datetime, date, timezone

from app import db


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(db.Model):
    """Application user with role-based access (student, placement_officer, admin)."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="student")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    profile = db.relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_user_email", "email", unique=True),
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# StudentProfile
# ---------------------------------------------------------------------------

class StudentProfile(db.Model):
    """Academic and skill profile for a student user."""

    __tablename__ = "student_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    institution = db.Column(db.String(255), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    skills_json = db.Column(db.Text, nullable=True)
    skill_vector_json = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship("User", back_populates="profile")
    projects = db.relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    certifications = db.relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    shortlists = db.relationship("Shortlist", back_populates="profile", cascade="all, delete-orphan")
    placement_records = db.relationship("PlacementRecord", back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_profile_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<StudentProfile id={self.id} user_id={self.user_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "institution": self.institution,
            "degree": self.degree,
            "branch": self.branch,
            "cgpa": self.cgpa,
            "graduation_year": self.graduation_year,
            "skills_json": self.skills_json,
            "skill_vector_json": self.skill_vector_json,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "projects": [p.to_dict() for p in self.projects],
            "certifications": [c.to_dict() for c in self.certifications],
        }


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class Project(db.Model):
    """A project entry linked to a student profile."""

    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.String(500), nullable=True)

    # Relationships
    profile = db.relationship("StudentProfile", back_populates="projects")

    def __repr__(self):
        return f"<Project id={self.id} title={self.title!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
            "technologies": self.technologies,
        }


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

class Certification(db.Model):
    """A certification entry linked to a student profile."""

    __tablename__ = "certification"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    issuer = db.Column(db.String(255), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)

    # Relationships
    profile = db.relationship("StudentProfile", back_populates="certifications")

    def __repr__(self):
        return f"<Certification id={self.id} name={self.name!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "name": self.name,
            "issuer": self.issuer,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
        }


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

class Company(db.Model):
    """A company that offers job roles for placement."""

    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(150), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job_roles = db.relationship("JobRole", back_populates="company", cascade="all, delete-orphan")
    placement_records = db.relationship("PlacementRecord", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company id={self.id} name={self.name!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "location": self.location,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# JobRole
# ---------------------------------------------------------------------------

class JobRole(db.Model):
    """A job role offered by a company with skill requirements and eligibility criteria."""

    __tablename__ = "job_role"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    required_skills_json = db.Column(db.Text, nullable=True)
    job_vector_json = db.Column(db.Text, nullable=True)
    cgpa_threshold = db.Column(db.Float, nullable=True, default=0.0)
    academic_status = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    company = db.relationship("Company", back_populates="job_roles")
    shortlists = db.relationship("Shortlist", back_populates="job_role", cascade="all, delete-orphan")
    placement_records = db.relationship("PlacementRecord", back_populates="job_role", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_job_company_id", "company_id"),
        db.Index("idx_job_active", "is_active"),
    )

    def __repr__(self):
        return f"<JobRole id={self.id} title={self.title!r} active={self.is_active}>"

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "title": self.title,
            "description": self.description,
            "required_skills_json": self.required_skills_json,
            "job_vector_json": self.job_vector_json,
            "cgpa_threshold": self.cgpa_threshold,
            "academic_status": self.academic_status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Shortlist
# ---------------------------------------------------------------------------

class Shortlist(db.Model):
    """A shortlisting record linking a student profile to a job role."""

    __tablename__ = "shortlist"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_role.id"), nullable=False)
    compatibility_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
    shortlisted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    profile = db.relationship("StudentProfile", back_populates="shortlists")
    job_role = db.relationship("JobRole", back_populates="shortlists")

    __table_args__ = (
        db.Index("idx_shortlist_job", "job_role_id"),
    )

    def __repr__(self):
        return f"<Shortlist id={self.id} profile_id={self.profile_id} job_role_id={self.job_role_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "job_role_id": self.job_role_id,
            "compatibility_score": self.compatibility_score,
            "status": self.status,
            "shortlisted_at": self.shortlisted_at.isoformat() if self.shortlisted_at else None,
        }


# ---------------------------------------------------------------------------
# SkillTaxonomy
# ---------------------------------------------------------------------------

class SkillTaxonomy(db.Model):
    """Canonical skill entry with category and synonym mappings."""

    __tablename__ = "skill_taxonomy"

    id = db.Column(db.Integer, primary_key=True)
    canonical_name = db.Column(db.String(150), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)
    synonyms_json = db.Column(db.Text, nullable=True)
    is_deprecated = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.Index("idx_skill_canonical", "canonical_name", unique=True),
    )

    def __repr__(self):
        return f"<SkillTaxonomy id={self.id} canonical_name={self.canonical_name!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "canonical_name": self.canonical_name,
            "category": self.category,
            "synonyms_json": self.synonyms_json,
            "is_deprecated": self.is_deprecated,
        }


# ---------------------------------------------------------------------------
# UncategorizedSkill
# ---------------------------------------------------------------------------

class UncategorizedSkill(db.Model):
    """A skill term flagged by the Skill Analyzer for admin review."""

    __tablename__ = "uncategorized_skill"

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(255), nullable=False)
    occurrence_count = db.Column(db.Integer, nullable=False, default=1)
    reviewed = db.Column(db.Boolean, nullable=False, default=False)
    flagged_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<UncategorizedSkill id={self.id} term={self.term!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "term": self.term,
            "occurrence_count": self.occurrence_count,
            "reviewed": self.reviewed,
            "flagged_at": self.flagged_at.isoformat() if self.flagged_at else None,
        }


# ---------------------------------------------------------------------------
# CourseRecommendation
# ---------------------------------------------------------------------------

class CourseRecommendation(db.Model):
    """A course recommendation mapped to a specific skill."""

    __tablename__ = "course_recommendation"

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(150), nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(150), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<CourseRecommendation id={self.id} skill={self.skill_name!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "skill_name": self.skill_name,
            "course_name": self.course_name,
            "provider": self.provider,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# PlacementRecord
# ---------------------------------------------------------------------------

class PlacementRecord(db.Model):
    """Records a student's placement at a company for a specific job role."""

    __tablename__ = "placement_record"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_role.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    placement_date = db.Column(db.Date, nullable=True)
    department = db.Column(db.String(150), nullable=True)

    # Relationships
    profile = db.relationship("StudentProfile", back_populates="placement_records")
    job_role = db.relationship("JobRole", back_populates="placement_records")
    company = db.relationship("Company", back_populates="placement_records")

    __table_args__ = (
        db.Index("idx_placement_date", "placement_date"),
        db.Index("idx_placement_dept", "department"),
    )

    def __repr__(self):
        return f"<PlacementRecord id={self.id} profile_id={self.profile_id} company_id={self.company_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "job_role_id": self.job_role_id,
            "company_id": self.company_id,
            "placement_date": self.placement_date.isoformat() if self.placement_date else None,
            "department": self.department,
        }
