"""Shared test fixtures for the AI Trip Planner test suite."""

import fnmatch
from pathlib import Path

import pytest

import trip_planner.core.auth as auth


class FakeRedis:
    """Unified fake Redis client for testing.

    Supports the subset of redis-py methods used across the codebase:
    get, set, delete, incr, expire, ttl, scan_iter, keys, ping.
    """

    def __init__(self, values: dict[str, str] | None = None, ttls: dict[str, int] | None = None):
        self.store: dict[str, str] = dict(values) if values else {}
        self.ttls: dict[str, int] = dict(ttls) if ttls else {}

    def ping(self) -> bool:
        return True

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ex=None):
        self.store[key] = str(value) if not isinstance(value, str) else value
        if ex is not None:
            self.ttls[key] = int(ex)
        return True

    def delete(self, key: str):
        self.store.pop(key, None)
        self.ttls.pop(key, None)
        return 1

    def incr(self, key: str):
        current = int(self.store.get(key, 0))
        current += 1
        self.store[key] = str(current)
        return current

    def expire(self, key: str, seconds: int):
        self.ttls[key] = seconds
        return True

    def ttl(self, key: str):
        return self.ttls.get(key, -1)

    def scan_iter(self, match: str = "*", count: int = 10):
        del count
        for key in sorted(self.store.keys()):
            if fnmatch.fnmatch(key, match):
                yield key

    def keys(self, pattern: str = "*"):
        return [k for k in sorted(self.store.keys()) if fnmatch.fnmatch(k, pattern)]


@pytest.fixture
def fake_redis():
    """Provide a fresh FakeRedis instance."""
    return FakeRedis()


@pytest.fixture
def temp_auth_db(tmp_path: Path):
    """Configure auth module to use a temporary database."""
    auth.DATABASE_PATH = str(tmp_path / "auth_test.db")
    auth.init_db()
    return tmp_path
