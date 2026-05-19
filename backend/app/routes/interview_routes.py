"""Interview management API routes for the Skill2Job Placement System.

Provides endpoints for scheduling, listing, updating, and deleting
interview slots. Accessible by placement officers and admins.
"""

from datetime import date as date_type

from flask import Blueprint, g, jsonify, request

from app import db
from app.models import Interview, StudentProfile, JobRole, Company, User
from app.utils.auth_decorator import jwt_required, role_required

interview_bp = Blueprint("interviews", __name__, url_prefix="/api/interviews")


# ---------------------------------------------------------------------------
# List interviews
# ---------------------------------------------------------------------------

@interview_bp.route("", methods=["GET"])
@jwt_required
@role_required("placement_officer")
def list_interviews():
    """List all interviews with optional filters.

    Query params:
        status: Filter by status (scheduled, completed, cancelled, no-show)
        profile_id: Filter by student profile ID
        job_role_id: Filter by job role ID

    Returns:
        200: JSON list of interview records.
    """
    status = request.args.get("status")
    profile_id = request.args.get("profile_id", type=int)
    job_role_id = request.args.get("job_role_id", type=int)

    query = Interview.query

    if status:
        query = query.filter(Interview.status == status)
    if profile_id:
        query = query.filter(Interview.profile_id == profile_id)
    if job_role_id:
        query = query.filter(Interview.job_role_id == job_role_id)

    interviews = query.order_by(Interview.interview_date.desc()).all()
    return jsonify([i.to_dict() for i in interviews]), 200


# ---------------------------------------------------------------------------
# Create interview
# ---------------------------------------------------------------------------

