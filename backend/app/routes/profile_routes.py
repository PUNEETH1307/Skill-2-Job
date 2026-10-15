"""Student profile API routes for the Skill2Job Placement System.

Provides endpoints for retrieving and updating student profiles,
including nested projects, certifications, and skill data.
"""

import os
from datetime import datetime, timezone

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

    filename = secure_filename(photo.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_extensions = {"jpg", "jpeg", "png", "webp"}
    allowed_mimetypes = {
        "image/jpeg",
        "image/jpg",
        "image/pjpeg",
        "image/png",
        "image/x-png",
        "image/webp",
    }
    mime_to_extension = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/pjpeg": "jpg",
        "image/png": "png",
        "image/x-png": "png",
        "image/webp": "webp",
    }

    is_valid_extension = extension in allowed_extensions
    is_valid_mimetype = (photo.mimetype or "") in allowed_mimetypes
    resolved_extension = extension if is_valid_extension else mime_to_extension.get(photo.mimetype or "", "")
    if not (is_valid_extension or is_valid_mimetype) or not resolved_extension:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Only JPG, PNG, and WEBP photos are allowed"}}), 400

    from app import db
    from app.models import StudentProfile
    user_id = g.current_user["user_id"]
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.session.add(profile)

    stored_filename = f"profile_{user_id}.{resolved_extension}"
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


@profile_bp.route("/profile/certifications/<int:certification_id>/certificate", methods=["POST"])
@jwt_required
@role_required("student")
def upload_certificate(certification_id):
    """Upload or replace proof for one certification."""
    from app import db
    from app.models import Certification, StudentProfile

    certification = db.session.get(Certification, certification_id)
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    if certification is None or profile is None or certification.profile_id != profile.id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Certification not found"}}), 404

    certificate = request.files.get("certificate")
    if not certificate or not certificate.filename:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Please select a certificate"}}), 400

    filename = secure_filename(certificate.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = current_app.config.get("ALLOWED_CERTIFICATE_EXTENSIONS", set())
    if extension not in allowed:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Only PDF, JPG, PNG, and WEBP certificates are allowed",
            }
        }), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    certificate_folder = os.path.join(upload_folder, "certificates")
    os.makedirs(certificate_folder, exist_ok=True)
    stored_filename = f"{profile.user_id}_{certification.id}_{filename}"
    certificate.save(os.path.join(certificate_folder, stored_filename))
    certification.certificate_original_filename = filename
    certification.certificate_stored_filename = stored_filename
    certification.certificate_content_type = certificate.content_type or "application/octet-stream"
    certification.certificate_uploaded_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(certification.to_dict()), 200


@profile_bp.route("/profile/certifications/<int:certification_id>/certificate", methods=["GET"])
@jwt_required
def download_certificate(certification_id):
    """Serve a certificate to its owner or a placement officer/admin."""
    from app import db
    from app.models import Certification

    certification = db.session.get(Certification, certification_id)
    current_user = g.current_user
    if certification is None or not certification.certificate_stored_filename:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Certificate not found"}}), 404
    if current_user["role"] == "student" and certification.profile.user_id != current_user["user_id"]:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    if current_user["role"] not in {"student", "placement_officer", "admin"}:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    return send_from_directory(
        os.path.join(current_app.config["UPLOAD_FOLDER"], "certificates"),
        certification.certificate_stored_filename,
        as_attachment=False,
        download_name=certification.certificate_original_filename,
        mimetype=certification.certificate_content_type,
    )
