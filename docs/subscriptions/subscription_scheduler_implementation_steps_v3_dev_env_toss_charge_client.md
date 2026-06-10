# 구독 스케줄러 구현 계획 v3 - 개발 `.env` + Toss `charge_client` 주입 방식

> **작업 대상:** Gemini 3.5 Flash High 또는 Codex 같은 코드 작업 에이전트가 이 문서를 기준으로 단계별 구현한다.
>
> **핵심 변경점:** v2 문서의 개발 환경 우선 테스트 방향은 유지하되, 자동결제 시 실제 Toss Billing 승인 API를 호출할 수 있도록 **방식 2: `charge_client` 주입 구조**를 추가한다. `docker-compose.yml`은 수정하지 않고, 개발 테스트용 환경변수는 `backend/.env`에서 관리한다.

---

## 0. 결제 테스트 안전성 확인

Toss Payments의 **테스트 키는 `test_`로 시작**한다. 테스트 환경에서는 실제 카드번호나 휴대폰 번호 같은 결제 정보를 사용해도 결제 승인은 가상으로 이루어지고, 결제수단에서 금액이 차감되지 않는다.

따라서 개발 테스트에서는 아래 원칙을 반드시 지킨다.

```env
# 실제 운영 키 사용 금지
TOSS_SECRET_KEY=test_sk_...
TOSS_BILLING_TEST_MODE=true
```

또는 실제 Toss 테스트 API 호출까지 확인하고 싶을 때만 아래처럼 둔다.

```env
TOSS_SECRET_KEY=test_sk_...
TOSS_BILLING_TEST_MODE=false
```

주의:

- `live_sk_...` 형태의 라이브 시크릿 키를 넣으면 실제 결제 환경으로 연결될 수 있으므로 개발 테스트에서는 절대 사용하지 않는다.
- 처음에는 반드시 `TOSS_BILLING_TEST_MODE=true`로 테스트해서 DB 갱신 흐름만 먼저 검증한다.
- 이후 Toss 테스트 결제내역까지 보고 싶을 때만 `TOSS_BILLING_TEST_MODE=false`와 `test_sk_...` 조합으로 확인한다.

---

## 1. 목표

기존 `backend/services/subscription_renewal.py`에 있는 아래 함수를 FastAPI 실행 중 주기적으로 호출하는 구독 스케줄러를 추가한다.

```python
run_subscription_renewals(db, limit=50, charge_client=None)
run_scheduled_downgrades(db, limit=50, charge_client=None)
```

추가로, `charge_client`에 Toss Billing 결제 함수를 주입해서 아래 흐름이 가능하도록 한다.

```text
subscription_scheduler.py
→ run_subscription_scheduler_once()
→ subscription_renewal.run_subscription_renewals(..., charge_client=toss_billing_client.charge_with_billing_key)
→ subscription_renewal._charge_subscription()
→ charge_client(...) 호출
→ Toss Billing API 또는 테스트 모드 응답
```

---

## 2. 아키텍처 원칙

- 결제/구독 비즈니스 로직은 `backend/services/subscription_renewal.py`에 유지한다.
- 새 `backend/services/subscription_scheduler.py`는 주기 실행, DB 세션, 로깅, `charge_client` 주입만 담당한다.
- 새 `backend/services/toss_billing_client.py`는 Toss Billing API 호출만 담당한다.
- `subscription_renewal.py` 안에 Toss HTTP 호출 코드를 직접 넣지 않는다.
- 스케줄러 활성화 여부와 실행 주기는 `backend/.env`에서 관리한다.
- 이번 작업에서는 `docker-compose.yml`을 수정하지 않는다.

---

## 3. 현재 상태와 부족한 부분

현재 구현되어 있는 부분:

- `backend/services/subscription_renewal.py`
  - `run_subscription_renewals(db, limit=50, charge_client=None)`
  - `run_scheduled_downgrades(db, limit=50, charge_client=None)`
  - `_charge_subscription()`에서 `charge_client`가 있으면 외부 결제 함수를 호출할 수 있음
  - `TOSS_BILLING_TEST_MODE=true`일 때 가짜 성공 응답 처리 가능
  - 대상 조회 SQL에 `FOR UPDATE ... SKIP LOCKED`가 있어 중복 처리 방어가 들어가 있음

