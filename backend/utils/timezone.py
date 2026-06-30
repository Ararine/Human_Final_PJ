"""
KST(Korea Standard Time) 타임존 공통 유틸리티.
프로젝트 전반에서 datetime.now(timezone.utc) 대신
datetime.now(KST)를 사용하여 한국 표준시 기준으로 통일한다.
"""
from datetime import timezone, timedelta

# [한글 주석] KST = UTC+9 (한국 표준시). pytz 의존 없이 timedelta로 정의.
KST = timezone(timedelta(hours=9), name="KST")


def now_kst():
    """현재 KST 기준 datetime을 반환한다."""
    from datetime import datetime
    return datetime.now(tz=KST)


def to_kst(dt):
    """
    timezone-aware 또는 naive datetime을 KST로 변환한다.
    DB 세션 타임존이 Asia/Seoul이므로 naive datetime은 KST로 간주한다.
    """
    from datetime import datetime
    if dt is None:
        return None
    if isinstance(dt, str):
        from dateutil.parser import parse
        dt = parse(dt)
    if dt.tzinfo is None:
        # [한글 주석] DB timestamp without time zone 값은 KST 기준 naive datetime으로 들어온다.
        dt = dt.replace(tzinfo=KST)
    return dt.astimezone(KST)
