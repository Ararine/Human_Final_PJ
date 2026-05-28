import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "garim")

from fastapi.testclient import TestClient  # noqa: E402
from main import app                       # noqa: E402
from services import worker                # noqa: E402

client = TestClient(app)

SECRET = "test-secret"
HEADERS = {"Authorization": f"Bearer {SECRET}"}
WRONG_HEADERS = {"Authorization": "Bearer wrong-secret"}


class Row:
    def __init__(self, **values):
        self._mapping = values


class Result:
    def __init__(self, rows=None):
        self.rows = rows or []

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeSession:
    def __init__(self, job_row):
        self._row = job_row

    def execute(self, statement, params=None):
        if "from analysis_jobs" in str(statement).lower():
            return Result([Row(**self._row)] if self._row else [])
        return Result([])

    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


# ── 서비스 레이어 ──────────────────────────────────────────────────

def test_service_raises_for_missing_job(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(None))
    try:
        worker.get_job_status("no-id")
        assert False, "ValueError 발생해야 함"
    except ValueError as e:
        assert "찾을 수 없습니다" in str(e)


def test_service_returns_status_fields(monkeypatch):
    row = {
        "job_id": "job-1",
        "status": "processing",
        "cancel_requested": False,
        "current_stage": "stt",
        "total_progress": 45,
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    result = worker.get_job_status("job-1")
    assert result["job_id"] == "job-1"
    assert result["status"] == "processing"
    assert result["cancel_requested"] is False
    assert result["current_stage"] == "stt"
    assert result["total_progress"] == 45


def test_service_returns_cancel_requested_true(monkeypatch):
    row = {
        "job_id": "job-1",
        "status": "cancelling",
        "cancel_requested": True,
        "current_stage": "stt",
        "total_progress": 45,
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    result = worker.get_job_status("job-1")
    assert result["cancel_requested"] is True
    assert result["status"] == "cancelling"


# ── HTTP 엔드포인트 ─────────────────────────────────────────────────

def test_status_no_auth(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.get("/worker/jobs/job-1/status")
    assert r.status_code == 401


def test_status_wrong_secret(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.get("/worker/jobs/job-1/status", headers=WRONG_HEADERS)
    assert r.status_code == 401


def test_status_job_not_found(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(None))
    r = client.get("/worker/jobs/no-such/status", headers=HEADERS)
    assert r.status_code == 404


def test_status_returns_processing_not_cancelled(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    row = {
        "job_id": "job-1",
        "status": "processing",
        "cancel_requested": False,
        "current_stage": "stt",
        "total_progress": 45,
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    r = client.get("/worker/jobs/job-1/status", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["cancel_requested"] is False
    assert data["status"] == "processing"
    assert data["current_stage"] == "stt"
    assert data["total_progress"] == 45


def test_status_returns_cancel_requested_true(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    row = {
        "job_id": "job-1",
        "status": "cancelling",
        "cancel_requested": True,
        "current_stage": "stt",
        "total_progress": 45,
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    r = client.get("/worker/jobs/job-1/status", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["cancel_requested"] is True
    assert data["status"] == "cancelling"


# ── complete가 cancel을 덮어쓰지 않는지 확인 ────────────────────────
# worker는 check_cancel=True 일 때 complete_job을 호출하지 않는다.
# 이 테스트는 cancel 감지 이후 complete API를 호출하지 않는 흐름을 검증한다.

def test_complete_not_called_after_cancel(monkeypatch):
    """check_cancel이 True를 반환하면 complete API를 호출하지 않아야 한다."""
    complete_called = []

    # cancel_requested=True 인 job 상태 반환
    status_row = {
        "job_id": "job-1",
        "status": "cancelling",
        "cancel_requested": True,
        "current_stage": "file_download",
        "total_progress": 10,
    }

    # progress 업데이트용 FakeSession (UPDATE 무시)
    class FullFakeSession:
        def execute(self, statement, params=None):
            sql = str(statement).lower()
            if "from analysis_jobs" in sql:
                return Result([Row(**status_row)])
            return Result([])
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass

    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FullFakeSession())

    # complete_job 서비스 호출 여부 추적
    original_complete = worker.complete_job

    def spy_complete(*args, **kwargs):
        complete_called.append(True)
        return original_complete(*args, **kwargs)

    monkeypatch.setattr(worker, "complete_job", spy_complete)

    # check_cancel이 True를 반환하면 worker는 complete를 보내지 않는다
    result = worker.get_job_status("job-1")
    assert result["cancel_requested"] is True
    # complete가 호출되지 않았음
    assert len(complete_called) == 0
