from fastapi import Header, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from services import worker


class AcceptJobRequest(BaseModel):
    worker_id: str | None = None


class ProgressRequest(BaseModel):
    worker_id: str | None = None
    stage_name: str
    stage_progress: int = Field(ge=0, le=100)
    total_progress: int = Field(ge=0, le=100)
    message: str | None = None


class CompleteRequest(BaseModel):
    worker_id: str | None = None
    detection_count: int = Field(default=0, ge=0)


class FailRequest(BaseModel):
    worker_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class HeartbeatRequest(BaseModel):
    job_id: str
    worker_id: str | None = None
    worker_type: str = "colab"
    public_endpoint: str | None = None
    current_stage: str | None = None
    progress: int = Field(default=0, ge=0, le=100)
    message: str | None = None


def _check_auth(authorization: str | None):
    try:
        worker.authenticate_worker(authorization)
    except PermissionError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_401_UNAUTHORIZED)
    return None


def get_next_job_handler(authorization: str | None = Header(default=None)):
    if (err := _check_auth(authorization)):
        return err
    result = worker.get_next_job()
    if result is None:
        return JSONResponse(
            {"job": None, "message": "대기 중인 작업이 없습니다."},
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse({"job": result}, status_code=status.HTTP_200_OK)


def accept_job_handler(
    job_id: str,
    body: AcceptJobRequest,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        result = worker.accept_job(job_id)
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return JSONResponse(
            {"message": f"작업 수락에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_file_handler(
    upload_id: str,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        info = worker.get_upload_file_info(upload_id)
        return FileResponse(
            path=info["stored_path"],
            media_type=info["content_type"],
            filename=info["original_filename"],
        )
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return JSONResponse(
            {"message": f"파일 조회에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def update_progress_handler(
    job_id: str,
    body: ProgressRequest,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        result = worker.update_job_progress(
            job_id=job_id,
            worker_id=body.worker_id,
            stage_name=body.stage_name,
            stage_progress=body.stage_progress,
            total_progress=body.total_progress,
            message=body.message,
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except Exception as exc:
        return JSONResponse(
            {"message": f"진행률 업데이트에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def complete_job_handler(
    job_id: str,
    body: CompleteRequest,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        result = worker.complete_job(
            job_id=job_id,
            worker_id=body.worker_id,
            detection_count=body.detection_count,
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except Exception as exc:
        return JSONResponse(
            {"message": f"작업 완료 처리에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def fail_job_handler(
    job_id: str,
    body: FailRequest,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        result = worker.fail_job(
            job_id=job_id,
            worker_id=body.worker_id,
            error_code=body.error_code,
            error_message=body.error_message,
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except Exception as exc:
        return JSONResponse(
            {"message": f"작업 실패 처리에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def heartbeat_handler(
    body: HeartbeatRequest,
    authorization: str | None = Header(default=None),
):
    if (err := _check_auth(authorization)):
        return err
    try:
        result = worker.record_heartbeat(
            job_id=body.job_id,
            worker_id=body.worker_id,
            worker_type=body.worker_type,
            public_endpoint=body.public_endpoint,
            current_stage=body.current_stage,
            progress=body.progress,
            message=body.message,
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except Exception as exc:
        return JSONResponse(
            {"message": f"heartbeat 기록에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
