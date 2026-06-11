# 구독 업그레이드 정책 변경 작업 지시서

대상 저장소/브랜치: `https://github.com/Ararine/Human_Final_PJ/tree/sedeok`

## 0. 변경 목적

현재 구독 업그레이드 로직은 하위 플랜의 남은 기간을 상위 플랜 종료 뒤로 이어 붙이는 `carryover` 방식으로 구현되어 있다.

변경 후 정책은 다음과 같다.

- 하위 플랜 → 상위 플랜 업그레이드: 즉시 결제, 즉시 적용
- 기존 하위 플랜의 남은 기간은 뒤로 이월하지 않는다.
- 기존 하위 플랜의 남은 가치는 금액으로 환산하여 상위 플랜 결제 금액에서 차감한다.
- 업그레이드 후 상위 플랜을 취소하면 상위 플랜의 현재 결제 기간 종료 후 Free로 전환한다.
- 과거 하위 플랜 잔여 기간은 다시 복구하지 않는다.
- 상위 플랜 → 하위 플랜 다운그레이드: 기존처럼 현재 기간 종료 후 적용 예약
- 유료 플랜 → Free 변경: 기존처럼 현재 기간 종료 후 취소 예약

---

## 1. 현재 코드에서 확인해야 할 핵심 파일

우선 아래 파일을 중심으로 작업한다.

```text
backend/services/subscription.py
backend/services/subscription_renewal.py
backend/controllers/subscription.py
backend/routes/subscription.py
backend/schemas/subscription.py
backend/services/payment.py
backend/services/billing.py
frontend/src/**
```

특히 `backend/services/subscription.py` 안의 아래 함수가 핵심 변경 대상이다.

```python
def apply_upgrade_with_carryover(...):
    """Create the upgraded subscription now and carry the lower plan's remaining time after it."""
```

이 함수는 이름과 주석에서 알 수 있듯이 현재 하위 플랜 잔여 기간을 상위 플랜 뒤로 이월하는 구조다. 이 함수를 제거하거나, 새 정책에 맞는 함수로 대체한다.

---

## 2. 기존 방식과 변경 방식 비교

### 기존 방식: 기간 이월 방식

예시:

```text
현재 PRO 사용 중
PRO 잔여 기간 20일
STUDIO로 업그레이드
STUDIO 30일 즉시 시작
PRO 남은 20일을 STUDIO 종료 뒤로 이월
```

문제점:

- 사용자가 현재 어떤 플랜을 쓰는지 혼란스러워진다.
- `active` 구독이 여러 개 겹칠 가능성이 커진다.
- `resolve_current_plan()`이 plan_rank 기준으로 가장 높은 플랜을 고르더라도, 하위 플랜 잔여 기간이 뒤에 남아 있어 상태 해석이 복잡해진다.
- 취소, 재구독, 재업그레이드, 다운그레이드 예약이 섞이면 `current_period_end`, `next_billing_at`, `cancel_at_period_end`, `superseded_by_subscription_id`, `carried_over_days` 해석이 어려워진다.
- 사용자 화면에서 “남은 기간이 뒤로 이월되었습니다” 같은 문구가 필요해져 UX가 복잡해진다.

### 변경 방식: 금액 정산 방식

예시:

```text
현재 PRO 2,900원 / 30일 사용 중
10일 사용, 20일 남음
STUDIO 3,900원 / 30일로 업그레이드
PRO 잔여 가치 = 2,900 * 20 / 30 = 1,933원
STUDIO 결제 금액 = 3,900 - 1,933 = 1,967원
STUDIO 즉시 적용, 30일 새 기간 시작
기존 PRO 구독은 종료 처리
```

이 방식에서는 기존 하위 플랜의 남은 기간이 사라지는 것이 아니라, 업그레이드 결제 시 `할인/차감 금액`으로 정산된 것으로 처리한다.

---

## 3. 최종 정책 정의

### 3.1 업그레이드

조건:

```text
target_plan.plan_rank > current_plan.plan_rank
```

처리:

1. 현재 활성 구독 조회
2. 대상 상위 플랜 조회
3. 기존 구독의 잔여 시간 계산
4. 기존 구독의 잔여 금액 계산
5. 상위 플랜 금액에서 잔여 금액 차감
6. 차감 후 결제 금액이 0원 미만이면 0원으로 보정
7. 결제 성공 시 기존 하위 구독 종료 처리
8. 새 상위 구독 생성
9. `subscription_plan_changes`에 `upgrade`, `immediate`, `applied` 이력 저장
10. 화면에는 “기존 플랜의 남은 이용분이 결제 금액에 반영되었습니다.” 형태로 표시

