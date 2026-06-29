from math import floor
from sqlalchemy import text
from sqlalchemy.orm import Session


def _to_iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _row_mapping(row):
    if not row:
        return None
    return row._mapping if hasattr(row, "_mapping") else row


def award_pending_ai_refund(db: Session, user_id: str):
    # 1. Fetch pending AI refund
    row = db.execute(
        text("""
            SELECT pending_ai_refund_usage
            FROM user_credit_balances
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchone()
    
    if not row:
        return 0

    pending = int(row._mapping["pending_ai_refund_usage"])
    if pending <= 0:
        return 0

    # 10% refund (round half up or just integer division, let's use standard integer round)
    refund_amount = round(pending * 0.1)

    if refund_amount > 0:
        # 2. Add to free_balance and reset pending
        db.execute(
            text("""
                UPDATE user_credit_balances
                SET
                    free_balance = free_balance + :refund_amount,
                    pending_ai_refund_usage = 0,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": user_id, "refund_amount": refund_amount}
        )

        # 3. Log to credit_ledger
        db.execute(
            text("""
                INSERT INTO credit_ledger (
                    user_id, amount, balance_after, entry_type, source_type, source_id, description, created_at
                )
                VALUES (
                    :user_id, :refund_amount, 
                    (SELECT free_balance FROM user_credit_balances WHERE user_id = :user_id),
                    'ai_refund', 'system', 'ai_refund', 'AI 활용동의 리워드 10% 환급 (무료 크레딧)', NOW()
                )
            """),
            {"user_id": user_id, "refund_amount": refund_amount}
        )
    else:
        # Just reset
        db.execute(
            text("UPDATE user_credit_balances SET pending_ai_refund_usage = 0, updated_at = NOW() WHERE user_id = :user_id"),
            {"user_id": user_id}
        )

    return refund_amount


def _subscription_payload(row):
    if not row:
        return None
    return {
        "subscription_id": str(row["subscription_id"]) if row.get("subscription_id") else None,
        "status": row.get("subscription_status"),
        "current_period_start": _to_iso(row.get("current_period_start")),
        "current_period_end": _to_iso(row.get("current_period_end")),
        "next_billing_at": _to_iso(row.get("next_billing_at")),
        "auto_renew": row.get("auto_renew"),
        "cancel_at_period_end": row.get("cancel_at_period_end"),
        "cancelled_at": _to_iso(row.get("cancelled_at")),
        "billing_status": row.get("billing_status"),
    }


def _plan_payload(row):
    return {
        "plan_id": str(row["plan_id"]) if row.get("plan_id") else None,
        "plan_code": (row.get("plan_code") or "free").lower(),
        "plan_name": row.get("plan_name") or "Free",
        "plan_rank": int(row.get("plan_rank") or 0),
        "price_amount": int(row.get("price_amount") or 0),
        "credits": int(row.get("credits") or 0),
        "billing_period_days": int(row.get("billing_period_days") or 30), # [한글 주석] 플랜 갱신 주기(일 단위) 추가
    }


def _default_free_plan():
    return {
        "plan_id": None,
        "plan_code": "free",
        "plan_name": "Free",
        "plan_rank": 0,
        "price_amount": 0,
        "credits": 0,
        "billing_period_days": 30, # [한글 주석] 기본 무료 플랜 주기 설정
    }


def resolve_current_plan(db: Session, user_id: str):
    """현재 시점에 유효한 active 구독 중 plan_rank가 가장 높은 플랜을 반환한다."""
    current_row = db.execute(
        text("""
            SELECT
                s.subscription_id,
                s.status AS subscription_status,
                s.current_period_start,
                s.current_period_end,
                s.next_billing_at,
                s.auto_renew,
                s.cancel_at_period_end,
                s.cancelled_at,
                s.billing_status,
                p.plan_id,
                p.plan_code,
                p.plan_name,
                p.plan_rank,
                p.price_amount,
                p.credits,
                p.billing_period_days -- [한글 주석] 동적 만료일 설정을 위해 추가
            FROM subscriptions s
            JOIN plans p ON p.plan_id = s.plan_id
            WHERE s.user_id = :user_id
              AND s.status = 'active'
              AND s.current_period_start <= NOW()
              AND s.current_period_end > NOW()
            ORDER BY
                p.plan_rank DESC,
                s.current_period_end DESC,
                s.created_at DESC
            LIMIT 1
        """),
        {"user_id": user_id},
    ).fetchone()

    current = _row_mapping(current_row)
    if current:
        return {
            "current_plan": _plan_payload(current),
            "current_subscription": _subscription_payload(current),
            "is_fallback_free": False,
        }

    free_row = db.execute(
        text("""
            SELECT
                plan_id,
                plan_code,
                plan_name,
                plan_rank,
                price_amount,
                credits,
                billing_period_days -- [한글 주석] 동적 만료일 설정을 위해 추가
            FROM plans
            WHERE LOWER(plan_code) = 'free'
              AND status = 'active'
            ORDER BY plan_rank ASC, sort_order ASC
            LIMIT 1
        """),
        {},
    ).fetchone()

    free = _row_mapping(free_row) or _default_free_plan()
    return {
        "current_plan": _plan_payload(free),
        "current_subscription": None,
        "is_fallback_free": True,
    }


def _get_target_plan(db: Session, to_plan_id: str):
    row = db.execute(
        text("""
            SELECT
                plan_id,
                plan_code,
                plan_name,
                plan_rank,
                price_amount,
                credits,
                billing_period_days -- [한글 주석] 동적 만료일 설정을 위해 추가
            FROM plans
            WHERE status = 'active'
              AND (
                  CAST(plan_id AS varchar) = :to_plan_id
                  OR LOWER(plan_code) = LOWER(:to_plan_id)
              )
            LIMIT 1
        """),
        {"to_plan_id": to_plan_id},
    ).fetchone()

    target = _row_mapping(row)
    if not target:
        raise ValueError("대상 플랜을 찾을 수 없습니다.")
    return _plan_payload(target)


def calculate_upgrade_proration(current_plan, current_subscription, target_plan, now=None):
    """업그레이드 시 기존 플랜의 잔여 이용 가치를 금액으로 계산한다. (소수점 이하 버림)"""
    if now is None:
        from datetime import datetime
        now = datetime.now()

    from dateutil.parser import parse
    def parse_dt(dt_val):
        if isinstance(dt_val, str):
            return parse(dt_val)
        return dt_val

    current_period_start = parse_dt(current_subscription["current_period_start"])
    current_period_end = parse_dt(current_subscription["current_period_end"])
    now = parse_dt(now)

    period_seconds = max(1.0, (current_period_end - current_period_start).total_seconds())
    remaining_seconds = max(0.0, (current_period_end - now).total_seconds())

    remaining_amount = floor(int(current_plan["price_amount"] or 0) * remaining_seconds / period_seconds)
    target_plan_amount = int(target_plan["price_amount"] or 0)
    charged_amount = max(0, target_plan_amount - remaining_amount)
    discount_amount = target_plan_amount - charged_amount

    return {
        "period_seconds": int(period_seconds),
        "remaining_seconds": int(remaining_seconds),
        "remaining_amount": remaining_amount,
        "target_plan_amount": target_plan_amount,
        "discount_amount": discount_amount,
        "charged_amount": charged_amount
    }


def classify_plan_change(db: Session, user_id: str, to_plan_id: str):
    """현재 플랜과 대상 플랜의 rank를 비교해 플랜 변경 유형만 판단한다."""
    current = resolve_current_plan(db, user_id)
    current_plan = current["current_plan"]
    target_plan = _get_target_plan(db, to_plan_id)

    current_rank = int(current_plan.get("plan_rank") or 0)
    target_rank = int(target_plan.get("plan_rank") or 0)
    target_code = (target_plan.get("plan_code") or "").lower()

    proration = None
    if target_code == "free":
        change_type = "cancel_to_free"
        apply_timing = "period_end"
        requires_payment_now = False
    elif target_rank > current_rank:
        change_type = "upgrade"
        apply_timing = "immediate"
        requires_payment_now = True
        if current["current_subscription"]:
            proration = calculate_upgrade_proration(
                current_plan=current_plan,
                current_subscription=current["current_subscription"],
                target_plan=target_plan
            )
    elif target_rank < current_rank:
        change_type = "downgrade"
        apply_timing = "period_end"
        requires_payment_now = False
    else:
        change_type = "same_plan"
        apply_timing = "none"
        requires_payment_now = False

    res = {
        "change_type": change_type,
        "apply_timing": apply_timing,
        "requires_payment_now": requires_payment_now,
        "current_plan": current_plan,
        "target_plan": target_plan,
        "current_subscription": current["current_subscription"],
    }
    if proration:
        res["proration"] = proration
    return res


def request_plan_change(db: Session, user_id: str, to_plan_id: str):
    classification = classify_plan_change(db, user_id, to_plan_id)
    if classification["change_type"] == "cancel_to_free":
        scheduled = schedule_cancel_to_free(
            db=db,
            user_id=user_id,
            from_subscription_id=classification["current_subscription"]["subscription_id"],
            current_plan=classification["current_plan"],
            current_subscription=classification["current_subscription"],
            target_plan=classification["target_plan"],
        )
        return {
            **classification,
            "scheduled_plan_change": scheduled,
        }

    if classification["change_type"] != "downgrade":
        return classification

    scheduled = schedule_downgrade(
        db=db,
        user_id=user_id,
        from_subscription_id=classification["current_subscription"]["subscription_id"],
        to_plan_id=classification["target_plan"]["plan_id"],
        current_plan=classification["current_plan"],
        current_subscription=classification["current_subscription"],
        target_plan=classification["target_plan"],
    )

    return {
        **classification,
        "scheduled_plan_change": scheduled,
    }


def schedule_cancel_to_free(
    db: Session,
    user_id: str,
    from_subscription_id: str,
    current_plan=None,
    current_subscription=None,
    target_plan=None,
):
    if not current_plan or not current_subscription:
        current = resolve_current_plan(db, user_id)
        current_plan = current["current_plan"]
        current_subscription = current["current_subscription"]
    if not target_plan:
        target_plan = _get_target_plan(db, "free")

    if not current_subscription:
        raise ValueError("Active subscription was not found for cancellation.")

    effective_at = current_subscription["current_period_end"]
    if not effective_at:
        raise ValueError("Current subscription period end is required for cancellation scheduling.")

    db.execute(
        text("""
            UPDATE subscriptions
            SET
                auto_renew = false,
                cancel_at_period_end = true,
                cancelled_at = NOW(),
                status = 'active',
                updated_at = NOW()
            WHERE subscription_id = :subscription_id
        """),
        {"subscription_id": from_subscription_id},
    )

    db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id
              AND from_subscription_id = :from_subscription_id
              AND change_type IN ('downgrade', 'cancel_to_free')
              AND status = 'scheduled'
        """),
        {
            "user_id": user_id,
            "from_subscription_id": from_subscription_id,
        },
    )

    row = db.execute(
        text("""
            INSERT INTO subscription_plan_changes (
                user_id,
                subscription_id,
                from_plan_id,
                to_plan_id,
                from_subscription_id,
                to_subscription_id,
                change_type,
                apply_timing,
                status,
                requested_at,
                effective_at,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :subscription_id,
                :from_plan_id,
                :to_plan_id,
                :from_subscription_id,
                NULL,
                'cancel_to_free',
                'period_end',
                'scheduled',
                NOW(),
                CAST(:effective_at AS timestamp),
                NOW(),
                NOW()
            )
            RETURNING plan_change_id, status, effective_at
        """),
        {
            "user_id": user_id,
            "subscription_id": from_subscription_id,
            "from_plan_id": current_plan["plan_id"],
            "to_plan_id": target_plan["plan_id"],
            "from_subscription_id": from_subscription_id,
            "effective_at": effective_at,
        },
    ).fetchone()
    scheduled = _row_mapping(row)

    return {
        "plan_change_id": str(scheduled["plan_change_id"]) if scheduled.get("plan_change_id") else None,
        "change_type": "cancel_to_free",
        "to_plan_id": target_plan["plan_id"],
        "to_plan_code": target_plan["plan_code"],
        "to_plan_name": target_plan["plan_name"],
        "status": scheduled["status"],
        "effective_at": _to_iso(scheduled["effective_at"]),
    }


def resume_subscription(db: Session, user_id: str, subscription_id: str):
    subscription_row = db.execute(
        text("""
            SELECT
                subscription_id,
                status,
                current_period_end,
                auto_renew,
                cancel_at_period_end
            FROM subscriptions
            WHERE subscription_id = :subscription_id
              AND user_id = :user_id
              AND status = 'active'
              AND cancel_at_period_end = true
              AND current_period_end > NOW()
            LIMIT 1
        """),
        {
            "subscription_id": subscription_id,
            "user_id": user_id,
        },
    ).fetchone()
    subscription = _row_mapping(subscription_row)
    if not subscription:
        raise ValueError("Resumable active subscription was not found.")

    updated_row = db.execute(
        text("""
            UPDATE subscriptions
            SET
                auto_renew = true,
                cancel_at_period_end = false,
                cancelled_at = NULL,
                updated_at = NOW()
            WHERE subscription_id = :subscription_id
            RETURNING
                subscription_id,
                status AS subscription_status,
                current_period_start,
                current_period_end,
                next_billing_at,
                auto_renew,
                cancel_at_period_end,
                cancelled_at,
                billing_status
        """),
        {"subscription_id": subscription_id},
    ).fetchone()
    updated = _row_mapping(updated_row)

    db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id
              AND from_subscription_id = :subscription_id
              AND change_type = 'cancel_to_free'
              AND status = 'scheduled'
        """),
        {
            "user_id": user_id,
            "subscription_id": subscription_id,
        },
    )

    return {
        "subscription_id": str(updated["subscription_id"]) if updated.get("subscription_id") else None,
        "status": "active",
        "auto_renew": updated.get("auto_renew"),
        "cancel_at_period_end": updated.get("cancel_at_period_end"),
        "cancelled_at": _to_iso(updated.get("cancelled_at")),
        "current_period_end": _to_iso(updated.get("current_period_end")),
    }


