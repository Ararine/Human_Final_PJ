# Claude Code v7 실행 가이드

이 문서는 Claude Code에서 `GARIM_front_back_colab_upload_progress_db_v7_IMPLEMENTATION_MASTER.md`를 기준으로 작업할 때 사용할 단계별 지시문이다.

기준 문서:

```text
docs/upload&progress/GARIM_front_back_colab_upload_progress_db_v7_IMPLEMENTATION_MASTER.md
```

핵심 방향:

```text
DB v6 스키마는 변경하지 않는다.
로컬 백엔드를 ngrok으로 공개한다.
Colab worker는 백엔드 ngrok URL의 /worker/* API를 polling/call 한다.
프론트는 기존 /analysis/jobs/{job_id} polling 구조를 유지한다.
docs/colab/ 아래 새 파일은 Colab 셀 형식으로 작성한다.
```

---

## 공통 작업 규칙

Claude Code에 각 단계를 지시할 때 아래 조건을 매번 포함한다.

```text
- DB 스키마 변경 금지
- v6에서 구현된 업로드/분석 진행률/프론트 polling 흐름 유지
- 해당 단계 범위 밖의 리팩터링 금지
- docs/colab/ 아래 새 파일은 Colab 셀 형식(# %% [markdown], # %%)으로 작성
- 테스트 추가 또는 기존 테스트 보강
- 작업 후 검증 명령 실행
- 완료 후 수정 파일 목록, 테스트 결과, 다음 단계 가능 여부만 보고하고 멈춤
```

한 번에 전체를 진행시키지 말고 반드시 단계별로 진행한다.

---

## 1단계 지시문: Worker 파일 다운로드 API

Claude Code에 아래처럼 지시한다.

```text
docs/upload&progress/GARIM_front_back_colab_upload_progress_db_v7_IMPLEMENTATION_MASTER.md 를 기준으로 v7 1단계만 진행해줘.

목표:
- Colab worker가 업로드된 원본 파일을 백엔드 ngrok URL로 다운로드할 수 있게 한다.

범위:
- /worker/files/{upload_id}/download API 추가
- 기존 /worker/files/{upload_id} 정보 조회 API 유지
- WORKER_SECRET Bearer 인증 유지
- uploads.status = uploaded 인 파일만 다운로드 허용
- FileResponse로 실제 파일 바이너리 반환
- DB 스키마 변경 금지

수정 예상 파일:
- backend/services/worker.py
- backend/controllers/worker.py
- backend/routes/worker.py
- tests/test_worker_file_download.py 또는 기존 worker 테스트

검증:
- pytest tests/test_worker_file_download.py -q
- pytest -q

완료 후:
- 수정 파일 목록
- 테스트 결과
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 2단계 지시문: Colab worker 클라이언트

1단계 테스트가 통과한 뒤 진행한다.

```text
v7 2단계만 진행해줘.

목표:
- Colab에서 백엔드 worker API를 polling/call 하는 worker 클라이언트 스크립트를 만든다.

중요 조건:
- docs/colab/ 아래 새 파일은 반드시 Colab 셀 형식으로 작성
- # %% [markdown], # %% 셀 마커 사용
- 설치 셀, 설정 셀, API helper 셀, worker loop 셀, 실행 셀 분리
- 로컬 Windows 경로 의존 금지
- /content 경로 기준 사용
- DB 스키마 변경 금지

생성 파일:
- docs/colab/garim_colab_worker.py

필수 기능:
- BACKEND_URL 설정
- WORKER_SECRET 설정
- WORKER_ID 설정
- get_next_job()
- accept_job(job_id)
- download_file(upload_id, output_dir)
- report_progress(...)
- send_heartbeat(...)
- complete_job(...)
- fail_job(...)
- check_cancel(job_id)
- run_once()
- run_loop()

검증:
- python -m py_compile docs/colab/garim_colab_worker.py
- pytest tests/test_analysis_progress_flow.py -q

완료 후:
- 수정 파일 목록
- 테스트 결과
- Colab에서 어떤 셀 순서로 실행하면 되는지
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 3단계 지시문: Cancel 확인 흐름

```text
v7 3단계만 진행해줘.

목표:
- 프론트에서 분석 취소를 누르면 Colab worker가 취소 상태를 확인하고 complete로 덮어쓰지 않게 한다.

범위:
- worker용 job status 조회 API 추가 검토
- GET /worker/jobs/{job_id}/status 추가
- cancel_requested, status, current_stage, total_progress 반환
- Colab worker의 check_cancel(job_id) 연결
- DB 스키마 변경 금지

수정 예상 파일:
- backend/services/worker.py
- backend/controllers/worker.py
- backend/routes/worker.py
- docs/colab/garim_colab_worker.py
- tests/test_worker_cancel_flow.py

검증:
- pytest tests/test_worker_cancel_flow.py -q
- pytest tests/test_analysis_progress_flow.py -q
- pytest -q

완료 후:
- 수정 파일 목록
- 테스트 결과
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 4단계 지시문: 확장 가능한 분석 파이프라인

```text
v7 4단계만 진행해줘.

목표:
- STT/PII/beep 1차 분석을 연결하되, 이후 다른 분석 로직도 analyzer 단위로 추가 가능한 구조로 만든다.

