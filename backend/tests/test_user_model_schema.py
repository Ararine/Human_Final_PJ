from models import user as user_model


class FakeResult:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConn:
    def __init__(self):
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params or {}))
        if "RETURNING user_id, email, display_name" in str(statement):
            return FakeResult({"user_id": "user-1"})
        return FakeResult()


def test_get_user_by_provider_uses_oauth_accounts_join():
    conn = FakeConn()

    user_model.get_user_by_provider_query(conn, "google", "google-user-1", "user@example.com")

    sql, params = conn.calls[0]
    assert "FROM oauth_accounts oa" in sql
    assert "JOIN users u ON u.user_id = oa.user_id" in sql
    assert "u.user_id AS id" in sql
    assert "u.display_name AS name" in sql
    assert "oa.provider_email" in sql
    assert "LOWER(oa.provider_email) = LOWER(:provider_email)" in sql
    assert "OR oa.provider_user_id = :provider_user_id" in sql
    assert params == {
        "provider": "google",
        "provider_user_id": "google-user-1",
        "provider_email": "user@example.com",
    }


def test_create_oauth_user_inserts_users_then_oauth_accounts():
    conn = FakeConn()

    user_model.create_oauth_user_query(
        conn,
        {
            "provider": "google",
            "provider_user_id": "google-user-1",
            "email": "user@example.com",
            "name": "Garim User",
            "profile_image_url": "https://example.com/avatar.png",
        },
        "user",
        "active",
    )

    insert_user_sql, insert_user_params = conn.calls[0]
    insert_account_sql, insert_account_params = conn.calls[1]
    lookup_sql, lookup_params = conn.calls[2]

    assert "INSERT INTO users" in insert_user_sql
    assert "display_name" in insert_user_sql
    assert "provider_user_id" not in insert_user_sql
    assert insert_user_params["role"] == "user"
    assert insert_user_params["status"] == "active"

    assert "INSERT INTO oauth_accounts" in insert_account_sql
    assert insert_account_params["user_id"] == "user-1"
    assert insert_account_params["provider"] == "google"
    assert insert_account_params["provider_user_id"] == "google-user-1"

    assert "FROM oauth_accounts oa" in lookup_sql
    assert lookup_params == {
        "provider": "google",
        "provider_user_id": "google-user-1",
        "provider_email": "user@example.com",
    }


def test_update_user_status_uses_user_id_column():
    conn = FakeConn()

    user_model.update_user_status_query(conn, "user-1", "suspended")

    sql, params = conn.calls[0]
    assert "WHERE user_id = :user_id" in sql
    assert "RETURNING user_id AS id" in sql
    assert params == {"user_id": "user-1", "status": "suspended"}
