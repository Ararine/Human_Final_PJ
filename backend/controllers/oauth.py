import logging

from fastapi import Body, Cookie, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from services import auth, oauth, redis_store, users

logger = logging.getLogger(__name__)
MAX_LOGIN_ATTEMPTS = 5


def start_oauth(provider: str, reregister: bool = Query(False)):
    try:
        authorization_url = oauth.build_authorization_url(provider, force_consent=reregister)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="지원하지 않는 OAuth 제공자입니다.") from exc
    except oauth.OAuthConfigError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    return RedirectResponse(authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def oauth_callback(
    request: Request,
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    attempt_count = redis_store.get_login_attempt(ip)

    if attempt_count >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요."
        )

    if error:
        logger.warning("[oauth] provider=%s ip=%s provider_error=%s", provider, ip, error)
        return redirect_to_frontend()
    if not code or not state:
        logger.warning("[oauth] provider=%s ip=%s error=missing_code_or_state", provider, ip)
        return redirect_to_frontend()

    try:
        oauth_user, state_data, provider_token = oauth.exchange_code_for_user(provider, code, state)
        if state_data.get("reregister"):
            user = users.reactivate_or_create_user(oauth_user)
            logger.info("[oauth] reregister provider=%s email=%s ip=%s", provider, oauth_user.get("email"), ip)
        else:
            user = users.get_or_create_oauth_user(oauth_user)
            if user.get("status") == users.DELETED:
                logger.info("[oauth] deleted_user provider=%s email=%s ip=%s → redirect reregister", provider, oauth_user.get("email"), ip)
                if provider == "kakao":
                    oauth.unlink_kakao_with_user_token(provider_token)
                elif provider == "naver":
                    oauth.unlink_naver_with_user_token(provider_token)
                return redirect_to_reregister(provider)
        token_pair = auth.create_login_session(
            user,
            user_agent=ua,
            ip_address=ip,
        )
    except (oauth.OAuthStateError, oauth.OAuthExchangeError) as exc:
        logger.error("[oauth] provider=%s ip=%s error=%s", provider, ip, exc, exc_info=True)
        return redirect_to_frontend()
    except (KeyError, oauth.OAuthConfigError) as exc:
        logger.error("[oauth] provider=%s ip=%s config_error=%s", provider, ip, exc, exc_info=True)
        return redirect_to_frontend()
    except HTTPException:
        logger.warning("[oauth] provider=%s email=%s ip=%s error=account_inactive", provider, oauth_user.get("email"), ip)
        return redirect_to_frontend()
    except Exception as exc:
        logger.error("[oauth] provider=%s ip=%s unhandled_error=%s", provider, ip, exc, exc_info=True)
        return redirect_to_frontend()

    role = user.get("role", users.USER)
    logger.info("[oauth] login_success provider=%s user_id=%s role=%s ip=%s", provider, user.get("id"), role, ip)
    response = redirect_to_frontend(role=role)
    auth.set_auth_cookies(response, token_pair)
    return response


def get_me(access_token: str | None = Cookie(default=None)):
    user = auth.authenticate_access_token(access_token)
    return {"authenticated": True, "user": user}


def get_status(access_token: str | None = Cookie(default=None)):
    try:
        user = auth.authenticate_access_token(access_token)
    except HTTPException:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


def refresh(refresh_token: str | None = Cookie(default=None)):
    token_pair = auth.refresh_login_session(refresh_token)
    response = JSONResponse({"authenticated": True})
    auth.set_auth_cookies(response, token_pair)
    return response


def logout(
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
    garim_auth: str | None = Cookie(default=None),
):
    auth.delete_session_from_tokens(access_token, refresh_token, garim_auth)
    response = JSONResponse({"authenticated": False})
    auth.delete_auth_cookies(response)
    return response


def delete_me(access_token: str | None = Cookie(default=None)):
    current_user = auth.authenticate_access_token(access_token)
    users.mark_user_deleted(current_user["id"])
    redis_store.delete_user_sessions(current_user["id"])
    response = JSONResponse({"deleted": True})
    auth.delete_auth_cookies(response)
    return response


def update_user_status(user_id: int, payload: dict = Body(...)):
    status_value = payload.get("status", "")
    try:
        user = users.update_user_status(user_id, status_value)
    except users.UserStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user["status"] != users.ACTIVE:
        redis_store.delete_user_sessions(user_id)
    return {"user": user}


def delete_session(session_id: str):
    redis_store.delete_session(session_id)
    return {"deleted": True}


def delete_sessions(access_token: str | None = Cookie(default=None)):
    current_user = auth.authenticate_access_token(access_token)
    redis_store.delete_user_sessions(current_user["id"])
    response = JSONResponse({"deleted": True})
    auth.delete_auth_cookies(response)
    return response


def redirect_to_frontend(role=None):
    base_url = oauth.get_frontend_base_url()
    path = "/admin/monitoring" if role == "admin" else "/dashboard"
    return RedirectResponse(f"{base_url}{path}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def redirect_to_reregister(provider):
    base_url = oauth.get_frontend_base_url()
    return RedirectResponse(
        f"{base_url}/login?reregister=true&provider={provider}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
