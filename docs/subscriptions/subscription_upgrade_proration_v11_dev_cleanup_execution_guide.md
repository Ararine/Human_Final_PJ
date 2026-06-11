# 구독 업그레이드 정산 정책 v11 개발환경 정리 실행 가이드

대상 기준:

- 실제 DB 설계: `docs/db/Garim_DB_Design_final_clean_v11.xlsx`
- 초기화 SQL: `docker/database/init/0_init_table_v11.sql`
- 기존 실행 가이드: `docs/subscriptions/subscription_upgrade_proration_v11_execution_guide.md`

## 0. 이 문서의 차이점

이 프로젝트는 아직 운영 데이터 마이그레이션을 고려해야 하는 단계가 아니라 개발 단계다. 따라서 구독 정책 변경으로 의미가 사라진 carryover 컬럼, API 필드, 화면 문구, 테스트 기대값은 호환용으로 남기지 않고 삭제한다.

기존 `subscription_upgrade_proration_v11_execution_guide.md`에는 아래 내용이 포함되어 있었다.

- carryover 로직 제거
- 정산 금액 컬럼 추가
- 사용자/관리자 화면에서 이월 문구 제거
- `apply_upgrade_with_carryover()` 교체

하지만 아래 부분은 개발환경 정리 원칙으로는 부족했다.

- carryover 컬럼을 "기존 호환용"으로 남기는 선택지가 있음
- `superseded_by_subscription_id`를 기록용으로 남기는 선택지가 있음
- `remaining_days`, `from_subscription_new_end`를 기존 호환 컬럼으로 남기는 선택지가 있음
- 테스트와 관리자 API에서 carryover 응답 필드를 완전히 삭제해야 한다는 기준이 약함

이 보완판에서는 위 선택지를 제거하고, 삭제 기준을 기본값으로 삼는다.

## 1. 최종 정책

업그레이드:

- 하위 플랜에서 상위 플랜으로 변경하면 즉시 결제하고 즉시 적용한다.
- 기존 하위 플랜의 잔여 기간은 상위 플랜 뒤로 이월하지 않는다.
- 기존 하위 플랜의 잔여 가치는 금액으로 환산해 업그레이드 결제 금액에서 차감한다.
- 기존 하위 구독은 즉시 `cancelled` 처리하고 현재 권한/자동결제 대상에서 제외한다.
- 새 상위 구독은 즉시 `active`로 생성한다.

다운그레이드:

- 즉시 결제하지 않는다.
- 현재 구독 기간 종료 시점에 적용되도록 예약한다.

Free 변경:

- 즉시 Free로 바꾸지 않는다.
- 현재 유료 구독 기간 종료 후 Free로 전환되도록 예약한다.

업그레이드 후 취소:

- 현재 상위 플랜 기간 종료 후 Free로 전환한다.
- 과거 하위 플랜의 남은 기간은 복구하지 않는다.

## 2. 삭제 우선 원칙

개발환경에서는 아래 원칙을 따른다.

1. 새 정책에서 의미가 사라진 DB 컬럼은 삭제한다.
2. 삭제한 컬럼을 읽거나 쓰는 SQL은 모두 제거한다.
3. 삭제한 필드를 API 응답에 남기지 않는다.
4. 삭제한 필드를 프론트 상태나 UI 조건에 남기지 않는다.
5. 삭제한 필드를 기대하는 테스트는 수정하거나 삭제한다.
6. 과거 정책 설명 문구는 관리자 화면에도 남기지 않는다.
7. 호환을 위해 `0`이나 `NULL`을 계속 저장하는 방식은 쓰지 않는다.

예외:

- 과거 문서 파일에 남은 정책 설명은 보존 가능하다.
- 단, 현재 실행 문서와 현재 코드에서는 carryover 정책을 참조하지 않는다.

## 3. 삭제할 DB 컬럼과 제약

### 3.1 `subscriptions`에서 삭제

삭제 대상:

```text
upgraded_at
superseded_by_subscription_id
carried_over_days
original_period_end
```

