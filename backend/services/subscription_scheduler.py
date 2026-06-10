import asyncio
import logging
import os
from dataclasses import dataclass

from services import subscription_renewal, toss_billing_client
from utils.database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubscriptionSchedulerSettings:
    # 스케줄러 동작에 필요한 설정 값들을 관리하는 읽기 전용 데이터 클래스입니다.
    enabled: bool
    interval_seconds: int
    batch_limit: int


def _parse_bool(value, default=False):
    # 환경변수 문자열을 불리언(Boolean) 값으로 파싱합니다.
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_positive_int(value, default):
    # 환경변수 문자열을 양의 정수로 안전하게 파싱합니다.
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_scheduler_settings():
    # 환경변수로부터 스케줄러 관련 설정 값을 추출하여 반환합니다.
    return SubscriptionSchedulerSettings(
        enabled=_parse_bool(os.getenv("SUBSCRIPTION_SCHEDULER_ENABLED"), default=False),
        interval_seconds=_parse_positive_int(
            os.getenv("SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS"),
            default=300,
        ),
        batch_limit=_parse_positive_int(
            os.getenv("SUBSCRIPTION_SCHEDULER_BATCH_LIMIT"),
            default=50,
        ),
    )


def run_subscription_scheduler_once(session_factory=SessionLocal, batch_limit=50):
    # 자동결제 및 다운그레이드 처리 함수를 각각 1회씩 호출하여 동기적으로 구독 갱신을 실행합니다.
    db = session_factory()
    charge_client = toss_billing_client.charge_with_billing_key
    try:
        renewal_result = subscription_renewal.run_subscription_renewals(
            db,
            limit=batch_limit,
            charge_client=charge_client,
        )
        downgrade_result = subscription_renewal.run_scheduled_downgrades(
            db,
            limit=batch_limit,
            charge_client=charge_client,
        )
        return {
            "renewals": renewal_result,
            "scheduled_downgrades": downgrade_result,
        }
    finally:
        db.close()


async def _subscription_scheduler_loop(interval_seconds, batch_limit):
    # 무한 루프를 돌며 주기적으로 run_subscription_scheduler_once를 백그라운드 스레드에서 안전하게 호출합니다.
    while True:
        try:
            # 동기 DB I/O 함수를 asyncio.to_thread로 감싸서 이벤트 루프 차단을 방지합니다.
            result = await asyncio.to_thread(
                run_subscription_scheduler_once,
                batch_limit=batch_limit,
            )
            logger.info(
                "subscription scheduler finished: renewals=%s scheduled_downgrades=%s",
                result["renewals"].get("processed"),
                result["scheduled_downgrades"].get("processed"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("subscription scheduler failed")

        await asyncio.sleep(interval_seconds)


def start_subscription_scheduler(
    enabled,
    interval_seconds=300,
    batch_limit=50,
):
    # 스케줄러가 활성화 상태인 경우 백그라운드 비동기 태스크(Task)를 시작합니다.
    if not enabled:
        logger.info("subscription scheduler disabled")
        return None

    logger.info(
        "subscription scheduler enabled: interval_seconds=%s batch_limit=%s",
        interval_seconds,
        batch_limit,
    )
    return asyncio.create_task(
        _subscription_scheduler_loop(
            interval_seconds=interval_seconds,
            batch_limit=batch_limit,
        )
    )


async def stop_subscription_scheduler(task):
    # 작동 중인 백그라운드 태스크를 안전하게 정지시키고 대기합니다.
    if task is None:
        return

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("subscription scheduler stopped")
