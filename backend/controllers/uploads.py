from fastapi import File, UploadFile, status
from fastapi.responses import JSONResponse

from services import uploads


async def create_upload(file: UploadFile = File(...)):
    try:
        data = uploads.save_upload_file(file)
        return JSONResponse(data, status_code=status.HTTP_201_CREATED)
    except Exception as exc:
        return JSONResponse(
            {"message": f"파일 업로드에 실패했습니다: {exc}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
