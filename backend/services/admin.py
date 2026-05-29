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
                SELECT plan_code, file_size_limit, max_jobs, monthly_quota, 
                       result_retention_days, price_amount, watermark_required, 
                       auto_delete_original_hours, metadata_retention_days, credits
                FROM plans
            """)
        ).fetchall()

        for prow in plan_rows:
            pm = prow._mapping
            pcode = pm["plan_code"].lower()
            if pcode in ["free", "pro", "studio"]:
                policies["file_processing"]["plans"][pcode] = {
                    "fileSizeLimit": pm["file_size_limit"],
                    "maxJobs": pm["max_jobs"],
                    "monthlyQuota": pm["monthly_quota"],
                    "resultRetention": pm["result_retention_days"],
                    "watermarkRequired": pm["watermark_required"]
                }
                policies["payment"]["plans"][pcode] = {
                    "credits": pm["credits"],
                    "price": pm["price_amount"]
                }
                policies["retention"]["plans"][pcode] = {
                    "autoDeleteOriginalHours": pm["auto_delete_original_hours"],
                    "metadataRetentionDays": pm["metadata_retention_days"]
                }

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
