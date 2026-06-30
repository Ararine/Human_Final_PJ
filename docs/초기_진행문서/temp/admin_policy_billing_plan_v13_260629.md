# admin/policy 월/년 결제 정책 v13 작업 계획

## 작업 목표

`admin/policy`의 구독 플랜 수정 팝업을 정리하고, 구독 플랜의 월/년 결제 금액과 제공 크레딧을 각각 관리할 수 있도록 DB v13 스키마, DB 설계 문서, 백엔드 API, 결제 로직, 프론트 화면을 함께 수정한다.

## 고정 전제

1. DB는 초기화할 예정이므로 기존 DB에 대한 `ALTER TABLE` 작업은 진행하지 않는다.
2. v13 초기화 SQL과 DB 설계 문서만 v13 기준으로 업데이트한다.
3. 연 결제 전용 값이 비어 있으면 기존 계산식을 fallback으로 유지한다.
   - 연 결제 금액: `price_amount * 10`
   - 연 제공 크레딧: `credits * 12`
4. `badge_class` 컬럼은 삭제하지 않는다. 이번 작업에서는 admin 수정 팝업의 `배지 스타일` 입력만 제거한다.
5. 관련 없는 리팩토링, 파일 삭제, 인증/권한 우회, 테스트 약화는 하지 않는다.

## 핵심 변경 요약

### 팝업 UI 정리

- 구독 플랜 수정/추가 팝업 본문 하단의 `문의 내역` 링크를 제거한다.
- 구독 플랜 미리보기 하단의 `문의 내역` 링크를 제거한다.
- 크레딧 플랜 수정/추가 팝업 본문 하단의 `문의 내역` 링크를 제거한다.
- 크레딧 플랜 미리보기 하단의 `문의 내역` 링크를 제거한다.
- 구독 플랜 폼의 `배지 스타일` 입력을 제거한다.

### 월/년 결제 정책 분리

- 기존 `price_amount`, `credits`는 월 결제 기준으로 유지한다.
- v13에서 `plans` 테이블에 연 결제 전용 컬럼을 추가한다.
  - `yearly_price_amount integer`
  - `yearly_credits integer`
- 연 결제 컬럼 값이 없으면 기존 계산식으로 표시/결제/크레딧 지급을 처리한다.

## 수정 대상 파일

### DB

- `docker/database/init/0_init_table_v13.sql`
  - `0_init_table_v12.sql` 기반으로 생성한다.
  - `plans` 테이블에 `yearly_price_amount`, `yearly_credits`를 추가한다.
  - `COMMENT ON COLUMN`을 추가한다.
  - 초기 seed/upsert 구문에 새 컬럼을 포함한다.
  - 기존 DB용 ALTER 구문은 작성하지 않는다.

- `docs/초기_진행문서/db/Garim_DB_Design_final_clean_v13.xlsx`
  - 기존 v12 DB 설계 문서를 기반으로 v13 문서를 만든다.
  - `plans` 정의에 `yearly_price_amount`, `yearly_credits`를 추가한다.
  - `price_amount`, `credits`는 월 결제 기준임을 명시한다.
  - 연 결제 컬럼은 값이 없으면 fallback 계산식을 사용한다고 설명한다.

### Backend

- `backend/services/admin.py`
  - `PLAN_FIELDS`에 `yearly_price_amount`, `yearly_credits`를 추가한다.
  - 관리자 구독 플랜 목록/생성/수정 SQL의 SELECT/RETURNING에 새 컬럼을 포함한다.
  - `/admin/policy` 응답의 `payment.plans`에 `yearlyPrice`, `yearlyCredits`를 포함한다.
  - 기존 `price`, `credits`는 유지해 기존 프론트 호환성을 보존한다.

- `backend/services/payment.py`
  - 구독 상품 조회 시 `yearly_price_amount`, `yearly_credits`를 함께 조회한다.
  - `billingCycle === "yearly"`이면 연 결제 전용 값이 있을 때 해당 값을 사용한다.
  - 연 결제 전용 값이 없으면 `price_amount * 10`, `credits * 12`를 사용한다.
  - `billingCycle === "monthly"`이면 기존 `price_amount`, `credits`를 사용한다.

