import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import main
from services import auth, payment as payment_service

client = TestClient(main.app)


def test_confirm_payment(monkeypatch):
    async def fake_confirm_payment(db, payment_key, order_id, amount):
        return {
            "status": "DONE",
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": amount,
        }

    monkeypatch.setattr(payment_service, "confirm_payment", fake_confirm_payment)

    response = client.post(
        "/payment/confirm",
        json={
            "paymentKey": "test_key",
            "orderId": "order_1",
            "amount": 100,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DONE"
    assert response.json()["paymentKey"] == "test_key"


def test_create_temp_order_unauthorized():
    response = client.post(
        "/payment/temp-order",
        json={"plan_code": "pro", "amount": 2900},
    )
    assert response.status_code == 401


def test_create_temp_order_success(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    async def fake_create_temp_order(db, user_id, plan_code, amount):
        assert user_id == fake_user["id"]
        assert plan_code == "pro"
        assert amount == 2900
        return {
            "payment_id": "payment-uuid-1234",
            "amount": 2900,
            "plan_name": "Pro Plan",
            "plan_code": "pro",
        }

    monkeypatch.setattr(payment_service, "create_temp_order", fake_create_temp_order)

    response = client.post(
        "/payment/temp-order",
        json={"plan_code": "pro", "amount": 2900},
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["orderId"] == "payment-uuid-1234"
    assert data["amount"] == 2900
    assert data["orderName"] == "Pro Plan"
    assert data["planCode"] == "pro"


def test_create_temp_order_invalid_amount(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    async def fake_create_temp_order_fail(db, user_id, plan_code, amount):
        raise ValueError("requested amount does not match plan price")

    monkeypatch.setattr(payment_service, "create_temp_order", fake_create_temp_order_fail)

    response = client.post(
        "/payment/temp-order",
        json={"plan_code": "pro", "amount": 9999},
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 400
    assert "requested amount does not match plan price" in response.json()["detail"]


@pytest.mark.anyio
async def test_service_create_temp_order_success():
    db_mock = MagicMock()

    plan_mock_row = MagicMock()
    plan_mock_row._mapping = {
        "plan_id": "plan-uuid-1234",
        "plan_name": "Pro Plan",
        "price_amount": 2900,
        "is_active": True,
        "monthly_quota": 50,
        "credits": 50,
    }

    subscription_mock_row = MagicMock()
    subscription_mock_row._mapping = {
        "subscription_id": "subscription-uuid-1234",
    }

    payment_mock_row = MagicMock()
    payment_mock_row._mapping = {
        "payment_id": "payment-uuid-5678",
        "amount": 2900,
        "subscription_id": "subscription-uuid-1234",
    }

    plan_result = MagicMock()
    plan_result.fetchone.return_value = plan_mock_row
    subscription_result = MagicMock()
    subscription_result.fetchone.return_value = subscription_mock_row
    payment_result = MagicMock()
    payment_result.fetchone.return_value = payment_mock_row
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    db_mock.execute.side_effect = [plan_result, restore_result, subscription_result, payment_result]

    result = await payment_service.create_temp_order(
        db=db_mock,
        user_id="user-uuid-1234",
        plan_code="pro",
        amount=2900,
    )

    assert result["payment_id"] == "payment-uuid-5678"
    assert result["amount"] == 2900
    assert result["plan_name"] == "Pro Plan"
    assert result["plan_code"] == "pro"
    assert result["subscription_id"] == "subscription-uuid-1234"

    assert db_mock.execute.call_count == 4
    executed_sql = "\n".join(str(call.args[0]) for call in db_mock.execute.call_args_list)
    payment_insert_sql = str(db_mock.execute.call_args_list[3].args[0])
    payment_insert_params = db_mock.execute.call_args_list[3].args[1]
    assert "INSERT INTO subscriptions" not in executed_sql
    assert "INSERT INTO payments" in payment_insert_sql
    assert "order_name" in payment_insert_sql
    assert payment_insert_params["subscription_id"] == "subscription-uuid-1234"
    assert payment_insert_params["plan_code"] == "pro"
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_service_confirm_payment_returns_existing_success(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-1",
        "amount": 2900,
        "status": "success",
        "pg_transaction_id": "payment-key-1",
        "paid_at": "2026-05-29T00:00:00",
        "order_name": "Garim Pro",
        "payment_method": "card",
        "receipt_url": "https://dashboard.tosspayments.com/receipt/existing",
        "approved_at": "2026-05-29T00:00:00",
    }
    db_mock.execute.return_value.fetchone.return_value = payment_row

    toss_call = MagicMock()
    monkeypatch.setattr(payment_service, "_confirm_toss_payment", toss_call)

    result = await payment_service.confirm_payment(
        db=db_mock,
        payment_key="payment-key-1",
        order_id="payment-uuid-1",
        amount=2900,
    )

    assert result["status"] == "success"
    assert result["orderId"] == "payment-uuid-1"
    assert result["orderName"] == "Garim Pro"
    assert result["method"] == "card"
    assert result["receiptUrl"] == "https://dashboard.tosspayments.com/receipt/existing"
    assert "paymentKey" not in result
    toss_call.assert_not_called()


@pytest.mark.anyio
async def test_service_confirm_payment_rejects_amount_mismatch():
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-2",
        "amount": 2900,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
    }
    db_mock.execute.return_value.fetchone.return_value = payment_row

    with pytest.raises(ValueError):
        await payment_service.confirm_payment(
            db=db_mock,
            payment_key="payment-key-2",
            order_id="payment-uuid-2",
            amount=9999,
        )


@pytest.mark.anyio
async def test_service_confirm_payment_saves_only_allowed_toss_fields(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-3",
        "amount": 2900,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
        "user_id": "user-uuid-3",
        "subscription_id": "subscription-uuid-3",
        "plan_id": "plan-uuid-pro",
        "credits": 50,
        "monthly_quota": 50,
    }
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    carryover_row = MagicMock()
    carryover_row._mapping = {"credits": 12}
    carryover_result = MagicMock()
    carryover_result.fetchone.return_value = carryover_row
    payment_select_result = MagicMock()
    payment_select_result.fetchone.return_value = payment_row
    db_mock.execute.side_effect = [
        payment_select_result,
        MagicMock(),
        restore_result,
        carryover_result,
        MagicMock(),
    ]

    async def fake_toss_confirm(payment_key, order_id, amount):
        return {
            "status": "DONE",
            "paymentKey": payment_key,
            "orderId": order_id,
            "orderName": "Garim Pro",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "lastTransactionKey": "tx-key-3",
            "method": "card",
            "easyPay": {
                "provider": "kakaopay",
            },
            "approvedAt": "2026-05-29T12:00:00+09:00",
            "requestedAt": "2026-05-29T11:59:30+09:00",
            "receipt": {
                "url": "https://dashboard.tosspayments.com/receipt/test",
            },
            "isPartialCancelable": True,
            "checkout": {
                "url": "https://api.tosspayments.com/v1/payments/test/checkout",
            },
            "secret": "ps_should_not_be_saved",
            "version": "2024-06-01",
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_payment", fake_toss_confirm)

    result = await payment_service.confirm_payment(
        db=db_mock,
        payment_key="payment-key-3",
        order_id="payment-uuid-3",
        amount=2900,
    )

    assert result["status"] == "DONE"
    assert result["orderId"] == "payment-uuid-3"
    assert result["orderName"] == "Garim Pro"
    assert result["amount"] == 2900
    assert result["method"] == "card"
    assert result["receiptUrl"] == "https://dashboard.tosspayments.com/receipt/test"
    assert "paymentKey" not in result
    assert "lastTransactionKey" not in result
    assert "checkout" not in result
    assert "secret" not in result
    assert "version" not in result
    assert db_mock.execute.call_count == 5
    payment_update_params = db_mock.execute.call_args_list[1].args[1]
    subscription_update_sql = str(db_mock.execute.call_args_list[4].args[0])
    subscription_update_params = db_mock.execute.call_args_list[4].args[1]
    assert payment_update_params["last_transaction_key"] == "tx-key-3"
    assert payment_update_params["order_name"] == "Garim Pro"
    assert payment_update_params["payment_method"] == "card"
    assert payment_update_params["easy_pay_provider"] == "kakaopay"
    assert payment_update_params["toss_status"] == "DONE"
    assert payment_update_params["total_amount"] == 2900
    assert payment_update_params["balance_amount"] == 2900
    assert payment_update_params["currency"] == "KRW"
    assert payment_update_params["requested_at"] == "2026-05-29T11:59:30+09:00"
    assert payment_update_params["approved_at"] == "2026-05-29T12:00:00+09:00"
    assert payment_update_params["receipt_url"] == "https://dashboard.tosspayments.com/receipt/test"
    assert payment_update_params["is_partial_cancelable"] is True
    assert "checkout_url" not in payment_update_params
    assert "raw_response" not in payment_update_params
    assert "secret" not in payment_update_params
    assert "version" not in payment_update_params
    assert "plan_id = :plan_id" in subscription_update_sql
    assert "ended_at = NOW() + INTERVAL '30 days'" in subscription_update_sql
    assert "renew_at = NOW() + INTERVAL '30 days'" in subscription_update_sql
    assert "remaining_credits = :remaining_credits" in subscription_update_sql
    assert "remaining_quota" not in subscription_update_sql
    assert subscription_update_params["plan_id"] == "plan-uuid-pro"
    assert subscription_update_params["remaining_credits"] == 62
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_service_confirm_payment_rejects_toss_result_mismatch(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-4",
        "amount": 2900,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
        "subscription_id": "subscription-uuid-4",
        "credits": 50,
        "monthly_quota": 50,
    }
    db_mock.execute.return_value.fetchone.return_value = payment_row

    async def fake_toss_confirm(payment_key, order_id, amount):
        return {
            "status": "DONE",
            "paymentKey": payment_key,
            "orderId": "different-order-id",
            "totalAmount": amount,
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_payment", fake_toss_confirm)

    with pytest.raises(ValueError):
        await payment_service.confirm_payment(
            db=db_mock,
            payment_key="payment-key-4",
            order_id="payment-uuid-4",
            amount=2900,
        )

    db_mock.commit.assert_not_called()
