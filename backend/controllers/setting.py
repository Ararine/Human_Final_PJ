from uuid import UUID

from fastapi import Body, Path, status
from fastapi.responses import JSONResponse

from services import setting


async def get_setting(
    user_id: UUID = Path(
        ...,
        description="유저 ID"
    )
):
    try:
        data = setting.get_setting(user_id)

        if not data:
            return JSONResponse(
                {"message": "설정 정보가 없습니다."},
                status_code=status.HTTP_404_NOT_FOUND
            )

        return JSONResponse(
            {
                "data": data,
                "message": "환경설정 조회"
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            {"message": "조회 실패 " + str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_setting(
    user_id: UUID = Path(
        ...,
        description="유저 ID"
    ),

    email_notification: bool = Body(
        ...,
        example=True,
        description="이메일 알림 여부"
    ),

    browser_notification: bool = Body(
        ...,
        example=True,
        description="브라우저 알림 여부"
    ),

    data_usage_consent: bool = Body(
        ...,
        example=False,
        description="학습 데이터 활용 동의 여부"
    )
):
    try:
        data = setting.update_setting(
            user_id,
            email_notification,
            browser_notification,
            data_usage_consent,
        )

        return JSONResponse(
            {
                "data": data,
                "message": "환경설정 수정 완료"
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            {"message": "수정 실패 " + str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )