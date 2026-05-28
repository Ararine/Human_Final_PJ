import os
import sys
import uuid
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

JOB_ID = "job-results-1"
USER_ID = str(uuid.uuid4())
ARTIFACT_ID = str(uuid.uuid4())
DETECTION_ID = str(uuid.uuid4())


class Row:
    def __init__(self, **values):
        self._mapping = values


class Result:
    def __init__(self, rows=None):
        self.rows = rows or []

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeSessionJobNotFound:
    def execute(self, statement, params=None):
        sql = str(statement).lower()
        if "from analysis_jobs" in sql:
            return Result([])
        return Result([])
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


class FakeSessionForSTT:
    def execute(self, statement, params=None):
        sql = str(statement).lower()
        if "from analysis_jobs" in sql:
            return Result([Row(user_id=USER_ID)])
        if "into analysis_artifacts" in sql:
            return Result([Row(artifact_id=ARTIFACT_ID)])
        return Result([])
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


class FakeSessionForPII:
    def execute(self, statement, params=None):
        sql = str(statement).lower()
        if "into detections" in sql:
            return Result([Row(detection_id=DETECTION_ID)])
        return Result([])
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


class FakeSessionForArtifact:
    def execute(self, statement, params=None):
        sql = str(statement).lower()
        if "from analysis_jobs" in sql:
            return Result([Row(user_id=USER_ID)])
        if "into analysis_artifacts" in sql:
            return Result([Row(artifact_id=ARTIFACT_ID)])
        return Result([])
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


# ── 서비스 레이어 ──────────────────────────────────────────────────

def test_service_save_stt_raises_for_missing_job(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionJobNotFound())
    try:
        worker.save_stt_result(JOB_ID, "ko", "안녕하세요", 3)
        assert False, "ValueError 발생해야 함"
    except ValueError as e:
        assert "찾을 수 없습니다" in str(e)


def test_service_save_stt_returns_artifact_info(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForSTT())
    result = worker.save_stt_result(JOB_ID, "ko", "안녕하세요", 3)
    assert result["artifact_id"] == ARTIFACT_ID
    assert result["artifact_type"] == "stt_transcript"
    assert result["job_id"] == JOB_ID


def test_service_save_pii_empty_segments(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForPII())
    result = worker.save_pii_result(JOB_ID, [])
    assert result["saved_count"] == 0
    assert result["detection_ids"] == []


def test_service_save_pii_returns_detection_ids(monkeypatch):
    segments = [
        {"start_time_sec": 1.0, "end_time_sec": 2.5,
         "detected_text": "홍길동", "label": "name", "confidence": 0.9},
    ]
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForPII())
    result = worker.save_pii_result(JOB_ID, segments)
    assert result["saved_count"] == 1
    assert len(result["detection_ids"]) == 1
    assert result["detection_ids"][0] == DETECTION_ID


def test_service_save_artifact_raises_for_missing_job(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionJobNotFound())
    try:
        worker.save_artifact(JOB_ID, "beep_output", "/content/out.mp4")
        assert False, "ValueError 발생해야 함"
    except ValueError as e:
        assert "찾을 수 없습니다" in str(e)


def test_service_save_artifact_returns_artifact_info(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForArtifact())
    result = worker.save_artifact(JOB_ID, "beep_output", "/content/out.mp4", "video/mp4")
    assert result["artifact_id"] == ARTIFACT_ID
    assert result["artifact_type"] == "beep_output"
    assert result["job_id"] == JOB_ID


# ── HTTP 엔드포인트 ─────────────────────────────────────────────────

def test_stt_no_auth(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.post(f"/worker/jobs/{JOB_ID}/results/stt",
                    json={"full_text": "hi", "segment_count": 1})
    assert r.status_code == 401


def test_stt_wrong_secret(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.post(f"/worker/jobs/{JOB_ID}/results/stt",
                    headers=WRONG_HEADERS, json={"full_text": "hi"})
    assert r.status_code == 401


def test_stt_job_not_found(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionJobNotFound())
    r = client.post(f"/worker/jobs/{JOB_ID}/results/stt",
                    headers=HEADERS, json={"full_text": "hi"})
    assert r.status_code == 404


def test_stt_success(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForSTT())
    r = client.post(
        f"/worker/jobs/{JOB_ID}/results/stt",
        headers=HEADERS,
        json={"language": "ko", "full_text": "안녕하세요", "segment_count": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["artifact_id"] == ARTIFACT_ID
    assert data["artifact_type"] == "stt_transcript"


def test_pii_no_auth(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.post(f"/worker/jobs/{JOB_ID}/results/pii", json={"pii_segments": []})
    assert r.status_code == 401


def test_pii_success_empty(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForPII())
    r = client.post(f"/worker/jobs/{JOB_ID}/results/pii",
                    headers=HEADERS, json={"pii_segments": []})
    assert r.status_code == 200
    assert r.json()["saved_count"] == 0


def test_pii_success_with_segments(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForPII())
    r = client.post(
        f"/worker/jobs/{JOB_ID}/results/pii",
        headers=HEADERS,
        json={"pii_segments": [
            {"start_time_sec": 1.0, "end_time_sec": 2.5,
             "detected_text": "홍길동", "label": "name"}
        ]},
    )
    assert r.status_code == 200
    assert r.json()["saved_count"] == 1


def test_artifact_no_auth(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.post(f"/worker/jobs/{JOB_ID}/results/artifact",
                    json={"artifact_type": "beep_output", "stored_path": "/out.mp4"})
    assert r.status_code == 401


def test_artifact_job_not_found(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionJobNotFound())
    r = client.post(f"/worker/jobs/{JOB_ID}/results/artifact",
                    headers=HEADERS,
                    json={"artifact_type": "beep_output", "stored_path": "/out.mp4"})
    assert r.status_code == 404


def test_artifact_success(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSessionForArtifact())
    r = client.post(
        f"/worker/jobs/{JOB_ID}/results/artifact",
        headers=HEADERS,
        json={"artifact_type": "beep_output", "stored_path": "/content/out.mp4",
              "content_type": "video/mp4"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["artifact_id"] == ARTIFACT_ID
    assert data["artifact_type"] == "beep_output"
