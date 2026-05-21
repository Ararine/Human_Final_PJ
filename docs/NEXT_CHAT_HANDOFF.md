# Garim 프로젝트 다음 채팅 인수인계 메모

이 문서는 다음 채팅에서 현재 프로젝트 맥락을 빠르게 이어가기 위한 요약입니다.

## 현재 작업 위치

- 작업 루트: `D:/final_project\Human_Final_PJ`
- 프론트엔드: `D:/final_project\Human_Final_PJ/frontend`
- 백엔드: `D:/final_project\Human_Final_PJ/backend`
- DB 설계 최종본: `D:/final_project\Human_Final_PJ/docs/Garim_DB_Design_final_clean.xlsx`
- 프로젝트 결정 메모: `D:/final_project\Human_Final_PJ/docs/Garim_Project_Notes.md`

## 프로젝트 방향

- Garim은 업로드한 이미지/영상/음성에서 개인정보 노출 위험을 탐지하고, 치환/블러/워터마크/다운로드 흐름을 제공하는 서비스다.
- 현재는 백엔드 완성보다 프론트 화면과 주요 백엔드 연결 흐름을 먼저 맞추는 단계다.
- 자체 이메일/비밀번호 로그인은 사용하지 않는 방향이다.
- 로그인은 Kakao, Google, Facebook, X OAuth를 대상으로 한다.
- Instagram OAuth는 현재 구현 범위에서 제외했지만, 추후 추가 가능성이 있어 DB 설계에는 SNS 확장 테이블을 남겼다.
- 실제 파일 바이너리는 DB에 저장하지 않고, DB에는 저장 경로, 해시, MIME 타입, 크기 등 메타데이터만 저장한다.

## 프론트엔드 상태

- Vite/React 기반이다.
- 포트는 `3000`으로 변경했다.
- `frontend/src/data/garim/pages.js`에서 라우트와 페이지 메타데이터를 관리한다.
- `App.jsx`는 실질적으로 `path`, `component`를 사용한다.
- 기존 HTML 기반 Garim 화면들은 React 컴포넌트로 분리되어 있다.
- 각 페이지 JSX 안에 있던 스타일은 `frontend/src/css/garim-pages` 쪽 CSS 파일로 분리했다.
- `hooks`, `context`, `utils` 폴더가 추가되었고, 라우트 관련 훅 등 일부 구조를 나눴다.
- 로그인 페이지는 Kakao, Google, Facebook, X 버튼이 존재하며, 버튼 클릭 시 백엔드 OAuth start URL로 이동한다.
- Instagram OAuth 버튼/연결 로직은 제거되어야 한다.

## 백엔드 상태

- FastAPI 기반이다.
- 백엔드는 conda 가상환경 `final_1team`에서 실행한다.
- 백엔드 포트는 `8000`으로 맞췄다.
- 이전에 `5000` 포트는 Windows 권한 문제로 바인딩 실패한 적이 있다.
- 주요 라우터:
  - `/uploads`
  - `/auth/{provider}/start`
  - `/auth/{provider}/callback`
  - `/auth/me`
  - `/auth/logout`
- 업로드는 실제 파일을 받아 `UPLOAD_DIR`에 저장하고, 응답으로 `upload_id`, `stored_path`, `content_type`, `size` 등을 반환한다.
- OAuth는 Kakao, Google, Facebook, X provider 설정을 가지고 있다.
- 현재 OAuth 인증 성공 후 signed cookie 기반 흐름이 구현되어 있으나, 이후 Redis/DB 세션 기반으로 개선할 예정으로 논의했다.

## OAuth/세션 결정사항

- 쿠키는 프론트가 아니라 백엔드에서 `Set-Cookie`로 설정한다.
- 프론트는 쿠키를 직접 신뢰하지 않고 `/auth/me`를 호출해서 로그인 여부를 확인해야 한다.
- 세션 ID는 백엔드가 로그인 성공 시 생성하는 예측 불가능한 랜덤 값이다.
- 권장 흐름:
  1. SNS OAuth 성공
  2. 백엔드가 세션 생성
  3. 세션 ID를 HttpOnly 쿠키로 전달
  4. 실제 세션 정보는 서버 저장소(DB 또는 Redis)에 저장
  5. 요청마다 백엔드가 쿠키의 세션 ID를 검증
- 사용자가 쿠키를 임의로 바꾸면, 백엔드는 서버 저장소에 존재하는 세션인지 확인해서 걸러야 한다.
- 더 강하게 하려면 `session_id.signature` 형태로 서명된 세션 쿠키를 사용한다.

## Redis 결정사항

