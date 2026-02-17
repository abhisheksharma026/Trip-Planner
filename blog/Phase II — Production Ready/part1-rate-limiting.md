# Building a Production-Grade AI Agent from Scratch - Phase II Part 1: Rate Limiting

## Overview

In Phase I, we built a fully functional AI Trip Planner. Now in Phase II, we're making it **production-ready**. The first critical concern is **rate limiting** - without it, your application is vulnerable to API quota exhaustion, cost overruns, and abuse.

## Why Rate Limiting Matters

For AI applications, rate limiting is not optional:

1. **API Quotas**: External APIs like Amadeus have strict limits
2. **Cost Control**: LLM API calls are pay-per-use - uncontrolled access can drain your budget
3. **Resource Protection**: Unlimited sessions can crash your server
4. **Abuse Prevention**: Malicious users can spam your endpoints

Our constraint: **Maximum 200 API calls per day**.

## Rate Limiting Architecture

We implement rate limiting at multiple levels:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Request Flow                                │
│                                                                 │
│  User Request ──▶ IP Rate Limit ──▶ Global Limit ──▶ API       │
│                     100/hr            200/day                  │
└─────────────────────────────────────────────────────────────────┘
```

| Level | Scope | Limit | Purpose |
|-------|-------|-------|---------|
| Global | Entire app | 200/day | Protect API budget |
| Per-IP | Client IP | 100/hour | Prevent abuse |
| Per-Endpoint | /api/query | 20/minute | Fair usage |

## Building the Rate Limiter

### Step 1: Add Dependency

Add to `requirements.txt`:

```
slowapi>=0.1.9
```

### Step 2: Create Rate Limiter Module

Create `trip_planner/core/rate_limiter.py`:

```python
"""
Rate Limiter - Multi-level rate limiting for production safety.
"""

import os
import threading
from datetime import datetime, date
from typing import Dict, Tuple

from slowapi import Limiter
from slowapi.util import get_remote_address


# Configuration from environment
DAILY_API_LIMIT = int(os.getenv("DAILY_API_LIMIT", "200"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))


class GlobalDailyLimiter:
    """
    A global rate limiter that enforces a daily API call limit.
    Thread-safe implementation.
    """
    
    def __init__(self, daily_limit: int = 200):
        self.daily_limit = daily_limit
        self._count = 0
        self._reset_date: date = datetime.now().date()
        self._lock = threading.Lock()
        print(f"[RateLimiter] Initialized with daily limit: {daily_limit} calls/day")
    
    def increment(self) -> Tuple[bool, int, int]:
        """Increment counter and check if limit exceeded."""
        with self._lock:
            # Reset at midnight
            today = datetime.now().date()
            if today > self._reset_date:
                self._count = 0
                self._reset_date = today
            
            if self._count >= self.daily_limit:
                return False, self._count, 0
            
            self._count += 1
            return True, self._count, self.daily_limit - self._count
    
    def get_status(self) -> Dict:
        """Get current rate limit status."""
        with self._lock:
            return {
                "count": self._count,
                "limit": self.daily_limit,
                "remaining": self.daily_limit - self._count,
                "reset_date": self._reset_date.isoformat(),
            }


# SlowAPI limiter for FastAPI
def get_client_identifier(request) -> str:
    """Get client IP, handling proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{RATE_LIMIT_PER_HOUR}/hour"],
    storage_uri="memory://",
)

global_limiter = GlobalDailyLimiter(daily_limit=DAILY_API_LIMIT)


def check_global_limit() -> Tuple[bool, int, int]:
    return global_limiter.increment()

def get_global_status() -> Dict:
    return global_limiter.get_status()
```

### Step 3: Integrate with FastAPI

Update `app.py`:

```python
# Add imports
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from trip_planner.core.rate_limiter import (
    limiter, check_global_limit, get_global_status, RATE_LIMIT_PER_MINUTE
)

# Configure rate limiting after creating app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Update query endpoint
@app.post("/api/query", response_model=QueryResponse)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def handle_query(http_request: Request, request: QueryRequest):
    # Check global daily limit
    allowed, count, remaining = check_global_limit()
    if not allowed:
        raise HTTPException(status_code=429, detail="Daily API limit exceeded")
    
    # ... process query ...
    
    # Return with rate limit headers
    status = get_global_status()
    return JSONResponse(
        content=response.model_dump(),
        headers={
            "X-RateLimit-Limit": str(status["limit"]),
            "X-RateLimit-Remaining": str(status["remaining"]),
        }
    )

# Add status endpoint
@app.get("/api/rate-limit-status")
async def rate_limit_status():
    return get_global_status()
```

### Step 4: Update Environment Configuration

Add to `.env.example`:

```bash
# Rate Limiting Configuration
DAILY_API_LIMIT=200
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

## Testing

```bash
# Check rate limit status
curl http://localhost:5000/api/rate-limit-status

# Response:
# {"count": 0, "limit": 200, "remaining": 200, "reset_date": "2026-02-17"}
```

When rate limited, clients receive:

```json
{
    "detail": "Daily API limit exceeded. Please try again tomorrow."
}
```

## Files Changed

| File | Change |
|------|--------|
| `trip_planner/core/rate_limiter.py` | NEW - Rate limiting module |
| `app.py` | MODIFIED - Added rate limiting |
| `requirements.txt` | MODIFIED - Added slowapi |
| `.env.example` | MODIFIED - Added config options |

## Summary

In this part, we implemented:

1. **Global daily limit** - Protecting the 200 calls/day budget
2. **Per-IP rate limiting** - Preventing abuse from single sources
3. **Per-endpoint limits** - Fair usage across endpoints
4. **Status endpoint** - Visibility into rate limit state
5. **Response headers** - Client-side rate limit awareness

### Key Takeaway

Rate limiting is essential for production AI applications. Without it, a single user could exhaust your API budget in minutes. Start with conservative limits and adjust based on usage patterns.

## Next Steps

In Part 2, we'll add Docker containerization for consistent deployment across environments.
