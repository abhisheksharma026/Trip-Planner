import asyncio

import trip_planner.core.session_manager as session_manager_module


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value, ex=None):
        self.store[key] = value
        return True

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)
        return 1


def test_redis_session_memory_restore(monkeypatch):
    fake_redis = FakeRedis()

    monkeypatch.setattr(
        session_manager_module,
        "get_session_memory_settings",
        lambda: {
            "backend": "redis",
            "redis_url": "redis://test:6379/0",
            "key_prefix": "test_trip_planner",
            "ttl_seconds": 3600,
        },
    )
    monkeypatch.setattr(session_manager_module, "get_redis_client", lambda _url: fake_redis)
    monkeypatch.setattr(session_manager_module, "OPIK_AVAILABLE", False)

    manager1 = session_manager_module.SessionManager(app_name="test_app")
    session1 = asyncio.run(manager1.get_or_create_session("user-1"))
    manager1.add_query_to_conversation("user-1", "hello", "world")
    asyncio.run(manager1.persist_user_memory("user-1", session1))

    manager2 = session_manager_module.SessionManager(app_name="test_app")
    session2 = asyncio.run(manager2.get_or_create_session("user-1"))

    assert session2.id == session1.id
    assert manager2.get_query_count("user-1") == 1
    assert manager2.conversation_queries["user-1"][0]["query"] == "hello"


def test_end_conversation_clears_persisted_memory(monkeypatch):
    fake_redis = FakeRedis()

    monkeypatch.setattr(
        session_manager_module,
        "get_session_memory_settings",
        lambda: {
            "backend": "redis",
            "redis_url": "redis://test:6379/0",
            "key_prefix": "test_trip_planner",
            "ttl_seconds": 3600,
        },
    )
    monkeypatch.setattr(session_manager_module, "get_redis_client", lambda _url: fake_redis)
    monkeypatch.setattr(session_manager_module, "OPIK_AVAILABLE", False)

    manager = session_manager_module.SessionManager(app_name="test_app")
    session = asyncio.run(manager.get_or_create_session("user-2"))
    asyncio.run(manager.persist_user_memory("user-2", session))

    redis_key = manager._session_memory_key("user-2")
    assert fake_redis.get(redis_key) is not None

    manager.end_conversation("user-2", "satisfied")
    assert fake_redis.get(redis_key) is None