- Redis는 AOF 영속화 없이 진행하기로 했다.
- 중요한 원본 데이터와 최종 이력은 PostgreSQL에 저장한다.
- Redis는 임시 데이터/캐시 중심으로 사용한다.
- 사용 용도:
  - OAuth state
  - 로그인 세션 캐시
  - 대시보드 10초 캐시
  - 진행률 캐시
  - 추후 큐/락/알림 캐시
- 백엔드 환경변수:
  - `REDIS_URL`
  - `REDIS_SESSION_TTL_SECONDS`
  - `REDIS_OAUTH_STATE_TTL_SECONDS`
  - `REDIS_DASHBOARD_CACHE_TTL_SECONDS`
  - `REDIS_PROGRESS_TTL_SECONDS`
- 현재 `.env`와 `.env.sample`에는 `REDIS_URL=redis://final_redis:6379/0`로 들어가 있다.
- 주의:
  - 백엔드도 Docker 네트워크 안에서 실행하면 `redis://final_redis:6379/0`가 맞다.
  - 백엔드를 conda로 로컬 실행하고 Redis만 Docker 컨테이너로 띄운다면 보통 `redis://localhost:6379/0`가 맞다.
  - Docker 권한 문제로 `final_redis` 컨테이너 포트 매핑은 확인하지 못했다.

## Redis 코드 추가 상태

추가/수정된 파일:

- `backend/core/redis.py`
  - `get_redis_client()`
  - `ping_redis()`
- `backend/services/redis_store.py`
  - `get_ttl()`
  - `build_key()`
  - `set_json()`
  - `get_json()`
  - `delete_key()`
  - `save_oauth_state()`
  - `get_oauth_state()`
  - `delete_oauth_state()`
  - `consume_oauth_state()`
  - `save_session()`
  - `get_session()`
  - `delete_session()`
  - `set_dashboard_cache()`
  - `get_dashboard_cache()`
  - `delete_dashboard_cache()`
  - `set_progress()`
  - `get_progress()`
  - `delete_progress()`
  - `redis_healthcheck()`
- `backend/tests/test_redis_store.py`
  - 실제 Redis 없이 fake client로 동작 검증
- `backend/requirement.txt`
  - `redis` 패키지 추가

검증:

```bash
cmd /c "conda activate final_1team && python -m pytest tests/test_redis_store.py tests/test_oauth.py tests/test_upload.py -q -p no:cacheprovider --basetemp D:\final_project\Human_Final_PJ\backend\.pytest_tmp"
```

결과:

- `9 passed`
- FastAPI `example` deprecation warning 등 기존 경고는 있음

## Redis 코드 주의사항

- `backend/services/redis_store.py`와 `backend/core/redis.py`에 함수별 docstring을 추가했다.
- PowerShell 출력에서는 한글이 깨져 보일 수 있다. 파일 자체가 깨졌는지는 에디터에서 직접 확인해야 한다.
- 만약 파일 내 한글 주석/docstring이 실제로 깨져 있으면 UTF-8로 다시 저장하거나 영어 docstring으로 바꾸는 것이 안전하다.

## DB 설계서 상태

최종 파일:

- `D:/final_project\Human_Final_PJ/docs/Garim_DB_Design_final_clean.xlsx`

현재 시트:

1. `01_users`
2. `02_oauth_accounts`
3. `03_user_consents`
4. `04_uploads`
5. `05_analysis_jobs`
6. `06_detections`
7. `07_replacement_actions`
8. `08_processed_files`
9. `09_download_events`
10. `10_plans`
11. `11_subscriptions`
12. `12_payments`
13. `13_face_whitelists`
14. `14_abuse_reports`
15. `15_audit_logs`
16. `16_sns_connections`
17. `17_sns_media_items`
18. `18_sns_diagnosis_jobs`
19. `19_notification_events`
20. `20_analysis_artifacts`
21. `21_deletion_events`
22. `22_worker_tasks`
23. `23_indexes`

DB 설계서에 반영된 주요 결정:

- SNS 확장 테이블 포함
- 알림 이벤트 테이블 포함
- 분석 산출물 테이블 포함
- 삭제 완료 이력 테이블 포함
- 워커 처리 이력 테이블 포함
- 인덱스 설계 시트 포함
- 모든 테이블 시트에 `컬럼 역할` 컬럼 추가
- `??`로 깨진 셀은 최종 스캔 결과 `0개`로 정리
- `22_worker_tasks`는 `21_deletion_events` 스타일에 맞춰 재정리
- `22_worker_tasks`의 `제약조건` 칸은 실제 DB 제약식 중심으로 정리

`22_worker_tasks` 제약조건 예:

