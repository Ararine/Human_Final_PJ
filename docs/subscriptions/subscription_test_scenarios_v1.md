# GARIM 30일 자동결제 구독 테스트 시나리오 v1

## 0. 문서 목적

이 문서는 `docs/subscriptions/subscription_30day_auto_renewal_final_v2_with_model_guide.md` 기준으로 Codex가 구현한 구독 기능을 검증하기 위한 테스트 시나리오 문서다.

검증 범위는 다음과 같다.

- Free / Pro / Studio 플랜 우선순위
- 30일 유료 구독 생성
- 현재 플랜 계산 로직
- 업그레이드 즉시 결제 + 즉시 적용
- 업그레이드 시 하위 플랜 잔여 기간 이월
- 업그레이드 후 하위 플랜 중복 자동결제 방지
- 다운그레이드 예약
- 다운그레이드 예약 적용
- 다운그레이드 예약 취소
- Free 변경 / 구독 취소 예약
- 구독 취소 철회
- 자동결제 성공 / 실패
- 모든 유료 플랜 만료 후 Free 적용
- 사용자 화면 표시
- 관리자 화면 표시
- 기존 결제/플랜/크레딧 데이터 보존

---

## 1. 테스트 전제

### 1.1 플랜 전제

`plans` 테이블에는 최소 아래 플랜이 존재해야 한다.

| plan_code | plan_name | plan_rank | price | active |
|---|---:|---:|---:|---:|
| free | Free | 0 | 0 | true |
| pro | Pro | 10 | 유료 금액 | true |
| studio | Studio | 20 | 유료 금액 | true |

검증 포인트:

- `plan_rank`가 `Free < Pro < Studio` 순서인지 확인한다.
- `active=false` 플랜은 신규 구독/변경 대상에서 제외되는지 확인한다.
- 기존 seed 데이터가 삭제되지 않았는지 확인한다.

### 1.2 주요 테이블 전제

아래 테이블 또는 동등한 구조가 존재해야 한다.

- `plans`
- `subscriptions`
- `payments`
- `billing_keys`
- `subscription_billing_attempts`
- `subscription_plan_changes`

### 1.3 현재 플랜 계산 원칙

현재 플랜은 `users.plan_id` 같은 단일 컬럼에 고정 저장하지 않는다.

현재 플랜은 다음 조건을 만족하는 active subscription 중 `plans.plan_rank`가 가장 높은 플랜으로 계산되어야 한다.

```sql
SELECT s.*, p.*
FROM subscriptions s
JOIN plans p ON p.plan_id = s.plan_id
WHERE s.user_id = :user_id
  AND s.status = 'active'
  AND s.current_period_start <= now()
  AND s.current_period_end > now()
ORDER BY p.plan_rank DESC
LIMIT 1;
```

조회 결과가 없으면 Free가 적용되어야 한다.

### 1.4 API 후보

프로젝트 실제 라우트가 다르면 현재 구현된 라우트명으로 치환한다.

사용자 API 후보:

```http
GET  /subscriptions/me
GET  /plans/current
POST /subscriptions/checkout
POST /subscriptions/change-plan
POST /subscriptions/{subscription_id}/cancel
POST /subscriptions/{subscription_id}/resume
POST /subscriptions/plan-changes/{plan_change_id}/cancel
```

관리자 API 후보:

```http
GET /admin/subscriptions
GET /admin/subscriptions/{subscription_id}
GET /admin/subscriptions/{subscription_id}/billing-attempts
GET /admin/subscriptions/{subscription_id}/plan-changes
```

내부 서비스 함수 후보:

```text
resolve_current_plan(user_id)
classify_plan_change(user_id, to_plan_id)
create_or_extend_subscription(user_id, plan_id, payment_id)
apply_upgrade_with_carryover(user_id, from_subscription_id, to_plan_id, payment_id)
schedule_downgrade(user_id, from_subscription_id, to_plan_id)
cancel_to_free(user_id, subscription_id)
resume_subscription(subscription_id)
cancel_scheduled_plan_change(plan_change_id)
run_subscription_renewals()
run_scheduled_downgrades()
charge_subscription_with_billing_key(subscription_id)
```

---

## 2. 테스트 환경 준비

### 2.1 권장 테스트 방식

Codex는 아래 순서로 테스트를 구성한다.

1. 기존 테스트 구조 확인
2. 구독 서비스 단위 테스트 추가
3. API 통합 테스트 추가
4. 스케줄러 함수 테스트 추가
5. 사용자/관리자 응답 shape 테스트 추가
6. 테스트 결과 리포트 작성

### 2.2 테스트 데이터 원칙

테스트는 운영 seed 데이터를 직접 오염시키지 않아야 한다.

권장 방식:

- 테스트 전용 user 생성
- 테스트 전용 billing_key 생성
- 테스트 전용 payment 생성
- 테스트 후 rollback 또는 teardown
- 시간 의존 테스트는 `freezegun`, mock clock, DB timestamp 주입 중 프로젝트에 맞는 방식을 사용

### 2.3 테스트 사용자 예시

| 구분 | 이메일 | 목적 |
|---|---|---|
| user_free | test_free_subscription@example.com | Free 신규 결제 테스트 |
| user_pro | test_pro_subscription@example.com | Pro 업그레이드/취소 테스트 |
| user_studio | test_studio_subscription@example.com | Studio 다운그레이드/Free 변경 테스트 |
| user_billing_fail | test_billing_fail_subscription@example.com | 자동결제 실패 테스트 |

### 2.4 결제 Mock 원칙

실제 Toss 결제를 호출하지 않는 테스트 모드를 준비한다.

