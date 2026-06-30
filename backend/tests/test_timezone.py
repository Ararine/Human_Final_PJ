from datetime import datetime

from utils.timezone import to_kst


def test_to_kst_treats_naive_datetime_as_kst_after_db_timezone_change():
    result = to_kst(datetime(2026, 6, 29, 10, 15, 30))

    assert result.isoformat() == "2026-06-29T10:15:30+09:00"


def test_to_kst_converts_explicit_utc_datetime_to_kst():
    result = to_kst("2026-06-29T01:15:30Z")

    assert result.isoformat() == "2026-06-29T10:15:30+09:00"
