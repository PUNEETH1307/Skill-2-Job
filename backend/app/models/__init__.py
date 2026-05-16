# Database models package
# Import all models so they are registered with SQLAlchemy when this package
# is imported (required for migrations and create_all to discover tables).

from app.models.models import (  # noqa: F401
    User,
    StudentProfile,
    Project,
    Certification,
    Company,
    JobRole,
    Shortlist,
    SkillTaxonomy,
    UncategorizedSkill,
    CourseRecommendation,
    PlacementRecord,
    ResumeUpload,
    PasswordResetToken,
)
