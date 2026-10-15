"""Job matching API routes for the Skill2Job Placement System.

Provides endpoints for job recommendations, skill gap analysis,
and course recommendations for gap skills.

Requirements: 6.1, 6.3, 6.4, 6.5, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3
"""

import json
import logging

from flask import Blueprint, jsonify, g, request

from app import db
from app.models import StudentProfile, JobRole, CourseRecommendation, Company, DreamJob, SkillTaxonomy
from app.services.job_matching import JobMatchingEngine
from app.services.skill_analyzer import SkillAnalyzer
from app.services.hiring_updates import get_hiring_updates
from app.utils.auth_decorator import jwt_required, role_required

job_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

logger = logging.getLogger(__name__)

# In-memory cache for recommendations (keyed by user_id).
# Used as a fallback when the JobMatchingEngine fails.
_recommendations_cache: dict[int, list[dict]] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _current_skill_comparison(profile, job_role):
    """Compare current profile skills with current job requirements."""
    profile_skills = []
    if profile.skills_json:
        try:
            parsed = json.loads(profile.skills_json)
            if isinstance(parsed, list):
                profile_skills = [
                    str(skill).strip() for skill in parsed if str(skill).strip()
                ]
        except (json.JSONDecodeError, TypeError):
            pass

    required_skills = []
    if job_role.required_skills_json:
        try:
            parsed = json.loads(job_role.required_skills_json)
            if isinstance(parsed, list):
                required_skills = [
                    str(skill).strip() for skill in parsed if str(skill).strip()
                ]
        except (json.JSONDecodeError, TypeError):
            pass

    analyzer = SkillAnalyzer()
    student_skills = {
        analyzer.normalize_skill(skill).lower() for skill in profile_skills
    }
    matched = [
        skill for skill in required_skills
        if analyzer.normalize_skill(skill).lower() in student_skills
    ]
    missing = [
        skill for skill in required_skills
        if analyzer.normalize_skill(skill).lower() not in student_skills
    ]
    gaps = [{"skill": skill, "deficit_score": 1.0} for skill in missing]
    return required_skills, matched, missing, gaps


@job_bp.route("/options", methods=["GET"])
@jwt_required
@role_required("student")
def get_job_options():
    """Return active companies and their active roles for Dream Job selection."""
    companies = Company.query.order_by(Company.name.asc()).all()
    roles = JobRole.query.filter_by(is_active=True).order_by(JobRole.title.asc()).all()
    return jsonify({
        "companies": [company.to_dict() for company in companies],
        "job_roles": [
            {
                "id": role.id,
                "company_id": role.company_id,
                "company_name": role.company.name if role.company else None,
                "title": role.title,
                "required_skills": json.loads(role.required_skills_json) if role.required_skills_json else [],
            }
            for role in roles
        ],
    }), 200


@job_bp.route("/dream-jobs", methods=["GET", "POST"])
@jwt_required
@role_required("student")
def dream_jobs():
    """List or save up to three company-specific Dream Jobs with AI gap analysis."""
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        job_role_id = data.get("job_role_id")
        if not job_role_id:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "job_role_id is required", "fields": {}}}), 400
        if DreamJob.query.filter_by(profile_id=profile.id).count() >= 3:
            return jsonify({"error": {"code": "LIMIT_REACHED", "message": "You can save a maximum of 3 Dream Jobs.", "fields": {}}}), 400
        job = db.session.get(JobRole, job_role_id)
        if job is None or not job.is_active:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Active job role not found", "fields": {}}}), 404
        if DreamJob.query.filter_by(profile_id=profile.id, job_role_id=job.id).first():
            return jsonify({"error": {"code": "CONFLICT", "message": "This Dream Job is already saved.", "fields": {}}}), 409
        record = DreamJob(profile_id=profile.id, job_role_id=job.id)
        db.session.add(record)
        db.session.commit()
        return jsonify(_dream_job_result(record)), 201

    return jsonify([_dream_job_result(record) for record in DreamJob.query.filter_by(profile_id=profile.id).all()]), 200


