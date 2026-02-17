"""
Security Headers Middleware.

Adds security-related HTTP headers to all responses.
"""

import os
from fastapi import Request, Response


async def add_security_headers(request: Request, call_next):
    """
    Add security-related HTTP headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS filter
    - Strict-Transport-Security: Enforces HTTPS (production only)

    Args:
        request: The incoming HTTP request
        call_next: The next middleware or route handler

    Returns:
        Response with security headers added
    """
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HSTS only in production with HTTPS
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response
