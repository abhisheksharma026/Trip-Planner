"""
Request ID Middleware.

Adds a unique request ID to each request for distributed tracing and debugging.
"""

import re
import uuid
from fastapi import Request
from trip_planner.logging_utils import set_request_id, clear_request_id

_REQUEST_ID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")


async def add_request_id(request: Request, call_next):
    """
    Add a unique request ID to each request.

    Uses the X-Request-ID header if provided by the client (validated),
    otherwise generates a new UUID. The request ID is stored in request.state
    for use in other middleware or route handlers.

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response with X-Request-ID header added
    """
    # Check for existing request ID header and validate format
    request_id = request.headers.get("X-Request-ID")

    if not request_id or not _REQUEST_ID_RE.fullmatch(request_id):
        # Generate new UUID if not provided or invalid
        request_id = str(uuid.uuid4())

    # Store in request.state for use in handlers
    request.state.request_id = request_id

    # Keep request_id in logging context for this request lifecycle.
    token = set_request_id(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_request_id(token)