@job_bp.route("/dream-jobs/<int:id>", methods=["DELETE"])
@jwt_required
@role_required("student")
def delete_dream_job(id):
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    record = DreamJob.query.filter_by(id=id, profile_id=profile.id if profile else None).first()
    if record is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Dream Job not found", "fields": {}}}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Dream Job removed"}), 200


@job_bp.route("/dream-jobs/updates", methods=["GET"])
@jwt_required
@role_required("student")
def dream_job_updates():
    """Return current hiring links and preparation resources for saved roles."""
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404

    role_id = request.args.get("role_id", type=int)
    query = DreamJob.query.filter_by(profile_id=profile.id)
    if role_id:
        query = query.filter_by(job_role_id=role_id)

    updates = []
    for record in query.all():
        role = record.job_role
        company_name = role.company.name if role.company else ""
        hiring = get_hiring_updates(company_name, role.title)
        updates.append({
            "dream_job_id": record.id,
            "job_role_id": role.id,
            "company_name": company_name,
            "role_title": role.title,
            "live_jobs": hiring["live_jobs"],
            "preparation_resources": hiring["preparation_resources"],
            "last_checked_at": hiring["last_checked_at"],
        })
    return jsonify(updates), 200


def _dream_job_result(record):
    """Use the shared skill analyzer to compare a target role with profile skills."""
    result = record.to_dict()
    profile_skills = []
    if record.profile.skills_json:
        try:
            profile_skills = json.loads(record.profile.skills_json)
        except (TypeError, ValueError):
            profile_skills = []
    required = result["required_skills"]
    known = {str(skill).strip().lower() for skill in profile_skills}
    gaps = [skill for skill in required if str(skill).strip().lower() not in known]
    try:
        analyzer = SkillAnalyzer()
        matcher = JobMatchingEngine()
        taxonomy = SkillTaxonomy.query.filter_by(is_deprecated=False).order_by(SkillTaxonomy.id).all()
        student_vector = analyzer.generate_skill_vector(profile_skills)
        job_vector = analyzer.generate_job_requirement_vector(required)
        result["ai_match_score"] = round(matcher.compute_compatibility(student_vector, job_vector) * 100, 1)
        skill_index = {skill.canonical_name.lower(): index for index, skill in enumerate(taxonomy)}
        vector_gaps = matcher.compute_skill_gap(student_vector, job_vector, skill_index)
        if vector_gaps:
            gaps = [gap["skill"] for gap in vector_gaps]
    except Exception:
        result["ai_match_score"] = None
    result["skill_gaps"] = [{"skill": skill, "reason": "Required by the selected role"} for skill in gaps]
    result["recommended_skills"] = gaps[:]
    result["analysis_status"] = "complete" if record.profile.skill_vector_json else "pending_profile_analysis"
    return result


@job_bp.route("/recommendations", methods=["GET"])
@jwt_required
@role_required("student")
def get_recommendations():
    """Return ranked job recommendations for the authenticated student.

    Calls :meth:`JobMatchingEngine.get_recommendations` with the current
    user's ID and returns the sorted list as JSON.

    Returns:
        200: JSON list of recommendations sorted by compatibility score descending.
        Each item contains job_role_id, title, company_name,
        compatibility_score (percentage), and required_skills.

    Requirements: 6.1, 6.3, 6.4, 6.5
    """
    user_id = g.current_user["user_id"]

    try:
        engine = JobMatchingEngine()
        recommendations = engine.get_recommendations(user_id)
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if profile:
            for recommendation in recommendations:
                job_role = db.session.get(JobRole, recommendation["job_role_id"])
                if job_role:
                    _, matched, missing, _ = _current_skill_comparison(
                        profile, job_role
                    )
                    recommendation["matched_skills"] = matched
                    recommendation["missing_skills"] = missing
        # Cache successful results for graceful degradation
        _recommendations_cache[user_id] = recommendations
        return jsonify(recommendations), 200
    except Exception as exc:
        logger.exception(
            "JobMatchingEngine failed for user_id=%s: %s", user_id, exc
        )
        # Return cached recommendations if available
        cached = _recommendations_cache.get(user_id)
        if cached is not None:
            return jsonify(cached), 200
        # No cache — return a user-friendly "temporarily unavailable" message
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Job recommendations are temporarily unavailable. Please try again later.",
                        "fields": {},
                    }
                }
            ),
            500,
        )


