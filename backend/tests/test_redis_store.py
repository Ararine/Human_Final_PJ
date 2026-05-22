import json

from services import redis_store


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}
        self.deleted = []

    def setex(self, key, seconds, value):
        self.values[key] = value
        self.expirations[key] = seconds
        return True

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.deleted.append(key)
        existed = key in self.values
        self.values.pop(key, None)
        self.expirations.pop(key, None)
        return 1 if existed else 0

    def ping(self):
        return True


def test_oauth_state_helpers_store_json_with_ttl(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: client)
    monkeypatch.setenv("REDIS_OAUTH_STATE_TTL_SECONDS", "300")

    redis_store.save_oauth_state("state-1", {"provider": "kakao"})

    assert client.expirations["oauth_state:state-1"] == 300
    assert json.loads(client.values["oauth_state:state-1"]) == {"provider": "kakao"}
    assert redis_store.get_oauth_state("state-1") == {"provider": "kakao"}


def test_session_helpers_use_session_ttl_and_delete(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: client)
    monkeypatch.setenv("REDIS_SESSION_TTL_SECONDS", "604800")

    redis_store.save_session("session-1", {"user_id": "user-1"})

    assert client.expirations["auth:session:session-1"] == 604800
    assert redis_store.get_session("session-1") == {"user_id": "user-1"}

    assert redis_store.delete_session("session-1") is True
    assert "auth:session:session-1" in client.deleted
    assert redis_store.get_session("session-1") is None


def test_cache_helpers_use_named_ttls(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: client)
    monkeypatch.setenv("REDIS_DASHBOARD_CACHE_TTL_SECONDS", "10")
    monkeypatch.setenv("REDIS_PROGRESS_TTL_SECONDS", "3600")

    redis_store.set_dashboard_cache("summary", {"today": 3})
    redis_store.set_progress("job-1", {"progress_percent": 35})

    assert client.expirations["dashboard:summary"] == 10
    assert client.expirations["progress:job-1"] == 3600
    assert redis_store.get_dashboard_cache("summary") == {"today": 3}
    assert redis_store.get_progress("job-1") == {"progress_percent": 35}
