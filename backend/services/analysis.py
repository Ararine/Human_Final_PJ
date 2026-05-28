from uuid import uuid4

from sqlalchemy import text

from utils.database import SessionLocal


def create_analysis_job(upload_id: str, user_id: str) -> dict:
    db = SessionLocal()
    try:
        upload = db.execute(
            text("SELECT user_id, status FROM uploads WHERE upload_id = :upload_id"),
            {"upload_id": upload_id},
        ).fetchone()

        if not upload:
            raise ValueError("업로드를 찾을 수 없습니다.")

        um = upload._mapping
        if str(um["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")
        if um["status"] != "uploaded":
            raise ValueError(f"분석 요청할 수 없는 업로드 상태입니다: {um['status']}")

        existing = db.execute(
            text("""
                SELECT job_id, status FROM analysis_jobs
                WHERE upload_id = :upload_id
                  AND status NOT IN ('failed', 'cancelled')
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"upload_id": upload_id},
        ).fetchone()

        if existing:
            em = existing._mapping
            return {
                "job_id": str(em["job_id"]),
                "upload_id": upload_id,
                "status": em["status"],
                "already_exists": True,
                "message": "이미 처리 중인 분석 작업이 있습니다.",
            }

        queue_count = db.execute(
            text("SELECT COUNT(*) FROM analysis_jobs WHERE status = 'queued'")
        ).scalar() or 0

        job_id = str(uuid4())
        message = "분석 작업이 대기열에 등록되었습니다."
        db.execute(
            text("""
                INSERT INTO analysis_jobs (
                    job_id, upload_id, user_id, status, job_type,
                    current_stage, queue_position, total_progress, stage_progress, message
                ) VALUES (
                    :job_id, :upload_id, :user_id, 'queued', 'analysis',
                    :current_stage, :queue_position, :total_progress, :stage_progress, :message
                )
            """),
            {
                "job_id": job_id,
                "upload_id": upload_id,
                "user_id": user_id,
                "current_stage": "queued",
                "queue_position": queue_count + 1,
                "total_progress": 0,
                "stage_progress": 0,
                "message": message,
            },
        )
        db.execute(
            text("""
                INSERT INTO job_queue_history
                    (job_id, queue_name, priority, entered_position, status, message)
                VALUES
                    (:job_id, :queue_name, :priority, :entered_position, :status, :message)
            """),
            {
                "job_id": job_id,
                "queue_name": "default",
                "priority": 0,
                "entered_position": queue_count + 1,
                "status": "entered",
                "message": message,
            },
        )
        db.commit()

        return {
            "job_id": job_id,
            "upload_id": upload_id,
            "status": "queued",
            "queue_position": queue_count + 1,
            "message": "분석 작업이 대기열에 등록되었습니다.",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def cancel_analysis_job(job_id: str, user_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT user_id, status
                FROM analysis_jobs
                WHERE job_id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()

        if not row:
            raise ValueError("분석 작업을 찾을 수 없습니다.")

        m = row._mapping
        if str(m["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")
        if m["status"] in ("completed", "failed", "cancelled"):
            return {"job_id": job_id, "status": m["status"], "cancel_requested": False}

        message = "작업 취소가 요청되었습니다."
        updated = db.execute(
            text("""
                UPDATE analysis_jobs
                SET cancel_requested = true,
                    status = 'cancelling',
                    message = :message,
                    updated_at = now()
                WHERE job_id = :job_id
                RETURNING job_id, status
            """),
            {"job_id": job_id, "message": message},
        ).fetchone()

        db.execute(
            text("""
                INSERT INTO job_stage_logs
                    (job_id, stage_name, stage_progress, total_progress, status, message, source)
                VALUES
                    (:job_id, 'cancel_requested', 0, 0, 'cancelling', :message, 'backend')
            """),
            {"job_id": job_id, "message": message},
        )

        db.commit()
        return {
            "job_id": str(updated._mapping["job_id"]) if updated else job_id,
            "status": updated._mapping["status"] if updated else "cancelling",
            "cancel_requested": True,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_analysis_job(job_id: str, user_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT job_id, upload_id, user_id, status, job_type,
                       total_progress, current_stage, stage_progress,
                       queue_position, eta_seconds, message,
                       cancel_requested, started_at, completed_at,
                       error_message, error_code
                FROM analysis_jobs
                WHERE job_id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()

        if not row:
            raise ValueError("분석 작업을 찾을 수 없습니다.")

        m = row._mapping
        if str(m["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")

        logs = db.execute(
            text("""
                SELECT stage_name, stage_progress, total_progress, status, message,
                       eta_seconds, queue_position, source, created_at
                FROM job_stage_logs
                WHERE job_id = :job_id
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"job_id": job_id},
        ).fetchall()

        return {
            "job_id": str(m["job_id"]),
            "upload_id": str(m["upload_id"]),
            "status": m["status"],
            "job_type": m["job_type"],
            "total_progress": m["total_progress"],
            "current_stage": m["current_stage"],
            "stage_progress": m["stage_progress"],
            "queue_position": m["queue_position"],
            "eta_seconds": m["eta_seconds"],
            "message": m["message"],
            "cancel_requested": m["cancel_requested"],
            "started_at": m["started_at"].isoformat() if m["started_at"] else None,
            "completed_at": m["completed_at"].isoformat() if m["completed_at"] else None,
            "error_message": m["error_message"],
            "error_code": m["error_code"],
            "stage_logs": [
                {
                    "stage_name": l._mapping["stage_name"],
                    "stage_progress": l._mapping["stage_progress"],
                    "total_progress": l._mapping["total_progress"],
                    "status": l._mapping["status"],
                    "message": l._mapping["message"],
                    "eta_seconds": l._mapping["eta_seconds"],
                    "queue_position": l._mapping["queue_position"],
                    "source": l._mapping["source"],
                    "created_at": l._mapping["created_at"].isoformat() if l._mapping["created_at"] else None,
                }
                for l in logs
            ],
        }
    finally:
        db.close()