### 3.2 다운그레이드

조건:

```text
target_plan.plan_rank < current_plan.plan_rank
```

처리:

- 즉시 결제하지 않는다.
- 현재 플랜은 `current_period_end`까지 유지한다.
- `subscription_plan_changes`에 `downgrade`, `period_end`, `scheduled`로 예약한다.
- 만료 시점에 스케줄러가 대상 하위 플랜을 결제하고 새 구독을 생성한다.

### 3.3 Free 변경

조건:

```text
target_plan.plan_code == "free"
```

처리:

- 즉시 Free로 바꾸지 않는다.
- 현재 플랜은 기간 종료일까지 유지한다.
- 현재 구독에 `auto_renew = false`, `cancel_at_period_end = true`를 설정한다.
- `subscription_plan_changes`에 `cancel_to_free`, `period_end`, `scheduled`로 저장한다.
- 기간 종료 후 Free fallback으로 처리한다.

### 3.4 같은 플랜

조건:

```text
target_plan.plan_rank == current_plan.plan_rank
```

처리:

- 플랜 변경 요청으로 처리하지 않는다.
- 필요하다면 “현재 이용 중인 플랜입니다.” 메시지를 반환한다.

---

## 4. DB 컬럼 정리 방향

현재 `subscriptions`에 다음과 같은 carryover 관련 컬럼이 있는 것으로 보인다.

```text
carried_over_days
superseded_by_subscription_id
original_period_end
upgraded_at
```

새 정책에서는 “기간 이월” 개념을 제거해야 한다.

### 4.1 컬럼을 바로 삭제하지 않는 경우

기존 데이터/쿼리 충돌을 줄이고 싶다면 컬럼은 유지하되, 업그레이드 로직에서 더 이상 사용하지 않는다.

권장 처리:

```text
carried_over_days = 0
superseded_by_subscription_id = new_subscription_id 또는 NULL
original_period_end = 기존 종료일 기록용으로만 사용 가능
upgraded_at = NOW()
```

단, `carried_over_days`는 사용자 화면에 노출하지 않는다.

### 4.2 컬럼을 정리하는 경우

마이그레이션 여유가 있다면 아래처럼 의미를 분리하는 편이 낫다.

#### `subscriptions`

```text
subscription_id
user_id
plan_id
status
current_period_start
current_period_end
next_billing_at
auto_renew
cancel_at_period_end
billing_status
last_payment_id
upgraded_at
ended_at
created_at
updated_at
```

#### `subscription_plan_changes`

업그레이드 정산 정보를 남길 컬럼이 필요하다.

```text
plan_change_id
user_id
from_plan_id
to_plan_id
from_subscription_id
to_subscription_id
change_type
apply_timing
status
requested_at
effective_at
applied_at
remaining_seconds
remaining_amount
target_plan_amount
discount_amount
charged_amount
from_subscription_original_end
created_at
updated_at
```

이미 `remaining_seconds`, `remaining_days`, `from_subscription_original_end` 계열 컬럼이 있다면 재사용한다. 다만 `from_subscription_new_end`처럼 이월 종료일을 의미하는 컬럼은 더 이상 사용하지 않는다.

---

## 5. 금액 정산 계산 규칙

### 5.1 기준 값

```text
current_plan.price_amount: 현재 플랜 가격
current_subscription.current_period_start: 현재 주기 시작일
current_subscription.current_period_end: 현재 주기 종료일
target_plan.price_amount: 대상 상위 플랜 가격
now: 업그레이드 요청 시점
```

### 5.2 계산식

```python
period_seconds = max(1, (current_period_end - current_period_start).total_seconds())
remaining_seconds = max(0, (current_period_end - now).total_seconds())
remaining_ratio = remaining_seconds / period_seconds
remaining_amount = floor(current_plan.price_amount * remaining_ratio)
target_amount = target_plan.price_amount
charged_amount = max(0, target_amount - remaining_amount)
discount_amount = target_amount - charged_amount
```

정책 선택:

- 원 단위 결제면 `floor` 권장
- 사용자에게 유리하게 하려면 `ceil` 가능
- 결제 금액이 0원이 될 수 있으므로 `charged_amount = 0` 케이스도 처리해야 한다.

권장:

```text
remaining_amount는 floor 처리
charged_amount는 max(0, target_amount - remaining_amount)
```

---

