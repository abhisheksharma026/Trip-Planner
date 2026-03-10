# Building a Production-Grade AI Agent from Scratch - Phase III Part 5: Redis-Backed Rate Limiting

Rate limiting now supports shared counters across instances, with safe fallback to memory.

## What changed

- Added backend-aware rate-limit config in `trip_planner/config.py`:
  - `RATE_LIMIT_BACKEND` (`memory` or `redis`)
  - `RATE_LIMIT_REDIS_URL`
  - `RATE_LIMIT_KEY_PREFIX`
  - `USER_DAILY_RATE_LIMIT`
- Added `trip_planner/core/redis_client.py` to initialize Redis once and gracefully fall back when unavailable.
- `trip_planner/core/rate_limiter.py` now supports Redis-backed global and anonymous counters (with daily TTL behavior).
- `trip_planner/core/auth.py` now supports Redis-backed per-user daily counters.
- `/api/query` in `app.py` now enforces authenticated user daily quota and returns `X-User-RateLimit-Remaining`.
- Added auth endpoint throttles:
  - `/api/register`: `3/minute`
  - `/api/login`: `5/minute`
- Added dependency: `redis>=5.0.0`.

## Why this matters

With Redis enabled, limits are consistent across multiple app processes. If Redis is down, the app still works with in-memory fallback.

## Files touched

- `trip_planner/config.py`
- `trip_planner/core/redis_client.py`
- `trip_planner/core/rate_limiter.py`
- `trip_planner/core/auth.py`
- `app.py`
- `requirements.txt`
- `pyproject.toml`
