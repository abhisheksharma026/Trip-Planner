# Building a Production-Grade AI Agent from Scratch - Phase III Part 1: HTTPS-Only Cookies

We tightened session cookie security so production defaults are safe, not just convenient.

## What changed

- Cookie behavior is now centralized in `trip_planner/config.py` via `get_session_settings()`.
- `SESSION_HTTPS_ONLY` defaults to `True`.
- Insecure cookies are allowed only for explicit localhost development, and only when all checks pass:
  - `ALLOW_INSECURE_LOCAL_DEV=True`
  - `APP_ENVIRONMENT="development"`
  - `LOCAL_DEV_BASE_URL` points to `http://localhost` (or `127.0.0.1` / `::1`)
- `SessionMiddleware` in `trip_planner/core/auth.py` now reads these settings instead of hardcoded values.

## Why this matters

Before this, it was easier to accidentally ship insecure cookie settings. Now the default is secure, and local HTTP is still possible when intentionally enabled.

## Tests

`tests/test_auth_security.py` verifies:
- secure cookie behavior in production
- local insecure override works only for localhost
- override is rejected for non-localhost HTTP URLs

## Files touched

- `trip_planner/config.py`
- `trip_planner/core/auth.py`
- `tests/test_auth_security.py`
