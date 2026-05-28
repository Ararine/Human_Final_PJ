import os
import sys
import tempfile
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
    def __init__(self, upload_row):
        self._row = upload_row

    def execute(self, statement, params=None):
        if "from uploads" in str(statement).lower():
            return Result([Row(**self._row)] if self._row else [])
        return Result([])

    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


# ── 서비스 레이어 ──────────────────────────────────────────────────

def test_service_raises_for_missing_upload(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(None))
    try:
        worker.get_upload_file_info("no-id")
        assert False, "ValueError 발생해야 함"
    except ValueError as e:
        assert "찾을 수 없습니다" in str(e)


def test_service_raises_when_not_uploaded(monkeypatch):
    row = {
        "stored_path": "/tmp/x.mp4",
        "original_filename": "x.mp4",
        "content_type": "video/mp4",
        "status": "uploading",
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    try:
        worker.get_upload_file_info("some-id")
        assert False, "ValueError 발생해야 함"
    except ValueError as e:
        assert "준비되지 않았습니다" in str(e)


def test_service_returns_file_info(monkeypatch):
    row = {
        "stored_path": "/tmp/v.mp4",
        "original_filename": "video.mp4",
        "content_type": "video/mp4",
        "status": "uploaded",
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    info = worker.get_upload_file_info("some-id")
    assert info["stored_path"] == "/tmp/v.mp4"
    assert info["original_filename"] == "video.mp4"
    assert info["content_type"] == "video/mp4"


# ── /download 엔드포인트 ───────────────────────────────────────────

def test_download_no_auth(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.get("/worker/files/some-id/download")
    assert r.status_code == 401


def test_download_wrong_secret(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    r = client.get("/worker/files/some-id/download", headers=WRONG_HEADERS)
    assert r.status_code == 401


def test_download_upload_not_found(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(None))
    r = client.get("/worker/files/no-such/download", headers=HEADERS)
    assert r.status_code == 404


def test_download_upload_not_ready(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    row = {
        "stored_path": "/tmp/x.mp4",
        "original_filename": "x.mp4",
        "content_type": "video/mp4",
        "status": "uploading",
    }
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
    r = client.get("/worker/files/upload-1/download", headers=HEADERS)
    assert r.status_code == 404


def test_download_returns_file_binary(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake-video-bytes")
        tmp_path = f.name
    try:
        row = {
            "stored_path": tmp_path,
            "original_filename": "video.mp4",
            "content_type": "video/mp4",
            "status": "uploaded",
        }
        monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
        r = client.get("/worker/files/upload-1/download", headers=HEADERS)
        assert r.status_code == 200
        assert r.content == b"fake-video-bytes"
        assert "attachment" in r.headers.get("content-disposition", "")
    finally:
        os.unlink(tmp_path)


# ── 기존 /files/{upload_id} 엔드포인트 유지 확인 ────────────────────

def test_existing_get_file_endpoint_unchanged(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", SECRET)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"existing-bytes")
        tmp_path = f.name
    try:
        row = {
            "stored_path": tmp_path,
            "original_filename": "video.mp4",
            "content_type": "video/mp4",
            "status": "uploaded",
        }
        monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(row))
        r = client.get("/worker/files/upload-1", headers=HEADERS)
        assert r.status_code == 200
        assert r.content == b"existing-bytes"
    finally:
        os.unlink(tmp_path)
