# 구독 업그레이드 정산 정책 v11 최종 실행 가이드 (상세 보완판) - v12 선작업 반영본

대상 기준:
- 실제 DB 설계: `docs/db/Garim_DB_Design_final_clean_v12.xlsx` (사용자 선작업 완료)
- 초기화 SQL: `docker/database/init/0_init_table_v12.sql` (사용자 선작업 완료)
- 기존 실행 가이드: `docs/subscriptions/subscription_upgrade_proration_v11_execution_guide.md`
- 개발환경 정리 지침: `docs/subscriptions/subscription_upgrade_proration_v11_dev_cleanup_execution_guide.md`

이 문서는 개발환경 정리 지침 및 사용자의 선작업을 통해 v12 버전으로 반영된 DB 스키마 사양을 참고하여, 정기 결제 빌링키 자동 갱신 연동 및 0원 결제 승인 예외 처리 보완 사항을 구체적인 구현 쿼리와 코드 지침 수준으로 통합한 최종 문서입니다.

> [!NOTE]
> DB 설계서(`docs/db/Garim_DB_Design_final_clean_v12.xlsx`)와 초기화 DDL(`docker/database/init/0_init_table_v12.sql`)은 기존 `v11` 사양에서 carryover 관련 컬럼을 완벽하게 제거하고 정산 관련 금액 컬럼 4종을 추가 및 제약 조건을 반영하여 사용자의 선작업을 통해 `v12` 버전으로 이미 안전하게 구성되었습니다. 에이전트 검증 결과, 선작업 내용에 누락이 없음을 확인하였습니다. 아래의 데이터베이스 수정 DDL 및 마이그레이션 쿼리는 로컬 개발 환경 DB에 마이그레이션을 수동 적용할 때 참고용으로 사용하시기 바랍니다.

---

## 1. 최종 정산(Proration) 및 빌링 연동 정책

- **업그레이드**:
  - 하위 플랜에서 상위 플랜으로 변경하면 즉시 결제하고 즉시 적용합니다.
  - 기존 하위 플랜의 잔여 기간은 상위 플랜 뒤로 이월(carryover)하지 않습니다.
  - 기존 하위 플랜의 잔여 가치는 금액으로 환산해 업그레이드 결제 금액에서 차감(Proration)합니다.
  - 기존 하위 구독은 즉시 `cancelled` 처리하고 현재 권한 및 자동결제 갱신 대상에서 제외합니다.
  - 새 상위 구독은 즉시 `active`로 생성하되, 자동 갱신을 위해 **결제 수단 빌링키(`billing_key_id`)를 누락 없이 이식**합니다.
- **다운그레이드**:
  - 즉시 결제하지 않고, 현재 구독 기간 종료 시점에 적용되도록 예약합니다.
- **Free 변경**:
  - 즉시 Free로 바꾸지 않고, 현재 유료 구독 기간 종료 후 Free로 전환되도록 예약합니다.
- **업그레이드 후 취소**:
  - 현재 상위 플랜 기간 종료 후 Free로 전환하며, 과거 하위 플랜의 남은 기간은 복구하지 않습니다.

---

## 2. 데이터베이스 컬럼 및 제약 정리 (SQL)

### 2.1 `subscriptions` 테이블 수정
의미가 사라진 carryover 추적 컬럼 4개와 관련 제약을 삭제합니다.

```sql
-- 1) 인덱스 및 제약 조건 삭제
DROP INDEX IF EXISTS idx_subscriptions_superseded_by;

ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS fk_subscriptions_superseded_by,
    DROP CONSTRAINT IF EXISTS ck_subscriptions_carried_over_days_non_negative;

-- 2) carryover 컬럼 삭제
ALTER TABLE subscriptions
    DROP COLUMN IF EXISTS upgraded_at,
    DROP COLUMN IF EXISTS superseded_by_subscription_id,
    DROP COLUMN IF EXISTS carried_over_days,
    DROP COLUMN IF EXISTS original_period_end;
```

### 2.2 `subscription_plan_changes` 테이블 수정
이월 일수 관련 컬럼을 지우고, 정산 금액을 추적하기 위한 컬럼 4개를 신규 추가합니다.

