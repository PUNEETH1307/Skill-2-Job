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
    """Return categorized skill breakdown for the logged-in student."""
    user_id = g.current_user["user_id"]

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return (
            jsonify({"error": {"code": "NOT_FOUND", "message": "Profile not found", "fields": {}}}),
            404,
        )

    analyzer = SkillAnalyzer()
    result = analyzer.analyze_and_store(profile)

    # If taxonomy is empty / skills not recognized, fall back to raw skills_json
    if not result.get("skills") and profile.skills_json:
        try:
            import json as _json
            raw_skills = _json.loads(profile.skills_json)
            if isinstance(raw_skills, list) and raw_skills:
                result["skills"] = [str(s).strip() for s in raw_skills if str(s).strip()]
                # Attempt categorization; if still empty, bucket as 'Skills'
                if not result.get("categories"):
                    result["categories"] = {"Skills": result["skills"]}
        except Exception:
            pass

    return jsonify(result), 200