Mock 결제 성공 응답 예시:

```json
{
  "payment_id": "pay_test_success_001",
  "status": "DONE",
  "amount": 2900,
  "method": "billing",
  "approved_at": "2026-06-10T00:00:00"
}
```

Mock 결제 실패 응답 예시:

```json
{
  "payment_id": null,
  "status": "FAILED",
  "error_code": "BILLING_KEY_INVALID",
  "error_message": "테스트용 Billing Key 실패"
}
```

주의:

- billing_key 원문은 로그/API 응답/리포트에 노출하지 않는다.
- 테스트 로그에도 마스킹된 카드 정보만 남긴다.

---

## 3. 테스트 시나리오 요약표

| ID | 시나리오 | 핵심 검증 |
|---|---|---|
| SUB-001 | Free → Pro 신규 구독 | 30일 Pro 생성, 현재 플랜 Pro |
| SUB-002 | Free → Studio 신규 구독 | 30일 Studio 생성, 현재 플랜 Studio |
| SUB-003 | 같은 플랜 재결제/연장 | 같은 플랜 active 구독 30일 연장 |
| SUB-004 | Pro → Studio 업그레이드 | Studio 즉시 적용, Pro 잔여 기간 이월 |
| SUB-005 | 업그레이드 후 중복 자동결제 방지 | Pro auto_renew=false, Studio만 자동결제 대상 |
| SUB-006 | Studio → Pro 다운그레이드 예약 | 즉시 결제 없음, scheduled 기록 |
| SUB-007 | 다운그레이드 예약 적용 성공 | effective_at 도래 후 Pro 결제/생성 |
| SUB-008 | 다운그레이드 예약 적용 실패 | failed/retry 기록, billing_attempt 저장 |
| SUB-009 | 다운그레이드 예약 취소 | plan_change cancelled, Studio 유지 |
| SUB-010 | Studio → Free 변경 | 취소 예약, 기간 종료까지 Studio 유지 |
| SUB-011 | 구독 취소 철회 | auto_renew 복구, cancel_at_period_end=false |
| SUB-012 | 만료 후 취소 철회 불가 | period_end 이후 resume 불가 |
| SUB-013 | 자동결제 성공 | 기간 30일 연장, next_billing_at 갱신 |
| SUB-014 | 자동결제 실패 | billing_attempt failed 저장 |
| SUB-015 | 모든 유료 플랜 만료 후 Free | 현재 플랜 Free |
| SUB-016 | 현재 플랜 rank 우선순위 | Pro/Studio 동시 active 시 Studio 우선 |
| SUB-017 | 사용자 화면 응답 | 현재 플랜/예약/이월/취소 상태 표시 |
| SUB-018 | 관리자 화면 응답 | active 구독/변경 이력/결제 실패 조회 |
| SUB-019 | 비활성 플랜 변경 차단 | active=false 플랜 변경 불가 |
| SUB-020 | 다른 사용자 예약 취소 차단 | 본인 plan_change만 취소 가능 |
| SUB-021 | 기존 데이터 보존 | 기존 plans/credit_plans/admin 데이터 삭제 없음 |

---

## 4. 상세 테스트 시나리오

## SUB-001. Free → Pro 신규 구독

### 목적

Free 사용자가 Pro를 결제하면 30일 Pro 구독이 생성되고 현재 플랜이 Pro로 계산되는지 확인한다.

### Given

- 사용자 `user_free`는 유효한 유료 구독이 없다.
- Pro 플랜은 `active=true`, `plan_rank=10`이다.
- Mock 결제는 성공으로 설정한다.

### When

```http
POST /subscriptions/checkout
Content-Type: application/json

{
  "plan_code": "pro",
  "billing_key_id": "billing_key_success"
}
```

또는 실제 구현이 `change-plan`으로 통합되어 있으면:

```http
POST /subscriptions/change-plan
Content-Type: application/json

{
  "to_plan_code": "pro"
}
```

### Then - API 검증

- 응답 상태는 200 또는 201이다.
- `current_plan.plan_code = "pro"`이다.
- `current_subscription.status = "active"`이다.
- `current_subscription.current_period_start <= now()`이다.
- `current_subscription.current_period_end = current_period_start + 30 days`이다.
- `auto_renew = true`이다.
- `cancel_at_period_end = false`이다.

### Then - DB 검증

```sql
SELECT s.*, p.plan_code, p.plan_rank
FROM subscriptions s
JOIN plans p ON p.plan_id = s.plan_id
WHERE s.user_id = :user_id
ORDER BY s.created_at DESC;
```

검증:

- Pro subscription 1건 생성
- `status='active'`
- `current_period_end`가 시작일 기준 30일 뒤
- payments에 결제 성공 이력 1건 생성

---

## SUB-002. Free → Studio 신규 구독

### 목적

Free 사용자가 Studio를 결제하면 30일 Studio 구독이 생성되고 현재 플랜이 Studio로 계산되는지 확인한다.

### Given

- 사용자 `user_free`는 유효한 유료 구독이 없다.
- Studio 플랜은 `active=true`, `plan_rank=20`이다.
- Mock 결제는 성공으로 설정한다.

### When

```http
POST /subscriptions/checkout
Content-Type: application/json

{
  "plan_code": "studio",
  "billing_key_id": "billing_key_success"
}
```

### Then

- 현재 플랜은 Studio이다.
- Studio subscription이 active로 생성된다.
- `current_period_end = current_period_start + 30 days`이다.
- `next_billing_at = current_period_end` 또는 구현 정책에 맞는 다음 결제일이다.
- payments에 Studio 금액 결제 성공 이력이 남는다.