## 6. 백엔드 작업 상세

## STEP 1. `apply_upgrade_with_carryover` 제거 또는 교체

기존 함수:

```python
def apply_upgrade_with_carryover(...):
```

새 함수명 예시:

```python
def apply_upgrade_with_proration(
    db: Session,
    user_id: str,
    from_subscription_id=None,
    to_plan_id=None,
    payment_id=None,
    charged_amount=None,
):
```

또는 결제까지 함수 내부에서 처리한다면:

```python
def request_upgrade_with_proration(
    db: Session,
    user_id: str,
    to_plan_id: str,
    charge_client=None,
):
```

핵심은 더 이상 하위 구독의 `current_period_end`를 상위 구독 종료 뒤로 늘리지 않는 것이다.

삭제해야 할 기존 로직:

```sql
CAST(:upper_period_end AS timestamp) + (remaining_seconds || ' seconds')::interval AS carried_end
```

이 로직은 하위 플랜 잔여 기간을 상위 플랜 종료 뒤로 붙이는 핵심이므로 제거한다.

---

## STEP 2. 정산 금액 계산 함수 추가

`backend/services/subscription.py`에 유틸 함수를 추가한다.

```python
def calculate_proration_amount(current_plan, current_subscription, target_plan, now=None):
    """업그레이드 시 기존 플랜 잔여 가치를 계산한다."""
```

반환 예시:

```python
{
    "period_seconds": 2592000,
    "remaining_seconds": 1728000,
    "remaining_ratio": 0.666666,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967,
}
```

주의:

- `current_period_start`, `current_period_end`가 없으면 예외 처리한다.
- `target_plan.price_amount <= current_plan.price_amount`인 경우 업그레이드 정산으로 처리하지 않는다.
- `remaining_seconds <= 0`이면 잔여 금액은 0원으로 처리한다.

---

## STEP 3. 기존 하위 구독 종료 처리

업그레이드 결제 성공 후 기존 구독은 아래처럼 종료한다.

```sql
UPDATE subscriptions
SET
    status = 'ended',
    ended_at = NOW(),
    current_period_end = NOW(),
    next_billing_at = NULL,
    auto_renew = false,
    cancel_at_period_end = false,
    billing_status = 'superseded',
    upgraded_at = NOW(),
    superseded_by_subscription_id = :new_subscription_id,
    carried_over_days = 0,
    updated_at = NOW()
WHERE subscription_id = :from_subscription_id
  AND user_id = :user_id
  AND status = 'active';
```

`status = 'ended'` 값이 현재 enum/체크 제약에 없다면 기존 프로젝트에서 사용하는 종료 상태값을 확인해서 맞춘다. 예를 들어 `cancelled`, `expired`, `inactive`만 있다면 그중 가장 의미가 맞는 값을 사용한다.

중요:

- 기존 구독의 기간을 뒤로 늘리면 안 된다.
- 기존 구독의 `next_billing_at`은 반드시 `NULL`로 만든다.
- 기존 구독이 스케줄러에서 다시 결제되지 않게 해야 한다.

---

## STEP 4. 새 상위 구독 생성

상위 구독은 업그레이드 시점부터 새로 30일 생성한다.

```sql
INSERT INTO subscriptions (
    user_id,
    plan_id,
    status,
    started_at,
    ended_at,
    renew_at,
    current_period_start,
    current_period_end,
    next_billing_at,
    auto_renew,
    cancel_at_period_end,
    billing_status,
    last_payment_id,
    created_at,
    updated_at
)
VALUES (
    :user_id,
    :to_plan_id,
    'active',
    NOW(),
    NOW() + INTERVAL '30 days',
    NOW() + INTERVAL '30 days',
    NOW(),
    NOW() + INTERVAL '30 days',
    NOW() + INTERVAL '30 days',
    true,
    false,
    'paid',
    :payment_id,
    NOW(),
    NOW()
)
RETURNING subscription_id, current_period_start, current_period_end, next_billing_at;
```

---

## STEP 5. `subscription_plan_changes` 이력 저장

업그레이드 이력은 반드시 정산 정보와 함께 남긴다.

