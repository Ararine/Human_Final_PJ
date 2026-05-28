from fastapi import Cookie, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import auth, analysis


class CreateJobRequest(BaseModel):
    upload_id: str


def create_job_handler(
    body: CreateJobRequest,
    access_token: str | None = Cookie(default=None),
):
    current_user = auth.authenticate_access_token(access_token)
    try:
        result = analysis.create_analysis_job(
            upload_id=body.upload_id,
            user_id=str(current_user["id"]),
        )
        code = status.HTTP_200_OK if result.get("already_exists") else status.HTTP_201_CREATED
        return JSONResponse(result, status_code=code)
    except PermissionError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return JSONResponse(
            {"message": f"analysis job creation failed: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_job_handler(
    job_id: str,
    access_token: str | None = Cookie(default=None),
):
    current_user = auth.authenticate_access_token(access_token)
    try:
        result = analysis.get_analysis_job(
            job_id=job_id,
            user_id=str(current_user["id"]),
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except PermissionError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return JSONResponse(
            {"message": f"analysis job lookup failed: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def cancel_job_handler(
    job_id: str,
    access_token: str | None = Cookie(default=None),
):
    current_user = auth.authenticate_access_token(access_token)
    try:
        result = analysis.cancel_analysis_job(
            job_id=job_id,
            user_id=str(current_user["id"]),
        )
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    except PermissionError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return JSONResponse(
            {"message": f"analysis job cancel failed: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