- `primary key`
- `references analysis_jobs(job_id) on delete cascade`
- `references uploads(upload_id) on delete set null`
- `check (task_type in (...))`
- `check (status in (...))`
- `check (progress_percent between 0 and 100)`
- `check (priority >= 0)`
- `check (attempt_no >= 1)`
- `check (duration_ms >= 0)`

## DB 설계와 프로젝트 간 차이/주의점

- DB 설계서는 현재 코드보다 앞서 있다. 현재 백엔드는 OAuth와 업로드 일부만 구현되어 있고, DB 전체 테이블이 코드로 구현된 상태는 아니다.
- `16_sns_connections`에는 Instagram 관련 표현이 일부 남아 있다. 현재 구현 범위에서는 Instagram OAuth를 제외하지만, 추후 확장 대비로 볼 수 있다.
- 프론트에는 `/signup`, `/password-reset` 페이지가 남아 있지만, 자체 로그인은 사용하지 않는 방향이다. 나중에 제거하거나 OAuth 안내 페이지로 바꾸는 것이 좋다.
- `23_indexes`는 설계용 목록이다. 실제 DB에 적용하려면 PostgreSQL `CREATE INDEX` SQL 또는 migration으로 변환해야 한다.

## 보관/운영 정책 결정사항

- 원본 파일: 처리 완료 후 12시간 보관
- Free 결과 파일: 7일 보관
- 1회권 결과 파일: 30일 보관
- 구독/플랜 결과 파일: 90일 보관
- 메타데이터/분석 요약: 90일 보관
- 회원 탈퇴: 7일 유예 후 개인정보 삭제 또는 익명화
- 삭제 완료/실패 이력은 `deletion_events`에 기록
- 진행률은 DB에 매번 쓰지 않고 5% 단위 변화 시 업데이트
- 대시보드 통계는 실시간 무한 조회가 아니라 10초 주기 조회
- 반복 집계는 캐시 또는 요약 데이터를 사용하고, 원본 테이블 전체 count를 매번 돌리지 않는다.

## 최근 테스트/검증

Redis 유틸 추가 후 실행한 검증:

```bash
cmd /c "conda activate final_1team && python -m pytest tests/test_redis_store.py -q -p no:cacheprovider --basetemp D:\final_project\Human_Final_PJ\backend\.pytest_tmp"
```

결과:

- `3 passed`

전체 관련 테스트:

```bash
cmd /c "conda activate final_1team && python -m pytest tests/test_redis_store.py tests/test_oauth.py tests/test_upload.py -q -p no:cacheprovider --basetemp D:\final_project\Human_Final_PJ\backend\.pytest_tmp"
```

결과:

- `9 passed`

## 다음에 이어서 하면 좋은 작업

1. Redis 연결을 실제 OAuth state 저장소로 연결
   - 현재 `oauth.py`에는 `_oauth_states = {}` 인메모리 저장이 남아 있다.
   - 다음 단계에서 `services.redis_store.save_oauth_state()`와 `consume_oauth_state()`로 교체하면 된다.

2. 로그인 세션을 signed payload cookie에서 서버 세션 방식으로 전환
   - 현재는 `garim_auth` signed cookie가 사용자 정보를 담고 있다.
   - 목표는 `session_id`만 쿠키로 보내고, 세션 본문은 DB/Redis에서 검증하는 방식이다.

3. `user_sessions` 테이블 추가 여부 결정
   - Redis만 세션 캐시로 쓸지, DB에 세션 원본을 둘지 결정해야 한다.
   - 앞선 대화에서는 중요한 데이터는 DB에 저장하기로 했으므로 `user_sessions` 테이블 추가가 자연스럽다.

4. `23_indexes`를 실제 PostgreSQL migration SQL로 변환
   - 현재는 설계 시트다.

5. DB 설계서의 `16_sns_connections` 표현 정리
   - Instagram 제외 정책과 혼동되지 않도록 `추후 확장 가능한 SNS provider` 식으로 바꾸면 좋다.

6. 백엔드 실제 DB 모델/마이그레이션 작업 시작
   - 현재 DB 설계서가 있으므로 SQLAlchemy 모델 또는 Alembic migration으로 옮길 수 있다.

7. 한글 깨짐 확인
   - PowerShell 출력은 한글이 자주 깨진다.
   - 실제 파일이 깨진 것인지, 콘솔 출력만 깨진 것인지 에디터에서 확인해야 한다.

## 중요한 주의

- `backend/.env`에는 실제 Kakao OAuth 값이 들어가 있을 수 있으므로 외부 공유하면 안 된다.
- 새 채팅에서 `.env` 내용을 그대로 출력하거나 공유하지 않는 것이 좋다.
- Docker 명령은 현재 권한 문제로 실패한 적이 있다.
- `D:/final_project\Human_Final_PJ`는 git 저장소로 인식되지 않았다.
