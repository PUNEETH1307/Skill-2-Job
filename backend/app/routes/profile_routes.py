"""Student profile API routes for the Skill2Job Placement System.

Provides endpoints for retrieving and updating student profiles,
including nested projects, certifications, and skill data.
"""

import os

from flask import Blueprint, request, jsonify, g, current_app, send_from_directory
from werkzeug.utils import secure_filename

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
        if isinstance(error_detail, dict):
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid input data", "fields": error_detail}}), 400
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(error_detail), "fields": {}}}), 400


@profile_bp.route("/profile/photo", methods=["POST"])
@jwt_required
@role_required("student")
def upload_profile_photo():
    """Upload or replace the authenticated student's profile photo."""
    photo = request.files.get("photo")
    if not photo or not photo.filename:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Please select a photo"}}), 400
    if photo.mimetype not in {"image/jpeg", "image/png", "image/webp"}:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Only JPG, PNG, and WEBP photos are allowed"}}), 400

    from app import db
    from app.models import StudentProfile
    user_id = g.current_user["user_id"]
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.session.add(profile)

    filename = secure_filename(photo.filename)
    extension = filename.rsplit(".", 1)[-1].lower()
    stored_filename = f"profile_{user_id}.{extension}"
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    os.makedirs(upload_folder, exist_ok=True)
    photo.save(os.path.join(upload_folder, stored_filename))
    profile.photo_filename = stored_filename
    db.session.commit()
    generated_folder = os.path.join(upload_folder, "generated_resumes")
    if os.path.isdir(generated_folder):
        for generated_name in os.listdir(generated_folder):
            if generated_name.startswith(f"{user_id}_") and generated_name.endswith(".pdf"):
                try:
                    os.remove(os.path.join(generated_folder, generated_name))
                except OSError:
                    pass
    return jsonify({"message": "Profile photo updated", "photo_url": "/api/profile/photo"}), 200


@profile_bp.route("/profile/photo", methods=["GET"])
@jwt_required
@role_required("student")
def get_profile_photo():
    """Serve the authenticated student's profile photo."""
    from app.models import StudentProfile
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    if not profile or not profile.photo_filename:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Profile photo not found"}}), 404
    return send_from_directory(current_app.config.get("UPLOAD_FOLDER"), profile.photo_filename)
