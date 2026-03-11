"""
Logging utilities for consistent, request-correlated application logs.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar, Token
from typing import Optional


_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject request_id from context vars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = _request_id_ctx.get("-")
        return True


def _ensure_request_id_filter() -> None:
    request_id_filter = RequestIdFilter()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        has_filter = any(isinstance(existing, RequestIdFilter) for existing in handler.filters)
        if not has_filter:
            handler.addFilter(request_id_filter)


def configure_logging(level: str = "INFO") -> None:
    """
    Configure app-wide logging once with request_id support.

    Safe to call multiple times.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s",
        )
    else:
        root_logger.setLevel(numeric_level)

    _ensure_request_id_filter()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with request_id support."""
    return logging.getLogger(name)


def set_request_id(request_id: str) -> Token:
    """Set request ID for current context and return reset token."""
    return _request_id_ctx.set(request_id)


def clear_request_id(token: Optional[Token]) -> None:
    """Reset request ID context using token from set_request_id."""
    if token is not None:
        _request_id_ctx.reset(token)

