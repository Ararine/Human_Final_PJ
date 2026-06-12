from fastapi import Body, Query, status, Cookie
from fastapi.responses import JSONResponse, StreamingResponse

from services import admin as admin_service
from services import auth as auth_service


def _json_error(error: Exception):
    status_code = 400 if isinstance(error, ValueError) else 500
    return JSONResponse({"message": str(error)}, status_code=status_code)


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


def list_subscription_plans(
    q: str = Query(None),
    include_deleted: bool = Query(False),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        result = admin_service.list_subscription_plans(q, include_deleted, status, page, limit)
        return JSONResponse(
            {
                "data": result["data"],
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "message": "Subscription plans loaded.",
            },
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def create_subscription_plan(payload: dict = Body(...)):
    try:
        data = admin_service.create_subscription_plan(payload)
        return JSONResponse(
            {"data": data, "message": "Subscription plan created."},
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return _json_error(e)


def update_subscription_plan(plan_id: str, payload: dict = Body(...)):
    try:
        data = admin_service.update_subscription_plan(plan_id, payload)
        return JSONResponse(
            {"data": data, "message": "Subscription plan updated."},
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def delete_subscription_plan(plan_id: str):
    try:
        data = admin_service.delete_subscription_plan(plan_id)
        return JSONResponse(
            {"data": data, "message": "Subscription plan deleted."},
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def list_credit_plans(
    q: str = Query(None),
    include_deleted: bool = Query(False),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        result = admin_service.list_credit_plans(q, include_deleted, status, page, limit)
        return JSONResponse(
            {
                "data": result["data"],
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "message": "Credit plans loaded.",
            },
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def create_credit_plan(payload: dict = Body(...)):
    try:
        data = admin_service.create_credit_plan(payload)
        return JSONResponse(
            {"data": data, "message": "Credit plan created."},
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return _json_error(e)


def update_credit_plan(credit_plan_id: str, payload: dict = Body(...)):
    try:
        data = admin_service.update_credit_plan(credit_plan_id, payload)
        return JSONResponse(
            {"data": data, "message": "Credit plan updated."},
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def delete_credit_plan(credit_plan_id: str):
    try:
        data = admin_service.delete_credit_plan(credit_plan_id)
        return JSONResponse(
            {"data": data, "message": "Credit plan deleted."},
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def list_admin_subscriptions(
    q: str = Query(None),
    search_key: str = Query("email"),
    plan_code: str = Query(None),
    subscription_status: str = Query(None),
    auto_renew: str = Query(None),
    cancel_scheduled: str = Query(None),
    billing_failed: str = Query(None),
    scheduled_change: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        result = admin_service.get_admin_subscriptions_list(
            q=q,
            search_key=search_key,
            plan_code=plan_code,
            subscription_status=subscription_status,
            auto_renew=auto_renew,
            cancel_scheduled=cancel_scheduled,
            billing_failed=billing_failed,
            scheduled_change=scheduled_change,
            page=page,
            limit=limit,
        )
        return JSONResponse(
            {
                "data": result["data"],
                "summary": result["summary"],
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "message": "Admin subscriptions loaded successfully.",
            },
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def get_admin_subscription_detail(user_id: str):
    try:
        data = admin_service.get_admin_subscription_detail(user_id)
        return JSONResponse(
            {"data": data, "message": "Admin subscription detail loaded successfully."},
            status_code=200,
        )
    except ValueError as ve:
        return JSONResponse({"message": str(ve)}, status_code=404)
    except Exception as e:
        return _json_error(e)


def list_payments(
    product_type: str = Query(None),
    status: str = Query(None),
    q: str = Query(None),
    search_key: str = Query("email"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        result = admin_service.get_payments_list(
            product_type=product_type,
            status=status,
            q=q,
            search_key=search_key,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )
        return JSONResponse(
            {
                "data": result["data"],
                "summary": result["summary"],
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "message": "Payments list loaded successfully.",
            },
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def get_payment_detail(payment_id: str):
    try:
        data = admin_service.get_payment_detail(payment_id)
        return JSONResponse(
            {"data": data, "message": "Payment detail loaded successfully."},
            status_code=200,
        )
    except ValueError as ve:
        return JSONResponse({"message": str(ve)}, status_code=404)
    except Exception as e:
        return _json_error(e)


def refund_payment(payment_id: str, access_token: str | None = Cookie(default=None)):
    try:
        user_id = None
        if access_token:
            try:
                current_user = auth_service.authenticate_access_token(access_token)
                user_id = current_user.get("id")
            except Exception:
                pass

        data = admin_service.refund_payment(payment_id, user_id)
        return JSONResponse(
            {"data": data, "message": "Payment refunded successfully."},
            status_code=200,
        )
    except ValueError as ve:
        return JSONResponse({"message": str(ve)}, status_code=400)
    except Exception as e:
        return _json_error(e)


def list_login_histories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    period: str = Query(None),
    result: str = Query(None),
    provider: str = Query(None),
    ip: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    search_type: str = Query(None),
    search_keyword: str = Query(None),
):
    # [한글 주석] 로그인 히스토리 목록 데이터를 필터 파라미터와 함께 조회하는 컨트롤러입니다.
    try:
        data = admin_service.get_login_histories_list(
            page=page,
            limit=limit,
            keyword=keyword,
            period=period,
            result=result,
            provider=provider,
            ip=ip,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            search_keyword=search_keyword,
        )
        return JSONResponse(
            {"data": data, "message": "Login histories loaded successfully."},
            status_code=200,
        )
    except Exception as e:
        return _json_error(e)


def get_login_history_detail(login_history_id: str):
    # [한글 주석] 로그인 히스토리 단건의 상세 정보를 조회하는 컨트롤러입니다.
    try:
        data = admin_service.get_login_history_detail(login_history_id)
        return JSONResponse(
            {"data": data, "message": "Login history detail loaded successfully."},
            status_code=200,
        )
    except ValueError as ve:
        return JSONResponse({"message": str(ve)}, status_code=404)
    except Exception as e:
        return _json_error(e)


def export_login_histories_csv(
    keyword: str = Query(None),
    period: str = Query(None),
    result: str = Query(None),
    provider: str = Query(None),
    ip: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    search_type: str = Query(None),
    search_keyword: str = Query(None),
):
    # [한글 주석] 필터링된 로그인 히스토리를 CSV 파일 스트림 형태로 다운로드하는 컨트롤러입니다.
    try:
        generator = admin_service.export_login_histories_csv_stream(
            keyword=keyword,
            period=period,
            result=result,
            provider=provider,
            ip=ip,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            search_keyword=search_keyword,
        )
        headers = {
            "Content-Disposition": 'attachment; filename="garim_login_histories.csv"',
            "Content-Type": "text/csv; charset=utf-8-sig",
        }
        return StreamingResponse(generator, headers=headers, media_type="text/csv")
    except Exception as e:
        return _json_error(e)



