"""
Rate Limiter - Multi-level rate limiting for production safety.

This module supports:
1. Global daily limit - Protects overall API budget
2. Per-IP endpoint limits (SlowAPI)
3. Anonymous usage limits
4. Redis-backed storage with automatic in-memory fallback
"""

import os
import threading
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Tuple

from slowapi import Limiter
from slowapi.util import get_remote_address

from trip_planner.config import get_rate_limit_settings
from trip_planner.core.redis_client import get_redis_client
from trip_planner.logging_utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DAILY_API_LIMIT = int(os.getenv("DAILY_API_LIMIT", "200"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
ANONYMOUS_FREE_LIMIT = int(os.getenv("ANONYMOUS_FREE_LIMIT", "5"))

RATE_LIMIT_SETTINGS = get_rate_limit_settings()
RATE_LIMIT_STORAGE_BACKEND = RATE_LIMIT_SETTINGS["backend"]
_RATE_LIMIT_KEY_PREFIX = RATE_LIMIT_SETTINGS["key_prefix"]
_redis_client = (
    get_redis_client(RATE_LIMIT_SETTINGS["redis_url"])
    if RATE_LIMIT_STORAGE_BACKEND == "redis"
    else None
)

if RATE_LIMIT_STORAGE_BACKEND == "redis" and _redis_client is None:
    logger.warning("Requested Redis backend but unavailable. Falling back to memory.")


def _seconds_until_next_day_utc() -> int:
    """Return seconds until next UTC day boundary."""
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).date()
    midnight = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
    return max(1, int((midnight - now).total_seconds()))


# =============================================================================
# Global Daily Rate Limiter
# =============================================================================

class DailyResetMixin:
    """Mixin for in-memory rate limiters that reset daily."""

    def _needs_reset(self) -> bool:
        return datetime.now().date() > self._reset_date

    def _update_reset_date(self) -> None:
        self._reset_date = datetime.now().date()


class GlobalDailyLimiter(DailyResetMixin):
    """Global daily limiter with optional Redis backing."""

    def __init__(self, daily_limit: int, redis_client=None, key_prefix: str = "trip_planner"):
        self.daily_limit = daily_limit
        self._count = 0
        self._reset_date: date = datetime.now().date()
        self._lock = threading.Lock()
        self._warning_thresholds = [0.5, 0.8, 0.9, 0.95]
        self._warnings_issued: set[int] = set()
        self._redis_client = redis_client
        self._key_prefix = key_prefix

        logger.info(
            "Global daily limiter initialized (limit=%s, backend=%s).",
            daily_limit,
            "redis" if redis_client is not None else "memory",
        )

    def _check_reset(self) -> None:
        if self._needs_reset():
            self._count = 0
            self._update_reset_date()
            self._warnings_issued.clear()
            logger.info("Global daily limiter reset for new day: %s", self._reset_date)

    def _issue_warning_if_needed(self, count: int) -> None:
        for threshold in self._warning_thresholds:
            threshold_key = int(threshold * 100)
            threshold_count = max(1, int(self.daily_limit * threshold))
            if count >= threshold_count and threshold_key not in self._warnings_issued:
                self._warnings_issued.add(threshold_key)
                logger.warning(
                    "Global rate limit usage reached %s%% (%s/%s).",
                    threshold_key,
                    count,
                    self.daily_limit,
                )

    def _redis_key(self, today: date) -> str:
        return f"{self._key_prefix}:global_limit:{today.isoformat()}"

    def _increment_memory(self) -> Tuple[bool, int, int]:
        with self._lock:
            self._check_reset()
            if self._count >= self.daily_limit:
                return False, self._count, 0
            self._count += 1
            remaining = self.daily_limit - self._count
            self._issue_warning_if_needed(self._count)
            return True, self._count, remaining

    def _increment_redis(self) -> Tuple[bool, int, int]:
        today = date.today()
        key = self._redis_key(today)
        try:
            count = int(self._redis_client.incr(key))
            if count == 1:
                self._redis_client.expire(key, _seconds_until_next_day_utc())
            self._issue_warning_if_needed(min(count, self.daily_limit))
            remaining = max(0, self.daily_limit - count)
            return count <= self.daily_limit, count, remaining
        except Exception as exc:  # pragma: no cover - runtime connectivity
            logger.warning("Redis global limiter failed, using memory fallback: %s", exc)
            return self._increment_memory()

    def increment(self) -> Tuple[bool, int, int]:
        if self._redis_client is not None:
            return self._increment_redis()
        return self._increment_memory()

    def _get_memory_status(self) -> Dict:
        with self._lock:
            self._check_reset()
            return {
                "count": self._count,
                "limit": self.daily_limit,
                "remaining": self.daily_limit - self._count,
                "reset_date": self._reset_date.isoformat(),
                "usage_percent": round((self._count / self.daily_limit) * 100, 1),
            }

    def _get_redis_status(self) -> Dict:
        today = date.today()
        key = self._redis_key(today)
        try:
            count = int(self._redis_client.get(key) or 0)
            return {
                "count": count,
                "limit": self.daily_limit,
                "remaining": max(0, self.daily_limit - count),
                "reset_date": today.isoformat(),
                "usage_percent": round((count / self.daily_limit) * 100, 1),
            }
        except Exception as exc:  # pragma: no cover - runtime connectivity
            logger.warning("Redis global status failed, using memory fallback: %s", exc)
            return self._get_memory_status()

    def get_status(self) -> Dict:
        if self._redis_client is not None:
            return self._get_redis_status()
        return self._get_memory_status()

    def reset(self) -> None:
        if self._redis_client is not None:
            key = self._redis_key(date.today())
            try:
                self._redis_client.delete(key)
                self._warnings_issued.clear()
                return
            except Exception as exc:  # pragma: no cover - runtime connectivity
                logger.warning("Redis global reset failed, using memory fallback: %s", exc)

        with self._lock:
            self._count = 0
            self._warnings_issued.clear()


# =============================================================================
# Anonymous User Limiter
# =============================================================================

class AnonymousLimiter(DailyResetMixin):
    """Tracks daily anonymous query usage, optionally backed by Redis."""

    def __init__(self, free_limit: int, redis_client=None, key_prefix: str = "trip_planner"):
        self.free_limit = free_limit
        self._usage: Dict[str, int] = {}
        self._reset_date: date = datetime.now().date()
        self._lock = threading.Lock()
        self._redis_client = redis_client
        self._key_prefix = key_prefix
        logger.info(
            "Anonymous limiter initialized (limit=%s, backend=%s).",
            free_limit,
            "redis" if redis_client is not None else "memory",
        )

    def _check_reset(self) -> None:
        if self._needs_reset():
            self._usage.clear()
            self._update_reset_date()

    def _redis_key(self, client_id: str, today: date) -> str:
        return f"{self._key_prefix}:anonymous_limit:{today.isoformat()}:{client_id}"

    def _increment_memory(self, client_id: str) -> Tuple[bool, int, int]:
        with self._lock:
            self._check_reset()
            count = self._usage.get(client_id, 0)
            if count >= self.free_limit:
                return False, count, 0
            count += 1
            self._usage[client_id] = count
            return True, count, self.free_limit - count

    def _increment_redis(self, client_id: str) -> Tuple[bool, int, int]:
        today = date.today()
        key = self._redis_key(client_id, today)
        try:
            count = int(self._redis_client.incr(key))
            if count == 1:
                self._redis_client.expire(key, _seconds_until_next_day_utc())
            remaining = max(0, self.free_limit - count)
            return count <= self.free_limit, count, remaining
        except Exception as exc:  # pragma: no cover - runtime connectivity
            logger.warning("Redis anonymous limiter failed, using memory fallback: %s", exc)
            return self._increment_memory(client_id)

    def check_and_increment(self, client_id: str) -> Tuple[bool, int, int]:
        if self._redis_client is not None:
            return self._increment_redis(client_id)
        return self._increment_memory(client_id)

    def get_remaining(self, client_id: str) -> int:
        if self._redis_client is not None:
            key = self._redis_key(client_id, date.today())
            try:
                count = int(self._redis_client.get(key) or 0)
                return max(0, self.free_limit - count)
            except Exception as exc:  # pragma: no cover - runtime connectivity
                logger.warning("Redis anonymous remaining check failed, using memory fallback: %s", exc)

        with self._lock:
            self._check_reset()
            count = self._usage.get(client_id, 0)
            return max(0, self.free_limit - count)

    def reset(self) -> None:
        with self._lock:
            self._usage.clear()


# =============================================================================
# SlowAPI Limiter
# =============================================================================

def get_client_identifier(request) -> str:
    """Get client identifier using proxy headers when available."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return get_remote_address(request)


_storage_uri = RATE_LIMIT_SETTINGS["redis_url"] if _redis_client is not None else "memory://"
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{RATE_LIMIT_PER_HOUR}/hour"],
    storage_uri=_storage_uri,
    enabled=True,
    swallow_errors=False,
)


# =============================================================================
# Global Singletons
# =============================================================================

global_limiter = GlobalDailyLimiter(
    daily_limit=DAILY_API_LIMIT,
    redis_client=_redis_client,
    key_prefix=_RATE_LIMIT_KEY_PREFIX,
)
anonymous_limiter = AnonymousLimiter(
    free_limit=ANONYMOUS_FREE_LIMIT,
    redis_client=_redis_client,
    key_prefix=_RATE_LIMIT_KEY_PREFIX,
)


# =============================================================================
# Convenience Functions
# =============================================================================

def check_global_limit() -> Tuple[bool, int, int]:
    return global_limiter.increment()


def get_global_status() -> Dict:
    return global_limiter.get_status()


def is_rate_limited() -> bool:
    status = global_limiter.get_status()
    return status["remaining"] <= 0

