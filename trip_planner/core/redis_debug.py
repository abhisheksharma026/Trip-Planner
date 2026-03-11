"""
Redis debug helpers for safe admin visibility.

This module intentionally returns metadata-only views and avoids exposing
full payload contents for session snapshots.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from trip_planner.logging_utils import get_logger

logger = get_logger(__name__)


def _to_text(value: Any) -> str:
    """Convert Redis value/key to text."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _hash_identifier(raw_value: str) -> str:
    """Return a short stable hash for potentially sensitive identifiers."""
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()[:12]


def _safe_get_count(redis_client, key: str) -> int:
    """Get an integer count safely from Redis."""
    try:
        return int(redis_client.get(key) or 0)
    except Exception:
        return 0


def _safe_get_ttl(redis_client, key: str) -> Optional[int]:
    """Get Redis TTL in seconds, returning None if unavailable."""
    try:
        ttl = int(redis_client.ttl(key))
        return ttl
    except Exception:
        return None


def _iter_keys(redis_client, pattern: str, max_keys: int) -> list[str]:
    """Iterate keys using scan-based strategies with a hard cap."""
    keys: list[str] = []

    # Preferred path for redis-py client.
    if hasattr(redis_client, "scan_iter"):
        try:
            for key in redis_client.scan_iter(match=pattern, count=max_keys):
                keys.append(_to_text(key))
                if len(keys) >= max_keys:
                    break
            return keys
        except Exception as exc:  # pragma: no cover - runtime backend behavior
            logger.warning("scan_iter failed for pattern '%s': %s", pattern, exc)

    # Fallback path for clients exposing SCAN only.
    if hasattr(redis_client, "scan"):
        try:
            cursor = 0
            while True:
                cursor, batch = redis_client.scan(cursor=cursor, match=pattern, count=max_keys)
                for key in batch:
                    keys.append(_to_text(key))
                    if len(keys) >= max_keys:
                        return keys
                if cursor == 0:
                    break
            return keys
        except Exception as exc:  # pragma: no cover - runtime backend behavior
            logger.warning("scan failed for pattern '%s': %s", pattern, exc)

    # Last-resort fallback for simple fake clients in tests.
    if hasattr(redis_client, "keys"):
        try:
            for key in redis_client.keys(pattern):
                keys.append(_to_text(key))
                if len(keys) >= max_keys:
                    break
        except Exception:
            return keys

    return keys


def _collect_global_limit_metadata(redis_client, prefix: str, max_keys: int) -> dict:
    base = f"{prefix}:global_limit:"
    pattern = f"{base}*"
    entries = []

    for key in _iter_keys(redis_client, pattern, max_keys=max_keys):
        if not key.startswith(base):
            continue
        date_part = key[len(base):]
        entries.append(
            {
                "date": date_part,
                "count": _safe_get_count(redis_client, key),
                "ttl_seconds": _safe_get_ttl(redis_client, key),
            }
        )

    entries.sort(key=lambda item: item["date"], reverse=True)
    return {
        "scanned_keys": len(entries),
        "entries": entries,
    }


def _collect_user_limit_metadata(redis_client, prefix: str, max_keys: int) -> dict:
    base = f"{prefix}:user_limit:"
    pattern = f"{base}*"
    entries = []

    for key in _iter_keys(redis_client, pattern, max_keys=max_keys):
        if not key.startswith(base):
            continue
        rest = key[len(base):]
        if ":" not in rest:
            continue

        date_part, user_id = rest.split(":", 1)
        entries.append(
            {
                "date": date_part,
                "subject_hash": _hash_identifier(user_id),
                "count": _safe_get_count(redis_client, key),
                "ttl_seconds": _safe_get_ttl(redis_client, key),
            }
        )

    entries.sort(key=lambda item: item["count"], reverse=True)
    return {
        "scanned_keys": len(entries),
        "entries": entries,
    }


