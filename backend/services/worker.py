import os

from sqlalchemy import text

from utils.database import SessionLocal

WORKER_SECRET = os.getenv("WORKER_SECRET", "")


def authenticate_worker(authorization: str | None) -> None:
    if not WORKER_SECRET:
        raise PermissionError("WORKER_SECRET이 설정되지 않았습니다.")
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionError("Worker 인증이 필요합니다.")
    if authorization[7:] != WORKER_SECRET:
        raise PermissionError("유효하지 않은 Worker 토큰입니다.")


def get_next_job() -> dict | None:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT aj.job_id, aj.upload_id, aj.job_type, aj.queue_position,
                       u.stored_path, u.original_filename, u.media_type,
                       u.content_type, u.file_size
                FROM analysis_jobs aj
                JOIN uploads u ON u.upload_id = aj.upload_id
                WHERE aj.status = 'queued'
                ORDER BY aj.queue_position ASC NULLS LAST, aj.created_at ASC
                LIMIT 1
            """)
        ).fetchone()

        if not row:
            return None

        m = row._mapping
        return {
            "job_id": str(m["job_id"]),
            "upload_id": str(m["upload_id"]),
            "job_type": m["job_type"],
            "queue_position": m["queue_position"],
            "file_path": m["stored_path"],
            "original_filename": m["original_filename"],
            "media_type": m["media_type"],
            "content_type": m["content_type"],
            "file_size": m["file_size"],
        }
    finally:
        db.close()


def accept_job(job_id: str) -> dict:
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                UPDATE analysis_jobs
                SET status = 'processing',
                    started_at = now(),
                    updated_at = now()
                WHERE job_id = :job_id AND status = 'queued'
                RETURNING job_id, status
            """),
            {"job_id": job_id},
        ).fetchone()

        if not result:
            existing = db.execute(
                text("SELECT status FROM analysis_jobs WHERE job_id = :job_id"),
                {"job_id": job_id},
            ).fetchone()
            if not existing:
                raise ValueError("분석 작업을 찾을 수 없습니다.")
            db.rollback()
            return {
                "job_id": job_id,
                "status": existing._mapping["status"],
                "message": "이미 처리 중이거나 완료된 작업입니다.",
            }

        db.commit()
        return {"job_id": job_id, "status": "processing"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_upload_file_info(upload_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT stored_path, original_filename, content_type, status
                FROM uploads
                WHERE upload_id = :upload_id
            """),
            {"upload_id": upload_id},
        ).fetchone()

        if not row:
            raise ValueError("업로드를 찾을 수 없습니다.")

        m = row._mapping
        if m["status"] != "uploaded":
            raise ValueError(f"파일이 아직 준비되지 않았습니다. (status: {m['status']})")

        return {
            "stored_path": m["stored_path"],
            "original_filename": m["original_filename"],
            "content_type": m["content_type"],
        }
    finally:
        db.close()


def update_job_progress(
    job_id: str,
    worker_id: str | None,
    stage_name: str,
    stage_progress: int,
    total_progress: int,
    message: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE analysis_jobs
                SET current_stage = :stage_name,
                    stage_progress = :stage_progress,
                    total_progress = :total_progress,
                    message = :message,
                    updated_at = now()
                WHERE job_id = :job_id
            """),
            {
                "job_id": job_id,
                "stage_name": stage_name,
                "stage_progress": stage_progress,
                "total_progress": total_progress,
                "message": message,
            },
        )

        db.execute(
            text("""
                INSERT INTO job_stage_logs
                    (job_id, stage_name, stage_progress, total_progress, status, message)
                VALUES
                    (:job_id, :stage_name, :stage_progress, :total_progress, 'running', :message)
            """),
            {
                "job_id": job_id,
                "stage_name": stage_name,
                "stage_progress": stage_progress,
                "total_progress": total_progress,
                "message": message,
            },
        )

        db.commit()
        return {
            "job_id": job_id,
            "stage_name": stage_name,
            "stage_progress": stage_progress,
            "total_progress": total_progress,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def complete_job(
    job_id: str,
    worker_id: str | None,
    detection_count: int = 0,
) -> dict:
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE analysis_jobs
                SET status = 'completed',
                    completed_at = now(),
                    total_progress = 100,
                    stage_progress = 100,
                    detection_count = :detection_count,
                    updated_at = now()
                WHERE job_id = :job_id
            """),
            {"job_id": job_id, "detection_count": detection_count},
        )

        db.execute(
            text("""
                INSERT INTO job_stage_logs
                    (job_id, stage_name, stage_progress, total_progress, status, message)
                VALUES
                    (:job_id, 'completed', 100, 100, 'completed', '분석이 완료되었습니다.')
            """),
            {"job_id": job_id},
        )

        db.commit()
        return {"job_id": job_id, "status": "completed"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def fail_job(
    job_id: str,
    worker_id: str | None,
    error_code: str | None,
    error_message: str | None,
) -> dict:
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE analysis_jobs
                SET status = 'failed',
                    error_code = :error_code,
                    error_message = :error_message,
                    updated_at = now()
                WHERE job_id = :job_id
            """),
            {
                "job_id": job_id,
                "error_code": error_code,
                "error_message": error_message,
            },
        )

        db.execute(
            text("""
                INSERT INTO job_stage_logs
                    (job_id, stage_name, stage_progress, total_progress, status, message)
                VALUES
                    (:job_id, 'failed', 0, 0, 'failed', :error_message)
            """),
            {"job_id": job_id, "error_message": error_message},
        )

        db.commit()
        return {"job_id": job_id, "status": "failed"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def record_heartbeat(
    job_id: str,
    worker_id: str | None,
    worker_type: str,
    public_endpoint: str | None,
    current_stage: str | None,
    progress: int,
    message: str | None,
) -> dict:
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO job_worker_heartbeats
                    (job_id, worker_id, worker_type, public_endpoint,
                     current_stage, progress, message)
                VALUES
                    (:job_id, :worker_id, :worker_type, :public_endpoint,
                     :current_stage, :progress, :message)
            """),
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "worker_type": worker_type,
                "public_endpoint": public_endpoint,
                "current_stage": current_stage,
                "progress": progress,
                "message": message,
            },
        )
        db.commit()
        return {"job_id": job_id, "recorded": True}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
