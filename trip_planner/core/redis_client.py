"""
Shared Redis client helper with graceful fallback.
"""

from __future__ import annotations

from typing import Optional

from trip_planner.logging_utils import get_logger

logger = get_logger(__name__)

try:
    import redis
except ImportError:  # pragma: no cover - depends on optional package
    redis = None


_cached_url: Optional[str] = None
_cached_client = None


def get_redis_client(redis_url: str):
    """
    Get a reusable Redis client or None if unavailable.

    Uses a simple module cache to avoid repeated connection setup.
    """
    global _cached_url, _cached_client

    if not redis_url:
        return None

    if redis is None:
        logger.warning("Redis package is not installed; falling back to in-memory storage.")
        return None

    if _cached_client is not None and _cached_url == redis_url:
        return _cached_client

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        _cached_url = redis_url
        _cached_client = client
        logger.info("Connected to Redis backend for rate limiting.")
        return client
    except Exception as exc:  # pragma: no cover - runtime connectivity
        logger.warning("Redis unavailable (%s); falling back to in-memory storage.", exc)
        _cached_url = None
        _cached_client = None
        return None

