import os
import base64
import json
import urllib.error
import urllib.request
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from services import subscription as subscription_service
from services.subscription import resolve_current_plan

load_dotenv()

TOSS_SECRET_KEY = os.getenv(
    "TOSS_SECRET_KEY"
)

async def create_temp_order(
    db: Session,
    user_id: str,
    product_type: str,
    product_code: str,
    amount: int
):
    product_type = product_type.lower()
    product_code_lower = product_code.lower()

    if product_type == "subscription":
        product_query = text("""
            SELECT
                plan_id AS product_id,
                plan_code AS product_code,
                plan_name AS product_name,
                price_amount,
                status,
                credits
            FROM plans
            WHERE LOWER(plan_code) = :product_code
        """)
    elif product_type == "credit":
        product_query = text("""
            SELECT
                credit_plan_id AS product_id,
                credit_plan_code AS product_code,
                credit_plan_name AS product_name,
                price_amount,
                status,
                base_credits,
                bonus_credits
            FROM credit_plans
            WHERE LOWER(credit_plan_code) = :product_code
        """)
    else:
        raise ValueError("Unsupported payment product type.")

    result = db.execute(product_query, {"product_code": product_code_lower}).fetchone()

    if not result:
        raise ValueError("Invalid payment product code.")

    product = result._mapping

    if product["status"] != "active":
        raise ValueError("Inactive payment product.")

    # 업그레이드 여부 및 정산 금액 사전 계산
    if product_type == "subscription":
        plan_change = subscription_service.classify_plan_change(db=db, user_id=user_id, to_plan_id=product_code_lower)
        is_upgrade = (plan_change["change_type"] == "upgrade" and plan_change.get("current_subscription"))
        if is_upgrade:
            expected_amount = plan_change["proration"]["charged_amount"]
        else:
            expected_amount = product["price_amount"]
    else:
        expected_amount = product["price_amount"]

    if expected_amount != amount:
        raise ValueError("Requested amount does not match product price.")

    if product_type == "credit":
        insert_query = text("""
            INSERT INTO payments (
                user_id,
                subscription_id,
                product_type,
                credit_plan_id,
                amount,
                status,
                pg_provider,
                order_name,
                created_at
            )
            VALUES (
                :user_id,
                :subscription_id,
                :product_type,
                :credit_plan_id,
                :amount,
                'ready',
                'toss',
                :order_name,
                NOW()
            )
            RETURNING payment_id, amount, subscription_id, product_type
        """)
        try:
            inserted = db.execute(
                insert_query,
                {
                    "user_id": user_id,
                    "subscription_id": None,
                    "product_type": "credit",
                    "credit_plan_id": product["product_id"],
                    "amount": amount,
                    "order_name": product["product_name"],
                }
            ).fetchone()
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

        payment = inserted._mapping
        return {
            "payment_id": str(payment["payment_id"]),
            "amount": payment["amount"],
            "order_name": product["product_name"],
            "product_type": "credit",
            "product_code": product_code_lower,
            "subscription_id": None,
        }

    _restore_free_plan_for_expired_subscriptions(db, user_id)

    insert_query = text("""
        INSERT INTO payments (
            user_id,
            subscription_id,
            product_type,
            plan_id,
            amount,
            status,
            pg_provider,
            order_name,
            created_at
        )
        VALUES (
            :user_id,
            :subscription_id,
            :product_type,
            :plan_id,
            :amount,
            'ready',
            'toss',
            :order_name,
            NOW()
        )
        RETURNING payment_id, amount, subscription_id, product_type
    """)

    try:
        subscription = _get_user_subscription(db, user_id)
        if not subscription:
            raise ValueError("User subscription was not found.")
        inserted = db.execute(
            insert_query,
            {
                "user_id": user_id,
                "subscription_id": subscription["subscription_id"],
                "product_type": "subscription",
                "plan_id": product["product_id"],
                "amount": amount,
                "order_name": product["product_name"],
            }
        ).fetchone()
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    payment = inserted._mapping

    return {
        "payment_id": str(payment["payment_id"]),
        "amount": payment["amount"],
        "order_name": product["product_name"],
        "product_type": product_type,
        "product_code": product_code_lower,
        "subscription_id": str(payment["subscription_id"]) if payment["subscription_id"] else None,
    }