def cancel_scheduled_plan_change(db: Session, user_id: str, plan_change_id: str):
    plan_change_row = db.execute(
        text("""
            SELECT
                plan_change_id,
                change_type,
                status,
                from_subscription_id,
                effective_at
            FROM subscription_plan_changes
            WHERE plan_change_id = CAST(:plan_change_id AS uuid)
              AND user_id = :user_id
              AND status = 'scheduled'
            LIMIT 1
        """),
        {
            "plan_change_id": plan_change_id,
            "user_id": user_id,
        },
    ).fetchone()
    plan_change = _row_mapping(plan_change_row)
    if not plan_change:
        raise ValueError("Scheduled plan change was not found.")

    if plan_change.get("change_type") != "downgrade":
        raise ValueError("Only scheduled downgrades can be cancelled here.")

    updated_row = db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE plan_change_id = CAST(:plan_change_id AS uuid)
            RETURNING plan_change_id, change_type, status, effective_at
        """),
        {"plan_change_id": plan_change_id},
    ).fetchone()
    updated = _row_mapping(updated_row)

    return {
        "plan_change_id": str(updated["plan_change_id"]) if updated.get("plan_change_id") else None,
        "change_type": updated.get("change_type"),
        "status": updated.get("status"),
        "effective_at": _to_iso(updated.get("effective_at")),
    }


def schedule_downgrade(
    db: Session,
    user_id: str,
    from_subscription_id: str,
    to_plan_id: str,
    current_plan=None,
    current_subscription=None,
    target_plan=None,
):
    if not current_plan or not current_subscription:
        current = resolve_current_plan(db, user_id)
        current_plan = current["current_plan"]
        current_subscription = current["current_subscription"]
    if not target_plan:
        target_plan = _get_target_plan(db, str(to_plan_id))

    if not current_subscription:
        raise ValueError("Active subscription was not found for downgrade.")

    if int(target_plan["plan_rank"]) >= int(current_plan.get("plan_rank") or 0):
        raise ValueError("Target plan must be lower than the current plan.")

    effective_at = current_subscription["current_period_end"]
    if not effective_at:
        raise ValueError("Current subscription period end is required for downgrade scheduling.")

    db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id
              AND from_subscription_id = :from_subscription_id
              AND change_type = 'downgrade'
              AND status = 'scheduled'
        """),
        {
            "user_id": user_id,
            "from_subscription_id": from_subscription_id,
        },
    )

    row = db.execute(
        text("""
            INSERT INTO subscription_plan_changes (
                user_id,
                subscription_id,
                from_plan_id,
                to_plan_id,
                from_subscription_id,
                to_subscription_id,
                change_type,
                apply_timing,
                status,
                requested_at,
                effective_at,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :subscription_id,
                :from_plan_id,
                :to_plan_id,
                :from_subscription_id,
                NULL,
                'downgrade',
                'period_end',
                'scheduled',
                NOW(),
                CAST(:effective_at AS timestamp),
                NOW(),
                NOW()
            )
            RETURNING plan_change_id, status, effective_at
        """),
        {
            "user_id": user_id,
            "subscription_id": from_subscription_id,
            "from_plan_id": current_plan["plan_id"],
            "to_plan_id": target_plan["plan_id"],
            "from_subscription_id": from_subscription_id,
            "effective_at": effective_at,
        },
    ).fetchone()
    scheduled = _row_mapping(row)

    return {
        "plan_change_id": str(scheduled["plan_change_id"]) if scheduled.get("plan_change_id") else None,
        "change_type": "downgrade",
        "to_plan_id": target_plan["plan_id"],
        "to_plan_code": target_plan["plan_code"],
        "to_plan_name": target_plan["plan_name"],
        "status": scheduled["status"],
        "effective_at": _to_iso(scheduled["effective_at"]),
    }