삭제 이유:

- `upgraded_at`: 업그레이드 이력은 `subscription_plan_changes.applied_at`으로 추적한다.
- `superseded_by_subscription_id`: 상위 구독이 하위 구독을 대체한다는 carryover 모델의 흔적이다.
- `carried_over_days`: 잔여 기간 이월 정책 자체가 사라진다.
- `original_period_end`: 기존 구독 원래 종료일은 `subscription_plan_changes.from_subscription_original_end`에 남긴다.

함께 삭제할 제약/인덱스:

```text
fk_subscriptions_superseded_by
ck_subscriptions_carried_over_days_non_negative
idx_subscriptions_superseded_by
```

SQL 예시:

```sql
DROP INDEX IF EXISTS idx_subscriptions_superseded_by;

ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS fk_subscriptions_superseded_by,
    DROP CONSTRAINT IF EXISTS ck_subscriptions_carried_over_days_non_negative;

ALTER TABLE subscriptions
    DROP COLUMN IF EXISTS upgraded_at,
    DROP COLUMN IF EXISTS superseded_by_subscription_id,
    DROP COLUMN IF EXISTS carried_over_days,
    DROP COLUMN IF EXISTS original_period_end;
```

### 3.2 `subscription_plan_changes`에서 삭제

삭제 대상:

```text
remaining_days
from_subscription_new_end
```

삭제 이유:

- `remaining_days`: 이월 일수 표시용 컬럼이다. 정산 계산에는 `remaining_seconds`와 금액 컬럼을 사용한다.
- `from_subscription_new_end`: 상위 플랜 종료 뒤로 이어 붙인 새 종료일을 의미한다. 새 정책에서는 존재하지 않는 개념이다.

함께 삭제할 제약:

```text
chk_subscription_plan_changes_remaining_days
```

SQL 예시:

```sql
ALTER TABLE subscription_plan_changes
    DROP CONSTRAINT IF EXISTS chk_subscription_plan_changes_remaining_days;

ALTER TABLE subscription_plan_changes
    DROP COLUMN IF EXISTS remaining_days,
    DROP COLUMN IF EXISTS from_subscription_new_end;
```

### 3.3 `subscription_plan_changes`에 추가

추가 대상:

```text
remaining_amount
target_plan_amount
discount_amount
charged_amount
```

SQL 예시:

```sql
ALTER TABLE subscription_plan_changes
    ADD COLUMN IF NOT EXISTS remaining_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS target_plan_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS discount_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS charged_amount integer NOT NULL DEFAULT 0;
```

