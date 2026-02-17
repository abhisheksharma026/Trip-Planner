"""
Content-Type Validation Middleware.

Validates that POST/PUT/PATCH requests have appropriate content-type headers.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse


async def validate_content_type(request: Request, call_next):
    """
    Validate Content-Type for POST/PUT/PATCH requests.

    Ensures that requests with a body have the correct content-type header.
    Skips validation for requests without a content-type header (letting
    FastAPI/Pydantic handle validation) and for multipart form data.

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response from the next handler, or 415 error if content-type is invalid
    """
    if request.method in ["POST", "PUT", "PATCH"]:
        # Get content-type header
        content_type = request.headers.get("content-type", "")

        if content_type:
            # Check if content-type is allowed
            allowed_types = [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded",
            ]

            if not any(content_type.startswith(ct) for ct in allowed_types):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "Unsupported Media Type",
                        "message": "Content-Type must be application/json"
                    }
                )

    return await call_next(request)