```sql
-- 1) 기존 이월 제약 조건 및 컬럼 삭제
ALTER TABLE subscription_plan_changes
    DROP CONSTRAINT IF EXISTS chk_subscription_plan_changes_remaining_days;

ALTER TABLE subscription_plan_changes
    DROP COLUMN IF EXISTS remaining_days,
    DROP COLUMN IF EXISTS from_subscription_new_end;

-- 2) 정산 금액 정보 기록용 컬럼 4개 추가
ALTER TABLE subscription_plan_changes
    ADD COLUMN IF NOT EXISTS remaining_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS target_plan_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS discount_amount integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS charged_amount integer NOT NULL DEFAULT 0;

-- 3) 정산 금액 비음수(Non-negative) 체크 제약 조건 추가
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

### 2.3 엑셀 설계 문서 및 초기화 시드 반영
- **설계서 수정 (`docs/db/Garim_DB_Design_final_clean_v12.xlsx`)**:
  - `11_subscriptions` 시트와 `39_subscription_plan_changes` 시트에서 삭제/추가된 컬럼 정보를 이미 선작업으로 반영 완료했습니다.
- **초기화 DDL 수정 (`docker/database/init/0_init_table_v12.sql`)**:
  - 시드 구문 내부 주석에서 carryover 관련 용어 삭제 및 `Upgrade is charged/applied immediately with remaining-value proration`으로의 업데이트가 이미 완료되어 있습니다.

---

## 3. 백엔드 비즈니스 로직 리팩토링 및 구현

### STEP 1. 업그레이드 잔여 가치 정산 연산 함수 추가
- **대상**: `backend/services/subscription.py`
- **구현**: 기존 플랜의 남은 가치를 초 단위 정밀도로 금액 환산하는 헬퍼 함수를 신규 구현합니다.

```python
from math import floor

def calculate_upgrade_proration(current_plan, current_subscription, target_plan, now=None):
    """업그레이드 시 기존 플랜의 잔여 이용 가치를 금액으로 계산한다."""
    if now is None:
        from datetime import datetime
        now = datetime.now()
        
    current_period_start = current_subscription["current_period_start"]
    current_period_end = current_subscription["current_period_end"]
    
    # 총 이용 기간 및 남은 기간 계산 (초 단위)
    period_seconds = max(1.0, (current_period_end - current_period_start).total_seconds())
    remaining_seconds = max(0.0, (current_period_end - now).total_seconds())
    
    # 1) 기존 플랜의 남은 가치 환산 금액 (소수점 버림)
    remaining_amount = floor(current_plan["price_amount"] * remaining_seconds / period_seconds)
    
    # 2) 대상 플랜 금액 및 최종 청구 금액 계산
    target_plan_amount = target_plan["price_amount"]
    charged_amount = max(0, target_plan_amount - remaining_amount)
    
    # 3) 할인(차감) 적용된 금액
    discount_amount = target_plan_amount - charged_amount
    
    return {
        "period_seconds": int(period_seconds),
        "remaining_seconds": int(remaining_seconds),
        "remaining_amount": remaining_amount,
        "target_plan_amount": target_plan_amount,
        "discount_amount": discount_amount,
        "charged_amount": charged_amount
    }
```

### STEP 2. `classify_plan_change()` 응답 확장
- **대상**: `backend/services/subscription.py`
- **구현**: 업그레이드일 때 계산된 정산 금액 상세 객체(`proration`)를 응답에 바인딩합니다.

```python
# classify_plan_change() 내 upgrade 분기점
if target_rank > current_rank:
    change_type = "upgrade"
    apply_timing = "immediate"
    requires_payment_now = True
    
    # 정산 금액 연산 수행
    from datetime import datetime
    proration = calculate_upgrade_proration(
        current_plan=current_plan,
        current_subscription=current["current_subscription"],
        target_plan=target_plan,
        now=datetime.now()
    )
else:
    # downgrade, cancel_to_free 등은 기존 구조 유지 (proration 필드 제외)
