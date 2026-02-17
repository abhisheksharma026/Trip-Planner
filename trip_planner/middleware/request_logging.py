"""
Request Logging Middleware.

Logs all HTTP requests with timing information.
"""

import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing information.

    Logs the HTTP method, path, status code, duration in milliseconds,
    and client host address. Uses structured logging for better parsing.

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response from the next handler
    """
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_host": request.client.host if request.client else None
        }
    )

    return response