---

## SUB-003. 같은 플랜 재결제/연장

### 목적

같은 플랜의 active 구독이 이미 있을 때 새 결제가 들어오면 중복 구독을 무분별하게 만들지 않고 기존 구독 기간을 30일 연장하는지 확인한다.

### Given

- 사용자 `user_pro`는 Pro active 구독을 가지고 있다.
- Pro 구독 기간은 `2026-06-01 00:00:00` ~ `2026-07-01 00:00:00`이다.
- Mock 결제는 성공으로 설정한다.

### When

- 같은 사용자로 Pro 결제를 다시 요청한다.

### Then

- 현재 플랜은 Pro이다.
- Pro 구독의 `current_period_end`가 기존 종료일 기준 30일 연장된다.
- 기대값: `2026-07-31 00:00:00`
- 결제 성공 이력은 추가된다.
- 다른 플랜 subscription은 삭제/수정되지 않는다.

---

## SUB-004. Pro → Studio 업그레이드 + Pro 잔여 기간 이월

### 목적

Pro가 남아 있는 사용자가 Studio로 업그레이드하면 Studio가 즉시 적용되고, 남은 Pro 기간은 Studio 종료 후로 이월되는지 확인한다.

### Given

- 기준 시각: `2026-06-10 00:00:00`
- 사용자 `user_pro`는 Pro active 구독을 가지고 있다.
- Pro 구독 기간: `2026-06-01 00:00:00` ~ `2026-06-30 00:00:00`
- Pro 잔여 기간: 20일
- Studio 플랜은 `plan_rank=20`이고 Pro보다 높다.
- Mock 결제는 성공으로 설정한다.

### When

```http
POST /subscriptions/change-plan
Content-Type: application/json

{
  "to_plan_code": "studio"
}
```

### Then - API 검증

- 응답에 `change_type = "upgrade"`가 포함된다.
- 현재 플랜은 Studio이다.
- Studio subscription이 즉시 생성된다.
- Studio 기간은 `2026-06-10 00:00:00` ~ `2026-07-10 00:00:00`이다.
- Pro 잔여 20일은 Studio 종료 후로 이월된다.
- Pro 최종 `current_period_end = 2026-07-30 00:00:00`이다.

### Then - DB 검증

Pro subscription:

- `status = 'active'` 유지
- `auto_renew = false`
- `cancel_at_period_end = true`
- `upgraded_at` 저장
- `superseded_by_subscription_id`가 Studio subscription을 참조
- `carried_over_days = 20`
- `original_period_end = 2026-06-30 00:00:00`
- `current_period_end = 2026-07-30 00:00:00`

Studio subscription:

- `status = 'active'`
- `auto_renew = true`
- `cancel_at_period_end = false`
- `current_period_start = 2026-06-10 00:00:00`
- `current_period_end = 2026-07-10 00:00:00`

subscription_plan_changes:

- `change_type = 'upgrade'`
- `status = 'applied'`
- `from_plan = pro`
- `to_plan = studio`
- `from_subscription_id`는 기존 Pro
- `to_subscription_id`는 신규 Studio

---

## SUB-005. 업그레이드 후 하위 플랜 중복 자동결제 방지

### 목적

Pro → Studio 업그레이드 이후 기존 Pro가 자동결제 대상에서 제외되어 중복 결제가 발생하지 않는지 확인한다.

### Given

- SUB-004 완료 상태
- Pro subscription은 Studio에 의해 superseded 된 상태다.
- Pro의 `auto_renew=false`, `cancel_at_period_end=true`이다.
- Studio의 `auto_renew=true`, `cancel_at_period_end=false`이다.
- 기준 시각을 Pro의 원래 다음 결제일 이후로 이동한다.

### When

내부 스케줄러를 실행한다.

```text
run_subscription_renewals()
```

또는 해당 스케줄러 API/command가 있다면 실행한다.

### Then

- Pro에 대한 자동결제 시도가 없어야 한다.
- `subscription_billing_attempts`에 Pro 성공 결제 이력이 추가되면 안 된다.
- Studio만 자동결제 대상이어야 한다.
- 중복 결제 payments가 생성되면 실패다.

검증 SQL 예시:

```sql
SELECT *
FROM subscription_billing_attempts
WHERE subscription_id = :pro_subscription_id;
```

기대:

- Pro 자동결제 attempt 없음
- 또는 skipped 상태가 있다면 `reason='auto_renew_disabled'` 등 명확한 사유 기록

---

## SUB-006. Studio → Pro 다운그레이드 예약

### 목적

Studio 사용자가 Pro로 변경할 때 즉시 Pro 결제하지 않고 Studio 종료일 이후 적용되도록 예약되는지 확인한다.

### Given

- 기준 시각: `2026-06-15 00:00:00`
- 사용자 `user_studio`는 Studio active 구독을 가지고 있다.
- Studio 기간: `2026-06-01 00:00:00` ~ `2026-07-01 00:00:00`
- Pro는 Studio보다 낮은 `plan_rank`이다.

### When

```http
POST /subscriptions/change-plan
Content-Type: application/json

{
  "to_plan_code": "pro"
}
```

### Then - API 검증

- 응답에 `change_type = "downgrade"`가 포함된다.
- 응답에 `status = "scheduled"`가 포함된다.
- 응답에 `effective_at = "2026-07-01T00:00:00"`가 포함된다.
- 현재 플랜은 계속 Studio이다.
- 즉시 Pro 결제는 발생하지 않는다.

### Then - DB 검증

subscription_plan_changes:

