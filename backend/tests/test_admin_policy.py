from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import main
from services import admin as admin_service


client = TestClient(main.app)


def test_get_admin_policy_settings(monkeypatch):
    monkeypatch.setattr(admin_service, "get_admin_policies", lambda: {
        "payment": {
            "plans": {
                "free": {"credits": 5, "price": 0},
                "pro": {"credits": 50, "price": 2900},
                "studio": {"credits": 500, "price": 19800},
            },
            "creditPlans": {
                "credit_100": {"credits": 100, "bonusCredits": 0, "price": 5000},
                "credit_500": {"credits": 500, "bonusCredits": 0, "price": 20000},
            },
        },
        "retention": {
            "plans": {
                "free": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                "pro": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                "studio": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
            }
        },
    })

    response = client.get("/admin/policy")

    assert response.status_code == 200
    assert response.json()["data"]["payment"]["plans"]["free"]["credits"] == 5
    assert response.json()["data"]["payment"]["plans"]["pro"]["price"] == 2900
    assert response.json()["data"]["payment"]["plans"]["studio"]["price"] == 19800
    assert response.json()["data"]["retention"]["plans"]["free"]["metadataRetentionDays"] == 90
    assert response.json()["data"]["payment"]["creditPlans"]["credit_100"]["credits"] == 100
    assert response.json()["data"]["payment"]["creditPlans"]["credit_500"]["price"] == 20000


def test_update_admin_policy_settings(monkeypatch):
    saved = []

    def fake_update(policies, *args, **kwargs):
        saved.append(policies)
        return policies

    monkeypatch.setattr(admin_service, "update_admin_policies", fake_update)

    payload = {
        "policies": {
            "payment": {
                "plans": {
                    "free": {"credits": 5, "price": 0},
                    "pro": {"credits": 50, "price": 2900},
                    "studio": {"credits": 500, "price": 19800},
                }
            },
            "retention": {
                "plans": {
                    "free": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                    "pro": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                    "studio": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                }
            },
        }
    }

    response = client.put("/admin/policy", json=payload)

    assert response.status_code == 200
    assert saved == [payload["policies"]]
    assert response.json()["data"]["payment"]["plans"]["pro"]["price"] == 2900
    assert response.json()["data"]["retention"]["plans"]["studio"]["autoDeleteOriginalHours"] == 12


