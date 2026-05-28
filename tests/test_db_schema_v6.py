from pathlib import Path
import re


SQL_PATH = Path("docker/database/init/0_init_table_v6.sql")


def _sql() -> str:
    return SQL_PATH.read_text(encoding="utf-8", errors="ignore")


def _create_block(sql: str, table: str) -> str:
    match = re.search(
        rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"{table} create block not found"
    return match.group(1).lower()


def test_v6_removes_v5_upload_tables():
    sql = _sql().lower()

    assert "drop table if exists uploaded_files" in sql
    assert "drop table if exists upload_sessions" in sql
    assert "create table if not exists uploaded_files" not in sql
    assert "create table if not exists upload_sessions" not in sql


def test_analysis_jobs_matches_v6_progress_contract():
    block = _create_block(_sql(), "analysis_jobs")

    assert "upload_id uuid references uploads(upload_id) on delete set null" in block
    assert "job_type varchar(30)" in block
    assert "current_stage varchar(50)" in block
    assert "stage_progress integer" in block
    assert "total_progress integer" in block
    assert "queue_position integer" in block
    assert "eta_seconds integer" in block
    assert "cancel_requested boolean" in block
    assert "progress_percent" not in block

    sql = _sql().lower()
    assert "whitelist_scan" in sql
    assert "white_list_scan" not in sql


def test_job_stage_logs_uses_v6_column_names():
    block = _create_block(_sql(), "job_stage_logs")

    assert "stage_log_id uuid" in block
    assert "job_stage_log_id" not in block
    assert "eta_seconds integer" in block
    assert "queue_position integer" in block
    assert "source varchar(50)" in block
    assert "payload jsonb" not in block


def test_worker_heartbeats_use_v6_column_names():
    block = _create_block(_sql(), "job_worker_heartbeats")

    assert "ngrok_url text" in block
    assert "progress_percent integer" in block
    assert "public_endpoint" not in block
    assert re.search(r"\bprogress integer\b", block) is None


def test_queue_history_uses_v6_column_names():
    block = _create_block(_sql(), "job_queue_history")

    assert "entered_position integer" in block
    assert "dequeued_position integer" in block
    assert "status varchar(30)" in block
    assert "message text" in block
    assert "queue_position" not in block
    assert "event_type" not in block
