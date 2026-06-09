from fastapi.testclient import TestClient

import main
from services import admin as admin_service

client = TestClient(main.app)


class FakeResult:
    def __init__(self, scalar_value=None, row=None, rows=None):
        self._scalar_value = scalar_value
        self._row = row
        self._rows = rows or []

    def scalar(self):
        return self._scalar_value

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class FakeAdminSubscriptionsSession:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params or {}))

        if "SELECT COUNT(*)" in sql and "FROM users u" in sql:
            return FakeResult(scalar_value=1)

        if "COUNT(*) FILTER" in sql and "scheduled_change_users" in sql:
            return FakeResult(row=FakeRow({
                "total_users": 1,
                "paid_users": 1,
                "billing_failed_users": 1,
                "scheduled_change_users": 1,
            }))

        if "ORDER BY" in sql and "active_subscription_count" in sql:
            return FakeResult(rows=[FakeRow({
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "email": "admin-check@example.com",
                "current_plan_code": "studio",
                "current_plan_name": "Studio",
                "subscription_id": "750e8400-e29b-41d4-a716-446655440000",
                "subscription_status": "active",
                "current_period_start": None,
                "current_period_end": None,
                "next_billing_at": None,
                "auto_renew": True,
                "cancel_at_period_end": False,
                "cancelled_at": None,
                "billing_status": "failed",
                "active_subscription_count": 2,
                "carried_over_subscription_id": "850e8400-e29b-41d4-a716-446655440000",
                "carried_over_plan_code": "pro",
                "carried_over_plan_name": "Pro",
                "carried_over_period_end": None,
                "carried_over_days": 12,
                "plan_change_id": "950e8400-e29b-41d4-a716-446655440000",
                "scheduled_change_type": "downgrade",
                "scheduled_change_status": "scheduled",
                "scheduled_change_effective_at": None,
                "scheduled_to_plan_code": "pro",
                "scheduled_to_plan_name": "Pro",
                "last_attempted_at": None,
                "last_attempt_status": None,
                "last_attempt_type": None,
                "last_failure_reason": None,
            })])

        raise AssertionError(f"Unexpected SQL: {sql}")

    def close(self):
        self.closed = True


class FakeAdminSubscriptionDetailSession:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params or {}))

        if "FROM users u" in sql and "LEFT JOIN LATERAL" in sql:
            return FakeResult(row=FakeRow({
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "email": "user1@example.com",
                "subscription_id": "750e8400-e29b-41d4-a716-446655440000",
                "subscription_status": "active",
                "current_period_start": None,
                "current_period_end": None,
                "next_billing_at": None,
                "auto_renew": True,
                "cancel_at_period_end": False,
                "cancelled_at": None,
                "billing_status": "failed",
                "carried_over_days": 0,
                "superseded_by_subscription_id": None,
                "current_plan_code": "studio",
                "current_plan_name": "Studio",
                "free_plan_code": "free",
                "free_plan_name": "Free",
            }))

        if "FROM subscriptions s" in sql and "ORDER BY p.plan_rank DESC" in sql:
            return FakeResult(rows=[FakeRow({
                "subscription_id": "750e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "current_period_start": None,
                "current_period_end": None,
                "next_billing_at": None,
                "auto_renew": True,
                "cancel_at_period_end": False,
                "cancelled_at": None,
                "billing_status": "failed",
                "carried_over_days": 0,
                "superseded_by_subscription_id": None,
                "original_period_end": None,
                "upgraded_at": None,
                "created_at": None,
                "plan_id": "plan-studio",
                "plan_code": "studio",
                "plan_name": "Studio",
            })])

        if "FROM subscription_billing_attempts" in sql:
            return FakeResult(rows=[FakeRow({
                "billing_attempt_id": "a50e8400-e29b-41d4-a716-446655440000",
                "subscription_id": "750e8400-e29b-41d4-a716-446655440000",
                "plan_change_id": None,
                "attempt_type": "renewal",
                "status": "failed",
                "amount": 19800,
                "payment_id": None,
                "failure_message": "card_declined",
                "attempted_at": None,
            })])

        if "FROM subscription_plan_changes pc" in sql:
            return FakeResult(rows=[FakeRow({
                "plan_change_id": "950e8400-e29b-41d4-a716-446655440000",
                "change_type": "downgrade",
                "status": "scheduled",
                "apply_timing": "period_end",
                "effective_at": None,
                "applied_at": None,
                "created_at": None,
                "from_subscription_id": "750e8400-e29b-41d4-a716-446655440000",
                "to_subscription_id": None,
                "from_plan_code": "studio",
                "from_plan_name": "Studio",
                "to_plan_code": "pro",
                "to_plan_name": "Pro",
            })])

        raise AssertionError(f"Unexpected SQL: {sql}")

    def close(self):
        self.closed = True


