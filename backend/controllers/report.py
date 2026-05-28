from fastapi import APIRouter, Cookie, HTTPException
from services import report as report_service
from services import auth

router = APIRouter(tags=["report"])


# 리포트 생성 (FR-21-01)
@router.post("/reports/analyze")
def analyze(payload: dict, access_token: str | None = Cookie(default=None)):
    user = auth.authenticate_access_token(access_token)

    return report_service.analyze_and_save(user["id"], payload)


# 전체 리포트 조회
@router.get("/reports")
def get_reports(access_token: str | None = Cookie(default=None)):
    user = auth.authenticate_access_token(access_token)

    return report_service.get_reports(user["id"])


# 단일 리포트 조회
@router.get("/reports/{report_id}")
def get_report(report_id: int, access_token: str | None = Cookie(default=None)):
    user = auth.authenticate_access_token(access_token)

    return report_service.get_report(user["id"], report_id)


# FR-21-02 SNS 누적 리포트 (핵심)
@router.get("/reports/summary")
def get_summary(access_token: str | None = Cookie(default=None)):
    user = auth.authenticate_access_token(access_token)

    return report_service.get_summary(user["id"])