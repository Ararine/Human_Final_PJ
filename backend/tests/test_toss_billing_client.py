import json
from unittest.mock import MagicMock

# 아직 구현되지 않은 toss_billing_client 임포트 (실패 유도)
from services import toss_billing_client


def test_charge_with_billing_key_returns_fake_success_in_test_mode(monkeypatch):
    # TOSS_BILLING_TEST_MODE=true 일 때 가상의 테스트 성공 응답 검증
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "true")
    monkeypatch.delenv("TOSS_SECRET_KEY", raising=False)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="test_billing_key",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is True
    assert result["method"] == "billing"
    assert result["pg_transaction_id"].startswith("test-renewal-")


def test_charge_with_billing_key_fails_without_secret_key(monkeypatch):
    # 테스트 모드가 아니고 시크릿 키가 없을 때 실패 검증
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "false")
    monkeypatch.delenv("TOSS_SECRET_KEY", raising=False)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="test_billing_key",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is False
    assert result["failure_code"] == "toss_secret_key_missing"


def test_charge_with_billing_key_calls_toss_api(monkeypatch):
    # 실제 Toss API를 호출하는 경우에 대한 모킹 테스트 검증
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "false")
    monkeypatch.setenv("TOSS_SECRET_KEY", "test_sk_example")

    class FakeResponse:
        status = 200

        def read(self):
            return json.dumps({
                "paymentKey": "payment-key-1",
                "method": "카드",
                "status": "DONE",
            }).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    urlopen_mock = MagicMock(return_value=FakeResponse())
    monkeypatch.setattr(toss_billing_client.request, "urlopen", urlopen_mock)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="billing-key-1",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is True
    assert result["pg_transaction_id"] == "payment-key-1"
    assert result["method"] == "카드"
    urlopen_mock.assert_called_once()