- `backend/services/subscription.py`
  - 현재 구독/업그레이드/다운그레이드 계산에서 연 구독의 가격 기준이 필요한지 확인한다.
  - 필요한 경우 기존 동작을 깨지 않는 범위에서 연 결제 금액 fallback helper를 공유하거나 동일 규칙으로 보정한다.

- `backend/services/subscription_renewal.py`
  - 연 구독 갱신 시 청구 금액이 월 금액으로 떨어지지 않는지 확인한다.
  - 필요 시 구독 row 또는 plan row의 주기 기준으로 연 결제 금액 fallback 규칙을 적용한다.

### Frontend

- `frontend/src/pages/garim/AdminPolicy.jsx`
  - `SUBSCRIPTION_DEFAULT`에 `yearly_price_amount`, `yearly_credits`를 추가한다.
  - `SUBSCRIPTION_NUMBER_FIELDS`에 새 필드를 추가한다.
  - `BADGE_CLASS_OPTIONS`와 `배지 스타일` SelectField 사용을 제거한다.
  - 구독 결제 정책 섹션을 `월 결제` / `연 결제` 탭으로 분리한다.
  - 월 결제 탭:
    - `price_amount`
    - `credits`
  - 연 결제 탭:
    - `yearly_price_amount`
    - `yearly_credits`
  - 연 결제 입력값은 비워둘 수 있게 유지한다.
  - 미리보기는 선택한 탭에 따라 월/년 금액과 크레딧을 표시한다.
  - 연 결제 값이 비어 있으면 fallback 계산값을 표시한다.
  - 폼/미리보기 하단의 `문의 내역` 링크를 모두 제거한다.

- `frontend/src/hooks/usePricingPlans.js`
  - `payment.yearlyPrice`, `payment.yearlyCredits`를 plan 객체에서 사용할 수 있게 유지한다.
  - 기존 `payment.price`, `payment.credits`는 월 결제 기준으로 유지한다.

- `frontend/src/pages/garim/Pricing.jsx`
  - 연 결제 표시 시 `yearlyPrice`가 있으면 사용하고 없으면 `price * 10`을 사용한다.
  - 연 제공 크레딧 표시 시 `yearlyCredits`가 있으면 사용하고 없으면 `credits * 12`를 사용한다.
  - 결제 페이지 이동 파라미터도 선택된 결제 주기의 실제 금액/크레딧으로 전달한다.

- `frontend/src/pages/garim/Payment.jsx`
  - URL 파라미터로 넘어온 금액/크레딧 표시가 월/년 선택값과 맞는지 확인한다.
  - 필요 시 표시 문구만 보정한다.

- `frontend/src/pages/garim/PaymentSuccess.jsx`
  - `billingCycle` 전달은 기존 방식을 유지한다.
  - 백엔드 confirm 로직이 실제 금액/크레딧을 검증하므로 프론트는 표시/전달 일관성만 확인한다.

## 권장 구현 순서

1. 현재 작업 전 상태 확인
   - `git status`
   - 관련 파일의 사용자 변경 여부 확인

2. DB v13 파일 생성
   - `0_init_table_v12.sql`을 기반으로 `0_init_table_v13.sql` 생성
   - `plans` 테이블, 컬럼 코멘트, seed/upsert 구문 수정

3. DB 설계 xlsx v13 생성/수정
   - v12 문서가 있으면 v13 파일로 복사 후 수정
   - `plans` 컬럼 설명 추가

4. 백엔드 관리자 API 반영
   - `admin.py`에 새 필드 추가
   - 관리자 플랜 CRUD 테스트 갱신

5. 백엔드 결제 로직 반영
   - 연 결제 금액/크레딧 fallback 규칙 추가
   - 결제 테스트에 전용 값 사용 케이스와 fallback 케이스 추가

