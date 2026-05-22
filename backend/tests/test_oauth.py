from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

import main
from services import oauth, redis_store, users


client = TestClient(main.app, follow_redirects=False)


class FakeRedis:
    def __init__(self):
        self.values = {}

    def setex(self, key, seconds, value):
        self.values[key] = value
        return True

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)
        return 1


def test_oauth_start_redirects_to_provider_with_state(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

    response = client.get("/auth/google/start")

    assert response.status_code == 307
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)

    assert parsed.netloc == "accounts.google.com"
    assert params["client_id"] == ["google-client-id"]
    assert params["redirect_uri"] == ["http://localhost:5000/auth/google/callback"]
    assert params["response_type"] == ["code"]
    assert params["scope"] == ["openid email profile"]
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["select_account"]
    assert params["state"][0]


def test_google_provider_uses_openid_userinfo_endpoint():
    provider = oauth.get_provider("google")

    assert provider.userinfo_url == "https://openidconnect.googleapis.com/v1/userinfo"


def test_normalize_google_user_reads_openid_profile_response():
    user = oauth.normalize_user(
        "google",
        {
            "sub": "google-user-1",
            "email": "user@example.com",
            "name": "Garim User",
            "picture": "https://example.com/avatar.png",
        },
    )

    assert user == {
        "provider": "google",
        "provider_user_id": "google-user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "profile_image_url": "https://example.com/avatar.png",
    }


def test_naver_oauth_start_redirects_to_naver_with_state(monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "naver-client-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "naver-client-secret")
    monkeypatch.setenv("NAVER_REDIRECT_URI", "http://localhost:5000/auth/naver/callback")

    response = client.get("/auth/naver/start")

    assert response.status_code == 307
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)

    assert parsed.netloc == "nid.naver.com"
    assert parsed.path == "/oauth2.0/authorize"
    assert params["client_id"] == ["naver-client-id"]
    assert params["redirect_uri"] == ["http://localhost:5000/auth/naver/callback"]
    assert params["response_type"] == ["code"]
    assert params["state"][0]


def test_normalize_naver_user_reads_profile_response():
    user = oauth.normalize_user(
        "naver",
        {
            "resultcode": "00",
            "message": "success",
            "response": {
                "id": "naver-user-1",
                "email": "naver@example.com",
                "name": "Garim Naver User",
                "profile_image": "https://example.com/naver.png",
            },
        },
    )

    assert user == {
        "provider": "naver",
        "provider_user_id": "naver-user-1",
        "email": "naver@example.com",
        "name": "Garim Naver User",
        "profile_image_url": "https://example.com/naver.png",
    }


def test_oauth_start_reports_missing_provider_config(monkeypatch):
    monkeypatch.delenv("KAKAO_CLIENT_ID", raising=False)
    monkeypatch.delenv("KAKAO_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("KAKAO_REDIRECT_URI", raising=False)

    response = client.get("/auth/kakao/start")

    assert response.status_code == 503
    assert response.json()["message"] == "kakao OAuth 설정이 필요합니다."


def test_oauth_callback_sets_auth_cookie_and_redirects(monkeypatch):
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:3000")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: fake_redis)

    state = oauth.create_oauth_state("google")

    def fake_exchange_code(provider, code, state_value):
        assert provider == "google"
        assert code == "sample-code"
        assert state_value == state
        return {
            "provider": "google",
            "provider_user_id": "google-user-1",
            "email": "user@example.com",
            "name": "Garim User",
        }

    monkeypatch.setattr(oauth, "exchange_code_for_user", fake_exchange_code)
    monkeypatch.setattr(users, "get_or_create_oauth_user", lambda oauth_user: {
        "id": 1,
        "provider": "google",
        "provider_user_id": "google-user-1",
        "provider_email": "oauth-user@example.com",
        "email": "user@example.com",
        "name": "Garim User",
        "profile_image_url": None,
        "role": "USER",
        "status": "ACTIVE",
    })

    response = client.get(f"/auth/google/callback?code=sample-code&state={state}")

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/dashboard?login=success&provider=google"
    cookies = response.headers.get_list("set-cookie")
    assert any(cookie.startswith("access_token=") for cookie in cookies)
    assert any(cookie.startswith("refresh_token=") for cookie in cookies)


def test_oauth_me_reads_access_cookie(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-secret")
    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis_client", lambda: fake_redis)
    from services import auth

    user = {
        "id": 1,
        "provider": "google",
        "provider_user_id": "google-user-1",
        "provider_email": "oauth-user@example.com",
        "email": "user@example.com",
        "name": "Garim User",
        "profile_image_url": None,
        "role": "USER",
        "status": "ACTIVE",
    }
    token_pair = auth.create_login_session(user)
    monkeypatch.setattr(users, "get_user_by_id", lambda user_id: user)

    response = client.get("/auth/me", cookies={"access_token": token_pair["access_token"]})

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["email"] == "user@example.com"
    assert response.json()["user"]["provider_email"] == "oauth-user@example.com"
