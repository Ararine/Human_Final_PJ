import asyncio
from unittest.mock import MagicMock

# 아직 구현되지 않은 subscription_scheduler 임포트 (실패 유도)
from services import subscription_scheduler


def test_scheduler_settings_disabled_by_default(monkeypatch):
    # 환경변수가 없을 때 스케줄러가 기본적으로 비활성화(disabled)되는지 검증
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_ENABLED", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_BATCH_LIMIT", raising=False)

    settings = subscription_scheduler.get_scheduler_settings()

    assert settings.enabled is False
    assert settings.interval_seconds == 300
    assert settings.batch_limit == 50


def test_scheduler_settings_reads_environment(monkeypatch):
    # 환경변수 설정값을 정상적으로 읽어오는지 검증
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS", "60")
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_BATCH_LIMIT", "25")

    settings = subscription_scheduler.get_scheduler_settings()

    assert settings.enabled is True
    assert settings.interval_seconds == 60
    assert settings.batch_limit == 25


def test_run_subscription_scheduler_once_calls_both_jobs_with_charge_client(monkeypatch):
    # run_once 실행 시 자동결제와 예약 다운그레이드가 모두 호출되고 charge_client가 올바르게 주입되는지 검증
    db = MagicMock()
    session_factory = MagicMock(return_value=db)
    renewals = MagicMock(return_value={"processed": 2, "results": []})
    downgrades = MagicMock(return_value={"processed": 1, "results": []})
    charge_client = MagicMock()

    monkeypatch.setattr(subscription_scheduler.subscription_renewal, "run_subscription_renewals", renewals)
    monkeypatch.setattr(subscription_scheduler.subscription_renewal, "run_scheduled_downgrades", downgrades)
    monkeypatch.setattr(subscription_scheduler.toss_billing_client, "charge_with_billing_key", charge_client)

    result = subscription_scheduler.run_subscription_scheduler_once(
        session_factory=session_factory,
        batch_limit=25,
    )

    session_factory.assert_called_once()
    renewals.assert_called_once_with(db, limit=25, charge_client=charge_client)
    downgrades.assert_called_once_with(db, limit=25, charge_client=charge_client)
    db.close.assert_called_once()
    assert result["renewals"]["processed"] == 2
    assert result["scheduled_downgrades"]["processed"] == 1


def test_start_subscription_scheduler_returns_none_when_disabled():
    # 스케줄러가 비활성화인 경우 비동기 태스크를 생성하지 않고 None을 반환하는지 검증
    task = subscription_scheduler.start_subscription_scheduler(enabled=False)

    assert task is None


def test_start_subscription_scheduler_creates_task_when_enabled():
    # 스케줄러가 활성화인 경우 비동기 백그라운드 태스크가 정상적으로 생성되는지 검증
    async def runner():
        task = subscription_scheduler.start_subscription_scheduler(
            enabled=True,
            interval_seconds=3600,
            batch_limit=1,
        )
        assert task is not None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(runner())
