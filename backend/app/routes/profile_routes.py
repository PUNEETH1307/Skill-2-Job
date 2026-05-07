"""Student profile API routes for the Skill2Job Placement System.

Provides endpoints for retrieving and updating student profiles,
including nested projects, certifications, and skill data.
"""

from flask import Blueprint, request, jsonify, g

from app.services import profile_service
from app.utils.auth_decorator import jwt_required, role_required

profile_bp = Blueprint("profile", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@profile_bp.route("/profile", methods=["GET"])
@jwt_required
@role_required("student")
def get_profile():
    """Retrieve the authenticated student's profile.

    Returns the profile with projects, certifications, and skill data.
    Returns 404 if no profile exists yet.
    """
    user_id = g.current_user["user_id"]
    profile = profile_service.get_profile(user_id)

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

    return jsonify(profile), 200


@profile_bp.route("/profile", methods=["PUT"])
@jwt_required
@role_required("student")
def update_profile():
    """Create or update the authenticated student's profile.

    Accepts JSON body with academic details, skills, projects, and
    certifications. Validates required fields and CGPA range via
    the profile service.
    """
    user_id = g.current_user["user_id"]

    json_data = request.get_json(silent=True)
    if not json_data:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request body must be valid JSON",
                        "fields": {},
                    }
                }
            ),
            400,
        )

    try:
        updated_profile = profile_service.create_or_update_profile(user_id, json_data)
        return jsonify(updated_profile), 200
    except ValueError as exc:
        error_detail = exc.args[0] if exc.args else {}
        # The profile service raises ValueError with a dict of field errors
        if isinstance(error_detail, dict):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid input data",
                            "fields": error_detail,
                        }
                    }
                ),
                400,
            )
        # Fallback for string error messages
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(error_detail),
                        "fields": {},
                    }
                }
            ),
            400,
        )
