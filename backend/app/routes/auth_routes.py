"""Authentication API routes for the Skill2Job Placement System.

Provides endpoints for user registration, login, and logout.
"""

from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate

from app.services.auth_service import AuthModule
from app.utils.auth_decorator import jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ---------------------------------------------------------------------------
# Request validation schemas
# ---------------------------------------------------------------------------


class RegisterSchema(Schema):
    """Validates registration request payloads."""

    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(load_default=None)
    password = fields.String(required=True)


class LoginSchema(Schema):
    """Validates login request payloads."""

    email = fields.String(required=True)
    password = fields.String(required=True)


class ForgotPasswordSchema(Schema):
    """Validates password reset request payloads."""

    email = fields.String(required=True)


class ResetPasswordSchema(Schema):
    """Validates the reset password payload."""

    token = fields.String(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))


# Schema instances (reused across requests)
_register_schema = RegisterSchema()
_login_schema = LoginSchema()
_forgot_schema = ForgotPasswordSchema()
_reset_password_schema = ResetPasswordSchema()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new student account.

    Accepts JSON body with name, email, phone (optional), and password.
    Returns 201 on success or an appropriate error response.
    """
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

    # Validate with marshmallow
    errors = _register_schema.validate(json_data)
    if errors:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input data",
                        "fields": errors,
                    }
                }
            ),
            400,
        )

    data = _register_schema.load(json_data)

    try:
        auth = AuthModule()
        result = auth.register(
            name=data["name"],
            email=data["email"],
            phone=data.get("phone") or "",
            password=data["password"],
        )
        return jsonify(result), 201

    except ValueError as exc:
        error_message = str(exc)

        # Duplicate email → 409 Conflict
        if "already registered" in error_message.lower():
            return (
                jsonify(
                    {
                        "error": {
                            "code": "CONFLICT",
                            "message": error_message,
                            "fields": {"email": error_message},
                        }
                    }
                ),
                409,
            )

        # Validation errors → 400
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": error_message,
                        "fields": {},
                    }
                }
            ),
            400,
        )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT token.

    Accepts JSON body with email and password.
    Returns 200 with token on success or a generic 401 error.
    """
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

    errors = _login_schema.validate(json_data)
    if errors:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input data",
                        "fields": errors,
                    }
                }
            ),
            400,
        )

    data = _login_schema.load(json_data)

    try:
        auth = AuthModule()
        result = auth.login(email=data["email"], password=data["password"])
        return jsonify(result), 200

    except ValueError:
        # Always return generic message — never reveal whether email or password was wrong
        return (
            jsonify(
                {
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Invalid credentials",
                        "fields": {},
                    }
                }
            ),
            401,
        )


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Issue a password reset request for the given email."""
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

    errors = _forgot_schema.validate(json_data)
    if errors:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input data",
                        "fields": errors,
                    }
                }
            ),
            400,
        )

    data = _forgot_schema.load(json_data)
    try:
        auth = AuthModule()
        result = auth.request_password_reset(email=data["email"])
        return jsonify(result), 200
    except ValueError as exc:
        return (
            jsonify(
                {
                    "message": "If an account with that email exists, a password reset link will be sent.",
                }
            ),
            200,
        )


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset the user's password using a reset token."""
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

    errors = _reset_password_schema.validate(json_data)
    if errors:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input data",
                        "fields": errors,
                    }
                }
            ),
            400,
        )

    data = _reset_password_schema.load(json_data)
    try:
        auth = AuthModule()
        result = auth.reset_password(token=data["token"], password=data["password"])
        return jsonify(result), 200
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                        "fields": {},
                    }
                }
            ),
            400,
        )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    """Invalidate the current session token.

    Requires a valid JWT in the Authorization header.
    Returns 200 on success.
    """
    from flask import g

    auth = AuthModule()
    auth.logout(g.jwt_token)
    return jsonify({"message": "Logged out successfully"}), 200