체크 제약:

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_remaining_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_remaining_amount CHECK (remaining_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_target_plan_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_target_plan_amount CHECK (target_plan_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_discount_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_discount_amount CHECK (discount_amount >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_subscription_plan_changes_charged_amount') THEN
        ALTER TABLE subscription_plan_changes
            ADD CONSTRAINT chk_subscription_plan_changes_charged_amount CHECK (charged_amount >= 0);
    END IF;
END $$;
```

### 3.4 엑셀 설계 문서 반영

대상:

```text
docs/db/Garim_DB_Design_final_clean_v11.xlsx
```

수정:

- `11_subscriptions` 시트에서 삭제 대상 4개 컬럼 제거
- `39_subscription_plan_changes` 시트에서 `remaining_days`, `from_subscription_new_end` 제거
- `39_subscription_plan_changes` 시트에 정산 금액 컬럼 4개 추가
- `40_v11_change_summary`에서 carryover 추적 추가 내용을 제거하고 정산 방식으로 수정

`40_v11_change_summary` 권장 문구:

```text
Change: 업그레이드는 잔여 기간 이월이 아니라 잔여 이용분 금액 정산 방식으로 처리한다.
Change: subscriptions의 carryover 추적 컬럼을 제거했다.
Change: subscription_plan_changes에 remaining_amount, target_plan_amount, discount_amount, charged_amount를 추가했다.
```

### 3.5 초기화 SQL 주석과 요약 문구 삭제

대상:

```text
docker/database/init/0_init_table_v11.sql
```

삭제 또는 수정할 문구:

```text
Upgrade is charged/applied immediately and lower-plan remaining period is carried over.
carry-over tracking
이월 일수
상위 구독 ID - 이 구독보다 우선 적용되는 상위 구독
상위 플랜 종료 후 이어서 적용될 하위 플랜 잔여 일수
from_subscription_new_end
```

대체 문구:

```text
Upgrade is charged/applied immediately with remaining-value proration.
Upgrade proration amounts are stored in subscription_plan_changes.
```

개발 DB를 초기화해서 쓰는 환경이면 별도 마이그레이션 파일보다 `0_init_table_v11.sql`의 최종 스키마를 깨끗하게 수정하는 편이 낫다. 이미 로컬 DB가 떠 있다면 docker volume 또는 DB 데이터를 재생성하는 절차를 별도로 실행한다.

## 4. 삭제할 백엔드 로직

### STEP 1. `apply_upgrade_with_carryover()` 삭제

대상:

```text
backend/services/subscription.py
backend/services/payment.py
backend/tests/test_subscription.py
backend/tests/test_payment.py
```

삭제:

```python
apply_upgrade_with_carryover
```

대체:

```python
apply_upgrade_with_proration
```

삭제할 SQL 개념:

```sql
CAST(:upper_period_end AS timestamp) + (remaining_seconds || ' seconds')::interval AS carried_end
```

삭제할 반환 필드:

```text
carried_over_days
lower_subscription.current_period_end를 상위 구독 종료 뒤로 늘린 값
```

### STEP 2. 구독 payload에서 carryover 필드 삭제

대상:

```text
backend/services/subscription.py
backend/schemas/subscription.py
backend/controllers/subscription.py
backend/routes/subscription.py
```

삭제:

```text
carried_over_days
superseded_by_subscription_id
```

`resolve_current_plan()` 조회 컬럼에서도 삭제한다.

기존 현재 플랜 계산은 아래 기준만 사용한다.

```sql
s.status = 'active'
s.current_period_start <= NOW()
s.current_period_end > NOW()
ORDER BY p.plan_rank DESC
```

Pydantic schema나 controller 응답 모델에 carryover 필드가 있다면 함께 제거한다. API 문서나 프론트 타입에서 아래 필드가 계속 보이면 삭제가 덜 된 것이다.

```text
carried_over_days
superseded_by_subscription_id
carried_over_subscription
original_period_end
from_subscription_new_end
remaining_days
```

### STEP 3. 업그레이드 정산 함수 추가

대상:

```text
backend/services/subscription.py
```

추가:

```python
def calculate_upgrade_proration(current_plan, current_subscription, target_plan, now=None):
    """업그레이드 시 기존 플랜의 잔여 이용 가치를 금액으로 계산한다."""
```

계산:

```text
period_seconds = max(1, current_period_end - current_period_start)
remaining_seconds = max(0, current_period_end - now)
remaining_amount = floor(current_plan.price_amount * remaining_seconds / period_seconds)
target_plan_amount = target_plan.price_amount
charged_amount = max(0, target_plan_amount - remaining_amount)
discount_amount = target_plan_amount - charged_amount
```

반환:

```json
{
  "period_seconds": 2592000,
  "remaining_seconds": 1728000,
  "remaining_amount": 1933,
  "target_plan_amount": 3900,
  "discount_amount": 1933,
  "charged_amount": 1967
}
```

`remaining_days`는 반환하지 않는다. 화면과 DB에서 이월 일수 개념을 제거하기 때문이다.

### STEP 4. `classify_plan_change()` 응답 확장

업그레이드일 때만 `proration`을 포함한다.

```json
{
  "change_type": "upgrade",
  "apply_timing": "immediate",
  "requires_payment_now": true,
  "proration": {
    "remaining_seconds": 1728000,
    "remaining_amount": 1933,
    "target_plan_amount": 3900,
    "discount_amount": 1933,
    "charged_amount": 1967
  }
}
```

다운그레이드와 Free 변경은 기존 예약 방식을 유지하되 carryover 필드는 포함하지 않는다.

### STEP 5. `apply_upgrade_with_proration()` 구현

처리 순서:

1. 현재 하위 구독을 조회한다.
2. 대상 상위 플랜을 조회한다.
3. 정산 금액을 계산하거나 결제 전 계산값과 일치하는지 검증한다.
4. 새 상위 구독을 `active`로 생성한다.
5. 기존 하위 구독을 `cancelled`로 즉시 종료한다.
6. 기존 하위 구독의 예약 다운그레이드/Free 변경을 `cancelled`로 변경한다.
7. `subscription_plan_changes`에 정산 이력을 저장한다.
8. 생성된 `plan_change_id`를 반환한다.

기존 하위 구독 업데이트:

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
    updated_at = NOW()
WHERE subscription_id = :from_subscription_id
  AND user_id = :user_id
  AND status = 'active';
```

주의:

- 삭제한 컬럼인 `upgraded_at`, `superseded_by_subscription_id`, `carried_over_days`, `original_period_end`를 쓰지 않는다.
- 하위 구독의 `current_period_end`를 미래로 늘리지 않는다.
- 하위 구독은 renewal 대상에서 빠져야 한다.

플랜 변경 이력 저장:

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
)
RETURNING plan_change_id;
```

### STEP 6. 결제 전 정산 금액 적용

대상:

```text
backend/services/payment.py
```

현재 위험:

- `confirm_billing_payment()`가 업그레이드 여부를 결제 승인 후 판단한다.
- 이 구조에서는 상위 플랜 정가가 청구될 수 있다.

수정:

1. Toss billing charge 전에 `classify_plan_change()`를 호출한다.
2. 업그레이드이면 `proration.charged_amount`를 결제 금액으로 사용한다.
3. `payments.amount`도 `charged_amount`로 생성한다.
4. 결제 성공 후 `apply_upgrade_with_proration()`을 호출한다.
5. `payments.plan_change_id`에 생성된 plan change를 연결한다.

0원 업그레이드:

- `charged_amount = 0`이면 Toss를 호출하지 않는다.
- `subscription_plan_changes`에는 반드시 이력을 남긴다.
- 결제 이력을 남길 경우 `payments.status`는 실제 DB 체크 제약과 코드에서 합의한 성공 상태값을 사용한다.

### STEP 7. `create_temp_order()` 경로 정리

대상:

```text
backend/services/payment.py
frontend/src/pages/garim/Payment.jsx
```

현재 검증:

```python
if product["price_amount"] != amount:
    raise ValueError("Requested amount does not match product price.")
```

업그레이드 결제를 기존 `/payment` 경로로 계속 처리하면 정산 금액이 정가와 달라서 막힌다.

개발환경 권장 정리:

- 업그레이드 전용 주문 생성 API를 만든다.
- 프론트에서 금액을 계산해 보내지 않는다.
- 백엔드가 현재 구독과 대상 플랜을 기준으로 `charged_amount`를 계산하고 주문을 만든다.
- 기존 정가 검증은 일반 신규 구독/크레딧 결제에만 유지한다.

## 5. 삭제할 관리자 API와 프론트 로직

### STEP 8. 사용자 결제 정보 API에서 carryover 제거

대상:

```text
backend/services/payment.py
```

삭제:

```text
carried_over_subscription 조회 SQL
carried_over_subscription 응답 필드
carried_over_days 응답 필드
superseded_by_subscription_id 기반 조회
```

대체:

- 최근 업그레이드 정산 이력이 필요하면 `subscription_plan_changes`에서 `change_type = 'upgrade'`인 최신 applied 이력을 조회한다.
- 응답 필드 이름은 `latest_upgrade_proration`처럼 정산 의미가 드러나게 한다.

예시:

```json
{
  "latest_upgrade_proration": {
    "from_plan_name": "Pro",
    "to_plan_name": "Studio",
    "remaining_amount": 1933,
    "discount_amount": 1933,
    "charged_amount": 1967,
    "applied_at": "2026-06-11T10:00:00"
  }
}
```

### STEP 9. 관리자 구독 API에서 carryover 제거

대상:

```text
backend/services/admin.py
backend/tests/test_admin_subscription_check.py
```

삭제:

```text
carried_over_subscription
carried_over_days
superseded_by_subscription_id
대체 구독 플랜
이월 기간
```

대체:

- 구독 상세의 "플랜 변경 이력"에 정산 금액을 표시한다.
- active subscription 목록에는 현재 활성 구독만 표시한다.
- cancelled 된 과거 하위 구독은 active 목록에 포함하지 않는다.

관리자 상세 권장 컬럼:

```text
변경 유형
상태
이전 플랜
변경 플랜
대상 플랜 금액
잔여 이용분 차감
실제 청구 금액
적용 시점
```

### STEP 10. Pricing 화면에서 carryover 제거

대상:

```text
frontend/src/pages/garim/Pricing.jsx
```

삭제:

```text
paymentInfo.carried_over_subscription
isCarriedPlan
이전 플랜 배지
업그레이드로 종료됨 배지
남은 N일이 현재 플랜 기간 뒤로 이월되었습니다.
```

대체:

- 현재 플랜과 예약 변경만 표시한다.
- 업그레이드 정산 안내는 결제 확인 UI에서 표시한다.

### STEP 11. Billing 화면에서 carryover 제거

대상:

```text
frontend/src/pages/garim/Billing.jsx
```

삭제:

```text
carriedOver
업그레이드 후 이월된 하위 플랜 섹션
잔여 기간 N일이 현재 플랜 종료 이후까지 이어집니다.
```

대체:

```text
업그레이드 정산
기존 Pro 플랜의 남은 이용분 1,933원이 Studio 결제 금액에서 차감되었습니다.
실제 결제 금액: 1,967원
```

이 섹션은 `latest_upgrade_proration` 응답이 있을 때만 표시한다.

### STEP 12. AdminSubscriptions 화면에서 carryover 제거

대상:

```text
frontend/src/pages/garim/AdminSubscriptions.jsx
frontend/src/css/garim-pages/AdminSubscriptions.css
```

삭제:

```text
이월 기간
대체 구독 플랜
getSupersededPlanName
carried_over_days 표시
superseded_by_subscription_id 표시
```

대체:

- 활성 구독 목록에는 플랜, 종료 일시, 자동결제, 취소 예약, 결제 상태만 표시한다.
- 플랜 변경 이력에 정산 금액 컬럼을 추가한다.

## 6. 테스트 정리

### STEP 13. 삭제해야 할 테스트 기대값

대상:

```text
backend/tests/test_subscription.py
backend/tests/test_payment.py
backend/tests/test_admin_subscription_check.py
tests/test_frontend_analysis_progress_static.py
```

삭제 또는 수정할 기대값:

```text
apply_upgrade_with_carryover
carried_over_days
superseded_by_subscription_id
original_period_end
from_subscription_new_end
carried_over_subscription
대체 구독 플랜
이월 기간
남은 N일이 ... 뒤로 이월
```

### STEP 14. 추가해야 할 테스트

정산 계산:

```text
Pro 2,900원, 30일 기간 중 20일 남음
Studio 3,900원 업그레이드
remaining_amount = 1933
charged_amount = 1967
```

업그레이드 적용:

```text
새 Studio 구독 active 생성
기존 Pro 구독 cancelled 처리
기존 Pro next_billing_at = NULL
기존 Pro auto_renew = false
기존 Pro current_period_end <= now
subscription_plan_changes에 정산 금액 저장
```

결제:

```text
Toss 요청 금액 = charged_amount
payments.amount = charged_amount
payments.plan_change_id 연결
charged_amount = 0이면 Toss 호출 없음
```

renewal:

```text
cancelled 된 기존 Pro는 renewal 대상 아님
새 Studio만 renewal 대상
```

프론트 정적 검사:

```text
Pricing/Billing/AdminSubscriptions에서 이월/대체 구독 문구 없음
업그레이드 확인 UI에 대상 플랜 금액, 차감 금액, 오늘 결제 금액 표시
```

## 7. 실행 순서

1. `docker/database/init/0_init_table_v11.sql`에서 carryover 컬럼, 제약, 인덱스 삭제
2. `subscription_plan_changes` 정산 금액 컬럼 추가
3. `docs/db/Garim_DB_Design_final_clean_v11.xlsx` 시트와 v11 변경 요약 수정
4. `backend/services/subscription.py`에서 carryover payload와 함수 삭제
5. `calculate_upgrade_proration()` 추가
6. `apply_upgrade_with_proration()` 구현
7. `backend/services/payment.py`에서 결제 전 정산 금액 적용
8. 0원 업그레이드 처리
9. `create_temp_order()` 또는 업그레이드 전용 주문 API 정리
10. 사용자 결제 정보 API에서 carryover 응답 삭제
11. 관리자 API에서 carryover 응답 삭제
12. Pricing/Billing/AdminSubscriptions 화면에서 carryover UI 삭제
13. 기존 carryover 테스트 삭제 또는 정산 테스트로 교체
14. 전체 검색으로 남은 흔적 확인
15. 백엔드/프론트 테스트 실행

## 8. 최종 검색 체크

아래 검색어가 현재 로직, API 응답, 화면 코드에서 나오면 다시 확인한다.

```powershell
rg -n "apply_upgrade_with_carryover|carryover|carried_over|superseded_by_subscription_id|carried_over_days|original_period_end|from_subscription_new_end|remaining_days|이월|대체 구독|업그레이드로 종료됨" backend frontend tests docker/database/init docs/subscriptions
```

허용 가능한 결과:

- 과거 정책 문서의 설명
- 이 보완 가이드의 삭제 대상 목록

허용하면 안 되는 결과:

- 현재 실행 코드에서 컬럼을 SELECT/INSERT/UPDATE 하는 부분
- API 응답에 carryover 필드를 넣는 부분
- 프론트에서 carryover 필드를 읽는 부분
- 테스트가 carryover 필드를 기대하는 부분
- v11 초기화 SQL이 carryover 컬럼을 생성하는 부분

## 9. 최종 체크리스트

- [ ] `subscriptions.upgraded_at` 삭제
- [ ] `subscriptions.superseded_by_subscription_id` 삭제
- [ ] `subscriptions.carried_over_days` 삭제
- [ ] `subscriptions.original_period_end` 삭제
- [ ] `idx_subscriptions_superseded_by` 삭제
- [ ] `fk_subscriptions_superseded_by` 삭제
- [ ] `ck_subscriptions_carried_over_days_non_negative` 삭제
- [ ] `subscription_plan_changes.remaining_days` 삭제
- [ ] `subscription_plan_changes.from_subscription_new_end` 삭제
- [ ] `subscription_plan_changes.remaining_amount` 추가
- [ ] `subscription_plan_changes.target_plan_amount` 추가
- [ ] `subscription_plan_changes.discount_amount` 추가
- [ ] `subscription_plan_changes.charged_amount` 추가
- [ ] `apply_upgrade_with_carryover()` 삭제
- [ ] `apply_upgrade_with_proration()` 추가
- [ ] 하위 구독 기간을 미래로 늘리는 SQL 삭제
- [ ] 업그레이드 결제 금액을 `charged_amount`로 변경
- [ ] 0원 업그레이드 처리
- [ ] 사용자 API carryover 응답 삭제
- [ ] 관리자 API carryover 응답 삭제
- [ ] Pricing carryover UI 삭제
- [ ] Billing carryover UI 삭제
- [ ] AdminSubscriptions carryover UI 삭제
- [ ] carryover 테스트 기대값 삭제
- [ ] 정산 방식 테스트 추가
