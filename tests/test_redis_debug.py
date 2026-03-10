import fnmatch
import json

from trip_planner.core.redis_debug import collect_redis_debug_snapshot


class FakeRedis:
    def __init__(self, values: dict[str, str], ttls: dict[str, int]):
        self.values = values
        self.ttls = ttls

    def get(self, key: str):
        return self.values.get(key)

    def ttl(self, key: str):
        return self.ttls.get(key, -1)

    def scan_iter(self, match: str = "*", count: int = 10):
        del count
        for key in sorted(self.values.keys()):
            if fnmatch.fnmatch(key, match):
                yield key


def test_collect_redis_debug_snapshot_masks_identifiers_and_omits_payloads():
    session_payload = {
        "session": {
            "id": "session-1234567890abcdef",
            "state": {"destination": "Paris", "budget": "3000"},
            "events": [{"id": "e1"}, {"id": "e2"}],
        },
        "conversation_id": "conv_abcdef1234567890",
        "conversation_queries": [
            {"query": "full query text", "response": "full response text"},
            {"query": "another query", "response": "another response"},
        ],
    }

    values = {
        "trip_planner:global_limit:2026-02-25": "7",
        "trip_planner:user_limit:2026-02-25:user:abc123": "3",
        "trip_planner:anonymous_limit:2026-02-25:203.0.113.45": "2",
        "trip_planner:session_memory:trip_planner_concierge:user:abc123": json.dumps(session_payload),
    }
    ttls = {
        "trip_planner:global_limit:2026-02-25": 700,
        "trip_planner:user_limit:2026-02-25:user:abc123": 600,
        "trip_planner:anonymous_limit:2026-02-25:203.0.113.45": 500,
        "trip_planner:session_memory:trip_planner_concierge:user:abc123": 3600,
    }

    snapshot = collect_redis_debug_snapshot(
        redis_client=FakeRedis(values=values, ttls=ttls),
        rate_limit_prefix="trip_planner",
        session_memory_prefix="trip_planner",
        max_keys_per_group=20,
    )

    user_entry = snapshot["rate_limits"]["user"]["entries"][0]
    anon_entry = snapshot["rate_limits"]["anonymous"]["entries"][0]
    session_entry = snapshot["session_memory"]["entries"][0]

    assert user_entry["subject_hash"] != "user:abc123"
    assert anon_entry["subject_hash"] != "203.0.113.45"

    assert session_entry["event_count"] == 2
    assert session_entry["query_count"] == 2
    assert session_entry["state_key_count"] == 2
    assert session_entry["session_id"] == "session-12345678"
    assert session_entry["conversation_id"] == "conv_abcdef12345"

    # We expose counts only, not raw payload contents.
    assert "events" not in session_entry
    assert "conversation_queries" not in session_entry


def test_collect_redis_debug_snapshot_respects_max_keys_per_group():
    values = {
        f"trip_planner:user_limit:2026-02-25:user:{idx}": str(idx)
        for idx in range(10)
    }
    ttls = {key: 100 for key in values}

    snapshot = collect_redis_debug_snapshot(
        redis_client=FakeRedis(values=values, ttls=ttls),
        rate_limit_prefix="trip_planner",
        session_memory_prefix="trip_planner",
        max_keys_per_group=3,
    )

    assert len(snapshot["rate_limits"]["user"]["entries"]) == 3
