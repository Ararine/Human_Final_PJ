from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import main
from services import auth
from services import subscription as subscription_service
from utils.database import get_db


def test_resolve_current_plan_uses_valid_active_subscription_rank_order():
    db_mock = MagicMock()
    studio_row = MagicMock()
    studio_row._mapping = {
        "subscription_id": "subscription-studio",
        "subscription_status": "active",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
        "auto_renew": True,
        "cancel_at_period_end": False,
        "cancelled_at": None,
        "billing_status": "paid",
        "carried_over_days": 0,
        "superseded_by_subscription_id": None,
        "plan_id": "plan-studio",
        "plan_code": "studio",
        "plan_name": "Studio",
        "plan_rank": 20,
        "price_amount": 19800,
        "credits": 500,
    }
    db_mock.execute.return_value.fetchone.return_value = studio_row

    result = subscription_service.resolve_current_plan(db_mock, "user-1")

    sql = str(db_mock.execute.call_args.args[0])
    assert "s.current_period_start <= NOW()" in sql
    assert "s.current_period_end > NOW()" in sql
    assert "p.plan_rank DESC" in sql
    assert "cancel_at_period_end = false" not in sql
    assert "auto_renew = true" not in sql
    assert result["current_plan"]["plan_code"] == "studio"
    assert result["current_plan"]["plan_rank"] == 20
    assert result["is_fallback_free"] is False


def test_resolve_current_plan_falls_back_to_free_when_no_valid_subscription():
    db_mock = MagicMock()
    free_row = MagicMock()
    free_row._mapping = {
        "plan_id": "plan-free",
        "plan_code": "free",
        "plan_name": "Free",
        "plan_rank": 0,
        "price_amount": 0,
        "credits": 5,
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=None)),
        MagicMock(fetchone=MagicMock(return_value=free_row)),
    ]

    result = subscription_service.resolve_current_plan(db_mock, "user-1")

    assert db_mock.execute.call_count == 2
    assert result["current_plan"]["plan_code"] == "free"
    assert result["current_subscription"] is None
    assert result["is_fallback_free"] is True


def _mock_plan_row(code, rank):
    row = MagicMock()
    row._mapping = {
        "plan_id": f"plan-{code}",
        "plan_code": code,
        "plan_name": code.title(),
        "plan_rank": rank,
        "price_amount": 0 if code == "free" else 1000,
        "credits": 0,
    }
    return row


def _mock_subscription_row(code, rank):
    row = MagicMock()
    row._mapping = {
        "subscription_id": f"subscription-{code}",
        "subscription_status": "active",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
        "auto_renew": False,
        "cancel_at_period_end": True,
        "cancelled_at": None,
        "billing_status": "paid",
        "carried_over_days": 0,
        "superseded_by_subscription_id": None,
        "plan_id": f"plan-{code}",
        "plan_code": code,
        "plan_name": code.title(),
        "plan_rank": rank,
        "price_amount": 1000,
        "credits": 0,
    }
    return row


def _db_for_classify(current_code, current_rank, target_code, target_rank):
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=_mock_subscription_row(current_code, current_rank))),
        MagicMock(fetchone=MagicMock(return_value=_mock_plan_row(target_code, target_rank))),
    ]
    return db_mock


def test_classify_plan_change_upgrade_requires_payment_now():
    db_mock = _db_for_classify("pro", 10, "studio", 20)

    result = subscription_service.classify_plan_change(db_mock, "user-1", "studio")

    assert result["change_type"] == "upgrade"
    assert result["apply_timing"] == "immediate"
    assert result["requires_payment_now"] is True


def test_classify_plan_change_downgrade_is_period_end():
    db_mock = _db_for_classify("studio", 20, "pro", 10)

    result = subscription_service.classify_plan_change(db_mock, "user-1", "pro")

    assert result["change_type"] == "downgrade"
    assert result["apply_timing"] == "period_end"
    assert result["requires_payment_now"] is False


