import os
from pathlib import Path
from uuid import uuid4


def get_upload_dir():
    return Path(os.getenv("UPLOAD_DIR", "storage/uploads")).resolve()


def sanitize_filename(filename):
    return Path(filename or "upload.bin").name


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
