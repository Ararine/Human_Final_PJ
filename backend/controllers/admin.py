from fastapi import Query, status
from fastapi.responses import JSONResponse

from services import admin as admin_service


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
