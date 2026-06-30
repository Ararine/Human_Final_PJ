import base64
import json
import os
import uuid
from urllib import error, request

# Toss Payments API 베이스 URL
TOSS_BILLING_API_BASE_URL = "https://api.tosspayments.com"


def _is_test_mode():
    # TOSS_BILLING_TEST_MODE 환경변수가 참(True, 1, Yes)으로 설정되었는지 판별합니다.
    return os.getenv("TOSS_BILLING_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def _basic_auth_header(secret_key: str):
    # Toss Payments API 호출에 필요한 Basic 인증 토큰 헤더를 생성합니다.
    token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def charge_with_billing_key(
    billing_key,
    customer_key,
    amount,
    order_id,
    order_name,
):
    """
    subscription_renewal._charge_subscription()에서 주입받아 호출할 Toss Billing 결제 요청 함수입니다.

    반환 딕셔너리 포맷은 subscription_renewal.py에서 기대하는 구조를 준수합니다.
    - success: 결제 성공 여부 (bool)
    - pg_transaction_id: PG 거래 식별자 (str)
    - method: 결제 수단 (str)
    - failure_code: 실패 코드 (str, 선택)
    - failure_message: 실패 메시지 (str, 선택)
    """
    # 1. 가상 결제 테스트 모드인 경우
    if _is_test_mode():
        return {
            "success": True,
            "pg_transaction_id": f"test-renewal-{uuid.uuid4()}",
            "method": "billing",
        }

    # 2. 실제 API 호출을 위한 Toss 시크릿 키 검증
    secret_key = os.getenv("TOSS_SECRET_KEY")
    if not secret_key:
        return {
            "success": False,
            "failure_code": "toss_secret_key_missing",
            "failure_message": "TOSS_SECRET_KEY is not configured.",
        }

    payload = {
        "customerKey": customer_key,
        "amount": int(amount),
        "orderId": order_id,
        "orderName": order_name,
    }

    url = f"{TOSS_BILLING_API_BASE_URL}/v1/billing/{billing_key}"
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": _basic_auth_header(secret_key),
            "Content-Type": "application/json",
        },
    )

    try:
        # 타임아웃 15초 지정하여 API 요청
        with request.urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "pg_transaction_id": body.get("paymentKey") or body.get("transactionKey"),
                "method": body.get("method") or "billing",
                "raw": body,
            }
    except error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return {
            "success": False,
            "failure_code": body.get("code") or f"http_{exc.code}",
            "failure_message": body.get("message") or str(exc),
            "raw": body,
        }
    except Exception as exc:
        return {
            "success": False,
            "failure_code": "toss_billing_request_failed",
            "failure_message": str(exc),
        }