현재 빠진 부분:

- FastAPI 앱 시작 시 위 함수를 주기적으로 호출하는 스케줄러가 없음
- `backend/main.py`에 `lifespan`/`asyncio.create_task` 연결이 없음
- `charge_client`로 Toss Billing 결제 함수를 주입하는 연결부가 없음
- Toss Billing 승인 API를 호출하는 별도 클라이언트가 없음
- 개발 환경에서 사용할 `backend/.env`에 스케줄러/Toss 테스트 환경변수가 정리되어 있지 않음
- 스케줄러가 자동결제와 예약 다운그레이드 함수에 `charge_client`를 주입하는지 검증하는 테스트가 없음

---

## 4. 파일 작업 계획

### 생성

- `backend/services/subscription_scheduler.py`
  - 스케줄러 설정 파싱
  - 1회 실행 함수
  - 백그라운드 루프 함수
  - 시작/종료 함수
  - `toss_billing_client.charge_with_billing_key`를 `charge_client`로 주입

- `backend/services/toss_billing_client.py`
  - Toss Billing API 호출 함수
  - 테스트 모드 응답 처리
  - Toss API 에러 응답 표준화

- `backend/tests/test_subscription_scheduler.py`
  - 환경변수 파싱 테스트
  - `run_once`가 자동결제와 예약 다운그레이드에 `charge_client`를 넘기는지 테스트
  - 비활성화 시 백그라운드 태스크를 만들지 않는지 테스트

- `backend/tests/test_toss_billing_client.py`
  - 테스트 모드 성공 응답 테스트
  - 시크릿 키 미설정 실패 테스트
  - 실제 HTTP 호출은 monkeypatch로 가짜 응답 처리

### 수정

- `backend/main.py`
  - FastAPI `lifespan` 추가
  - 앱 시작 시 스케줄러 시작
  - 앱 종료 시 스케줄러 중지

- `backend/.env`
  - 개발 환경 스케줄러/Toss 테스트 환경변수 추가

- `docs/subscriptions/subscription_user_manual_test_scenarios_v1.md`
  - 수동 1회 실행 명령 추가
  - Toss 테스트 키 사용 시 실제 금액 차감 없음 주의사항 추가

### 수정하지 않음

- `docker-compose.yml`
  - 이번 작업에서는 수정하지 않는다.

---

## 작업 1: Toss Billing Client 테스트 추가

**파일:**

- 생성: `backend/tests/test_toss_billing_client.py`

- [ ] **1단계: 테스트 파일 생성**

```python
import json
from unittest.mock import MagicMock

from services import toss_billing_client


def test_charge_with_billing_key_returns_fake_success_in_test_mode(monkeypatch):
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "true")
    monkeypatch.delenv("TOSS_SECRET_KEY", raising=False)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="test_billing_key",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is True
    assert result["method"] == "billing"
    assert result["pg_transaction_id"].startswith("test-renewal-")


def test_charge_with_billing_key_fails_without_secret_key(monkeypatch):
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "false")
    monkeypatch.delenv("TOSS_SECRET_KEY", raising=False)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="test_billing_key",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is False
    assert result["failure_code"] == "toss_secret_key_missing"


def test_charge_with_billing_key_calls_toss_api(monkeypatch):
    monkeypatch.setenv("TOSS_BILLING_TEST_MODE", "false")
    monkeypatch.setenv("TOSS_SECRET_KEY", "test_sk_example")

    class FakeResponse:
        status = 200

        def read(self):
            return json.dumps({
                "paymentKey": "payment-key-1",
                "method": "카드",
                "status": "DONE",
            }).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    urlopen_mock = MagicMock(return_value=FakeResponse())
    monkeypatch.setattr(toss_billing_client.request, "urlopen", urlopen_mock)

    result = toss_billing_client.charge_with_billing_key(
        billing_key="billing-key-1",
        customer_key="customer-1",
        amount=2900,
        order_id="order-1",
        order_name="Garim Pro renewal",
    )

    assert result["success"] is True
    assert result["pg_transaction_id"] == "payment-key-1"
    assert result["method"] == "카드"
    urlopen_mock.assert_called_once()
```

- [ ] **2단계: 테스트 실행 후 실패 확인**

```bash
python -m pytest backend/tests/test_toss_billing_client.py -q
```

