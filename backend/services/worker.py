import json
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
                  AND aj.cancel_requested = false
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
                    current_stage = 'queued',
                    message = '작업자가 분석 작업을 시작했습니다.',
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

        db.execute(
            text("""
                INSERT INTO job_queue_history
                    (job_id, queue_name, priority, dequeued_position, status, message, dequeued_at)
                VALUES
                    (:job_id, 'default', 0, 0, 'dequeued', :message, now())
            """),
            {"job_id": job_id, "message": "작업자가 분석 작업을 가져갔습니다."},
        )

        db.execute(
            text("""
                INSERT INTO job_stage_logs
                    (job_id, stage_name, stage_progress, total_progress, status, message, source)
                VALUES
                    (:job_id, 'queued', 100, 0, 'processing', :message, 'worker')
            """),
            {"job_id": job_id, "message": "작업자가 분석 작업을 시작했습니다."},
        )

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
                    (job_id, stage_name, stage_progress, total_progress, status, message, source)
                VALUES
                    (:job_id, :stage_name, :stage_progress, :total_progress, 'processing', :message, 'worker')
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
                    (job_id, stage_name, stage_progress, total_progress, status, message, source)
                VALUES
                    (:job_id, 'completed', 100, 100, 'completed', '분석이 완료되었습니다.', 'worker')
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
                    (job_id, stage_name, stage_progress, total_progress, status, message, source)
                VALUES
                    (:job_id, 'failed', 0, 0, 'failed', :error_message, 'worker')
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


def get_job_status(job_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT job_id, status, cancel_requested, current_stage, total_progress
                FROM analysis_jobs
                WHERE job_id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()

        if not row:
            raise ValueError("분석 작업을 찾을 수 없습니다.")

        m = row._mapping
        return {
            "job_id": str(m["job_id"]),
            "status": m["status"],
            "cancel_requested": bool(m["cancel_requested"]),
            "current_stage": m["current_stage"],
            "total_progress": m["total_progress"],
        }
    finally:
        db.close()


def save_stt_result(
    job_id: str,
    language: str,
    full_text: str,
    segment_count: int,
) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT user_id FROM analysis_jobs WHERE job_id = :job_id"),
            {"job_id": job_id},
        ).fetchone()
        if not row:
            raise ValueError("분석 작업을 찾을 수 없습니다.")
        user_id = row._mapping["user_id"]

        result = db.execute(
            text("""
                INSERT INTO analysis_artifacts
                    (job_id, user_id, artifact_type, stored_path, metadata)
                VALUES
                    (:job_id, :user_id, 'stt_transcript', '', :metadata)
                RETURNING artifact_id
            """),
            {
                "job_id": job_id,
                "user_id": user_id,
                "metadata": json.dumps({
                    "language": language,
                    "full_text": full_text,
                    "segment_count": segment_count,
                }),
            },
        ).fetchone()

        db.commit()
        return {
            "job_id": job_id,
            "artifact_id": str(result._mapping["artifact_id"]),
            "artifact_type": "stt_transcript",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_pii_result(job_id: str, pii_segments: list) -> dict:
    db = SessionLocal()
    try:
        detection_ids = []
        for seg in pii_segments:
            result = db.execute(
                text("""
                    INSERT INTO detections
                        (job_id, detection_type, label, confidence,
                         start_time_sec, end_time_sec, detected_text)
                    VALUES
                        (:job_id, 'voice_pii', :label, :confidence,
                         :start_time_sec, :end_time_sec, :detected_text)
                    RETURNING detection_id
                """),
                {
                    "job_id": job_id,
                    "label": seg.get("label"),
                    "confidence": seg.get("confidence"),
                    "start_time_sec": seg.get("start_time_sec"),
                    "end_time_sec": seg.get("end_time_sec"),
                    "detected_text": seg.get("detected_text"),
                },
            ).fetchone()
            detection_ids.append(str(result._mapping["detection_id"]))

        db.commit()
        return {
            "job_id": job_id,
            "saved_count": len(detection_ids),
            "detection_ids": detection_ids,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_artifact(
    job_id: str,
    artifact_type: str,
    stored_path: str,
    content_type: str | None = None,
    file_size: int | None = None,
    metadata: dict | None = None,
) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT user_id FROM analysis_jobs WHERE job_id = :job_id"),
            {"job_id": job_id},
        ).fetchone()
        if not row:
            raise ValueError("분석 작업을 찾을 수 없습니다.")
        user_id = row._mapping["user_id"]

        result = db.execute(
            text("""
                INSERT INTO analysis_artifacts
                    (job_id, user_id, artifact_type, stored_path,
                     content_type, file_size, metadata)
                VALUES
                    (:job_id, :user_id, :artifact_type, :stored_path,
                     :content_type, :file_size, :metadata)
                RETURNING artifact_id
            """),
            {
                "job_id": job_id,
                "user_id": user_id,
                "artifact_type": artifact_type,
                "stored_path": stored_path,
                "content_type": content_type,
                "file_size": file_size,
                "metadata": json.dumps(metadata) if metadata else None,
            },
        ).fetchone()

        db.commit()
        return {
            "job_id": job_id,
            "artifact_id": str(result._mapping["artifact_id"]),
            "artifact_type": artifact_type,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def record_heartbeat(
    job_id: str,
    worker_id: str | None,
    worker_type: str,
    ngrok_url: str | None,
    current_stage: str | None,
    progress_percent: int,
    message: str | None,
) -> dict:
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO job_worker_heartbeats
                    (job_id, worker_id, worker_type, ngrok_url,
                     current_stage, progress_percent, message)
                VALUES
                    (:job_id, :worker_id, :worker_type, :ngrok_url,
                     :current_stage, :progress_percent, :message)
            """),
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "worker_type": worker_type,
                "ngrok_url": ngrok_url,
                "current_stage": current_stage,
                "progress_percent": progress_percent,
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