중요 조건:
- docs/colab/ 아래 파일은 Colab 셀 형식으로 작성
- STT/PII/beep에 고정된 구조로 만들지 말 것
- analyzer 단위 확장 구조 사용
- 새 analyzer 추가 시 worker loop, progress API, 프론트 진행 화면을 다시 설계하지 않아도 되게 할 것
- DB 스키마 변경 금지

수정/생성 예상 파일:
- docs/colab/garim_colab_worker.py
- docs/colab/garim_pipeline.py
- 필요 시 backend/services/worker.py
- 필요 시 backend/controllers/worker.py

권장 구조:
- analyzer.run(input_path, context)
- analyzer가 stage_name, stage_progress, total_progress, message 보고
- file_download, audio_extract, stt, pii_detect, beep_render, result_upload, completed stage 사용

검증:
- python -m py_compile docs/colab/garim_colab_worker.py
- python -m py_compile docs/colab/garim_pipeline.py

완료 후:
- 수정 파일 목록
- Colab 실행 셀 순서
- analyzer 추가 방법
- 검증 결과
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 5단계 지시문: 분석 결과 저장 API

```text
v7 5단계만 진행해줘.

목표:
- Colab에서 만든 STT/PII/beep 및 이후 analyzer 결과를 백엔드에 저장할 수 있게 한다.

중요 조건:
- DB 스키마 변경 금지
- 기존 결과 저장 테이블이 있으면 사용
- 결과 저장 테이블이 명확하지 않으면 상세 저장은 v8로 분리하고, v7에서는 detection_count/message/summary 수준만 저장

수정 예상 파일:
- backend/services/worker.py
- backend/controllers/worker.py
- backend/routes/worker.py
- docs/colab/garim_colab_worker.py
- tests/test_worker_results_flow.py

API 후보:
- POST /worker/jobs/{job_id}/results/stt
- POST /worker/jobs/{job_id}/results/pii
- POST /worker/jobs/{job_id}/results/artifact

검증:
- pytest tests/test_worker_results_flow.py -q
- pytest -q

완료 후:
- 수정 파일 목록
- 어떤 결과를 어디에 저장했는지
- 저장하지 못한 결과가 있다면 v8 과제로 분리
- 테스트 결과
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 6단계 지시문: 로컬 ngrok 실행 문서화

```text
v7 6단계만 진행해줘.

목표:
- 로컬 백엔드를 ngrok으로 열고 Colab worker가 붙는 절차를 문서화한다.

수정/생성 파일:
- docs/colab/COLAB_WORKER_RUNBOOK.md
- backend/.env.sample
- 필요 시 backend/ngrok.py

문서 포함 내용:
- 로컬 DB/Redis 실행
- 로컬 백엔드 실행
- WORKER_SECRET 설정
- 로컬에서 ngrok 8000 포트 공개
- Colab에서 BACKEND_URL/WORKER_SECRET/WORKER_ID 설정
- Colab worker 실행
- 업로드 후 analysis-progress 화면 확인
- 실패 시 확인할 로그와 DB 테이블

검증:
- pytest -q
- cmd /c npm run build

완료 후:
- 수정 파일 목록
- 실행 순서 요약
- 테스트 결과
- 다음 단계 진행 가능 여부만 보고하고 멈춰줘.
```

---

## 7단계 지시문: E2E 통합 검증

```text
v7 7단계만 진행해줘.

목표:
- 브라우저 업로드부터 Colab 분석 완료까지 전체 흐름을 검증한다.

검증 흐름:
- Docker DB/Redis 실행
- 로컬 백엔드 실행
- 프론트 dev server 실행
- 로컬 ngrok으로 백엔드 공개
- Colab worker 실행
- 프론트에서 샘플 영상 업로드
- analysis-progress 화면 이동 확인
- Colab worker job polling 확인
- 파일 다운로드 확인
- stage progress 프론트 반영 확인
- complete 후 polling 중단 확인
- DB의 analysis_jobs/job_stage_logs/job_worker_heartbeats 확인

검증 명령:
- pytest -q
- cmd /c npm run lint
- cmd /c npm run build
- cmd /c npm run test:garim

완료 후:
- 성공한 항목
- 실패한 항목
- 수동으로 확인한 URL/API/DB 테이블
- 남은 리스크
- 다음 작업 제안만 보고해줘.
```

---

## Claude Code에 주면 안 좋은 지시

아래 방식은 피한다.

```text
v7 전체 다 구현해줘
알아서 고쳐줘
테스트는 나중에 해도 돼
DB도 필요하면 바꿔
Colab 파일은 그냥 Python 파일로 만들어줘
```

이런 지시는 범위가 커져서 v6 구조를 깨거나, Colab에서 바로 실행하기 어려운 파일이 만들어질 수 있다.

---

## 매 단계 완료 후 확인할 질문

Claude Code 결과를 받은 뒤 아래를 확인한다.

```text
1. DB 스키마를 바꾸지 않았는가?
2. 단계 범위 밖 파일을 과하게 수정하지 않았는가?
3. /worker/* 기존 API가 깨지지 않았는가?
4. pytest 결과가 있는가?
5. 프론트 빌드가 필요한 단계라면 build 결과가 있는가?
6. docs/colab/ 파일은 Colab 셀 형식인가?
7. 다음 단계로 넘어가도 되는 근거가 있는가?
```
