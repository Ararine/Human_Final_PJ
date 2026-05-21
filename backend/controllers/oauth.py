from fastapi import Cookie, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse

from services import oauth


def start_oauth(provider: str):
    try:
        authorization_url = oauth.build_authorization_url(provider)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="지원하지 않는 OAuth 제공자입니다.") from exc
    except oauth.OAuthConfigError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    return RedirectResponse(authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def oauth_callback(provider: str, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return redirect_to_frontend(provider, "error", error)
    if not code or not state:
        return redirect_to_frontend(provider, "error", "missing_code_or_state")

    try:
        user = oauth.exchange_code_for_user(provider, code, state)
    except (KeyError, oauth.OAuthConfigError, oauth.OAuthStateError, oauth.OAuthExchangeError):
        return redirect_to_frontend(provider, "error", "oauth_failed")

    response = redirect_to_frontend(provider, "success")
    response.set_cookie(
        key=oauth.AUTH_COOKIE_NAME,
        value=oauth.create_auth_cookie(user),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=oauth.AUTH_COOKIE_TTL_SECONDS,
    )
    return response


def get_me(garim_auth: str | None = Cookie(default=None)):
    user = oauth.read_auth_cookie(garim_auth)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


def logout():
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(oauth.AUTH_COOKIE_NAME)
    return response


def redirect_to_frontend(provider, status_value, error=None):
    base_url = oauth.get_frontend_base_url()
    query = f"login={status_value}&provider={provider}"
    if error:
        query = f"{query}&error={error}"
    return RedirectResponse(f"{base_url}/dashboard?{query}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
