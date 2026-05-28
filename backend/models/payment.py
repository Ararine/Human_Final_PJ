from sqlalchemy import text


def create_payment_query(conn, data):
    return conn.execute(
        text("""
        INSERT INTO payments (
            user_id,
            amount,
            status,
            order_id,
            payment_key,
            order_name,
            method,
            pg_provider,
            paid_at,
            created_at
        )
        VALUES (
            :user_id,
            :amount,
            :status,
            :order_id,
            :payment_key,
            :order_name,
            :method,
            'toss',
            NOW(),
            NOW()
        )
        RETURNING *
        """),
        data,
    ).fetchone()