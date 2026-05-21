from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

import main
from services import oauth


client = TestClient(main.app, follow_redirects=False)


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
    assert params["state"][0]


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

    response = client.get(f"/auth/google/callback?code=sample-code&state={state}")

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/dashboard?login=success&provider=google"
    assert "garim_auth=" in response.headers["set-cookie"]


def test_oauth_me_reads_signed_cookie(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-secret")
    auth_cookie = oauth.create_auth_cookie(
        {
            "provider": "google",
            "provider_user_id": "google-user-1",
            "email": "user@example.com",
            "name": "Garim User",
        }
    )

    response = client.get("/auth/me", cookies={"garim_auth": auth_cookie})

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["email"] == "user@example.com"
