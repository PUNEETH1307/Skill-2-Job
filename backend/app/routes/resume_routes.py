"""Resume generation API routes for the Skill2Job Placement System.

Provides endpoints for generating, uploading, and downloading student resumes.
"""

import logging
import os
import hashlib
from datetime import datetime, timezone

from flask import Blueprint, jsonify, g, Response, current_app, request, send_from_directory
from werkzeug.utils import secure_filename

from app import db
from app.models import ResumeUpload, User
from app.services.resume_generator import ResumeGenerator
from app.utils.auth_decorator import jwt_required, role_required

resume_bp = Blueprint("resume", __name__, url_prefix="/api/resume")

logger = logging.getLogger(__name__)


def _is_allowed_resume_file(filename: str) -> bool:
    """Check whether the upload filename has an allowed resume extension."""
    allowed = current_app.config.get('ALLOWED_RESUME_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _validation_error(message: str, status_code: int = 400):
    """Return a consistent resume validation error response."""
    fields = {}
    marker = "Profile is missing required fields:"
    if marker in message:
        missing = [
            field.strip()
            for field in message.split(marker, 1)[1].split(",")
            if field.strip()
        ]
        fields["missing_fields"] = missing

    return (
        jsonify(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": message,
                    "fields": fields,
                }
            }
        ),
        status_code,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@resume_bp.route("/parse-for-profile", methods=["POST"])
@jwt_required
@role_required("student")
def parse_resume_for_profile():
    """Upload a resume and extract profile data from it using NLP.

    Returns extracted profile fields (skills, education, projects, etc.)
    that can be used to auto-populate the student profile form.
    Also saves the uploaded file and creates the profile if one doesn't exist.
    """
    if 'resume' not in request.files:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "No resume file was provided",
                    }
                }
            ),
            400,
        )

    file = request.files['resume']
    if file.filename == '':
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "No resume file was provided",
                    }
                }
            ),
            400,
        )

    if not _is_allowed_resume_file(file.filename):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Only PDF and DOCX files are allowed",
                    }
                }
            ),
            400,
        )

    user_id = g.current_user["user_id"]
    user = db.session.get(User, user_id)

    # Save the file
    filename = secure_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    stored_filename = f"{user_id}_{timestamp}_{filename}"
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, stored_filename)
    file.save(file_path)

    # Ensure profile exists for the resume upload record
    from app.models import StudentProfile
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    # Save upload record
    resume_record = ResumeUpload(
        profile_id=profile.id,
        original_filename=filename,
        stored_filename=stored_filename,
        content_type=file.content_type or 'application/octet-stream',
    )
    db.session.add(resume_record)
    db.session.commit()

    # Parse the resume to extract profile data
    from app.services.resume_parser import ResumeParser
    parser = ResumeParser()
    extracted_data = parser.parse_resume(file_path)

    return jsonify({
        "message": "Resume parsed successfully",
        "extracted_profile": extracted_data,
        "upload": resume_record.to_dict(),
    }), 200


@resume_bp.route("/upload", methods=["POST"])
@jwt_required
@role_required("student")
def upload_resume():
    """Upload a student resume file to the server."""
    if 'resume' not in request.files:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "No resume file was provided",
                    }
                }
            ),
            400,
        )

    file = request.files['resume']
    if file.filename == '':
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "No resume file was provided",
                    }
                }
            ),
            400,
        )

    if not _is_allowed_resume_file(file.filename):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Only PDF and DOCX files are allowed",
                    }
                }
            ),
            400,
        )

    user_id = g.current_user["user_id"]
    user = db.session.get(User, user_id)
    profile = user.profile if user else None
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Student profile not found",
                    }
                }
            ),
            404,
        )

    filename = secure_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    stored_filename = f"{user_id}_{timestamp}_{filename}"
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, stored_filename)
    file.save(file_path)

    resume_record = ResumeUpload(
        profile_id=profile.id,
        original_filename=filename,
        stored_filename=stored_filename,
        content_type=file.content_type or 'application/octet-stream',
    )
    db.session.add(resume_record)
    db.session.commit()

    return jsonify({
        "message": "Resume uploaded successfully",
        "upload": resume_record.to_dict(),
    }), 201


