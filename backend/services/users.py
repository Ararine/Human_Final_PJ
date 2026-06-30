from models import user as user_model
from utils.database import engine


ACTIVE = "active"
SUSPENDED = "suspended"
DELETED = "deleted"
USER = "user"
VALID_STATUSES = {ACTIVE, SUSPENDED, DELETED}


class UserStatusError(Exception):
    pass


def normalize_user_row(row):
    if row is None:
        return None
    mapping = row._mapping if hasattr(row, "_mapping") else row
    return {
        "id": mapping["id"],
        "provider": mapping.get("provider"),
        "provider_user_id": mapping.get("provider_user_id"),
        "provider_email": mapping.get("provider_email"),
        "email": mapping.get("email"),
        "name": mapping.get("name"),
        "profile_image_url": mapping.get("profile_image_url"),
        "role": mapping.get("role", USER),
        "status": mapping.get("status", ACTIVE),
    }


def get_or_create_oauth_user(oauth_user):
    with engine.begin() as conn:
        existing = user_model.get_user_by_provider_query(
            conn,
            oauth_user["provider"],
            oauth_user["provider_user_id"],
            oauth_user.get("email"),
        )
        if existing:
            user_id = existing._mapping["id"] if hasattr(existing, "_mapping") else existing[0]
            user_model.update_oauth_user_query(conn, user_id, oauth_user)
            existing = user_model.get_user_by_provider_query(
                conn,
                oauth_user["provider"],
                oauth_user["provider_user_id"],
                oauth_user.get("email"),
            )
            return normalize_user_row(existing)

        created = user_model.create_oauth_user_query(conn, oauth_user, USER, ACTIVE)
        return normalize_user_row(created)


def get_user_by_id(user_id):
    with engine.begin() as conn:
        row = user_model.get_user_by_id_query(conn, user_id)
        return normalize_user_row(row)


def reactivate_or_create_user(oauth_user):
    with engine.begin() as conn:
        existing = user_model.get_user_by_provider_query(
            conn,
            oauth_user["provider"],
            oauth_user["provider_user_id"],
            oauth_user.get("email"),
        )
        if existing:
            user_id = existing._mapping["id"] if hasattr(existing, "_mapping") else existing[0]
            user_model.update_oauth_user_query(conn, user_id, oauth_user)
            user_model.reactivate_user_query(conn, user_id)
            existing = user_model.get_user_by_provider_query(
                conn,
                oauth_user["provider"],
                oauth_user["provider_user_id"],
                oauth_user.get("email"),
            )
            return normalize_user_row(existing)
        created = user_model.create_oauth_user_query(conn, oauth_user, USER, ACTIVE)
        return normalize_user_row(created)


def mark_user_deleted(user_id):
    with engine.begin() as conn:
        row = user_model.mark_user_deleted_query(conn, user_id, DELETED)
        return normalize_user_row(row)


def update_user_status(user_id, status_value):
    status_value = status_value.lower()
    if status_value not in VALID_STATUSES:
        raise UserStatusError("Invalid user status.")

    with engine.begin() as conn:
        row = user_model.update_user_status_query(conn, user_id, status_value)
        return normalize_user_row(row)


# 사용자의 역할(role)과 상태(status)를 검증하고 동시 업데이트하는 한국어 주석 서비스 함수
def update_user_role_and_status(user_id, role_value, status_value):
    role_value = role_value.lower()
    status_value = status_value.lower()
    if role_value not in {"user", "admin"}:
        raise ValueError("Invalid user role.")
    if status_value not in VALID_STATUSES:
        raise UserStatusError("Invalid user status.")

    with engine.begin() as conn:
        row = user_model.update_user_role_and_status_query(conn, user_id, role_value, status_value)
        return normalize_user_row(row)


# [한글 주석] 소셜 로그인 시도 시 즉시 DB에 계정을 생성하지 않고, 가입 여부 조회를 위한 단독 쿼리 함수입니다.
def get_oauth_user_only(provider, provider_user_id, email):
    with engine.begin() as conn:
        row = user_model.get_user_by_provider_query(
            conn,
            provider,
            provider_user_id,
            email,
        )
        return normalize_user_row(row)


# [한글 주석] 개인정보 수집 동의가 완료된 신규 회원에 대해 단독으로 회원 계정을 데이터베이스에 인서트하는 함수입니다.
def create_oauth_user(oauth_user):
    with engine.begin() as conn:
        created = user_model.create_oauth_user_query(conn, oauth_user, USER, ACTIVE)
        return normalize_user_row(created)

def get_user_consent(user_id):
    with engine.begin() as conn:
        row = user_model.get_user_consent_query(conn, user_id)
        if row:
            mapping = row._mapping if hasattr(row, "_mapping") else row
            return {"is_agreed": mapping["is_agreed"], "version": mapping["version"]}
        return None


def save_user_consent(user_id, is_agreed, version, ip_address, user_agent):
    with engine.begin() as conn:
        row = user_model.save_user_consent_query(conn, user_id, is_agreed, version, ip_address, user_agent)
        mapping = row._mapping if hasattr(row, "_mapping") else row
        return {"is_agreed": mapping["is_agreed"], "version": mapping["version"]}


def record_login_history(user_id, provider, provider_email, login_result, ip_address, user_agent, session_id):
    data = {
        "user_id": user_id,
        "provider": provider,
        "provider_email": provider_email,
        "login_result": login_result,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "session_id": session_id,
    }
    with engine.begin() as conn:
        user_model.insert_login_history_query(conn, data)


def get_login_histories(user_id, limit=5):
    with engine.begin() as conn:
        rows = user_model.get_user_login_histories_query(conn, user_id, limit)
        results = []
        for row in rows:
            mapping = row._mapping if hasattr(row, "_mapping") else row
            results.append({
                "id": str(mapping["login_history_id"]),
                "provider": mapping["provider"],
                "login_result": mapping["login_result"],
                "ip_address": mapping["ip_address"],
                "user_agent": mapping["user_agent"],
                "session_id": str(mapping["session_id"]) if mapping.get("session_id") else None,
                "logged_in_at": mapping["logged_in_at"].isoformat() if mapping["logged_in_at"] else None
            })
        return results
