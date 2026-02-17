"""
Rate Limiter - Multi-level rate limiting for production safety.

This module implements rate limiting at multiple levels:
1. Global daily limit - Protects overall API budget (default: 200 calls/day)
2. Per-IP rate limiting - Prevents abuse from single IPs
3. Per-user rate limiting - Ensures fair usage across users

Environment variables:
    DAILY_API_LIMIT: Maximum API calls per day (default: 200)
    RATE_LIMIT_PER_MINUTE: Per-user minute limit (default: 20)
    RATE_LIMIT_PER_HOUR: Per-IP hour limit (default: 100)
"""

import os
import threading
from datetime import datetime, date
from typing import Dict, Tuple

from slowapi import Limiter
from slowapi.util import get_remote_address


# =============================================================================
# Configuration
# =============================================================================

DAILY_API_LIMIT = int(os.getenv("DAILY_API_LIMIT", "200"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))


# =============================================================================
# Global Daily Rate Limiter
# =============================================================================

class DailyResetMixin:
    """Mixin for rate limiters that reset daily at midnight."""

    def _needs_reset(self) -> bool:
        """Check if reset is needed (new day)."""
        return datetime.now().date() > self._reset_date

    def _update_reset_date(self) -> None:
        """Update the reset date to today."""
        self._reset_date = datetime.now().date()


class GlobalDailyLimiter(DailyResetMixin):
    """
    A global rate limiter that enforces a daily API call limit.

    This is the most critical limiter - it protects your API budget
    by ensuring you never exceed a specified number of calls per day.

    Thread-safe implementation using locks.

    Example:
        limiter = GlobalDailyLimiter(daily_limit=200)

        allowed, count, remaining = limiter.increment()
        if not allowed:
            raise Exception("Daily limit exceeded")
    """

    def __init__(self, daily_limit: int = 200):
        """
        Initialize the global daily limiter.

        Args:
            daily_limit: Maximum API calls allowed per day
        """
        self.daily_limit = daily_limit
        self._count = 0
        self._reset_date: date = datetime.now().date()
        self._lock = threading.Lock()
        self._warning_thresholds = [0.5, 0.8, 0.9, 0.95]  # 50%, 80%, 90%, 95%
        self._warnings_issued: set = set()

        print(f"[RateLimiter] Initialized with daily limit: {daily_limit} calls/day")

    def _check_reset(self) -> None:
        """Reset counter if it's a new day."""
        if self._needs_reset():
            self._count = 0
            self._update_reset_date()
            self._warnings_issued.clear()
            print(f"[RateLimiter] Daily counter reset. New day: {self._reset_date}")
    
    def _issue_warning_if_needed(self, count: int) -> None:
        """Issue warnings at configured thresholds."""
        usage_ratio = count / self.daily_limit
        
        for threshold in self._warning_thresholds:
            threshold_key = int(threshold * 100)
            if usage_ratio >= threshold and threshold_key not in self._warnings_issued:
                self._warnings_issued.add(threshold_key)
                percentage = int(threshold * 100)
                print(f"[RateLimiter] WARNING: {percentage}% of daily limit used ({count}/{self.daily_limit})")
    
    def increment(self) -> Tuple[bool, int, int]:
        """
        Increment the counter and check if limit is exceeded.
        
        Returns:
            Tuple of (allowed: bool, current_count: int, remaining: int)
        """
        with self._lock:
            self._check_reset()
            
            # Check limit
            if self._count >= self.daily_limit:
                return False, self._count, 0
            
            # Increment
            self._count += 1
            remaining = self.daily_limit - self._count
            
            # Issue warnings at thresholds
            self._issue_warning_if_needed(self._count)
            
            return True, self._count, remaining
    
    def get_status(self) -> Dict:
        """
        Get current rate limit status.
        
        Returns:
            Dict with count, limit, remaining, reset_date, usage_percent
        """
        with self._lock:
            self._check_reset()
            
            return {
                "count": self._count,
                "limit": self.daily_limit,
                "remaining": self.daily_limit - self._count,
                "reset_date": self._reset_date.isoformat(),
                "usage_percent": round((self._count / self.daily_limit) * 100, 1)
            }
    
    def reset(self) -> None:
        """
        Force reset the counter (for testing purposes only).
        """
        with self._lock:
            self._count = 0
            self._warnings_issued.clear()
            print("[RateLimiter] Counter manually reset")


