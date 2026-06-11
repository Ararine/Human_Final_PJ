# 구독 업그레이드 정산 정책 v11 실행 가이드

대상 기준:

- 실제 DB 설계: `docs/db/Garim_DB_Design_final_clean_v11.xlsx`
- 초기화 SQL: `docker/database/init/0_init_table_v11.sql`
- 기존 정책 초안: `docs/subscriptions/subscription_upgrade_proration_change_guide.md`

## 0. 목적

기존 업그레이드 정책은 하위 플랜의 잔여 기간을 상위 플랜 종료 뒤로 이어 붙이는 `carryover` 방식이다. 이 문서는 v11 실제 테이블과 현재 코드 흐름에 맞춰, 해당 방식을 제거하고 잔여 이용분을 금액으로 정산하는 방식으로 바꾸기 위한 실행 절차를 정리한다.

변경 후 원칙:

- 하위 플랜에서 상위 플랜으로 업그레이드하면 즉시 결제하고 즉시 적용한다.
- 기존 하위 플랜의 남은 기간은 상위 플랜 뒤로 이월하지 않는다.
- 기존 하위 플랜의 남은 가치는 금액으로 환산해 업그레이드 결제 금액에서 차감한다.
- 업그레이드 후 상위 플랜을 취소하면 현재 상위 플랜 기간 종료 후 Free로 전환한다.
- 과거 하위 플랜 잔여 기간은 복구하지 않는다.
- 상위 플랜에서 하위 플랜으로 다운그레이드하거나 유료 플랜에서 Free로 변경하는 흐름은 현재처럼 기간 종료 예약 방식으로 유지한다.

## 1. 현재 v11 스키마 기준 주의사항

문서나 코드 예시를 그대로 옮기기 전에 아래 제약을 반드시 맞춘다.

### 1.1 `subscriptions.status`

v11 기준 허용값:

```text
active, past_due, cancelled, expired
```

따라서 업그레이드로 종료되는 하위 구독에 `ended`를 쓰면 안 된다.

권장값:

```text
status = 'cancelled'
```

의미:

- 사용자가 환불 취소를 한 것은 아니지만, 이 구독은 업그레이드 정산으로 즉시 더 이상 현재 권한 계산 대상이 아니다.
- `resolve_current_plan()`과 renewal scheduler가 모두 `status = 'active'`를 기준으로 동작하므로, `cancelled` 처리하면 기존 하위 구독이 다시 현재 플랜이나 자동결제 대상이 되지 않는다.

### 1.2 `subscriptions.billing_status`

v11 SQL 체크 제약 기준 허용값:

```text
ready, paid, failed, billing_key_missing, retry_scheduled, cancelled, expired
```

따라서 `superseded`를 쓰면 안 된다.

권장값:

```text
billing_status = 'cancelled'
```

### 1.3 기존 carryover 컬럼

현재 v11에는 carryover 추적 컬럼이 존재한다.

```text
subscriptions.upgraded_at
subscriptions.superseded_by_subscription_id
subscriptions.carried_over_days
subscriptions.original_period_end
subscription_plan_changes.remaining_days
subscription_plan_changes.from_subscription_new_end
```

새 정책에서는 사용자 권한과 화면에서 이월 개념을 제거한다.

권장 처리:

- `carried_over_days`는 항상 `0`으로 저장한다.
- `from_subscription_new_end`는 더 이상 쓰지 않는다.
- `original_period_end` 또는 `from_subscription_original_end`는 감사용 기록으로만 사용할 수 있다.
- `superseded_by_subscription_id`는 새 상위 구독 연결 기록으로 유지 가능하지만, 화면에서는 "대체 구독"이나 "이월"로 표현하지 않는다.

### 1.4 `payments.status` 불일치 점검

v11 엑셀의 `payments.status` 설명은 아래 값을 기준으로 한다.

```text
ready, paid, failed, cancelled, refunded
```

현재 코드와 테스트 일부는 `success` 또는 `DONE`도 사용한다. 업그레이드 정산 작업을 하면서 결제 상태값을 새로 추가하거나 0원 내부 결제를 만들기 전에, 먼저 실제 DB 체크 제약과 코드 사용값을 맞춘다.

권장 방향:

- DB 제약을 v11 설계대로 유지한다면 결제 성공 상태는 `paid`로 통일한다.
- 기존 코드 호환 때문에 `success`를 유지해야 한다면 SQL 체크 제약, 테스트, 관리자 필터, 결제 이력 조회 조건을 함께 맞춘다.
- 새 업그레이드 로직에서는 특정 문자열을 임의로 추가하지 않는다.

