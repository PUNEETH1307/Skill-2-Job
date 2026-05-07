"""Job matching API routes for the Skill2Job Placement System.

Provides endpoints for job recommendations, skill gap analysis,
and course recommendations for gap skills.

Requirements: 6.1, 6.3, 6.4, 6.5, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3
"""

import json
import logging

import numpy as np
from flask import Blueprint, jsonify, g

from app import db
from app.models import StudentProfile, JobRole, CourseRecommendation
from app.services.job_matching import JobMatchingEngine
from app.utils.auth_decorator import jwt_required, role_required

job_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

logger = logging.getLogger(__name__)

# In-memory cache for recommendations (keyed by user_id).
# Used as a fallback when the JobMatchingEngine fails.
_recommendations_cache: dict[int, list[dict]] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


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
    if profile is None or not profile.skill_vector_json:
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

    if not job_role.job_vector_json:
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Job role has no skill vector",
                        "fields": {},
                    }
                }
            ),
            500,
        )

    # Parse vectors
    try:
        student_data = json.loads(profile.skill_vector_json)
        job_data = json.loads(job_role.job_vector_json)
    except (json.JSONDecodeError, TypeError):
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Failed to parse skill vectors",
                        "fields": {},
                    }
                }
            ),
            500,
        )

    student_vector = np.array(student_data.get("vector", []), dtype=float)
    job_vector = np.array(job_data.get("vector", []), dtype=float)
    skill_index = job_data.get("skill_index", {})

    # Compute skill gap
    engine = JobMatchingEngine()
    gaps = engine.compute_skill_gap(student_vector, job_vector, skill_index)

    if not gaps:
        return jsonify({"message": "Full skill coverage"}), 200

    return (
        jsonify(
            {
                "job_role_id": id,
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
    if profile is None or not profile.skill_vector_json:
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

    if not job_role.job_vector_json:
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Job role has no skill vector",
                        "fields": {},
                    }
                }
            ),
            500,
        )

    # Parse vectors
    try:
        student_data = json.loads(profile.skill_vector_json)
        job_data = json.loads(job_role.job_vector_json)
    except (json.JSONDecodeError, TypeError):
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Failed to parse skill vectors",
                        "fields": {},
                    }
                }
            ),
            500,
        )

    student_vector = np.array(student_data.get("vector", []), dtype=float)
    job_vector = np.array(job_data.get("vector", []), dtype=float)
    skill_index = job_data.get("skill_index", {})

    # Compute skill gap
    engine = JobMatchingEngine()
    gaps = engine.compute_skill_gap(student_vector, job_vector, skill_index)

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
                "skill_courses": courses_by_skill,
            }
        ),
        200,
    )