@resume_bp.route("/uploads", methods=["GET"])
@jwt_required
@role_required("student")
def list_uploaded_resumes():
    """List resumes uploaded by the authenticated student."""
    user_id = g.current_user["user_id"]
    user = db.session.get(User, user_id)
    profile = user.profile if user else None
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Student profile not found",
                    }
                }
            ),
            404,
        )

    uploads = [upload.to_dict() for upload in profile.resume_uploads]
    return jsonify({"uploads": uploads}), 200


@resume_bp.route("/uploads/<int:upload_id>/download", methods=["GET"])
@jwt_required
@role_required("student")
def download_upload(upload_id: int):
    """Download a previously uploaded resume file."""
    user_id = g.current_user["user_id"]
    user = db.session.get(User, user_id)
    profile = user.profile if user else None
    if profile is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Student profile not found",
                    }
                }
            ),
            404,
        )

    upload = db.session.get(ResumeUpload, upload_id)
    if upload is None or upload.profile_id != profile.id:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Resume upload not found",
                    }
                }
            ),
            404,
        )

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    return send_from_directory(
        upload_folder,
        upload.stored_filename,
        as_attachment=True,
        download_name=upload.original_filename,
        mimetype=upload.content_type,
    )


@resume_bp.route("/generate", methods=["POST"])
@jwt_required
@role_required("student")
def generate_resume():
    """Generate a resume for the authenticated student.

    Accepts optional JSON body:
        template (str): Template ID — classic, modern, minimal,
                        sidebar, executive, photo_classic,
                        photo_modern, photo_sidebar. Default: classic.
        profile_override (dict): Optional field overrides to fill
                                 missing profile data inline.
    """
    user_id = g.current_user["user_id"]

    json_data = request.get_json(silent=True) or {}
    template_id = json_data.get("template", "classic")
    profile_override = json_data.get("profile_override", {})

    try:
        generator = ResumeGenerator()
        pdf_bytes = generator.generate_resume(
            user_id,
            template_id=template_id,
            profile_override=profile_override,
        )
        user = db.session.get(User, user_id)
        filename = generator.get_download_filename(user.name if user else "Student")

        generated_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER'), 'generated_resumes')
        os.makedirs(generated_folder, exist_ok=True)
        generated_path = os.path.join(generated_folder, f"{user_id}.pdf")
        with open(generated_path, 'wb') as pdf_file:
            pdf_file.write(pdf_bytes)

        return jsonify({
            "message": "Resume generated successfully",
            "filename": filename,
            "size_bytes": len(pdf_bytes),
        }), 200
    except ValueError as exc:
        return _validation_error(str(exc))
    except Exception as exc:
        logger.exception(
            "ResumeGenerator failed for user_id=%s: %s", user_id, exc
        )
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Resume generation failed. Please try again.",
                        "retry": True,
                    }
                }
            ),
            500,
        )


@resume_bp.route("/download", methods=["GET"])
@jwt_required
@role_required("student")
def download_resume():
    """Download the student's resume as PDF. Accepts ?template= query param."""
    user_id = g.current_user["user_id"]
    template_id = request.args.get("template", "classic")

    try:
        generated_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER'), 'generated_resumes')
        generated_path = os.path.join(generated_folder, f"{user_id}.pdf")

        if os.path.exists(generated_path):
            user = db.session.get(User, user_id)
            generator = ResumeGenerator()
            filename = generator.get_download_filename(user.name if user else "Student")
            return send_from_directory(
                generated_folder,
                f"{user_id}.pdf",
                as_attachment=True,
                download_name=filename,
                mimetype="application/pdf",
            )

        generator = ResumeGenerator()
        pdf_bytes = generator.generate_resume(user_id, template_id=template_id)

        user = db.session.get(User, user_id)
        filename = generator.get_download_filename(user.name)

        return Response(
            pdf_bytes,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    except ValueError as exc:
        return _validation_error(str(exc))
    except Exception as exc:
        logger.exception(
            "ResumeGenerator download failed for user_id=%s: %s", user_id, exc
        )
        return (
            jsonify(
                {
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": "Resume download failed. Please try again.",
                        "retry": True,
                    }
                }
            ),
            500,
        )
