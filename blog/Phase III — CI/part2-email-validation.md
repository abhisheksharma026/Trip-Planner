# Building a Production-Grade AI Agent from Scratch - Phase III Part 2: Email Validation

This update makes email handling consistent across API validation and auth internals.

## What changed

- Request models in `app.py` (`LoginRequest`, `RegisterRequest`) now enforce:
  - valid email pattern
  - `min_length=3`, `max_length=254`
- `trip_planner/core/auth.py` now uses `normalize_email()` as the single path for email normalization and validation.
- `normalize_email()` trims whitespace, validates local/domain rules, and stores values in lowercase.
- Auth paths (`register_user`, `login_user`, `verify_user`, `get_user_by_email`, `create_user`) now use normalized email consistently.

## Why this matters

It prevents duplicate accounts caused by casing or whitespace differences and keeps login behavior predictable.

Example:
- input: `"  USER@Example.COM "`
- stored/queried as: `"user@example.com"`

## Tests

- `tests/test_auth_security.py`: invalid email rejection and duplicate protection
- `tests/test_auth_password.py`: normalization and edge-case validation coverage

## Files touched

- `app.py`
- `trip_planner/core/auth.py`
- `tests/test_auth_security.py`
- `tests/test_auth_password.py`
