from fastapi import Body, Query, status, Cookie
from fastapi.responses import JSONResponse

from services import admin as admin_service
from services import auth as auth_service


def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str = Query(None),
    status: str = Query(None),
):
    try:
        data = admin_service.get_users_list(page, limit, role, status)
        return JSONResponse(
            {"data": data, "message": "사용자 목록 조회"},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            {"message": str(e)},
            status_code=500,
        )


def get_policy_settings():
    try:
        data = admin_service.get_admin_policies()
        return JSONResponse(
            {"data": data, "message": "Admin policy settings loaded."},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            {"message": str(e)},
            status_code=500,
        )


def update_policy_settings(payload: dict = Body(...), access_token: str | None = Cookie(default=None)):
    try:
        user_id = None
        if access_token:
            try:
                current_user = auth_service.authenticate_access_token(access_token)
                user_id = current_user.get("id")
            except Exception:
                pass

        policies = payload.get("policies", payload)
        data = admin_service.update_admin_policies(policies, updated_by=user_id)
        return JSONResponse(
            {"data": data, "message": "Admin policy settings saved."},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            {"message": str(e)},
            status_code=500,
        )
