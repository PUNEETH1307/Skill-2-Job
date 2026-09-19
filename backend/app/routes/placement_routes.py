"""Placement Records API routes for the Skill2Job Placement System.

Provides endpoints for recording confirmed placements, listing them,
and updating placement details. Accessible by placement officers and admins.
"""

from datetime import date as date_type, datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db
from app.models import (
    PlacementRecord, StudentProfile, JobRole, Company, User, DriveRegistration,
    PlacementDrive, DriveShortlist,
)
from app.utils.auth_decorator import jwt_required, role_required

placement_bp = Blueprint("placements", __name__, url_prefix="/api/placements")


@placement_bp.route("/drives", methods=["GET"])
@jwt_required
@role_required("student")
def list_student_drives():
    """List active placement drives and the student's registration status."""
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    if profile is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student profile not found", "fields": {}}}), 404
    registrations = {item.drive_id: item for item in DriveRegistration.query.filter_by(profile_id=profile.id).all()}
    drives = []
    for drive in PlacementDrive.query.filter(PlacementDrive.status == "open").order_by(PlacementDrive.drive_date.asc()).all():
        item = drive.to_dict()
        item["registration"] = registrations.get(drive.id).to_dict() if registrations.get(drive.id) else None
        item["blocked"] = profile.missed_drive_blocks > 0
        item["eligible"], item["eligibility_reasons"] = _drive_eligibility(profile, drive)
        item["deadline_passed"] = bool(drive.registration_deadline and drive.registration_deadline < datetime.now(timezone.utc).replace(tzinfo=None))
        drives.append(item)
    return jsonify({"missed_drive_blocks": profile.missed_drive_blocks, "drives": drives}), 200


@placement_bp.route("/drives/<int:job_role_id>/register", methods=["POST"])
@jwt_required
@role_required("student")
def register_for_drive(job_role_id):
    """Register for a drive, rejecting students serving a missed-drive block."""
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    drive = db.session.get(PlacementDrive, job_role_id)
    if profile is None or drive is None or drive.status != "open":
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Active drive not found", "fields": {}}}), 404
    if not _drive_eligible(profile, drive):
        return jsonify({"error": {"code": "NOT_ELIGIBLE", "message": "You do not meet this drive's eligibility criteria.", "fields": {}}}), 403
    if drive.registration_deadline and drive.registration_deadline < datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({"error": {"code": "DEADLINE_PASSED", "message": "The registration deadline for this drive has passed.", "fields": {}}}), 403
    if profile.missed_drive_blocks > 0:
        return jsonify({"error": {"code": "DRIVE_BLOCKED", "message": f"Registration is unavailable. You missed a previous eligible drive and are blocked from the next {profile.missed_drive_blocks} drive(s).", "fields": {}}}), 403
    registration = DriveRegistration.query.filter_by(profile_id=profile.id, drive_id=drive.id).first()
    if registration is None:
        registration = DriveRegistration(profile_id=profile.id, job_role_id=drive.job_role_id, drive_id=drive.id)
        db.session.add(registration)
        db.session.commit()
    return jsonify(registration.to_dict()), 201


@placement_bp.route("/drives/<int:drive_id>/attend", methods=["POST"])
@jwt_required
@role_required("student")
def attend_drive(drive_id):
    profile = StudentProfile.query.filter_by(user_id=g.current_user["user_id"]).first()
    drive = db.session.get(PlacementDrive, drive_id)
    registration = DriveRegistration.query.filter_by(profile_id=profile.id if profile else None, drive_id=drive_id).first()
    if not profile or not drive or not registration:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Drive registration not found", "fields": {}}}), 404
    code = (request.get_json(silent=True) or {}).get("attendance_code", "").strip()
    if code != drive.attendance_code:
        return jsonify({"error": {"code": "INVALID_CODE", "message": "Attendance code is incorrect.", "fields": {}}}), 400
    registration.attended = True
    registration.status = "attended"
    db.session.commit()
    return jsonify(registration.to_dict()), 200


def _drive_eligible(profile, drive):
    eligible, _ = _drive_eligibility(profile, drive)
    return eligible


def _drive_eligibility(profile, drive):
    import json
    reasons = []
    if (profile.cgpa or 0.0) < drive.minimum_cgpa:
        reasons.append(f"Your CGPA is {profile.cgpa if profile.cgpa is not None else 'not provided'}; minimum required is {drive.minimum_cgpa}.")
    if drive.no_backlogs_required and (profile.backlogs_count or 0) > 0:
        reasons.append(f"The drive requires no backlogs; your profile has {profile.backlogs_count}.")
    try:
        years = json.loads(drive.allowed_graduation_years_json) if drive.allowed_graduation_years_json else []
    except (TypeError, ValueError):
        years = []
    if years and profile.graduation_year not in years:
        reasons.append(f"This drive accepts graduation years {', '.join(str(year) for year in years)}; your year is {profile.graduation_year or 'not provided'}.")
    return not reasons, reasons


