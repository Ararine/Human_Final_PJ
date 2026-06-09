from fastapi.testclient import TestClient
import pytest
import main
from services import admin as admin_service

client = TestClient(main.app)


class FakePaymentRow:
    def __init__(self, status="success", amount=2900, balance_amount=2900):
        self._mapping = {
            "payment_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": status,
            "amount": amount,
            "balance_amount": balance_amount,
        }


class FakeResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class FakeRefundSession:
    def __init__(self, payment_status="success"):
        self.payment_status = payment_status
        self.calls = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params or {}))
        if "SELECT payment_id, status, amount, balance_amount" in sql:
            return FakeResult(FakePaymentRow(status=self.payment_status))
        return FakeResult()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakePaymentDetailRow:
    def __init__(self):
        self._mapping = {
            "payment_id": "550e8400-e29b-41d4-a716-446655440000",
            "paid_at": None,
            "requested_at": None,
            "approved_at": None,
            "refunded_at": None,
            "created_at": None,
            "user_id": "650e8400-e29b-41d4-a716-446655440000",
            "user_email": "user1@example.com",
            "product_type": "credit",
            "product_name": "100 Credits",
            "amount": 5000,
            "balance_amount": 5000,
            "status": "success",
            "payment_method": "card",
            "pg_provider": "toss",
            "subscription_id": None,
            "credit_ledger_id": "750e8400-e29b-41d4-a716-446655440000",
            "credit_amount": 100,
        }


class FakePaymentDetailSession:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params or {}))
        return FakeResult(FakePaymentDetailRow())

    def close(self):
        self.closed = True


