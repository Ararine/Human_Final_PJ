import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from secrets import token_urlsafe


AUTH_COOKIE_NAME = "garim_auth"
STATE_TTL_SECONDS = 600
AUTH_COOKIE_TTL_SECONDS = 60 * 60 * 24 * 7

_oauth_states = {}


@dataclass(frozen=True)
class OAuthProvider:
    name: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str
    client_id_env: str
    client_secret_env: str
    redirect_uri_env: str
    user_id_field: str = "id"


PROVIDERS = {
    "kakao": OAuthProvider(
        name="kakao",
        authorize_url="https://kauth.kakao.com/oauth/authorize",
        token_url="https://kauth.kakao.com/oauth/token",
        userinfo_url="https://kapi.kakao.com/v2/user/me",
        scope="profile_nickname account_email",
        client_id_env="KAKAO_CLIENT_ID",
        client_secret_env="KAKAO_CLIENT_SECRET",
        redirect_uri_env="KAKAO_REDIRECT_URI",
    ),
    "google": OAuthProvider(
        name="google",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scope="openid email profile",
        client_id_env="GOOGLE_CLIENT_ID",
        client_secret_env="GOOGLE_CLIENT_SECRET",
        redirect_uri_env="GOOGLE_REDIRECT_URI",
    ),
    "facebook": OAuthProvider(
        name="facebook",
        authorize_url="https://www.facebook.com/v20.0/dialog/oauth",
        token_url="https://graph.facebook.com/v20.0/oauth/access_token",
        userinfo_url="https://graph.facebook.com/me?fields=id,name,email",
        scope="email,public_profile",
        client_id_env="FACEBOOK_CLIENT_ID",
        client_secret_env="FACEBOOK_CLIENT_SECRET",
        redirect_uri_env="FACEBOOK_REDIRECT_URI",
    ),
    "x": OAuthProvider(
        name="x",
        authorize_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        userinfo_url="https://api.twitter.com/2/users/me?user.fields=profile_image_url,username",
        scope="users.read tweet.read offline.access",
        client_id_env="X_CLIENT_ID",
        client_secret_env="X_CLIENT_SECRET",
        redirect_uri_env="X_REDIRECT_URI",
    ),
}


class OAuthConfigError(Exception):
    pass


class OAuthStateError(Exception):
    pass


class OAuthExchangeError(Exception):
    pass


def get_provider(provider):
    if provider not in PROVIDERS:
        raise KeyError(provider)
    return PROVIDERS[provider]


def get_provider_config(provider):
    provider_config = get_provider(provider)
    config = {
        "client_id": os.getenv(provider_config.client_id_env, "").strip(),
        "client_secret": os.getenv(provider_config.client_secret_env, "").strip(),
        "redirect_uri": os.getenv(provider_config.redirect_uri_env, "").strip(),
    }
    if not all(config.values()):
        raise OAuthConfigError(f"{provider} OAuth 설정이 필요합니다.")
    return provider_config, config


def create_oauth_state(provider):
    state = token_urlsafe(32)
    code_verifier = token_urlsafe(64) if provider == "x" else None
    _oauth_states[state] = {
        "provider": provider,
        "code_verifier": code_verifier,
        "expires_at": time.time() + STATE_TTL_SECONDS,
    }
    return state


def consume_oauth_state(provider, state):
    state_data = _oauth_states.pop(state or "", None)
    if not state_data:
        raise OAuthStateError("OAuth state가 유효하지 않습니다.")
    if state_data["provider"] != provider:
        raise OAuthStateError("OAuth state 제공자가 일치하지 않습니다.")
    if state_data["expires_at"] < time.time():
        raise OAuthStateError("OAuth state가 만료되었습니다.")
    return state_data


def build_authorization_url(provider):
    provider_config, config = get_provider_config(provider)
    state = create_oauth_state(provider)
    state_data = _oauth_states[state]
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": provider_config.scope,
        "state": state,
    }

    if provider == "google":
        params["access_type"] = "offline"
        params["prompt"] = "select_account"

    if provider == "x":
        code_challenge = base64_urlencode(
            hashlib.sha256(state_data["code_verifier"].encode("utf-8")).digest()
        )
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    return f"{provider_config.authorize_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user(provider, code, state):
    provider_config, config = get_provider_config(provider)
    state_data = consume_oauth_state(provider, state)
    token_body = {
        "grant_type": "authorization_code",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
        "code": code,
    }

    if provider == "x":
        token_body["code_verifier"] = state_data["code_verifier"]

    token_response = post_form(provider_config.token_url, token_body)
    access_token = token_response.get("access_token")
    if not access_token:
        raise OAuthExchangeError("OAuth access token을 받지 못했습니다.")

    user_response = get_json(provider_config.userinfo_url, access_token)
    return normalize_user(provider, user_response)


def post_form(url, data):
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    return request_json(request)


def get_json(url, access_token):
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    return request_json(request)


def request_json(request):
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OAuthExchangeError(f"OAuth 제공자 응답 오류: {detail}") from exc
    except urllib.error.URLError as exc:
        raise OAuthExchangeError(f"OAuth 제공자 연결 실패: {exc.reason}") from exc


def normalize_user(provider, user_response):
    if provider == "kakao":
        kakao_account = user_response.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        return {
            "provider": provider,
            "provider_user_id": str(user_response.get("id", "")),
            "email": kakao_account.get("email"),
            "name": profile.get("nickname"),
        }

    if provider == "x":
        data = user_response.get("data", {})
        return {
            "provider": provider,
            "provider_user_id": str(data.get("id", "")),
            "email": None,
            "name": data.get("name") or data.get("username"),
        }

    return {
        "provider": provider,
        "provider_user_id": str(user_response.get("id", "")),
        "email": user_response.get("email"),
        "name": user_response.get("name"),
    }


def create_auth_cookie(user):
    expires_at = int(time.time() + AUTH_COOKIE_TTL_SECONDS)
    payload = {
        "provider": user.get("provider"),
        "provider_user_id": user.get("provider_user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "exp": expires_at,
    }
    encoded_payload = base64_urlencode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def read_auth_cookie(cookie_value):
    if not cookie_value or "." not in cookie_value:
        return None
    encoded_payload, signature = cookie_value.rsplit(".", 1)
    if not hmac.compare_digest(sign(encoded_payload), signature):
        return None
    try:
        payload = json.loads(base64_urldecode(encoded_payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def sign(value):
    secret = os.getenv("AUTH_COOKIE_SECRET") or "change-me"
    return base64_urlencode(hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest())


def base64_urlencode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def base64_urldecode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def get_frontend_base_url():
    return os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
