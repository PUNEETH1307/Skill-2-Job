"""Authentication and authorization decorators for Flask routes.

Provides ``@jwt_required`` and ``@role_required(role)`` decorators that
integrate with :class:`~app.services.auth_service.AuthModule` to enforce
JWT authentication and role-based access control on API endpoints.
"""

import functools

from flask import request, g, jsonify

from app.services.auth_service import AuthModule


def jwt_required(fn):
    """Decorator that enforces JWT authentication on a route.

    Extracts the Bearer token from the ``Authorization`` header, validates it
    via :meth:`AuthModule.validate_token`, and attaches the decoded user info
    to ``flask.g.current_user``.  The raw token string is stored on
    ``flask.g.jwt_token`` so that downstream decorators (e.g.
    ``@role_required``) can pass it to :meth:`AuthModule.check_permission`.

    Returns a ``401`` JSON error when the token is missing, malformed, expired,
    or otherwise invalid.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "AUTHENTICATION_ERROR",
                            "message": "Missing or invalid Authorization header",
                        }
                    }
                ),
                401,
            )

        token = auth_header[len("Bearer "):]

        try:
            auth_module = AuthModule()
            user_info = auth_module.validate_token(token)
        except ValueError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "AUTHENTICATION_ERROR",
                            "message": str(exc),
                        }
                    }
                ),
                401,
            )

        g.current_user = {
            "user_id": user_info["user_id"],
            "role": user_info["role"],
        }
        g.jwt_token = token

        return fn(*args, **kwargs)

    return wrapper


def role_required(role):
    """Decorator factory that enforces a minimum role on a route.

    Must be applied **after** ``@jwt_required`` so that ``g.current_user``
    and ``g.jwt_token`` are already populated.

    Usage::

        @app.route("/admin/users")
        @jwt_required
        @role_required("admin")
        def admin_users():
            ...

    Returns a ``403`` JSON error when the authenticated user does not have
    sufficient permissions.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                auth_module = AuthModule()
                has_permission = auth_module.check_permission(g.jwt_token, role)
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "AUTHORIZATION_ERROR",
                                "message": "Insufficient permissions",
                            }
                        }
                    ),
                    403,
                )

            if not has_permission:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "AUTHORIZATION_ERROR",
                                "message": "Insufficient permissions",
                            }
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