def _collect_anonymous_limit_metadata(redis_client, prefix: str, max_keys: int) -> dict:
    base = f"{prefix}:anonymous_limit:"
    pattern = f"{base}*"
    entries = []

    for key in _iter_keys(redis_client, pattern, max_keys=max_keys):
        if not key.startswith(base):
            continue
        rest = key[len(base):]
        if ":" not in rest:
            continue

        date_part, client_id = rest.split(":", 1)
        entries.append(
            {
                "date": date_part,
                "subject_hash": _hash_identifier(client_id),
                "count": _safe_get_count(redis_client, key),
                "ttl_seconds": _safe_get_ttl(redis_client, key),
            }
        )

    entries.sort(key=lambda item: item["count"], reverse=True)
    return {
        "scanned_keys": len(entries),
        "entries": entries,
    }


def _collect_session_memory_metadata(redis_client, prefix: str, max_keys: int) -> dict:
    base = f"{prefix}:session_memory:"
    pattern = f"{base}*"
    entries = []

    for key in _iter_keys(redis_client, pattern, max_keys=max_keys):
        if not key.startswith(base):
            continue

        rest = key[len(base):]
        if ":" in rest:
            app_name, user_id = rest.split(":", 1)
        else:
            app_name, user_id = "unknown", rest

        raw_payload = None
        try:
            raw_payload = redis_client.get(key)
        except Exception:
            raw_payload = None

        payload_text = _to_text(raw_payload) if raw_payload is not None else ""
        payload_size_bytes = len(payload_text.encode("utf-8")) if payload_text else 0
        ttl_seconds = _safe_get_ttl(redis_client, key)

        if not payload_text:
            entries.append(
                {
                    "app": app_name,
                    "subject_hash": _hash_identifier(user_id),
                    "payload_bytes": payload_size_bytes,
                    "ttl_seconds": ttl_seconds,
                    "status": "missing_payload",
                }
            )
            continue

        try:
            payload = json.loads(payload_text)
        except Exception:
            entries.append(
                {
                    "app": app_name,
                    "subject_hash": _hash_identifier(user_id),
                    "payload_bytes": payload_size_bytes,
                    "ttl_seconds": ttl_seconds,
                    "status": "invalid_json",
                }
            )
            continue

        session_data = payload.get("session") if isinstance(payload, dict) else {}
        state_data = session_data.get("state") if isinstance(session_data, dict) else {}
        events_data = session_data.get("events") if isinstance(session_data, dict) else []
        conversation_queries = payload.get("conversation_queries") if isinstance(payload, dict) else []

        entries.append(
            {
                "app": app_name,
                "subject_hash": _hash_identifier(user_id),
                "session_id": str(session_data.get("id", ""))[:16],
                "conversation_id": str(payload.get("conversation_id", ""))[:16],
                "event_count": len(events_data) if isinstance(events_data, list) else 0,
                "query_count": len(conversation_queries) if isinstance(conversation_queries, list) else 0,
                "state_key_count": len(state_data) if isinstance(state_data, dict) else 0,
                "payload_bytes": payload_size_bytes,
                "ttl_seconds": ttl_seconds,
                "status": "ok",
            }
        )

    entries.sort(key=lambda item: item.get("payload_bytes", 0), reverse=True)
    return {
        "scanned_keys": len(entries),
        "entries": entries,
    }


def collect_redis_debug_snapshot(
    redis_client,
    rate_limit_prefix: str,
    session_memory_prefix: str,
    max_keys_per_group: int = 25,
) -> dict:
    """
    Collect safe Redis metadata for admin debugging.

    Returns grouped metadata for rate-limit counters and session-memory
    snapshots without exposing full event/query payloads.
    """
    max_keys = int(max_keys_per_group)
    if max_keys < 1:
        max_keys = 1
    if max_keys > 100:
        max_keys = 100

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "max_keys_per_group": max_keys,
        "rate_limits": {
            "global": _collect_global_limit_metadata(redis_client, rate_limit_prefix, max_keys),
            "user": _collect_user_limit_metadata(redis_client, rate_limit_prefix, max_keys),
            "anonymous": _collect_anonymous_limit_metadata(redis_client, rate_limit_prefix, max_keys),
        },
        "session_memory": _collect_session_memory_metadata(
            redis_client,
            session_memory_prefix,
            max_keys,
        ),
    }