def test_classify_plan_change_free_is_cancel_to_free():
    db_mock = _db_for_classify("studio", 20, "free", 0)

    result = subscription_service.classify_plan_change(db_mock, "user-1", "free")

    assert result["change_type"] == "cancel_to_free"
    assert result["apply_timing"] == "period_end"
    assert result["requires_payment_now"] is False


def test_classify_plan_change_same_rank_is_same_plan():
    db_mock = _db_for_classify("pro", 10, "pro", 10)

    result = subscription_service.classify_plan_change(db_mock, "user-1", "pro")

    assert result["change_type"] == "same_plan"
    assert result["apply_timing"] == "none"
    assert result["requires_payment_now"] is False


def test_change_plan_route_returns_classification(monkeypatch):
    client = TestClient(main.app)
    fake_user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
    }
    db_mock = _db_for_classify("pro", 10, "studio", 20)
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/subscriptions/change-plan",
            json={"to_plan_id": "studio"},
            cookies={"access_token": "fake-token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["change_type"] == "upgrade"
    assert response.json()["requires_payment_now"] is True
    db_mock.commit.assert_called_once()


def test_schedule_downgrade_creates_scheduled_plan_change():
    db_mock = MagicMock()
    inserted = MagicMock()
    inserted._mapping = {
        "plan_change_id": "change-downgrade-1",
        "status": "scheduled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock.execute.side_effect = [
        MagicMock(),
        MagicMock(fetchone=MagicMock(return_value=inserted)),
    ]

    result = subscription_service.schedule_downgrade(
        db=db_mock,
        user_id="user-1",
        from_subscription_id="subscription-studio",
        to_plan_id="plan-pro",
        current_plan=_mock_plan_row("studio", 20)._mapping,
        current_subscription=_mock_subscription_row("studio", 20)._mapping,
        target_plan=_mock_plan_row("pro", 10)._mapping,
    )

    cancel_sql = str(db_mock.execute.call_args_list[0].args[0])
    insert_sql = str(db_mock.execute.call_args_list[1].args[0])
    insert_params = db_mock.execute.call_args_list[1].args[1]
    assert "UPDATE subscription_plan_changes" in cancel_sql
    assert "status = 'cancelled'" in cancel_sql
    assert "INSERT INTO subscription_plan_changes" in insert_sql
    assert "'downgrade'" in insert_sql
    assert "'period_end'" in insert_sql
    assert "'scheduled'" in insert_sql
    assert insert_params["from_subscription_id"] == "subscription-studio"
    assert result["plan_change_id"] == "change-downgrade-1"
    assert result["to_plan_code"] == "pro"
    assert result["status"] == "scheduled"


def test_change_plan_route_schedules_downgrade(monkeypatch):
    client = TestClient(main.app)
    fake_user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
    }
    current_row = _mock_subscription_row("studio", 20)
    target_row = _mock_plan_row("pro", 10)
    scheduled_row = MagicMock()
    scheduled_row._mapping = {
        "plan_change_id": "change-downgrade-2",
        "status": "scheduled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=current_row)),
        MagicMock(fetchone=MagicMock(return_value=target_row)),
        MagicMock(),
        MagicMock(fetchone=MagicMock(return_value=scheduled_row)),
    ]
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/subscriptions/change-plan",
            json={"to_plan_id": "pro"},
            cookies={"access_token": "fake-token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["change_type"] == "downgrade"
    assert body["apply_timing"] == "period_end"
    assert body["scheduled_plan_change"]["status"] == "scheduled"
    assert body["scheduled_plan_change"]["to_plan_code"] == "pro"
    db_mock.commit.assert_called_once()


def test_schedule_cancel_to_free_updates_subscription_and_creates_plan_change():
    db_mock = MagicMock()
    inserted = MagicMock()
    inserted._mapping = {
        "plan_change_id": "change-cancel-free-1",
        "status": "scheduled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock.execute.side_effect = [
        MagicMock(),
        MagicMock(),
        MagicMock(fetchone=MagicMock(return_value=inserted)),
    ]

    result = subscription_service.schedule_cancel_to_free(
        db=db_mock,
        user_id="user-1",
        from_subscription_id="subscription-studio",
        current_plan=_mock_plan_row("studio", 20)._mapping,
        current_subscription=_mock_subscription_row("studio", 20)._mapping,
        target_plan=_mock_plan_row("free", 0)._mapping,
    )

    subscription_sql = str(db_mock.execute.call_args_list[0].args[0])
    cancel_sql = str(db_mock.execute.call_args_list[1].args[0])
    insert_sql = str(db_mock.execute.call_args_list[2].args[0])
    assert "UPDATE subscriptions" in subscription_sql
    assert "auto_renew = false" in subscription_sql
    assert "cancel_at_period_end = true" in subscription_sql
    assert "cancelled_at = NOW()" in subscription_sql
    assert "UPDATE subscription_plan_changes" in cancel_sql
    assert "change_type IN ('downgrade', 'cancel_to_free')" in cancel_sql
    assert "INSERT INTO subscription_plan_changes" in insert_sql
    assert "'cancel_to_free'" in insert_sql
    assert result["plan_change_id"] == "change-cancel-free-1"
    assert result["to_plan_code"] == "free"
    assert result["status"] == "scheduled"


def test_change_plan_route_schedules_cancel_to_free(monkeypatch):
    client = TestClient(main.app)
    fake_user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
    }
    current_row = _mock_subscription_row("studio", 20)
    free_row = _mock_plan_row("free", 0)
    scheduled_row = MagicMock()
    scheduled_row._mapping = {
        "plan_change_id": "change-cancel-free-2",
        "status": "scheduled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=current_row)),
        MagicMock(fetchone=MagicMock(return_value=free_row)),
        MagicMock(),
        MagicMock(),
        MagicMock(fetchone=MagicMock(return_value=scheduled_row)),
    ]
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/subscriptions/change-plan",
            json={"to_plan_id": "free"},
            cookies={"access_token": "fake-token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["change_type"] == "cancel_to_free"
    assert body["apply_timing"] == "period_end"
    assert body["scheduled_plan_change"]["status"] == "scheduled"
    assert body["scheduled_plan_change"]["to_plan_code"] == "free"
    db_mock.commit.assert_called_once()


def test_resume_subscription_restores_auto_renew_and_cancels_cancel_to_free():
    db_mock = MagicMock()
    existing = MagicMock()
    existing._mapping = {
        "subscription_id": "subscription-studio",
        "status": "active",
        "current_period_end": "2026-07-01T00:00:00",
        "auto_renew": False,
        "cancel_at_period_end": True,
    }
    updated = MagicMock()
    updated._mapping = {
        "subscription_id": "subscription-studio",
        "subscription_status": "active",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
        "auto_renew": True,
        "cancel_at_period_end": False,
        "cancelled_at": None,
        "billing_status": "paid",
        "carried_over_days": 0,
        "superseded_by_subscription_id": None,
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=existing)),
        MagicMock(fetchone=MagicMock(return_value=updated)),
        MagicMock(),
    ]

    result = subscription_service.resume_subscription(
        db=db_mock,
        user_id="user-1",
        subscription_id="subscription-studio",
    )

    select_sql = str(db_mock.execute.call_args_list[0].args[0])
    update_sql = str(db_mock.execute.call_args_list[1].args[0])
    cancel_sql = str(db_mock.execute.call_args_list[2].args[0])
    assert "FROM subscriptions" in select_sql
    assert "current_period_end > NOW()" in select_sql
    assert "UPDATE subscriptions" in update_sql
    assert "auto_renew = true" in update_sql
    assert "cancel_at_period_end = false" in update_sql
    assert "cancelled_at = NULL" in update_sql
    assert "UPDATE subscription_plan_changes" in cancel_sql
    assert "change_type = 'cancel_to_free'" in cancel_sql
    assert result["subscription_id"] == "subscription-studio"
    assert result["auto_renew"] is True
    assert result["cancel_at_period_end"] is False