```sql
INSERT INTO subscription_plan_changes (
    user_id,
    subscription_id,
    from_plan_id,
    to_plan_id,
    from_subscription_id,
    to_subscription_id,
    change_type,
    apply_timing,
    status,
    remaining_seconds,
    remaining_amount,
    target_plan_amount,
    discount_amount,
    charged_amount,
    from_subscription_original_end,
    requested_at,
    effective_at,
    applied_at,
    created_at,
    updated_at
)
VALUES (
    :user_id,
    :to_subscription_id,
    :from_plan_id,
    :to_plan_id,
    :from_subscription_id,
    :to_subscription_id,
    'upgrade',
    'immediate',
    'applied',
    :remaining_seconds,
    :remaining_amount,
    :target_plan_amount,
    :discount_amount,
    :charged_amount,
    :from_subscription_original_end,
    NOW(),
    NOW(),
    NOW(),
    NOW(),
    NOW()
);
```

현재 테이블에 `remaining_amount`, `target_plan_amount`, `discount_amount`, `charged_amount` 컬럼이 없다면 마이그레이션을 추가한다.

---

## STEP 6. 결제 금액 연동

업그레이드 결제 시 Toss 결제 요청 금액은 `target_plan.price_amount`가 아니라 `charged_amount`여야 한다.

수정 전 개념:

```python
amount = target_plan.price_amount
```

수정 후:

```python
amount = proration["charged_amount"]
```

결제 이력에는 아래 값을 구분해서 저장하는 것이 좋다.

```text
payments.amount = 실제 결제 금액(charged_amount)
payments.total_amount = 대상 플랜 원래 금액(target_plan_amount)
payments.discount_amount = 차감 금액(discount_amount) 컬럼이 있으면 사용
payments.balance_amount = 실제 결제 금액 또는 PG 응답 기준 금액
```

만약 `payments` 테이블에 `discount_amount` 컬럼이 없다면 다음 둘 중 하나로 처리한다.

1. `subscription_plan_changes.discount_amount`에만 저장
2. `payments.raw_response` 또는 메타 JSON 컬럼이 있다면 정산 정보를 JSON으로 저장

---

## STEP 7. `request_plan_change` 흐름 수정

현재 `classify_plan_change()`는 업그레이드에 대해 다음을 반환한다.

```python
{
    "change_type": "upgrade",
    "apply_timing": "immediate",
    "requires_payment_now": True,
}
```

이 구조는 유지하되, 업그레이드 응답에 정산 정보를 포함한다.

예상 응답:

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "requires_payment_now": true,
  "current_plan": {...},
  "target_plan": {...},
  "current_subscription": {...},
  "proration": {
    "remaining_seconds": 1728000,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967
  }
}
```

프론트는 이 응답을 사용해 결제 전 확인 모달에 실제 결제 금액을 보여준다.

---

## STEP 8. renewal 스케줄러 영향 확인

`backend/services/subscription_renewal.py`의 갱신 대상 쿼리는 다음 조건을 사용한다.

```sql
s.status = 'active'
s.auto_renew = true
s.cancel_at_period_end = false
s.next_billing_at <= NOW()
p.price_amount > 0
```

업그레이드 후 기존 하위 구독이 다시 결제되지 않도록 아래 상태를 반드시 만족시킨다.

```text
status != 'active'
auto_renew = false
next_billing_at = NULL
```

새 상위 구독만 다음 결제 대상이 되어야 한다.

---

## STEP 9. 다운그레이드/Free 변경 로직은 유지

아래 함수들은 원칙적으로 유지한다.

```python
schedule_downgrade(...)
schedule_cancel_to_free(...)
resume_subscription(...)
cancel_scheduled_plan_change(...)
run_scheduled_downgrades(...)
```

단, 업그레이드 후 기존 하위 구독에 걸려 있던 `downgrade`, `cancel_to_free` 예약이 남아 있으면 충돌할 수 있다.

업그레이드 성공 시 기존 구독 기준 예약은 취소한다.

```sql
UPDATE subscription_plan_changes
SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW()
WHERE user_id = :user_id
  AND from_subscription_id = :from_subscription_id
  AND status = 'scheduled'
  AND change_type IN ('downgrade', 'cancel_to_free');
```

---

## 7. 프론트엔드 작업 상세

## STEP 10. “기간 이월” 문구 제거

삭제해야 할 문구 예시:

```text
남은 30일의 Studio 플랜 기간 뒤로 이월되었습니다.
```

변경 문구:

```text
기존 플랜의 남은 이용분이 결제 금액에 반영되었습니다.
```

또는 짧게:

```text
남은 이용분이 정산되었습니다.
```

---

## STEP 11. 업그레이드 결제 확인 UI 수정

업그레이드 모달 또는 안내 박스에는 아래 정보를 보여준다.

```text
STUDIO 플랜으로 즉시 변경됩니다.
기존 PRO 플랜의 남은 이용분이 결제 금액에서 차감됩니다.

