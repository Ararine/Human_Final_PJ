import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "garim")

from services import analysis, worker  # noqa: E402


class Row:
    def __init__(self, **values):
        self._mapping = values


class Result:
    def __init__(self, rows=None, scalar_value=None):
        self.rows = rows or []
        self.scalar_value = scalar_value

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def scalar(self):
        return self.scalar_value


class FakeSession:
    def __init__(self, state):
        self.state = state

    def execute(self, statement, params=None):
        sql = str(statement).lower()
        params = params or {}

        if "select user_id, status from uploads" in sql:
            upload = self.state["uploads"].get(params["upload_id"])
            return Result([Row(**upload)] if upload else [])

        if "select user_id, status" in sql and "from analysis_jobs" in sql:
            job = self.state["jobs"].get(params["job_id"])
            return Result([Row(user_id=job["user_id"], status=job["status"])] if job else [])

        if "select job_id, status from analysis_jobs" in sql:
            jobs = [
                Row(job_id=job_id, status=job["status"])
                for job_id, job in self.state["jobs"].items()
                if job["upload_id"] == params["upload_id"] and job["status"] not in ("failed", "cancelled")
            ]
            return Result(jobs[:1])

        if "select count(*) from analysis_jobs where status = 'queued'" in sql:
            return Result(scalar_value=sum(1 for job in self.state["jobs"].values() if job["status"] == "queued"))

        if "insert into analysis_jobs" in sql:
            self.state["jobs"][params["job_id"]] = {
                "job_id": params["job_id"],
                "upload_id": params["upload_id"],
                "user_id": params["user_id"],
                "status": "queued",
                "job_type": "analysis",
                "current_stage": params.get("current_stage"),
                "stage_progress": params.get("stage_progress", 0),
                "total_progress": params.get("total_progress", 0),
                "queue_position": params["queue_position"],
                "eta_seconds": params.get("eta_seconds"),
                "message": params.get("message"),
                "cancel_requested": False,
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "error_code": None,
            }
            return Result()

        if "insert into job_queue_history" in sql:
            self.state["queue_history"].append(dict(params))
            return Result()

        if "update analysis_jobs" in sql and "cancel_requested = true" in sql:
            job = self.state["jobs"][params["job_id"]]
            job["cancel_requested"] = True
            job["status"] = "cancelling"
            job["message"] = params.get("message")
            return Result([Row(job_id=params["job_id"], status="cancelling")])

        if "update analysis_jobs" in sql and "current_stage = :stage_name" in sql:
            job = self.state["jobs"][params["job_id"]]
            job["current_stage"] = params["stage_name"]
            job["stage_progress"] = params["stage_progress"]
            job["total_progress"] = params["total_progress"]
            job["message"] = params["message"]
            return Result()

        if "insert into job_stage_logs" in sql:
            log = dict(params)
            log.setdefault("stage_name", "cancel_requested" if "cancel_requested" in sql else params.get("stage_name"))
            log.setdefault("stage_progress", 0)
            log.setdefault("total_progress", 0)
            log.setdefault("status", "cancelling" if "cancelling" in sql else "processing")
            log.setdefault("source", "backend" if "'backend'" in sql else "worker")
            log.setdefault("eta_seconds", None)
            log.setdefault("queue_position", None)
            log.setdefault("created_at", datetime(2026, 1, 1, 12, 0, 0))
            self.state["stage_logs"].append(log)
            return Result()

        if "select job_id, upload_id, user_id, status, job_type" in sql:
            job = self.state["jobs"].get(params["job_id"])
            return Result([Row(**job)] if job else [])

        if "from job_stage_logs" in sql:
            logs = [Row(**log) for log in reversed(self.state["stage_logs"]) if log["job_id"] == params["job_id"]]
            return Result(logs[:10])

        if "from analysis_jobs aj" in sql:
            self.state["last_next_job_sql"] = sql
            return Result([])

        raise AssertionError(f"Unexpected SQL: {statement}")

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def install_fake_sessions(monkeypatch):
    state = {
        "uploads": {"upload-1": {"user_id": "user-1", "status": "uploaded"}},
        "jobs": {},
        "stage_logs": [],
        "queue_history": [],
        "last_next_job_sql": "",
    }
    monkeypatch.setattr(analysis, "SessionLocal", lambda: FakeSession(state))
    monkeypatch.setattr(worker, "SessionLocal", lambda: FakeSession(state))
    monkeypatch.setattr(analysis, "uuid4", lambda: "job-1")
    return state


def test_create_analysis_job_writes_v6_fields_and_queue_history(monkeypatch):
    state = install_fake_sessions(monkeypatch)

    result = analysis.create_analysis_job("upload-1", "user-1")

    job = state["jobs"]["job-1"]
    assert result["job_id"] == "job-1"
    assert job["current_stage"] == "queued"
    assert job["stage_progress"] == 0
    assert job["total_progress"] == 0
    assert job["message"]
    assert state["queue_history"] == [
        {
            "job_id": "job-1",
            "queue_name": "default",
            "priority": 0,
            "entered_position": 1,
            "status": "entered",
            "message": job["message"],
        }
    ]


def test_worker_progress_updates_job_and_stage_log_visible_to_polling(monkeypatch):
    state = install_fake_sessions(monkeypatch)
    analysis.create_analysis_job("upload-1", "user-1")

    worker.update_job_progress("job-1", "colab-1", "visual_detection", 25, 10, "detecting")
    result = analysis.get_analysis_job("job-1", "user-1")

    assert result["current_stage"] == "visual_detection"
    assert result["stage_progress"] == 25
    assert result["total_progress"] == 10
    assert result["message"] == "detecting"
    assert result["cancel_requested"] is False
    assert result["stage_logs"][0]["source"] == "worker"
    assert result["stage_logs"][0]["message"] == "detecting"


def test_cancel_request_is_persisted_and_workers_skip_cancelled_jobs(monkeypatch):
    state = install_fake_sessions(monkeypatch)
    analysis.create_analysis_job("upload-1", "user-1")

    cancelled = analysis.cancel_analysis_job("job-1", "user-1")
    result = analysis.get_analysis_job("job-1", "user-1")
    worker.get_next_job()

    assert cancelled["status"] == "cancelling"
    assert result["cancel_requested"] is True
    assert result["status"] == "cancelling"
    assert "cancel_requested = false" in state["last_next_job_sql"]
