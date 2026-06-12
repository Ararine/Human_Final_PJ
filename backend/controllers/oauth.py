import logging
import time
from urllib.parse import urlparse

from fastapi import Body, Cookie, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from services import auth, oauth, redis_store, users
from utils.database import SessionLocal

logger = logging.getLogger(__name__)


def start_oauth(
    provider: str,
    reregister: bool = Query(False),
    next: str | None = Query(default=None),
):
    try:
        authorization_url = oauth.build_authorization_url(
            provider,
            force_consent=reregister,
            next_path=safe_frontend_path(next),
        )
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
    db = SessionLocal()

    user_id = None
    provider_user_id = None
    provider_email = None
    oauth_account_id = None

    try:
        if error:
            logger.warning("[oauth] provider=%s ip=%s provider_error=%s", provider, ip, error)
            auth.record_login_attempt(
                db=db,
                user_id=None,
                provider=provider,
                provider_user_id=None,
                provider_email=None,
                login_result="failed",
                failure_reason=f"provider_error: {error}",
                ip_address=ip,
                user_agent=ua,
            )
            return redirect_after_login_failure()
        if not code or not state:
            logger.warning("[oauth] provider=%s ip=%s error=missing_code_or_state", provider, ip)
            auth.record_login_attempt(
                db=db,
                user_id=None,
                provider=provider,
                provider_user_id=None,
                provider_email=None,
                login_result="failed",
                failure_reason="missing_code_or_state",
                ip_address=ip,
                user_agent=ua,
            )
            return redirect_after_login_failure()

        try:
            oauth_user, state_data, provider_token = oauth.exchange_code_for_user(provider, code, state)
            provider_user_id = oauth_user.get("provider_user_id")
            provider_email = oauth_user.get("email")

            if state_data.get("reregister"):
                user = users.reactivate_or_create_user(oauth_user)
                logger.info("[oauth] reregister provider=%s email=%s ip=%s", provider, oauth_user.get("email"), ip)
            else:
                # [한글 주석] 로그인 시 즉시 DB 생성하지 않고, 먼저 기존 계정이 가입되어 있는지 조회합니다.
                user = users.get_oauth_user_only(provider, provider_user_id, provider_email)

                if not user:
                    # [한글 주석] 가입하지 않고 이탈 시에도 추적할 수 있게 'consent_required' 이력을 선제 적재합니다.
                    auth.record_login_attempt(
                        db=db,
                        user_id=None,
                        provider=provider,
                        provider_user_id=provider_user_id,
                        provider_email=provider_email,
                        login_result="failed",
                        failure_reason="consent_required",
                        ip_address=ip,
                        user_agent=ua,
                    )
                    # [한글 주석] 개인정보 동의용 단기 유효 임시 토큰을 발행합니다.
                    consent_payload = {
                        "type": "consent",
                        "provider": provider,
                        "provider_user_id": provider_user_id,
                        "email": provider_email,
                        "name": oauth_user.get("name"),
                        "profile_image_url": oauth_user.get("profile_image_url"),
                        "exp": int(time.time()) + 600
                    }
                    consent_token = auth.create_jwt(consent_payload)
                    return redirect_to_consent(consent_token)

                if user:
                    user_id = str(user.get("id"))
                    from sqlalchemy import text
                    oa_row = db.execute(
                        text("SELECT oauth_account_id FROM oauth_accounts WHERE user_id = CAST(:user_id AS uuid) AND provider = :provider"),
                        {"user_id": user_id, "provider": provider}
                    ).fetchone()
                    if oa_row:
                        oauth_account_id = str(oa_row._mapping["oauth_account_id"])

                if user.get("status") == users.DELETED:
                    logger.info("[oauth] deleted_user provider=%s email=%s ip=%s → redirect reregister", provider, oauth_user.get("email"), ip)
                    auth.record_login_attempt(
                        db=db,
                        user_id=user_id,
                        oauth_account_id=oauth_account_id,
                        provider=provider,
                        provider_user_id=provider_user_id,
                        provider_email=provider_email,
                        login_result="deleted",
                        failure_reason="deleted_user",
                        ip_address=ip,
                        user_agent=ua,
                    )
                    if provider == "kakao":
                        oauth.unlink_kakao_with_user_token(provider_token)
                    elif provider == "naver":
                        oauth.unlink_naver_with_user_token(provider_token)
                    return redirect_to_reregister(provider)

            user_id = str(user.get("id"))

            if user.get("status") == users.SUSPENDED:
                auth.record_login_attempt(
                    db=db,
                    user_id=user_id,
                    oauth_account_id=oauth_account_id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_email=provider_email,
                    login_result="blocked",
                    failure_reason="account_suspended",
                    ip_address=ip,
                    user_agent=ua,
                )
                return redirect_after_login_suspended()

            if user.get("status") != users.ACTIVE:
                auth.record_login_attempt(
                    db=db,
                    user_id=user_id,
                    oauth_account_id=oauth_account_id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_email=provider_email,
                    login_result="blocked",
                    failure_reason="account_inactive",
                    ip_address=ip,
                    user_agent=ua,
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive.")

            token_pair = auth.create_login_session(
                user,
                user_agent=ua,
                ip_address=ip,
            )

            auth.record_login_attempt(
                db=db,
                user_id=user_id,
                oauth_account_id=oauth_account_id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=provider_email,
                login_result="success",
                failure_reason=None,
                ip_address=ip,
                user_agent=ua,
                session_id=token_pair.get("session_id"),
            )

        except (oauth.OAuthStateError, oauth.OAuthExchangeError) as exc:
            logger.error("[oauth] provider=%s ip=%s error=%s", provider, ip, exc, exc_info=True)
            auth.record_login_attempt(
                db=db,
                user_id=user_id,
                oauth_account_id=oauth_account_id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=provider_email,
                login_result="failed",
                failure_reason=f"oauth_exchange_error: {str(exc)}",
                ip_address=ip,
                user_agent=ua,
            )
            return redirect_after_login_failure()
        except (KeyError, oauth.OAuthConfigError) as exc:
            logger.error("[oauth] provider=%s ip=%s config_error=%s", provider, ip, exc, exc_info=True)
            auth.record_login_attempt(
                db=db,
                user_id=user_id,
                oauth_account_id=oauth_account_id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=provider_email,
                login_result="error",
                failure_reason=f"config_error: {str(exc)}",
                ip_address=ip,
                user_agent=ua,
            )
            return redirect_after_login_failure()
        except HTTPException:
            logger.warning("[oauth] provider=%s ip=%s error=account_inactive", provider, ip)
            return redirect_after_login_failure()
        except Exception as exc:
            logger.error("[oauth] provider=%s ip=%s unhandled_error=%s", provider, ip, exc, exc_info=True)
            auth.record_login_attempt(
                db=db,
                user_id=user_id,
                oauth_account_id=oauth_account_id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=provider_email,
                login_result="error",
                failure_reason=f"unhandled_error: {str(exc)}",
                ip_address=ip,
                user_agent=ua,
            )
            return redirect_after_login_failure()

        role = user.get("role", users.USER)
        logger.info("[oauth] login_success provider=%s user_id=%s role=%s ip=%s", provider, user.get("id"), role, ip)
        response = redirect_to_frontend(role=role, next_path=state_data.get("next_path"))
        auth.set_auth_cookies(response, token_pair)
        return response
    finally:
        db.close()


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


# 사용자의 역할(role)과 상태(status)를 함께 수정하고, 정지/탈퇴 처리 시 강제 세션 만료를 처리하는 컨트롤러 함수
def update_user_role_and_status(user_id: str, payload: dict = Body(...)):
    role_value = payload.get("role", "")
    status_value = payload.get("status", "")
    try:
        user = users.update_user_role_and_status(user_id, role_value, status_value)
    except (ValueError, users.UserStatusError) as exc:
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


def safe_frontend_path(path: str | None) -> str:
    if not path:
        return "/"
    parsed = urlparse(path)
    if parsed.scheme or parsed.netloc:
        return "/"
    if not path.startswith("/") or path.startswith("//"):
        return "/"
    return path


def redirect_to_frontend(role=None, next_path=None):
    base_url = oauth.get_frontend_base_url()
    path = "/admin/monitoring" if role == "admin" else safe_frontend_path(next_path)
    return RedirectResponse(f"{base_url}{path}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def redirect_after_login_failure():
    return redirect_to_frontend(next_path="/")


def redirect_after_login_suspended():
    return redirect_to_frontend(next_path="/login?error=suspended")


def redirect_to_reregister(provider):
    base_url = oauth.get_frontend_base_url()
    return RedirectResponse(
        f"{base_url}/login?reregister=true&provider={provider}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


# [한글 주석] 최초 가입 사용자를 개인정보 수집 및 약관 동의(Consent) 페이지로 리다이렉트 시킵니다.
def redirect_to_consent(token):
    base_url = oauth.get_frontend_base_url()
    return RedirectResponse(
        f"{base_url}/consent?token={token}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


# [한글 주석] 프론트엔드 동의 페이지에서 동의가 완료되었을 때 호출되며, 비로소 DB에 신규 유저 데이터를 적재하고 로그인 세션을 발행합니다.
def confirm_consent(request: Request, payload: dict = Body(...)):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="토큰 정보가 부재합니다.")

    # [한글 주석] 프론트에서 전달받은 각 약관 항목별 동의 여부 객체 (agreements)
    agreements = payload.get("agreements") or {}

    try:
        # [한글 주석] 임시 가입 신청을 발급할 때 담았던 payload 정보를 복구 검증합니다.
        consent_data = auth.decode_jwt(token, expected_type="consent")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="만료되었거나 유효하지 않은 약관 동의 세션입니다.") from exc

    db = SessionLocal()
    try:
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")

        # [한글 주석] 복구된 소셜 정보를 바탕으로 실제 DB에 회원 데이터를 인서트합니다.
        oauth_user = {
            "provider": consent_data["provider"],
            "provider_user_id": consent_data["provider_user_id"],
            "email": consent_data["email"],
            "name": consent_data.get("name"),
            "profile_image_url": consent_data.get("profile_image_url")
        }
        user = users.create_oauth_user(oauth_user)
        user_id = str(user["id"])

        # [한글 주석] DB 상의 고유 OAuth Account ID를 조회합니다.
        from sqlalchemy import text
        oa_row = db.execute(
            text("SELECT oauth_account_id FROM oauth_accounts WHERE user_id = CAST(:user_id AS uuid) AND provider = :provider"),
            {"user_id": user_id, "provider": consent_data["provider"]}
        ).fetchone()
        oauth_account_id = str(oa_row._mapping["oauth_account_id"]) if oa_row else None

        # [한글 주석] 약관 항목별 동의 이력을 user_consents 테이블에 각각 1행씩 INSERT합니다.
        # consent_type은 프론트 agreements 키를 snake_case로 매핑하며, 버전은 "1.0", 출처는 "signup"으로 고정합니다.
        consent_type_map = [
            ("terms",       bool(agreements.get("terms",       False))),
            ("privacy",     bool(agreements.get("privacy",     False))),
            ("third_party", bool(agreements.get("thirdParty",  False))),
            ("marketing",   bool(agreements.get("marketing",   False))),
        ]
        for consent_type, is_agreed in consent_type_map:
            db.execute(
                text("""
                    INSERT INTO user_consents
                        (user_id, consent_type, is_agreed, version, source, ip_address, user_agent)
                    VALUES
                        (CAST(:user_id AS uuid), :consent_type, :is_agreed, :version, :source, :ip_address, :user_agent)
                """),
                {
                    "user_id":      user_id,
                    "consent_type": consent_type,
                    "is_agreed":    is_agreed,
                    "version":      "1.0",
                    "source":       "signup",
                    "ip_address":   ip,
                    "user_agent":   ua,
                },
            )
        db.commit()

        # [한글 주석] 성공적인 로그인 및 쿠키 세션을 생성합니다.
        token_pair = auth.create_login_session(
            user,
            user_agent=ua,
            ip_address=ip,
        )

        # [한글 주석] 회원 가입 및 로그인 성공 이력을 적재합니다.
        auth.record_login_attempt(
            db=db,
            user_id=user_id,
            oauth_account_id=oauth_account_id,
            provider=consent_data["provider"],
            provider_user_id=consent_data["provider_user_id"],
            provider_email=consent_data["email"],
            login_result="success",
            failure_reason=None,
            ip_address=ip,
            user_agent=ua,
            session_id=token_pair.get("session_id"),
        )

        response = JSONResponse({"success": True})
        auth.set_auth_cookies(response, token_pair)
        return response
    finally:
        db.close()