- `change_type = 'downgrade'`
- `apply_timing = 'period_end'`
- `status = 'scheduled'`
- `effective_at = Studio.current_period_end`
- `from_plan = studio`
- `to_plan = pro`

payments:

- Pro 결제 성공 이력이 즉시 생성되면 실패다.

---

## SUB-007. 다운그레이드 예약 적용 성공

### 목적

다운그레이드 예약의 `effective_at`이 도래하면 Pro 결제가 진행되고 Pro subscription이 생성되는지 확인한다.

### Given

- SUB-006 완료 상태
- `subscription_plan_changes.status='scheduled'`
- `effective_at <= now()` 상태로 시간 이동
- 사용자에게 active billing_key가 있다.
- Mock 결제는 성공으로 설정한다.

### When

```text
run_scheduled_downgrades()
```

### Then

- Pro 결제가 진행된다.
- Pro subscription이 30일로 생성된다.
- `subscription_plan_changes.status = 'applied'`로 변경된다.
- `applied_at`이 저장된다.
- `to_subscription_id`가 생성된 Pro subscription을 참조한다.
- 현재 플랜은 Pro이다.

---

## SUB-008. 다운그레이드 예약 적용 실패

### 목적

다운그레이드 예약 적용 시 결제 실패 또는 billing_key 누락이 발생하면 실패 상태와 결제 시도 이력이 저장되는지 확인한다.

### Given

- Studio → Pro 다운그레이드 예약이 존재한다.
- `effective_at <= now()`이다.
- billing_key가 없거나 Mock 결제를 실패로 설정한다.

### When

```text
run_scheduled_downgrades()
```

### Then

- Pro subscription은 생성되지 않는다.
- `subscription_plan_changes.status`는 `failed` 또는 `retry_scheduled`가 된다.
- `subscription_billing_attempts`에 실패 이력이 저장된다.
- 실패 사유가 저장된다.
- 동일 plan_change가 중복 적용되지 않아야 한다.

---

## SUB-009. 다운그레이드 예약 취소

### 목적

사용자가 scheduled 상태의 다운그레이드 예약을 취소할 수 있는지 확인한다.

### Given

- Studio → Pro 예약이 존재한다.
- `subscription_plan_changes.status='scheduled'`이다.
- 현재 시각은 `effective_at` 이전이다.

### When

```http
POST /subscriptions/plan-changes/{plan_change_id}/cancel
```

### Then

- `subscription_plan_changes.status = 'cancelled'`
- `cancelled_at`이 저장된다.
- 현재 플랜은 Studio 유지
- 이후 `run_scheduled_downgrades()` 실행 시 해당 예약은 적용되지 않는다.

---

## SUB-010. Studio → Free 변경 / 구독 취소 예약

### 목적

Free 변경이 즉시 권한 제거가 아니라 구독 취소 예약과 동일하게 처리되는지 확인한다.

### Given

- 사용자 `user_studio`는 Studio active 구독을 가지고 있다.
- Studio 기간: `2026-06-01 00:00:00` ~ `2026-07-01 00:00:00`
- 기준 시각: `2026-06-15 00:00:00`

### When

```http
POST /subscriptions/change-plan
Content-Type: application/json

{
  "to_plan_code": "free"
}
```

또는 별도 cancel API가 구현되어 있으면:

```http
POST /subscriptions/{subscription_id}/cancel
```

### Then

- 현재 플랜은 Studio로 유지된다.
- `auto_renew = false`
- `cancel_at_period_end = true`
- `cancelled_at = now()`
- `status = 'active'` 유지
- `subscription_plan_changes.change_type = 'cancel_to_free'` 이력이 저장된다.
- `current_period_end` 이후 유효한 다른 구독이 없으면 현재 플랜은 Free가 된다.

---

## SUB-011. 구독 취소 철회

### 목적

`current_period_end`가 지나기 전 취소 예약을 철회하면 자동결제가 복구되는지 확인한다.

### Given

- Studio subscription이 취소 예약 상태다.
- `auto_renew=false`
- `cancel_at_period_end=true`
- `cancelled_at`이 존재한다.
- 현재 시각은 `current_period_end` 이전이다.

### When

```http
POST /subscriptions/{subscription_id}/resume
```

### Then

- `auto_renew = true`
- `cancel_at_period_end = false`
- `cancelled_at = null`
- 현재 플랜은 Studio 유지
- 다음 자동결제 대상에 포함된다.

---

## SUB-012. 만료 후 구독 취소 철회 불가

### 목적

이미 `current_period_end`가 지난 구독은 취소 철회가 불가능한지 확인한다.

### Given

- 취소 예약된 Pro subscription이 존재한다.
- 현재 시각은 `current_period_end` 이후다.

### When

```http
POST /subscriptions/{subscription_id}/resume
```

### Then

- 400 또는 정책에 맞는 에러 응답을 반환한다.
- `auto_renew`가 true로 복구되면 실패다.
- `cancel_at_period_end`가 false로 복구되면 실패다.
- 현재 플랜은 유효 구독이 없으면 Free이다.

---

## SUB-013. 자동결제 성공

### 목적

`next_billing_at <= now()`인 active 구독이 자동결제에 성공하면 구독 기간이 30일 연장되는지 확인한다.

### Given

- Pro subscription이 active이다.
- `auto_renew=true`
- `cancel_at_period_end=false`
- `next_billing_at <= now()`
- active billing_key가 존재한다.
- Mock 결제는 성공으로 설정한다.
- 현재 Pro 기간: `2026-06-01` ~ `2026-07-01`

### When

```text
run_subscription_renewals()
```

### Then