async def confirm_payment(
    db: Session,
    payment_key: str,
    order_id: str,
    amount: int
):
    payment_row = db.execute(
        text("""
            SELECT
                p.payment_id,
                p.amount,
                p.status,
                p.pg_transaction_id,
                p.paid_at,
                p.order_name,
                p.payment_method,
                p.receipt_url,
                p.approved_at,
                p.user_id,
                p.subscription_id,
                p.product_type,
                p.plan_id,
                p.credit_plan_id,
                pl.credits AS plan_credits,
                pl.plan_code,
                cp.base_credits,
                cp.bonus_credits,
                cp.credit_plan_code
            FROM payments p
            LEFT JOIN plans pl
                ON pl.plan_id = p.plan_id
            LEFT JOIN credit_plans cp
                ON cp.credit_plan_id = p.credit_plan_id
            WHERE p.payment_id = CAST(:order_id AS uuid)
        """),
        {"order_id": order_id},
    ).fetchone()

    if not payment_row:
        raise ValueError("결제 요청을 찾을 수 없습니다.")

    payment = payment_row._mapping
    current_status = str(payment["status"]).lower()

    if payment["amount"] != amount:
        raise ValueError("승인 금액이 사전 주문 금액과 일치하지 않습니다.")

    if current_status == "success":
        return {
            "status": "success",
            "orderId": str(payment["payment_id"]),
            "orderName": payment.get("order_name"),
            "amount": payment["amount"],
            "method": payment.get("payment_method"),
            "approvedAt": _to_iso_or_value(payment.get("approved_at") or payment.get("paid_at")),
            "receiptUrl": payment.get("receipt_url"),
            "idempotent": True,
        }

    if current_status not in ("ready", "pending"):
        raise ValueError("승인 가능한 결제 상태가 아닙니다.")

    try:
        user_id = payment.get("user_id")
        plan_change = subscription_service.classify_plan_change(
            db=db,
            user_id=user_id,
            to_plan_id=str(payment.get("plan_id")) if payment.get("plan_id") else "",
        )
        is_upgrade = (plan_change["change_type"] == "upgrade" and plan_change.get("current_subscription"))

        # 0원 결제 승인 예외 처리 (PG 승인 요청 스킵)
        if is_upgrade and amount == 0:
            toss_status = "SUCCESS"
            toss_result = {
                "status": "DONE",
                "paymentKey": "MOCK_ZERO_UPGRADE_KEY_" + order_id,
                "lastTransactionKey": "MOCK_ZERO_TRANS_KEY_" + order_id,
                "orderId": order_id,
                "orderName": payment.get("order_name") or "Garim 업그레이드 정산(0원)",
                "method": "차액정산(0원)",
                "totalAmount": 0,
                "balanceAmount": 0,
                "currency": "KRW",
                "requestedAt": _to_iso_or_value(payment.get("created_at")),
                "approvedAt": _to_iso_or_value(payment.get("created_at")),
                "isPartialCancelable": False,
                "receipt": {"url": None}
            }
        else:
            toss_result = await _confirm_toss_payment(payment_key, order_id, amount)
            toss_status = str(toss_result.get("status", "")).upper()

        if toss_status not in ("DONE", "SUCCESS"):
            return _public_payment_response(toss_result)

        if not (is_upgrade and amount == 0):
            _validate_toss_result(toss_result, order_id, amount)

        db.execute(
            text("""
                UPDATE payments
                SET
                    status = 'success',
                    pg_transaction_id = :payment_key,
                    last_transaction_key = :last_transaction_key,
                    order_name = :order_name,
                    payment_method = :payment_method,
                    easy_pay_provider = :easy_pay_provider,
                    toss_status = :toss_status,
                    total_amount = :total_amount,
                    balance_amount = :balance_amount,
                    currency = :currency,
                    requested_at = CAST(:requested_at AS timestamp),
                    approved_at = CAST(:approved_at AS timestamp),
                    receipt_url = :receipt_url,
                    is_partial_cancelable = :is_partial_cancelable,
                    paid_at = NOW(),
                    updated_at = NOW()
                WHERE payment_id = CAST(:order_id AS uuid)
            """),
            {
                "payment_key": toss_result.get("paymentKey") or payment_key,
                "order_id": order_id,
                "last_transaction_key": toss_result.get("lastTransactionKey"),
                "order_name": toss_result.get("orderName"),
                "payment_method": toss_result.get("method"),
                "easy_pay_provider": (toss_result.get("easyPay") or {}).get("provider") if toss_result.get("easyPay") else None,
                "toss_status": toss_status,
                "total_amount": toss_result.get("totalAmount"),
                "balance_amount": toss_result.get("balanceAmount"),
                "currency": toss_result.get("currency") or "KRW",
                "requested_at": toss_result.get("requestedAt"),
                "approved_at": toss_result.get("approvedAt"),
                "receipt_url": (toss_result.get("receipt") or {}).get("url") if toss_result.get("receipt") else None,
                "is_partial_cancelable": toss_result.get("isPartialCancelable"),
            },
        )

        product_type = str(payment.get("product_type") or "").lower()

        if product_type == "subscription":
            _restore_free_plan_for_expired_subscriptions(db, user_id)

            if is_upgrade:
                subscription = subscription_service.apply_upgrade_with_proration(
                    db=db,
                    user_id=user_id,
                    from_subscription_id=(
                        plan_change["current_subscription"].get("subscription_id")
                        or payment.get("subscription_id")
                    ),
                    to_plan_id=payment.get("plan_id"),
                    payment_id=payment.get("payment_id"),
                )
            else:
                subscription = subscription_service.create_or_extend_subscription(
                    db=db,
                    user_id=user_id,
                    plan_id=payment.get("plan_id"),
                    payment_id=payment.get("payment_id"),
                )
            subscription_id = subscription["subscription_id"]

            db.execute(
                text("""
                    UPDATE payments
                    SET
                        subscription_id = :subscription_id,
                        updated_at = NOW()
                    WHERE payment_id = :payment_id
                """),
                {
                    "subscription_id": subscription_id,
                    "payment_id": payment.get("payment_id"),
                },
            )

            grant_amount = int(payment.get("plan_credits") or 0)
            if grant_amount > 0:
                _add_user_credits(
                    db=db,
                    user_id=user_id,
                    amount=grant_amount,
                    entry_type="grant",
                    source_type="subscription",
                    source_id=subscription_id,
                    description=f"구독 플랜 기본 크레딧 지급: {payment.get('plan_code')}",
                )

        elif product_type == "credit":
            purchase_amount = int(payment.get("base_credits") or 0) + int(payment.get("bonus_credits") or 0)
            if purchase_amount <= 0:
                raise ValueError("지급할 크레딧이 없는 크레딧 상품입니다.")

            _add_user_credits(
                db=db,
                user_id=payment.get("user_id"),
                amount=purchase_amount,
                entry_type="purchase",
                source_type="payment",
                source_id=payment.get("payment_id"),
                description=f"크레딧 충전: {payment.get('credit_plan_code')}",
            )

        db.commit()
        return _public_payment_response(toss_result)
    except Exception:
        db.rollback()
        raise