```

### STEP 3. `apply_upgrade_with_proration()` 구현
- **대상**: `backend/services/subscription.py`
- **보완 핵심**: 새 상위 구독을 `active`로 생성할 때, **갱신 결제용 빌링키 고유 ID(`billing_key_id`)를 파라미터로 받아서 SQL에 반드시 매핑**해야 합니다.

```python
def apply_upgrade_with_proration(
    db: Session,
    user_id: str,
    from_subscription_id=None,
    to_plan_id=None,
    payment_id=None,
    billing_key_id=None,  # <-- 빌링키 자동 갱신 누락 방지를 위해 필수 지정
):
    if not to_plan_id:
        raise ValueError("Target plan is required for upgrade.")
        
    target_plan = _get_target_plan(db, str(to_plan_id))
    lower = _find_upgrade_source_subscription(db, user_id, from_subscription_id)
    if not lower:
        raise ValueError("Active source subscription was not found for upgrade.")
        
    # 1. 정산 금액 계산
    from datetime import datetime
    now = datetime.now()
    proration = calculate_upgrade_proration(
        current_plan=lower,
        current_subscription=lower,
        target_plan=target_plan,
        now=now
    )

    # 2. 새 상위 구독 active 생성 (billing_key_id 적용)
    upper_row = db.execute(
        text("""
            INSERT INTO subscriptions (
                user_id, plan_id, status, started_at, ended_at, renew_at,
                current_period_start, current_period_end, next_billing_at,
                auto_renew, cancel_at_period_end, billing_status, last_payment_id,
                billing_key_id, -- [한글 주석] 정기 결제 빌링키 ID 이식
                created_at, updated_at
            )
            VALUES (
                :user_id, :plan_id, 'active', NOW(), NOW() + INTERVAL '30 days', NOW() + INTERVAL '30 days',
                NOW(), NOW() + INTERVAL '30 days', NOW() + INTERVAL '30 days',
                true, false, 'paid', :payment_id,
                CAST(:billing_key_id AS uuid), -- [한글 주석] 빌링키 고유키 이식 바인딩
                NOW(), NOW()
            )
            RETURNING subscription_id, current_period_start, current_period_end, next_billing_at
        """),
        {
            "user_id": user_id,
            "plan_id": target_plan["plan_id"],
            "payment_id": payment_id,
            "billing_key_id": billing_key_id,
        }
    ).fetchone()
    upper = _row_mapping(upper_row)

    # 3. 기존 하위 구독 즉시 해지(cancelled) 처리
    db.execute(
        text("""
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
              AND status = 'active'
        """),
        {
            "from_subscription_id": lower["subscription_id"],
            "user_id": user_id
        }
    )

    # 4. 기존 하위 구독에 묶여 있던 예약 이력은 모두 cancelled로 취소
    db.execute(
        text("""
            UPDATE subscription_plan_changes
            SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW()
            WHERE user_id = :user_id
              AND from_subscription_id = :from_subscription_id
              AND status = 'scheduled'
        """),
        {
            "user_id": user_id,
            "from_subscription_id": lower["subscription_id"]
        }
    )

    # 5. subscription_plan_changes 테이블에 정산 이력 기록
    plan_change_row = db.execute(
        text("""
            INSERT INTO subscription_plan_changes (
                user_id, subscription_id, from_plan_id, to_plan_id,
                from_subscription_id, to_subscription_id, change_type, apply_timing, status,
                remaining_seconds, remaining_amount, target_plan_amount, discount_amount, charged_amount,
                from_subscription_original_end, requested_at, effective_at, applied_at, created_at, updated_at
            )
            VALUES (
                :user_id, :upper_subscription_id, :from_plan_id, :to_plan_id,
                :lower_subscription_id, :upper_subscription_id, 'upgrade', 'immediate', 'applied',
                :remaining_seconds, :remaining_amount, :target_plan_amount, :discount_amount, :charged_amount,
                :from_subscription_original_end, NOW(), NOW(), NOW(), NOW(), NOW()
            )
            RETURNING plan_change_id
        """),
        {
            "user_id": user_id,
            "upper_subscription_id": upper["subscription_id"],
            "from_plan_id": lower["plan_id"],
            "to_plan_id": target_plan["plan_id"],
            "lower_subscription_id": lower["subscription_id"],
            "remaining_seconds": proration["remaining_seconds"],
            "remaining_amount": proration["remaining_amount"],
            "target_plan_amount": proration["target_plan_amount"],
            "discount_amount": proration["discount_amount"],
            "charged_amount": proration["charged_amount"],
            "from_subscription_original_end": lower["current_period_end"],
        }
    ).fetchone()
    plan_change = _row_mapping(plan_change_row)

    return {
        "subscription_id": upper["subscription_id"],
        "upper_subscription": upper,
        "plan_change_id": plan_change["plan_change_id"] if plan_change else None
    }