- 결제 성공 이력이 생성된다.
- `subscription_billing_attempts.status = 'success'`
- `current_period_end`가 30일 연장된다.
- 기대값: `2026-07-31`
- `next_billing_at`도 갱신된다.
- `billing_status`가 정상 상태로 갱신된다.

---

## SUB-014. 자동결제 실패

### 목적

자동결제 실패 시 구독 상태와 실패 이력이 올바르게 저장되는지 확인한다.

### Given

- Pro subscription이 active이다.
- `auto_renew=true`
- `cancel_at_period_end=false`
- `next_billing_at <= now()`
- billing_key가 없거나 Mock 결제가 실패로 설정되어 있다.

### When

```text
run_subscription_renewals()
```

### Then

- `subscription_billing_attempts.status = 'failed'`
- 실패 코드/메시지가 저장된다.
- `billing_status`가 실패 상태로 갱신된다.
- 성공 payment가 생성되면 실패다.
- 정책에 따라 subscription 유지/유예/만료 처리가 명확해야 한다.

추가 검증:

- 같은 subscription이 한 번의 스케줄러 실행에서 중복 결제 시도되지 않는다.

---

## SUB-015. 모든 유료 플랜 만료 후 Free 적용

### 목적

유효한 active 유료 subscription이 없으면 현재 플랜이 Free로 계산되는지 확인한다.

### Given

- 사용자에게 Pro/Studio subscription이 존재하지만 모두 `current_period_end <= now()`이다.
- 또는 status가 inactive/cancelled/expired이다.

### When

```http
GET /plans/current
```

또는

```http
GET /subscriptions/me
```

### Then

- `current_plan.plan_code = "free"`
- 유료 플랜 권한이 비활성화된다.
- Free 기본 사용량/권한이 적용된다.

---

## SUB-016. 현재 플랜 plan_rank 우선순위 계산

### 목적

동일 사용자에게 Pro와 Studio가 동시에 active로 존재할 때 현재 플랜이 plan_rank가 높은 Studio로 계산되는지 확인한다.

### Given

- Pro subscription active
- Studio subscription active
- 두 구독 모두 현재 시각에 유효
- Pro `plan_rank=10`
- Studio `plan_rank=20`

### When

```http
GET /plans/current
```

### Then

- 현재 플랜은 Studio이다.
- Pro가 먼저 생성되었더라도 Studio가 우선이다.
- 종료일이 더 늦은 구독이 아니라 `plan_rank`가 더 높은 구독이 우선이다.

---

## SUB-017. 사용자 화면 응답 검증

### 목적

사용자 화면에서 현재 플랜, 다음 결제일, 취소 상태, 다운그레이드 예약, 업그레이드 이월 기간이 표시 가능한 응답을 제공하는지 확인한다.

### Given

- 사용자가 Studio active 구독을 가지고 있다.
- Pro 이월 구독이 존재할 수 있다.
- 다운그레이드 예약이 존재할 수 있다.

### When

```http
GET /subscriptions/me
```

### Then

응답은 최소 아래 정보를 제공해야 한다.

```json
{
  "current_plan": {
    "plan_code": "studio",
    "plan_name": "Studio",
    "plan_rank": 20
  },
  "current_subscription": {
    "status": "active",
    "current_period_start": "2026-06-10T00:00:00",
    "current_period_end": "2026-07-10T00:00:00",
    "next_billing_at": "2026-07-10T00:00:00",
    "auto_renew": true,
    "cancel_at_period_end": false
  },
  "carried_over_subscription": {
    "plan_code": "pro",
    "carried_over_days": 20,
    "current_period_end": "2026-07-30T00:00:00",
    "auto_renew": false
  },
  "scheduled_plan_change": {
    "change_type": "downgrade",
    "to_plan_code": "pro",
    "status": "scheduled",
    "effective_at": "2026-07-10T00:00:00"
  }
}
```

UI 표시 검증:

- 업그레이드 후: `기존 Pro 잔여 기간은 Studio 종료 후 이어서 적용됩니다.`
- 다운그레이드 예약 후: `Pro로 변경 예약됨`, `Studio는 YYYY-MM-DD까지 유지됩니다.`
- Free 변경 후: `구독 취소 예약됨`, `YYYY-MM-DD까지 Studio 플랜을 사용할 수 있습니다.`
- 취소 예약 상태에서는 취소 철회 버튼이 보여야 한다.
- 다운그레이드 예약 상태에서는 예약 취소 버튼이 보여야 한다.

---

## SUB-018. 관리자 구독 관리 화면 응답 검증

### 목적

관리자가 사용자별 구독 상태, 자동결제 상태, 결제 실패, 플랜 변경 이력을 조회할 수 있는지 확인한다.

### Given

- 관리자 권한 사용자가 있다.
- 테스트 사용자에게 active subscription, billing_attempt, plan_change 이력이 존재한다.

### When

```http
GET /admin/subscriptions
GET /admin/subscriptions/{subscription_id}
GET /admin/subscriptions/{subscription_id}/billing-attempts
GET /admin/subscriptions/{subscription_id}/plan-changes
```

### Then

관리자 목록/상세에서 아래 항목이 확인되어야 한다.

- 사용자
- 현재 적용 플랜
- active 구독 목록
- `current_period_start`
- `current_period_end`
- `next_billing_at`
- `auto_renew`
- `cancel_at_period_end`
- `carried_over_days`
- `superseded_by_subscription_id`
- 최근 결제 성공/실패
- `billing_status`
- 예약된 다운그레이드
- 플랜 변경 이력
- 결제 실패 필터
- 플랜 변경 예약 필터

주의:

- 관리자 화면에는 billing_key 원문이 노출되면 안 된다.
- 강제 취소/강제 변경 기능은 이번 테스트 범위가 아니며, 조회 중심으로 검증한다.

---

## SUB-019. 비활성 플랜 변경 차단

### 목적

`plans.active=false`인 플랜으로 checkout/change-plan 요청이 들어오면 차단되는지 확인한다.

### Given

- `plans.active=false`인 테스트 플랜이 존재한다.
- 사용자는 Free 상태다.

### When

```http
POST /subscriptions/change-plan
Content-Type: application/json

{
  "to_plan_code": "inactive_test_plan"
}
```

### Then

- 400 또는 정책에 맞는 에러 응답
- subscription 생성 없음
- payment 생성 없음
- plan_change 생성 없음 또는 failed/rejected 상태 기록

---

## SUB-020. 다른 사용자 예약 취소 차단

### 목적

사용자는 본인 소유가 아닌 `subscription_plan_changes`를 취소할 수 없어야 한다.

### Given

- user A에게 scheduled downgrade가 존재한다.
- user B로 로그인한다.

### When

user B가 user A의 plan_change_id로 요청한다.

```http
POST /subscriptions/plan-changes/{user_a_plan_change_id}/cancel
```

### Then

- 403 또는 404 응답
- user A의 plan_change 상태는 scheduled 유지
- `cancelled_at`이 저장되면 실패다.

---

## SUB-021. 기존 결제/플랜/크레딧 데이터 보존

### 목적

구독 기능 추가 후 기존 plans, credit_plans, admin_policy_settings, payments 등 기존 데이터가 삭제되거나 깨지지 않았는지 확인한다.

### Given

- 테스트 전 기존 데이터 row count를 기록한다.

```sql
SELECT COUNT(*) FROM plans;
SELECT COUNT(*) FROM credit_plans;
SELECT COUNT(*) FROM admin_policy_settings;
SELECT COUNT(*) FROM payments;
```

### When

- migration 실행
- 구독 테스트 전체 실행

### Then

- 기존 seed row가 삭제되지 않아야 한다.
- 기존 plan_code/credit_plan_code가 변경되지 않아야 한다.
- 기존 결제 조회 API가 깨지지 않아야 한다.
- 신규 컬럼 추가는 nullable/default/IF NOT EXISTS 등 안전한 방식이어야 한다.

---

## 5. 스케줄러 전용 테스트

## 5.1 자동결제 대상 조회 조건

자동결제 스케줄러는 아래 조건만 대상으로 삼아야 한다.

```sql
status = 'active'
auto_renew = true
cancel_at_period_end = false
next_billing_at <= now()
```

제외 대상:

- `auto_renew=false`
- `cancel_at_period_end=true`
- `status != active`
- `next_billing_at > now()`
- 업그레이드로 밀려난 하위 플랜
- billing_key가 inactive인 구독

## 5.2 다운그레이드 예약 적용 대상 조회 조건

다운그레이드 예약 적용 스케줄러는 아래 조건만 대상으로 삼아야 한다.

```sql
change_type = 'downgrade'
status = 'scheduled'
effective_at <= now()
```

제외 대상:

- `status='cancelled'`
- `status='applied'`
- `status='failed'` 중 재시도 정책이 없는 경우
- `effective_at > now()`
- 다른 사용자의 billing_key를 참조하는 경우

## 5.3 중복 실행 방지

스케줄러가 동시에 두 번 실행되어도 같은 subscription 또는 같은 plan_change가 중복 결제/적용되지 않아야 한다.

검증 방법:

1. 같은 `subscription_id`로 동시에 renewal 함수 2회 호출
2. 같은 `plan_change_id`로 동시에 downgrade 적용 함수 2회 호출
3. payments, billing_attempts, subscriptions 생성 건수 확인

기대:

- 성공 payment는 1건만 생성
- subscription 기간 연장은 1회만 반영
- plan_change는 applied 1회만 반영

---

## 6. DB 검증 쿼리 모음

### 6.1 사용자 현재 유효 구독 목록

```sql
SELECT s.subscription_id,
       p.plan_code,
       p.plan_rank,
       s.status,
       s.current_period_start,
       s.current_period_end,
       s.next_billing_at,
       s.auto_renew,
       s.cancel_at_period_end,
       s.carried_over_days,
       s.superseded_by_subscription_id
FROM subscriptions s
JOIN plans p ON p.plan_id = s.plan_id
WHERE s.user_id = :user_id
ORDER BY p.plan_rank DESC, s.current_period_end DESC;
```

### 6.2 현재 플랜 계산 검증

```sql
SELECT s.subscription_id,
       p.plan_code,
       p.plan_rank
FROM subscriptions s
JOIN plans p ON p.plan_id = s.plan_id
WHERE s.user_id = :user_id
  AND s.status = 'active'
  AND s.current_period_start <= now()
  AND s.current_period_end > now()
ORDER BY p.plan_rank DESC
LIMIT 1;
```

결과가 없으면 Free여야 한다.

### 6.3 플랜 변경 이력

```sql
SELECT *
FROM subscription_plan_changes
WHERE user_id = :user_id
ORDER BY created_at DESC;
```

### 6.4 자동결제 시도 이력

```sql
SELECT *
FROM subscription_billing_attempts
WHERE subscription_id = :subscription_id
ORDER BY created_at DESC;
```

### 6.5 업그레이드 이월 검증

```sql
SELECT subscription_id,
       current_period_start,
       current_period_end,
       original_period_end,
       upgraded_at,
       carried_over_days,
       auto_renew,
       cancel_at_period_end,
       superseded_by_subscription_id
FROM subscriptions
WHERE subscription_id = :lower_subscription_id;
```

