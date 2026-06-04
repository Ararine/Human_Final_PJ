import os
import base64
import json
import urllib.error
import urllib.request
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

load_dotenv()

TOSS_SECRET_KEY = os.getenv(
    "TOSS_SECRET_KEY"
)

async def create_temp_order(
    db: Session,
    user_id: str,
    plan_code: str,
    amount: int
):
    plan_code_lower = plan_code.lower()

    plan_query = text("""
        SELECT
            plan_id,
            plan_name,
            price_amount,
            is_active,
            monthly_quota,
            credits
        FROM plans
        WHERE LOWER(plan_code) = :plan_code
    """)
    result = db.execute(plan_query, {"plan_code": plan_code_lower}).fetchone()

    if not result:
        raise ValueError("유효하지 않은 요금제 코드입니다.")

    plan = result._mapping

    if not plan["is_active"]:
        raise ValueError("비활성화된 요금제입니다.")

    if plan["price_amount"] != amount:
        raise ValueError("요청 금액이 요금제 가격과 일치하지 않습니다.")

    _restore_free_plan_for_expired_subscriptions(db, user_id)

    insert_query = text("""
        INSERT INTO payments (
            user_id,
            subscription_id,
            amount,
            status,
            pg_provider,
            order_name,
            created_at
        )
        VALUES (
            :user_id,
            :subscription_id,
            :amount,
            'ready',
            'toss',
            :plan_code,
            NOW()
        )
        RETURNING payment_id, amount, subscription_id
    """)

    try:
        subscription = _get_user_subscription(db, user_id)
        if not subscription:
            raise ValueError("사용자 구독 정보를 찾을 수 없습니다.")
        inserted = db.execute(
            insert_query,
            {
                "user_id": user_id,
                "subscription_id": subscription["subscription_id"],
                "amount": amount,
                "plan_code": plan_code_lower,
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
        "plan_name": plan["plan_name"],
        "plan_code": plan_code_lower,
        "subscription_id": str(payment["subscription_id"]),
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
                pl.plan_id,
                pl.credits,
                pl.monthly_quota,
                pl.plan_code
            FROM payments p
            LEFT JOIN subscriptions s
                ON s.subscription_id = p.subscription_id
            LEFT JOIN plans pl
                ON LOWER(pl.plan_code) = LOWER(p.order_name)
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
        toss_result = await _confirm_toss_payment(payment_key, order_id, amount)
        toss_status = str(toss_result.get("status", "")).upper()
        if toss_status not in ("DONE", "SUCCESS"):
            return _public_payment_response(toss_result)

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
                "payment_key": payment_key,
                "order_id": order_id,
                "last_transaction_key": toss_result.get("lastTransactionKey"),
                "order_name": toss_result.get("orderName"),
                "payment_method": toss_result.get("method"),
                "easy_pay_provider": (toss_result.get("easyPay") or {}).get("provider"),
                "toss_status": toss_status,
                "total_amount": toss_result.get("totalAmount"),
                "balance_amount": toss_result.get("balanceAmount"),
                "currency": toss_result.get("currency") or "KRW",
                "requested_at": toss_result.get("requestedAt"),
                "approved_at": toss_result.get("approvedAt"),
                "receipt_url": (toss_result.get("receipt") or {}).get("url"),
                "is_partial_cancelable": toss_result.get("isPartialCancelable"),
            },
        )
        subscription_id = payment.get("subscription_id")
        if subscription_id:
            user_id = payment.get("user_id")
            _restore_free_plan_for_expired_subscriptions(db, user_id)
            carried_credits = _get_subscription_credits(db, subscription_id)
            remaining_credits = carried_credits + _get_plan_credits(payment)

            db.execute(
                text("""
                    UPDATE subscriptions
                    SET
                        plan_id = :plan_id,
                        status = 'active',
                        started_at = NOW(),
                        ended_at = NOW() + INTERVAL '30 days',
                        renew_at = NOW() + INTERVAL '30 days',
                        remaining_credits = :remaining_credits,
                        updated_at = NOW()
                    WHERE subscription_id = :subscription_id
                """),
                {
                    "subscription_id": subscription_id,
                    "plan_id": payment.get("plan_id"),
                    "remaining_credits": remaining_credits,
                },
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


def _get_plan_credits(payment):
    credits = payment.get("credits")
    if credits is None:
        credits = payment.get("monthly_quota")
    return int(credits or 0)


def _get_user_subscription(db: Session, user_id):
    row = db.execute(
        text("""
            SELECT subscription_id, remaining_credits
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


def _get_subscription_credits(db: Session, subscription_id):
    row = db.execute(
        text("""
            SELECT COALESCE(remaining_credits, 0) AS credits
            FROM subscriptions
            WHERE subscription_id = :subscription_id
        """),
        {"subscription_id": subscription_id},
    ).fetchone()
    mapping = row._mapping if hasattr(row, "_mapping") else row
    return int((mapping or {}).get("credits") or 0)


def _restore_free_plan_for_expired_subscriptions(db: Session, user_id):
    if not user_id:
        return

    db.execute(
        text("""
            UPDATE subscriptions
            SET
                plan_id = free_plan.plan_id,
                status = 'active',
                started_at = NOW(),
                ended_at = NULL,
                renew_at = NOW() + INTERVAL '30 days',
                remaining_credits = COALESCE(free_plan.credits, free_plan.monthly_quota, 0),
                updated_at = NOW()
            FROM (
                SELECT plan_id, credits, monthly_quota
                FROM plans
                WHERE LOWER(plan_code) = 'free'
                  AND is_active = TRUE
                LIMIT 1
            ) AS free_plan
            WHERE subscriptions.user_id = :user_id
              AND status = 'active'
              AND ended_at IS NOT NULL
              AND ended_at <= NOW()
        """),
        {"user_id": user_id},
    )


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

def get_my_payment_info(db: Session, user_id: str):
    # 1. 유저의 현재 활성화된 구독 플랜 조회
    plan_row = db.execute(
        text("""
            SELECT pl.plan_name, pl.plan_code
            FROM subscriptions s
            JOIN plans pl ON s.plan_id = pl.plan_id
            WHERE s.user_id = :user_id AND s.status = 'active'
            ORDER BY s.updated_at DESC
            LIMIT 1
        """),
        {"user_id": user_id}
    ).fetchone()

    plan_code = "free"
    if plan_row:
        plan_code = plan_row._mapping["plan_code"].lower()

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

    return {
        "is_premium": plan_code != "free",
        "payment_info": payment_info
    }