기대 결과:

```text
ModuleNotFoundError 또는 ImportError가 발생해야 한다.
```

---

## 작업 2: Toss Billing Client 구현

**파일:**

- 생성: `backend/services/toss_billing_client.py`

- [ ] **1단계: 클라이언트 파일 생성**

```python
import base64
import json
import os
import uuid
from urllib import error, request


TOSS_BILLING_API_BASE_URL = "https://api.tosspayments.com"


def _is_test_mode():
    return os.getenv("TOSS_BILLING_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def _basic_auth_header(secret_key: str):
    token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def charge_with_billing_key(
    billing_key,
    customer_key,
    amount,
    order_id,
    order_name,
):
    """
    subscription_renewal._charge_subscription()에서 주입받아 호출할 Toss Billing 결제 함수.

    반환 형식은 subscription_renewal.py가 기대하는 charge dict에 맞춘다.
    - success: bool
    - pg_transaction_id: str | None
    - method: str | None
    - failure_code: str | None
    - failure_message: str | None
    """
    if _is_test_mode():
        return {
            "success": True,
            "pg_transaction_id": f"test-renewal-{uuid.uuid4()}",
            "method": "billing",
        }

    secret_key = os.getenv("TOSS_SECRET_KEY")
    if not secret_key:
        return {
            "success": False,
            "failure_code": "toss_secret_key_missing",
            "failure_message": "TOSS_SECRET_KEY is not configured.",
        }

    payload = {
        "customerKey": customer_key,
        "amount": int(amount),
        "orderId": order_id,
        "orderName": order_name,
    }

    url = f"{TOSS_BILLING_API_BASE_URL}/v1/billing/{billing_key}"
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": _basic_auth_header(secret_key),
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "pg_transaction_id": body.get("paymentKey") or body.get("transactionKey"),
                "method": body.get("method") or "billing",
                "raw": body,
            }
    except error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return {
            "success": False,
            "failure_code": body.get("code") or f"http_{exc.code}",
            "failure_message": body.get("message") or str(exc),
            "raw": body,
        }
    except Exception as exc:
        return {
            "success": False,
            "failure_code": "toss_billing_request_failed",
            "failure_message": str(exc),
        }
```

- [ ] **2단계: Toss Billing Client 테스트 실행**

```bash
python -m pytest backend/tests/test_toss_billing_client.py -q
```

기대 결과:

```text
3 passed
```

---

## 작업 3: 스케줄러 서비스 단위 테스트 추가

**파일:**

- 생성: `backend/tests/test_subscription_scheduler.py`

- [ ] **1단계: 실패하는 테스트 작성**

```python
import asyncio
from unittest.mock import MagicMock

from services import subscription_scheduler


def test_scheduler_settings_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_ENABLED", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_SCHEDULER_BATCH_LIMIT", raising=False)

    settings = subscription_scheduler.get_scheduler_settings()

    assert settings.enabled is False
    assert settings.interval_seconds == 300
    assert settings.batch_limit == 50


def test_scheduler_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS", "60")
    monkeypatch.setenv("SUBSCRIPTION_SCHEDULER_BATCH_LIMIT", "25")

    settings = subscription_scheduler.get_scheduler_settings()

    assert settings.enabled is True
    assert settings.interval_seconds == 60
    assert settings.batch_limit == 25


def test_run_subscription_scheduler_once_calls_both_jobs_with_charge_client(monkeypatch):
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
    task = subscription_scheduler.start_subscription_scheduler(enabled=False)

    assert task is None


def test_start_subscription_scheduler_creates_task_when_enabled():
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
```

- [ ] **2단계: 테스트 실행 후 실패 확인**

```bash
python -m pytest backend/tests/test_subscription_scheduler.py -q
```

기대 결과:

```text
ModuleNotFoundError: No module named 'services.subscription_scheduler'
```

---

## 작업 4: 스케줄러 서비스 구현

**파일:**

- 생성: `backend/services/subscription_scheduler.py`

- [ ] **1단계: 스케줄러 서비스 추가**

```python
import asyncio
import logging
import os
from dataclasses import dataclass

from services import subscription_renewal, toss_billing_client
from utils.database import SessionLocal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubscriptionSchedulerSettings:
    enabled: bool
    interval_seconds: int
    batch_limit: int


def _parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_scheduler_settings():
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
    while True:
        try:
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
    if task is None:
        return

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("subscription scheduler stopped")
```