```

---

### STEP 4. 결제 승인 프로세스 연동 및 0원 결제 차단 처리

- **대상**: `backend/services/payment.py`
- **구현 내용**:
  - 일회성 결제(`confirm_payment`)와 정기 결제(`confirm_billing_payment`) 모두 카드 청구 전 `classify_plan_change()`를 수행해 결제 승인 금액을 `proration.charged_amount`로 변경합니다.
  - 정기결제 최초 승인 시 **0원 업그레이드 분기**를 확실하게 보완합니다.

```python
# confirm_billing_payment() 함수 내부 결제 승인 영역 리팩토링 예시
# 1. 업그레이드 여부 및 정산 금액 사전 계산
plan_change = subscription_service.classify_plan_change(db=db, user_id=user_id, to_plan_id=str(plan_id))
is_upgrade = (plan_change["change_type"] == "upgrade" and plan_change.get("current_subscription"))

if is_upgrade:
    amount = plan_change["proration"]["charged_amount"]
else:
    amount = plan["price_amount"]

# ... ready 상태 임시 결제(payments) 기록 작성 (생략) ...

# 2. 0원 결제 예외 차단 분기
if is_upgrade and amount == 0:
    # 0원일 경우 Toss API 결제 승인 요청을 완전히 스킵(Skip)
    toss_status = "SUCCESS"
    receipt_url = None
    toss_result = {
        "status": "DONE",
        "paymentKey": "MOCK_ZERO_UPGRADE_KEY_" + payment_id,
        "lastTransactionKey": "MOCK_ZERO_TRANS_KEY_" + payment_id,
        "method": "차액정산(0원)",
        "totalAmount": 0,
        "balanceAmount": 0,
        "currency": "KRW",
        "requestedAt": datetime.now().isoformat(),
        "approvedAt": datetime.now().isoformat(),
        "isPartialCancelable": False
    }
else:
    # 0원이 아닌 경우에만 Toss 카드 청구 API 호출
    toss_result = await _confirm_toss_billing_payment(
        billing_key=billing_key,
        customer_key=customer_key,
        order_id=payment_id,
        amount=amount,
        order_name=f"Garim {plan_name} 정기구독"
    )
    toss_status = str(toss_result.get("status", "")).upper()

# ... payments 테이블의 상태를 success로 업데이트 (생략) ...

# 3. 신규 정산형 업그레이드 서비스 호출 연계
if is_upgrade:
    subscription = subscription_service.apply_upgrade_with_proration(
        db=db,
        user_id=user_id,
        from_subscription_id=plan_change["current_subscription"].get("subscription_id"),
        to_plan_id=plan_id,
        payment_id=payment_id,
        billing_key_id=billing_key_id, # <-- 빌링키 ID 인계 보존
    )
else:
    subscription = subscription_service.create_or_extend_subscription(
        db=db,
        user_id=user_id,
        plan_id=plan_id,
        payment_id=payment_id,
        billing_key_id=billing_key_id,
    )