플랜 금액: 3,900원
남은 이용분 차감: -1,933원
오늘 결제 금액: 1,967원
```

UI 문구 추천:

```text
즉시 변경
결제 완료 즉시 STUDIO 플랜이 적용됩니다.
기존 플랜의 남은 이용분은 결제 금액에 반영됩니다.
```

---

## STEP 12. 플랜 카드 상태 문구 수정

기존에 “이월”을 설명하던 박스는 제거한다.

업그레이드 완료 후 상위 플랜 카드:

```text
현재 플랜
STUDIO 플랜을 이용 중입니다.
다음 결제일: 2026.08.10
```

기존 하위 플랜 카드:

```text
이전 플랜
기존 PRO 플랜은 업그레이드 결제에 정산되었습니다.
```

가능하면 이전 플랜 카드에는 정산 안내를 길게 노출하지 않는다. 결제 내역 또는 구독 변경 내역에서만 자세히 보여주는 편이 깔끔하다.

---

## STEP 13. 구독 취소 화면 문구 수정

업그레이드 후 취소 시, 이전 하위 플랜 기간이 복구되지 않는 정책을 명확히 한다.

추천 문구:

```text
구독을 취소해도 현재 결제 기간 종료일까지 STUDIO 플랜을 사용할 수 있습니다.
기간 종료 후 Free 플랜으로 전환됩니다.
```

사용하지 말아야 할 문구:

```text
이전 PRO 플랜의 남은 기간으로 전환됩니다.
```

---

## 8. API 응답 예시

### 8.1 업그레이드 분류 응답

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "requires_payment_now": true,
  "current_plan": {
    "plan_code": "pro",
    "plan_name": "PRO",
    "price_amount": 2900,
    "plan_rank": 1
  },
  "target_plan": {
    "plan_code": "studio",
    "plan_name": "STUDIO",
    "price_amount": 3900,
    "plan_rank": 2
  },
  "proration": {
    "remaining_seconds": 1728000,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967
  }
}
```

### 8.2 업그레이드 적용 완료 응답

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "status": "applied",
  "from_subscription_id": "...",
  "to_subscription_id": "...",
  "plan_change_id": "...",
  "payment_id": "...",
  "proration": {
    "remaining_amount": 1933,
    "discount_amount": 1933,
    "charged_amount": 1967
  },
  "message": "기존 플랜의 남은 이용분이 결제 금액에 반영되었습니다."
}
```

---

## 9. 테스트 시나리오

## STEP 14. 단위 테스트

### 테스트 1. PRO → STUDIO 업그레이드 정산

조건:

```text
PRO 가격: 2,900원
STUDIO 가격: 3,900원
PRO 기간: 30일
PRO 잔여: 20일
```

기대 결과:

```text
remaining_amount ≈ 1,933원
charged_amount ≈ 1,967원
새 STUDIO 구독 즉시 active
기존 PRO 구독 ended 또는 inactive
기존 PRO next_billing_at = NULL
carried_over_days = 0
```

### 테스트 2. 업그레이드 후 취소

조건:

```text
PRO → STUDIO 업그레이드 완료
STUDIO 취소 요청
```

기대 결과:

```text
STUDIO cancel_at_period_end = true
STUDIO current_period_end까지 유지
기간 종료 후 Free fallback
기존 PRO 기간 복구 없음
```

### 테스트 3. STUDIO → PRO 다운그레이드

조건:

```text
STUDIO active
PRO로 변경 요청
```

기대 결과:

```text
즉시 결제 없음
subscription_plan_changes에 downgrade scheduled 생성
현재 STUDIO는 current_period_end까지 유지
```

### 테스트 4. STUDIO → Free 변경

조건:

```text
STUDIO active
Free로 변경 요청
```

기대 결과:

```text
즉시 Free 전환 없음
cancel_at_period_end = true
auto_renew = false
subscription_plan_changes에 cancel_to_free scheduled 생성
```

### 테스트 5. 업그레이드 후 renewal 대상 확인

조건:

```text
PRO → STUDIO 업그레이드 완료
renewal scheduler 실행
```

기대 결과:

```text
기존 PRO는 결제 대상 아님
새 STUDIO만 next_billing_at 기준으로 결제 대상
```

---

## 10. 작업 체크리스트

- [ ] `apply_upgrade_with_carryover` 함수 제거 또는 `apply_upgrade_with_proration`으로 교체
- [ ] 하위 플랜 잔여 기간을 상위 플랜 뒤로 붙이는 SQL 제거
- [ ] 정산 금액 계산 함수 추가
- [ ] 업그레이드 결제 금액을 `target_plan.price_amount`가 아닌 `charged_amount`로 변경
- [ ] 업그레이드 성공 시 기존 구독 종료 처리
- [ ] 기존 구독의 `next_billing_at = NULL`, `auto_renew = false` 처리
- [ ] 새 상위 구독은 즉시 30일 active 생성
- [ ] `subscription_plan_changes`에 정산 이력 저장
- [ ] 업그레이드 성공 시 기존 예약 다운그레이드/취소 예약 취소
- [ ] 프론트에서 “기간 이월” 문구 제거
- [ ] 프론트 결제 확인 모달에 정산 금액 표시
- [ ] 업그레이드 후 취소 시 이전 하위 플랜 기간 복구 문구 제거
- [ ] renewal scheduler에서 기존 하위 구독이 재결제되지 않는지 테스트
- [ ] PRO → STUDIO, STUDIO → PRO, STUDIO → Free 테스트 완료

---

## 11. Codex 작업 지시문

아래 내용을 Codex에 그대로 전달해서 작업한다.

```text
현재 sedeok 브랜치의 구독 업그레이드 로직은 하위 플랜의 잔여 기간을 상위 플랜 종료 뒤로 이월하는 carryover 방식으로 되어 있다. 이 방식을 제거하고 일반적인 구독 정책에 맞게 “잔여 기간 금액 정산 방식”으로 변경해줘.

