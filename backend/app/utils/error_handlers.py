"""Global error handlers for the Skill2Job Placement System.

Registers Flask error handlers that return the standard JSON error format
defined in the design document.

Requirements: 14.1, 14.2, 14.3, 14.4
"""

import logging
import traceback
from datetime import datetime, timezone

from flask import jsonify

logger = logging.getLogger(__name__)


def _error_response(code: str, message: str, status: int, fields: dict = None):
    """Build a standard JSON error response.

    Args:
        code: Error code string (e.g. VALIDATION_ERROR).
        message: Human-readable error description.
        status: HTTP status code.
        fields: Optional dict of field-specific errors.

    Returns:
        Tuple of (response, status_code).
    """
    body = {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
        }
    }
    return jsonify(body), status


def register_error_handlers(app):
    """Register global error handlers on the Flask app.

    Args:
        app: The Flask application instance.
    """

    @app.errorhandler(400)
    def bad_request(error):
        message = getattr(error, "description", "Bad request")
        return _error_response("VALIDATION_ERROR", message, 400)

    @app.errorhandler(401)
    def unauthorized(error):
        message = getattr(error, "description", "Authentication required")
        return _error_response("AUTHENTICATION_ERROR", message, 401)

    @app.errorhandler(403)
    def forbidden(error):
        message = getattr(error, "description", "Insufficient permissions")
        return _error_response("AUTHORIZATION_ERROR", message, 403)

    @app.errorhandler(404)
    def not_found(error):
        message = getattr(error, "description", "Resource not found")
        return _error_response("NOT_FOUND", message, 404)

    @app.errorhandler(409)
    def conflict(error):
        message = getattr(error, "description", "Resource conflict")
        return _error_response("CONFLICT", message, 409)

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(
            "Internal server error at %s: %s\n%s",
            datetime.now(timezone.utc).isoformat(),
            str(error),
            traceback.format_exc(),
        )
        return _error_response(
            "PROCESSING_ERROR",
            "An internal error occurred. Please try again later.",
            500,
        )

    @app.errorhandler(503)
    def service_unavailable(error):
        logger.error(
            "Service unavailable at %s: %s",
            datetime.now(timezone.utc).isoformat(),
            str(error),
        )
        return _error_response(
            "SERVICE_UNAVAILABLE",
            "The service is temporarily unavailable. Please try again later.",
            503,
        )
