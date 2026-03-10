"""
Request Logging Middleware.

Logs all HTTP requests with timing information.
"""

import logging
import time
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
    start_time = time.perf_counter()
    request_id = getattr(request.state, "request_id", "-")
    client_host = request.client.host if request.client else None

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "HTTP request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "client_host": client_host,
                "request_id": request_id,
            },
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "HTTP request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_host": client_host,
            "request_id": request_id,
        },
    )
    return response
