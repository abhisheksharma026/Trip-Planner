"""
Request ID Middleware.

Adds a unique request ID to each request for distributed tracing and debugging.
"""

import uuid
from fastapi import Request, Response


async def add_request_id(request: Request, call_next):
    """
    Add a unique request ID to each request.

    Uses the X-Request-ID header if provided by the client, otherwise
    generates a new UUID. The request ID is stored in request.state
    for use in other middleware or route handlers.

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response with X-Request-ID header added
    """
    # Check for existing request ID header
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        # Generate new UUID if not provided
        request_id = str(uuid.uuid4())

    # Store in request.state for use in handlers
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Add request ID to response header
    response.headers["X-Request-ID"] = request_id

    return response
