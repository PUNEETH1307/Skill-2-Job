"""Dashboard API routes for the Skill2Job Placement System.

Provides role-specific dashboard summary endpoints that aggregate
data for Student, Coordinator (placement_officer), and Admin dashboards.

Each endpoint delegates to DashboardService and is protected by
JWT authentication and role-based authorization.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

from flask import Blueprint, g, jsonify

from app.services.dashboard_service import DashboardService
from app.utils.auth_decorator import jwt_required, role_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/student", methods=["GET"])
@jwt_required
@role_required("student")
def get_student_dashboard():
    """Get student dashboard summary data.

    Returns aggregated student data including profile completeness,
    skill count, skill breakdown, matched job count, and top
    recommendations.

    Returns:
        200: JSON with student dashboard summary.
        401: Missing or invalid JWT token.
        403: User does not have the student role.
        500: Unexpected server error.

    Requirements: 9.1
    """
    try:
        user_id = g.current_user["user_id"]
        service = DashboardService()
        summary = service.get_student_summary(user_id)
        return jsonify(summary), 200
    except Exception:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    }
                }
            ),
            500,
        )


@dashboard_bp.route("/coordinator", methods=["GET"])
@jwt_required
@role_required("placement_officer")
def get_coordinator_dashboard():
    """Get coordinator/placement officer dashboard summary data.

    Returns aggregated placement data including placement overview,
    active job count, shortlisted count, recent shortlists, and
    top skills demand.

    Returns:
        200: JSON with coordinator dashboard summary.
        401: Missing or invalid JWT token.
        403: User does not have the placement_officer role.
        500: Unexpected server error.

    Requirements: 9.2
    """
    try:
        service = DashboardService()
        summary = service.get_coordinator_summary()
        return jsonify(summary), 200
    except Exception:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    }
                }
            ),
            500,
        )


@dashboard_bp.route("/admin", methods=["GET"])
@jwt_required
@role_required("admin")
def get_admin_dashboard():
    """Get admin dashboard summary data.

    Returns aggregated system data including user counts by role
    and status, taxonomy health metrics, and placement overview.

    Returns:
        200: JSON with admin dashboard summary.
        401: Missing or invalid JWT token.
        403: User does not have the admin role.
        500: Unexpected server error.

    Requirements: 9.3
    """
    try:
        service = DashboardService()
        summary = service.get_admin_summary()
        return jsonify(summary), 200
    except Exception:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    }
                }
            ),
            500,
        )


@dashboard_bp.route("/student/prediction", methods=["GET"])
@jwt_required
@role_required("student")
def get_student_prediction():
    """Get placement success prediction for the authenticated student.

    Uses Random Forest model (or heuristic fallback) to predict
    placement probability based on profile features.

    Returns:
        200: JSON with probability, confidence, and contributing factors.
    """
    from app.services.placement_predictor import get_predictor

    user_id = g.current_user["user_id"]
    predictor = get_predictor()
    result = predictor.predict(user_id)
    return jsonify(result), 200