@placement_bp.route("/drive-management", methods=["GET", "POST"])
@jwt_required
@role_required("placement_officer")
def manage_drives():
    if request.method == "GET":
        return jsonify([drive.to_dict() for drive in PlacementDrive.query.order_by(PlacementDrive.drive_date.desc()).all()]), 200
    data = request.get_json(silent=True) or {}
    required = ("company_id", "job_role_id", "title", "drive_date", "attendance_code")
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Required drive details are missing.", "fields": {field: "Required" for field in missing}}}), 400
    try:
        drive_date = date_type.fromisoformat(data["drive_date"])
    except ValueError:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "drive_date must use YYYY-MM-DD.", "fields": {}}}), 400
    drive = PlacementDrive(
        company_id=data["company_id"], job_role_id=data["job_role_id"], title=data["title"].strip(),
        description=data.get("description"), job_description=data.get("job_description"),
        package_lpa=data.get("package_lpa"), location=data.get("location"),
        eligibility_criteria=data.get("eligibility_criteria"), minimum_cgpa=data.get("minimum_cgpa", 0),
        allowed_graduation_years_json=__import__("json").dumps(data.get("allowed_graduation_years", [])),
        no_backlogs_required=bool(data.get("no_backlogs_required")), drive_date=drive_date,
        registration_deadline=datetime.fromisoformat(data["registration_deadline"]) if data.get("registration_deadline") else None,
        drive_time=data.get("drive_time"), attendance_code=data["attendance_code"].strip(),
        status="open",
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify(drive.to_dict()), 201


@placement_bp.route("/drive-management/<int:drive_id>", methods=["PUT", "DELETE"])
@jwt_required
@role_required("placement_officer")
def update_drive(drive_id):
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Drive not found", "fields": {}}}), 404
    if request.method == "DELETE":
        db.session.delete(drive)
        db.session.commit()
        return jsonify({"message": "Drive deleted"}), 200
    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "job_description", "package_lpa", "location", "eligibility_criteria", "minimum_cgpa", "no_backlogs_required", "drive_time", "attendance_code", "status"):
        if field in data:
            setattr(drive, field, data[field])
    if "allowed_graduation_years" in data:
        drive.allowed_graduation_years_json = __import__("json").dumps(data["allowed_graduation_years"])
    if "drive_date" in data:
        drive.drive_date = date_type.fromisoformat(data["drive_date"])
    db.session.commit()
    return jsonify(drive.to_dict()), 200


@placement_bp.route("/drive-management/<int:drive_id>/shortlist", methods=["GET", "POST", "DELETE"])
@jwt_required
@role_required("placement_officer")
def manage_drive_shortlist(drive_id):
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Drive not found", "fields": {}}}), 404
    if request.method == "GET":
        eligible = StudentProfile.query.all()
        current = {item.profile_id: item for item in drive.shortlists}
        return jsonify({"eligible_candidates": [{"profile_id": p.id, "student_name": p.user.name, "cgpa": p.cgpa, "graduation_year": p.graduation_year, "backlogs_count": p.backlogs_count, "eligible": _drive_eligibility(p, drive)[0], "eligibility_reasons": _drive_eligibility(p, drive)[1], "shortlisted": p.id in current} for p in eligible], "shortlisted": [item.to_dict() for item in drive.shortlists]}), 200
    data = request.get_json(silent=True) or {}
    profile_id = data.get("profile_id")
    item = DriveShortlist.query.filter_by(drive_id=drive_id, profile_id=profile_id).first()
    if request.method == "DELETE":
        if item:
            db.session.delete(item); db.session.commit()
        return jsonify({"message": "Student removed from shortlist"}), 200
    profile = db.session.get(StudentProfile, profile_id)
    if not profile or not _drive_eligible(profile, drive):
        return jsonify({"error": {"code": "NOT_ELIGIBLE", "message": "Student does not meet drive criteria.", "fields": {}}}), 400
    if not item:
        item = DriveShortlist(drive_id=drive_id, profile_id=profile_id, status="shortlisted")
        db.session.add(item); db.session.commit()
    return jsonify(item.to_dict()), 201


@placement_bp.route("/drives/<int:job_role_id>/missed/<int:profile_id>", methods=["POST"])
@jwt_required
@role_required("placement_officer")
def mark_drive_missed(job_role_id, profile_id):
    """Mark an eligible non-registrant as missed and apply the two-drive block."""
    profile = db.session.get(StudentProfile, profile_id)
    role = db.session.get(JobRole, job_role_id)
    if profile is None or role is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Student or drive not found", "fields": {}}}), 404
    if (profile.cgpa or 0.0) < (role.cgpa_threshold or 0.0):
        return jsonify({"error": {"code": "NOT_ELIGIBLE", "message": "This student is below the drive's eligibility threshold.", "fields": {}}}), 400
    registration = DriveRegistration.query.filter_by(profile_id=profile_id, job_role_id=job_role_id).first()
    if registration and registration.status == "registered":
        return jsonify({"error": {"code": "CONFLICT", "message": "A registered student cannot be marked as a missed registration.", "fields": {}}}), 409
    if registration and registration.status == "missed":
        return jsonify({"error": {"code": "CONFLICT", "message": "This missed registration has already been recorded.", "fields": {}}}), 409
    if registration is None:
        registration = DriveRegistration(profile_id=profile_id, job_role_id=job_role_id)
        db.session.add(registration)
    registration.status = "missed"
    registration.marked_at = datetime.now(timezone.utc)
    profile.missed_drive_blocks = max(profile.missed_drive_blocks, 0) + 2
    db.session.commit()
    return jsonify({"registration": registration.to_dict(), "missed_drive_blocks": profile.missed_drive_blocks}), 200


@placement_bp.route("/drives/<int:job_role_id>/close", methods=["POST"])
@jwt_required
@role_required("placement_officer")
def close_drive(job_role_id):
    """Close a drive and consume one missed-drive block for affected students."""
    role = db.session.get(JobRole, job_role_id)
    if role is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Drive not found", "fields": {}}}), 404
    role.is_active = False
    blocked_profiles = StudentProfile.query.filter(StudentProfile.missed_drive_blocks > 0).all()
    for profile in blocked_profiles:
        profile.missed_drive_blocks -= 1
    db.session.commit()
    return jsonify({"message": "Drive closed", "students_unblocked_for_next_drive": len(blocked_profiles)}), 200


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
