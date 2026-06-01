# Garim Colab Worker 실행 가이드

로컬 백엔드를 Cloudflare Tunnel로 공개하고 Colab worker를 연결하는 전체 절차.

---

## 사전 준비

| 항목 | 버전/조건 |
|---|---|
| Docker Desktop | 실행 중 |
| Python 3.10+ | 백엔드 가상환경 |
| Node.js 18+ | 프론트 dev server |
| Cloudflare Tunnel | `cloudflared` 실행 가능 환경 |
| Google Colab | GPU 런타임 권장 (STT 속도) |

---

## 1단계: DB / Redis 실행

```bash
cd docker
docker compose up -d
```

컨테이너 상태 확인:

```bash
docker compose ps
# final_db, final_redis 모두 healthy 여야 한다.
```

> `docker/.env` 에 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_PORT`, `REDIS_PORT` 가 설정되어 있어야 한다.
> 초기 실행 시 `docker/database/init/0_init_table_v6.sql` 이 자동으로 적용된다.

---

## 2단계: 백엔드 .env 설정

`backend/.env` 파일을 `backend/.env.sample` 기준으로 생성하고 아래 항목을 반드시 설정한다.

```dotenv
# DB 연결 (docker/.env 와 일치시킬 것)
DB_HOST=localhost
DB_PORT=5433
DB_USER=1team
DB_PASSWORD=1team
DB_NAME=1team

# Redis
REDIS_URL=redis://localhost:6379/0

# 백엔드 서버
HOST=0.0.0.0
PORT=8001

# Colab Worker 인증 시크릿 — Worker 와 반드시 동일한 값 사용
WORKER_SECRET=여기에_긴_임의_문자열_입력

# Cloudflare Tunnel은 별도 계정 토큰 없이 실행 가능
```

`WORKER_SECRET` 생성 예시:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 3단계: 로컬 백엔드 실행

```bash
cd backend
pip install -r requirements.txt   # 최초 1회
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

서버 정상 확인:

```
http://localhost:8001/docs
```

---

## 4단계: Cloudflare Tunnel로 8001 포트 공개

**방법 A — 백엔드 스크립트 사용 (권장)**

```bash
cd backend
python cloudflare_tunnel.py
```

출력 예시:

```
Cloudflare Tunnel URL: https://xxxx.trycloudflare.com
Colab garim_colab_worker.py 의 BACKEND_URL 에 위 URL 을 입력하세요.
```

**방법 B — cloudflared 직접 실행**

```bash
cloudflared tunnel --url http://localhost:8001
```

> Cloudflare Tunnel 세션이 종료되면 URL이 바뀐다. 새 URL을 Colab 에 다시 입력해야 한다.

---

## 5단계: Colab worker 설정 및 실행

### 5-1. 분석 파이프라인 파일을 Drive에 업로드

Google Drive의 `MyDrive/garim_colab` 폴더에 아래 파일을 업로드한다.

```text
garim_pipeline.py
garim_visual_pii_ocr_pipeline.py
```

worker가 `garim_pipeline.py`를 import하면 필요한 패키지를 설치하고
`VisualOCR → AudioExtract → STT → PIIDetect → BeepRender` analyzer를 등록한다.
`WHISPER_MODEL_SIZE`는 `garim_pipeline.py`에서 `medium` 정도로 낮춰도 된다.

### 5-2. garim_colab_worker.py 셀 순서대로 실행

`docs/colab/garim_colab_worker.py` 를 Colab에 올리고 순서대로 실행한다.

1. `[설치]` 셀
2. `[Config]` 셀 — **아래 3개 값 반드시 수정**

```python
BACKEND_URL   = "https://xxxx.trycloudflare.com"   # 4단계에서 복사한 URL (슬래시 없이)
WORKER_SECRET = "여기에_백엔드_env와_동일한_값"
WORKER_ID     = "colab-worker-01"                # 식별 이름 (자유)
```