def test_cancel_scheduled_plan_change_marks_downgrade_cancelled():
    db_mock = MagicMock()
    existing = MagicMock()
    existing._mapping = {
        "plan_change_id": "change-downgrade-3",
        "change_type": "downgrade",
        "status": "scheduled",
        "from_subscription_id": "subscription-studio",
        "effective_at": "2026-07-01T00:00:00",
    }
    updated = MagicMock()
    updated._mapping = {
        "plan_change_id": "change-downgrade-3",
        "change_type": "downgrade",
        "status": "cancelled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=existing)),
        MagicMock(fetchone=MagicMock(return_value=updated)),
    ]

    result = subscription_service.cancel_scheduled_plan_change(
        db=db_mock,
        user_id="user-1",
        plan_change_id="change-downgrade-3",
    )

    select_sql = str(db_mock.execute.call_args_list[0].args[0])
    update_sql = str(db_mock.execute.call_args_list[1].args[0])
    assert "FROM subscription_plan_changes" in select_sql
    assert "status = 'scheduled'" in select_sql
    assert "UPDATE subscription_plan_changes" in update_sql
    assert "status = 'cancelled'" in update_sql
    assert result["plan_change_id"] == "change-downgrade-3"
    assert result["status"] == "cancelled"


def test_resume_subscription_route_restores_cancellation(monkeypatch):
    client = TestClient(main.app)
    fake_user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
    }
    existing = MagicMock()
    existing._mapping = {
        "subscription_id": "subscription-studio",
        "status": "active",
        "current_period_end": "2026-07-01T00:00:00",
        "auto_renew": False,
        "cancel_at_period_end": True,
    }
    updated = MagicMock()
    updated._mapping = {
        "subscription_id": "subscription-studio",
        "subscription_status": "active",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
        "auto_renew": True,
        "cancel_at_period_end": False,
        "cancelled_at": None,
        "billing_status": "paid",
        "carried_over_days": 0,
        "superseded_by_subscription_id": None,
    }
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=existing)),
        MagicMock(fetchone=MagicMock(return_value=updated)),
        MagicMock(),
    ]
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/subscriptions/subscription-studio/resume",
            cookies={"access_token": "fake-token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["subscription_id"] == "subscription-studio"
    assert body["auto_renew"] is True
    assert body["cancel_at_period_end"] is False
    db_mock.commit.assert_called_once()


def test_cancel_plan_change_route_cancels_scheduled_downgrade(monkeypatch):
    client = TestClient(main.app)
    fake_user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "Garim User",
        "role": "USER",
        "status": "active",
    }
    existing = MagicMock()
    existing._mapping = {
        "plan_change_id": "change-downgrade-4",
        "change_type": "downgrade",
        "status": "scheduled",
        "from_subscription_id": "subscription-studio",
        "effective_at": "2026-07-01T00:00:00",
    }
    updated = MagicMock()
    updated._mapping = {
        "plan_change_id": "change-downgrade-4",
        "change_type": "downgrade",
        "status": "cancelled",
        "effective_at": "2026-07-01T00:00:00",
    }
    db_mock = MagicMock()
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=existing)),
        MagicMock(fetchone=MagicMock(return_value=updated)),
    ]
    monkeypatch.setattr(auth, "authenticate_access_token", lambda token: fake_user)
    main.app.dependency_overrides[get_db] = lambda: db_mock

    try:
        response = client.post(
            "/subscriptions/plan-changes/change-downgrade-4/cancel",
            cookies={"access_token": "fake-token"},
        )
    finally:
        main.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["plan_change_id"] == "change-downgrade-4"
    assert body["status"] == "cancelled"
    db_mock.commit.assert_called_once()


