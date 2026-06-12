# 멀티 워커 동작 가능성 점검

## 결론

현재 구현은 워커를 여러 개 실행하는 것 자체는 가능하지만, 여러 워커가 동시에 안전하게 같은 큐를 처리할 수 있는 구조라고 보기는 어렵다.

특히 `GET /worker/jobs/next`와 `POST /worker/jobs/{job_id}/accept`가 분리되어 있어 여러 워커가 같은 queued job을 동시에 조회할 수 있다. `accept` 단계의 DB 업데이트 조건 때문에 최종적으로 `queued -> processing` 변경은 한 워커만 성공하지만, Colab 워커 클라이언트가 accept 결과를 엄격히 확인하지 않아 중복 처리로 이어질 수 있다.

## 현재 구현 흐름

1. Colab 워커가 `/worker/jobs/next`를 호출한다.
2. 백엔드는 `analysis_jobs`에서 `status = 'queued'`이고 `cancel_requested = false`인 job 1개를 조회해 반환한다.
3. Colab 워커가 `/worker/jobs/{job_id}/accept`를 호출한다.
4. 백엔드는 `UPDATE analysis_jobs ... WHERE job_id = :job_id AND status = 'queued'`로 상태를 `processing`으로 바꾼다.
5. 워커는 파일 다운로드, 분석, progress, heartbeat, complete/fail 보고를 진행한다.

## 확인한 근거

- `backend/services/worker.py`
  - `get_next_job()`은 queued job을 단순 조회한다.
  - 조회 쿼리에 `FOR UPDATE`, `SKIP LOCKED` 같은 row lock 기반 dequeue 처리가 없다.
  - `accept_job()`은 `WHERE job_id = :job_id AND status = 'queued'` 조건으로 한 번만 `processing` 전환되도록 한다.
- `backend/controllers/worker.py`
  - `AcceptJobRequest`에는 `worker_id`가 있지만 `accept_job(job_id)` 호출 시 전달되지 않는다.
  - 따라서 어떤 워커가 job을 소유했는지 `analysis_jobs`에 기록하거나 검증하지 않는다.
- `colab/garim_colab_worker.py`
  - `run_once()`는 `get_next_job()` 이후 `accept_job(job_id)`를 호출한다.
  - accept 응답이 실제 수락 성공인지 확인하지 않고 이후 다운로드/분석을 계속 진행한다.
- `docker/database/init/0_init_table_v12.sql`
  - `job_worker_heartbeats`에는 `worker_id` 기록 구조가 있다.
  - 하지만 job claim/assignment를 강제하는 구조는 확인되지 않았다.

## 멀티 워커에서 가능한 문제

### 중복 조회

두 워커가 거의 동시에 `/worker/jobs/next`를 호출하면 같은 queued job을 받을 수 있다.

### 중복 처리 가능성

첫 번째 워커는 accept에 성공해 job을 `processing`으로 변경한다. 두 번째 워커의 accept는 실제로는 새 claim에 실패하지만, 현재 응답이 오류로 강하게 처리되지 않고 Colab 워커도 결과를 검증하지 않는다. 이 경우 두 번째 워커도 같은 파일을 다운로드하고 분석을 진행할 수 있다.

### worker_id 미활용

progress, complete, fail 요청 body에 `worker_id`는 포함되지만 job 소유권 검증에 쓰이지 않는다. 따라서 어떤 워커가 claim한 job인지 기준으로 후속 요청을 제한하지 못한다.

## 현재 상태에서의 판단

- 단일 워커: 현재 구조로 동작 가능성이 높다.
- 여러 워커 실행: 실행은 가능하다.
- 여러 워커 병렬 처리: queued job이 여러 개 있으면 일부 병렬 처리는 될 수 있다.
- 안전한 멀티 워커 운영: 아직 부족하다.

## 개선 방향

### 필수

- `get_next_job + accept_job`을 하나의 원자적 claim 동작으로 합친다.
- PostgreSQL 기준으로는 `FOR UPDATE SKIP LOCKED` 또는 `UPDATE ... WHERE job_id IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING ...` 패턴을 검토한다.
- accept 실패 또는 이미 처리 중인 job이면 Colab 워커가 즉시 해당 job 처리를 중단하고 다음 polling으로 넘어가게 한다.

### 권장

- `analysis_jobs`에 `worker_id`, `claimed_at` 같은 할당 정보를 기록하거나 별도 assignment/history 테이블을 사용한다.
- progress, complete, fail 요청에서 claim된 `worker_id`와 요청 `worker_id`가 일치하는지 검증한다.
- accept 실패 응답은 `200 OK`보다 `409 Conflict`처럼 워커 클라이언트가 명확히 분기할 수 있는 상태 코드가 적합하다.

### 후순위

- worker heartbeat를 기준으로 timeout/retry 정책을 구현한다.
- 오래된 `processing` job을 재시도 큐로 되돌리는 복구 작업을 추가한다.
- 멀티 워커 동시 claim 테스트를 추가한다.

## 검증 기록

- 실행한 명령어:

```powershell
python -m pytest tests\test_worker_cancel_flow.py tests\test_worker_results_flow.py tests\test_analysis_progress_flow.py
```

- 결과: 일부 실패
- 통과: `tests/test_worker_cancel_flow.py`, `tests/test_worker_results_flow.py`
- 실패: `tests/test_analysis_progress_flow.py` 3개
- 실패 원인: `create_analysis_job()`에서 크레딧 차감 SQL이 추가되었지만 해당 테스트의 fake session이 `UPDATE user_credit_balances ... RETURNING balance` SQL을 처리하지 못한다.
- 비고: 이 실패는 멀티 워커 동시성 검증 실패라기보다 테스트 fixture가 최신 결제/크레딧 로직을 따라가지 못한 문제로 보인다.

