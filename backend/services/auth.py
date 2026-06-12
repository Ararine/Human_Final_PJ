import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Cookie, HTTPException, status
from sqlalchemy import text

from services import redis_store, users


ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
LEGACY_AUTH_COOKIE_NAMES = ("garim_auth",)
ACCESS_TOKEN_TTL_SECONDS = 60 * 15
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7


def get_token_secret():
    return os.getenv("JWT_SECRET") or os.getenv("AUTH_COOKIE_SECRET") or "change-me"


def get_ttl(env_name, default_value):
    try:
        value = int(os.getenv(env_name, str(default_value)))
    except ValueError:
        return default_value
    return value if value > 0 else default_value


def get_access_ttl_seconds():
    return get_ttl("ACCESS_TOKEN_EXPIRE_SECONDS", ACCESS_TOKEN_TTL_SECONDS)


def get_refresh_ttl_seconds():
    return get_ttl("REFRESH_TOKEN_EXPIRE_SECONDS", REFRESH_TOKEN_TTL_SECONDS)


def get_cookie_secure():
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def get_cookie_samesite():
    return os.getenv("COOKIE_SAMESITE", "lax").lower()


def base64_urlencode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def base64_urldecode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign(value):
    return base64_urlencode(
        hmac.new(get_token_secret().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    )


def create_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = base64_urlencode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = base64_urlencode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{sign(signing_input)}"


def decode_jwt(token, expected_type=None, verify_exp=True):
    if not token or token.count(".") != 2:
        raise_auth_error()
    encoded_header, encoded_payload, signature = token.split(".", 2)
    signing_input = f"{encoded_header}.{encoded_payload}"
    if not hmac.compare_digest(sign(signing_input), signature):
        raise_auth_error()
    try:
        payload = json.loads(base64_urldecode(encoded_payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        raise_auth_error()
    if expected_type and payload.get("type") != expected_type:
        raise_auth_error()
    if verify_exp and int(payload.get("exp", 0)) < int(time.time()):
        raise_auth_error()
    return payload


def hash_refresh_token(refresh_token):
    return hmac.new(
        get_token_secret().encode("utf-8"),
        refresh_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_login_session(user, user_agent=None, ip_address=None):
    ensure_active_user(user)
    session_id = str(uuid4())
    refresh_jti = str(uuid4())
    now = int(time.time())
    access_expires_at = now + get_access_ttl_seconds()
    refresh_expires_at = now + get_refresh_ttl_seconds()
    user_id = str(user["id"])
    role = user.get("role") or users.USER

    access_token = create_jwt(
        {
            "sub": user_id,
            "sid": session_id,
            "jti": str(uuid4()),
            "role": role,
            "type": "access",
            "exp": access_expires_at,
        }
    )
    refresh_token = create_jwt(
        {
            "sub": user_id,
            "sid": session_id,
            "jti": refresh_jti,
            "type": "refresh",
            "exp": refresh_expires_at,
        }
    )

    redis_store.save_session(
        session_id,
        {
            "user_id": user_id,
            "refresh_jti": refresh_jti,
            "refresh_hash": hash_refresh_token(refresh_token),
            "provider": user.get("provider"),
            "role": role,
            "user_agent": user_agent,
            "ip": ip_address,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(refresh_expires_at, timezone.utc).isoformat(),
        },
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "session_id": session_id,
        "access_expires_at": access_expires_at,
        "refresh_expires_at": refresh_expires_at,
    }


def refresh_login_session(refresh_token):
    payload = decode_jwt(refresh_token, expected_type="refresh")
    session_id = payload.get("sid")
    session = redis_store.get_session(session_id)
    if not session:
        raise_auth_error()
    if session.get("refresh_jti") != payload.get("jti") or session.get("refresh_hash") != hash_refresh_token(refresh_token):
        redis_store.delete_session(session_id)
        raise_auth_error()

    user = users.get_user_by_id(payload.get("sub"))
    ensure_active_user(user)

    new_refresh_jti = str(uuid4())
    now = int(time.time())
    access_expires_at = now + get_access_ttl_seconds()
    refresh_expires_at = now + get_refresh_ttl_seconds()
    role = user.get("role") or session.get("role") or users.USER
    access_token = create_jwt(
        {
            "sub": str(user["id"]),
            "sid": session_id,
            "jti": str(uuid4()),
            "role": role,
            "type": "access",
            "exp": access_expires_at,
        }
    )
    new_refresh_token = create_jwt(
        {
            "sub": str(user["id"]),
            "sid": session_id,
            "jti": new_refresh_jti,
            "type": "refresh",
            "exp": refresh_expires_at,
        }
    )
    session.update(
        {
            "refresh_jti": new_refresh_jti,
            "refresh_hash": hash_refresh_token(new_refresh_token),
            "role": role,
            "expires_at": datetime.fromtimestamp(refresh_expires_at, timezone.utc).isoformat(),
        }
    )
    redis_store.save_session(session_id, session)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "session_id": session_id,
        "access_expires_at": access_expires_at,
        "refresh_expires_at": refresh_expires_at,
    }


def authenticate_access_token(access_token):
    payload = decode_jwt(access_token, expected_type="access")
    session_id = payload.get("sid")
    session = redis_store.get_session(session_id)
    if not session:
        raise_auth_error()
    if str(session.get("user_id")) != str(payload.get("sub")):
        redis_store.delete_session(session_id)
        raise_auth_error()

    user = users.get_user_by_id(payload.get("sub"))
    ensure_active_user(user)
    return {
        "id": user["id"],
        "provider_email": user.get("provider_email"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role") or session.get("role") or users.USER,
        "status": user.get("status"),
        "session_id": session_id,
    }


def get_current_user(access_token: str | None = Cookie(default=None)):
    return authenticate_access_token(access_token)


def set_auth_cookies(response, token_pair):
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token_pair["access_token"],
        httponly=True,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        path="/",
        max_age=get_access_ttl_seconds(),
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token_pair["refresh_token"],
        httponly=True,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        path="/auth/refresh",
        max_age=get_refresh_ttl_seconds(),
    )
    # [한글 주석] 프론트엔드 자바스크립트가 로그인 여부를 간접 식별할 수 있도록 비-HttpOnly 쿠키를 심어줍니다.
    # 만료 기한은 세션 전체 수명(Refresh Token 만료 기한)과 동일하게 7일로 설정합니다.
    response.set_cookie(
        key="logged_in",
        value="yes",
        httponly=False,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        path="/",
        max_age=get_refresh_ttl_seconds(),
    )


def delete_auth_cookies(response):
    cookie_options = {
        "secure": get_cookie_secure(),
        "httponly": True,
        "samesite": get_cookie_samesite(),
    }
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/", **cookie_options)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth/refresh", **cookie_options)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/", **cookie_options)
    
    # [한글 주석] 로그아웃 시 프론트엔드 인식용 비-HttpOnly 쿠키 logged_in도 함께 지워줍니다.
    non_httponly_options = {
        "secure": get_cookie_secure(),
        "httponly": False,
        "samesite": get_cookie_samesite(),
    }
    response.delete_cookie("logged_in", path="/", **non_httponly_options)

    for cookie_name in LEGACY_AUTH_COOKIE_NAMES:
        response.delete_cookie(cookie_name, path="/", **cookie_options)



def delete_session_from_tokens(access_token=None, refresh_token=None, *extra_tokens):
    for token in (access_token, refresh_token, *extra_tokens):
        try:
            payload = decode_jwt(token, verify_exp=False)
        except HTTPException:
            continue
        session_id = payload.get("sid")
        if session_id:
            redis_store.delete_session(session_id)
            return session_id
    return None


def ensure_active_user(user):
    if not user or str(user.get("status", "")).lower() != users.ACTIVE:
        raise_auth_error()


def raise_auth_error():
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


def record_login_attempt(
    db,
    user_id: str | None,
    provider: str,
    provider_user_id: str | None,
    provider_email: str | None,
    login_result: str,  # success, failed, blocked, deleted, error
    failure_reason: str | None,
    ip_address: str,
    user_agent: str,
    session_id: str | None = None,
    refresh_jti: str | None = None,
    oauth_account_id: str | None = None,
):
    # [한글 주석] 로그인 성공/실패 시도 이력을 DB의 user_login_histories 테이블에 적재합니다.
    try:
        db.execute(
            text("""
                INSERT INTO user_login_histories (
                    user_id,
                    oauth_account_id,
                    provider,
                    provider_user_id,
                    provider_email,
                    login_result,
                    failure_reason,
                    ip_address,
                    user_agent,
                    session_id,
                    refresh_jti,
                    logged_in_at
                )
                VALUES (
                    CAST(:user_id AS uuid),
                    CAST(:oauth_account_id AS uuid),
                    :provider,
                    :provider_user_id,
                    :provider_email,
                    :login_result,
                    :failure_reason,
                    :ip_address,
                    :user_agent,
                    CAST(:session_id AS uuid),
                    CAST(:refresh_jti AS uuid),
                    NOW()
                )
            """),
            {
                "user_id": user_id if user_id else None,
                "oauth_account_id": oauth_account_id if oauth_account_id else None,
                "provider": provider,
                "provider_user_id": provider_user_id,
                "provider_email": provider_email,
                "login_result": login_result,
                "failure_reason": failure_reason,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id if session_id else None,
                "refresh_jti": refresh_jti if refresh_jti else None,
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error("[auth] failed to record login attempt: %s", str(e))
        return

    if login_result != "success" or not user_id:
        return

    try:
        db.execute(
            text("""
                UPDATE users
                SET last_login_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = CAST(:user_id AS uuid)
            """),
            {"user_id": user_id},
        )
        db.commit()
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error("[auth] failed to update last_login_at cache: %s", str(e))