def test_list_payments(monkeypatch):
    captured = {}
    def fake_get_list(product_type=None, status=None, q=None, search_key="email", date_from=None, date_to=None, page=1, limit=10):
        captured.update({
            "product_type": product_type,
            "status": status,
            "q": q,
            "search_key": search_key,
            "date_from": date_from,
            "date_to": date_to,
            "page": page,
            "limit": limit
        })
        return {
            "data": [{
                "payment_id": "550e8400-e29b-41d4-a716-446655440000",
                "paid_at": "2026-06-09T14:20:15",
                "requested_at": "2026-06-09T14:20:00",
                "user_id": "user-uuid-1",
                "user_email": "user1@example.com",
                "product_type": "subscription",
                "product_name": "Pro 구독 플랜",
                "amount": 2900,
                "status": "success",
                "payment_method": "카드",
                "pg_provider": "toss"
            }],
            "summary": {
                "today_amount": 2900,
                "success_count": 1,
                "refund_count": 0,
                "credit_count": 0
            },
            "total": 1,
            "page": page,
            "limit": limit
        }

    monkeypatch.setattr(admin_service, "get_payments_list", fake_get_list)

    response = client.get(
        "/admin/payments?product_type=subscription&status=success&q=user1&search_key=email&date_from=2026-06-01&date_to=2026-06-10&page=1&limit=10"
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total"] == 1
    assert len(res_data["data"]) == 1
    assert res_data["data"][0]["user_email"] == "user1@example.com"
    assert "pg_transaction_id" not in res_data["data"][0]
    assert "last_transaction_key" not in res_data["data"][0]
    assert "receipt_url" not in res_data["data"][0]
    assert res_data["summary"]["today_amount"] == 2900
    assert captured == {
        "product_type": "subscription",
        "status": "success",
        "q": "user1",
        "search_key": "email",
        "date_from": "2026-06-01",
        "date_to": "2026-06-10",
        "page": 1,
        "limit": 10
    }


def test_get_payment_detail(monkeypatch):
    def fake_get_detail(payment_id):
        if payment_id == "550e8400-e29b-41d4-a716-446655440000":
            return {
                "payment_id": payment_id,
                "paid_at": "2026-06-09T14:20:15",
                "requested_at": "2026-06-09T14:20:00",
                "approved_at": "2026-06-09T14:20:15",
                "refunded_at": None,
                "user_id": "user-uuid-1",
                "user_email": "user1@example.com",
                "product_type": "subscription",
                "product_name": "Pro 구독 플랜",
                "amount": 2900,
                "balance_amount": 2900,
                "status": "success",
                "payment_method": "카드",
                "pg_provider": "toss",
                "subscription_id": "sub-uuid-1",
                "credit_ledger_id": None,
                "credit_amount": 0,
                "admin_note": "정상 결제 건입니다."
            }
        raise ValueError("결제 내역을 찾을 수 없습니다.")

    monkeypatch.setattr(admin_service, "get_payment_detail", fake_get_detail)

    # 성공 케이스
    response = client.get("/admin/payments/550e8400-e29b-41d4-a716-446655440000")
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert res_data["payment_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert "pg_transaction_id" not in res_data
    assert "last_transaction_key" not in res_data
    assert "receipt_url" not in res_data

    # 실패 케이스 (404)
    response_fail = client.get("/admin/payments/non-existent-uuid")
    assert response_fail.status_code == 404
    assert "결제 내역을 찾을 수 없습니다." in response_fail.json()["message"]


def test_get_payment_detail_service_uses_credit_ledger_ledger_id(monkeypatch):
    session = FakePaymentDetailSession()
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: session)

    result = admin_service.get_payment_detail("550e8400-e29b-41d4-a716-446655440000")

    executed_sql = "\n".join(sql for sql, _ in session.calls)
    assert "cl.ledger_id" in executed_sql
    assert "cl.credit_ledger_id" not in executed_sql
    assert result["credit_ledger_id"] == "750e8400-e29b-41d4-a716-446655440000"
    assert result["credit_amount"] == 100
    assert session.closed is True


def test_refund_payment(monkeypatch):
    captured = {}
    def fake_refund(payment_id, admin_user_id):
        captured.update({"payment_id": payment_id, "admin_user_id": admin_user_id})
        return {"payment_id": payment_id, "status": "refunded"}

    monkeypatch.setattr(admin_service, "refund_payment", fake_refund)

    response = client.post("/admin/payments/550e8400-e29b-41d4-a716-446655440000/refund")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "refunded"
    assert captured["payment_id"] == "550e8400-e29b-41d4-a716-446655440000"


def test_refund_payment_service_updates_payment_and_writes_audit_log(monkeypatch):
    session = FakeRefundSession(payment_status="success")
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: session)

    result = admin_service.refund_payment(
        "550e8400-e29b-41d4-a716-446655440000",
        admin_user_id="admin-user-1",
    )

    executed_sql = "\n".join(sql for sql, _ in session.calls)
    assert result == {
        "payment_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "refunded",
    }
    assert "SELECT payment_id, status, amount, balance_amount" in executed_sql
    assert "UPDATE payments" in executed_sql
    assert "SET status = 'refunded'" in executed_sql
    assert "INSERT INTO audit_logs" in executed_sql
    assert "'refund_payment'" in executed_sql
    assert "'payment'" in executed_sql

    audit_call = next(sql_params for sql_params in session.calls if "INSERT INTO audit_logs" in sql_params[0])
    assert audit_call[1]["actor_user_id"] == "admin-user-1"
    assert '"action": "refund_payment"' in audit_call[1]["detail"]
    assert '"payment_id": "550e8400-e29b-41d4-a716-446655440000"' in audit_call[1]["detail"]
    assert session.committed is True
    assert session.rolled_back is False
    assert session.closed is True


def test_refund_payment_service_rejects_already_refunded_payment(monkeypatch):
    session = FakeRefundSession(payment_status="refunded")
    monkeypatch.setattr(admin_service, "SessionLocal", lambda: session)

    with pytest.raises(ValueError, match="이미 환불/취소 처리된 결제입니다."):
        admin_service.refund_payment("550e8400-e29b-41d4-a716-446655440000")

    executed_sql = "\n".join(sql for sql, _ in session.calls)
    assert "SELECT payment_id, status, amount, balance_amount" in executed_sql
    assert "UPDATE payments" not in executed_sql
    assert "INSERT INTO audit_logs" not in executed_sql
    assert session.committed is False
    assert session.rolled_back is True
    assert session.closed is True