def test_create_or_extend_subscription_extends_future_same_plan():
    db_mock = MagicMock()
    existing = MagicMock()
    existing._mapping = {
        "subscription_id": "subscription-pro",
        "status": "active",
        "current_period_end": "2026-07-01T00:00:00",
    }
    extended = MagicMock()
    extended._mapping = {
        "subscription_id": "subscription-pro",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-31T00:00:00",
        "next_billing_at": "2026-07-31T00:00:00",
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=existing)),
        MagicMock(fetchone=MagicMock(return_value=extended)),
    ]

    result = subscription_service.create_or_extend_subscription(
        db=db_mock,
        user_id="user-1",
        plan_id="plan-pro",
        payment_id="payment-1",
    )

    update_sql = str(db_mock.execute.call_args_list[1].args[0])
    assert "current_period_end + INTERVAL '30 days'" in update_sql
    assert "last_payment_id = :payment_id" in update_sql
    assert result["subscription_id"] == "subscription-pro"


def test_create_or_extend_subscription_inserts_when_same_plan_missing():
    db_mock = MagicMock()
    inserted = MagicMock()
    inserted._mapping = {
        "subscription_id": "subscription-new",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
    }
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=None)),
        MagicMock(fetchone=MagicMock(return_value=inserted)),
    ]

    result = subscription_service.create_or_extend_subscription(
        db=db_mock,
        user_id="user-1",
        plan_id="plan-pro",
        payment_id="payment-1",
    )

    insert_sql = str(db_mock.execute.call_args_list[1].args[0])
    insert_params = db_mock.execute.call_args_list[1].args[1]
    assert "INSERT INTO subscriptions" in insert_sql
    assert "NOW() + INTERVAL '30 days'" in insert_sql
    assert insert_params["plan_id"] == "plan-pro"
    assert insert_params["payment_id"] == "payment-1"
    assert result["subscription_id"] == "subscription-new"


