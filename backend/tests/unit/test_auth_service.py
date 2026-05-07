"""Unit tests for the AuthModule service.

Covers registration, login, logout, token validation, and permission checking.
"""

import time

import jwt
import pytest

from app.services.auth_service import AuthModule, _token_blacklist


@pytest.fixture(autouse=True)
def clear_blacklist():
    """Ensure the token blacklist is empty before each test."""
    _token_blacklist.clear()
    yield
    _token_blacklist.clear()


@pytest.fixture()
def auth(app):
    """Provide an AuthModule instance inside an app context."""
    with app.app_context():
        yield AuthModule()


# -----------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------

def _register_user(auth_module, db_session, **overrides):
    """Register a default user and return the result dict."""
    defaults = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "password": "securepass123",
    }
    defaults.update(overrides)
    return auth_module.register(**defaults)


# -----------------------------------------------------------------------
# Registration tests
# -----------------------------------------------------------------------

class TestRegister:
    def test_successful_registration(self, auth, db_session):
        result = _register_user(auth, db_session)
        assert "user_id" in result
        assert result["message"] == "Registration successful"
        assert isinstance(result["user_id"], int)

    def test_duplicate_email_rejected(self, auth, db_session):
        _register_user(auth, db_session)
        with pytest.raises(ValueError, match="Email is already registered"):
            _register_user(auth, db_session)

    def test_invalid_email_format(self, auth, db_session):
        with pytest.raises(ValueError, match="Invalid email format"):
            _register_user(auth, db_session, email="not-an-email")

    def test_short_password(self, auth, db_session):
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            _register_user(auth, db_session, password="short")

    def test_missing_name(self, auth, db_session):
        with pytest.raises(ValueError, match="Missing required fields.*name"):
            _register_user(auth, db_session, name="")

    def test_missing_email(self, auth, db_session):
        with pytest.raises(ValueError, match="Missing required fields.*email"):
            _register_user(auth, db_session, email="")

    def test_missing_password(self, auth, db_session):
        with pytest.raises(ValueError, match="Missing required fields.*password"):
            _register_user(auth, db_session, password="")


# -----------------------------------------------------------------------
# Login tests
# -----------------------------------------------------------------------

class TestLogin:
    def test_successful_login(self, auth, db_session):
        _register_user(auth, db_session)
        result = auth.login("test@example.com", "securepass123")
        assert "token" in result
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["role"] == "student"
        assert result["user"]["name"] == "Test User"
        assert "id" in result["user"]

    def test_wrong_password(self, auth, db_session):
        _register_user(auth, db_session)
        with pytest.raises(ValueError, match="Invalid credentials"):
            auth.login("test@example.com", "wrongpassword")

    def test_inactive_account(self, auth, db_session):
        from app.models import User

        _register_user(auth, db_session)
        user = User.query.filter_by(email="test@example.com").first()
        user.status = "inactive"
        db_session.commit()

        with pytest.raises(ValueError, match="Account is inactive"):
            auth.login("test@example.com", "securepass123")

    def test_nonexistent_email(self, auth, db_session):
        with pytest.raises(ValueError, match="Invalid credentials"):
            auth.login("nobody@example.com", "somepassword")


# -----------------------------------------------------------------------
# Token validation tests
# -----------------------------------------------------------------------

class TestValidateToken:
    def test_valid_token(self, auth, db_session):
        _register_user(auth, db_session)
        login_result = auth.login("test@example.com", "securepass123")
        token = login_result["token"]

        info = auth.validate_token(token)
        assert info["user_id"] == login_result["user"]["id"]
        assert info["role"] == "student"

    def test_expired_token(self, auth, db_session, app):
        """A token with a past expiry should be rejected."""
        from datetime import datetime, timezone, timedelta

        secret = app.config["JWT_SECRET_KEY"]
        payload = {
            "user_id": 1,
            "role": "student",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(ValueError, match="Token has expired"):
            auth.validate_token(expired_token)

    def test_blacklisted_token(self, auth, db_session):
        _register_user(auth, db_session)
        login_result = auth.login("test@example.com", "securepass123")
        token = login_result["token"]

        auth.logout(token)

        with pytest.raises(ValueError, match="Token has been invalidated"):
            auth.validate_token(token)

    def test_invalid_token_string(self, auth, db_session):
        with pytest.raises(ValueError, match="Invalid token"):
            auth.validate_token("this.is.not.a.valid.jwt")


# -----------------------------------------------------------------------
# Logout tests
# -----------------------------------------------------------------------

class TestLogout:
    def test_logout_adds_to_blacklist(self, auth, db_session):
        _register_user(auth, db_session)
        login_result = auth.login("test@example.com", "securepass123")
        token = login_result["token"]

        result = auth.logout(token)
        assert result is True
        assert token in _token_blacklist


# -----------------------------------------------------------------------
# Permission checking tests
# -----------------------------------------------------------------------

class TestCheckPermission:
    def _make_token(self, app, role):
        """Create a JWT with the given role."""
        from datetime import datetime, timezone, timedelta

        secret = app.config["JWT_SECRET_KEY"]
        payload = {
            "user_id": 1,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    def test_student_can_access_student(self, auth, db_session, app):
        token = self._make_token(app, "student")
        assert auth.check_permission(token, "student") is True

    def test_student_cannot_access_placement_officer(self, auth, db_session, app):
        token = self._make_token(app, "student")
        assert auth.check_permission(token, "placement_officer") is False

    def test_student_cannot_access_admin(self, auth, db_session, app):
        token = self._make_token(app, "student")
        assert auth.check_permission(token, "admin") is False

    def test_placement_officer_can_access_student(self, auth, db_session, app):
        token = self._make_token(app, "placement_officer")
        assert auth.check_permission(token, "student") is True

    def test_placement_officer_can_access_own_role(self, auth, db_session, app):
        token = self._make_token(app, "placement_officer")
        assert auth.check_permission(token, "placement_officer") is True

    def test_placement_officer_cannot_access_admin(self, auth, db_session, app):
        token = self._make_token(app, "placement_officer")
        assert auth.check_permission(token, "admin") is False

    def test_admin_can_access_all_roles(self, auth, db_session, app):
        token = self._make_token(app, "admin")
        assert auth.check_permission(token, "student") is True
        assert auth.check_permission(token, "placement_officer") is True
        assert auth.check_permission(token, "admin") is True