- [ ] **2단계: 스케줄러 테스트 실행**

```bash
python -m pytest backend/tests/test_subscription_scheduler.py -q
```

기대 결과:

```text
5 passed
```

---

## 작업 5: 스케줄러를 FastAPI Lifespan에 연결

**파일:**

- 수정: `backend/main.py`

- [ ] **1단계: import 수정**

`backend/main.py` 상단을 아래와 같이 변경한다.

기존:

```python
import uvicorn,os,logging
from pathlib import Path
from dotenv import load_dotenv
```

변경:

```python
import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
```

- [ ] **2단계: 스케줄러 서비스 import**

`backend/main.py`의 route import 이후에 아래 코드를 추가한다.

```python
from services import subscription_scheduler
```

- [ ] **3단계: lifespan 함수 추가**

`app = FastAPI()`보다 위에 아래 코드를 추가한다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = subscription_scheduler.get_scheduler_settings()
    scheduler_task = subscription_scheduler.start_subscription_scheduler(
        enabled=settings.enabled,
        interval_seconds=settings.interval_seconds,
        batch_limit=settings.batch_limit,
    )
    try:
        yield
    finally:
        await subscription_scheduler.stop_subscription_scheduler(scheduler_task)
```

- [ ] **4단계: FastAPI에 lifespan 연결**

기존:

```python
app = FastAPI()
```

변경:

```python
app = FastAPI(lifespan=lifespan)
```

주의:

- `main.py`에 이미 `FastAPI(title=..., version=...)` 같은 옵션이 있으면 삭제하지 말고 그대로 유지하면서 `lifespan=lifespan`만 추가한다.
- 기존 라우터, CORS, 정적 파일 설정을 삭제하거나 순서를 크게 바꾸지 않는다.

---

## 작업 6: 개발 환경 `.env` 설정

**파일:**

- 수정: `backend/.env`

이번 작업은 우선 개발 환경에서 직접 테스트하는 것이 목적이다. 따라서 `docker-compose.yml`에 스케줄러 환경변수를 추가하지 않고, 기존 개발 실행 방식에서 읽는 `backend/.env`에 값을 추가한다.

- [ ] **1단계: 스케줄러 환경변수 추가**

```env
# Subscription scheduler
SUBSCRIPTION_SCHEDULER_ENABLED=true
SUBSCRIPTION_SCHEDULER_INTERVAL_SECONDS=300
SUBSCRIPTION_SCHEDULER_BATCH_LIMIT=50
```

- [ ] **2단계: Toss Billing 테스트 환경변수 추가**

처음 테스트는 실제 Toss API 호출 없이 DB 흐름만 검증하기 위해 아래처럼 둔다.

```env
# Toss Billing scheduler test mode
TOSS_BILLING_TEST_MODE=true

# 실제 Toss 테스트 API 호출까지 확인할 때만 test_sk_... 값을 넣고 TOSS_BILLING_TEST_MODE=false로 변경한다.
# 절대 live_sk_... 키를 개발 테스트에 넣지 않는다.
TOSS_SECRET_KEY=test_sk_여기에_테스트_시크릿_키
```

테스트 단계별 권장값:

```text
1차: DB 갱신 흐름만 확인
TOSS_BILLING_TEST_MODE=true
TOSS_SECRET_KEY는 없어도 됨

2차: Toss 테스트 결제내역까지 확인
TOSS_BILLING_TEST_MODE=false
TOSS_SECRET_KEY=test_sk_...