@interview_bp.route("", methods=["POST"])
@jwt_required
@role_required("placement_officer")
def create_interview():
    """Schedule a new interview.

    Accepts JSON body with:
        profile_id (required): Student profile ID
        interview_date (required): Date string YYYY-MM-DD
        job_role_id (optional): Job role ID
        company_id (optional): Company ID
        interview_time (optional): e.g. "10:00 AM"
        mode (optional): in-person | online | phone
        venue_or_link (optional): Location or meeting link

    Returns:
        201: Created interview record.
        400: Validation error.
        404: Profile or job role not found.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    errors = {}
    profile_id = json_data.get("profile_id")
    interview_date_str = json_data.get("interview_date", "").strip() if json_data.get("interview_date") else ""

    if not profile_id:
        errors["profile_id"] = "Profile ID is required"
    if not interview_date_str:
        errors["interview_date"] = "Interview date is required"

    if errors:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid input data", "fields": errors}}), 400

    # Parse date
    try:
        interview_date = date_type.fromisoformat(interview_date_str)
    except ValueError:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid date format. Use YYYY-MM-DD.", "fields": {"interview_date": "Invalid date format"}}}), 400

    # Verify profile exists
    profile = db.session.get(StudentProfile, profile_id)
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404

    # Optionally verify job role
    job_role_id = json_data.get("job_role_id")
    if job_role_id:
        job_role = db.session.get(JobRole, job_role_id)
        if job_role is None:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Job role not found", "fields": {}}}), 404

    # Optionally verify company
    company_id = json_data.get("company_id")
    if company_id:
        company = db.session.get(Company, company_id)
        if company is None:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Company not found", "fields": {}}}), 404

    interview = Interview(
        profile_id=profile_id,
        job_role_id=job_role_id,
        company_id=company_id,
        scheduled_by=g.current_user["user_id"],
        interview_date=interview_date,
        interview_time=json_data.get("interview_time"),
        mode=json_data.get("mode", "in-person"),
        venue_or_link=json_data.get("venue_or_link"),
        status="scheduled",
    )
    db.session.add(interview)
    db.session.commit()

    # Send email notification to student
    try:
        from app.services.email_service import get_email_service
        email_svc = get_email_service()
        user = db.session.get(User, profile.user_id)
        if user and user.email:
            job_title = db.session.get(JobRole, job_role_id).title if job_role_id else "N/A"
            company_name = db.session.get(Company, company_id).name if company_id else "N/A"
            email_svc.send_interview_scheduled(
                to_email=user.email,
                user_name=user.name,
                job_title=job_title,
                company_name=company_name,
                interview_date=interview_date_str,
                interview_time=json_data.get("interview_time", "TBD"),
                mode=json_data.get("mode", "in-person"),
                venue_or_link=json_data.get("venue_or_link", ""),
            )
    except Exception:
        pass  # Don't fail if email fails

    return jsonify(interview.to_dict()), 201


# ---------------------------------------------------------------------------
# Update interview
# ---------------------------------------------------------------------------

@interview_bp.route("/<int:id>", methods=["PUT"])
@jwt_required
@role_required("placement_officer")
def update_interview(id):
    """Update an interview record (status, feedback, result, etc.).

    Returns:
        200: Updated interview record.
        404: Interview not found.
    """
    interview = db.session.get(Interview, id)
    if interview is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Interview not found", "fields": {}}}), 404

    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    allowed_statuses = {"scheduled", "completed", "cancelled", "no-show"}
    allowed_results = {"selected", "rejected", "on-hold", None}

    if "status" in json_data:
        if json_data["status"] not in allowed_statuses:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": f"Status must be one of: {', '.join(allowed_statuses)}", "fields": {}}}), 400
        interview.status = json_data["status"]

    if "result" in json_data:
        if json_data["result"] not in allowed_results:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Result must be selected, rejected, or on-hold", "fields": {}}}), 400
        interview.result = json_data["result"]

    if "feedback" in json_data:
        interview.feedback = json_data["feedback"]
    if "interview_time" in json_data:
        interview.interview_time = json_data["interview_time"]
    if "mode" in json_data:
        interview.mode = json_data["mode"]
    if "venue_or_link" in json_data:
        interview.venue_or_link = json_data["venue_or_link"]

    if "interview_date" in json_data:
        try:
            interview.interview_date = date_type.fromisoformat(json_data["interview_date"])
        except ValueError:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid date format. Use YYYY-MM-DD.", "fields": {}}}), 400

    db.session.commit()

    # If result is "selected", auto-create placement record
    if json_data.get("result") == "selected" and interview.job_role_id and interview.company_id:
        from app.models import PlacementRecord
        existing = PlacementRecord.query.filter_by(
            profile_id=interview.profile_id,
            job_role_id=interview.job_role_id,
        ).first()
        if not existing:
            record = PlacementRecord(
                profile_id=interview.profile_id,
                job_role_id=interview.job_role_id,
                company_id=interview.company_id,
                placement_date=interview.interview_date,
            )
            db.session.add(record)
            db.session.commit()

    return jsonify(interview.to_dict()), 200


# ---------------------------------------------------------------------------
# Delete interview
# ---------------------------------------------------------------------------

@interview_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required
@role_required("placement_officer")
def delete_interview(id):
    """Delete an interview record.

    Returns:
        200: Confirmation message.
        404: Interview not found.
    """
    interview = db.session.get(Interview, id)
    if interview is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Interview not found", "fields": {}}}), 404

    db.session.delete(interview)
    db.session.commit()
    return jsonify({"message": "Interview deleted successfully"}), 200


# ---------------------------------------------------------------------------
# Student: view own interviews
# ---------------------------------------------------------------------------

@interview_bp.route("/my", methods=["GET"])
@jwt_required
@role_required("student")
def get_my_interviews():
    """Get interviews scheduled for the authenticated student.

    Returns:
        200: JSON list of interview records for the student.
        404: Student profile not found.
    """
    user_id = g.current_user["user_id"]
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404

    interviews = Interview.query.filter_by(profile_id=profile.id).order_by(Interview.interview_date.desc()).all()
    return jsonify([i.to_dict() for i in interviews]), 200
