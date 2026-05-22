from sqlalchemy import text
from utils.database import SessionLocal


def get_users_list(page: int = 1, limit: int = 20, role: str = None, status_val: str = None):
    db = SessionLocal()
    try:
        offset = (page - 1) * limit
        params = {"limit": limit, "offset": offset}

        conditions = []
        if role:
            conditions.append("u.role = :role")
            params["role"] = role
        if status_val:
            conditions.append("u.status = :status_val")
            params["status_val"] = status_val

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = db.execute(
            text(f"""
                SELECT
                    u.user_id,
                    u.email,
                    u.role,
                    u.status,
                    u.created_at,
                    oa.provider
                FROM users u
                LEFT JOIN oauth_accounts oa ON oa.user_id = u.user_id
                {where}
                ORDER BY u.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

        counts = db.execute(
            text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'active')    AS active,
                    COUNT(*) FILTER (WHERE status = 'suspended') AS suspended,
                    COUNT(*) FILTER (WHERE status = 'deleted')   AS deleted
                FROM users
            """)
        ).fetchone()

        users = []
        for row in rows:
            m = row._mapping
            users.append(
                {
                    "user_id": str(m["user_id"]),
                    "email": m["email"] or "",
                    "role": m["role"],
                    "status": m["status"],
                    "created_at": m["created_at"].strftime("%Y.%m.%d") if m["created_at"] else "",
                    "provider": m["provider"] or "",
                }
            )

        cm = counts._mapping
        return {
            "users": users,
            "total": cm["total"],
            "active": cm["active"],
            "suspended": cm["suspended"],
            "deleted": cm["deleted"],
            "page": page,
            "limit": limit,
        }
    finally:
        db.close()