금지:
TOSS_SECRET_KEY=live_sk_...
```

- [ ] **3단계: 환경변수 로딩 확인**

```bash
rg -n "load_dotenv|SUBSCRIPTION_SCHEDULER_ENABLED|TOSS_BILLING_TEST_MODE|TOSS_SECRET_KEY" backend
```

기대 결과:

```text
backend/main.py:...:load_dotenv()
backend/services/subscription_scheduler.py:...:SUBSCRIPTION_SCHEDULER_ENABLED
backend/services/toss_billing_client.py:...:TOSS_BILLING_TEST_MODE
backend/services/toss_billing_client.py:...:TOSS_SECRET_KEY
```

---

## 작업 7: 수동 1회 실행 검증 명령 추가

**파일:**

- 수정: `docs/subscriptions/subscription_user_manual_test_scenarios_v1.md`

- [ ] **1단계: 수동 실행 명령 섹션 추가**

기존 자동결제 스케줄러 시나리오 근처에 아래 섹션을 추가한다.

````markdown
## 자동결제 스케줄러 수동 1회 실행 확인

FastAPI lifespan에서 스케줄러가 자동 실행되지만, 개발 중에는 아래 명령으로 1회 실행 결과를 확인할 수 있다.

```bash
cd backend
python -c "from services.subscription_scheduler import run_subscription_scheduler_once; print(run_subscription_scheduler_once())"
```

기대 결과:

```text
{'renewals': {'processed': ...}, 'scheduled_downgrades': {'processed': ...}}
```

테스트 모드별 동작:

- `TOSS_BILLING_TEST_MODE=true`: 실제 Toss API를 호출하지 않고 테스트 성공 응답으로 처리한다.
- `TOSS_BILLING_TEST_MODE=false` + `TOSS_SECRET_KEY=test_sk_...`: Toss 테스트 API를 호출한다. 테스트 키 환경에서는 결제 승인이 가상으로 이루어지며 실제 금액은 차감되지 않는다.
- `TOSS_SECRET_KEY=live_sk_...`: 실제 운영 결제로 이어질 수 있으므로 개발 테스트에서는 사용하지 않는다.

처리 대상 조건:

- 자동결제: `subscriptions.next_billing_at <= NOW()`인 유료 active 구독이어야 한다.
- 예약 다운그레이드: `subscription_plan_changes.effective_at <= NOW()`인 scheduled downgrade여야 한다.
````

- [ ] **2단계: docs grep 실행**

```bash
rg -n "자동결제 스케줄러 수동 1회 실행 확인|run_subscription_scheduler_once|TOSS_BILLING_TEST_MODE" docs/subscriptions
```

---

## 작업 8: 최종 검증

- [ ] **1단계: Toss Client 테스트 실행**

```bash
python -m pytest backend/tests/test_toss_billing_client.py -q
```

기대 결과:

```text
3 passed
```

- [ ] **2단계: 스케줄러 테스트 실행**

```bash
python -m pytest backend/tests/test_subscription_scheduler.py -q
```

기대 결과:

```text
5 passed
```

- [ ] **3단계: 기존 결제/구독 테스트 실행**

```bash
python -m pytest backend/tests/test_payment.py backend/tests/test_subscription.py -q
```

기대 결과:

```text
선택한 모든 테스트가 통과해야 한다.
```

- [ ] **4단계: 전체 관련 테스트 실행**

```bash
python -m pytest backend/tests/test_toss_billing_client.py backend/tests/test_subscription_scheduler.py backend/tests/test_payment.py backend/tests/test_subscription.py -q
```

- [ ] **5단계: 코드 연결 확인**

```bash
rg -n "subscription_scheduler|toss_billing_client|charge_client|TOSS_BILLING_TEST_MODE|SUBSCRIPTION_SCHEDULER_ENABLED|run_subscription_scheduler_once" backend docs/subscriptions
```

기대 결과:

```text
backend/main.py:...:from services import subscription_scheduler
backend/main.py:...:async def lifespan(app: FastAPI):
backend/services/subscription_scheduler.py:...:charge_client=toss_billing_client.charge_with_billing_key
backend/services/toss_billing_client.py:...:def charge_with_billing_key
backend/.env:...:SUBSCRIPTION_SCHEDULER_ENABLED=true
backend/.env:...:TOSS_BILLING_TEST_MODE=true
```

- [ ] **6단계: 개발 서버 실행 확인**

```bash
cd backend
python -m uvicorn main:app --reload
```

기대 로그 예시:

```text
subscription scheduler enabled: interval_seconds=300 batch_limit=50
```

---

## 9. 승인 기준

- [ ] `backend/services/toss_billing_client.py` 파일이 존재한다.
- [ ] `charge_with_billing_key()`가 `TOSS_BILLING_TEST_MODE=true`일 때 실제 API 호출 없이 성공 응답을 반환한다.
- [ ] `charge_with_billing_key()`가 `TOSS_BILLING_TEST_MODE=false`일 때 `TOSS_SECRET_KEY`로 Toss Billing API를 호출할 수 있다.
- [ ] `backend/services/subscription_scheduler.py` 파일이 존재한다.
- [ ] `run_subscription_scheduler_once()`가 `run_subscription_renewals()`와 `run_scheduled_downgrades()`를 모두 호출한다.
- [ ] 두 호출 모두 `charge_client=toss_billing_client.charge_with_billing_key`를 전달한다.
- [ ] `SUBSCRIPTION_SCHEDULER_ENABLED=true`일 때만 FastAPI startup에서 scheduler task를 생성한다.
- [ ] FastAPI shutdown 시 scheduler task가 정상적으로 cancel된다.
- [ ] 개발 환경용 `backend/.env`에 스케줄러/Toss 테스트 환경변수가 정리되어 있다.
- [ ] `docker-compose.yml`은 이번 작업에서 수정되지 않는다.
- [ ] 기존 renewal/downgrade service 테스트가 계속 통과한다.
- [ ] 새 scheduler 테스트와 Toss client 테스트가 통과한다.

---

## 10. 구현 시 주의사항

- `subscription_renewal.py`의 기존 결제/구독 비즈니스 로직을 대규모로 옮기지 않는다.
- `subscription_renewal.py`에 Toss HTTP 호출 코드를 직접 넣지 않는다.
- 실제 Toss API 호출은 `backend/services/toss_billing_client.py`에서만 처리한다.
- 스케줄러는 `charge_client`를 주입하는 방식으로만 Toss 결제 함수를 연결한다.
- 코드 기본값에서 `SUBSCRIPTION_SCHEDULER_ENABLED`는 `false`로 유지한다.
- 개발 검증 단계에서는 `backend/.env`에서 스케줄러를 명시적으로 활성화한다.
- 테스트 중 실제 운영 결제를 방지하기 위해 `live_sk_` 키를 절대 사용하지 않는다.
- Toss 테스트 키는 `test_`로 시작해야 한다.
- 현재 `subscription_renewal.py`의 SQL locking은 중요하다. 대상 조회 쿼리의 `FOR UPDATE ... SKIP LOCKED`를 유지한다.

---

## 11. Gemini 3.5 Flash High 작업 지시문

아래 문장을 MD와 함께 전달한다.

```text
첨부한 MD 파일 기준으로 작업해줘.

