"""Unit tests for trip_planner.core.rate_limiter.

Tests the GlobalDailyLimiter, AnonymousLimiter, and get_client_identifier
using fresh instances (not the module-level singletons).
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import FakeRedis

# Import classes directly — the module-level singletons are already created
# at import time, but we instantiate fresh objects for each test.
from trip_planner.core.rate_limiter import (
    AnonymousLimiter,
    GlobalDailyLimiter,
    get_client_identifier,
)


# =============================================================================
# GlobalDailyLimiter — in-memory path
# =============================================================================

class TestGlobalDailyLimiterMemory:
    def test_increment_under_limit_returns_true(self):
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=None, key_prefix="test")
        allowed, count, remaining = limiter.increment()
        assert allowed is True
        assert count == 1
        assert remaining == 4

    def test_increment_at_limit_blocks(self):
        limiter = GlobalDailyLimiter(daily_limit=3, redis_client=None, key_prefix="test")
        for _ in range(3):
            limiter.increment()
        allowed, count, remaining = limiter.increment()
        assert allowed is False
        assert count == 3
        assert remaining == 0

    def test_get_status_reflects_current_count(self):
        limiter = GlobalDailyLimiter(daily_limit=10, redis_client=None, key_prefix="test")
        limiter.increment()
        limiter.increment()
        status = limiter.get_status()
        assert status["count"] == 2
        assert status["limit"] == 10
        assert status["remaining"] == 8
        assert status["reset_date"] == date.today().isoformat()

    def test_counter_resets_on_new_day(self):
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=None, key_prefix="test")
        limiter.increment()
        limiter.increment()
        assert limiter.get_status()["count"] == 2

        # Simulate next day
        tomorrow = datetime.now().date() + timedelta(days=1)
        with patch("trip_planner.core.rate_limiter.DailyResetMixin._needs_reset", return_value=True), \
             patch("trip_planner.core.rate_limiter.DailyResetMixin._update_reset_date"):
            limiter._reset_date = tomorrow - timedelta(days=2)  # Force reset
            allowed, count, remaining = limiter.increment()
            assert count == 1  # Reset happened
            assert allowed is True

    def test_reset_clears_counter(self):
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=None, key_prefix="test")
        limiter.increment()
        limiter.increment()
        limiter.reset()
        status = limiter.get_status()
        assert status["count"] == 0


# =============================================================================
# GlobalDailyLimiter — Redis path
# =============================================================================

class TestGlobalDailyLimiterRedis:
    def test_increment_uses_redis(self):
        fake = FakeRedis()
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=fake, key_prefix="test")
        allowed, count, remaining = limiter.increment()
        assert allowed is True
        assert count == 1
        assert remaining == 4
        # Verify key was created in Redis
        key = f"test:global_limit:{date.today().isoformat()}"
        assert fake.get(key) == "1"

    def test_redis_blocks_at_limit(self):
        fake = FakeRedis()
        limiter = GlobalDailyLimiter(daily_limit=2, redis_client=fake, key_prefix="test")
        limiter.increment()
        limiter.increment()
        allowed, count, remaining = limiter.increment()
        assert allowed is False
        assert count == 3
        assert remaining == 0

    def test_get_status_reads_from_redis(self):
        fake = FakeRedis()
        limiter = GlobalDailyLimiter(daily_limit=10, redis_client=fake, key_prefix="test")
        limiter.increment()
        limiter.increment()
        limiter.increment()
        status = limiter.get_status()
        assert status["count"] == 3
        assert status["remaining"] == 7

    def test_redis_failure_falls_back_to_memory(self):
        """When Redis raises an exception, fallback to memory."""
        broken_redis = MagicMock()
        broken_redis.incr.side_effect = ConnectionError("Redis down")
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=broken_redis, key_prefix="test")
        allowed, count, remaining = limiter.increment()
        # Should succeed via memory fallback
        assert allowed is True
        assert count == 1

    def test_reset_deletes_redis_key(self):
        fake = FakeRedis()
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=fake, key_prefix="test")
        limiter.increment()
        key = f"test:global_limit:{date.today().isoformat()}"
        assert fake.get(key) is not None
        limiter.reset()
        assert fake.get(key) is None

    def test_expire_set_on_first_increment(self):
        fake = FakeRedis()
        limiter = GlobalDailyLimiter(daily_limit=5, redis_client=fake, key_prefix="test")
        limiter.increment()
        key = f"test:global_limit:{date.today().isoformat()}"
        assert fake.ttls.get(key) is not None
        assert fake.ttls[key] > 0


# =============================================================================
# AnonymousLimiter — in-memory path
# =============================================================================

class TestAnonymousLimiterMemory:
    def test_increment_under_limit_returns_true(self):
        limiter = AnonymousLimiter(free_limit=5, redis_client=None, key_prefix="test")
        allowed, count, remaining = limiter.check_and_increment("client1")
        assert allowed is True
        assert count == 1
        assert remaining == 4

    def test_different_clients_independent(self):
        limiter = AnonymousLimiter(free_limit=2, redis_client=None, key_prefix="test")
        limiter.check_and_increment("client1")
        limiter.check_and_increment("client1")
        # client1 is at limit
        allowed1, _, _ = limiter.check_and_increment("client1")
        assert allowed1 is False
        # client2 is fresh
        allowed2, count2, remaining2 = limiter.check_and_increment("client2")
        assert allowed2 is True
        assert count2 == 1

    def test_blocks_at_limit(self):
        limiter = AnonymousLimiter(free_limit=3, redis_client=None, key_prefix="test")
        for _ in range(3):
            limiter.check_and_increment("client1")
        allowed, count, remaining = limiter.check_and_increment("client1")
        assert allowed is False
        assert remaining == 0

    def test_get_remaining(self):
        limiter = AnonymousLimiter(free_limit=5, redis_client=None, key_prefix="test")
        limiter.check_and_increment("client1")
        limiter.check_and_increment("client1")
        assert limiter.get_remaining("client1") == 3
        assert limiter.get_remaining("unknown_client") == 5

    def test_reset_clears_all_clients(self):
        limiter = AnonymousLimiter(free_limit=5, redis_client=None, key_prefix="test")
        limiter.check_and_increment("client1")
        limiter.check_and_increment("client2")
        limiter.reset()
        assert limiter.get_remaining("client1") == 5
        assert limiter.get_remaining("client2") == 5


# =============================================================================
# AnonymousLimiter — Redis path
# =============================================================================

class TestAnonymousLimiterRedis:
    def test_increment_uses_redis(self):
        fake = FakeRedis()
        limiter = AnonymousLimiter(free_limit=5, redis_client=fake, key_prefix="test")
        allowed, count, remaining = limiter.check_and_increment("client1")
        assert allowed is True
        assert count == 1
        assert remaining == 4

    def test_redis_key_includes_client_and_date(self):
        fake = FakeRedis()
        limiter = AnonymousLimiter(free_limit=5, redis_client=fake, key_prefix="test")
        limiter.check_and_increment("192.168.1.1")
        expected_key = f"test:anonymous_limit:{date.today().isoformat()}:192.168.1.1"
        assert fake.get(expected_key) is not None

    def test_redis_blocks_at_limit(self):
        fake = FakeRedis()
        limiter = AnonymousLimiter(free_limit=2, redis_client=fake, key_prefix="test")
        limiter.check_and_increment("client1")
        limiter.check_and_increment("client1")
        allowed, count, remaining = limiter.check_and_increment("client1")
        assert allowed is False

    def test_redis_failure_falls_back_to_memory(self):
        broken_redis = MagicMock()
        broken_redis.incr.side_effect = ConnectionError("Redis down")
        limiter = AnonymousLimiter(free_limit=5, redis_client=broken_redis, key_prefix="test")
        allowed, count, remaining = limiter.check_and_increment("client1")
        assert allowed is True
        assert count == 1


# =============================================================================
# get_client_identifier
# =============================================================================

class TestGetClientIdentifier:
    def _make_request(self, headers=None, client_host="127.0.0.1"):
        request = MagicMock()
        request.headers = headers or {}
        request.client = MagicMock()
        request.client.host = client_host
        return request

    def test_returns_x_forwarded_for_first_ip(self):
        request = self._make_request(
            headers={"X-Forwarded-For": "203.0.113.50, 70.41.3.18, 150.172.238.178"}
        )
        assert get_client_identifier(request) == "203.0.113.50"

    def test_strips_whitespace_from_forwarded_for(self):
        request = self._make_request(
            headers={"X-Forwarded-For": "  203.0.113.50  , 70.41.3.18"}
        )
        assert get_client_identifier(request) == "203.0.113.50"

    def test_returns_x_real_ip_when_no_forwarded_for(self):
        request = self._make_request(headers={"X-Real-IP": "10.0.0.1"})
        assert get_client_identifier(request) == "10.0.0.1"

    def test_falls_back_to_client_host(self):
        request = self._make_request(headers={}, client_host="192.168.1.100")
        # get_remote_address from slowapi uses request.client.host
        result = get_client_identifier(request)
        assert result is not None

    def test_x_forwarded_for_takes_priority_over_x_real_ip(self):
        request = self._make_request(
            headers={"X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"}
        )
        assert get_client_identifier(request) == "1.2.3.4"
