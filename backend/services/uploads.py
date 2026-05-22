import hashlib
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from utils.database import SessionLocal

CHUNK_UPLOAD_EXPIRE_HOURS = int(os.getenv("CHUNK_UPLOAD_EXPIRE_HOURS", "24"))


def get_upload_dir():
    return Path(os.getenv("UPLOAD_DIR", "storage/uploads")).resolve()


def get_temp_base_dir():
    return Path(os.getenv("TEMP_DIR", "storage/temp")).resolve()


def sanitize_filename(filename):
    return Path(filename or "upload.bin").name


def init_upload(
    user_id: str,
    original_filename: str,
    content_type: str,
    file_size: int,
    media_type: str,
    chunk_size: int,
    total_chunks: int,
) -> dict:
    upload_id = str(uuid4())
    original_name = sanitize_filename(original_filename)
    stored_filename = f"{upload_id}_{original_name}"
    stored_path = str(get_upload_dir() / stored_filename)
    temp_dir_path = str(get_temp_base_dir() / upload_id)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=CHUNK_UPLOAD_EXPIRE_HOURS)

    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO uploads (
                    upload_id, user_id, original_filename, stored_filename,
                    stored_path, content_type, file_size, media_type,
                    chunk_size, total_chunks, uploaded_chunks,
                    temp_dir_path, status, expires_at
                ) VALUES (
                    :upload_id, :user_id, :original_filename, :stored_filename,
                    :stored_path, :content_type, :file_size, :media_type,
                    :chunk_size, :total_chunks, 0,
                    :temp_dir_path, 'initialized', :expires_at
                )
            """),
            {
                "upload_id": upload_id,
                "user_id": user_id,
                "original_filename": original_name,
                "stored_filename": stored_filename,
                "stored_path": stored_path,
                "content_type": content_type,
                "file_size": file_size,
                "media_type": media_type,
                "chunk_size": chunk_size,
                "total_chunks": total_chunks,
                "temp_dir_path": temp_dir_path,
                "expires_at": expires_at,
            },
        )
        db.commit()
    finally:
        db.close()

    return {
        "upload_id": upload_id,
        "status": "initialized",
        "total_chunks": total_chunks,
        "chunk_size": chunk_size,
        "expires_at": expires_at.isoformat(),
    }


def save_chunk(
    upload_id: str,
    user_id: str,
    chunk_index: int,
    chunk_file,
    chunk_hash: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT user_id, status, total_chunks, uploaded_chunks, temp_dir_path
                FROM uploads
                WHERE upload_id = :upload_id
            """),
            {"upload_id": upload_id},
        ).fetchone()

        if not row:
            raise ValueError("업로드를 찾을 수 없습니다.")

        m = row._mapping
        if str(m["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")
        if m["status"] not in ("initialized", "uploading"):
            raise ValueError(f"업로드할 수 없는 상태입니다: {m['status']}")
        if chunk_index < 0 or chunk_index >= m["total_chunks"]:
            raise ValueError(f"유효하지 않은 chunk_index입니다. (0 ~ {m['total_chunks'] - 1})")

        existing = db.execute(
            text("""
                SELECT upload_chunk_id FROM upload_chunks
                WHERE upload_id = :upload_id AND chunk_index = :chunk_index
            """),
            {"upload_id": upload_id, "chunk_index": chunk_index},
        ).fetchone()

        if existing:
            return {
                "upload_id": upload_id,
                "chunk_index": chunk_index,
                "status": "already_uploaded",
                "uploaded_chunks": m["uploaded_chunks"],
                "total_chunks": m["total_chunks"],
            }

        temp_dir = Path(m["temp_dir_path"])
        temp_dir.mkdir(parents=True, exist_ok=True)
        chunk_path = temp_dir / str(chunk_index)

        chunk_size = 0
        with chunk_path.open("wb") as f:
            while data := chunk_file.file.read(1024 * 1024):
                chunk_size += len(data)
                f.write(data)

        db.execute(
            text("""
                INSERT INTO upload_chunks
                    (upload_chunk_id, upload_id, chunk_index, chunk_size, chunk_hash, storage_path, status)
                VALUES
                    (gen_random_uuid(), :upload_id, :chunk_index, :chunk_size, :chunk_hash, :storage_path, 'uploaded')
            """),
            {
                "upload_id": upload_id,
                "chunk_index": chunk_index,
                "chunk_size": chunk_size,
                "chunk_hash": chunk_hash,
                "storage_path": str(chunk_path),
            },
        )

        db.execute(
            text("""
                UPDATE uploads
                SET uploaded_chunks = uploaded_chunks + 1,
                    status = 'uploading',
                    updated_at = now()
                WHERE upload_id = :upload_id
            """),
            {"upload_id": upload_id},
        )

        db.commit()

        return {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "status": "uploaded",
            "uploaded_chunks": m["uploaded_chunks"] + 1,
            "total_chunks": m["total_chunks"],
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_upload_status(upload_id: str, user_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT user_id, status, total_chunks, uploaded_chunks,
                       expires_at, file_hash, stored_path
                FROM uploads
                WHERE upload_id = :upload_id
            """),
            {"upload_id": upload_id},
        ).fetchone()

        if not row:
            raise ValueError("업로드를 찾을 수 없습니다.")

        m = row._mapping
        if str(m["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")

        total = m["total_chunks"] or 0
        done = m["uploaded_chunks"] or 0
        progress = round(done / total * 100) if total > 0 else 0

        missing_chunks = []
        if m["status"] not in ("uploaded", "cancelled", "failed") and total > 0:
            uploaded_indices = {
                r._mapping["chunk_index"]
                for r in db.execute(
                    text("SELECT chunk_index FROM upload_chunks WHERE upload_id = :upload_id"),
                    {"upload_id": upload_id},
                ).fetchall()
            }
            missing_chunks = sorted(set(range(total)) - uploaded_indices)

        return {
            "upload_id": upload_id,
            "status": m["status"],
            "total_chunks": total,
            "uploaded_chunks": done,
            "progress": progress,
            "missing_chunks": missing_chunks,
            "expires_at": m["expires_at"].isoformat() if m["expires_at"] else None,
            "file_hash": m["file_hash"],
            "stored_path": m["stored_path"] if m["status"] == "uploaded" else None,
        }
    finally:
        db.close()


def complete_upload(upload_id: str, user_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT user_id, status, total_chunks, uploaded_chunks,
                       temp_dir_path, stored_path, file_hash
                FROM uploads
                WHERE upload_id = :upload_id
            """),
            {"upload_id": upload_id},
        ).fetchone()

        if not row:
            raise ValueError("업로드를 찾을 수 없습니다.")

        m = row._mapping
        if str(m["user_id"]) != user_id:
            raise PermissionError("접근 권한이 없습니다.")

        if m["status"] == "uploaded":
            return {
                "upload_id": upload_id,
                "status": "uploaded",
                "file_hash": m["file_hash"],
                "stored_path": m["stored_path"],
            }

        if m["status"] not in ("uploading",):
            raise ValueError(f"병합할 수 없는 상태입니다: {m['status']}")

        if m["uploaded_chunks"] != m["total_chunks"]:
            raise ValueError(
                f"모든 chunk가 업로드되지 않았습니다. "
                f"({m['uploaded_chunks']}/{m['total_chunks']})"
            )

        chunks = db.execute(
            text("""
                SELECT chunk_index, storage_path
                FROM upload_chunks
                WHERE upload_id = :upload_id
                ORDER BY chunk_index ASC
            """),
            {"upload_id": upload_id},
        ).fetchall()

        if len(chunks) != m["total_chunks"]:
            raise ValueError(
                f"upload_chunks 레코드 수가 일치하지 않습니다. "
                f"({len(chunks)}/{m['total_chunks']})"
            )

        final_path = Path(m["stored_path"])
        final_path.parent.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256()
        with final_path.open("wb") as out_f:
            for chunk_row in chunks:
                chunk_path = Path(chunk_row._mapping["storage_path"])
                with chunk_path.open("rb") as in_f:
                    while data := in_f.read(1024 * 1024):
                        hasher.update(data)
                        out_f.write(data)

        file_hash = hasher.hexdigest()

        db.execute(
            text("""
                UPDATE uploads
                SET status = 'uploaded',
                    merged_file_path = :merged_file_path,
                    file_hash = :file_hash,
                    updated_at = now()
                WHERE upload_id = :upload_id
            """),
            {
                "upload_id": upload_id,
                "merged_file_path": str(final_path),
                "file_hash": file_hash,
            },
        )

        db.commit()

        shutil.rmtree(Path(m["temp_dir_path"]), ignore_errors=True)

        return {
            "upload_id": upload_id,
            "status": "uploaded",
            "file_hash": file_hash,
            "stored_path": str(final_path),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_upload_file(upload_file):
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = sanitize_filename(upload_file.filename)
    upload_id = uuid4().hex
    stored_path = upload_dir / f"{upload_id}_{original_name}"

    size = 0
    with stored_path.open("wb") as buffer:
        while chunk := upload_file.file.read(1024 * 1024):
            size += len(chunk)
            buffer.write(chunk)

    return {
        "upload_id": upload_id,
        "filename": original_name,
        "content_type": upload_file.content_type or "application/octet-stream",
        "size": size,
        "stored_path": str(stored_path),
    }