def create_or_extend_subscription(
    db: Session,
    user_id: str,
    plan_id,
    payment_id=None,
    billing_key_id=None, # [한글 주석] 정기 결제 빌링키 ID 파라미터 추가
):
    """결제 성공 후 같은 플랜 구독을 동적으로 정의된 기간만큼 생성하거나 연장한다."""
    target_plan = _get_target_plan(db, str(plan_id))
    p_days = int(target_plan.get("billing_period_days") or 30)

    existing_row = db.execute(
        text("""
            SELECT
                subscription_id,
                status,
                current_period_end
            FROM subscriptions
            WHERE user_id = :user_id
              AND plan_id = :plan_id
            ORDER BY
                CASE
                    WHEN status = 'active'
                     AND current_period_end IS NOT NULL
                     AND current_period_end > NOW()
                    THEN 0
                    ELSE 1
                END,
                current_period_end DESC NULLS LAST,
                updated_at DESC NULLS LAST,
                created_at DESC
            LIMIT 1
        """),
        {"user_id": user_id, "plan_id": plan_id},
    ).fetchone()

    existing = _row_mapping(existing_row)
    if existing and existing.get("status") == "active" and existing.get("current_period_end"):
        extend_row = db.execute(
            text("""
                UPDATE subscriptions
                SET
                    current_period_start = COALESCE(current_period_start, NOW()),
                    current_period_end = CASE
                        WHEN current_period_end > NOW()
                        THEN current_period_end + CAST(:period_days || ' days' AS interval) -- [한글 주석] 동적 만료일 연장
                        ELSE NOW() + CAST(:period_days || ' days' AS interval)
                    END,
                    next_billing_at = CASE
                        WHEN current_period_end > NOW()
                        THEN current_period_end + CAST(:period_days || ' days' AS interval) -- [한글 주석] 동적 다음결제일 연장
                        ELSE NOW() + CAST(:period_days || ' days' AS interval)
                    END,
                    ended_at = CASE
                        WHEN current_period_end > NOW()
                        THEN current_period_end + CAST(:period_days || ' days' AS interval) -- [한글 주석] 동적 만료일 연장
                        ELSE NOW() + CAST(:period_days || ' days' AS interval)
                    END,
                    renew_at = CASE
                        WHEN current_period_end > NOW()
                        THEN current_period_end + CAST(:period_days || ' days' AS interval) -- [한글 주석] 동적 갱신일 연장
                        ELSE NOW() + CAST(:period_days || ' days' AS interval)
                    END,
                    status = 'active',
                    auto_renew = true,
                    cancel_at_period_end = false,
                    cancelled_at = NULL,
                    billing_status = 'paid',
                    last_payment_id = :payment_id,
                    billing_key_id = COALESCE(CAST(:billing_key_id AS uuid), billing_key_id), -- [한글 주석] 빌링키 정보 업데이트
                    updated_at = NOW()
                WHERE subscription_id = :subscription_id
                RETURNING subscription_id, current_period_start, current_period_end, next_billing_at
            """),
            {
                "subscription_id": existing["subscription_id"],
                "payment_id": payment_id,
                "billing_key_id": billing_key_id, # [한글 주석] 빌링키 바인딩 추가
                "period_days": p_days,
            },
        ).fetchone()
        return _row_mapping(extend_row)

    if existing:
        reset_row = db.execute(
            text("""
                UPDATE subscriptions
                SET
                    status = 'active',
                    started_at = NOW(),
                    ended_at = NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                    renew_at = NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 갱신일 설정
                    current_period_start = NOW(),
                    current_period_end = NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                    next_billing_at = NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 다음결제일 설정
                    auto_renew = true,
                    cancel_at_period_end = false,
                    cancelled_at = NULL,
                    billing_status = 'paid',
                    last_payment_id = :payment_id,
                    billing_key_id = CAST(:billing_key_id AS uuid), -- [한글 주석] 빌링키 정보 재설정
                    updated_at = NOW()
                WHERE subscription_id = :subscription_id
                RETURNING subscription_id, current_period_start, current_period_end, next_billing_at
            """),
            {
                "subscription_id": existing["subscription_id"],
                "payment_id": payment_id,
                "billing_key_id": billing_key_id, # [한글 주석] 빌링키 바인딩 추가
                "period_days": p_days,
            },
        ).fetchone()
        return _row_mapping(reset_row)

    insert_row = db.execute(
        text("""
            INSERT INTO subscriptions (
                user_id,
                plan_id,
                status,
                started_at,
                ended_at,
                renew_at,
                current_period_start,
                current_period_end,
                next_billing_at,
                auto_renew,
                cancel_at_period_end,
                billing_status,
                last_payment_id,
                billing_key_id, -- [한글 주석] 빌링키 컬럼 추가
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :plan_id,
                'active',
                NOW(),
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 갱신일 설정
                NOW(),
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 다음결제일 설정
                true,
                false,
                'paid',
                :payment_id,
                CAST(:billing_key_id AS uuid), -- [한글 주석] 빌링키 컬럼 바인딩
                NOW(),
                NOW()
            )
            RETURNING subscription_id, current_period_start, current_period_end, next_billing_at
        """),
        {
            "user_id": user_id,
            "plan_id": plan_id,
            "payment_id": payment_id,
            "billing_key_id": billing_key_id, # [한글 주석] 빌링키 바인딩 추가
            "period_days": p_days,
        },
    ).fetchone()
    return _row_mapping(insert_row)