3. `[API 헬퍼]` 셀
4. `[Heartbeat 스레드]` 셀
5. `[파이프라인 연동]` 셀
6. `[Worker Loop]` 셀
7. `[실행]` 셀 — `run_loop()` 실행

```python
run_loop()   # job을 계속 polling (■ 버튼으로 중단)
```

---

## 6단계: 프론트 dev server 실행 및 업로드 확인

```bash
cd frontend
npm install   # 최초 1회
npm run dev
```

브라우저에서 `http://localhost:3000` 접속 후:

1. 로그인
2. `업로드` 페이지에서 영상 파일 업로드
3. 업로드 완료 후 자동으로 `analysis-progress` 페이지(`/analysis-progress`)로 이동
4. 진행률 바가 `file_download → visual_ocr → audio_extract → stt → pii_detect → beep_render → result_upload → completed` 순으로 업데이트되는지 확인

Colab 콘솔에서도 아래와 같은 로그가 출력되어야 한다:

```
09:01:23 [INFO] job 수신: <job_id> | upload: <upload_id>
09:01:24 [INFO] job 수락 완료
09:01:25 [INFO] 파일 다운로드 완료: upload_xxx.mp4 (45.3 MB)
09:01:50 [INFO] 시각 OCR 결과물 저장 완료: /content/garim_visual_pii/<upload_id>/visual_pii_detections.json
09:02:10 [INFO] 파이프라인 완료 | detection_count=3
09:02:11 [INFO] STT 결과 저장 완료: 42개 세그먼트
09:02:11 [INFO] job 완료: <job_id>
```

---

## 실패 시 확인 항목

### 로그

| 위치 | 확인 방법 |
|---|---|
| 백엔드 콘솔 | `uvicorn` 터미널 — HTTP 요청/응답, 오류 스택 |
| Colab 셀 출력 | `[ERROR]` 또는 `[WARNING]` 라인 |
| Cloudflare 터미널 로그 | 터널 URL 출력 및 연결 로그 |

### DB 테이블

```sql
-- job 상태 확인
SELECT job_id, status, current_stage, total_progress, error_code, error_message
FROM analysis_jobs
ORDER BY created_at DESC
LIMIT 5;

-- 단계별 로그 확인
SELECT stage_name, stage_progress, total_progress, message, created_at
FROM job_stage_logs
WHERE job_id = '<job_id>'
ORDER BY created_at ASC;

-- Heartbeat 확인 (worker가 살아있는지)
SELECT worker_id, current_stage, progress_percent, heartbeat_at
FROM job_worker_heartbeats
WHERE job_id = '<job_id>'
ORDER BY heartbeat_at DESC
LIMIT 10;

-- STT/artifact 결과 확인
SELECT artifact_type, stored_path, metadata, created_at
FROM analysis_artifacts
WHERE job_id = '<job_id>';

-- PII 탐지 결과 확인
SELECT detection_type, label, start_time_sec, end_time_sec, detected_text
FROM detections
WHERE job_id = '<job_id>';
```

### 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|---|---|---|
| `401 Unauthorized` | WORKER_SECRET 불일치 | 백엔드 `.env` 와 Colab Config 셀의 `WORKER_SECRET` 비교 |
| `Connection refused` | Cloudflare Tunnel URL 만료 또는 백엔드 미실행 | Cloudflare Tunnel URL 재발급 후 Colab Config 셀 재실행 |
| `파일이 아직 준비되지 않았습니다` | 업로드 status 가 `uploaded` 아님 | `uploads` 테이블 status 컬럼 확인 |
| `대기 중인 작업 없음` | job이 큐에 없음 | `analysis_jobs` 테이블 status=`queued` 확인 |
| STT 매우 느림 | Colab CPU 런타임 | GPU 런타임으로 변경, 또는 `WHISPER_MODEL_SIZE=base` 로 축소 |