@job_bp.route("/<int:id>/skill-gap", methods=["GET"])
@jwt_required
@role_required("student")
def get_skill_gap(id):
    """Return skill gap analysis for the authenticated student against a job role.

    Fetches the student's profile and the specified job role, parses their
    vectors, and calls :meth:`JobMatchingEngine.compute_skill_gap`.

    Returns:
        200: JSON with job_role_id, gaps list, and coverage info.
             If no gaps, returns {"message": "Full skill coverage"}.
        404: If the student profile or job role is not found.

    Requirements: 7.1, 7.3, 7.4
    """
    user_id = g.current_user["user_id"]

    # Fetch student profile
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Student profile or skill vector not found",
                        "fields": {},
                    }
                }
            ),
            404,
        )

    # Fetch job role
    job_role = db.session.get(JobRole, id)
    if job_role is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Job role not found",
                        "fields": {},
                    }
                }
            ),
            404,
        )

    _, matched, missing, gaps = _current_skill_comparison(profile, job_role)

    if not gaps:
        return jsonify({
            "job_role_id": id,
            "matched_skills": matched,
            "missing_skills": [],
            "message": "Full skill coverage",
        }), 200

    return (
        jsonify(
            {
                "job_role_id": id,
                "matched_skills": matched,
                "missing_skills": missing,
                "gaps": gaps,
            }
        ),
        200,
    )


@job_bp.route("/<int:id>/courses", methods=["GET"])
@jwt_required
@role_required("student")
def get_courses(id):
    """Return course recommendations for skill gaps against a job role.

    Computes the skill gap first, then for each gap skill queries the
    :class:`CourseRecommendation` table and returns courses grouped by skill.

    Returns:
        200: JSON with job_role_id and courses grouped by skill.
             If no courses exist for a skill, includes a "no courses available" message.
        404: If the student profile or job role is not found.

    Requirements: 8.1, 8.2, 8.3
    """
    user_id = g.current_user["user_id"]

    # Fetch student profile
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Student profile or skill vector not found",
                        "fields": {},
                    }
                }
            ),
            404,
        )

    # Fetch job role
    job_role = db.session.get(JobRole, id)
    if job_role is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Job role not found",
                        "fields": {},
                    }
                }
            ),
            404,
        )

    _, matched, missing, gaps = _current_skill_comparison(profile, job_role)

    # For each gap skill, query CourseRecommendation table
    courses_by_skill = []
    for gap in gaps:
        skill_name = gap["skill"]
        courses = CourseRecommendation.query.filter(
            db.func.lower(CourseRecommendation.skill_name) == skill_name.lower()
        ).all()

        if courses:
            courses_by_skill.append(
                {
                    "skill": skill_name,
                    "deficit_score": gap["deficit_score"],
                    "courses": [c.to_dict() for c in courses],
                }
            )
        else:
            courses_by_skill.append(
                {
                    "skill": skill_name,
                    "deficit_score": gap["deficit_score"],
                    "courses": [],
                    "message": "No courses available for this skill",
                }
            )

    return (
        jsonify(
            {
                "job_role_id": id,
                "matched_skills": matched,
                "missing_skills": missing,
                "skill_courses": courses_by_skill,
            }
        ),
        200,
    )
