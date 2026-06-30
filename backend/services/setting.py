import pandas as pd

from models import setting
from utils.database import engine


def get_setting(user_id):
    with engine.connect() as conn:
        row = setting.get_setting_query(conn, user_id)

    if not row:
        return None

    data = dict(row._mapping)
    
    data["user_id"] = str(data["user_id"])

    data["created_at"] = (
        pd.to_datetime(data["created_at"])
        .strftime("%Y-%m-%d %H:%M:%S")
    )

    if data["updated_at"]:
        data["updated_at"] = (
            pd.to_datetime(data["updated_at"])
            .strftime("%Y-%m-%d %H:%M:%S")
        )

    return data


def get_or_create_setting(user_id):
    with engine.begin() as conn:
        row = setting.get_setting_query(conn, user_id)
        if not row:
            setting.create_setting_query(conn, user_id)
            row = setting.get_setting_query(conn, user_id)

    if not row:
        return None

    result = dict(row._mapping)
    result["user_id"] = str(result["user_id"])

    if result.get("created_at"):
        result["created_at"] = result["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    if result.get("updated_at"):
        result["updated_at"] = result["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

    return result


def update_setting(
    user_id,
    email_notification,
    browser_notification,
    data_usage_consent,
):
    with engine.begin() as conn:

        row = setting.get_setting_query(conn, user_id)


        if not row:
            setting.create_setting_query(
                conn,
                user_id
            )

        setting.update_setting_query(
            conn,
            user_id,
            email_notification,
            browser_notification,
            data_usage_consent,
        )

        row = setting.get_setting_query(
            conn,
            user_id
        )

    result = dict(row._mapping)

    result["user_id"] = str(result["user_id"])


    if result.get("created_at"):
        result["created_at"] = result[
            "created_at"
        ].strftime("%Y-%m-%d %H:%M:%S")

    if result.get("updated_at"):
        result["updated_at"] = result[
            "updated_at"
        ].strftime("%Y-%m-%d %H:%M:%S")

    return result


def get_my_login_histories(user_id, current_session_id=None, limit: int = 5):
    # [한글 주석] 로그인한 유저의 최근 로그인 히스토리를 최대 limit건 만큼 조회하며, 현재 세션 여부도 판별합니다.
    from utils.database import SessionLocal
    from sqlalchemy import text
    from services.admin import _mask_ip, _parse_user_agent_to_device

    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT
                    ulh.login_history_id,
                    ulh.provider,
                    ulh.login_result,
                    ulh.ip_address,
                    ulh.user_agent,
                    ulh.session_id,
                    ulh.logged_in_at
                FROM user_login_histories ulh
                WHERE ulh.user_id = CAST(:user_id AS uuid)
                ORDER BY ulh.logged_in_at DESC, ulh.login_history_id DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "limit": limit}
        ).fetchall()

        items = []
        for row in rows:
            r = row._mapping
            is_current = False
            if r["session_id"] and current_session_id:
                is_current = (str(r["session_id"]).strip().lower() == str(current_session_id).strip().lower())

            items.append({
                "login_history_id": str(r["login_history_id"]),
                "provider": r["provider"] or "",
                "login_result": r["login_result"],
                "ip_address": _mask_ip(r["ip_address"]),
                "browser_device": _parse_user_agent_to_device(r["user_agent"]),
                "is_current_session": is_current,
                "logged_in_at": r["logged_in_at"].isoformat() if r["logged_in_at"] else "",
            })
        return items
    finally:
        db.close()
