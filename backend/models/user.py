from sqlalchemy import text


def get_user_by_provider_query(conn, provider, provider_user_id, provider_email=None):
    return conn.execute(
        text(
            """
            SELECT
                u.user_id AS id,
                oa.provider,
                oa.provider_user_id,
                oa.provider_email,
                u.email,
                u.display_name AS name,
                u.profile_image_url,
                u.role,
                u.status
            FROM oauth_accounts oa
            JOIN users u ON u.user_id = oa.user_id
            WHERE oa.provider = :provider
              AND (
                (
                  :provider_email IS NOT NULL
                  AND oa.provider_email IS NOT NULL
                  AND LOWER(oa.provider_email) = LOWER(:provider_email)
                )
                OR oa.provider_user_id = :provider_user_id
              )
            """
        ),
        {
            "provider": provider,
            "provider_user_id": provider_user_id,
            "provider_email": provider_email,
        },
    ).fetchone()


def create_oauth_user_query(conn, oauth_user, role, status):
    created_user = conn.execute(
        text(
            """
            INSERT INTO users (
                email,
                display_name,
                profile_image_url,
                role,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :email,
                :name,
                :profile_image_url,
                :role,
                :status,
                NOW(),
                NOW()
            )
            RETURNING user_id, email, display_name, profile_image_url, role, status
            """
        ),
        {
            "email": oauth_user.get("email"),
            "name": oauth_user.get("name"),
            "profile_image_url": oauth_user.get("profile_image_url"),
            "role": role,
            "status": status,
        },
    ).fetchone()
    user_id = created_user._mapping["user_id"] if hasattr(created_user, "_mapping") else created_user["user_id"]
    conn.execute(
        text(
            """
            INSERT INTO oauth_accounts (
                user_id,
                provider,
                provider_user_id,
                provider_email,
                provider_name,
                linked_at,
                last_used_at
            )
            VALUES (
                :user_id,
                :provider,
                :provider_user_id,
                :provider_email,
                :provider_name,
                NOW(),
                NOW()
            )
            """
        ),
        {
            "user_id": user_id,
            "provider": oauth_user["provider"],
            "provider_user_id": oauth_user["provider_user_id"],
            "provider_email": oauth_user.get("email"),
            "provider_name": oauth_user.get("name"),
        },
    )
    return get_user_by_provider_query(
        conn,
        oauth_user["provider"],
        oauth_user["provider_user_id"],
        oauth_user.get("email"),
    )


def get_user_by_id_query(conn, user_id):
    return conn.execute(
        text(
            """
            SELECT
                u.user_id AS id,
                oa.provider,
                oa.provider_user_id,
                oa.provider_email,
                u.email,
                u.display_name AS name,
                u.profile_image_url,
                u.role,
                u.status
            FROM users u
            LEFT JOIN oauth_accounts oa ON oa.user_id = u.user_id
            WHERE u.user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchone()


def mark_user_deleted_query(conn, user_id, status):
    return conn.execute(
        text(
            """
            UPDATE users
            SET status = :status,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id
            RETURNING user_id AS id, email, display_name AS name, profile_image_url, role, status
            """
        ),
        {"user_id": user_id, "status": status},
    ).fetchone()


def reactivate_user_query(conn, user_id):
    return conn.execute(
        text(
            """
            UPDATE users
            SET status = 'active',
                deleted_at = NULL,
                updated_at = NOW()
            WHERE user_id = :user_id
            RETURNING user_id AS id, email, display_name AS name, profile_image_url, role, status
            """
        ),
        {"user_id": user_id},
    ).fetchone()


def update_user_status_query(conn, user_id, status):
    return conn.execute(
        text(
            """
            UPDATE users
            SET status = :status,
                updated_at = NOW()
            WHERE user_id = :user_id
            RETURNING user_id AS id, email, display_name AS name, profile_image_url, role, status
            """
        ),
        {"user_id": user_id, "status": status},
    ).fetchone()