def _validate_toss_result(toss_result: dict, order_id: str, amount: int):
    if toss_result.get("orderId") != order_id:
        raise ValueError("Toss orderId does not match the requested orderId.")

    total_amount = toss_result.get("totalAmount")
    if total_amount is not None and total_amount != amount:
        raise ValueError("Toss totalAmount does not match the requested amount.")


def _get_user_subscription(db: Session, user_id):
    row = db.execute(
        text("""
            SELECT subscription_id
            FROM subscriptions
            WHERE user_id = :user_id
            ORDER BY
                CASE WHEN status = 'active' THEN 0 ELSE 1 END,
                created_at ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    ).fetchone()
    return row._mapping if hasattr(row, "_mapping") else row


def _add_user_credits(
    db: Session,
    user_id,
    amount: int,
    entry_type: str,
    source_type: str,
    source_id,
    description: str | None = None,
):
    row = db.execute(
        text("""
            INSERT INTO user_credit_balances (user_id, balance, updated_at)
            VALUES (:user_id, :amount, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET
                balance = user_credit_balances.balance + EXCLUDED.balance,
                updated_at = NOW()
            RETURNING balance
        """),
        {"user_id": user_id, "amount": amount},
    ).fetchone()

    balance_after = int(row._mapping["balance"])

    db.execute(
        text("""
            INSERT INTO credit_ledger (
                user_id,
                amount,
                balance_after,
                entry_type,
                source_type,
                source_id,
                description,
                created_at
            )
            VALUES (
                :user_id,
                :amount,
                :balance_after,
                :entry_type,
                :source_type,
                :source_id,
                :description,
                NOW()
            )
        """),
        {
            "user_id": user_id,
            "amount": amount,
            "balance_after": balance_after,
            "entry_type": entry_type,
            "source_type": source_type,
            "source_id": source_id,
            "description": description,
        },
    )

    return balance_after


def _spend_user_credits(
    db,
    user_id,
    amount: int,
    source_id,
    description: str | None = None,
):
    # 1. Fetch current balances and consent status
    row = db.execute(
        text("""
            SELECT b.balance, b.free_balance, b.pending_ai_refund_usage, COALESCE(s.data_usage_consent, false) as data_usage_consent
            FROM user_credit_balances b
            LEFT JOIN user_settings s ON b.user_id = s.user_id
            WHERE b.user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchone()

    if not row:
        raise ValueError("크레딧 잔액이 부족합니다.")

    m = row._mapping
    current_free = int(m["free_balance"])
    current_paid = int(m["balance"])
    data_usage_consent = bool(m["data_usage_consent"])

    if current_free + current_paid < amount:
        raise ValueError("크레딧 잔액이 부족합니다.")

    # Calculate deductions
    free_deducted = min(current_free, amount)
    paid_deducted = amount - free_deducted

    # Calculate pending AI refund accumulation
    pending_ai_accumulation = paid_deducted if data_usage_consent else 0

    # 2. Update balances
    update_row = db.execute(
        text("""
            UPDATE user_credit_balances
            SET
                free_balance = free_balance - :free_deducted,
                balance = balance - :paid_deducted,
                pending_ai_refund_usage = pending_ai_refund_usage + :pending_ai_accumulation,
                updated_at = NOW()
            WHERE user_id = :user_id
            RETURNING balance, free_balance
        """),
        {
            "user_id": user_id,
            "free_deducted": free_deducted,
            "paid_deducted": paid_deducted,
            "pending_ai_accumulation": pending_ai_accumulation,
        }
    ).fetchone()

    balance_after = int(update_row._mapping["balance"])
    free_balance_after = int(update_row._mapping["free_balance"])

    # 3. Log into credit_ledger
    # We log separately for free and paid deductions if both happened
    if free_deducted > 0:
        db.execute(
            text("""
                INSERT INTO credit_ledger (
                    user_id, amount, balance_after, entry_type, source_type, source_id, description, created_at
                )
                VALUES (
                    :user_id, :amount, :balance_after, 'spend', 'analysis', :source_id, :description, NOW()
                )
            """),
            {
                "user_id": user_id,
                "amount": -free_deducted,
                "balance_after": free_balance_after,
                "source_id": source_id,
                "description": (description or "") + " (무료 크레딧)",
            },
        )

    if paid_deducted > 0:
        db.execute(
            text("""
                INSERT INTO credit_ledger (
                    user_id, amount, balance_after, entry_type, source_type, source_id, description, created_at
                )
                VALUES (
                    :user_id, :amount, :balance_after, 'spend', 'analysis', :source_id, :description, NOW()
                )
            """),
            {
                "user_id": user_id,
                "amount": -paid_deducted,
                "balance_after": balance_after,
                "source_id": source_id,
                "description": (description or "") + " (보유 크레딧)",
            },
        )

    # Return total remaining balance for compatibility, or just paid balance
    return balance_after + free_balance_after


def _restore_free_plan_for_expired_subscriptions(db: Session, user_id):
    if not user_id:
        return

    # 1. Update subscription to Free
    row = db.execute(
        text("""
            UPDATE subscriptions
            SET
                plan_id = free_plan.plan_id,
                status = 'active',
                started_at = NOW(),
                ended_at = NULL,
                renew_at = NOW() + INTERVAL '30 days',
                updated_at = NOW()
            FROM (
                SELECT plan_id
                FROM plans
                WHERE LOWER(plan_code) = 'free'
                  AND status = 'active'
                LIMIT 1
            ) AS free_plan
            WHERE subscriptions.user_id = :user_id
              AND status = 'active'
              AND ended_at IS NOT NULL
              AND ended_at <= NOW()
            RETURNING subscription_id
        """),
        {"user_id": user_id},
    ).fetchone()

    # 2. Award pending AI refund if subscription actually expired and changed
    if row:
        from services.subscription import award_pending_ai_refund
        award_pending_ai_refund(db, user_id)


def _public_payment_response(toss_result: dict):
    receipt = toss_result.get("receipt") or {}
    return {
        "status": toss_result.get("status"),
        "orderId": toss_result.get("orderId"),
        "orderName": toss_result.get("orderName"),
        "amount": toss_result.get("totalAmount"),
        "method": toss_result.get("method"),
        "approvedAt": toss_result.get("approvedAt"),
        "receiptUrl": receipt.get("url"),
    }


def _to_iso_or_value(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


async def _confirm_toss_payment(
    payment_key: str,
    order_id: str,
    amount: int
):
    if not TOSS_SECRET_KEY:
        raise Exception(
            "TOSS_SECRET_KEY가 .env에서 로드되지 않았습니다."
        )

    secret_key = (
        f"{TOSS_SECRET_KEY}:"
    )

    encoded_key = base64.b64encode(
        secret_key.encode()
    ).decode()

    headers = {
        "Authorization":
            f"Basic {encoded_key}",

        "Content-Type":
            "application/json",
    }

    payload = {
        "paymentKey":
            payment_key,

        "orderId":
            order_id,

        "amount":
            amount,
    }

    request = urllib.request.Request(
        "https://api.tosspayments.com/v1/payments/confirm",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            raise Exception(error_body) from exc

def get_my_credit_balance(db: Session, user_id: str):
    row = db.execute(
        text("""
            SELECT COALESCE(b.balance, 0) AS balance, u.role
            FROM users u
            LEFT JOIN user_credit_balances b ON u.user_id = b.user_id
            WHERE u.user_id = :user_id
        """),
        {"user_id": user_id},
    ).fetchone()

    if not row:
        return {"balance": 0}

    balance = int(row._mapping["balance"] if row._mapping["balance"] is not None else 0)
    role = row._mapping["role"]

    if role == "admin" and balance < 5:
        amount_to_add = 50 - balance
        db.execute(
            text("""
                INSERT INTO user_credit_balances (user_id, balance, updated_at)
                VALUES (:user_id, 50, NOW())
                ON CONFLICT (user_id) DO UPDATE 
                SET balance = 50, updated_at = NOW()
            """),
            {"user_id": user_id}
        )
        db.execute(
            text("""
                INSERT INTO credit_ledger (
                    user_id, amount, balance_after, entry_type, source_type, description, created_at
                ) VALUES (
                    :user_id, :amount, 50, 'earn', 'admin_recharge', '관리자 자동 충전', NOW()
                )
            """),
            {"user_id": user_id, "amount": amount_to_add}
        )
        db.commit()
        balance = 50

    return {"balance": balance}


def get_my_payment_info(db: Session, user_id: str):
    # 현재 플랜은 단일 subscription row가 아니라 유효 기간과 plan_rank로 계산한다.
    current = resolve_current_plan(db, user_id)
    current_plan = current["current_plan"]
    current_subscription = current["current_subscription"]
    plan_code = current_plan["plan_code"]
    plan_name = current_plan["plan_name"]

    latest_upgrade_proration = None
    proration_row = db.execute(
        text("""
            SELECT
                pc.remaining_amount,
                pc.target_plan_amount,
                pc.discount_amount,
                pc.charged_amount,
                pc.applied_at,
                from_p.plan_name AS from_plan_name,
                to_p.plan_name AS to_plan_name
            FROM subscription_plan_changes pc
            LEFT JOIN plans from_p ON from_p.plan_id = pc.from_plan_id
            LEFT JOIN plans to_p ON to_p.plan_id = pc.to_plan_id
            WHERE pc.user_id = :user_id
              AND pc.change_type = 'upgrade'
              AND pc.status = 'applied'
            ORDER BY pc.applied_at DESC
            LIMIT 1
        """),
        {"user_id": user_id}
    ).fetchone()
    if proration_row:
        pro = proration_row._mapping
        latest_upgrade_proration = {
            "from_plan_name": pro.get("from_plan_name"),
            "to_plan_name": pro.get("to_plan_name"),
            "remaining_amount": int(pro.get("remaining_amount") or 0),
            "target_plan_amount": int(pro.get("target_plan_amount") or 0),
            "discount_amount": int(pro.get("discount_amount") or 0),
            "charged_amount": int(pro.get("charged_amount") or 0),
            "applied_at": pro["applied_at"].isoformat() if pro.get("applied_at") else None,
        }

    scheduled_row = db.execute(
        text("""
            SELECT
                pc.plan_change_id,
                pc.change_type,
                pc.status,
                pc.effective_at,
                p.plan_id,
                p.plan_code,
                p.plan_name
            FROM subscription_plan_changes pc
            LEFT JOIN plans p ON p.plan_id = pc.to_plan_id
            WHERE pc.user_id = :user_id
              AND pc.status = 'scheduled'
            ORDER BY pc.effective_at ASC, pc.created_at DESC
            LIMIT 1
        """),
        {"user_id": user_id},
    ).fetchone()

    scheduled_plan_change = None
    if scheduled_row:
        scheduled = scheduled_row._mapping
        scheduled_plan_change = {
            "plan_change_id": str(scheduled["plan_change_id"]),
            "change_type": scheduled.get("change_type"),
            "status": scheduled.get("status"),
            "effective_at": (
                scheduled["effective_at"].isoformat()
                if scheduled.get("effective_at")
                else None
            ),
            "to_plan_id": str(scheduled["plan_id"]) if scheduled.get("plan_id") else None,
            "to_plan_code": (
                (scheduled.get("plan_code") or "").lower()
                if scheduled.get("plan_code")
                else None
            ),
            "to_plan_name": scheduled.get("plan_name"),
        }

    # 2. 유저의 가장 최근 성공 결제 내역 조회 (영수증 모달용)
    payment_row = db.execute(
        text("""
            SELECT 
                payment_id,
                order_name,
                payment_method,
                total_amount,
                approved_at,
                receipt_url
            FROM payments
            WHERE user_id = :user_id AND status = 'success'
            ORDER BY approved_at DESC
            LIMIT 1
        """),
        {"user_id": user_id}
    ).fetchone()

    payment_info = None
    if payment_row:
        p = payment_row._mapping
        payment_info = {
            "orderId": str(p["payment_id"]),
            "orderName": p["order_name"],
            "method": p["payment_method"],
            "amount": p["total_amount"],
            "approvedAt": p["approved_at"].isoformat() if p["approved_at"] else None,
            "receiptUrl": p["receipt_url"]
        }

    payment_rows = db.execute(
        text("""
            SELECT
                payment_id,
                order_name,
                pg_provider,
                amount,
                created_at
            FROM payments
            WHERE user_id = :user_id
              AND status IN ('DONE', 'success')
            ORDER BY created_at DESC
        """),
        {"user_id": user_id}
    ).fetchall()

    payment_history = []
    for row in payment_rows:
        p = row._mapping
        payment_history.append({
            "orderId": str(p["payment_id"]),
            "orderName": p["order_name"],
            "method": p.get("pg_provider") or "간편결제",
            "amount": p["amount"],
            "approvedAt": p["created_at"].isoformat() if p["created_at"] else None,
        })

    return {
        "is_premium": plan_code != "free",
        "plan_code": plan_code,
        "plan_name": plan_name,
        "plan_date": (
            current_subscription["current_period_start"]
            if current_subscription
            else None
        ),
        "current_plan": current_plan,
        "current_subscription": current_subscription,
        "latest_upgrade_proration": latest_upgrade_proration,
        "scheduled_plan_change": scheduled_plan_change,
        "payment_info": payment_info,
        "payment_history": payment_history,
    }


# [한글 주석] 토스 빌링키 발급 API를 호출하는 헬퍼 함수
async def _issue_toss_billing_key(
    auth_key: str,
    customer_key: str
):
    if not TOSS_SECRET_KEY:
        raise Exception("TOSS_SECRET_KEY가 .env에서 로드되지 않았습니다.")

    secret_key = f"{TOSS_SECRET_KEY}:"
    encoded_key = base64.b64encode(secret_key.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "authKey": auth_key,
        "customerKey": customer_key,
    }

    request = urllib.request.Request(
        "https://api.tosspayments.com/v1/billing/authorizations/issue",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            raise Exception(error_body) from exc


# [한글 주석] 발급받은 토스 빌링키로 정기 자동결제 승인 API를 호출하는 헬퍼 함수
async def _confirm_toss_billing_payment(
    billing_key: str,
    customer_key: str,
    order_id: str,
    amount: int,
    order_name: str
):
    if not TOSS_SECRET_KEY:
        raise Exception("TOSS_SECRET_KEY가 .env에서 로드되지 않았습니다.")

    secret_key = f"{TOSS_SECRET_KEY}:"
    encoded_key = base64.b64encode(secret_key.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "customerKey": customer_key,
        "amount": amount,
        "orderId": order_id,
        "orderName": order_name,
    }

    url = f"https://api.tosspayments.com/v1/billing/{billing_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            raise Exception(error_body) from exc


# [한글 주석] 프런트엔드 요청에 대응하여 빌링키 발급, 최초 1회 승인 및 구독 개시를 처리하는 비즈니스 로직 함수
async def confirm_billing_payment(
    db: Session,
    auth_key: str,
    customer_key: str,
    plan_code: str,
    user_id: str
):
    try:
        # 1. plan_code에 해당하는 active 플랜 정보 조회
        plan_row = db.execute(
            text("""
                SELECT plan_id, plan_name, price_amount, credits
                FROM plans
                WHERE LOWER(plan_code) = LOWER(:plan_code)
                  AND status = 'active'
                LIMIT 1
            """),
            {"plan_code": plan_code}
        ).fetchone()

        if not plan_row:
            raise ValueError("유효하지 않거나 활성화되지 않은 플랜 코드입니다.")

        plan = plan_row._mapping
        plan_id = plan["plan_id"]
        plan_name = plan["plan_name"]

        # 업그레이드 여부 및 정산 금액 사전 계산
        plan_change = subscription_service.classify_plan_change(
            db=db,
            user_id=user_id,
            to_plan_id=str(plan_id),
        )
        is_upgrade = (plan_change["change_type"] == "upgrade" and plan_change.get("current_subscription"))

        if is_upgrade:
            amount = plan_change["proration"]["charged_amount"]
        else:
            amount = plan["price_amount"]

        # 2. 토스 빌링키 발급 API 호출
        toss_billing_result = await _issue_toss_billing_key(auth_key, customer_key)
        billing_key = toss_billing_result.get("billingKey")
        if not billing_key:
            raise ValueError(f"빌링키 발급 실패: {toss_billing_result.get('message', '알 수 없는 오류')}")

        # 3. payments 결제 테이블에 ready 상태의 임시 결제 내역 기록
        import uuid
        payment_id = str(uuid.uuid4())

        db.execute(
            text("""
                INSERT INTO payments (
                    payment_id,
                    user_id,
                    subscription_id,
                    product_type,
                    plan_id,
                    amount,
                    status,
                    pg_provider,
                    order_name,
                    created_at
                )
                VALUES (
                    CAST(:payment_id AS uuid),
                    :user_id,
                    NULL,
                    'subscription',
                    CAST(:plan_id AS uuid),
                    :amount,
                    'ready',
                    'toss',
                    :order_name,
                    NOW()
                )
            """),
            {
                "payment_id": payment_id,
                "user_id": user_id,
                "plan_id": plan_id,
                "amount": amount,
                "order_name": f"Garim {plan_name} 정기구독",
            }
        )

        # 4. 토스 자동결제 승인 API로 요금 청구 (0원인 경우 Toss API 호출 건너뛰기)
        if is_upgrade and amount == 0:
            toss_status = "SUCCESS"
            receipt_url = None
            from datetime import datetime
            toss_result = {
                "status": "DONE",
                "paymentKey": "MOCK_ZERO_UPGRADE_KEY_" + payment_id,
                "lastTransactionKey": "MOCK_ZERO_TRANS_KEY_" + payment_id,
                "method": "차액정산(0원)",
                "totalAmount": 0,
                "balanceAmount": 0,
                "currency": "KRW",
                "requestedAt": datetime.now().isoformat(),
                "approvedAt": datetime.now().isoformat(),
                "isPartialCancelable": False,
                "receipt": {"url": None}
            }
        else:
            toss_result = await _confirm_toss_billing_payment(
                billing_key=billing_key,
                customer_key=customer_key,
                order_id=payment_id,
                amount=amount,
                order_name=f"Garim {plan_name} 정기구독"
            )
            toss_status = str(toss_result.get("status", "")).upper()

        if toss_status not in ("DONE", "SUCCESS"):
            # 결제 실패 시 payments 테이블만 failed로 갱신하여 즉시 기록하고 롤백합니다.
            db.execute(
                text("""
                    UPDATE payments
                    SET status = 'failed', updated_at = NOW()
                    WHERE payment_id = CAST(:payment_id AS uuid)
                """),
                {"payment_id": payment_id}
            )
            db.commit()
            raise ValueError(f"정기결제 승인 실패: {toss_result.get('message', '알 수 없는 PG 오류')}")

        # 5. 결제 승인 성공 시에만 비로소 DB에 빌링키를 대칭 암호화하여 저장
        card_info = toss_billing_result.get("card") or {}
        card_company = card_info.get("company")
        masked_card_number = card_info.get("number")
        method_type = "card" if card_info else "unknown"

        from services import billing as billing_service
        saved_billing = billing_service.save_billing_key(
            db=db,
            user_id=user_id,
            billing_key=billing_key,
            customer_key=customer_key,
            card_company=card_company,
            masked_card_number=masked_card_number,
            method_type=method_type,
            pg_provider="toss"
        )
        billing_key_id = saved_billing["billing_key_id"]

        # 6. 결제 성공 시 payments 테이블 상태 업데이트
        easy_pay = toss_result.get("easyPay") or {}
        easy_pay_provider = easy_pay.get("provider")
        receipt = toss_result.get("receipt") or {}
        receipt_url = receipt.get("url")

        db.execute(
            text("""
                UPDATE payments
                SET
                    status = 'success',
                    pg_transaction_id = :payment_key,
                    last_transaction_key = :last_transaction_key,
                    payment_method = :payment_method,
                    easy_pay_provider = :easy_pay_provider,
                    toss_status = :toss_status,
                    total_amount = :total_amount,
                    balance_amount = :balance_amount,
                    currency = :currency,
                    requested_at = CAST(:requested_at AS timestamp),
                    approved_at = CAST(:approved_at AS timestamp),
                    receipt_url = :receipt_url,
                    is_partial_cancelable = :is_partial_cancelable,
                    paid_at = NOW(),
                    updated_at = NOW()
                WHERE payment_id = CAST(:payment_id AS uuid)
            """),
            {
                "payment_id": payment_id,
                "payment_key": toss_result.get("paymentKey"),
                "last_transaction_key": toss_result.get("lastTransactionKey"),
                "payment_method": toss_result.get("method"),
                "easy_pay_provider": easy_pay_provider,
                "toss_status": toss_status,
                "total_amount": toss_result.get("totalAmount"),
                "balance_amount": toss_result.get("balanceAmount"),
                "currency": toss_result.get("currency") or "KRW",
                "requested_at": toss_result.get("requestedAt"),
                "approved_at": toss_result.get("approvedAt"),
                "receipt_url": receipt_url,
                "is_partial_cancelable": toss_result.get("isPartialCancelable"),
            }
        )

        # 7. 구독 정보 생성 및 갱신 (upgrade vs create/extend 분기)
        if is_upgrade:
            subscription = subscription_service.apply_upgrade_with_proration(
                db=db,
                user_id=user_id,
                from_subscription_id=plan_change["current_subscription"].get("subscription_id"),
                to_plan_id=plan_id,
                payment_id=payment_id,
                billing_key_id=billing_key_id,
            )
        else:
            subscription = subscription_service.create_or_extend_subscription(
                db=db,
                user_id=user_id,
                plan_id=plan_id,
                payment_id=payment_id,
                billing_key_id=billing_key_id,
            )

        subscription_id = subscription["subscription_id"]

        # 8. 결제 내역과 구독 ID 연계
        db.execute(
            text("""
                UPDATE payments
                SET
                    subscription_id = CAST(:subscription_id AS uuid),
                    updated_at = NOW()
                WHERE payment_id = CAST(:payment_id AS uuid)
            """),
            {
                "subscription_id": subscription_id,
                "payment_id": payment_id,
            }
        )

        # 9. 구독 플랜 기본 크레딧 지급
        grant_amount = int(plan.get("credits") or 0)
        if grant_amount > 0:
            _add_user_credits(
                db=db,
                user_id=user_id,
                amount=grant_amount,
                entry_type="grant",
                source_type="subscription",
                source_id=subscription_id,
                description=f"구독 플랜 기본 크레딧 지급: {plan_code}",
            )

        db.commit()

        return {
            "status": toss_status,
            "orderId": payment_id,
            "orderName": f"Garim {plan_name} 정기구독",
            "amount": amount,
            "method": toss_result.get("method"),
            "approvedAt": toss_result.get("approvedAt"),
            "receiptUrl": receipt_url,
        }
    except Exception:
        db.rollback()
        raise

