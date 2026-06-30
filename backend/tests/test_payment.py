import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import main
from services import (
    auth,
    billing as billing_service,
    payment as payment_service,
    subscription_renewal,
)
from utils.database import get_db

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
        "status": "active",
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
    
    # [한글 주석] classify_plan_change 내 resolve_current_plan에서 활용할 빈 구독 결과 모킹
    current_sub_result = MagicMock()
    current_sub_result.fetchone.return_value = None
    
    # [한글 주석] resolve_current_plan에서 active 구독이 없을 때 조회할 free plan 정보 모킹
    free_plan_row = MagicMock()
    free_plan_row._mapping = {
        "plan_id": "plan-uuid-free",
        "plan_code": "free",
        "plan_name": "Free Plan",
        "price_amount": 0,
        "status": "active",
        "credits": 5,
    }
    free_plan_result = MagicMock()
    free_plan_result.fetchone.return_value = free_plan_row
    
    db_mock.execute.side_effect = [
        plan_result,          # 1: plans 테이블 조회 (pro)
        current_sub_result,   # 2: classify_plan_change 내 resolve_current_plan (active 구독 없음)
        free_plan_result,     # 3: resolve_current_plan 내 free plan 조회
        plan_result,          # 4: classify_plan_change 내 _get_target_plan (pro)
        restore_result,       # 5: 만료 구독 free 복구 조회
        subscription_result,  # 6: _get_user_subscription 조회
        payment_result        # 7: payments INSERT
    ]

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

    # [한글 주석] execute 호출 횟수가 7회로 증가함
    assert db_mock.execute.call_count == 7
    executed_sql = "\n".join(str(call.args[0]) for call in db_mock.execute.call_args_list)
    payment_insert_sql = str(db_mock.execute.call_args_list[6].args[0])
    payment_insert_params = db_mock.execute.call_args_list[6].args[1]
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
        "status": "active",
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
        MagicMock(),            # 4: UPDATE payments.subscription_id
        balance_result,         # 5: INSERT INTO user_credit_balances
        MagicMock(),            # 6: INSERT INTO credit_ledger
    ]

    def fake_create_or_extend_subscription(db, user_id, plan_id, payment_id):
        assert user_id == "user-uuid-3"
        assert plan_id == "plan-uuid-pro"
        assert payment_id == "payment-uuid-3"
        return {"subscription_id": "subscription-created-step5"}

    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        fake_create_or_extend_subscription,
    )

    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": {"subscription_id": "subscription-uuid-3"},
        },
    )

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
    payment_subscription_sql = str(db_mock.execute.call_args_list[3].args[0])
    payment_subscription_params = db_mock.execute.call_args_list[3].args[1]
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
    assert "UPDATE payments" in payment_subscription_sql
    assert "subscription_id = :subscription_id" in payment_subscription_sql
    assert payment_subscription_params["subscription_id"] == "subscription-created-step5"
    assert payment_subscription_params["payment_id"] == "payment-uuid-3"
    assert "INSERT INTO user_credit_balances" in balance_sql
    assert "INSERT INTO credit_ledger" in ledger_sql
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_service_confirm_payment_applies_upgrade_proration(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-uuid-upgrade",
        "amount": 19800,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
        "user_id": "user-uuid-upgrade",
        "subscription_id": "subscription-pro",
        "product_type": "subscription",
        "plan_id": "plan-studio",
        "credit_plan_id": None,
        "plan_credits": 0,
        "plan_code": "studio",
        "base_credits": None,
        "bonus_credits": None,
        "credit_plan_code": None,
    }
    payment_select_result = MagicMock()
    payment_select_result.fetchone.return_value = payment_row
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    db_mock.execute.side_effect = [
        payment_select_result,
        MagicMock(),
        restore_result,
        MagicMock(),
    ]

    async def fake_toss_confirm(payment_key, order_id, amount):
        return {
            "status": "DONE",
            "orderId": order_id,
            "orderName": "Garim Studio",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "lastTransactionKey": "tx-upgrade",
            "method": "card",
            "approvedAt": "2026-06-09T12:00:00+09:00",
            "requestedAt": "2026-06-09T11:59:30+09:00",
            "receipt": {"url": "https://dashboard.tosspayments.com/receipt/upgrade"},
            "isPartialCancelable": True,
        }

    apply_call = MagicMock(return_value={"subscription_id": "subscription-studio"})
    create_call = MagicMock()
    monkeypatch.setattr(payment_service, "_confirm_toss_payment", fake_toss_confirm)
    # [한글 주석] classify_plan_change 결과에 정산 차액 4개 필드 추가 모킹
    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "upgrade",
            "current_subscription": {"subscription_id": "subscription-pro"},
            "proration": {
                "remaining_amount": 1000,
                "target_plan_amount": 19800,
                "discount_amount": 1000,
                "charged_amount": 18800
            }
        },
    )
    # [한글 주석] apply_upgrade_with_proration 모킹 연결
    monkeypatch.setattr(
        payment_service.subscription_service,
        "apply_upgrade_with_proration",
        apply_call,
    )
    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        create_call,
    )

    result = await payment_service.confirm_payment(
        db=db_mock,
        payment_key="payment-key-upgrade",
        order_id="payment-uuid-upgrade",
        amount=19800,
    )

    assert result["status"] == "DONE"
    apply_call.assert_called_once_with(
        db=db_mock,
        user_id="user-uuid-upgrade",
        from_subscription_id="subscription-pro",
        to_plan_id="plan-studio",
        payment_id="payment-uuid-upgrade",
    )
    create_call.assert_not_called()
    payment_subscription_params = db_mock.execute.call_args_list[3].args[1]
    assert payment_subscription_params["subscription_id"] == "subscription-studio"
    assert payment_subscription_params["payment_id"] == "payment-uuid-upgrade"
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_acceptance_free_to_pro_confirm_payment_creates_30day_subscription(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-free-pro-1",
        "amount": 2900,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
        "user_id": "user-free-pro-1",
        "subscription_id": None,
        "product_type": "subscription",
        "plan_id": "plan-pro",
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
        payment_select_result,
        MagicMock(),
        restore_result,
        MagicMock(),
        balance_result,
        MagicMock(),
    ]

    create_call = MagicMock(return_value={
        "subscription_id": "subscription-pro-new",
        "current_period_end": "2026-07-10T00:00:00",
    })
    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        create_call,
    )
    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": None,
        },
    )

    async def fake_toss_confirm(payment_key, order_id, amount):
        return {
            "status": "DONE",
            "orderId": order_id,
            "orderName": "Garim Pro",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "lastTransactionKey": "tx-free-pro-1",
            "method": "card",
            "approvedAt": "2026-06-10T12:00:00+09:00",
            "requestedAt": "2026-06-10T11:59:30+09:00",
            "receipt": {"url": "https://dashboard.tosspayments.com/receipt/free-pro"},
            "isPartialCancelable": True,
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_payment", fake_toss_confirm)

    result = await payment_service.confirm_payment(
        db=db_mock,
        payment_key="payment-key-free-pro",
        order_id="payment-free-pro-1",
        amount=2900,
    )

    assert result["status"] == "DONE"
    assert result["orderName"] == "Garim Pro"
    create_call.assert_called_once_with(
        db=db_mock,
        user_id="user-free-pro-1",
        plan_id="plan-pro",
        payment_id="payment-free-pro-1",
    )
    payment_subscription_params = db_mock.execute.call_args_list[3].args[1]
    assert payment_subscription_params["subscription_id"] == "subscription-pro-new"
    assert payment_subscription_params["payment_id"] == "payment-free-pro-1"
    db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_acceptance_free_to_studio_confirm_payment_creates_30day_subscription(monkeypatch):
    db_mock = MagicMock()
    payment_row = MagicMock()
    payment_row._mapping = {
        "payment_id": "payment-free-studio-1",
        "amount": 19800,
        "status": "ready",
        "pg_transaction_id": None,
        "paid_at": None,
        "user_id": "user-free-studio-1",
        "subscription_id": None,
        "product_type": "subscription",
        "plan_id": "plan-studio",
        "credit_plan_id": None,
        "plan_credits": 500,
        "plan_code": "studio",
        "base_credits": None,
        "bonus_credits": None,
        "credit_plan_code": None,
    }
    restore_result = MagicMock()
    restore_result.fetchone.return_value = None
    balance_insert_row = MagicMock()
    balance_insert_row._mapping = {"balance": 500}
    balance_result = MagicMock()
    balance_result.fetchone.return_value = balance_insert_row
    payment_select_result = MagicMock()
    payment_select_result.fetchone.return_value = payment_row
    db_mock.execute.side_effect = [
        payment_select_result,
        MagicMock(),
        restore_result,
        MagicMock(),
        balance_result,
        MagicMock(),
    ]

    create_call = MagicMock(return_value={
        "subscription_id": "subscription-studio-new",
        "current_period_end": "2026-07-10T00:00:00",
    })
    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        create_call,
    )
    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": None,
        },
    )

    async def fake_toss_confirm(payment_key, order_id, amount):
        return {
            "status": "DONE",
            "orderId": order_id,
            "orderName": "Garim Studio",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "lastTransactionKey": "tx-free-studio-1",
            "method": "card",
            "approvedAt": "2026-06-10T12:00:00+09:00",
            "requestedAt": "2026-06-10T11:59:30+09:00",
            "receipt": {"url": "https://dashboard.tosspayments.com/receipt/free-studio"},
            "isPartialCancelable": True,
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_payment", fake_toss_confirm)

    result = await payment_service.confirm_payment(
        db=db_mock,
        payment_key="payment-key-free-studio",
        order_id="payment-free-studio-1",
        amount=19800,
    )

    assert result["status"] == "DONE"
    assert result["orderName"] == "Garim Studio"
    create_call.assert_called_once_with(
        db=db_mock,
        user_id="user-free-studio-1",
        plan_id="plan-studio",
        payment_id="payment-free-studio-1",
    )
    payment_subscription_params = db_mock.execute.call_args_list[3].args[1]
    assert payment_subscription_params["subscription_id"] == "subscription-studio-new"
    assert payment_subscription_params["payment_id"] == "payment-free-studio-1"
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


def test_service_save_billing_key_encrypts_and_returns_masked_public_fields(monkeypatch):
    monkeypatch.setenv("BILLING_KEY_ENCRYPTION_SECRET", "x" * 32)
    db_mock = MagicMock()
    inserted = MagicMock()
    inserted._mapping = {
        "billing_key_id": "billing-key-id-1",
        "pg_provider": "toss",
        "customer_key": "customer-key-1",
        "card_company": "Hyundai",
        "masked_card_number": "****1234",
        "method_type": "card",
        "status": "active",
        "last_used_at": None,
        "revoked_at": None,
        "created_at": "2026-06-09T00:00:00",
    }
    db_mock.execute.return_value.fetchone.return_value = inserted

    result = billing_service.save_billing_key(
        db=db_mock,
        user_id="user-uuid-1",
        billing_key="raw-billing-key-secret",
        customer_key="customer-key-1",
        card_company="Hyundai",
        masked_card_number="1234123412341234",
        method_type="card",
    )

    sql = str(db_mock.execute.call_args.args[0])
    params = db_mock.execute.call_args.args[1]
    assert "pgp_sym_encrypt(:billing_key, :secret)" in sql
    assert "encrypted_billing_key" in sql
    assert params["billing_key_hash"] != "raw-billing-key-secret"
    assert params["masked_card_number"] == "****1234"
    assert "billingKey" not in result
    assert "encrypted_billing_key" not in result
    assert "billing_key_hash" not in result
    assert result["masked_card_number"] == "****1234"
    assert result["status"] == "active"


def test_service_list_billing_keys_returns_no_sensitive_fields():
    db_mock = MagicMock()
    row = MagicMock()
    row._mapping = {
        "billing_key_id": "billing-key-id-1",
        "pg_provider": "toss",
        "customer_key": "customer-key-1",
        "card_company": "Hyundai",
        "masked_card_number": "****1234",
        "method_type": "card",
        "status": "active",
        "last_used_at": None,
        "revoked_at": None,
        "created_at": "2026-06-09T00:00:00",
    }
    db_mock.execute.return_value.fetchall.return_value = [row]

    result = billing_service.list_billing_keys(db=db_mock, user_id="user-uuid-1")

    sql = str(db_mock.execute.call_args.args[0])
    assert "encrypted_billing_key" not in sql
    assert "billing_key_hash" not in sql
    assert result == [
        {
            "billing_key_id": "billing-key-id-1",
            "pg_provider": "toss",
            "customer_key": "customer-key-1",
            "card_company": "Hyundai",
            "masked_card_number": "****1234",
            "method_type": "card",
            "status": "active",
            "last_used_at": None,
            "revoked_at": None,
            "created_at": "2026-06-09T00:00:00",
        }
    ]


def test_register_billing_key_route_returns_public_response(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setenv("BILLING_KEY_ENCRYPTION_SECRET", "x" * 32)
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    db_mock = MagicMock()
    inserted = MagicMock()
    inserted._mapping = {
        "billing_key_id": "billing-key-id-1",
        "pg_provider": "toss",
        "customer_key": "customer-key-1",
        "card_company": "Hyundai",
        "masked_card_number": "****1234",
        "method_type": "card",
        "status": "active",
        "last_used_at": None,
        "revoked_at": None,
        "created_at": "2026-06-09T00:00:00",
    }
    db_mock.execute.return_value.fetchone.return_value = inserted
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/payment/billing-keys",
            json={
                "billingKey": "raw-billing-key-secret",
                "customerKey": "customer-key-1",
                "cardCompany": "Hyundai",
                "maskedCardNumber": "1234123412341234",
                "methodType": "card",
            },
            cookies={"access_token": "fake_token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert "billingKey" not in body
    assert "encrypted_billing_key" not in body
    assert "billing_key_hash" not in body
    assert body["masked_card_number"] == "****1234"
    assert body["status"] == "active"
    db_mock.commit.assert_called_once()


def _renewal_subscription_row():
    return {
        "subscription_id": "subscription-renewal-1",
        "user_id": "user-uuid-1",
        "plan_id": "plan-pro",
        "billing_key_id": "billing-key-id-1",
        "next_billing_at": "2026-06-09T00:00:00",
        "plan_code": "pro",
        "plan_name": "Pro",
        "price_amount": 2900,
        "credits": 50,
    }


def test_find_due_renewal_subscriptions_filters_auto_renew_only():
    db_mock = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []
    db_mock.execute.return_value = result

    subscriptions = subscription_renewal._find_due_renewal_subscriptions(db_mock, limit=25)

    sql = str(db_mock.execute.call_args.args[0])
    params = db_mock.execute.call_args.args[1]
    assert subscriptions == []
    assert "s.status = 'active'" in sql
    assert "s.auto_renew = true" in sql
    assert "s.cancel_at_period_end = false" in sql
    assert "s.next_billing_at <= NOW()" in sql
    assert "yearly_price_amount" in sql
    assert "s.billing_period_days >= 365" in sql
    assert "FOR UPDATE OF s SKIP LOCKED" in sql
    assert params["limit"] == 25


def test_run_subscription_renewals_records_missing_billing_key(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    target_result.fetchall.return_value = [_renewal_subscription_row()]
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-missing-key"}
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: None,
    )

    result = subscription_renewal.run_subscription_renewals(db_mock)

    attempt_sql = str(db_mock.execute.call_args_list[1].args[0])
    update_sql = str(db_mock.execute.call_args_list[2].args[0])
    attempt_params = db_mock.execute.call_args_list[1].args[1]
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["failure_code"] == "billing_key_missing"
    assert "INSERT INTO subscription_billing_attempts" in attempt_sql
    assert attempt_params["attempt_type"] == "renewal"
    assert "billing_status = 'billing_key_missing'" in update_sql
    db_mock.commit.assert_called_once()


def test_run_subscription_renewals_success_creates_payment_and_extends_subscription(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    # billing_period_days를 30으로 함께 Mocking
    row_data = {**_renewal_subscription_row(), "billing_period_days": 30}
    target_result.fetchall.return_value = [row_data]
    payment_row = MagicMock()
    payment_row._mapping = {"payment_id": "payment-renewal-1"}
    subscription_row = MagicMock()
    subscription_row._mapping = {
        "subscription_id": "subscription-renewal-1",
        "current_period_end": "2026-07-09T00:00:00",
        "next_billing_at": "2026-07-09T00:00:00",
    }
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-success"}
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(fetchone=MagicMock(return_value=payment_row)),
        MagicMock(fetchone=MagicMock(return_value=subscription_row)),
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: {
            "billing_key_id": "billing-key-id-1",
            "billing_key": "raw-billing-key",
            "customer_key": "customer-key-1",
        },
    )

    def charge_client(billing_key, customer_key, amount, order_id, order_name):
        assert billing_key == "raw-billing-key"
        assert customer_key == "customer-key-1"
        assert amount == 2900
        assert "renewal" in order_name
        return {
            "success": True,
            "pg_transaction_id": "tx-renewal-1",
            "method": "billing",
        }

    result = subscription_renewal.run_subscription_renewals(
        db_mock,
        charge_client=charge_client,
    )

    payment_sql = str(db_mock.execute.call_args_list[1].args[0])
    subscription_sql = str(db_mock.execute.call_args_list[2].args[0])
    attempt_sql = str(db_mock.execute.call_args_list[3].args[0])
    billing_key_sql = str(db_mock.execute.call_args_list[4].args[0])
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "success"
    assert result["results"][0]["payment_id"] == "payment-renewal-1"
    assert "INSERT INTO payments" in payment_sql
    assert "billing_key_id" in payment_sql
    assert "current_period_end = current_period_end + CAST(:period_days || ' days' AS interval)" in subscription_sql
    assert "next_billing_at = current_period_end + CAST(:period_days || ' days' AS interval)" in subscription_sql
    assert "INSERT INTO subscription_billing_attempts" in attempt_sql
    assert ":status" in attempt_sql
    assert db_mock.execute.call_args_list[3].args[1]["attempt_type"] == "renewal"
    assert "UPDATE billing_keys" in billing_key_sql
    db_mock.commit.assert_called_once()


def test_run_subscription_renewals_charge_failure_records_failed_attempt(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    target_result.fetchall.return_value = [_renewal_subscription_row()]
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-failed"}
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: {
            "billing_key_id": "billing-key-id-1",
            "billing_key": "raw-billing-key",
            "customer_key": "customer-key-1",
        },
    )

    def charge_client(**kwargs):
        return {
            "success": False,
            "failure_code": "card_declined",
            "failure_message": "Card declined",
        }

    result = subscription_renewal.run_subscription_renewals(
        db_mock,
        charge_client=charge_client,
    )

    attempt_sql = str(db_mock.execute.call_args_list[1].args[0])
    attempt_params = db_mock.execute.call_args_list[1].args[1]
    update_sql = str(db_mock.execute.call_args_list[2].args[0])
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["failure_code"] == "card_declined"
    assert "INSERT INTO subscription_billing_attempts" in attempt_sql
    assert attempt_params["failure_code"] == "card_declined"
    assert attempt_params["failure_message"] == "Card declined"
    assert "billing_status = 'failed'" in update_sql
    db_mock.commit.assert_called_once()


def _scheduled_downgrade_row():
    return {
        "plan_change_id": "change-downgrade-due-1",
        "user_id": "user-uuid-1",
        "from_subscription_id": "subscription-studio-1",
        "source_subscription_id": "subscription-studio-1",
        "to_plan_id": "plan-pro",
        "effective_at": "2026-06-09T00:00:00",
        "plan_code": "pro",
        "plan_name": "Pro",
        "price_amount": 2900,
        "credits": 50,
    }


def test_find_due_scheduled_downgrades_filters_scheduled_due_only():
    db_mock = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []
    db_mock.execute.return_value = result

    changes = subscription_renewal._find_due_scheduled_downgrades(db_mock, limit=10)

    sql = str(db_mock.execute.call_args.args[0])
    params = db_mock.execute.call_args.args[1]
    assert changes == []
    assert "pc.change_type IN ('downgrade', 'cancel_to_free')" in sql
    assert "pc.status = 'scheduled'" in sql
    assert "pc.effective_at <= NOW()" in sql
    assert "FOR UPDATE OF pc SKIP LOCKED" in sql
    assert params["limit"] == 10


def test_run_scheduled_downgrades_missing_billing_key_marks_failed(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    target_result.fetchall.return_value = [_scheduled_downgrade_row()]
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-downgrade-missing-key"}
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: None,
    )

    result = subscription_renewal.run_scheduled_downgrades(db_mock)

    attempt_sql = str(db_mock.execute.call_args_list[1].args[0])
    attempt_params = db_mock.execute.call_args_list[1].args[1]
    change_sql = str(db_mock.execute.call_args_list[2].args[0])
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["failure_code"] == "billing_key_missing"
    assert "INSERT INTO subscription_billing_attempts" in attempt_sql
    assert attempt_params["attempt_type"] == "scheduled_downgrade"
    assert attempt_params["plan_change_id"] == "change-downgrade-due-1"
    assert "UPDATE subscription_plan_changes" in change_sql
    assert "status = :status" in change_sql
    db_mock.commit.assert_called_once()


def test_run_scheduled_downgrades_success_creates_subscription_and_applies_change(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    # billing_period_days를 30으로 함께 Mocking
    row_data = {**_scheduled_downgrade_row(), "billing_period_days": 30}
    target_result.fetchall.return_value = [row_data]
    subscription_row = MagicMock()
    subscription_row._mapping = {
        "subscription_id": "subscription-pro-new",
        "current_period_start": "2026-06-09T00:00:00",
        "current_period_end": "2026-07-09T00:00:00",
        "next_billing_at": "2026-07-09T00:00:00",
    }
    payment_row = MagicMock()
    payment_row._mapping = {"payment_id": "payment-downgrade-1"}
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-downgrade-success"}
    applied_row = MagicMock()
    applied_row._mapping = {
        "plan_change_id": "change-downgrade-due-1",
        "status": "applied",
        "applied_at": "2026-06-09T00:00:00",
        "to_subscription_id": "subscription-pro-new",
    }
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(), # 기존 구독 취소 처리 업데이트 쿼리용 MagicMock (L297 부근 추가분)
        MagicMock(fetchone=MagicMock(return_value=subscription_row)),
        MagicMock(fetchone=MagicMock(return_value=payment_row)),
        MagicMock(),
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(fetchone=MagicMock(return_value=applied_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: {
            "billing_key_id": "billing-key-id-1",
            "billing_key": "raw-billing-key",
            "customer_key": "customer-key-1",
        },
    )

    def charge_client(billing_key, customer_key, amount, order_id, order_name):
        assert billing_key == "raw-billing-key"
        assert customer_key == "customer-key-1"
        assert amount == 2900
        assert "scheduled downgrade" in order_name
        return {
            "success": True,
            "pg_transaction_id": "tx-downgrade-1",
            "method": "billing",
        }

    result = subscription_renewal.run_scheduled_downgrades(
        db_mock,
        charge_client=charge_client,
    )

    cancel_old_sub_sql = str(db_mock.execute.call_args_list[1].args[0])
    insert_subscription_sql = str(db_mock.execute.call_args_list[2].args[0])
    payment_sql = str(db_mock.execute.call_args_list[3].args[0])
    link_payment_sql = str(db_mock.execute.call_args_list[4].args[0])
    attempt_sql = str(db_mock.execute.call_args_list[5].args[0])
    apply_sql = str(db_mock.execute.call_args_list[6].args[0])
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "applied"
    assert result["results"][0]["subscription_id"] == "subscription-pro-new"
    assert "UPDATE subscriptions" in cancel_old_sub_sql
    assert "status = 'cancelled'" in cancel_old_sub_sql
    assert "INSERT INTO subscriptions" in insert_subscription_sql
    assert "billing_key_id" in insert_subscription_sql
    assert "NOW() + CAST(:period_days || ' days' AS interval)" in insert_subscription_sql
    assert "INSERT INTO payments" in payment_sql
    assert "plan_change_id" in payment_sql
    assert "UPDATE subscriptions" in link_payment_sql
    assert "last_payment_id = :payment_id" in link_payment_sql
    assert "INSERT INTO subscription_billing_attempts" in attempt_sql
    assert db_mock.execute.call_args_list[5].args[1]["attempt_type"] == "scheduled_downgrade"
    assert "status = 'applied'" in apply_sql
    assert "to_subscription_id = :to_subscription_id" in apply_sql
    db_mock.commit.assert_called_once()


def test_run_scheduled_downgrades_charge_failure_marks_plan_change_failed(monkeypatch):
    db_mock = MagicMock()
    target_result = MagicMock()
    target_result.fetchall.return_value = [_scheduled_downgrade_row()]
    attempt_row = MagicMock()
    attempt_row._mapping = {"billing_attempt_id": "attempt-downgrade-failed"}
    db_mock.execute.side_effect = [
        target_result,
        MagicMock(fetchone=MagicMock(return_value=attempt_row)),
        MagicMock(),
    ]
    monkeypatch.setattr(
        subscription_renewal.billing_service,
        "get_active_billing_key_for_charge",
        lambda db, user_id, billing_key_id=None: {
            "billing_key_id": "billing-key-id-1",
            "billing_key": "raw-billing-key",
            "customer_key": "customer-key-1",
        },
    )

    result = subscription_renewal.run_scheduled_downgrades(
        db_mock,
        charge_client=lambda **kwargs: {
            "success": False,
            "failure_code": "card_declined",
            "failure_message": "Card declined",
        },
    )

    attempt_params = db_mock.execute.call_args_list[1].args[1]
    change_sql = str(db_mock.execute.call_args_list[2].args[0])
    assert result["processed"] == 1
    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["failure_code"] == "card_declined"
    assert attempt_params["attempt_type"] == "scheduled_downgrade"
    assert attempt_params["failure_code"] == "card_declined"
    assert "UPDATE subscription_plan_changes" in change_sql
    db_mock.commit.assert_called_once()


def test_get_my_payment_info_route_returns_plan_code(monkeypatch):
    fake_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
        "session_id": "fake_session",
    }
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)

    plan_row = MagicMock()
    plan_row._mapping = {
        "subscription_id": "subscription-uuid-pro",
        "subscription_status": "active",
        "plan_name": "Pro",
        "plan_code": "pro",
        "plan_rank": 10,
        "current_period_start": None,
        "current_period_end": None,
        "next_billing_at": None,
        "auto_renew": True,
        "cancel_at_period_end": False,
        "cancelled_at": None,
        "billing_status": "paid",
    }
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_row)),
        MagicMock(fetchone=MagicMock(return_value=None)),
        MagicMock(fetchone=MagicMock(return_value=None)),
        MagicMock(fetchone=MagicMock(return_value=None)),
        MagicMock(fetchall=MagicMock(return_value=[])),
    ]
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.get(
            "/payment/me",
            cookies={"access_token": "fake_token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["plan_code"] == "pro"
    assert response.json()["plan_name"] == "Pro"
    assert response.json()["scheduled_plan_change"] is None


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


def test_service_get_my_payment_info_returns_current_plan_code():
    db_mock = MagicMock()
    # [한글 주석] resolve_current_plan이 반환할 current plan/subscription 정보 모킹
    plan_row = MagicMock()
    plan_row._mapping = {
        "subscription_id": "subscription-uuid-pro",
        "subscription_status": "active",
        "plan_name": "Pro",
        "plan_code": "pro",
        "plan_rank": 10,
        "current_period_start": None,
        "current_period_end": None,
        "next_billing_at": None,
        "auto_renew": True,
        "cancel_at_period_end": False,
        "cancelled_at": None,
        "billing_status": "paid",
    }
    
    # [한글 주석] applied upgrade 정산 변경 이력 정보 모킹
    proration_row = MagicMock()
    proration_row._mapping = {
        "remaining_amount": 1000,
        "target_plan_amount": 19800,
        "discount_amount": 1000,
        "charged_amount": 18800,
        "applied_at": None,
        "from_plan_name": "Pro",
        "to_plan_name": "Studio"
    }
    
    # [한글 주석] 예정된(scheduled) 플랜 변경 정보 모킹
    scheduled_row = MagicMock()
    scheduled_row._mapping = {
        "plan_change_id": "change-downgrade-1",
        "change_type": "downgrade",
        "status": "scheduled",
        "effective_at": None,
        "plan_id": "plan-pro",
        "plan_code": "pro",
        "plan_name": "Pro",
    }
    
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_row)),       # resolve_current_plan
        MagicMock(fetchone=MagicMock(return_value=proration_row)),  # applied upgrade proration 이력 조회
        MagicMock(fetchone=MagicMock(return_value=scheduled_row)),  # scheduled 변경 이력 조회
        MagicMock(fetchone=MagicMock(return_value=None)),           # 최근 성공 결제 내역 조회
        MagicMock(fetchall=MagicMock(return_value=[])),             # payments 결제 이력 전체 조회
    ]

    result = payment_service.get_my_payment_info(db=db_mock, user_id="user-uuid-pro")

    assert result["plan_code"] == "pro"
    assert result["plan_name"] == "Pro"
    assert result["is_premium"] is True
    assert result["current_plan"]["plan_rank"] == 10
    # [한글 주석] 이월 필드가 삭제되고 latest_upgrade_proration이 포함되었는지 검증
    assert result["latest_upgrade_proration"]["from_plan_name"] == "Pro"
    assert result["latest_upgrade_proration"]["to_plan_name"] == "Studio"
    assert result["latest_upgrade_proration"]["discount_amount"] == 1000
    assert result["scheduled_plan_change"]["change_type"] == "downgrade"


