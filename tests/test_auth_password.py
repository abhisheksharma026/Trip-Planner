"""Unit tests for password hashing, verification, and auth functions in auth.py."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import trip_planner.core.auth as auth


# =============================================================================
# hash_password / verify_password
# =============================================================================

class TestPasswordHashing:
    def test_hash_returns_salt_colon_hash_format(self):
        result = auth.hash_password("test_password")
        assert ":" in result
        salt, hashed = result.split(":")
        assert len(salt) == 32  # 16 bytes as hex
        assert len(hashed) == 64  # SHA-256 as hex

    def test_different_calls_produce_different_salts(self):
        h1 = auth.hash_password("same_password")
        h2 = auth.hash_password("same_password")
        salt1 = h1.split(":")[0]
        salt2 = h2.split(":")[0]
        assert salt1 != salt2

    def test_verify_correct_password(self):
        stored = auth.hash_password("my_secret")
        assert auth.verify_password("my_secret", stored) is True

    def test_verify_wrong_password(self):
        stored = auth.hash_password("my_secret")
        assert auth.verify_password("wrong_password", stored) is False

    def test_verify_malformed_hash_no_colon(self):
        assert auth.verify_password("anything", "nocolonhere") is False

    def test_verify_none_stored_hash(self):
        assert auth.verify_password("anything", None) is False

    def test_verify_empty_stored_hash(self):
        assert auth.verify_password("anything", "") is False

    def test_verify_empty_password_against_valid_hash(self):
        stored = auth.hash_password("real_password")
        assert auth.verify_password("", stored) is False


# =============================================================================
# normalize_email
# =============================================================================

class TestNormalizeEmail:
    def test_valid_email_lowercased(self):
        assert auth.normalize_email("User@Example.COM") == "user@example.com"

    def test_strips_whitespace(self):
        assert auth.normalize_email("  user@example.com  ") == "user@example.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(ValueError):
            auth.normalize_email("not-an-email")

    def test_email_too_long(self):
        long_email = "a" * 250 + "@b.com"
        with pytest.raises(ValueError):
            auth.normalize_email(long_email)

    def test_local_part_too_long(self):
        long_local = "a" * 65 + "@example.com"
        with pytest.raises(ValueError):
            auth.normalize_email(long_local)

    def test_local_part_starts_with_dot(self):
        with pytest.raises(ValueError):
            auth.normalize_email(".user@example.com")

    def test_local_part_ends_with_dot(self):
        with pytest.raises(ValueError):
            auth.normalize_email("user.@example.com")

    def test_double_dots_in_local_part(self):
        with pytest.raises(ValueError):
            auth.normalize_email("us..er@example.com")

    def test_domain_starts_with_hyphen(self):
        with pytest.raises(ValueError):
            auth.normalize_email("user@-example.com")

    def test_domain_ends_with_hyphen(self):
        with pytest.raises(ValueError):
            auth.normalize_email("user@-example.com")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            auth.normalize_email("")


# =============================================================================
# register_user
# =============================================================================

class TestRegisterUser:
    def test_password_too_short(self, temp_auth_db):
        user, error = auth.register_user("user@example.com", "short")
        assert user is None
        assert "at least 6" in error

    def test_password_too_long(self, temp_auth_db):
        user, error = auth.register_user("user@example.com", "x" * 129)
        assert user is None
        assert "no more than 128" in error

    def test_invalid_email(self, temp_auth_db):
        user, error = auth.register_user("bad-email", "validpass123")
        assert user is None
        assert error is not None

    def test_successful_registration(self, temp_auth_db):
        user, error = auth.register_user("newuser@example.com", "validpass123", "Test User")
        assert error is None
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.name == "Test User"

    def test_duplicate_email(self, temp_auth_db):
        auth.register_user("dup@example.com", "validpass123")
        user, error = auth.register_user("dup@example.com", "anotherpass123")
        assert user is None
        assert "already exists" in error


# =============================================================================
# login_user
# =============================================================================

class TestLoginUser:
    def test_valid_credentials(self, temp_auth_db):
        auth.register_user("login@example.com", "correct_password", "Login User")
        user, error = auth.login_user("login@example.com", "correct_password")
        assert error is None
        assert user is not None
        assert user.email == "login@example.com"

    def test_wrong_password(self, temp_auth_db):
        auth.register_user("login2@example.com", "correct_password")
        user, error = auth.login_user("login2@example.com", "wrong_password")
        assert user is None
        assert error == "Invalid email or password"

    def test_nonexistent_email(self, temp_auth_db):
        user, error = auth.login_user("nobody@example.com", "any_password")
        assert user is None
        assert error == "Invalid email or password"

    def test_invalid_email_format(self, temp_auth_db):
        user, error = auth.login_user("not-an-email", "any_password")
        assert user is None
        assert error is not None


# =============================================================================
# get_current_user / session functions
# =============================================================================

class TestSessionFunctions:
    def test_get_current_user_with_valid_session(self):
        request = MagicMock()
        request.session = {
            "user": {
                "id": "user123",
                "email": "test@example.com",
                "name": "Test",
                "created_at": "2025-01-01",
            }
        }
        user = auth.get_current_user(request)
        assert user is not None
        assert user.id == "user123"
        assert user.email == "test@example.com"

    def test_get_current_user_no_session(self):
        request = MagicMock()
        request.session = {}
        user = auth.get_current_user(request)
        assert user is None

    def test_get_current_user_malformed_session(self):
        request = MagicMock()
        request.session = {"user": "not-a-dict"}
        user = auth.get_current_user(request)
        assert user is None

    def test_set_and_get_session_user(self):
        request = MagicMock()
        request.session = {}
        user = auth.User(id="u1", email="u@example.com", name="U", created_at="2025-01-01")
        auth.set_session_user(request, user)
        assert request.session["user"]["id"] == "u1"

    def test_logout_clears_session(self):
        request = MagicMock()
        request.session = {"user": {"id": "u1"}, "other": "data"}
        auth.logout_user(request)
        assert request.session == {}

    def test_require_user_raises_when_not_authenticated(self):
        from fastapi import HTTPException

        request = MagicMock()
        request.session = {}
        with pytest.raises(HTTPException) as exc_info:
            auth.require_user(request)
        assert exc_info.value.status_code == 401