중요 조건:
1. 문서에 없는 대규모 리팩토링은 하지 마.
2. 결제/구독 비즈니스 로직은 backend/services/subscription_renewal.py에 그대로 두고, 새 subscription_scheduler.py는 주기 실행/DB 세션/로깅/charge_client 주입만 담당하게 해줘.
3. Toss API 직접 호출은 backend/services/toss_billing_client.py에서만 구현해줘.
4. docker-compose.yml은 이번 작업에서 수정하지 마.
5. 스케줄러/Toss 테스트 환경변수는 backend/.env에만 추가해줘.
6. TOSS_SECRET_KEY에는 테스트 키(test_sk_...)만 사용한다는 주석을 남겨줘.
7. 기존 main.py 구조가 문서와 다르면, 기존 라우터/CORS/정적 파일 설정을 유지한 상태에서 FastAPI lifespan만 안전하게 추가해줘.
8. import 경로가 실제 프로젝트 구조와 다르면, 테스트가 통과하는 방향으로 최소 수정해줘.
9. 작업 후 아래 명령이 통과해야 해.

python -m pytest backend/tests/test_toss_billing_client.py backend/tests/test_subscription_scheduler.py backend/tests/test_payment.py backend/tests/test_subscription.py -q

10. 마지막에 수정/생성한 파일 목록과 테스트 결과를 요약해줘.
```

---

## 12. 참고

- Toss Payments 테스트 키는 테스트 환경에서 가상 결제 승인만 수행하며 실제 금액이 차감되지 않는다.
- Toss Billing 자동결제 승인 API는 발급된 `billingKey`를 path parameter로 사용해 `POST /v1/billing/{billingKey}` 형태로 호출한다.
- Toss Payments는 구독 스케줄링 기능을 직접 제공하지 않으므로 서비스에서 직접 스케줄러를 구현해야 한다.
