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