def apply_upgrade_with_proration(
    db: Session,
    user_id: str,
    from_subscription_id=None,
    to_plan_id=None,
    payment_id=None,
    billing_key_id=None, # [한글 주석] 정기 결제 빌링키 ID 파라미터 추가
):
    """업그레이드 시 기존 구독을 즉시 취소하고, 새 플랜 구독을 정산 차액 기준으로 적용합니다."""
    if not to_plan_id:
        raise ValueError("Target plan is required for upgrade.")

    target_plan = _get_target_plan(db, str(to_plan_id))
    lower = _find_upgrade_source_subscription(
        db=db,
        user_id=user_id,
        from_subscription_id=from_subscription_id,
    )
    if not lower:
        raise ValueError("Active source subscription was not found for upgrade.")

    if int(target_plan["plan_rank"]) <= int(lower.get("plan_rank") or 0):
        raise ValueError("Target plan must be higher than the current plan.")

    # 1. 정산 금액 계산
    proration = calculate_upgrade_proration(
        current_plan=lower,
        current_subscription=lower,
        target_plan=target_plan
    )

    # 2. 새 상위 구독 active 생성 (빌링키 고유 ID 매핑 보존)
    upper_row = db.execute(
        text("""
            INSERT INTO subscriptions (
                user_id,
                plan_id,
                status,
                started_at,
                ended_at,
                renew_at,
                current_period_start,
                current_period_end,
                next_billing_at,
                auto_renew,
                cancel_at_period_end,
                billing_status,
                last_payment_id,
                billing_key_id, -- [한글 주석] 빌링키 고유키 매핑
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :plan_id,
                'active',
                NOW(),
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 갱신일 설정
                NOW(),
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 만료일 설정
                NOW() + CAST(:period_days || ' days' AS interval), -- [한글 주석] 동적 다음결제일 설정
                true,
                false,
                'paid',
                :payment_id,
                CAST(:billing_key_id AS uuid), -- [한글 주석] 빌링키 컬럼 바인딩
                NOW(),
                NOW()
            )
            RETURNING subscription_id, current_period_start, current_period_end, next_billing_at
        """),
        {
            "user_id": user_id,
            "plan_id": target_plan["plan_id"],
            "payment_id": payment_id,
            "billing_key_id": billing_key_id,
            "period_days": int(target_plan.get("billing_period_days") or 30),
        },
    ).fetchone()
    upper = _row_mapping(upper_row)

    # 3. 기존 하위 구독 즉시 취소(cancelled) 처리
    db.execute(
        text("""
            UPDATE subscriptions
            SET
                status = 'cancelled',
                ended_at = NOW(),
                renew_at = NULL,
                current_period_end = NOW(),
                next_billing_at = NULL,
                auto_renew = false,
                cancel_at_period_end = false,
                cancelled_at = NOW(),
                billing_status = 'cancelled',
                updated_at = NOW()
            WHERE subscription_id = :from_subscription_id
              AND user_id = :user_id
              AND status = 'active'
        """),
        {
            "from_subscription_id": lower["subscription_id"],
            "user_id": user_id,
        },
    )

    # 4. 기존 하위 구독에 연계되었던 모든 예약 변경(scheduled) 취소(cancelled)
    db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE user_id = :user_id
              AND from_subscription_id = :from_subscription_id
              AND status = 'scheduled'
        """),
        {
            "user_id": user_id,
            "from_subscription_id": lower["subscription_id"],
        },
    )

    # 5. subscription_plan_changes 정산 이력 기록
    plan_change_row = db.execute(
        text("""
            INSERT INTO subscription_plan_changes (
                user_id,
                subscription_id,
                from_plan_id,
                to_plan_id,
                from_subscription_id,
                to_subscription_id,
                change_type,
                apply_timing,
                status,
                remaining_seconds,
                remaining_amount,
                target_plan_amount,
                discount_amount,
                charged_amount,
                from_subscription_original_end,
                requested_at,
                effective_at,
                applied_at,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :upper_subscription_id,
                :from_plan_id,
                :to_plan_id,
                :lower_subscription_id,
                :upper_subscription_id,
                'upgrade',
                'immediate',
                'applied',
                :remaining_seconds,
                :remaining_amount,
                :target_plan_amount,
                :discount_amount,
                :charged_amount,
                :from_subscription_original_end,
                NOW(),
                NOW(),
                NOW(),
                NOW(),
                NOW()
            )
            RETURNING plan_change_id
        """),
        {
            "user_id": user_id,
            "upper_subscription_id": upper["subscription_id"],
            "from_plan_id": lower["plan_id"],
            "to_plan_id": target_plan["plan_id"],
            "lower_subscription_id": lower["subscription_id"],
            "remaining_seconds": proration["remaining_seconds"],
            "remaining_amount": proration["remaining_amount"],
            "target_plan_amount": proration["target_plan_amount"],
            "discount_amount": proration["discount_amount"],
            "charged_amount": proration["charged_amount"],
            "from_subscription_original_end": lower["current_period_end"],
        },
    ).fetchone()
    plan_change = _row_mapping(plan_change_row)

    return {
        "subscription_id": upper["subscription_id"],
        "upper_subscription": upper,
        "plan_change_id": plan_change["plan_change_id"] if plan_change else None,
    }


def _find_upgrade_source_subscription(
    db: Session,
    user_id: str,
    from_subscription_id=None,
):
    params = {
        "user_id": user_id,
        "from_subscription_id": from_subscription_id,
    }
    id_filter = (
        "AND s.subscription_id = :from_subscription_id"
        if from_subscription_id
        else ""
    )
    row = db.execute(
        text(f"""
            SELECT
                s.subscription_id,
                s.plan_id,
                s.current_period_start,
                s.current_period_end,
                p.plan_rank,
                p.price_amount -- [한글 주석] 기존 구독 플랜의 잔여 가치 금액 계산을 위해 가격 추가
            FROM subscriptions s
            JOIN plans p ON p.plan_id = s.plan_id
            WHERE s.user_id = :user_id
              AND s.status = 'active'
              AND s.current_period_start <= NOW()
              AND s.current_period_end > NOW()
              {id_filter}
            ORDER BY
                p.plan_rank DESC,
                s.current_period_end DESC,
                s.created_at DESC
            LIMIT 1
        """),
        params,
    ).fetchone()

    lower = _row_mapping(row)
    if lower or not from_subscription_id:
        return lower

    return _find_upgrade_source_subscription(
        db=db,
        user_id=user_id,
        from_subscription_id=None,
    )
