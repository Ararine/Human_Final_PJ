import json

from sqlalchemy import text
from utils.database import SessionLocal


DEFAULT_ADMIN_POLICIES = {
    "file_processing": {
        "plans": {
            "free":   {"fileSizeLimit": 50,   "maxJobs": 3,  "monthlyQuota": 5,    "resultRetention": 3,  "watermarkRequired": True},
            "pro":    {"fileSizeLimit": 500,  "maxJobs": 10, "monthlyQuota": 50,   "resultRetention": 7,  "watermarkRequired": False},
            "studio": {"fileSizeLimit": 2048, "maxJobs": 30, "monthlyQuota": None, "resultRetention": 30, "watermarkRequired": False},
        },
        "allowedFormats": ["jpg", "jpeg", "png", "webp", "mp4", "mov"],
    },
    "payment": {
        "plans": {
            "free":   {"credits": 5,   "price": 0},
            "pro":    {"credits": 50,  "price": 2900},
            "studio": {"credits": 500, "price": 19800},
        },
        "creditPlans": {
            "credit_100": {"credits": 100, "bonusCredits": 0, "price": 5000},
            "credit_500": {"credits": 500, "bonusCredits": 0, "price": 20000},
        },
    },
    "retention": {
        "plans": {
            "free":   {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
            "pro":    {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
            "studio": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
        },
    },
    "notification": {
        "notifyAbuse": True,
        "queueDelayMinutes": 30,
        "autoReport": True,
    },
}


PLAN_FIELDS = {
    "plan_code",
    "plan_name",
    "badge_label",
    "badge_class",
    "description",
    "monthly_quota",
    "result_retention_days",
    "watermark_required",
    "price_amount",
    "sort_order",
    "status",
    "file_size_limit",
    "max_jobs",
    "auto_delete_original_hours",
    "metadata_retention_days",
    "credits",
}

CREDIT_PLAN_FIELDS = {
    "credit_plan_code",
    "credit_plan_name",
    "price_amount",
    "base_credits",
    "bonus_credits",
    "expires_days",
    "sort_order",
    "status",
}

VALID_MANAGEMENT_STATUSES = {"active", "inactive", "deleted"}
PLAN_PAGE_LIMITS = {5, 10, 20, 50, 100}


def _row_to_dict(row):
    data = {}
    for key, value in row._mapping.items():
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        else:
            data[key] = str(value) if key.endswith("_id") and value is not None else value
    return data


def _clean_payload(payload: dict, allowed_fields: set[str]):
    cleaned = {key: value for key, value in payload.items() if key in allowed_fields}
    if "status" in cleaned and cleaned["status"] not in VALID_MANAGEMENT_STATUSES:
        raise ValueError("status must be one of active, inactive, deleted")
    return cleaned


def _build_filter_clause(code_column: str, name_column: str, q=None, include_deleted=False, status=None):
    conditions = []
    params = {}

    if status:
        conditions.append("status = :status_filter")
        params["status_filter"] = status
    elif not include_deleted:
        conditions.append("status <> 'deleted'")
    if q:
        conditions.append(
            f"(LOWER({code_column}) LIKE :q OR LOWER({name_column}) LIKE :q OR LOWER(status) LIKE :q)"
        )
        params["q"] = f"%{q.lower()}%"

    return ("WHERE " + " AND ".join(conditions)) if conditions else "", params


def _normalize_page_params(page: int = 1, limit: int = 20):
    page = max(int(page or 1), 1)
    limit = int(limit or 20)
    if limit not in PLAN_PAGE_LIMITS:
        limit = 20
    return page, limit, (page - 1) * limit


def _parse_bool_filter(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError("boolean filter must be true or false")


def list_subscription_plans(
    q=None,
    include_deleted: bool = False,
    status: str = None,
    page: int = 1,
    limit: int = 20,
):
    db = SessionLocal()
    try:
        if status and status not in VALID_MANAGEMENT_STATUSES:
            raise ValueError("status must be one of active, inactive, deleted")
        page, limit, offset = _normalize_page_params(page, limit)
        where, params = _build_filter_clause("plan_code", "plan_name", q, include_deleted, status)
        total = db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM plans
                {where}
            """),
            params,
        ).scalar()
        rows = db.execute(
            text(f"""
                SELECT
                    plan_id,
                    plan_code,
                    plan_name,
                    badge_label,
                    badge_class,
                    description,
                    monthly_quota,
                    result_retention_days,
                    watermark_required,
                    price_amount,
                    sort_order,
                    status,
                    file_size_limit,
                    max_jobs,
                    auto_delete_original_hours,
                    metadata_retention_days,
                    credits,
                    created_at,
                    updated_at
                FROM plans
                {where}
                ORDER BY sort_order ASC, created_at ASC
                LIMIT :limit OFFSET :offset
            """),
            {**params, "limit": limit, "offset": offset},
        ).fetchall()
        return {
            "data": [_row_to_dict(row) for row in rows],
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    finally:
        db.close()


def create_subscription_plan(payload: dict):
    data = _clean_payload(payload, PLAN_FIELDS)
    required = {"plan_code", "plan_name", "result_retention_days"}
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    db = SessionLocal()
    try:
        if data.get("status") == "active":
            active_count = db.execute(
                text("SELECT COUNT(*) FROM plans WHERE status = 'active'")
            ).scalar()
            if active_count >= 4:
                raise ValueError("활성화된 구독 플랜 카드는 최대 4개까지만 등록할 수 있습니다.")

        columns = list(data.keys())
        placeholders = [f":{column}" for column in columns]
        row = db.execute(
            text(f"""
                INSERT INTO plans ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
                RETURNING
                    plan_id,
                    plan_code,
                    plan_name,
                    badge_label,
                    badge_class,
                    description,
                    monthly_quota,
                    result_retention_days,
                    watermark_required,
                    price_amount,
                    sort_order,
                    status,
                    file_size_limit,
                    max_jobs,
                    auto_delete_original_hours,
                    metadata_retention_days,
                    credits,
                    created_at,
                    updated_at
            """),
            data,
        ).fetchone()
        db.commit()
        return _row_to_dict(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_subscription_plan(plan_id: str, payload: dict):
    data = _clean_payload(payload, PLAN_FIELDS)
    if not data:
        raise ValueError("no updatable fields provided")

    db = SessionLocal()
    try:
        if data.get("status") == "active":
            active_count = db.execute(
                text("SELECT COUNT(*) FROM plans WHERE status = 'active' AND plan_id <> CAST(:plan_id AS uuid)"),
                {"plan_id": plan_id}
            ).scalar()
            if active_count >= 4:
                raise ValueError("활성화된 구독 플랜 카드는 최대 4개까지만 등록할 수 있습니다.")

        set_clause = ", ".join([f"{field} = :{field}" for field in data])
        params = {**data, "plan_id": plan_id}
        row = db.execute(
            text(f"""
                UPDATE plans
                SET {set_clause},
                    updated_at = NOW()
                WHERE plan_id = CAST(:plan_id AS uuid)
                RETURNING
                    plan_id,
                    plan_code,
                    plan_name,
                    badge_label,
                    badge_class,
                    description,
                    monthly_quota,
                    result_retention_days,
                    watermark_required,
                    price_amount,
                    sort_order,
                    status,
                    file_size_limit,
                    max_jobs,
                    auto_delete_original_hours,
                    metadata_retention_days,
                    credits,
                    created_at,
                    updated_at
            """),
            params,
        ).fetchone()
        if not row:
            raise ValueError("subscription plan not found")
        db.commit()
        return _row_to_dict(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_subscription_plan(plan_id: str):
    return update_subscription_plan(plan_id, {"status": "deleted"})


def list_credit_plans(
    q=None,
    include_deleted: bool = False,
    status: str = None,
    page: int = 1,
    limit: int = 20,
):
    db = SessionLocal()
    try:
        if status and status not in VALID_MANAGEMENT_STATUSES:
            raise ValueError("status must be one of active, inactive, deleted")
        page, limit, offset = _normalize_page_params(page, limit)
        where, params = _build_filter_clause(
            "credit_plan_code", "credit_plan_name", q, include_deleted, status
        )
        total = db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM credit_plans
                {where}
            """),
            params,
        ).scalar()
        rows = db.execute(
            text(f"""
                SELECT
                    credit_plan_id,
                    credit_plan_code,
                    credit_plan_name,
                    price_amount,
                    base_credits,
                    bonus_credits,
                    expires_days,
                    sort_order,
                    status,
                    created_at,
                    updated_at
                FROM credit_plans
                {where}
                ORDER BY sort_order ASC, created_at ASC
                LIMIT :limit OFFSET :offset
            """),
            {**params, "limit": limit, "offset": offset},
        ).fetchall()
        return {
            "data": [_row_to_dict(row) for row in rows],
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    finally:
        db.close()


def create_credit_plan(payload: dict):
    data = _clean_payload(payload, CREDIT_PLAN_FIELDS)
    required = {"credit_plan_code", "credit_plan_name", "price_amount", "base_credits"}
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    db = SessionLocal()
    try:
        if data.get("status") == "active":
            active_count = db.execute(
                text("SELECT COUNT(*) FROM credit_plans WHERE status = 'active'")
            ).scalar()
            if active_count >= 8:
                raise ValueError("활성화된 크레딧 플랜 카드는 최대 8개까지만 등록할 수 있습니다.")

        columns = list(data.keys())
        placeholders = [f":{column}" for column in columns]
        row = db.execute(
            text(f"""
                INSERT INTO credit_plans ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
                RETURNING
                    credit_plan_id,
                    credit_plan_code,
                    credit_plan_name,
                    price_amount,
                    base_credits,
                    bonus_credits,
                    expires_days,
                    sort_order,
                    status,
                    created_at,
                    updated_at
            """),
            data,
        ).fetchone()
        db.commit()
        return _row_to_dict(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_credit_plan(credit_plan_id: str, payload: dict):
    data = _clean_payload(payload, CREDIT_PLAN_FIELDS)
    if not data:
        raise ValueError("no updatable fields provided")

    db = SessionLocal()
    try:
        if data.get("status") == "active":
            active_count = db.execute(
                text("SELECT COUNT(*) FROM credit_plans WHERE status = 'active' AND credit_plan_id <> CAST(:credit_plan_id AS uuid)"),
                {"credit_plan_id": credit_plan_id}
            ).scalar()
            if active_count >= 8:
                raise ValueError("활성화된 크레딧 플랜 카드는 최대 8개까지만 등록할 수 있습니다.")

        set_clause = ", ".join([f"{field} = :{field}" for field in data])
        params = {**data, "credit_plan_id": credit_plan_id}
        row = db.execute(
            text(f"""
                UPDATE credit_plans
                SET {set_clause},
                    updated_at = NOW()
                WHERE credit_plan_id = CAST(:credit_plan_id AS uuid)
                RETURNING
                    credit_plan_id,
                    credit_plan_code,
                    credit_plan_name,
                    price_amount,
                    base_credits,
                    bonus_credits,
                    expires_days,
                    sort_order,
                    status,
                    created_at,
                    updated_at
            """),
            params,
        ).fetchone()
        if not row:
            raise ValueError("credit plan not found")
        db.commit()
        return _row_to_dict(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_credit_plan(credit_plan_id: str):
    return update_credit_plan(credit_plan_id, {"status": "deleted"})


def get_admin_subscriptions_list(
    q=None,
    search_key="email",
    plan_code=None,
    subscription_status=None,
    auto_renew=None,
    cancel_scheduled=None,
    billing_failed=None,
    scheduled_change=None,
    page=1,
    limit=10,
):
    page, limit, offset = _normalize_page_params(page, limit)
    auto_renew = _parse_bool_filter(auto_renew)
    cancel_scheduled = _parse_bool_filter(cancel_scheduled)
    billing_failed = _parse_bool_filter(billing_failed)
    scheduled_change = _parse_bool_filter(scheduled_change)

    conditions = []
    params = {}

    if q:
        params["q"] = f"%{q.lower()}%"
        if search_key == "user_id":
            conditions.append("LOWER(CAST(u.user_id AS text)) LIKE :q")
        elif search_key == "all":
            conditions.append("(LOWER(u.email) LIKE :q OR LOWER(CAST(u.user_id AS text)) LIKE :q)")
        else:
            conditions.append("LOWER(u.email) LIKE :q")

    if plan_code:
        conditions.append("COALESCE(current_plan.plan_code, free_plan.plan_code) = :plan_code")
        params["plan_code"] = plan_code

    if subscription_status:
        if subscription_status == "free":
            conditions.append("current_sub.subscription_id IS NULL")
        else:
            conditions.append("COALESCE(current_sub.status, 'free') = :subscription_status")
            params["subscription_status"] = subscription_status

    if auto_renew is not None:
        if auto_renew:
            conditions.append("current_sub.auto_renew IS TRUE")
        else:
            conditions.append("(current_sub.subscription_id IS NULL OR current_sub.auto_renew IS FALSE)")

    if cancel_scheduled is not None:
        if cancel_scheduled:
            conditions.append("current_sub.cancel_at_period_end IS TRUE")
        else:
            conditions.append("(current_sub.subscription_id IS NULL OR current_sub.cancel_at_period_end IS FALSE)")

    if billing_failed is not None:
        if billing_failed:
            conditions.append("COALESCE(current_sub.billing_status, '') IN ('failed', 'billing_key_missing')")
        else:
            conditions.append("COALESCE(current_sub.billing_status, '') NOT IN ('failed', 'billing_key_missing')")

    if scheduled_change is not None:
        if scheduled_change:
            conditions.append("scheduled_change.plan_change_id IS NOT NULL")
        else:
            conditions.append("scheduled_change.plan_change_id IS NULL")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    base_from = f"""
        FROM users u
        LEFT JOIN LATERAL (
            SELECT
                s.subscription_id,
                s.plan_id,
                s.status,
                s.current_period_start,
                s.current_period_end,
                s.next_billing_at,
                s.auto_renew,
                s.cancel_at_period_end,
                s.cancelled_at,
                s.billing_status,
                s.carried_over_days,
                s.superseded_by_subscription_id,
                s.original_period_end,
                s.upgraded_at,
                p.plan_code,
                p.plan_name,
                p.plan_rank
            FROM subscriptions s
            JOIN plans p ON p.plan_id = s.plan_id
            WHERE s.user_id = u.user_id
              AND s.status = 'active'
              AND (
                  s.current_period_end IS NULL
                  OR s.current_period_end > NOW()
              )
            ORDER BY p.plan_rank DESC, s.current_period_end DESC NULLS LAST, s.created_at DESC
            LIMIT 1
        ) current_sub ON TRUE
        LEFT JOIN plans current_plan ON current_plan.plan_id = current_sub.plan_id
        LEFT JOIN plans free_plan ON free_plan.plan_code = 'free' AND free_plan.status = 'active'
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*) AS active_subscription_count
            FROM subscriptions s
            WHERE s.user_id = u.user_id
              AND s.status = 'active'
              AND (
                  s.current_period_end IS NULL
                  OR s.current_period_end > NOW()
              )
        ) active_counts ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                pc.plan_change_id,
                pc.change_type,
                pc.status,
                pc.effective_at,
                pc.created_at,
                tp.plan_code AS to_plan_code,
                tp.plan_name AS to_plan_name
            FROM subscription_plan_changes pc
            LEFT JOIN plans tp ON tp.plan_id = pc.to_plan_id
            WHERE pc.user_id = u.user_id
              AND pc.status = 'scheduled'
            ORDER BY pc.created_at DESC
            LIMIT 1
        ) scheduled_change ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                s.subscription_id,
                p.plan_code,
                p.plan_name,
                s.current_period_end,
                s.carried_over_days,
                s.superseded_by_subscription_id
            FROM subscriptions s
            JOIN plans p ON p.plan_id = s.plan_id
            WHERE s.user_id = u.user_id
              AND current_sub.subscription_id IS NOT NULL
              AND s.superseded_by_subscription_id = current_sub.subscription_id
            ORDER BY s.current_period_end DESC NULLS LAST, s.created_at DESC
            LIMIT 1
        ) carried_over ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                attempted_at,
                status,
                attempt_type,
                failure_message
            FROM subscription_billing_attempts sba
            WHERE sba.user_id = u.user_id
            ORDER BY attempted_at DESC, created_at DESC
            LIMIT 1
        ) last_attempt ON TRUE
        {where_clause}
    """

    db = SessionLocal()
    try:
        total = db.execute(text(f"SELECT COUNT(*) {base_from}"), params).scalar() or 0

        list_query = f"""
            SELECT
                u.user_id,
                u.email,
                COALESCE(current_plan.plan_code, free_plan.plan_code, 'free') AS current_plan_code,
                COALESCE(current_plan.plan_name, free_plan.plan_name, 'Free') AS current_plan_name,
                current_sub.subscription_id,
                current_sub.status AS subscription_status,
                current_sub.current_period_start,
                current_sub.current_period_end,
                current_sub.next_billing_at,
                current_sub.auto_renew,
                current_sub.cancel_at_period_end,
                current_sub.cancelled_at,
                current_sub.billing_status,
                COALESCE(active_counts.active_subscription_count, 0) AS active_subscription_count,
                carried_over.subscription_id AS carried_over_subscription_id,
                carried_over.plan_code AS carried_over_plan_code,
                carried_over.plan_name AS carried_over_plan_name,
                carried_over.current_period_end AS carried_over_period_end,
                carried_over.carried_over_days,
                scheduled_change.plan_change_id,
                scheduled_change.change_type AS scheduled_change_type,
                scheduled_change.status AS scheduled_change_status,
                scheduled_change.effective_at AS scheduled_change_effective_at,
                scheduled_change.to_plan_code AS scheduled_to_plan_code,
                scheduled_change.to_plan_name AS scheduled_to_plan_name,
                last_attempt.attempted_at AS last_attempted_at,
                last_attempt.status AS last_attempt_status,
                last_attempt.attempt_type AS last_attempt_type,
                last_attempt.failure_message AS last_failure_reason
            {base_from}
            ORDER BY
                CASE
                    WHEN COALESCE(current_sub.billing_status, '') IN ('failed', 'billing_key_missing') THEN 0
                    ELSE 1
                END,
                u.created_at DESC,
                u.user_id DESC
            LIMIT :limit OFFSET :offset
        """
        rows = db.execute(text(list_query), {**params, "limit": limit, "offset": offset}).fetchall()

        summary_query = """
            SELECT
                COUNT(*) AS total_users,
                COUNT(*) FILTER (WHERE current_sub.subscription_id IS NOT NULL) AS paid_users,
                COUNT(*) FILTER (WHERE COALESCE(current_sub.billing_status, '') IN ('failed', 'billing_key_missing')) AS billing_failed_users,
                COUNT(*) FILTER (WHERE scheduled_change.plan_change_id IS NOT NULL) AS scheduled_change_users
            """ + base_from
        summary_row = db.execute(text(summary_query), params).fetchone()
        summary_map = summary_row._mapping if summary_row else {}

        data = []
        for row in rows:
            m = row._mapping
            data.append({
                "user_id": str(m["user_id"]),
                "email": m["email"] or "",
                "current_plan_code": m["current_plan_code"] or "free",
                "current_plan_name": m["current_plan_name"] or "Free",
                "current_subscription": {
                    "subscription_id": str(m["subscription_id"]) if m["subscription_id"] else None,
                    "status": m["subscription_status"] or "free",
                    "current_period_start": m["current_period_start"].isoformat() if m["current_period_start"] else None,
                    "current_period_end": m["current_period_end"].isoformat() if m["current_period_end"] else None,
                    "next_billing_at": m["next_billing_at"].isoformat() if m["next_billing_at"] else None,
                    "auto_renew": bool(m["auto_renew"]) if m["subscription_id"] else False,
                    "cancel_at_period_end": bool(m["cancel_at_period_end"]) if m["subscription_id"] else False,
                    "cancelled_at": m["cancelled_at"].isoformat() if m["cancelled_at"] else None,
                    "billing_status": m["billing_status"] or None,
                },
                "active_subscription_count": int(m["active_subscription_count"] or 0),
                "carried_over_subscription": {
                    "subscription_id": str(m["carried_over_subscription_id"]) if m["carried_over_subscription_id"] else None,
                    "plan_code": m["carried_over_plan_code"],
                    "plan_name": m["carried_over_plan_name"],
                    "current_period_end": m["carried_over_period_end"].isoformat() if m["carried_over_period_end"] else None,
                    "carried_over_days": int(m["carried_over_days"] or 0),
                } if m["carried_over_subscription_id"] else None,
                "scheduled_plan_change": {
                    "plan_change_id": str(m["plan_change_id"]) if m["plan_change_id"] else None,
                    "change_type": m["scheduled_change_type"],
                    "status": m["scheduled_change_status"],
                    "effective_at": m["scheduled_change_effective_at"].isoformat() if m["scheduled_change_effective_at"] else None,
                    "to_plan_code": m["scheduled_to_plan_code"],
                    "to_plan_name": m["scheduled_to_plan_name"],
                } if m["plan_change_id"] else None,
                "latest_billing_attempt": {
                    "attempted_at": m["last_attempted_at"].isoformat() if m["last_attempted_at"] else None,
                    "status": m["last_attempt_status"],
                    "attempt_type": m["last_attempt_type"],
                    "failure_reason": m["last_failure_reason"],
                } if m["last_attempted_at"] else None,
            })

        return {
            "data": data,
            "summary": {
                "total_users": int(summary_map.get("total_users") or 0),
                "paid_users": int(summary_map.get("paid_users") or 0),
                "billing_failed_users": int(summary_map.get("billing_failed_users") or 0),
                "scheduled_change_users": int(summary_map.get("scheduled_change_users") or 0),
            },
            "total": total,
            "page": page,
            "limit": limit,
        }
    finally:
        db.close()


def get_admin_subscription_detail(user_id: str):
    db = SessionLocal()
    try:
        current_query = """
            SELECT
                u.user_id,
                u.email,
                cs.subscription_id,
                cs.status AS subscription_status,
                cs.current_period_start,
                cs.current_period_end,
                cs.next_billing_at,
                cs.auto_renew,
                cs.cancel_at_period_end,
                cs.cancelled_at,
                cs.billing_status,
                cs.carried_over_days,
                cs.superseded_by_subscription_id,
                cp.plan_code AS current_plan_code,
                cp.plan_name AS current_plan_name,
                fp.plan_code AS free_plan_code,
                fp.plan_name AS free_plan_name
            FROM users u
            LEFT JOIN LATERAL (
                SELECT s.*
                FROM subscriptions s
                JOIN plans p ON p.plan_id = s.plan_id
                WHERE s.user_id = u.user_id
                  AND s.status = 'active'
                  AND (
                      s.current_period_end IS NULL
                      OR s.current_period_end > NOW()
                  )
                ORDER BY p.plan_rank DESC, s.current_period_end DESC NULLS LAST, s.created_at DESC
                LIMIT 1
            ) cs ON TRUE
            LEFT JOIN plans cp ON cp.plan_id = cs.plan_id
            LEFT JOIN plans fp ON fp.plan_code = 'free' AND fp.status = 'active'
            WHERE u.user_id = CAST(:user_id AS uuid)
        """
        current_row = db.execute(text(current_query), {"user_id": user_id}).fetchone()
        if not current_row:
            raise ValueError("user not found")

        current = current_row._mapping

        active_query = """
            SELECT
                s.subscription_id,
                s.status,
                s.current_period_start,
                s.current_period_end,
                s.next_billing_at,
                s.auto_renew,
                s.cancel_at_period_end,
                s.cancelled_at,
                s.billing_status,
                s.carried_over_days,
                s.superseded_by_subscription_id,
                s.original_period_end,
                s.upgraded_at,
                s.created_at,
                p.plan_id,
                p.plan_code,
                p.plan_name
            FROM subscriptions s
            JOIN plans p ON p.plan_id = s.plan_id
            WHERE s.user_id = CAST(:user_id AS uuid)
              AND s.status = 'active'
            ORDER BY p.plan_rank DESC, s.current_period_end DESC NULLS LAST, s.created_at DESC
        """
        active_rows = db.execute(text(active_query), {"user_id": user_id}).fetchall()

        attempts_query = """
            SELECT
                billing_attempt_id,
                subscription_id,
                plan_change_id,
                attempt_type,
                status,
                amount,
                payment_id,
                failure_message,
                attempted_at
            FROM subscription_billing_attempts
            WHERE user_id = CAST(:user_id AS uuid)
            ORDER BY attempted_at DESC, created_at DESC
            LIMIT 30
        """
        attempt_rows = db.execute(text(attempts_query), {"user_id": user_id}).fetchall()

        changes_query = """
            SELECT
                pc.plan_change_id,
                pc.change_type,
                pc.status,
                pc.apply_timing,
                pc.effective_at,
                pc.applied_at,
                pc.created_at,
                pc.from_subscription_id,
                pc.to_subscription_id,
                fp.plan_code AS from_plan_code,
                fp.plan_name AS from_plan_name,
                tp.plan_code AS to_plan_code,
                tp.plan_name AS to_plan_name
            FROM subscription_plan_changes pc
            LEFT JOIN subscriptions fs ON fs.subscription_id = pc.from_subscription_id
            LEFT JOIN plans fp ON fp.plan_id = fs.plan_id
            LEFT JOIN plans tp ON tp.plan_id = pc.to_plan_id
            WHERE pc.user_id = CAST(:user_id AS uuid)
            ORDER BY pc.created_at DESC
            LIMIT 30
        """
        change_rows = db.execute(text(changes_query), {"user_id": user_id}).fetchall()

        active_subscriptions = []
        for row in active_rows:
            m = row._mapping
            active_subscriptions.append({
                "subscription_id": str(m["subscription_id"]),
                "plan_id": str(m["plan_id"]),
                "plan_code": m["plan_code"],
                "plan_name": m["plan_name"],
                "status": m["status"],
                "current_period_start": m["current_period_start"].isoformat() if m["current_period_start"] else None,
                "current_period_end": m["current_period_end"].isoformat() if m["current_period_end"] else None,
                "next_billing_at": m["next_billing_at"].isoformat() if m["next_billing_at"] else None,
                "auto_renew": bool(m["auto_renew"]),
                "cancel_at_period_end": bool(m["cancel_at_period_end"]),
                "cancelled_at": m["cancelled_at"].isoformat() if m["cancelled_at"] else None,
                "billing_status": m["billing_status"],
                "carried_over_days": int(m["carried_over_days"] or 0),
                "superseded_by_subscription_id": str(m["superseded_by_subscription_id"]) if m["superseded_by_subscription_id"] else None,
                "original_period_end": m["original_period_end"].isoformat() if m["original_period_end"] else None,
                "upgraded_at": m["upgraded_at"].isoformat() if m["upgraded_at"] else None,
                "created_at": m["created_at"].isoformat() if m["created_at"] else None,
            })

        billing_attempts = []
        for row in attempt_rows:
            m = row._mapping
            billing_attempts.append({
                "attempt_id": str(m["billing_attempt_id"]),
                "subscription_id": str(m["subscription_id"]) if m["subscription_id"] else None,
                "plan_change_id": str(m["plan_change_id"]) if m["plan_change_id"] else None,
                "attempt_type": m["attempt_type"],
                "status": m["status"],
                "amount": m["amount"],
                "payment_id": str(m["payment_id"]) if m["payment_id"] else None,
                "failure_reason": m["failure_message"],
                "attempted_at": m["attempted_at"].isoformat() if m["attempted_at"] else None,
            })

        plan_changes = []
        for row in change_rows:
            m = row._mapping
            plan_changes.append({
                "plan_change_id": str(m["plan_change_id"]),
                "change_type": m["change_type"],
                "status": m["status"],
                "apply_timing": m["apply_timing"],
                "effective_at": m["effective_at"].isoformat() if m["effective_at"] else None,
                "applied_at": m["applied_at"].isoformat() if m["applied_at"] else None,
                "created_at": m["created_at"].isoformat() if m["created_at"] else None,
                "from_subscription_id": str(m["from_subscription_id"]) if m["from_subscription_id"] else None,
                "to_subscription_id": str(m["to_subscription_id"]) if m["to_subscription_id"] else None,
                "from_plan_code": m["from_plan_code"],
                "from_plan_name": m["from_plan_name"],
                "to_plan_code": m["to_plan_code"],
                "to_plan_name": m["to_plan_name"],
            })

        return {
            "user": {
                "user_id": str(current["user_id"]),
                "email": current["email"] or "",
            },
            "current_applied_plan": {
                "plan_code": current["current_plan_code"] or current["free_plan_code"] or "free",
                "plan_name": current["current_plan_name"] or current["free_plan_name"] or "Free",
                "subscription_id": str(current["subscription_id"]) if current["subscription_id"] else None,
                "subscription_status": current["subscription_status"] or "free",
                "current_period_start": current["current_period_start"].isoformat() if current["current_period_start"] else None,
                "current_period_end": current["current_period_end"].isoformat() if current["current_period_end"] else None,
                "next_billing_at": current["next_billing_at"].isoformat() if current["next_billing_at"] else None,
                "auto_renew": bool(current["auto_renew"]) if current["subscription_id"] else False,
                "cancel_at_period_end": bool(current["cancel_at_period_end"]) if current["subscription_id"] else False,
                "cancelled_at": current["cancelled_at"].isoformat() if current["cancelled_at"] else None,
                "billing_status": current["billing_status"],
                "carried_over_days": int(current["carried_over_days"] or 0),
                "superseded_by_subscription_id": str(current["superseded_by_subscription_id"]) if current["superseded_by_subscription_id"] else None,
            },
            "active_subscriptions": active_subscriptions,
            "billing_attempts": billing_attempts,
            "plan_changes": plan_changes,
        }
    finally:
        db.close()


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


def get_admin_policies():
    db = SessionLocal()
    try:
        # 1. Load default policies as base structure
        policies = {key: value.copy() if isinstance(value, dict) else value for key, value in DEFAULT_ADMIN_POLICIES.items()}
        
        # Deep copy plans sub-dictionaries to avoid mutating global DEFAULT_ADMIN_POLICIES
        for group in ["file_processing", "payment", "retention"]:
            if group in policies and "plans" in policies[group]:
                policies[group]["plans"] = {
                    pk: pv.copy() for pk, pv in policies[group]["plans"].items()
                }

        # 2. Query admin_policy_settings for plan-independent policies (e.g. allowedFormats, notification)
        rows = db.execute(
            text("""
                SELECT policy_key, policy_value
                FROM admin_policy_settings
                ORDER BY policy_key
            """)
        ).fetchall()

        for row in rows:
            item = row._mapping
            db_val = item["policy_value"]
            if item["policy_key"] in policies:
                if isinstance(db_val, dict):
                    for k, v in db_val.items():
                        # Do not overwrite the 'plans' key with db_val since we fetch plans from plans table
                        if k != "plans":
                            policies[item["policy_key"]][k] = v
                else:
                    policies[item["policy_key"]] = db_val

        # 3. Query plans table to populate plan-dependent policies
        plan_rows = db.execute(
            text("""
                SELECT
                    plan_code,
                    plan_name,
                    badge_label,
                    badge_class,
                    description,
                    file_size_limit,
                    max_jobs,
                    monthly_quota,
                    result_retention_days,
                    price_amount,
                    watermark_required,
                    auto_delete_original_hours,
                    metadata_retention_days,
                    credits,
                    status,
                    sort_order
                FROM plans
                WHERE status = 'active'
                ORDER BY sort_order ASC, created_at ASC
            """)
        ).fetchall()

        for prow in plan_rows:
            pm = prow._mapping
            pcode = pm["plan_code"].lower()
            common = {
                "name": pm["plan_name"],
                "badgeLabel": pm["badge_label"],
                "badgeClass": pm["badge_class"],
                "description": pm["description"],
                "sortOrder": pm["sort_order"],
                "status": pm["status"],
            }
            policies["file_processing"]["plans"][pcode] = {
                **common,
                "fileSizeLimit": pm["file_size_limit"],
                "maxJobs": pm["max_jobs"],
                "monthlyQuota": pm["monthly_quota"],
                "resultRetention": pm["result_retention_days"],
                "watermarkRequired": pm["watermark_required"],
            }
            policies["payment"]["plans"][pcode] = {
                **common,
                "credits": pm["credits"],
                "price": pm["price_amount"],
            }
            policies["retention"]["plans"][pcode] = {
                **common,
                "autoDeleteOriginalHours": pm["auto_delete_original_hours"],
                "metadataRetentionDays": pm["metadata_retention_days"],
            }

        # 4. Query credit_plans table to populate creditPlans
        credit_plan_rows = db.execute(
            text("""
                SELECT
                    credit_plan_code,
                    credit_plan_name,
                    base_credits,
                    bonus_credits,
                    expires_days,
                    price_amount,
                    status,
                    sort_order
                FROM credit_plans
                WHERE status = 'active'
                ORDER BY sort_order ASC, created_at ASC
            """)
        ).fetchall()

        credit_plans_map = {}
        for crow in credit_plan_rows:
            cm = crow._mapping
            credit_plans_map[cm["credit_plan_code"]] = {
                "name": cm["credit_plan_name"],
                "credits": cm["base_credits"],
                "bonusCredits": cm["bonus_credits"],
                "expiresDays": cm["expires_days"],
                "price": cm["price_amount"],
                "status": cm["status"],
                "sortOrder": cm["sort_order"],
            }

        if credit_plans_map:
            policies["payment"]["creditPlans"] = credit_plans_map

        return policies
    finally:
        db.close()


def update_admin_policies(policies: dict, updated_by=None):
    db = SessionLocal()
    try:
        # 1. Extract and update plan-dependent policies in the plans table
        file_processing_plans = policies.get("file_processing", {}).get("plans", {})
        payment_plans = policies.get("payment", {}).get("plans", {})
        retention_plans = policies.get("retention", {}).get("plans", {})

        all_plan_codes = set(file_processing_plans.keys()) | set(payment_plans.keys()) | set(retention_plans.keys())
        for plan_code in all_plan_codes:
            fp_plan = file_processing_plans.get(plan_code, {})
            pay_plan = payment_plans.get(plan_code, {})
            ret_plan = retention_plans.get(plan_code, {})

            db.execute(
                text("""
                    UPDATE plans
                    SET file_size_limit = :file_size_limit,
                        max_jobs = :max_jobs,
                        monthly_quota = :monthly_quota,
                        result_retention_days = :result_retention_days,
                        price_amount = :price_amount,
                        auto_delete_original_hours = :auto_delete_original_hours,
                        metadata_retention_days = :metadata_retention_days,
                        credits = :credits,
                        watermark_required = :watermark_required
                    WHERE plan_code = :plan_code
                """),
                {
                    "plan_code": plan_code,
                    "file_size_limit": fp_plan.get("fileSizeLimit"),
                    "max_jobs": fp_plan.get("maxJobs"),
                    "monthly_quota": fp_plan.get("monthlyQuota"),
                    "result_retention_days": fp_plan.get("resultRetention"),
                    "price_amount": pay_plan.get("price"),
                    "auto_delete_original_hours": ret_plan.get("autoDeleteOriginalHours"),
                    "metadata_retention_days": ret_plan.get("metadataRetentionDays"),
                    "credits": pay_plan.get("credits"),
                    "watermark_required": fp_plan.get("watermarkRequired")
                }
            )

        # 2. Update admin_policy_settings for plan-independent policies
        # Save file_processing (allowedFormats only)
        file_proc_val = {
            "allowedFormats": policies.get("file_processing", {}).get("allowedFormats", [])
        }
        db.execute(
            text("""
                INSERT INTO admin_policy_settings (policy_key, policy_value, updated_by, created_at, updated_at)
                VALUES (:policy_key, CAST(:policy_value AS jsonb), :updated_by, now(), now())
                ON CONFLICT (policy_key) DO UPDATE
                SET policy_value = EXCLUDED.policy_value,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = now()
            """),
            {
                "policy_key": "file_processing",
                "policy_value": json.dumps(file_proc_val, ensure_ascii=False),
                "updated_by": updated_by,
            }
        )

        # Save notification if provided
        notify_val = policies.get("notification", {})
        if notify_val:
            db.execute(
                text("""
                    INSERT INTO admin_policy_settings (policy_key, policy_value, updated_by, created_at, updated_at)
                    VALUES (:policy_key, CAST(:policy_value AS jsonb), :updated_by, now(), now())
                    ON CONFLICT (policy_key) DO UPDATE
                    SET policy_value = EXCLUDED.policy_value,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = now()
                """),
                {
                    "policy_key": "notification",
                    "policy_value": json.dumps(notify_val, ensure_ascii=False),
                    "updated_by": updated_by,
                }
            )

        # 3. Write into audit_logs table
        db.execute(
            text("""
                INSERT INTO audit_logs (
                    actor_user_id,
                    actor_type,
                    action,
                    target_type,
                    detail,
                    created_at
                )
                VALUES (
                    :actor_user_id,
                    'admin',
                    'update_policy',
                    'policy',
                    CAST(:detail AS jsonb),
                    now()
                )
            """),
            {
                "actor_user_id": updated_by,
                "detail": json.dumps(policies, ensure_ascii=False)
            }
        )

        db.commit()
        return get_admin_policies()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_payments_list(
    product_type: str = None,
    status: str = None,
    q: str = None,
    search_key: str = "email",
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    limit: int = 10,
):
    db = SessionLocal()
    try:
        conditions = []
        params = {}

        if product_type and product_type != "all":
            conditions.append("p.product_type = :product_type")
            params["product_type"] = product_type

        if status and status != "all":
            conditions.append("p.status = :status")
            params["status"] = status

        if date_from:
            conditions.append("p.created_at >= CAST(:date_from AS date)")
            params["date_from"] = date_from

        if date_to:
            conditions.append("p.created_at < CAST(:date_to AS date) + INTERVAL '1 day'")
            params["date_to"] = date_to

        if q:
            val = f"%{q.lower()}%"
            params["q"] = val
            if search_key == "email":
                conditions.append("LOWER(u.email) LIKE :q")
            elif search_key == "payment_id":
                conditions.append("CAST(p.payment_id AS varchar) LIKE :q")
            elif search_key == "user_id":
                conditions.append("CAST(p.user_id AS varchar) LIKE :q")
            elif search_key == "product_name":
                conditions.append("(LOWER(p.order_name) LIKE :q OR LOWER(pl.plan_name) LIKE :q OR LOWER(cp.credit_plan_name) LIKE :q)")
            else:
                conditions.append(
                    "(LOWER(u.email) LIKE :q OR CAST(p.payment_id AS varchar) LIKE :q OR CAST(p.user_id AS varchar) LIKE :q OR LOWER(p.order_name) LIKE :q)"
                )

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        total_query = f"""
            SELECT COUNT(*)
            FROM payments p
            LEFT JOIN users u ON u.user_id = p.user_id
            LEFT JOIN plans pl ON pl.plan_id = p.plan_id
            LEFT JOIN credit_plans cp ON cp.credit_plan_id = p.credit_plan_id
            {where_clause}
        """
        total = db.execute(text(total_query), params).scalar() or 0

        offset = (page - 1) * limit
        list_query = f"""
            SELECT
                p.payment_id,
                p.paid_at,
                p.requested_at,
                p.created_at,
                p.user_id,
                u.email AS user_email,
                p.product_type,
                COALESCE(p.order_name, pl.plan_name, cp.credit_plan_name) AS product_name,
                p.amount,
                p.status,
                p.payment_method,
                p.pg_provider
            FROM payments p
            LEFT JOIN users u ON u.user_id = p.user_id
            LEFT JOIN plans pl ON pl.plan_id = p.plan_id
            LEFT JOIN credit_plans cp ON cp.credit_plan_id = p.credit_plan_id
            {where_clause}
            ORDER BY p.created_at DESC, p.payment_id DESC
            LIMIT :limit OFFSET :offset
        """
        rows = db.execute(text(list_query), {**params, "limit": limit, "offset": offset}).fetchall()

        summary_query = """
            SELECT
                COALESCE(SUM(amount) FILTER (WHERE status = 'success' AND created_at >= CURRENT_DATE), 0) AS today_amount,
                COUNT(*) FILTER (WHERE status = 'success') AS success_count,
                COUNT(*) FILTER (WHERE status IN ('refunded', 'canceled')) AS refund_count,
                COUNT(*) FILTER (WHERE product_type = 'credit' AND status = 'success') AS credit_count
            FROM payments
        """
        sum_row = db.execute(text(summary_query)).fetchone()
        sm = sum_row._mapping if sum_row else {}

        summary = {
            "today_amount": int(sm.get("today_amount") or 0),
            "success_count": int(sm.get("success_count") or 0),
            "refund_count": int(sm.get("refund_count") or 0),
            "credit_count": int(sm.get("credit_count") or 0),
        }

        data = []
        for row in rows:
            m = row._mapping
            data.append({
                "payment_id": str(m["payment_id"]),
                "paid_at": m["paid_at"].isoformat() if m["paid_at"] else (m["created_at"].isoformat() if m["created_at"] else ""),
                "requested_at": m["requested_at"].isoformat() if m["requested_at"] else "",
                "user_id": str(m["user_id"]),
                "user_email": m["user_email"] or "",
                "product_type": m["product_type"],
                "product_name": m["product_name"] or "",
                "amount": m["amount"],
                "status": m["status"],
                "payment_method": m["payment_method"] or "",
                "pg_provider": m["pg_provider"] or "",
            })

        return {
            "data": data,
            "summary": summary,
            "total": total,
            "page": page,
            "limit": limit,
        }
    finally:
        db.close()


def get_payment_detail(payment_id: str):
    db = SessionLocal()
    try:
        query = """
            SELECT
                p.payment_id,
                p.paid_at,
                p.requested_at,
                p.approved_at,
                p.refunded_at,
                p.created_at,
                p.user_id,
                u.email AS user_email,
                p.product_type,
                COALESCE(p.order_name, pl.plan_name, cp.credit_plan_name) AS product_name,
                p.amount,
                p.balance_amount,
                p.status,
                p.payment_method,
                p.pg_provider,
                p.subscription_id,
                (SELECT cl.ledger_id FROM credit_ledger cl WHERE cl.source_id = p.payment_id LIMIT 1) AS credit_ledger_id,
                (SELECT cl.amount FROM credit_ledger cl WHERE cl.source_id = p.payment_id LIMIT 1) AS credit_amount
            FROM payments p
            LEFT JOIN users u ON u.user_id = p.user_id
            LEFT JOIN plans pl ON pl.plan_id = p.plan_id
            LEFT JOIN credit_plans cp ON cp.credit_plan_id = p.credit_plan_id
            WHERE p.payment_id = CAST(:payment_id AS uuid)
        """
        row = db.execute(text(query), {"payment_id": payment_id}).fetchone()
        if not row:
            raise ValueError("결제 내역을 찾을 수 없습니다.")

        m = row._mapping
        return {
            "payment_id": str(m["payment_id"]),
            "paid_at": m["paid_at"].isoformat() if m["paid_at"] else (m["created_at"].isoformat() if m["created_at"] else ""),
            "requested_at": m["requested_at"].isoformat() if m["requested_at"] else "",
            "approved_at": m["approved_at"].isoformat() if m["approved_at"] else "",
            "refunded_at": m["refunded_at"].isoformat() if m["refunded_at"] else None,
            "user_id": str(m["user_id"]),
            "user_email": m["user_email"] or "",
            "product_type": m["product_type"],
            "product_name": m["product_name"] or "",
            "amount": m["amount"],
            "balance_amount": m["balance_amount"] if m["balance_amount"] is not None else m["amount"],
            "status": m["status"],
            "payment_method": m["payment_method"] or "",
            "pg_provider": m["pg_provider"] or "",
            "subscription_id": str(m["subscription_id"]) if m["subscription_id"] else None,
            "credit_ledger_id": str(m["credit_ledger_id"]) if m["credit_ledger_id"] else None,
            "credit_amount": m["credit_amount"] or 0,
            "admin_note": "정상 결제 건입니다.",
        }
    finally:
        db.close()


def refund_payment(payment_id: str, admin_user_id: str = None):
    db = SessionLocal()
    try:
        query = """
            SELECT payment_id, status, amount, balance_amount
            FROM payments
            WHERE payment_id = CAST(:payment_id AS uuid)
        """
        row = db.execute(text(query), {"payment_id": payment_id}).fetchone()
        if not row:
            raise ValueError("결제 내역을 찾을 수 없습니다.")

        m = row._mapping
        current_status = str(m["status"]).lower()
        if current_status in ("refunded", "canceled"):
            raise ValueError("이미 환불/취소 처리된 결제입니다.")

        db.execute(
            text("""
                UPDATE payments
                SET status = 'refunded',
                    refunded_at = NOW(),
                    balance_amount = 0,
                    updated_at = NOW()
                WHERE payment_id = CAST(:payment_id AS uuid)
            """),
            {"payment_id": payment_id}
        )

        detail = {
            "payment_id": payment_id,
            "amount": m["amount"],
            "action": "refund_payment"
        }
        db.execute(
            text("""
                INSERT INTO audit_logs (
                    actor_user_id,
                    actor_type,
                    action,
                    target_type,
                    detail,
                    created_at
                )
                VALUES (
                    :actor_user_id,
                    'admin',
                    'refund_payment',
                    'payment',
                    CAST(:detail AS jsonb),
                    NOW()
                )
            """),
            {
                "actor_user_id": admin_user_id,
                "detail": json.dumps(detail, ensure_ascii=False)
            }
        )

        db.commit()
        return {"payment_id": payment_id, "status": "refunded"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