def test_list_admin_subscriptions(monkeypatch):
    captured = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return {
            "data": [{
                "user_id": "user-1",
                "email": "user1@example.com",
                "current_plan_code": "pro",
                "current_plan_name": "Pro",
                "current_subscription": {
                    "subscription_id": "sub-1",
                    "status": "active",
                    "current_period_start": None,
                    "current_period_end": None,
                    "next_billing_at": None,
                    "auto_renew": True,
                    "cancel_at_period_end": False,
                    "cancelled_at": None,
                    "billing_status": "active",
                },
                "active_subscription_count": 1,
                "carried_over_subscription": None,
                "scheduled_plan_change": None,
                "latest_billing_attempt": None,
            }],
            "summary": {
                "total_users": 1,
                "paid_users": 1,
                "billing_failed_users": 0,
                "scheduled_change_users": 0,
            },
            "total": 1,
            "page": 1,
            "limit": 10,
        }

    monkeypatch.setattr(admin_service, "get_admin_subscriptions_list", fake_list)

    response = client.get(
        "/admin/subscriptions?q=user1&search_key=all&plan_code=pro&subscription_status=active"
        "&auto_renew=true&cancel_scheduled=false&billing_failed=true&scheduled_change=false&page=1&limit=10"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["current_plan_code"] == "pro"
    assert captured == {
        "q": "user1",
        "search_key": "all",
        "plan_code": "pro",
        "subscription_status": "active",
        "auto_renew": "true",
        "cancel_scheduled": "false",
        "billing_failed": "true",
        "scheduled_change": "false",
        "page": 1,
        "limit": 10,
    }


def test_get_admin_subscription_detail(monkeypatch):
    def fake_detail(user_id):
        if user_id == "650e8400-e29b-41d4-a716-446655440000":
            return {
                "user": {"user_id": user_id, "email": "user1@example.com"},
                "current_applied_plan": {"plan_code": "studio", "plan_name": "Studio"},
                "active_subscriptions": [],
                "billing_attempts": [],
                "plan_changes": [],
            }
        raise ValueError("user not found")

    monkeypatch.setattr(admin_service, "get_admin_subscription_detail", fake_detail)

    success = client.get("/admin/subscriptions/650e8400-e29b-41d4-a716-446655440000")
    assert success.status_code == 200
    assert success.json()["data"]["current_applied_plan"]["plan_code"] == "studio"

    failure = client.get("/admin/subscriptions/non-existent-user")
    assert failure.status_code == 404
    assert "user not found" in failure.json()["message"]


def test_get_admin_subscriptions_list_service_maps_filters_and_payload(monkeypatch):
    session = FakeAdminSubscriptionsSession()
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: session)

    result = admin_service.get_admin_subscriptions_list(
        q="admin-check",
        search_key="all",
        plan_code="studio",
        subscription_status="active",
        auto_renew="true",
        cancel_scheduled="false",
        billing_failed="true",
        scheduled_change="true",
        page=1,
        limit=10,
    )

    executed_sql = "\n".join(sql for sql, _ in session.calls)
    executed_params = session.calls[0][1]

    assert "COALESCE(current_plan.plan_code, free_plan.plan_code) = :plan_code" in executed_sql
    assert "current_sub.auto_renew IS TRUE" in executed_sql
    assert "COALESCE(current_sub.billing_status, '') IN ('failed', 'billing_key_missing')" in executed_sql
    assert "scheduled_change.plan_change_id IS NOT NULL" in executed_sql
    assert executed_params["q"] == "%admin-check%"
    assert executed_params["plan_code"] == "studio"
    assert result["summary"]["billing_failed_users"] == 1
    assert result["data"][0]["carried_over_subscription"]["plan_code"] == "pro"
    assert result["data"][0]["scheduled_plan_change"]["change_type"] == "downgrade"
    assert session.closed is True


def test_get_admin_subscription_detail_service_returns_histories(monkeypatch):
    session = FakeAdminSubscriptionDetailSession()
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: session)

    result = admin_service.get_admin_subscription_detail("650e8400-e29b-41d4-a716-446655440000")

    executed_sql = "\n".join(sql for sql, _ in session.calls)
    assert "FROM subscription_billing_attempts" in executed_sql
    assert "FROM subscription_plan_changes pc" in executed_sql
    assert result["user"]["email"] == "user1@example.com"
    assert result["current_applied_plan"]["plan_code"] == "studio"
    assert result["active_subscriptions"][0]["plan_code"] == "studio"
    assert result["billing_attempts"][0]["failure_reason"] == "card_declined"
    assert result["plan_changes"][0]["to_plan_code"] == "pro"
    assert session.closed is True