### 6.6 취소 예약 검증

```sql
SELECT subscription_id,
       status,
       auto_renew,
       cancel_at_period_end,
       cancelled_at,
       current_period_end
FROM subscriptions
WHERE subscription_id = :subscription_id;
```

---

## 7. 프론트 수동 테스트 체크리스트

## 7.1 결제/플랜 변경 화면

- [ ] Free 사용자에게 Pro 결제 버튼이 보인다.
- [ ] Free 사용자에게 Studio 결제 버튼이 보인다.
- [ ] 현재 Pro 사용자는 Studio 업그레이드 버튼이 보인다.
- [ ] 현재 Studio 사용자는 Pro 다운그레이드 예약 버튼이 보인다.
- [ ] 현재 유료 사용자는 Free 변경/구독 취소 버튼이 보인다.
- [ ] 현재 플랜과 동일한 플랜 버튼은 비활성화 또는 현재 사용 중으로 표시된다.

## 7.2 업그레이드 후 화면

- [ ] 현재 플랜이 Studio로 표시된다.
- [ ] Studio 즉시 적용 안내가 표시된다.
- [ ] 기존 Pro 잔여 기간이 Studio 종료 후 이어서 적용된다는 안내가 표시된다.
- [ ] 기존 Pro 자동결제가 중지되었다는 안내가 표시된다.
- [ ] 다음 결제일이 Studio 기준으로 표시된다.

## 7.3 다운그레이드 예약 후 화면

- [ ] 현재 플랜은 Studio로 유지된다.
- [ ] Pro로 변경 예약됨이 표시된다.
- [ ] Studio 유지 종료일이 표시된다.
- [ ] Pro 적용 예정일이 표시된다.
- [ ] 다운그레이드 예약 취소 버튼이 표시된다.

## 7.4 Free 변경 후 화면

- [ ] 현재 플랜은 유료 플랜으로 유지된다.
- [ ] 구독 취소 예약 상태가 표시된다.
- [ ] 유료 플랜 사용 가능 종료일이 표시된다.
- [ ] 이후 Free 전환 안내가 표시된다.
- [ ] 취소 철회 버튼이 표시된다.

## 7.5 관리자 화면

- [ ] 사용자별 현재 적용 플랜을 확인할 수 있다.
- [ ] active 구독 목록을 확인할 수 있다.
- [ ] 자동결제 여부를 확인할 수 있다.
- [ ] 취소 예약 여부를 확인할 수 있다.
- [ ] 업그레이드 이월 구독을 확인할 수 있다.
- [ ] 다운그레이드 예약 상태를 확인할 수 있다.
- [ ] 결제 실패 이력을 확인할 수 있다.
- [ ] billing_key 원문은 노출되지 않는다.

---

## 8. Codex 테스트 구현 지시문

아래 프롬프트를 Codex에 전달한다.

```text
프로젝트 루트의 docs/subscriptions/subscription_30day_auto_renewal_final_v2_with_model_guide.md 기준으로 구독 기능 구현이 완료된 상태다.

이제 테스트를 작성해줘.

목표:
- 30일 자동결제 구독 정책이 실제 코드에서 의도대로 동작하는지 검증한다.
- 테스트 결과 리포트를 report/subscription_test_report.md 로 작성한다.

반드시 확인할 시나리오:
1. Free → Pro 신규 구독
2. Free → Studio 신규 구독
3. 같은 플랜 재결제/연장
4. Pro → Studio 업그레이드 + Pro 잔여 기간 이월
5. 업그레이드 후 하위 플랜 중복 자동결제 방지
6. Studio → Pro 다운그레이드 예약
7. 다운그레이드 예약 적용 성공
8. 다운그레이드 예약 적용 실패
9. 다운그레이드 예약 취소
10. Studio → Free 변경 / 구독 취소 예약
11. 구독 취소 철회
12. 만료 후 구독 취소 철회 불가
13. 자동결제 성공
14. 자동결제 실패
15. 모든 유료 플랜 만료 후 Free 적용
16. 현재 플랜 plan_rank 우선순위 계산
17. 사용자 화면 응답 검증
18. 관리자 화면 응답 검증
19. 비활성 플랜 변경 차단
20. 다른 사용자 예약 취소 차단
21. 기존 결제/플랜/크레딧 데이터 보존

작업 규칙:
- 기존 테스트 구조를 먼저 확인하고 그 구조에 맞춰 작성한다.
- 실제 Toss 결제는 호출하지 말고 mock/test mode로 처리한다.
- billing_key 원문은 테스트 로그/API 응답/리포트에 노출하지 않는다.
- 시간 의존 테스트는 mock clock, freezegun, timestamp 주입 중 프로젝트에 맞는 방식을 사용한다.
- 테스트 데이터는 테스트 전용 user/payment/billing_key를 사용하고 테스트 후 정리한다.
- 기존 seed 데이터 삭제 또는 변경은 금지한다.
- 테스트가 실패하면 어떤 정책이 깨졌는지 report/subscription_test_report.md에 명확히 기록한다.
- 구현 라우트가 문서의 API 후보와 다르면 실제 라우트 기준으로 테스트하되, 어떤 라우트를 사용했는지 리포트에 적는다.

완료 기준:
- pytest 또는 프로젝트의 테스트 명령으로 전체 테스트가 실행된다.
- 위 필수 시나리오별 pass/fail 결과가 남는다.
- 실패한 테스트가 있으면 원인과 수정 후보가 리포트에 정리된다.
- report/subscription_test_report.md 파일이 생성된다.
```

