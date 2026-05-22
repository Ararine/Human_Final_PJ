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
            row = user_model.reactivate_user_query(conn, existing._mapping["id"])
            return normalize_user_row(row)
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
