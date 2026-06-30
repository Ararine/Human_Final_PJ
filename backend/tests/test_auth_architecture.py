import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from services import auth, oauth, redis_store, users


client = TestClient(main.app, follow_redirects=False)


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

    def delete(self, *keys):
        count = 0
        for key in keys:
            self.deleted.append(key)
            if key in self.values:
                count += 1
                self.values.pop(key, None)
                self.expirations.pop(key, None)
        return count

    def scan_iter(self, match=None):
        if match is None:
            yield from list(self.values.keys())
            return
        prefix = match.rstrip("*")
        for key in list(self.values.keys()):
            if key.startswith(prefix):
                yield key


@pytest.fixture(autouse=True)
def auth_env(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_SECONDS", "604800")
    monkeypatch.setenv("REDIS_SESSION_TTL_SECONDS", "604800")
    monkeypatch.setenv("COOKIE_SECURE", "false")


@pytest.fixture()
def fake_redis(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: redis)
    monkeypatch.setattr(users, "get_user_by_id", lambda user_id: active_user())
    return redis


def active_user():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "provider": "google",
        "provider_user_id": "google-user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "profile_image_url": None,
        "role": "USER",
        "status": "active",
    }


def test_oauth_callback_issues_jwt_cookies_and_stores_session(monkeypatch, fake_redis):
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:3000")
    state = oauth.create_oauth_state("google")
    monkeypatch.setattr(oauth, "exchange_code_for_user", lambda provider, code, state_value: (
        {
            "provider": provider,
            "provider_user_id": "google-user-1",
            "email": "user@example.com",
            "name": "Garim User",
            "profile_image_url": None,
        },
        {"provider": provider, "reregister": False},
        "provider-token",
    ))
    monkeypatch.setattr(users, "get_or_create_oauth_user", lambda oauth_user: active_user())

    response = client.get(f"/auth/google/callback?code=sample-code&state={state}")

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/"
    set_cookie = response.headers.get_list("set-cookie")
    assert any(cookie.startswith("access_token=") and "HttpOnly" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("refresh_token=") and "HttpOnly" in cookie for cookie in set_cookie)
    assert len([key for key in fake_redis.values if key.startswith("auth:session:")]) == 1


def test_access_token_requires_redis_session(fake_redis):
    token_pair = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    session_id = token_pair["session_id"]

    assert auth.authenticate_access_token(token_pair["access_token"])["session_id"] == session_id

    redis_store.delete_session(session_id)

    with pytest.raises(HTTPException) as exc_info:
        auth.authenticate_access_token(token_pair["access_token"])

    assert exc_info.value.status_code == 401


def test_refresh_rotates_token_and_verifies_stored_jti_and_hash(fake_redis):
    token_pair = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    session_before = redis_store.get_session(token_pair["session_id"])

    rotated = auth.refresh_login_session(token_pair["refresh_token"])

    session_after = redis_store.get_session(token_pair["session_id"])
    assert rotated["access_token"] != token_pair["access_token"]
    assert rotated["refresh_token"] != token_pair["refresh_token"]
    assert session_after["refresh_jti"] != session_before["refresh_jti"]
    assert session_after["refresh_hash"] == auth.hash_refresh_token(rotated["refresh_token"])

    with pytest.raises(HTTPException) as exc_info:
        auth.refresh_login_session(token_pair["refresh_token"])

    assert exc_info.value.status_code == 401
    assert redis_store.get_session(token_pair["session_id"]) is None


def test_logout_deletes_session_and_token_cookies(fake_redis):
    token_pair = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")

    response = client.post("/auth/logout", cookies={
        "access_token": token_pair["access_token"],
        "refresh_token": token_pair["refresh_token"],
    })

    assert response.status_code == 200
    assert redis_store.get_session(token_pair["session_id"]) is None
    set_cookie = response.headers.get_list("set-cookie")
    assert any(cookie.startswith("access_token=") and "Max-Age=0" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("refresh_token=") and "Max-Age=0" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("access_token=") and "Path=/" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("refresh_token=") and "Path=/auth/refresh" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("refresh_token=") and "Path=/" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("garim_auth=") and "Max-Age=0" in cookie for cookie in set_cookie)
    assert any(cookie.startswith("garim_auth=") and "Path=/" in cookie for cookie in set_cookie)


def test_logout_deletes_legacy_garim_auth_session_and_cookie(fake_redis):
    token_pair = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")

    response = client.post("/auth/logout", cookies={"garim_auth": token_pair["access_token"]})

    assert response.status_code == 200
    assert redis_store.get_session(token_pair["session_id"]) is None
    set_cookie = response.headers.get_list("set-cookie")
    assert any(cookie.startswith("garim_auth=") and "Max-Age=0" in cookie for cookie in set_cookie)


def test_delete_me_marks_user_deleted_and_deletes_all_user_sessions(monkeypatch, fake_redis):
    first = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    second = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    deleted = []
    monkeypatch.setattr(users, "mark_user_deleted", lambda user_id: deleted.append(user_id) or {
        **active_user(),
        "status": "deleted",
    })

    response = client.delete("/auth/me", cookies={"access_token": first["access_token"]})

    assert response.status_code == 200
    assert deleted == ["00000000-0000-0000-0000-000000000001"]
    assert redis_store.get_session(first["session_id"]) is None
    assert redis_store.get_session(second["session_id"]) is None


def test_suspended_user_cannot_use_protected_auth(monkeypatch, fake_redis):
    token_pair = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    monkeypatch.setattr(users, "get_user_by_id", lambda user_id: {**active_user(), "status": "suspended"})

    with pytest.raises(HTTPException) as exc_info:
        auth.authenticate_access_token(token_pair["access_token"])

    assert exc_info.value.status_code == 401


def test_admin_suspend_user_deletes_all_user_sessions(monkeypatch, fake_redis):
    first = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    second = auth.create_login_session(active_user(), user_agent="pytest", ip_address="127.0.0.1")
    updated = []
    monkeypatch.setattr(users, "update_user_status", lambda user_id, status_value: updated.append((user_id, status_value)) or {
        **active_user(),
        "status": status_value.lower(),
    })

    response = client.patch("/auth/admin/users/00000000-0000-0000-0000-000000000001/status", json={"status": "SUSPENDED"})

    assert response.status_code == 200
    assert updated == [("00000000-0000-0000-0000-000000000001", "SUSPENDED")]
    assert redis_store.get_session(first["session_id"]) is None
    assert redis_store.get_session(second["session_id"]) is None


def test_admin_users_route_updates_role_and_status(monkeypatch):
    updated = []
    monkeypatch.setattr(
        users,
        "update_user_role_and_status",
        lambda user_id, role_value, status_value: updated.append((user_id, role_value, status_value)) or {
            **active_user(),
            "id": user_id,
            "role": role_value.lower(),
            "status": status_value.lower(),
        },
    )

    response = client.patch("/admin/users/user-1", json={"role": "admin", "status": "active"})

    assert response.status_code == 200
    assert updated == [("user-1", "admin", "active")]
    assert response.json()["user"]["role"] == "admin"