정책은 다음과 같다.

1. 하위 플랜에서 상위 플랜으로 업그레이드할 때는 즉시 결제 + 즉시 적용한다.
2. 기존 하위 플랜의 남은 기간은 상위 플랜 종료 뒤로 이월하지 않는다.
3. 기존 하위 플랜의 남은 가치는 금액으로 환산해서 상위 플랜 결제 금액에서 차감한다.
4. 상위 플랜 결제 금액은 target_plan.price_amount - remaining_amount 로 계산하고, 0원 미만이면 0원으로 보정한다.
5. 결제 성공 후 기존 하위 구독은 ended/inactive 처리하고, next_billing_at은 NULL, auto_renew는 false로 변경한다.
6. 새 상위 구독은 NOW()부터 30일 active로 생성한다.
7. subscription_plan_changes에는 upgrade/immediate/applied 이력을 남기고, remaining_seconds, remaining_amount, target_plan_amount, discount_amount, charged_amount를 저장한다. 컬럼이 없으면 마이그레이션을 추가한다.
8. 기존 apply_upgrade_with_carryover 함수와 하위 구독 current_period_end를 상위 구독 종료 뒤로 늘리는 SQL을 제거하거나 새 함수 apply_upgrade_with_proration으로 교체한다.
9. 다운그레이드와 Free 변경은 기존처럼 period_end 예약 방식으로 유지한다.
10. 업그레이드 성공 시 기존 구독에 걸린 scheduled downgrade/cancel_to_free 예약은 cancelled 처리한다.
11. renewal scheduler에서 기존 하위 구독이 다시 결제되지 않도록 status, auto_renew, next_billing_at 조건을 점검한다.
12. 프론트엔드의 “남은 기간이 뒤로 이월되었습니다” 문구를 제거하고, “기존 플랜의 남은 이용분이 결제 금액에 반영되었습니다.”로 변경한다.
13. 업그레이드 결제 확인 UI에는 플랜 금액, 남은 이용분 차감, 오늘 결제 금액을 보여준다.
14. 업그레이드 후 구독 취소 시 이전 하위 플랜 기간이 복구된다는 표현이 나오지 않게 한다. 취소 문구는 “현재 결제 기간 종료 후 Free 플랜으로 전환됩니다.”로 통일한다.
15. 관련 테스트를 추가하거나 기존 테스트를 수정해서 PRO→STUDIO 업그레이드, STUDIO→PRO 다운그레이드, STUDIO→Free 취소, 업그레이드 후 취소, renewal scheduler 충돌 여부를 검증한다.

주의할 점:
- 기간 이월 개념을 완전히 제거해야 한다.
- carried_over_days는 더 이상 사용자 화면에 노출하지 않는다.
- 기존 하위 구독의 current_period_end를 미래로 늘리면 안 된다.
- 실제 결제 금액은 반드시 정산 후 charged_amount를 사용해야 한다.
```
