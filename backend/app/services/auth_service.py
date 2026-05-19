"""Authentication service for the Skill2Job Placement System.

Provides user registration, login, logout, token validation, and
role-based permission checking.
"""

import hashlib
import secrets
import re
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from flask import current_app

from app import db
from app.models import PasswordResetToken, User

# Module-level token blacklist (in-memory set for simplicity)
_token_blacklist: set[str] = set()

# Email validation regex
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Role hierarchy: higher index = more privilege
_ROLE_HIERARCHY = {
    "student": 0,
    "placement_officer": 1,
    "admin": 2,
}


class AuthModule:
    """Handles registration, authentication, session management, and RBAC."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, email: str, phone: str, password: str,
                 role: str = "student") -> dict:
        """Register a new user account.

        Args:
            name: Full name of the user.
            email: Email address (must be unique).
            phone: Phone number.
            password: Plain-text password (>= 8 characters).
            role: Account role — 'student', 'placement_officer', or 'admin'.
                  Defaults to 'student'. Only 'student' is allowed from the
                  public register endpoint; other roles require admin creation.

        Returns:
            dict with ``user_id`` and confirmation ``message``.

        Raises:
            ValueError: On validation failure or duplicate email.
        """
        # --- input validation ---
        missing: list[str] = []
        if not name or not name.strip():
            missing.append("name")
        if not email or not email.strip():
            missing.append("email")
        if not password:
            missing.append("password")
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if not _EMAIL_REGEX.match(email):
            raise ValueError("Invalid email format")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if role not in _ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {role}")

        # --- duplicate check ---
        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ValueError("Email is already registered")

        # --- hash password with bcrypt (unique salt) ---
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # --- create user record ---
        user = User(
            name=name.strip(),
            email=email.strip(),
            phone=phone,
            password_hash=password_hash,
            role=role,
            status="active",
        )
        db.session.add(user)
        db.session.commit()

        return {"user_id": user.id, "message": "Registration successful"}

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> dict:
        """Authenticate a user and issue a JWT token.

        Args:
            email: Registered email address.
            password: Plain-text password to verify.

        Returns:
            dict with ``token`` and ``user`` info (id, name, email, role).

        Raises:
            ValueError: On invalid credentials or inactive account.
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Invalid credentials")

        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise ValueError("Invalid credentials")

        if user.status != "active":
            raise ValueError("Account is inactive")

        # --- generate JWT ---
        expiry_minutes = current_app.config.get("JWT_TOKEN_EXPIRY_MINUTES", 30)
        payload = {
            "user_id": user.id,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
        }
        secret = current_app.config["JWT_SECRET_KEY"]
        token = jwt.encode(payload, secret, algorithm="HS256")

        return {
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
        }

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------

    def request_password_reset(self, email: str) -> dict:
        """Create a password reset token for a user.

        Args:
            email: Registered email address.

        Returns:
            dict containing a reset token and message. In production,
            this token should be emailed to the user rather than returned.

        Raises:
            ValueError: If no user exists with the given email.
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("If that email exists, a reset link will be sent")

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expiry,
            used=False,
        )
        db.session.add(reset_token)
        db.session.commit()

        # In a real deployment the token would be delivered via email.
        # Send password reset email
        from app.services.email_service import get_email_service
        email_svc = get_email_service()
        email_svc.send_password_reset(email, raw_token, user.name)

        return {
            "message": "Password reset token created. Please check your email.",
            "reset_token": raw_token,
        }

    def reset_password(self, token: str, password: str) -> dict:
        """Reset the user's password using a valid reset token.

        Args:
            token: Password reset token previously issued.
            password: New plain-text password.

        Returns:
            dict with confirmation message.

        Raises:
            ValueError: If the token is invalid, expired, used, or password invalid.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        reset_record = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        if reset_record is None:
            raise ValueError("Invalid password reset token")
        if reset_record.used:
            raise ValueError("Password reset token has already been used")
        expires_at = reset_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise ValueError("Password reset token has expired")

        user = db.session.get(User, reset_record.user_id)
        if user is None:
            raise ValueError("User not found")

        user.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        reset_record.used = True
        db.session.add(user)
        db.session.add(reset_record)
        db.session.commit()

        return {"message": "Password has been reset successfully"}

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self, token: str) -> bool:
        """Invalidate a session token by adding it to the blacklist.

        Args:
            token: JWT token string to invalidate.

        Returns:
            True on success.
        """
        _token_blacklist.add(token)
        return True

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    def validate_token(self, token: str) -> dict:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string.

        Returns:
            dict with ``user_id`` and ``role``.

        Raises:
            ValueError: On expired, blacklisted, or invalid token.
        """
        if token in _token_blacklist:
            raise ValueError("Token has been invalidated")

        secret = current_app.config["JWT_SECRET_KEY"]
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

        return {
            "user_id": payload["user_id"],
            "role": payload["role"],
        }

    # ------------------------------------------------------------------
    # Permission checking
    # ------------------------------------------------------------------

    def check_permission(self, token: str, required_role: str) -> bool:
        """Check whether the token holder has the required role or higher.

        The role hierarchy is: admin > placement_officer > student.

        Args:
            token: JWT token string.
            required_role: Minimum role needed (e.g. ``"placement_officer"``).

        Returns:
            True if the user's role meets or exceeds the required role.

        Raises:
            ValueError: If the token is invalid or the role is unrecognised.
        """
        user_info = self.validate_token(token)
        user_role = user_info["role"]

        if user_role not in _ROLE_HIERARCHY:
            raise ValueError(f"Unknown user role: {user_role}")
        if required_role not in _ROLE_HIERARCHY:
            raise ValueError(f"Unknown required role: {required_role}")

        return _ROLE_HIERARCHY[user_role] >= _ROLE_HIERARCHY[required_role]
