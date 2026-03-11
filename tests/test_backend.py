"""Backend API tests using FastAPI TestClient.

Tests authentication flows, rate limiting, health, and samples endpoints
without requiring a running server.
"""

import random
import string
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import trip_planner.core.auth as auth
from trip_planner.core.rate_limiter import limiter


def _random_email() -> str:
    slug = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{slug}@example.com"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_auth_db(tmp_path: Path):
    """Point the auth module at a throwaway SQLite DB for every test."""
    auth.DATABASE_PATH = str(tmp_path / "test_auth.db")
    auth.init_db()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear slowapi rate limiter state between tests."""
    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.fixture()
def client():
    """Provide a TestClient that skips real component initialization.

    Uses https base URL so that Secure session cookies round-trip correctly
    (the session middleware sets https_only=True by default).
    """
    with patch("app.initialize_components", return_value=False):
        from app import app
        with TestClient(app, base_url="https://testserver") as c:
            yield c


@pytest.fixture()
def mock_runner():
    """Patch app.runner with a mock that returns a canned response."""
    runner = AsyncMock()
    session_mock = MagicMock()
    session_mock.id = "test-session-id"
    runner.run_query.return_value = ("Here is your trip plan!", session_mock)
    with patch("app.runner", runner):
        yield runner


def _register(client: TestClient, email: str, password: str = "validpass123", name: str = "Test User"):
    return client.post("/api/register", json={"email": email, "password": password, "name": name})


def _login(client: TestClient, email: str, password: str = "validpass123"):
    return client.post("/api/login", json={"email": email, "password": password})


# =============================================================================
# Health & informational endpoints
# =============================================================================

class TestHealthAndInfo:
    def test_health_returns_status(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "initialized" in data

    def test_samples_returns_list(self, client):
        resp = client.get("/api/samples")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["samples"], list)
        assert len(data["samples"]) > 0

    def test_rate_limit_status_returns_keys(self, client):
        resp = client.get("/api/rate-limit-status")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("count", "limit", "remaining", "reset_date"):
            assert key in data


# =============================================================================
# Authentication flow
# =============================================================================

class TestAuthFlow:
    def test_user_not_authenticated_initially(self, client):
        resp = client.get("/api/user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False
        assert data["user"] is None

    def test_register_new_user(self, client):
        email = _random_email()
        resp = _register(client, email)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["email"] == email.lower()

    def test_register_sets_session(self, client):
        """After registration the session cookie should authenticate the user."""
        email = _random_email()
        _register(client, email)
        resp = client.get("/api/user")
        data = resp.json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == email.lower()

    def test_register_duplicate_email_rejected(self, client):
        email = _random_email()
        _register(client, email)
        resp = _register(client, email, password="anotherpass123")
        data = resp.json()
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_login_valid_credentials(self, client):
        email = _random_email()
        _register(client, email, password="correct_password")
        # Logout first so we can test login in isolation
        client.post("/api/logout")
        resp = _login(client, email, password="correct_password")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["email"] == email.lower()

    def test_login_wrong_password(self, client):
        email = _random_email()
        _register(client, email)
        client.post("/api/logout")
        resp = _login(client, email, password="wrong_password")
        data = resp.json()
        assert data["success"] is False
        assert data["error"] is not None

    def test_login_nonexistent_user(self, client):
        resp = _login(client, "nobody@example.com")
        data = resp.json()
        assert data["success"] is False

    def test_logout_clears_session(self, client):
        email = _random_email()
        _register(client, email)
        resp = client.post("/api/logout")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Verify session is cleared
        user_resp = client.get("/api/user")
        assert user_resp.json()["authenticated"] is False


# =============================================================================
# Query endpoint
# =============================================================================

class TestQueryEndpoint:
    def test_query_returns_response(self, client, mock_runner):
        email = _random_email()
        _register(client, email)
        resp = client.post("/api/query", json={
            "query": "Plan a trip to Paris",
            "user_id": "test_user",
            "new_session": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "trip plan" in data["response"].lower()

    def test_query_returns_503_when_runner_not_initialized(self, client):
        """When runner is None the endpoint should return 503."""
        email = _random_email()
        _register(client, email)
        with patch("app.runner", None):
            resp = client.post("/api/query", json={
                "query": "Plan a trip",
                "user_id": "test_user",
                "new_session": True,
            })
        assert resp.status_code == 503

    def test_query_empty_string_rejected(self, client, mock_runner):
        email = _random_email()
        _register(client, email)
        resp = client.post("/api/query", json={
            "query": "   ",
            "user_id": "test_user",
            "new_session": True,
        })
        assert resp.status_code == 400

    def test_query_rate_limit_headers_for_authenticated(self, client, mock_runner):
        email = _random_email()
        _register(client, email)
        resp = client.post("/api/query", json={
            "query": "Trip to Tokyo",
            "user_id": "test_user",
            "new_session": True,
        })
        assert resp.headers.get("x-authenticated") == "true"
        assert resp.headers.get("x-anonymous-remaining") == "unlimited"