@pytest.mark.anyio
async def test_confirm_billing_payment_uses_explicit_yearly_amount_and_credits(monkeypatch):
    db_mock = MagicMock()
    plan_row = MagicMock()
    plan_row._mapping = {
        "plan_id": "plan-pro",
        "plan_name": "Pro",
        "price_amount": 2900,
        "yearly_price_amount": 25000,
        "credits": 50,
        "yearly_credits": 650,
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_row)),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": None,
        },
    )
    create_call = MagicMock(return_value={"subscription_id": "subscription-pro-yearly"})
    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        create_call,
    )
    async def fake_issue_toss_billing_key(auth_key, customer_key):
        return {
            "billingKey": "raw-billing-key",
            "card": {"company": "테스트카드", "number": "****1234"},
        }

    monkeypatch.setattr(payment_service, "_issue_toss_billing_key", fake_issue_toss_billing_key)

    async def fake_confirm_billing_payment(billing_key, customer_key, order_id, amount, order_name):
        assert amount == 25000
        assert "연 구독" in order_name
        return {
            "status": "DONE",
            "paymentKey": "payment-key-yearly",
            "lastTransactionKey": "tx-yearly",
            "method": "card",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "requestedAt": "2026-06-29T10:00:00+09:00",
            "approvedAt": "2026-06-29T10:00:10+09:00",
            "isPartialCancelable": True,
            "receipt": {"url": "https://example.com/receipt"},
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_billing_payment", fake_confirm_billing_payment)
    monkeypatch.setattr(
        billing_service,
        "save_billing_key",
        MagicMock(return_value={"billing_key_id": "billing-key-yearly"}),
    )
    credit_grant = MagicMock()
    monkeypatch.setattr(payment_service, "_add_user_credits", credit_grant)

    result = await payment_service.confirm_billing_payment(
        db=db_mock,
        auth_key="auth-key",
        customer_key="customer-key",
        plan_code="pro",
        user_id="user-yearly",
        billing_cycle="yearly",
    )

    plan_sql = str(db_mock.execute.call_args_list[0].args[0])
    ready_payment_params = db_mock.execute.call_args_list[1].args[1]
    assert "yearly_price_amount" in plan_sql
    assert "yearly_credits" in plan_sql
    assert ready_payment_params["amount"] == 25000
    assert result["amount"] == 25000
    assert result["billingCycle"] == "yearly"
    create_call.assert_called_once_with(
        db=db_mock,
        user_id="user-yearly",
        plan_id="plan-pro",
        payment_id=result["orderId"],
        billing_key_id="billing-key-yearly",
        period_days=365,
    )
    credit_grant.assert_called_once()
    assert credit_grant.call_args.kwargs["amount"] == 650


@pytest.mark.anyio
async def test_confirm_billing_payment_yearly_falls_back_to_monthly_formula(monkeypatch):
    db_mock = MagicMock()
    plan_row = MagicMock()
    plan_row._mapping = {
        "plan_id": "plan-pro",
        "plan_name": "Pro",
        "price_amount": 2900,
        "yearly_price_amount": None,
        "credits": 50,
        "yearly_credits": None,
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_row)),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": None,
        },
    )
    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        MagicMock(return_value={"subscription_id": "subscription-pro-yearly-fallback"}),
    )
    async def fake_issue_toss_billing_key(auth_key, customer_key):
        return {"billingKey": "raw-billing-key", "card": {}}

    monkeypatch.setattr(payment_service, "_issue_toss_billing_key", fake_issue_toss_billing_key)

    async def fake_confirm_billing_payment(billing_key, customer_key, order_id, amount, order_name):
        assert amount == 29000
        return {
            "status": "DONE",
            "paymentKey": "payment-key-yearly-fallback",
            "lastTransactionKey": "tx-yearly-fallback",
            "method": "card",
            "totalAmount": amount,
            "balanceAmount": amount,
            "currency": "KRW",
            "requestedAt": "2026-06-29T10:00:00+09:00",
            "approvedAt": "2026-06-29T10:00:10+09:00",
            "isPartialCancelable": True,
            "receipt": {"url": "https://example.com/receipt"},
        }

    monkeypatch.setattr(payment_service, "_confirm_toss_billing_payment", fake_confirm_billing_payment)
    monkeypatch.setattr(
        billing_service,
        "save_billing_key",
        MagicMock(return_value={"billing_key_id": "billing-key-yearly-fallback"}),
    )
    credit_grant = MagicMock()
    monkeypatch.setattr(payment_service, "_add_user_credits", credit_grant)

    result = await payment_service.confirm_billing_payment(
        db=db_mock,
        auth_key="auth-key",
        customer_key="customer-key",
        plan_code="pro",
        user_id="user-yearly-fallback",
        billing_cycle="yearly",
    )

    ready_payment_params = db_mock.execute.call_args_list[1].args[1]
    assert ready_payment_params["amount"] == 29000
    assert result["amount"] == 29000
    credit_grant.assert_called_once()
    assert credit_grant.call_args.kwargs["amount"] == 600


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
        MagicMock(),            # 4: UPDATE payments.subscription_id
        balance_result,         # 5: INSERT INTO user_credit_balances
        MagicMock(),            # 6: INSERT INTO credit_ledger
    ]

    def fake_create_or_extend_subscription(db, user_id, plan_id, payment_id):
        assert user_id == "user-uuid-3"
        assert plan_id == "plan-uuid-pro"
        assert payment_id == "payment-uuid-3"
        return {"subscription_id": "subscription-created-step5"}

    monkeypatch.setattr(
        payment_service.subscription_service,
        "create_or_extend_subscription",
        fake_create_or_extend_subscription,
    )

    monkeypatch.setattr(
        payment_service.subscription_service,
        "classify_plan_change",
        lambda db, user_id, to_plan_id: {
            "change_type": "same_plan",
            "current_subscription": {"subscription_id": "subscription-uuid-3"},
        },
    )

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
    payment_subscription_sql = str(db_mock.execute.call_args_list[3].args[0])
    payment_subscription_params = db_mock.execute.call_args_list[3].args[1]
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
    assert "UPDATE payments" in payment_subscription_sql
    assert "subscription_id = :subscription_id" in payment_subscription_sql
    assert payment_subscription_params["subscription_id"] == "subscription-created-step5"
    assert payment_subscription_params["payment_id"] == "payment-uuid-3"
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
