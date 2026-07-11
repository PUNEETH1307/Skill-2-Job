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
    """Invalidate the current session token."""
    from flask import g
    auth = AuthModule()
    auth.logout(g.jwt_token)
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/setup", methods=["POST"])
def setup_first_admin():
    """Create the first admin account when no admin exists yet.

    This endpoint is only active when there are zero admin users in the DB.
    Once an admin exists, this endpoint returns 403.

    Accepts JSON: name, email, password, phone (optional), role (optional,
    defaults to 'admin').
    """
    from app import db
    from app.models import User

    # Only allow if no admin exists yet
    existing_admin = User.query.filter_by(role="admin").first()
    if existing_admin:
        return jsonify({
            "error": {
                "code": "FORBIDDEN",
                "message": "Setup already completed. Use admin panel to create users.",
                "fields": {},
            }
        }), 403

    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    role = json_data.get("role", "admin")
    if role not in ("admin", "placement_officer"):
        role = "admin"

    try:
        auth = AuthModule()
        result = auth.register(
            name=json_data.get("name", ""),
            email=json_data.get("email", ""),
            phone=json_data.get("phone") or "",
            password=json_data.get("password", ""),
            role=role,
        )
        return jsonify({**result, "role": role}), 201
    except ValueError as exc:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc), "fields": {}}}), 400


@auth_bp.route("/admin-reset-password", methods=["POST"])
@jwt_required
def admin_reset_password():
    """Allow admin to reset any user's password directly.

    Accepts JSON: user_id (int) OR email (str), new_password (str).
    Requires admin role.
    """
    from flask import g
    from app import db
    from app.models import User
    import bcrypt

    if g.current_user.get("role") != "admin":
        return jsonify({"error": {"code": "AUTHORIZATION_ERROR", "message": "Admin access required"}}), 403

    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON"}}), 400

    new_password = json_data.get("new_password", "")
    if len(new_password) < 6:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Password must be at least 6 characters"}}), 400

    # Find user by id or email
    user = None
    if json_data.get("user_id"):
        user = db.session.get(User, json_data["user_id"])
    elif json_data.get("email"):
        user = User.query.filter_by(email=json_data["email"]).first()

    if user is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    user.password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    db.session.commit()
    return jsonify({"message": f"Password updated for {user.email}", "user": user.to_dict()}), 200
@jwt_required
def update_user_role():
    """Update a user's role. Requires admin privileges.

    Accepts JSON: user_id (int), role ('student'|'placement_officer'|'admin').
    """
    from flask import g
    from app import db
    from app.models import User

    if g.current_user.get("role") != "admin":
        return jsonify({"error": {"code": "AUTHORIZATION_ERROR", "message": "Admin access required", "fields": {}}}), 403

    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON", "fields": {}}}), 400

    user_id = json_data.get("user_id")
    new_role = json_data.get("role", "")

    if not user_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "user_id is required", "fields": {}}}), 400
    if new_role not in ("student", "placement_officer", "admin"):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "role must be student, placement_officer, or admin", "fields": {}}}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found", "fields": {}}}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({"message": f"Role updated to {new_role}", "user": user.to_dict()}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required
def change_password():
    """Change the authenticated user's password.

    Accepts JSON body with current_password and new_password.
    Verifies the current password before updating.
    """
    from flask import g
    import bcrypt
    from app import db
    from app.models import User

    json_data = request.get_json(silent=True)
    if not json_data:
        return (
            jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Request body must be valid JSON"}}),
            400,
        )

    current_password = json_data.get("current_password", "")
    new_password = json_data.get("new_password", "")

    if not current_password or not new_password:
        return (
            jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Both current and new password are required"}}),
            400,
        )

    if len(new_password) < 8:
        return (
            jsonify({"error": {"code": "VALIDATION_ERROR", "message": "New password must be at least 8 characters"}}),
            400,
        )

    user_id = g.current_user["user_id"]
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    # Verify current password
    if not bcrypt.checkpw(current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return (
            jsonify({"error": {"code": "AUTHENTICATION_ERROR", "message": "Current password is incorrect"}}),
            401,
        )

    # Update password
    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200