6. 프론트 admin/policy 모달 수정
   - 하단 `문의 내역` 링크 제거
   - `배지 스타일` 입력 제거
   - 월/년 결제 정책 탭 추가
   - 미리보기 탭/표시 로직 추가

7. 프론트 pricing 결제 흐름 수정
   - 정책 응답의 연 결제 필드 사용
   - fallback 유지
   - 결제 URL 파라미터 확인

8. 최소 검증 실행
   - 백엔드 관련 pytest
   - 프론트 build 또는 관련 smoke check
   - SQL/xlsx 파일 존재 및 주요 컬럼 확인

## 테스트 계획

### Backend

- `backend/tests/test_admin_policy.py`
  - 관리자 플랜 목록 응답에 `yearly_price_amount`, `yearly_credits`가 포함되는지 확인한다.
  - 관리자 플랜 생성/수정 payload에 새 필드가 포함될 수 있는지 확인한다.
  - `/admin/policy` 응답에 `yearlyPrice`, `yearlyCredits`가 포함되는지 확인한다.

- `backend/tests/test_payment.py`
  - 연 결제 전용 값이 있을 때 해당 금액으로 결제 검증하는지 확인한다.
  - 연 결제 전용 값이 없을 때 `price_amount * 10`으로 결제 검증하는지 확인한다.
  - 연 제공 크레딧 전용 값이 있을 때 해당 크레딧을 지급하는지 확인한다.
  - 연 제공 크레딧 전용 값이 없을 때 `credits * 12`를 지급하는지 확인한다.

### Frontend

- `admin/policy`
  - 구독 플랜 수정 팝업 하단에 `문의 내역` 링크가 없는지 확인한다.
  - 크레딧 플랜 수정 팝업 하단에 `문의 내역` 링크가 없는지 확인한다.
  - 구독 플랜 폼에 `배지 스타일` 입력이 없는지 확인한다.
  - 결제 정책 섹션에서 `월 결제` / `연 결제` 탭 전환이 되는지 확인한다.
  - 연 결제 값을 비웠을 때 미리보기가 fallback 계산값을 보여주는지 확인한다.
  - 연 결제 값을 입력했을 때 미리보기가 입력값을 보여주는지 확인한다.

- `pricing`
  - 월 결제 탭에서 월 금액/월 크레딧을 보여주는지 확인한다.
  - 연 결제 탭에서 연 결제 전용 값이 있으면 해당 값을 보여주는지 확인한다.
  - 연 결제 전용 값이 없으면 기존 fallback 계산값을 보여주는지 확인한다.
  - 결제 이동 URL에 선택한 주기의 금액/크레딧이 들어가는지 확인한다.

## 추가 고려사항

### 필수

- 연 구독 갱신 로직이 월 금액으로 청구되지 않는지 확인해야 한다.
- 결제 금액 검증은 프론트 URL 파라미터가 아니라 백엔드 DB 정책 값을 기준으로 유지해야 한다.
- `yearly_price_amount`, `yearly_credits`가 `0`, `null`, 빈 문자열일 때 fallback 처리 기준을 일관되게 적용해야 한다.

### 권장

- 연 결제 fallback 계산은 프론트와 백엔드에서 같은 규칙으로 helper화한다.
- `badge_class`는 DB 컬럼과 기존 응답 필드 유지, admin 입력 UI만 제거한다.
- 정책 응답은 기존 `price`, `credits`를 유지하고 연 결제 필드만 추가한다.

### 후순위

- 결제 주기가 월/년 외로 늘어나면 `plan_prices` 별도 테이블 분리를 검토한다.
- 관리자 목록 테이블에서도 월/년 금액을 나란히 보여줄지 별도 UX로 개선할 수 있다.

## 완료 보고 시 포함할 내용

- 변경 파일 목록
- DB v13 스키마 반영 내용
- xlsx 문서 반영 내용
- 월/년 결제 fallback 동작 설명
- 실행한 테스트/빌드 명령과 결과
- 미실행 검증이 있으면 `미실행`으로 명시