# =============================================================================
# Anonymous User Limiter - 5 free queries before login required
# =============================================================================

ANONYMOUS_FREE_LIMIT = int(os.getenv("ANONYMOUS_FREE_LIMIT", "5"))

class AnonymousLimiter(DailyResetMixin):
    """
    Tracks query usage for anonymous (non-logged-in) users.

    Allows a limited number of free queries before requiring login.
    Uses IP address as identifier for anonymous users.
    Resets daily at midnight (UTC).
    """

    def __init__(self, free_limit: int = 5):
        self.free_limit = free_limit
        self._usage: Dict[str, int] = {}  # IP -> count
        self._reset_date: date = datetime.now().date()
        self._lock = threading.Lock()
        print(f"[AnonymousLimiter] Initialized with free limit: {free_limit} queries/day")

    def _check_reset(self) -> None:
        """Reset counter if it's a new day."""
        if self._needs_reset():
            self._usage.clear()
            self._update_reset_date()
            print(f"[AnonymousLimiter] Daily reset. New day: {self._reset_date}")
    
    def check_and_increment(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if anonymous client can make another query.
        
        Args:
            client_id: IP address or identifier for the anonymous user
            
        Returns:
            Tuple of (allowed: bool, current_count: int, remaining: int)
        """
        with self._lock:
            self._check_reset()
            count = self._usage.get(client_id, 0)
            
            if count >= self.free_limit:
                return False, count, 0
            
            count += 1
            self._usage[client_id] = count
            remaining = self.free_limit - count
            
            return True, count, remaining
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining free queries for an anonymous client."""
        with self._lock:
            self._check_reset()
            count = self._usage.get(client_id, 0)
            return max(0, self.free_limit - count)
    
    def reset(self) -> None:
        """Reset all anonymous usage (for testing)."""
        with self._lock:
            self._usage.clear()
            print("[AnonymousLimiter] Usage reset")


# Create singleton instance
anonymous_limiter = AnonymousLimiter(free_limit=ANONYMOUS_FREE_LIMIT)


# =============================================================================
# SlowAPI Limiter for FastAPI endpoints
# =============================================================================

def get_client_identifier(request) -> str:
    """
    Get a unique identifier for the client.
    
    Uses X-Forwarded-For header if behind a proxy, otherwise falls back
    to client IP address.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client identifier string (IP address)
    """
    # Check for forwarded header (when behind nginx/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return get_remote_address(request)


# Create the SlowAPI limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{RATE_LIMIT_PER_HOUR}/hour"],  # Default: per hour per IP
    storage_uri="memory://",  # In-memory storage (use Redis for production)
    enabled=True,
    swallow_errors=False,  # Don't silently ignore rate limit errors
)


# =============================================================================
# Global instance for daily limit
# =============================================================================

global_limiter = GlobalDailyLimiter(daily_limit=DAILY_API_LIMIT)


# =============================================================================
# Convenience functions
# =============================================================================

def check_global_limit() -> Tuple[bool, int, int]:
    """
    Check and increment the global daily limit.
    
    Returns:
        Tuple of (allowed: bool, current_count: int, remaining: int)
    """
    return global_limiter.increment()


def get_global_status() -> Dict:
    """
    Get the current global rate limit status.
    
    Returns:
        Dict with count, limit, remaining, reset_date, usage_percent
    """
    return global_limiter.get_status()


def is_rate_limited() -> bool:
    """
    Quick check if we're currently rate limited.
    
    Returns:
        True if rate limited, False otherwise
    """
    status = global_limiter.get_status()
    return status["remaining"] <= 0