def test_apply_upgrade_with_carryover_creates_upper_and_extends_lower():
    db_mock = MagicMock()
    target_plan = _mock_plan_row("studio", 20)
    lower = MagicMock()
    lower._mapping = {
        "subscription_id": "subscription-pro",
        "plan_id": "plan-pro",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-06-21T00:00:00",
        "plan_rank": 10,
    }
    upper = MagicMock()
    upper._mapping = {
        "subscription_id": "subscription-studio",
        "current_period_start": "2026-06-01T00:00:00",
        "current_period_end": "2026-07-01T00:00:00",
        "next_billing_at": "2026-07-01T00:00:00",
    }
    lower_update = MagicMock()
    lower_update._mapping = {
        "subscription_id": "subscription-pro",
        "plan_id": "plan-pro",
        "original_period_end": "2026-06-21T00:00:00",
        "current_period_end": "2026-07-21T00:00:00",
        "carried_over_days": 20,
        "remaining_seconds": 1728000,
    }
    plan_change = MagicMock()
    plan_change._mapping = {"plan_change_id": "change-upgrade-1"}
    db_mock.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=target_plan)),
        MagicMock(fetchone=MagicMock(return_value=lower)),
        MagicMock(fetchone=MagicMock(return_value=upper)),
        MagicMock(fetchone=MagicMock(return_value=lower_update)),
        MagicMock(fetchone=MagicMock(return_value=plan_change)),
    ]

    result = subscription_service.apply_upgrade_with_carryover(
        db=db_mock,
        user_id="user-1",
        from_subscription_id="subscription-pro",
        to_plan_id="studio",
        payment_id="payment-1",
    )

    insert_upper_sql = str(db_mock.execute.call_args_list[2].args[0])
    update_lower_sql = str(db_mock.execute.call_args_list[3].args[0])
    change_sql = str(db_mock.execute.call_args_list[4].args[0])
    assert "INSERT INTO subscriptions" in insert_upper_sql
    assert "NOW() + INTERVAL '30 days'" in insert_upper_sql
    assert "current_period_end = calculated.carried_end" in update_lower_sql
    assert "auto_renew = false" in update_lower_sql
    assert "cancel_at_period_end = true" in update_lower_sql
    assert "superseded_by_subscription_id = :upper_subscription_id" in update_lower_sql
    assert "INSERT INTO subscription_plan_changes" in change_sql
    assert "'upgrade'" in change_sql
    assert result["subscription_id"] == "subscription-studio"
    assert result["carried_over_days"] == 20
