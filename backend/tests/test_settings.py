from fastapi.testclient import TestClient

import main
from services import auth, redis_store, setting, users
from tests.test_auth_architecture import FakeRedis, active_user


client = TestClient(main.app)


def auth_cookie(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-secret")
    redis = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: redis)
    monkeypatch.setattr(users, "get_user_by_id", lambda user_id: active_user())
    token_pair = auth.create_login_session(active_user())
    return {"access_token": token_pair["access_token"]}


def test_get_my_settings_uses_authenticated_user(monkeypatch):
    monkeypatch.setattr(setting, "get_or_create_setting", lambda user_id: {
        "user_id": str(user_id),
        "email_notification": True,
        "browser_notification": False,
        "data_usage_consent": True,
    })

    response = client.get("/settings/me", cookies=auth_cookie(monkeypatch))

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "1"
    assert response.json()["data"]["email_notification"] is True
    assert response.json()["data"]["browser_notification"] is False
    assert response.json()["data"]["data_usage_consent"] is True


def test_update_my_settings_persists_authenticated_user_settings(monkeypatch):
    updated = []

    def fake_update(user_id, email_notification, browser_notification, data_usage_consent):
        updated.append((user_id, email_notification, browser_notification, data_usage_consent))
        return {
            "user_id": str(user_id),
            "email_notification": email_notification,
            "browser_notification": browser_notification,
            "data_usage_consent": data_usage_consent,
        }

    monkeypatch.setattr(setting, "update_setting", fake_update)

    response = client.put(
        "/settings/me",
        json={
            "email_notification": False,
            "browser_notification": True,
            "data_usage_consent": False,
        },
        cookies=auth_cookie(monkeypatch),
    )

    assert response.status_code == 200
    assert updated == [(1, False, True, False)]
    assert response.json()["data"]["email_notification"] is False
    assert response.json()["data"]["browser_notification"] is True
    assert response.json()["data"]["data_usage_consent"] is False
