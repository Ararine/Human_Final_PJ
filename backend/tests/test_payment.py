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
        json={"product_type": "subscription", "product_code": "pro", "amount": 2900},
    )
    assert response.status_code == 401


def test_create_temp_order_accepts_subscription_product_contract(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    async def fake_create_temp_order(db, user_id, product_type, product_code, amount):
        assert user_id == fake_user["id"]
        assert product_type == "subscription"
        assert product_code == "pro"
        assert amount == 2900
        return {
            "payment_id": "payment-uuid-1234",
            "amount": 2900,
            "order_name": "Pro Plan",
            "product_type": "subscription",
            "product_code": "pro",
        }

    monkeypatch.setattr(payment_service, "create_temp_order", fake_create_temp_order)

    response = client.post(
        "/payment/temp-order",
        json={"product_type": "subscription", "product_code": "pro", "amount": 2900},
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["orderId"] == "payment-uuid-1234"
    assert data["amount"] == 2900
    assert data["orderName"] == "Pro Plan"
    assert data["productType"] == "subscription"
    assert data["productCode"] == "pro"


def test_create_temp_order_accepts_credit_product_contract(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    async def fake_create_temp_order(db, user_id, product_type, product_code, amount):
        assert user_id == fake_user["id"]
        assert product_type == "credit"
        assert product_code == "credit_100"
        assert amount == 5000
        return {
            "payment_id": "payment-uuid-credit-100",
            "amount": 5000,
            "order_name": "100 Credits",
            "product_type": "credit",
            "product_code": "credit_100",
        }

    monkeypatch.setattr(payment_service, "create_temp_order", fake_create_temp_order)

    response = client.post(
        "/payment/temp-order",
        json={"product_type": "credit", "product_code": "credit_100", "amount": 5000},
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["orderId"] == "payment-uuid-credit-100"
    assert data["amount"] == 5000
    assert data["orderName"] == "100 Credits"
    assert data["productType"] == "credit"
    assert data["productCode"] == "credit_100"


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

    async def fake_create_temp_order_fail(db, user_id, product_type, product_code, amount):
        raise ValueError("requested amount does not match plan price")

    monkeypatch.setattr(payment_service, "create_temp_order", fake_create_temp_order_fail)

    response = client.post(
        "/payment/temp-order",
        json={"product_type": "subscription", "product_code": "pro", "amount": 9999},
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 400
    assert "requested amount does not match plan price" in response.json()["detail"]


@pytest.mark.anyio
async def test_service_create_temp_order_success():
    db_mock = MagicMock()

    plan_mock_row = MagicMock()
    plan_mock_row._mapping = {
        "product_id": "plan-uuid-1234",
        "product_code": "pro",
        "product_name": "Pro Plan",
        "price_amount": 2900,
        "is_active": True,
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
        "product_type": "subscription",
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
        product_type="subscription",
        product_code="pro",
        amount=2900,
    )

    assert result["payment_id"] == "payment-uuid-5678"
    assert result["amount"] == 2900
    assert result["order_name"] == "Pro Plan"
    assert result["product_type"] == "subscription"
    assert result["product_code"] == "pro"
    assert result["subscription_id"] == "subscription-uuid-1234"

    assert db_mock.execute.call_count == 4
    executed_sql = "\n".join(str(call.args[0]) for call in db_mock.execute.call_args_list)
    payment_insert_sql = str(db_mock.execute.call_args_list[3].args[0])
    payment_insert_params = db_mock.execute.call_args_list[3].args[1]
    assert "INSERT INTO subscriptions" not in executed_sql
    assert "INSERT INTO payments" in payment_insert_sql
    assert "order_name" in payment_insert_sql
    assert "product_type" in payment_insert_sql
    assert "plan_id" in payment_insert_sql
    assert payment_insert_params["subscription_id"] == "subscription-uuid-1234"
    assert payment_insert_params["product_type"] == "subscription"
    assert payment_insert_params["plan_id"] == "plan-uuid-1234"
    assert payment_insert_params["order_name"] == "Pro Plan"
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_service_create_temp_order_uses_credit_plans_for_credit():
    db_mock = MagicMock()

    credit_plan_row = MagicMock()
    credit_plan_row._mapping = {
        "product_id": "credit-plan-uuid-100",
        "product_code": "credit_100",
        "product_name": "100 Credits",
        "price_amount": 5000,
        "is_active": True,
        "base_credits": 100,
        "bonus_credits": 0,
    }

    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-credit-100",
        "amount": 5000,
        "subscription_id": None,
        "product_type": "credit",
    }

    credit_plan_result = MagicMock()
    credit_plan_result.fetchone.return_value = credit_plan_row
    payment_result = MagicMock()
    payment_result.fetchone.return_value = payment_row
    db_mock.execute.side_effect = [credit_plan_result, payment_result]

    result = await payment_service.create_temp_order(
        db=db_mock,
        user_id="user-uuid-1234",
        product_type="credit",
        product_code="credit_100",
        amount=5000,
    )

    assert result["payment_id"] == "payment-uuid-credit-100"
    assert result["amount"] == 5000
    assert result["order_name"] == "100 Credits"
    assert result["product_type"] == "credit"
    assert result["product_code"] == "credit_100"
    assert result["subscription_id"] is None

    assert db_mock.execute.call_count == 2
    product_select_sql = str(db_mock.execute.call_args_list[0].args[0])
    payment_insert_sql = str(db_mock.execute.call_args_list[1].args[0])
    payment_insert_params = db_mock.execute.call_args_list[1].args[1]
    assert "FROM credit_plans" in product_select_sql
    assert "INSERT INTO payments" in payment_insert_sql
    assert "credit_plan_id" in payment_insert_sql
    assert "\n                plan_id," not in payment_insert_sql
    assert payment_insert_params["product_type"] == "credit"
    assert payment_insert_params["credit_plan_id"] == "credit-plan-uuid-100"
    assert payment_insert_params["order_name"] == "100 Credits"
    assert payment_insert_params["subscription_id"] is None
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
        "product_type": "subscription",
        "plan_id": "plan-uuid-pro",
        "credit_plan_id": None,
        "plan_credits": 50,
        "plan_code": "pro",
        "base_credits": None,
        "bonus_credits": None,
        "credit_plan_code": None,
    }
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    balance_insert_row = MagicMock()
    balance_insert_row._mapping = {"balance": 50}
    balance_result = MagicMock()
    balance_result.fetchone.return_value = balance_insert_row
    payment_select_result = MagicMock()
    payment_select_result.fetchone.return_value = payment_row
    db_mock.execute.side_effect = [
        payment_select_result,  # 1: confirm SELECT
        MagicMock(),            # 2: UPDATE payments
        restore_result,         # 3: _restore_free_plan
        MagicMock(),            # 4: UPDATE subscriptions
        balance_result,         # 5: INSERT INTO user_credit_balances
        MagicMock(),            # 6: INSERT INTO credit_ledger
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
    assert db_mock.execute.call_count == 6
    payment_update_params = db_mock.execute.call_args_list[1].args[1]
    subscription_update_sql = str(db_mock.execute.call_args_list[3].args[0])
    subscription_update_params = db_mock.execute.call_args_list[3].args[1]
    balance_sql = str(db_mock.execute.call_args_list[4].args[0])
    ledger_sql = str(db_mock.execute.call_args_list[5].args[0])
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
    assert "remaining_credits" not in subscription_update_sql
    assert subscription_update_params["plan_id"] == "plan-uuid-pro"
    assert "INSERT INTO user_credit_balances" in balance_sql
    assert "INSERT INTO credit_ledger" in ledger_sql
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


def test_get_my_credit_balance_unauthorized():
    response = client.get("/payment/credits/me")
    assert response.status_code == 401


def test_get_my_credit_balance_returns_balance(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    def fake_get_credit_balance(db, user_id):
        assert user_id == fake_user["id"]
        return {"balance": 150}

    monkeypatch.setattr(payment_service, "get_my_credit_balance", fake_get_credit_balance)

    response = client.get(
        "/payment/credits/me",
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 150


def test_service_get_my_credit_balance_no_row():
    db_mock = MagicMock()
    db_mock.execute.return_value.fetchone.return_value = None

    result = payment_service.get_my_credit_balance(db=db_mock, user_id="user-uuid-new")

    assert result == {"balance": 0}


def test_service_get_my_credit_balance_existing():
    db_mock = MagicMock()
    row = MagicMock()
    row._mapping = {"balance": 300}
    db_mock.execute.return_value.fetchone.return_value = row

    result = payment_service.get_my_credit_balance(db=db_mock, user_id="user-uuid-existing")

    assert result == {"balance": 300}


def test_spend_user_credits_insufficient_balance():
    """user_credit_balances에 row가 없거나 잔액이 부족한 경우 ValueError 발생 검증"""
    db_mock = MagicMock()
    db_mock.execute.return_value.fetchone.return_value = None

    with pytest.raises(ValueError, match="크레딧 잔액이 부족합니다"):
        payment_service._spend_user_credits(
            db=db_mock,
            user_id="user-uuid-no-balance",
            amount=1,
            source_id="analysis-job-uuid",
            description="AI 분석 작업 크레딧 사용",
        )


def test_spend_user_credits_success():
    """잔액이 충분한 경우 credit_ledger INSERT가 실행됨"""
    db_mock = MagicMock()
    balance_row = MagicMock()
    balance_row._mapping = {"balance": 9}  # 10 - 1 = 9
    update_result = MagicMock()
    update_result.fetchone.return_value = balance_row
    db_mock.execute.side_effect = [update_result, MagicMock()]

    balance = payment_service._spend_user_credits(
        db=db_mock,
        user_id="user-uuid-has-credits",
        amount=1,
        source_id="analysis-job-uuid",
        description="AI 분석 작업 크레딧 사용",
    )

    assert balance == 9
    assert db_mock.execute.call_count == 2
    ledger_sql = str(db_mock.execute.call_args_list[1].args[0])
    ledger_params = db_mock.execute.call_args_list[1].args[1]
    assert "INSERT INTO credit_ledger" in ledger_sql
    assert ledger_params["entry_type"] == "spend"
    assert ledger_params["source_type"] == "analysis"


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
        "product_type": "subscription",
        "plan_id": "plan-uuid-pro",
        "credit_plan_id": None,
        "plan_credits": 50,
        "plan_code": "pro",
        "base_credits": None,
        "bonus_credits": None,
        "credit_plan_code": None,
    }
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    balance_insert_row = MagicMock()
    balance_insert_row._mapping = {"balance": 50}
    balance_result = MagicMock()
    balance_result.fetchone.return_value = balance_insert_row
    payment_select_result = MagicMock()
    payment_select_result.fetchone.return_value = payment_row
    db_mock.execute.side_effect = [
        payment_select_result,  # 1: confirm SELECT
        MagicMock(),            # 2: UPDATE payments
        restore_result,         # 3: _restore_free_plan
        MagicMock(),            # 4: UPDATE subscriptions
        balance_result,         # 5: INSERT INTO user_credit_balances
        MagicMock(),            # 6: INSERT INTO credit_ledger
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
    assert db_mock.execute.call_count == 6
    payment_update_params = db_mock.execute.call_args_list[1].args[1]
    subscription_update_sql = str(db_mock.execute.call_args_list[3].args[0])
    subscription_update_params = db_mock.execute.call_args_list[3].args[1]
    balance_sql = str(db_mock.execute.call_args_list[4].args[0])
    ledger_sql = str(db_mock.execute.call_args_list[5].args[0])
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
    assert "remaining_credits" not in subscription_update_sql
    assert subscription_update_params["plan_id"] == "plan-uuid-pro"
    assert "INSERT INTO user_credit_balances" in balance_sql
    assert "INSERT INTO credit_ledger" in ledger_sql
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


def test_get_my_credit_balance_unauthorized():
    response = client.get("/payment/credits/me")
    assert response.status_code == 401


def test_get_my_credit_balance_returns_balance(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    def fake_get_credit_balance(db, user_id):
        assert user_id == fake_user["id"]
        return {"balance": 150}

    monkeypatch.setattr(payment_service, "get_my_credit_balance", fake_get_credit_balance)

    response = client.get(
        "/payment/credits/me",
        cookies={"access_token": "fake_token"},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 150


def test_service_get_my_credit_balance_no_row():
    db_mock = MagicMock()
    db_mock.execute.return_value.fetchone.return_value = None

    result = payment_service.get_my_credit_balance(db=db_mock, user_id="user-uuid-new")

    assert result == {"balance": 0}


def test_service_get_my_credit_balance_existing():
    db_mock = MagicMock()
    row = MagicMock()
    row._mapping = {"balance": 300}
    db_mock.execute.return_value.fetchone.return_value = row

    result = payment_service.get_my_credit_balance(db=db_mock, user_id="user-uuid-existing")

    assert result == {"balance": 300}


def test_spend_user_credits_insufficient_balance():
    """user_credit_balances에 row가 없거나 잔액이 부족한 경우 ValueError 발생 검증"""
    db_mock = MagicMock()
    # UPDATE ... WHERE balance >= :amount 조건에 맞는 row가 없으면 fetchone() = None
    db_mock.execute.return_value.fetchone.return_value = None

    with pytest.raises(ValueError, match="크레딧 잔액이 부족합니다"):
        payment_service._spend_user_credits(
            db=db_mock,
            user_id="user-uuid-no-balance",
            amount=1,
            source_id="analysis-job-uuid",
            description="AI 분석 작업 크레딧 사용",
        )


def test_spend_user_credits_success():
    """잔액이 충분한 경우 credit_ledger INSERT가 실행됨"""
    db_mock = MagicMock()
    balance_row = MagicMock()
    balance_row._mapping = {"balance": 9}  # 10 - 1 = 9
    update_result = MagicMock()
    update_result.fetchone.return_value = balance_row
    db_mock.execute.side_effect = [update_result, MagicMock()]

    balance = payment_service._spend_user_credits(
        db=db_mock,
        user_id="user-uuid-has-credits",
        amount=1,
        source_id="analysis-job-uuid",
        description="AI 분석 작업 크레딧 사용",
    )

    assert balance == 9
    assert db_mock.execute.call_count == 2
    ledger_sql = str(db_mock.execute.call_args_list[1].args[0])
    ledger_params = db_mock.execute.call_args_list[1].args[1]
    assert "INSERT INTO credit_ledger" in ledger_sql
    assert "'spend'" in ledger_sql or "spend" in ledger_sql
    assert "'analysis'" in ledger_sql or "analysis" in ledger_sql
    assert ledger_params["balance_after"] == 9
    assert ledger_params["source_id"] == "analysis-job-uuid"