```

---

### STEP 5. 업그레이드 임시 주문 생성 API 정리
- **대상**: `backend/services/payment.py` / `frontend/src/pages/garim/Payment.jsx`
- **구현**:
  - 기존 `create_temp_order` 내의 정가 검증(`product["price_amount"] != amount`)은 일반 신규 구독 및 크레딧 결제에만 한정합니다.
  - 업그레이드의 경우 백엔드가 `classify_plan_change`를 통해 `charged_amount`를 동적으로 구하고, 이를 기준으로 임시 주문 데이터를 생성하도록 API를 정리합니다.

---

## 4. API 및 프런트엔드 화면 carryover 제거 (UI/UX)

### STEP 6. 사용자 결제 정보 API에서 carryover 제거
- **대상**: `backend/services/payment.py`
- **수정**:
  - `getMyPaymentInfo` 조회 SQL 및 응답 딕셔너리에서 `carried_over_subscription`, `carried_over_days` 필드를 제거합니다.
  - 대신 `subscription_plan_changes`에서 `change_type='upgrade'`에 해당하는 가장 최신의 applied 이력을 읽어 `latest_upgrade_proration` 필드로 프런트엔드에 전달합니다.
  ```json
  "latest_upgrade_proration": {
      "from_plan_name": "Pro",
      "to_plan_name": "Studio",
      "remaining_amount": 1933,
      "discount_amount": 1933,
      "charged_amount": 1967,
      "applied_at": "2026-06-11T10:00:00"
  }
  ```

### STEP 7. Pricing 화면에서 carryover 제거
- **대상**: [Pricing.jsx](file:///d:/final_project/Human_Final_PJ/frontend/src/pages/garim/Pricing.jsx)
- **수정**:
  - `paymentInfo.carried_over_subscription` 데이터 체크 구문과 카드의 이월 상태 조건식(`isCarriedPlan`), 그리고 "이월 적용" 관련 UI 배지들을 완전히 걷어냅니다.

### STEP 8. Billing 화면에서 carryover 제거 및 정산 정보 추가
- **대상**: [Billing.jsx](file:///d:/final_project/Human_Final_PJ/frontend/src/pages/garim/Billing.jsx)
- **수정**:
  - 하위 플랜 이월 메시지 영역(`carriedOver` 노출 블록)을 완전히 지웁니다.
  - `latest_upgrade_proration` 응답 값이 존재할 경우 다음과 같이 정산 결과를 알리는 안내 영역을 추가합니다:
    > "기존 Pro 플랜의 남은 이용분 1,933원이 Studio 결제 금액에서 차감되었습니다. (실제 결제 금액: 1,967원)"

### STEP 9. 관리자 구독 관리 화면에서 carryover 제거
- **대상**: [AdminSubscriptions.jsx](file:///d:/final_project/Human_Final_PJ/frontend/src/pages/garim/AdminSubscriptions.jsx) / `backend/services/admin.py`
- **수정**:
  - 활성 구독 목록 및 상세 모달에서 `이월 기간`, `대체 구독 플랜` 등의 컬럼과 함수(`getSupersededPlanName`)를 제거합니다.
  - 대신 구독 상세 모달의 "플랜 변경 이력" 테이블에 정산 금액 컬럼 4개(대상 금액, 잔여 이용분 차감, 실제 청구액 등)를 노출하도록 수정합니다.

---

## 5. 테스트 케이스 마이그레이션

### STEP 10. 기존 carryover 테스트 기대값 삭제
- **대상**: `backend/tests/test_subscription.py`, `backend/tests/test_payment.py`, `backend/tests/test_admin_subscription_check.py`
- **수정**: `apply_upgrade_with_carryover` 구문을 기조로 작성된 모든 구형 테스트 검증 논리를 제거합니다.

### STEP 11. 정산(Proration) 테스트 구축
- **추가할 테스트 케이스**:
  - Pro(2,900원, 30일 기간 중 20일 남음) 상태에서 Studio(3,900원) 업그레이드 시 `remaining_amount = 1933`, `charged_amount = 1967`로 정상 환산되는지 테스트.
  - 업그레이드 승인 직후 새 상위 구독이 `active`로 생성되고 기존 하위 구독은 `cancelled`로 즉시 마감되는지 검증.
  - 차액이 0원일 때 Toss PG 요청 없이 0원 업그레이드 계약이 체결되고 `billing_key_id`가 정상 매핑되는지 검증.

---

## 6. 최종 실행 체크리스트 (Verifications)

- [ ] `subscriptions` 테이블에서 `upgraded_at`, `superseded_by_subscription_id`, `carried_over_days`, `original_period_end` 컬럼 및 제약 제거 (v12 SQL 반영 완료, 로컬 DB 수동 마이그레이션 또는 컨테이너 재생성 시 자동 적용)
- [ ] `subscription_plan_changes` 테이블에서 `remaining_days`, `from_subscription_new_end` 제거 (v12 SQL 반영 완료, 로컬 DB 수동 마이그레이션 또는 컨테이너 재생성 시 자동 적용)
- [ ] `subscription_plan_changes` 테이블에 `remaining_amount`, `target_plan_amount`, `discount_amount`, `charged_amount` 정산 정보 컬럼 추가 및 체크 제약 생성 (v12 SQL 반영 완료, 로컬 DB 수동 마이그레이션 또는 컨테이너 재생성 시 자동 적용)
- [x] 엑셀 설계 문서와 초기화 DDL 파일에서 carryover 흔적 일치화 정리 (v12 선작업 완료)
- [ ] `subscription.py` 내 `calculate_upgrade_proration` 추가 및 `apply_upgrade_with_proration` (빌링키 이식 포함) 완성
- [ ] `payment.py` 내 `confirm_payment` 및 `confirm_billing_payment` (0원 업그레이드 처리 포함) 결제 전 정산금 반영
- [ ] 사용자 결제 정보 API에서 carryover 응답 제거 및 `latest_upgrade_proration` 포맷 적용
- [ ] Pricing / Billing / AdminSubscriptions 화면에서 carryover UI 제거 및 정산 정보 노출 보완
- [ ] carryover 구형 테스트 삭제 및 proration 시나리오 기반 테스트 갱신
- [ ] powershell 텍스트 검색을 활용하여 코드 및 문서 상에 carryover 잔여 찌꺼기 검색하여 최종 완수 검증
- [ ] 프런트엔드 프로덕션 빌드 성공 여부 검증
