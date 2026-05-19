"""Placement Records API routes for the Skill2Job Placement System.

Provides endpoints for recording confirmed placements, listing them,
and updating placement details. Accessible by placement officers and admins.
"""

from datetime import date as date_type

from flask import Blueprint, g, jsonify, request

from app import db
from app.models import PlacementRecord, StudentProfile, JobRole, Company, User
from app.utils.auth_decorator import jwt_required, role_required

placement_bp = Blueprint("placements", __name__, url_prefix="/api/placements")


# ---------------------------------------------------------------------------
# List all placement records
# ---------------------------------------------------------------------------

@placement_bp.route("", methods=["GET"])
@jwt_required
@role_required("placement_officer")
def list_placements():
    """List all placement records with optional filters.

    Query params:
        department: Filter by department/branch
        company_id: Filter by company
        year: Filter by placement year

    Returns:
        200: JSON list of placement records.
    """
    department = request.args.get("department")
    company_id = request.args.get("company_id", type=int)
    year = request.args.get("year", type=int)

    query = PlacementRecord.query

    if department:
        query = query.filter(db.func.lower(PlacementRecord.department) == department.lower())
    if company_id:
        query = query.filter(PlacementRecord.company_id == company_id)
    if year:
        query = query.filter(
            db.extract("year", PlacementRecord.placement_date) == year
        )

    records = query.order_by(PlacementRecord.placement_date.desc()).all()
    return jsonify([r.to_dict() for r in records]), 200


# ---------------------------------------------------------------------------
# Create placement record (mark student as placed)
# ---------------------------------------------------------------------------

@placement_bp.route("", methods=["POST"])
@jwt_required
@role_required("placement_officer")
def create_placement():
    """Record a confirmed student placement.

    Accepts JSON body with:
        profile_id (required): Student profile ID
        job_role_id (required): Job role ID
        company_id (required): Company ID
        placement_date (optional): YYYY-MM-DD
        department (optional): Department/branch
        package_lpa (optional): Salary package in LPA
        notes (optional): Additional notes

    Returns:
        201: Created placement record.
        400: Validation error.
        404: Profile, job role, or company not found.
        409: Placement already recorded for this student + job role.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    errors = {}
    profile_id = json_data.get("profile_id")
    job_role_id = json_data.get("job_role_id")
    company_id = json_data.get("company_id")

    if not profile_id:
        errors["profile_id"] = "Profile ID is required"
    if not job_role_id:
        errors["job_role_id"] = "Job role ID is required"
    if not company_id:
        errors["company_id"] = "Company ID is required"

    if errors:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid input data", "fields": errors}}), 400

    # Verify entities exist
    profile = db.session.get(StudentProfile, profile_id)
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404

    job_role = db.session.get(JobRole, job_role_id)
    if job_role is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Job role not found", "fields": {}}}), 404

    company = db.session.get(Company, company_id)
    if company is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Company not found", "fields": {}}}), 404

    # Check for duplicate
    existing = PlacementRecord.query.filter_by(
        profile_id=profile_id,
        job_role_id=job_role_id,
    ).first()
    if existing:
        return jsonify({"error": {"code": "CONFLICT", "message": "Placement already recorded for this student and job role", "fields": {}}}), 409

    # Parse placement date
    placement_date = None
    placement_date_str = json_data.get("placement_date")
    if placement_date_str:
        try:
            placement_date = date_type.fromisoformat(placement_date_str)
        except ValueError:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid placement_date format. Use YYYY-MM-DD.", "fields": {}}}), 400

    # Get department from profile if not provided
    department = json_data.get("department") or profile.branch

    record = PlacementRecord(
        profile_id=profile_id,
        job_role_id=job_role_id,
        company_id=company_id,
        placement_date=placement_date,
        department=department,
        package_lpa=json_data.get("package_lpa"),
        notes=json_data.get("notes"),
    )
    db.session.add(record)
    db.session.commit()

    # Send placement confirmation email
    try:
        from app.services.email_service import get_email_service
        email_svc = get_email_service()
        user = db.session.get(User, profile.user_id)
        if user and user.email:
            email_svc.send_placement_confirmation(
                to_email=user.email,
                user_name=user.name,
                job_title=job_role.title,
                company_name=company.name,
                package_lpa=json_data.get("package_lpa"),
            )
    except Exception:
        pass

    return jsonify(record.to_dict()), 201


# ---------------------------------------------------------------------------
# Update placement record
# ---------------------------------------------------------------------------

@placement_bp.route("/<int:id>", methods=["PUT"])
@jwt_required
@role_required("placement_officer")
def update_placement(id):
    """Update a placement record (package, date, notes, etc.).

    Returns:
        200: Updated placement record.
        404: Placement record not found.
    """
    record = db.session.get(PlacementRecord, id)
    if record is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Placement record not found", "fields": {}}}), 404

    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    if "placement_date" in json_data and json_data["placement_date"]:
        try:
            record.placement_date = date_type.fromisoformat(json_data["placement_date"])
        except ValueError:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid placement_date format. Use YYYY-MM-DD.", "fields": {}}}), 400

    if "department" in json_data:
        record.department = json_data["department"]
    if "package_lpa" in json_data:
        record.package_lpa = json_data["package_lpa"]
    if "notes" in json_data:
        record.notes = json_data["notes"]
    if "offer_letter_url" in json_data:
        record.offer_letter_url = json_data["offer_letter_url"]

    db.session.commit()
    return jsonify(record.to_dict()), 200


# ---------------------------------------------------------------------------
# Delete placement record
# ---------------------------------------------------------------------------

@placement_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required
@role_required("placement_officer")
def delete_placement(id):
    """Delete a placement record.

    Returns:
        200: Confirmation message.
        404: Placement record not found.
    """
    record = db.session.get(PlacementRecord, id)
    if record is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Placement record not found", "fields": {}}}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Placement record deleted successfully"}), 200


# ---------------------------------------------------------------------------
# Student: view own placement status
# ---------------------------------------------------------------------------

@placement_bp.route("/my", methods=["GET"])
@jwt_required
@role_required("student")
def get_my_placement():
    """Get placement record for the authenticated student.

    Returns:
        200: Placement record or null if not placed.
    """
    user_id = g.current_user["user_id"]
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        return jsonify({"placed": False, "record": None}), 200

    record = PlacementRecord.query.filter_by(profile_id=profile.id).first()
    if record is None:
        return jsonify({"placed": False, "record": None}), 200

    return jsonify({"placed": True, "record": record.to_dict()}), 200
