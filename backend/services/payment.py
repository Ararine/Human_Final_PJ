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

    subscription_query = text("""
        INSERT INTO subscriptions (
            user_id,
            plan_id,
            status,
            started_at,
            remaining_quota,
            created_at,
            updated_at
        )
        VALUES (
            :user_id,
            :plan_id,
            'pending',
            NOW(),
            0,
            NOW(),
            NOW()
        )
        RETURNING subscription_id
    """)

    insert_query = text("""
        INSERT INTO payments (
            user_id,
            subscription_id,
            amount,
            status,
            pg_provider,
            created_at
        )
        VALUES (
            :user_id,
            :subscription_id,
            :amount,
            'ready',
            'toss',
            NOW()
        )
        RETURNING payment_id, amount, subscription_id
    """)

    try:
        subscription_inserted = db.execute(
            subscription_query,
            {
                "user_id": user_id,
                "plan_id": plan["plan_id"],
            }
        ).fetchone()
        subscription = subscription_inserted._mapping
        inserted = db.execute(
            insert_query,
            {
                "user_id": user_id,
                "subscription_id": subscription["subscription_id"],
                "amount": amount,
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
                p.subscription_id,
                pl.credits,
                pl.monthly_quota
            FROM payments p
            LEFT JOIN subscriptions s
                ON s.subscription_id = p.subscription_id
            LEFT JOIN plans pl
                ON pl.plan_id = s.plan_id
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
            remaining_quota = payment.get("credits")
            if remaining_quota is None:
                remaining_quota = payment.get("monthly_quota")

            db.execute(
                text("""
                    UPDATE subscriptions
                    SET
                        status = 'active',
                        started_at = NOW(),
                        ended_at = NULL,
                        renew_at = NOW() + INTERVAL '1 month',
                        remaining_quota = :remaining_quota,
                        updated_at = NOW()
                    WHERE subscription_id = :subscription_id
                """),
                {
                    "subscription_id": subscription_id,
                    "remaining_quota": remaining_quota,
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