def test_list_admin_subscription_plans(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {
            "data": [
                {
                    "plan_id": "plan-1",
                    "plan_code": "pro",
                    "plan_name": "Pro",
                    "sort_order": 20,
                    "status": "active",
                }
            ],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    monkeypatch.setattr(admin_service, "list_subscription_plans", fake_list)

    response = client.get("/admin/plans?q=pro&page=2&limit=10")

    assert response.status_code == 200
    assert captured == {"q": "pro", "include_deleted": False, "status": None, "page": 2, "limit": 10}
    assert response.json()["data"][0]["plan_code"] == "pro"
    assert response.json()["total"] == 1
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 10


def test_create_admin_subscription_plan(monkeypatch):
    captured = {}

    def fake_create(payload):
        captured.update(payload)
        return {"plan_id": "plan-new", **payload}

    monkeypatch.setattr(admin_service, "create_subscription_plan", fake_create)

    payload = {
        "plan_code": "business",
        "plan_name": "Business",
        "badge_label": "기업",
        "badge_class": "mui-chip--secondary",
        "description": "기업 사용자에게 적합한 플랜입니다.",
        "price_amount": 99000,
        "sort_order": 40,
        "status": "active",
    }
    response = client.post("/admin/plans", json=payload)

    assert response.status_code == 201
    assert captured["plan_code"] == "business"
    assert captured["badge_label"] == "기업"
    assert captured["description"] == "기업 사용자에게 적합한 플랜입니다."
    assert response.json()["data"]["plan_name"] == "Business"


def test_update_admin_subscription_plan(monkeypatch):
    captured = {}

    def fake_update(plan_id, payload):
        captured.update({"plan_id": plan_id, "payload": payload})
        return {"plan_id": plan_id, **payload}

    monkeypatch.setattr(admin_service, "update_subscription_plan", fake_update)

    response = client.put(
        "/admin/plans/plan-1",
        json={
            "plan_name": "Pro Plus",
            "badge_label": "추천",
            "description": "자주 분석하는 사용자에게 적합합니다.",
            "sort_order": 25,
        },
    )

    assert response.status_code == 200
    assert captured == {
        "plan_id": "plan-1",
        "payload": {
            "plan_name": "Pro Plus",
            "badge_label": "추천",
            "description": "자주 분석하는 사용자에게 적합합니다.",
            "sort_order": 25,
        },
    }
    assert response.json()["data"]["plan_name"] == "Pro Plus"


def test_delete_admin_subscription_plan_soft_deletes(monkeypatch):
    captured = {}

    def fake_delete(plan_id):
        captured["plan_id"] = plan_id
        return {"plan_id": plan_id, "status": "deleted"}

    monkeypatch.setattr(admin_service, "delete_subscription_plan", fake_delete)

    response = client.delete("/admin/plans/plan-1")

    assert response.status_code == 200
    assert captured["plan_id"] == "plan-1"
    assert response.json()["data"]["status"] == "deleted"


def test_list_admin_credit_plans(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {
            "data": [
                {
                    "credit_plan_id": "credit-plan-1",
                    "credit_plan_code": "credit_100",
                    "credit_plan_name": "100 Credits",
                    "sort_order": 10,
                    "status": "active",
                }
            ],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    monkeypatch.setattr(admin_service, "list_credit_plans", fake_list)

    response = client.get("/admin/credit-plans?q=100&page=3&limit=5")

    assert response.status_code == 200
    assert captured == {"q": "100", "include_deleted": False, "status": None, "page": 3, "limit": 5}
    assert response.json()["data"][0]["credit_plan_code"] == "credit_100"
    assert response.json()["total"] == 1


def test_create_admin_credit_plan(monkeypatch):
    captured = {}

    def fake_create(payload):
        captured.update(payload)
        return {"credit_plan_id": "credit-plan-new", **payload}

    monkeypatch.setattr(admin_service, "create_credit_plan", fake_create)

    payload = {
        "credit_plan_code": "credit_1000",
        "credit_plan_name": "1000 Credits",
        "price_amount": 35000,
        "base_credits": 1000,
        "bonus_credits": 100,
        "sort_order": 30,
        "status": "active",
    }
    response = client.post("/admin/credit-plans", json=payload)

    assert response.status_code == 201
    assert captured["credit_plan_code"] == "credit_1000"
    assert response.json()["data"]["base_credits"] == 1000


def test_update_admin_credit_plan(monkeypatch):
    captured = {}

    def fake_update(credit_plan_id, payload):
        captured.update({"credit_plan_id": credit_plan_id, "payload": payload})
        return {"credit_plan_id": credit_plan_id, **payload}

    monkeypatch.setattr(admin_service, "update_credit_plan", fake_update)

    response = client.put(
        "/admin/credit-plans/credit-plan-1",
        json={"price_amount": 45000, "sort_order": 35},
    )

    assert response.status_code == 200
    assert captured == {
        "credit_plan_id": "credit-plan-1",
        "payload": {"price_amount": 45000, "sort_order": 35},
    }
    assert response.json()["data"]["price_amount"] == 45000


def test_delete_admin_credit_plan_soft_deletes(monkeypatch):
    captured = {}

    def fake_delete(credit_plan_id):
        captured["credit_plan_id"] = credit_plan_id
        return {"credit_plan_id": credit_plan_id, "status": "deleted"}

    monkeypatch.setattr(admin_service, "delete_credit_plan", fake_delete)

    response = client.delete("/admin/credit-plans/credit-plan-1")

    assert response.status_code == 200
    assert captured["credit_plan_id"] == "credit-plan-1"
    assert response.json()["data"]["status"] == "deleted"


def test_service_list_subscription_plans_filters_and_sorts(monkeypatch):
    row = MagicMock()
    row._mapping = {
        "plan_id": "550e8400-e29b-41d4-a716-446655440001",
        "plan_code": "pro",
        "plan_name": "Pro",
        "badge_label": "추천",
        "badge_class": "mui-chip--soft-warning",
        "description": "자주 분석하는 사용자에게 적합합니다.",
        "sort_order": 20,
        "status": "active",
    }
    result = MagicMock()
    result.scalar.return_value = 1
    result.fetchall.return_value = [row]
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_subscription_plans(q="pro")

    count_sql = str(db.execute.call_args_list[0].args[0])
    sql = str(db.execute.call_args_list[1].args[0])
    params = db.execute.call_args_list[1].args[1]
    assert "SELECT COUNT(*)" in count_sql
    assert "FROM plans" in sql
    assert "badge_label" in sql
    assert "badge_class" in sql
    assert "description" in sql
    assert "cta_label" not in sql
    assert "status <> 'deleted'" in sql
    assert "LOWER(plan_code)" in sql
    assert "ORDER BY sort_order ASC, created_at ASC" in sql
    assert "LIMIT :limit OFFSET :offset" in sql
    assert params == {"q": "%pro%", "limit": 20, "offset": 0}
    assert data["total"] == 1
    data = data["data"]
    assert data[0]["plan_code"] == "pro"
    assert data[0]["badge_label"] == "추천"
    db.close.assert_called_once()


def test_service_update_subscription_plan_soft_delete_sql(monkeypatch):
    row = MagicMock()
    row._mapping = {
        "plan_id": "550e8400-e29b-41d4-a716-446655440001",
        "plan_code": "pro",
        "plan_name": "Pro",
        "status": "deleted",
    }
    result = MagicMock()
    result.fetchone.return_value = row
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.delete_subscription_plan("550e8400-e29b-41d4-a716-446655440001")

    sql = str(db.execute.call_args.args[0])
    params = db.execute.call_args.args[1]
    assert "UPDATE plans" in sql
    assert "status = :status" in sql
    assert "updated_at = NOW()" in sql
    assert params["status"] == "deleted"
    assert data["status"] == "deleted"
    db.commit.assert_called_once()


def test_service_update_subscription_plan_pricing_copy_sql(monkeypatch):
    row = MagicMock()
    row._mapping = {
        "plan_id": "550e8400-e29b-41d4-a716-446655440001",
        "plan_code": "pro",
        "plan_name": "Pro",
        "badge_label": "추천",
        "badge_class": "mui-chip--soft-warning",
        "description": "자주 분석하는 사용자에게 적합합니다.",
        "status": "active",
    }
    result = MagicMock()
    result.fetchone.return_value = row
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.update_subscription_plan(
        "550e8400-e29b-41d4-a716-446655440001",
        {
            "badge_label": "추천",
            "badge_class": "mui-chip--soft-warning",
            "description": "자주 분석하는 사용자에게 적합합니다.",
        },
    )

    sql = str(db.execute.call_args.args[0])
    params = db.execute.call_args.args[1]
    assert "UPDATE plans" in sql
    assert "badge_label = :badge_label" in sql
    assert "badge_class = :badge_class" in sql
    assert "description = :description" in sql
    assert "cta_label" not in sql
    assert params["badge_label"] == "추천"
    assert data["description"] == "자주 분석하는 사용자에게 적합합니다."
    db.commit.assert_called_once()


def test_service_list_credit_plans_filters_and_sorts(monkeypatch):
    row = MagicMock()
    row._mapping = {
        "credit_plan_id": "550e8400-e29b-41d4-a716-446655440002",
        "credit_plan_code": "credit_100",
        "credit_plan_name": "100 Credits",
        "sort_order": 10,
        "status": "active",
    }
    result = MagicMock()
    result.scalar.return_value = 1
    result.fetchall.return_value = [row]
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_credit_plans(q="100")

    count_sql = str(db.execute.call_args_list[0].args[0])
    sql = str(db.execute.call_args_list[1].args[0])
    params = db.execute.call_args_list[1].args[1]
    assert "SELECT COUNT(*)" in count_sql
    assert "FROM credit_plans" in sql
    assert "status <> 'deleted'" in sql
    assert "LOWER(credit_plan_code)" in sql
    assert "ORDER BY sort_order ASC, created_at ASC" in sql
    assert "LIMIT :limit OFFSET :offset" in sql
    assert params == {"q": "%100%", "limit": 20, "offset": 0}
    assert data["total"] == 1
    data = data["data"]
    assert data[0]["credit_plan_code"] == "credit_100"
    db.close.assert_called_once()


def test_service_list_subscription_plans_status_filter_overrides_deleted_exclusion(monkeypatch):
    result = MagicMock()
    result.scalar.return_value = 0
    result.fetchall.return_value = []
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_subscription_plans(status="deleted")

    sql = str(db.execute.call_args_list[1].args[0])
    params = db.execute.call_args_list[1].args[1]
    assert "status = :status_filter" in sql
    assert "status <> 'deleted'" not in sql
    assert params["status_filter"] == "deleted"
    assert data["total"] == 0
    db.close.assert_called_once()


def test_service_list_subscription_plans_normalizes_page_and_limit(monkeypatch):
    result = MagicMock()
    result.scalar.return_value = 0
    result.fetchall.return_value = []
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_subscription_plans(page=3, limit=7)

    params = db.execute.call_args_list[1].args[1]
    assert params["limit"] == 20
    assert params["offset"] == 40
    assert data["page"] == 3
    assert data["limit"] == 20
    db.close.assert_called_once()


def test_service_list_credit_plans_status_filter_overrides_deleted_exclusion(monkeypatch):
    result = MagicMock()
    result.scalar.return_value = 0
    result.fetchall.return_value = []
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_credit_plans(status="deleted")

    sql = str(db.execute.call_args_list[1].args[0])
    params = db.execute.call_args_list[1].args[1]
    assert "status = :status_filter" in sql
    assert "status <> 'deleted'" not in sql
    assert params["status_filter"] == "deleted"
    assert data["total"] == 0
    db.close.assert_called_once()


def test_service_list_credit_plans_uses_allowed_page_limit(monkeypatch):
    result = MagicMock()
    result.scalar.return_value = 0
    result.fetchall.return_value = []
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.list_credit_plans(page=2, limit=50)

    params = db.execute.call_args_list[1].args[1]
    assert params["limit"] == 50
    assert params["offset"] == 50
    assert data["page"] == 2
    assert data["limit"] == 50
    db.close.assert_called_once()


def test_service_update_credit_plan_soft_delete_sql(monkeypatch):
    row = MagicMock()
    row._mapping = {
        "credit_plan_id": "550e8400-e29b-41d4-a716-446655440002",
        "credit_plan_code": "credit_100",
        "credit_plan_name": "100 Credits",
        "status": "deleted",
    }
    result = MagicMock()
    result.fetchone.return_value = row
    db = MagicMock()
    db.execute.return_value = result
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db)

    data = admin_service.delete_credit_plan("550e8400-e29b-41d4-a716-446655440002")

    sql = str(db.execute.call_args.args[0])
    params = db.execute.call_args.args[1]
    assert "UPDATE credit_plans" in sql
    assert "status = :status" in sql
    assert "updated_at = NOW()" in sql
    assert params["status"] == "deleted"
    assert data["status"] == "deleted"
    db.commit.assert_called_once()


def test_list_admin_subscription_plans_with_status_filter(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {"data": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(admin_service, "list_subscription_plans", fake_list)

    response = client.get("/admin/plans?status=active")

    assert response.status_code == 200
    assert captured["status"] == "active"


def test_list_admin_subscription_plans_can_request_deleted_status(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {"data": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(admin_service, "list_subscription_plans", fake_list)

    response = client.get("/admin/plans?status=deleted&page=1&limit=20")

    assert response.status_code == 200
    assert captured["status"] == "deleted"
    assert captured["page"] == 1
    assert captured["limit"] == 20


def test_list_admin_credit_plans_with_status_filter(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {"data": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(admin_service, "list_credit_plans", fake_list)

    response = client.get("/admin/credit-plans?status=inactive")

    assert response.status_code == 200
    assert captured["status"] == "inactive"


def test_list_admin_credit_plans_can_request_deleted_status(monkeypatch):
    captured = {}

    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        captured.update(
            {"q": q, "include_deleted": include_deleted, "status": status, "page": page, "limit": limit}
        )
        return {"data": [], "total": 0, "page": page, "limit": limit}

    monkeypatch.setattr(admin_service, "list_credit_plans", fake_list)

    response = client.get("/admin/credit-plans?status=deleted&page=1&limit=20")

    assert response.status_code == 200
    assert captured["status"] == "deleted"
    assert captured["page"] == 1
    assert captured["limit"] == 20


def test_list_admin_subscription_plans_invalid_status_returns_400(monkeypatch):
    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        raise ValueError("status must be one of active, inactive, deleted")

    monkeypatch.setattr(admin_service, "list_subscription_plans", fake_list)

    response = client.get("/admin/plans?status=archived")

    assert response.status_code == 400
    assert "status must be one of active, inactive, deleted" in response.json()["message"]


def test_list_admin_credit_plans_invalid_status_returns_400(monkeypatch):
    def fake_list(q=None, include_deleted=False, status=None, page=1, limit=20):
        raise ValueError("status must be one of active, inactive, deleted")

    monkeypatch.setattr(admin_service, "list_credit_plans", fake_list)

    response = client.get("/admin/credit-plans?status=archived")

    assert response.status_code == 400
    assert "status must be one of active, inactive, deleted" in response.json()["message"]


def test_service_create_subscription_plan_blocks_5th_active(monkeypatch):
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar.return_value = 4
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db_mock)

    payload = {
        "plan_code": "business",
        "plan_name": "Business",
        "result_retention_days": 10,
        "status": "active"
    }

    import pytest
    with pytest.raises(ValueError, match="활성화된 구독 플랜 카드는 최대 4개까지만 등록할 수 있습니다."):
        admin_service.create_subscription_plan(payload)


def test_service_update_subscription_plan_blocks_5th_active(monkeypatch):
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar.return_value = 4
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db_mock)

    payload = {
        "status": "active"
    }

    import pytest
    with pytest.raises(ValueError, match="활성화된 구독 플랜 카드는 최대 4개까지만 등록할 수 있습니다."):
        admin_service.update_subscription_plan("550e8400-e29b-41d4-a716-446655440001", payload)


def test_service_create_credit_plan_blocks_9th_active(monkeypatch):
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar.return_value = 8
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db_mock)

    payload = {
        "credit_plan_code": "credit_999",
        "credit_plan_name": "Premium Credit",
        "price_amount": 100000,
        "base_credits": 10000,
        "status": "active"
    }

    import pytest
    with pytest.raises(ValueError, match="활성화된 크레딧 플랜 카드는 최대 8개까지만 등록할 수 있습니다."):
        admin_service.create_credit_plan(payload)


def test_service_update_credit_plan_blocks_9th_active(monkeypatch):
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar.return_value = 8
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: db_mock)

    payload = {
        "status": "active"
    }

    import pytest
    with pytest.raises(ValueError, match="활성화된 크레딧 플랜 카드는 최대 8개까지만 등록할 수 있습니다."):
        admin_service.update_credit_plan("550e8400-e29b-41d4-a716-446655440002", payload)
