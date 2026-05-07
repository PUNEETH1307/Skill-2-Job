"""Resume generation API routes for the Skill2Job Placement System.

Provides endpoints for generating and downloading professional PDF
resumes from student profile data.
"""

import logging

from flask import Blueprint, jsonify, g, Response

from app import db
from app.models import User
from app.services.resume_generator import ResumeGenerator
from app.utils.auth_decorator import jwt_required, role_required

resume_bp = Blueprint("resume", __name__, url_prefix="/api/resume")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@resume_bp.route("/generate", methods=["POST"])
@jwt_required
@role_required("student")
def generate_resume():
    """Generate a resume for the authenticated student.

    Validates the student's profile and generates a PDF resume.
    Returns 200 on success or 400 if the profile is missing required fields.
    """
    user_id = g.current_user["user_id"]

    try:
        generator = ResumeGenerator()
        generator.generate_resume(user_id)
        return jsonify({"message": "Resume generated successfully"}), 200
    except ValueError as exc:
        error_message = str(exc)
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": error_message,
                    }
                }
            ),
            400,
        )
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
    """Download the authenticated student's resume as a PDF attachment.

    Generates the PDF on-the-fly from the latest profile data and
    returns it with the appropriate Content-Disposition header.
    """
    user_id = g.current_user["user_id"]

    try:
        generator = ResumeGenerator()
        pdf_bytes = generator.generate_resume(user_id)

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
        error_message = str(exc)
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": error_message,
                    }
                }
            ),
            400,
        )
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
