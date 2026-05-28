import hashlib
import io
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "garim")

from services import uploads  # noqa: E402


class Row:
    def __init__(self, **values):
        self._mapping = values


class Result:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._scalar_value


class FakeUploadFile:
    def __init__(self, data):
        self.file = io.BytesIO(data)


class FakeSession:
    def __init__(self, state):
        self.state = state
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, params=None):
        sql = str(statement).lower()
        params = params or {}
        upload_id = params.get("upload_id")

        if "select user_id, status, total_chunks" in sql and "from uploads" in sql:
            upload = self.state["uploads"].get(upload_id)
            return Result([Row(**upload)] if upload else [])

        if "select upload_chunk_id" in sql and "from upload_chunks" in sql:
            key = (upload_id, params["chunk_index"])
            chunk = self.state["chunks"].get(key)
            return Result([Row(upload_chunk_id=chunk["upload_chunk_id"])] if chunk else [])

        if "insert into upload_chunks" in sql:
            key = (upload_id, params["chunk_index"])
            if key not in self.state["chunks"]:
                self.state["chunks"][key] = {
                    "upload_chunk_id": f"chunk-{params['chunk_index']}",
                    "upload_id": upload_id,
                    "chunk_index": params["chunk_index"],
                    "chunk_size": params["chunk_size"],
                    "chunk_hash": params["chunk_hash"],
                    "storage_path": params["storage_path"],
                    "status": "uploaded",
                }
                return Result(scalar_value=1)
            return Result(scalar_value=0)

        if "set uploaded_chunks = uploaded_chunks + 1" in sql:
            self.state["uploads"][upload_id]["uploaded_chunks"] += 1
            self.state["uploads"][upload_id]["status"] = "uploading"
            return Result()

        if "set status = :status" in sql:
            self.state["uploads"][upload_id]["status"] = params["status"]
            return Result()

        if "set status = 'expired'" in sql:
            self.state["uploads"][upload_id]["status"] = "expired"
            return Result()

        if "set status = 'cancelled'" in sql:
            self.state["uploads"][upload_id]["status"] = "cancelled"
            return Result()

        if "select chunk_index from upload_chunks" in sql:
            rows = [
                Row(chunk_index=chunk["chunk_index"])
                for (chunk_upload_id, _), chunk in self.state["chunks"].items()
                if chunk_upload_id == upload_id
            ]
            return Result(rows)

        raise AssertionError(f"Unexpected SQL: {statement}")

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def install_fake_session(monkeypatch, tmp_path, expires_at=None):
    upload_id = "upload-1"
    state = {
        "uploads": {
            upload_id: {
                "user_id": "user-1",
                "status": "initialized",
                "total_chunks": 2,
                "uploaded_chunks": 0,
                "temp_dir_path": str(tmp_path / "temp" / upload_id),
                "expires_at": expires_at or datetime.now(timezone.utc) + timedelta(hours=1),
                "file_hash": None,
                "stored_path": str(tmp_path / "final.bin"),
            }
        },
        "chunks": {},
    }
    monkeypatch.setattr(uploads, "SessionLocal", lambda: FakeSession(state))
    return state


def test_duplicate_chunk_does_not_increment_uploaded_chunks(monkeypatch, tmp_path):
    state = install_fake_session(monkeypatch, tmp_path)
    data = b"hello"
    chunk_hash = hashlib.sha256(data).hexdigest()

    first = uploads.save_chunk("upload-1", "user-1", 0, FakeUploadFile(data), chunk_hash)
    second = uploads.save_chunk("upload-1", "user-1", 0, FakeUploadFile(data), chunk_hash)

    assert first["status"] == "uploaded"
    assert second["status"] == "already_uploaded"
    assert state["uploads"]["upload-1"]["uploaded_chunks"] == 1
    assert len(state["chunks"]) == 1


def test_chunk_hash_mismatch_rejects_upload(monkeypatch, tmp_path):
    state = install_fake_session(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="chunk hash mismatch"):
        uploads.save_chunk("upload-1", "user-1", 0, FakeUploadFile(b"hello"), "bad-hash")

    assert state["uploads"]["upload-1"]["uploaded_chunks"] == 0
    assert state["chunks"] == {}


def test_expired_upload_rejects_chunk_and_marks_expired(monkeypatch, tmp_path):
    state = install_fake_session(
        monkeypatch,
        tmp_path,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="upload expired"):
        uploads.save_chunk("upload-1", "user-1", 0, FakeUploadFile(b"hello"))

    assert state["uploads"]["upload-1"]["status"] == "expired"


def test_expired_upload_rejects_complete_and_marks_expired(monkeypatch, tmp_path):
    state = install_fake_session(
        monkeypatch,
        tmp_path,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    state["uploads"]["upload-1"]["status"] = "uploading"
    state["uploads"]["upload-1"]["uploaded_chunks"] = 2

    with pytest.raises(ValueError, match="upload expired"):
        uploads.complete_upload("upload-1", "user-1")

    assert state["uploads"]["upload-1"]["status"] == "expired"


def test_status_reports_missing_chunks(monkeypatch, tmp_path):
    state = install_fake_session(monkeypatch, tmp_path)
    data = b"hello"
    chunk_hash = hashlib.sha256(data).hexdigest()
    uploads.save_chunk("upload-1", "user-1", 0, FakeUploadFile(data), chunk_hash)

    status = uploads.get_upload_status("upload-1", "user-1")

    assert status["uploaded_chunks"] == 1
    assert status["progress"] == 50
    assert status["missing_chunks"] == [1]