---

## 9. 테스트 리포트 템플릿

Codex가 `report/subscription_test_report.md`에 아래 형식으로 결과를 남기도록 한다.

```markdown
# 구독 기능 테스트 리포트

## 1. 테스트 환경

- 실행 일시:
- 브랜치:
- DB:
- 백엔드 실행 방식:
- 프론트 실행 방식:
- 테스트 명령:
- 결제 모드: mock/test

## 2. 테스트 결과 요약

| ID | 시나리오 | 결과 | 비고 |
|---|---|---|---|
| SUB-001 | Free → Pro 신규 구독 | PASS/FAIL |  |
| SUB-002 | Free → Studio 신규 구독 | PASS/FAIL |  |
| SUB-003 | 같은 플랜 재결제/연장 | PASS/FAIL |  |
| SUB-004 | Pro → Studio 업그레이드 + Pro 잔여 기간 이월 | PASS/FAIL |  |
| SUB-005 | 업그레이드 후 하위 플랜 중복 자동결제 방지 | PASS/FAIL |  |
| SUB-006 | Studio → Pro 다운그레이드 예약 | PASS/FAIL |  |
| SUB-007 | 다운그레이드 예약 적용 성공 | PASS/FAIL |  |
| SUB-008 | 다운그레이드 예약 적용 실패 | PASS/FAIL |  |
| SUB-009 | 다운그레이드 예약 취소 | PASS/FAIL |  |
| SUB-010 | Studio → Free 변경 | PASS/FAIL |  |
| SUB-011 | 구독 취소 철회 | PASS/FAIL |  |
| SUB-012 | 만료 후 구독 취소 철회 불가 | PASS/FAIL |  |
| SUB-013 | 자동결제 성공 | PASS/FAIL |  |
| SUB-014 | 자동결제 실패 | PASS/FAIL |  |
| SUB-015 | 모든 유료 플랜 만료 후 Free 적용 | PASS/FAIL |  |
| SUB-016 | 현재 플랜 rank 우선순위 | PASS/FAIL |  |
| SUB-017 | 사용자 화면 응답 | PASS/FAIL |  |
| SUB-018 | 관리자 화면 응답 | PASS/FAIL |  |
| SUB-019 | 비활성 플랜 변경 차단 | PASS/FAIL |  |
| SUB-020 | 다른 사용자 예약 취소 차단 | PASS/FAIL |  |
| SUB-021 | 기존 데이터 보존 | PASS/FAIL |  |

## 3. 실패 상세

### 실패 케이스 ID

- 증상:
- 기대 결과:
- 실제 결과:
- 관련 파일:
- 관련 함수/API:
- DB 상태:
- 수정 후보:

## 4. 보안 확인

- billing_key 원문 API 응답 노출 여부: PASS/FAIL
- billing_key 원문 로그 노출 여부: PASS/FAIL
- 다른 사용자 구독/예약 접근 차단 여부: PASS/FAIL
- 관리자 API 권한 체크 여부: PASS/FAIL

## 5. 회귀 영향 확인

- 기존 plans seed 보존: PASS/FAIL
- 기존 credit_plans seed 보존: PASS/FAIL
- 기존 payments 조회 영향 없음: PASS/FAIL
- 기존 로그인/세션 영향 없음: PASS/FAIL

## 6. 최종 판단

- 전체 통과 여부:
- 배포 가능 여부:
- 배포 전 필수 수정 사항:
```

---

## 10. 최종 완료 기준

테스트 완료 후 아래 항목이 모두 확인되어야 한다.

- [ ] Free / Pro / Studio 플랜 우선순위가 명확하다.
- [ ] Pro / Studio 30일 구독 생성이 가능하다.
- [ ] 현재 적용 플랜은 active subscriptions + plan_rank 기반으로 계산된다.
- [ ] Free → Pro 결제가 정상 동작한다.
- [ ] Free → Studio 결제가 정상 동작한다.
- [ ] Pro → Studio 업그레이드 시 Studio가 즉시 적용된다.
- [ ] 업그레이드 시 Pro 잔여 기간이 Studio 종료 이후로 이월된다.
- [ ] 업그레이드 후 Pro auto_renew=false로 중복 자동결제가 방지된다.
- [ ] Studio → Pro 다운그레이드는 즉시 결제하지 않고 예약된다.
- [ ] 예약된 다운그레이드는 effective_at 도래 시 결제/적용된다.
- [ ] 다운그레이드 예약 취소가 가능하다.
- [ ] Free 변경은 구독 취소 예약으로 처리된다.
- [ ] 구독 취소 시 current_period_end까지 권한이 유지된다.
- [ ] 취소 예약 구독은 자동결제 대상에서 제외된다.
- [ ] 취소 철회가 가능하다.
- [ ] 만료 후 취소 철회는 불가능하다.
- [ ] 자동결제 성공 시 30일 연장된다.
- [ ] 자동결제 실패 이력이 남는다.
- [ ] 모든 유료 구독 만료 후 Free가 적용된다.
- [ ] 사용자 화면에서 현재 플랜/다음 결제일/취소 상태/변경 예약/이월 기간을 볼 수 있다.
- [ ] 관리자 화면에서 구독 상태/자동결제 상태/결제 실패/플랜 변경 이력을 볼 수 있다.
- [ ] billing_key 원문이 API 응답/로그/화면에 노출되지 않는다.
- [ ] 다른 사용자의 구독/예약을 수정할 수 없다.
- [ ] 기존 결제/플랜/크레딧 데이터가 삭제되지 않는다.
```
