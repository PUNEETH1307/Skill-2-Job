"""Skill analysis API routes for the Skill2Job Placement System.

Provides an endpoint for retrieving categorized skill breakdowns
for the authenticated student.
"""

from flask import Blueprint, jsonify, g

from app import db
from app.models import StudentProfile
from app.services.skill_analyzer import SkillAnalyzer
from app.utils.auth_decorator import jwt_required, role_required

skill_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@skill_bp.route("/analysis", methods=["GET"])
@jwt_required
@role_required("student")
def get_skill_analysis():
    """Return categorized skill breakdown for the logged-in student.

    Fetches the student's profile, runs a fresh skill analysis via
    :meth:`SkillAnalyzer.analyze_and_store`, and returns the categorized
    skill breakdown as JSON.

    Returns:
        200: JSON with ``skills``, ``categories``, and ``vector_stored``.
        404: If the student has no profile.

    Requirements: 5.6
    """
    user_id = g.current_user["user_id"]

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Profile not found",
                        "fields": {},
                    }
                }
            ),
            404,
        )

    analyzer = SkillAnalyzer()
    result = analyzer.analyze_and_store(profile)

    return jsonify(result), 200
