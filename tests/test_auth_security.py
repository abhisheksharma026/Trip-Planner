from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import trip_planner.config as config
import trip_planner.core.auth as auth


def _configure_temp_auth_db(tmp_path: Path) -> None:
    auth.DATABASE_PATH = str(tmp_path / "auth_test.db")
    auth.init_db()


def test_register_user_rejects_invalid_email(tmp_path):
    _configure_temp_auth_db(tmp_path)

    user, error = auth.register_user("not-an-email", "testpass123", "Invalid")

    assert user is None
    assert error == "Invalid email address format"


def test_register_user_normalizes_email(tmp_path):
    _configure_temp_auth_db(tmp_path)

    user, error = auth.register_user("  USER@Example.COM ", "testpass123", "User")

    assert error is None
    assert user is not None
    assert user.email == "user@example.com"


def test_register_duplicate_email_after_normalization(tmp_path):
    _configure_temp_auth_db(tmp_path)

    first_user, first_error = auth.register_user("User@Example.com", "testpass123", "User")
    second_user, second_error = auth.register_user("user@example.com", "testpass123", "User2")

    assert first_error is None
    assert first_user is not None
    assert second_user is None
    assert second_error == "An account with this email already exists"


def _cookie_header_for_current_config() -> str:
    async def set_session(request):
        request.session["user"] = {"id": "u1", "email": "user@example.com"}
        return JSONResponse({"success": True})

    app = Starlette(routes=[Route("/set-session", set_session)])
    app.add_middleware(auth.get_session_middleware())

    with TestClient(app) as client:
        response = client.get("/set-session")
    return response.headers.get("set-cookie", "")


def test_cookie_is_secure_by_default_in_production(monkeypatch):
    monkeypatch.setattr(config, "APP_ENVIRONMENT", "production")
    monkeypatch.setattr(config, "SESSION_HTTPS_ONLY", True)
    monkeypatch.setattr(config, "ALLOW_INSECURE_LOCAL_DEV", False)
    monkeypatch.setattr(config, "LOCAL_DEV_BASE_URL", "http://localhost:5000")

    cookie_header = _cookie_header_for_current_config().lower()

    assert "secure" in cookie_header


def test_cookie_not_secure_only_with_local_dev_override(monkeypatch):
    monkeypatch.setattr(config, "APP_ENVIRONMENT", "development")
    monkeypatch.setattr(config, "SESSION_HTTPS_ONLY", True)
    monkeypatch.setattr(config, "ALLOW_INSECURE_LOCAL_DEV", True)
    monkeypatch.setattr(config, "LOCAL_DEV_BASE_URL", "http://localhost:5000")

    cookie_header = _cookie_header_for_current_config().lower()

    assert "secure" not in cookie_header


def test_local_dev_override_does_not_apply_for_non_localhost(monkeypatch):
    monkeypatch.setattr(config, "APP_ENVIRONMENT", "development")
    monkeypatch.setattr(config, "SESSION_HTTPS_ONLY", True)
    monkeypatch.setattr(config, "ALLOW_INSECURE_LOCAL_DEV", True)
    monkeypatch.setattr(config, "LOCAL_DEV_BASE_URL", "http://example.com")

    cookie_header = _cookie_header_for_current_config().lower()

    assert "secure" in cookie_header