## 2. 추가해야 할 DB 컬럼

정산 금액을 플랜 변경 이력에 남기기 위해 `subscription_plan_changes`에 아래 컬럼을 추가한다.

```sql
ALTER TABLE subscription_plan_changes
    ADD COLUMN IF NOT EXISTS remaining_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS target_plan_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS discount_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS charged_amount integer NOT NULL DEFAULT 0;
```

권장 체크 제약:

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_remaining_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_remaining_amount
            CHECK (remaining_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_target_plan_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_target_plan_amount
            CHECK (target_plan_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_discount_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_discount_amount
            CHECK (discount_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_charged_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_charged_amount
            CHECK (charged_amount >= 0);
    END IF;
END $$;
```

컬럼 역할:

```text
remaining_amount: 기존 하위 플랜의 잔여 이용 가치
target_plan_amount: 대상 상위 플랜의 원래 결제 금액
discount_amount: 업그레이드 결제에서 차감된 금액
charged_amount: 실제 청구 금액
```

`payments`에는 이미 `amount`, `total_amount`, `balance_amount`, `plan_change_id`가 있으므로, 정산 상세 금액은 `subscription_plan_changes`에 남기고 결제 행은 `plan_change_id`로 연결한다.

## 3. 정산 계산 규칙

업그레이드 조건:

```text
target_plan.plan_rank > current_plan.plan_rank
target_plan.plan_code != 'free'
current_subscription exists
```

계산 기준:

```text
period_seconds = max(1, current_period_end - current_period_start)
remaining_seconds = max(0, current_period_end - now)
remaining_ratio = remaining_seconds / period_seconds
remaining_amount = floor(current_plan.price_amount * remaining_ratio)
target_plan_amount = target_plan.price_amount
charged_amount = max(0, target_plan_amount - remaining_amount)
discount_amount = target_plan_amount - charged_amount
```

주의:

- 원 단위 결제이므로 기본은 `floor`를 사용한다.
- `current_period_start` 또는 `current_period_end`가 없으면 업그레이드 정산을 진행하지 않는다.
- `remaining_seconds <= 0`이면 `remaining_amount = 0`이다.
- `charged_amount = 0`이 될 수 있다. 이 경우 PG 결제 요청을 보낼 수 없으므로 내부 적용 흐름을 별도로 처리해야 한다.

## 4. 백엔드 실행 단계

### STEP 1. DB 마이그레이션 반영

대상:

```text
docker/database/init/0_init_table_v11.sql
docs/db/Garim_DB_Design_final_clean_v11.xlsx
```

작업:

1. `subscription_plan_changes`에 정산 금액 컬럼 4개를 추가한다.
2. 컬럼 설명과 체크 제약을 추가한다.
3. v11 change summary에 "업그레이드 carryover 제거 및 금액 정산 컬럼 추가" 내용을 남긴다.
4. `from_subscription_new_end`, `remaining_days` 설명은 이월 중심 표현에서 감사용/기존 호환용 표현으로 바꾼다.

권장 설명:

```text
remaining_days: 기존 호환용 잔여 일수. 새 정책에서는 권한 이월에 사용하지 않는다.
from_subscription_new_end: 기존 carryover 호환 컬럼. 새 정책에서는 NULL 유지.
```

### STEP 2. 정산 계산 함수 추가

대상:

```text
backend/services/subscription.py
```

추가 함수 예시:

```python
def calculate_upgrade_proration(current_plan, current_subscription, target_plan, now=None):
    """업그레이드 시 기존 플랜 잔여 가치를 금액으로 계산한다."""
```

반환값:

```json
{
  "period_seconds": 2592000,
  "remaining_seconds": 1728000,
  "remaining_days": 20,
  "remaining_amount": 1933,
  "target_plan_amount": 3900,
  "discount_amount": 1933,
  "charged_amount": 1967
}
```

함수 내부 검증:

- 대상 플랜이 현재 플랜보다 높은 rank인지 확인한다.
- 현재 구독 기간 값이 존재하는지 확인한다.
- 가격은 `int`로 보정한다.
- 모든 금액은 0 이상으로 보정한다.

### STEP 3. `classify_plan_change()` 응답 확장

대상:

```text
backend/services/subscription.py
```

현재 업그레이드 응답은 변경 유형만 알려준다. 업그레이드이면 정산 정보를 함께 반환하도록 확장한다.

응답 예시:

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "requires_payment_now": true,
  "current_plan": {},
  "target_plan": {},
  "current_subscription": {},
  "proration": {
    "remaining_seconds": 1728000,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967
  }
}
```

다운그레이드, Free 변경, 같은 플랜 응답은 기존 구조를 유지한다.

### STEP 4. `apply_upgrade_with_carryover()` 제거 또는 교체

대상:

```text
backend/services/subscription.py
```

기존 함수:

```python
def apply_upgrade_with_carryover(...):
```

새 함수:

```python
def apply_upgrade_with_proration(
    db,
    user_id,
    from_subscription_id,
    to_plan_id,
    payment_id=None,
    billing_key_id=None,
    proration=None,
):
```

반드시 제거할 SQL 개념:

```sql
CAST(:upper_period_end AS timestamp) + (remaining_seconds || ' seconds')::interval AS carried_end
```

새 처리 순서:

1. 현재 하위 구독을 조회한다.
2. 대상 상위 플랜을 조회한다.
3. 정산 정보를 계산하거나 전달받은 `proration`을 검증한다.
4. 새 상위 구독을 즉시 생성한다.
5. 기존 하위 구독을 즉시 비활성 처리한다.
6. 기존 하위 구독에 걸린 예약 변경을 취소한다.
7. `subscription_plan_changes`에 `upgrade/immediate/applied` 이력을 정산 금액과 함께 저장한다.

### STEP 5. 새 상위 구독 생성

새 구독 기간은 하드코딩된 30일 대신 가능하면 `plans.billing_period_days`를 사용한다.

권장 SQL 개념:

```sql
NOW() + (COALESCE(:billing_period_days, 30) || ' days')::interval
```

필수 저장값:

```text
status = 'active'
current_period_start = NOW()
current_period_end = NOW() + billing_period_days
next_billing_at = current_period_end
auto_renew = true
cancel_at_period_end = false
billing_status = 'paid'
last_payment_id = payment_id
billing_key_id = billing_key_id
```

### STEP 6. 기존 하위 구독 종료 처리

v11 제약에 맞는 값만 사용한다.

권장 SQL:

```sql
UPDATE subscriptions
SET
    status = 'cancelled',
    ended_at = NOW(),
    renew_at = NULL,
    current_period_end = NOW(),
    next_billing_at = NULL,
    auto_renew = false,
    cancel_at_period_end = false,
    cancelled_at = NOW(),
    billing_status = 'cancelled',
    upgraded_at = NOW(),
    superseded_by_subscription_id = :new_subscription_id,
    carried_over_days = 0,
    original_period_end = COALESCE(original_period_end, :from_subscription_original_end),
    updated_at = NOW()
WHERE subscription_id = :from_subscription_id
  AND user_id = :user_id
  AND status = 'active';
```

중요:

- `current_period_end`를 미래로 늘리지 않는다.
- `next_billing_at`은 반드시 `NULL`로 만든다.
- `auto_renew`는 반드시 `false`로 만든다.
- `cancel_at_period_end`는 `false`로 둔다. 이미 즉시 종료된 구독이므로 기간 종료 예약 상태로 남기지 않는다.

### STEP 7. 기존 예약 변경 취소

업그레이드 성공 후 기존 하위 구독 기준 예약을 취소한다.

```sql
UPDATE subscription_plan_changes
SET
    status = 'cancelled',
    cancelled_at = NOW(),
    updated_at = NOW()
WHERE user_id = :user_id
  AND from_subscription_id = :from_subscription_id
  AND status = 'scheduled'
  AND change_type IN ('downgrade', 'cancel_to_free');
```

### STEP 8. 플랜 변경 이력 저장

`subscription_plan_changes`에 정산 정보를 저장한다.

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
    remaining_days,
    remaining_seconds,
    remaining_amount,
    target_plan_amount,
    discount_amount,
    charged_amount,
    from_subscription_original_end,
    from_subscription_new_end,
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
    :remaining_days,
    :remaining_seconds,
    :remaining_amount,
    :target_plan_amount,
    :discount_amount,
    :charged_amount,
    :from_subscription_original_end,
    NULL,
    NOW(),
    NOW(),
    NOW(),
    NOW(),
    NOW()
)
RETURNING plan_change_id;
```

### STEP 9. 결제 금액 계산 위치 수정

대상:

```text
backend/services/payment.py
```

현재 위험 지점:

- `confirm_billing_payment()`에서 `amount = plan["price_amount"]`를 먼저 정한다.
- Toss 자동결제 승인 후에 업그레이드 여부를 판단한다.
- 이 구조에서는 업그레이드 정산 금액이 아니라 상위 플랜 정가가 청구된다.

수정 원칙:

1. Toss 청구 전에 현재 플랜 변경 유형을 먼저 판단한다.
2. 업그레이드이면 `classification["proration"]["charged_amount"]`를 청구 금액으로 사용한다.
3. `payments.amount`도 청구 금액으로 생성한다.
4. 결제 성공 후 `apply_upgrade_with_proration()`을 호출한다.
5. 생성된 `plan_change_id`를 `payments.plan_change_id`에 연결한다.

흐름 예시:

```text
plan 조회
classify_plan_change()
upgrade이면 proration.charged_amount 계산
payments ready 생성(amount = charged_amount)
Toss billing charge(amount = charged_amount)
결제 성공
apply_upgrade_with_proration()
payments.subscription_id, payments.plan_change_id 갱신
```

### STEP 10. 0원 업그레이드 처리

`charged_amount = 0`이면 Toss 결제를 호출하지 않는다.

권장 처리:

1. `payments` 행을 만들지 않거나, 만들 경우 `amount = 0`과 내부 결제용 `pg_provider` 값을 명확히 정한다.
2. 결제 성공 상태값은 STEP 1.4에서 정리한 실제 허용값을 사용한다.
3. PG 거래 ID가 없음을 허용한다.
4. `apply_upgrade_with_proration()`은 결제 ID가 없어도 동작할 수 있어야 한다.
5. 사용자 응답에는 "남은 이용분 정산으로 추가 결제 없이 업그레이드되었습니다."를 반환한다.

주의:

- 현재 `payments.pg_provider` 제약이 강하지 않다면 `internal` 사용이 가능하지만, 운영 정책상 결제 이력으로 남길지 먼저 결정한다.
- 감사 추적을 위해서는 0원 결제도 `payments` 또는 `subscription_plan_changes` 중 하나에는 반드시 남겨야 한다.

### STEP 11. `create_temp_order()` 경로 점검

대상:

```text
backend/services/payment.py
frontend/src/pages/garim/Payment.jsx
```

현재 `create_temp_order()`는 구독 상품 결제 금액이 플랜 정가와 다르면 오류를 낸다.

```python
if product["price_amount"] != amount:
    raise ValueError("Requested amount does not match product price.")
```

업그레이드 결제를 이 경로로 계속 쓴다면 아래 중 하나를 선택한다.

권장안:

- 업그레이드 전용 API를 만들고, 백엔드가 정산 금액으로 임시 주문을 생성한다.
- 프론트가 임의 금액을 보내지 않도록 한다.

대안:

- `product_type = subscription_upgrade` 같은 별도 타입을 두고 정산 금액 검증을 서버에서 수행한다.

피해야 할 방식:

- 프론트에서 계산한 `charged_amount`를 그대로 신뢰해 `price_amount != amount` 예외만 우회하는 방식.

### STEP 12. renewal scheduler 확인

대상:

```text
backend/services/subscription_renewal.py
```

renewal 대상 조건은 현재 방향이 맞다.

```sql
s.status = 'active'
s.auto_renew = true
s.cancel_at_period_end = false
s.next_billing_at <= NOW()
p.price_amount > 0
```

업그레이드 후 기존 하위 구독은 아래 상태여야 한다.

```text
status = 'cancelled'
auto_renew = false
next_billing_at = NULL
```

새 상위 구독만 renewal 대상이 되어야 한다.

### STEP 13. 관리자 API carryover 제거

대상:

```text
backend/services/admin.py
backend/tests/test_admin_subscription_check.py
frontend/src/pages/garim/AdminSubscriptions.jsx
frontend/src/css/garim-pages/AdminSubscriptions.css
```

제거 또는 변경할 개념:

```text
carried_over_subscription
carried_over_days 화면 노출
대체 구독 플랜
이월 기간
superseded_by_subscription_id를 사용자/관리자에게 대체 플랜처럼 설명하는 UI
```

대체 표현:

```text
정산된 이전 구독
업그레이드 정산 완료
이전 플랜 잔여 이용분은 업그레이드 결제 금액에 반영됨
```

관리자 상세에는 필요한 경우 `subscription_plan_changes`의 정산 금액을 표시한다.

권장 표시:

```text
대상 플랜 금액
잔여 이용분 차감
실제 청구 금액
기존 구독 원래 종료일
```

## 5. 프론트엔드 실행 단계

### STEP 14. Pricing 화면 carryover 문구 제거

대상:

```text
frontend/src/pages/garim/Pricing.jsx
```

제거할 문구/개념:

```text
이전 플랜
업그레이드로 종료됨
남은 N일이 현재 플랜 기간 뒤로 이월되었습니다.
carried_over_subscription 기반 안내 박스
```

대체 문구:

```text
기존 플랜의 남은 이용분이 업그레이드 결제 금액에 반영되었습니다.
```

가능하면 Pricing 카드에는 과거 정산 안내를 길게 노출하지 않는다. 상세는 결제/구독 관리 또는 결제 이력에서 보여준다.

### STEP 15. Billing 화면 carryover 섹션 제거

대상:

```text
frontend/src/pages/garim/Billing.jsx
```

제거할 섹션:

```text
업그레이드 후 이월된 하위 플랜
잔여 기간 N일이 현재 플랜 종료 이후까지 이어집니다.
```

대체 섹션이 필요하면 최근 `upgrade/applied` 이력을 표시한다.

예시:

```text
업그레이드 정산
기존 Pro 플랜의 남은 이용분 1,933원이 Studio 결제 금액에서 차감되었습니다.
실제 결제 금액: 1,967원
```

### STEP 16. 구독 취소 문구 통일

취소 예약 문구:

```text
구독을 취소해도 현재 결제 기간 종료일까지 현재 플랜을 사용할 수 있습니다.
기간 종료 후 Free 플랜으로 전환됩니다.
```

사용 금지 문구:

```text
이전 플랜의 남은 기간으로 전환됩니다.
이월된 기간을 사용할 수 있습니다.
대체 구독 플랜으로 돌아갑니다.
```

### STEP 17. 업그레이드 결제 확인 UI

업그레이드 결제 전에는 정산 금액을 보여준다.

필수 표시:

```text
대상 플랜 금액
남은 이용분 차감
오늘 결제 금액
결제 완료 즉시 대상 플랜 적용
```

예시:

```text
Studio 플랜으로 즉시 변경됩니다.
기존 Pro 플랜의 남은 이용분이 결제 금액에서 차감됩니다.

플랜 금액: 3,900원
남은 이용분 차감: -1,933원
오늘 결제 금액: 1,967원
```

## 6. API 응답 보완

### 6.1 플랜 변경 분류 응답

업그레이드 응답:

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "requires_payment_now": true,
  "current_plan": {
    "plan_code": "pro",
    "plan_name": "Pro",
    "price_amount": 2900,
    "plan_rank": 10
  },
  "target_plan": {
    "plan_code": "studio",
    "plan_name": "Studio",
    "price_amount": 3900,
    "plan_rank": 20
  },
  "current_subscription": {
    "subscription_id": "...",
    "current_period_start": "2026-06-01T00:00:00",
    "current_period_end": "2026-07-01T00:00:00"
  },
  "proration": {
    "remaining_seconds": 1728000,
    "remaining_days": 20,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967
  }
}
```

### 6.2 업그레이드 적용 완료 응답

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

## 7. 테스트 계획

### STEP 18. 정산 계산 단위 테스트

대상:

```text
backend/tests/test_subscription.py
```

케이스:

```text
PRO 2,900원 / 30일
10일 사용, 20일 남음
STUDIO 3,900원 업그레이드
```

기대:

```text
remaining_seconds = 20일 상당 초
remaining_amount = 1933
target_plan_amount = 3900
discount_amount = 1933
charged_amount = 1967
```

### STEP 19. 업그레이드 적용 테스트

검증:

```text
새 Studio 구독 active 생성
기존 Pro 구독 cancelled 처리
기존 Pro current_period_end <= now
기존 Pro next_billing_at = NULL
기존 Pro auto_renew = false
기존 Pro carried_over_days = 0
subscription_plan_changes upgrade/immediate/applied 생성
remaining_amount, target_plan_amount, discount_amount, charged_amount 저장
from_subscription_new_end = NULL
```

### STEP 20. 결제 금액 테스트

대상:

```text
backend/tests/test_payment.py
```

검증:

```text
업그레이드 결제 시 Toss 요청 금액은 target_plan.price_amount가 아니라 charged_amount
payments.amount = charged_amount
payments.plan_change_id가 생성된 plan_change_id와 연결됨
0원 업그레이드는 Toss 호출 없이 적용됨
payments.status는 실제 DB 체크 제약과 일치하는 성공 상태값을 사용함
```

### STEP 21. 다운그레이드 유지 테스트

검증:

```text
Studio -> Pro 요청은 즉시 결제하지 않음
subscription_plan_changes downgrade/period_end/scheduled 생성
현재 Studio는 current_period_end까지 active 유지
```

### STEP 22. Free 변경 유지 테스트

검증:

```text
Studio -> Free 요청은 즉시 Free 전환하지 않음
현재 Studio cancel_at_period_end = true
현재 Studio auto_renew = false
subscription_plan_changes cancel_to_free/period_end/scheduled 생성
```

### STEP 23. 업그레이드 후 취소 테스트

검증:

```text
Pro -> Studio 업그레이드 완료
Studio 구독 취소 예약
Studio는 current_period_end까지 유지
기간 종료 후 Free fallback
기존 Pro 기간 복구 없음
```

### STEP 24. renewal scheduler 충돌 테스트

검증:

```text
업그레이드로 cancelled 처리된 Pro는 renewal 대상 아님
새 Studio만 next_billing_at 기준으로 renewal 대상
```

### STEP 25. 화면/정적 테스트

검증:

```text
Pricing/Billing/AdminSubscriptions에 "이월", "대체 구독 플랜", "남은 기간이 뒤로" 문구가 남지 않음
업그레이드 결제 확인 UI에 대상 플랜 금액, 차감 금액, 오늘 결제 금액이 표시됨
취소 문구는 기간 종료 후 Free 전환으로 통일됨
```

## 8. 작업 체크리스트

- [ ] v11 SQL에 `subscription_plan_changes` 정산 금액 컬럼 추가
- [ ] v11 엑셀 설계 문서에 정산 금액 컬럼 반영
- [ ] `apply_upgrade_with_carryover()` 제거 또는 `apply_upgrade_with_proration()`으로 교체
- [ ] 하위 구독 종료 시 `status = 'cancelled'`, `billing_status = 'cancelled'` 사용
- [ ] 하위 구독 `current_period_end`를 미래로 늘리는 SQL 제거
- [ ] 하위 구독 `next_billing_at = NULL`, `auto_renew = false`, `carried_over_days = 0` 처리
- [ ] `calculate_upgrade_proration()` 추가
- [ ] `classify_plan_change()` 업그레이드 응답에 `proration` 포함
- [ ] Toss 청구 전에 정산 금액 계산
- [ ] 업그레이드 청구 금액을 `charged_amount`로 변경
- [ ] `charged_amount = 0` 처리 정책 구현
- [ ] `payments.plan_change_id` 연결
- [ ] 기존 하위 구독의 scheduled downgrade/cancel_to_free 예약 취소
- [ ] renewal scheduler에서 기존 하위 구독 제외 검증
- [ ] Pricing carryover 문구 제거
- [ ] Billing carryover 섹션 제거
- [ ] AdminSubscriptions carryover/대체 구독 UI 제거 또는 정산 이력 UI로 변경
- [ ] 관리자 API carryover 응답 제거 또는 정산 이력 응답으로 변경
- [ ] 업그레이드/다운그레이드/Free/취소/renewal 테스트 추가

## 9. 구현 순서 권장안

1. DB 컬럼 추가와 문서 스키마 정리
2. 정산 계산 함수와 단위 테스트 작성
3. `classify_plan_change()` 응답 확장
4. `apply_upgrade_with_proration()` 구현
5. 결제 흐름에서 Toss 청구 전 정산 금액 적용
6. 0원 업그레이드 처리
7. renewal scheduler 충돌 테스트
8. 사용자 화면 carryover 제거
9. 관리자 화면/API carryover 제거
10. 전체 테스트 실행 및 문구 검색

마지막 검색 명령 예시:

```powershell
rg -n "carryover|carried_over|이월|대체 구독|남은 기간.*뒤|superseded" backend frontend docs/subscriptions docker/database/init
```

검색 결과 중 DB 호환 컬럼명이나 과거 마이그레이션 설명을 제외하고, 사용자/관리자 화면 및 현재 비즈니스 로직에 이월 정책이 남아 있으면 제거한다.
