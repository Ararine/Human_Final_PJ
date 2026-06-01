# %% [markdown]
# # Garim Colab Worker
#
# Cloudflare Tunnel로 공개된 백엔드 URL의 `/worker/*` API를 polling해 job을 처리하는 worker 클라이언트.
#
# **실행 순서**
# 1. `[설치]` 셀 실행
# 2. `[Config]` 셀에서 BACKEND_URL / WORKER_SECRET 설정
# 3. `[API 헬퍼]` 셀 실행
# 4. `[Heartbeat 스레드]` 셀 실행
# 5. Drive의 `garim_colab` 폴더에 `garim_pipeline.py`, `garim_visual_pii_ocr_pipeline.py` 업로드
# 6. `[파이프라인 연동]` 셀 실행
# 7. `[Worker Loop]` 셀 실행
# 8. `[실행]` 셀에서 `run_once()` 또는 `run_loop()` 실행
#
# **참고 문서**: `docs/upload&progress/GARIM_front_back_colab_upload_progress_db_v7_IMPLEMENTATION_MASTER.md`

# %% [markdown]
# ## 1. 설치

# %%
import subprocess
subprocess.run(["pip", "install", "-q", "requests"], check=True)

# %% [markdown]
# ## 2. Config
#
# | 변수 | 설명 |
# |---|---|
# | `BACKEND_URL` | Cloudflare Tunnel로 공개된 백엔드 URL (새 URL을 입력) |
# | `WORKER_SECRET` | 백엔드 `.env`의 `WORKER_SECRET`과 동일한 값 |
# | `WORKER_ID` | 이 Colab 인스턴스를 식별하는 임의 이름 |

# %%
import os, time, threading, logging
import requests

# ===== 여기만 수정 =====
BACKEND_URL                = "https://xxxx.trycloudflare.com"  # Cloudflare Tunnel URL (슬래시 없이)
WORKER_SECRET              = "change-me-worker-secret"
WORKER_ID                  = "colab-worker-01"
POLL_INTERVAL_SECONDS      = 10   # job이 없을 때 재polling 간격 (초)
HEARTBEAT_INTERVAL_SECONDS = 30   # heartbeat 전송 주기 (초)
DOWNLOAD_DIR               = "/content/garim_downloads"
# ======================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("garim-worker")
log.info(f"Config 로드 완료 | BACKEND_URL={BACKEND_URL} | WORKER_ID={WORKER_ID}")

# %% [markdown]
# ## 3. API 헬퍼
#
# 백엔드 `/worker/*` 엔드포인트 호출 함수 모음.
# 인증은 모든 요청에 `Authorization: Bearer {WORKER_SECRET}` 헤더로 처리한다.

# %%
def auth_headers() -> dict:
    return {"Authorization": f"Bearer {WORKER_SECRET}"}


def get_next_job() -> dict | None:
    """GET /worker/jobs/next — 대기 중인 job 1개 반환, 없으면 None"""
    r = requests.get(
        f"{BACKEND_URL}/worker/jobs/next",
        headers=auth_headers(),
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("job")


def accept_job(job_id: str) -> dict:
    """POST /worker/jobs/{job_id}/accept — job 처리 시작 선언"""
    r = requests.post(
        f"{BACKEND_URL}/worker/jobs/{job_id}/accept",
        headers=auth_headers(),
        json={"worker_id": WORKER_ID},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def download_file(upload_id: str, output_dir: str = DOWNLOAD_DIR) -> str:
    """GET /worker/files/{upload_id}/download — 원본 파일 바이너리 수신 후 저장

    Returns:
        저장된 로컬 파일 경로
    """
    url = f"{BACKEND_URL}/worker/files/{upload_id}/download"
    r = requests.get(url, headers=auth_headers(), stream=True, timeout=60)
    r.raise_for_status()

    cd = r.headers.get("content-disposition", "")
    filename = f"upload_{upload_id}"
    if "filename=" in cd:
        filename = cd.split("filename=")[-1].strip().strip('"').strip("'")

    out_path = os.path.join(output_dir, filename)
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    log.info(f"파일 다운로드 완료: {out_path} ({size_mb:.1f} MB)")
    return out_path


def report_progress(
    job_id: str,
    stage_name: str,
    stage_progress: int,
    total_progress: int,
    message: str | None = None,
) -> dict:
    """PUT /worker/jobs/{job_id}/progress — 진행률 업데이트"""
    r = requests.put(
        f"{BACKEND_URL}/worker/jobs/{job_id}/progress",
        headers=auth_headers(),
        json={
            "worker_id": WORKER_ID,
            "stage_name": stage_name,
            "stage_progress": stage_progress,
            "total_progress": total_progress,
            "message": message,
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def send_heartbeat(
    job_id: str,
    current_stage: str | None = None,
    progress_percent: int = 0,
    message: str | None = None,
) -> None:
    """POST /worker/heartbeat — 생존 신호 전송 (실패해도 worker 중단 안 함)"""
    try:
        r = requests.post(
            f"{BACKEND_URL}/worker/heartbeat",
            headers=auth_headers(),
            json={
                "job_id": job_id,
                "worker_id": WORKER_ID,
                "worker_type": "colab",
                "current_stage": current_stage,
                "progress_percent": progress_percent,
                "message": message,
            },
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        log.warning(f"heartbeat 실패 (무시): {e}")


def complete_job(job_id: str, detection_count: int = 0) -> dict:
    """POST /worker/jobs/{job_id}/complete — 정상 완료 보고"""
    r = requests.post(
        f"{BACKEND_URL}/worker/jobs/{job_id}/complete",
        headers=auth_headers(),
        json={"worker_id": WORKER_ID, "detection_count": detection_count},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def fail_job(
    job_id: str,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    """POST /worker/jobs/{job_id}/fail — 실패 보고 (전송 실패해도 로그만 남김)"""
    try:
        r = requests.post(
            f"{BACKEND_URL}/worker/jobs/{job_id}/fail",
            headers=auth_headers(),
            json={
                "worker_id": WORKER_ID,
                "error_code": error_code,
                "error_message": error_message,
            },
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        log.error(f"fail_job 전송 실패: {e}")


def check_cancel(job_id: str) -> bool:
    """GET /worker/jobs/{job_id}/status — 취소 여부 확인"""
    try:
        r = requests.get(
            f"{BACKEND_URL}/worker/jobs/{job_id}/status",
            headers=auth_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("cancel_requested", False)
    except Exception:
        return False  # 오류 시 취소 없음으로 간주

def submit_stt_result(
    job_id: str,
    language: str,
    full_text: str,
    segment_count: int,
) -> dict:
    """POST /worker/jobs/{job_id}/results/stt — STT 결과 저장"""
    r = requests.post(
        f"{BACKEND_URL}/worker/jobs/{job_id}/results/stt",
        headers=auth_headers(),
        json={
            "worker_id": WORKER_ID,
            "language": language,
            "full_text": full_text,
            "segment_count": segment_count,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def submit_pii_result(job_id: str, pii_segments: list) -> dict:
    """POST /worker/jobs/{job_id}/results/pii — PII 탐지 결과 저장"""
    r = requests.post(
        f"{BACKEND_URL}/worker/jobs/{job_id}/results/pii",
        headers=auth_headers(),
        json={"worker_id": WORKER_ID, "pii_segments": pii_segments},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def submit_artifact(
    job_id: str,
    artifact_type: str,
    stored_path: str,
    content_type: str | None = None,
    file_size: int | None = None,
    metadata: dict | None = None,
) -> dict:
    """POST /worker/jobs/{job_id}/results/artifact — 분석 산출물 저장"""
    r = requests.post(
        f"{BACKEND_URL}/worker/jobs/{job_id}/results/artifact",
        headers=auth_headers(),
        json={
            "worker_id": WORKER_ID,
            "artifact_type": artifact_type,
            "stored_path": stored_path,
            "content_type": content_type,
            "file_size": file_size,
            "metadata": metadata,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


log.info("API 헬퍼 함수 로드 완료")

# %% [markdown]
# ## 3-1. Upload / Job Progress Check
#
# Frontend upload itself is tracked in the browser. In Colab, the worker can
# confirm that upload has finished when a queued analysis job appears.
#
# - `peek_next_job()` checks whether an uploaded file has produced a queued job.
# - `watch_for_next_job()` waits until a queued job appears.
# - `watch_job_status(job_id)` prints backend analysis progress for a known job id.
#
# Run this section after uploading a file from the frontend.

# %%
def peek_next_job() -> dict | None:
    """Print and return the next queued analysis job, if one exists."""
    job = get_next_job()
    if not job:
        log.info("No queued analysis job yet. Upload may still be in progress or analysis job was not created.")
        return None

    log.info(
        "Queued job found | job_id=%s | upload_id=%s | file=%s | size=%s",
        job.get("job_id"),
        job.get("upload_id"),
        job.get("original_filename"),
        job.get("file_size"),
    )
    return job


def watch_for_next_job(timeout_seconds: int = 300, interval_seconds: int = 3) -> dict | None:
    """Wait until frontend upload creates a queued analysis job."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        job = peek_next_job()
        if job:
            return job
        time.sleep(interval_seconds)

    log.warning("Timed out waiting for a queued analysis job. Check frontend upload status and backend logs.")
    return None


def get_job_progress(job_id: str) -> dict:
    """Read worker-visible analysis job status."""
    r = requests.get(
        f"{BACKEND_URL}/worker/jobs/{job_id}/status",
        headers=auth_headers(),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def watch_job_status(job_id: str, interval_seconds: int = 2, stop_on_terminal: bool = True) -> None:
    """Print analysis job progress until it reaches a terminal state."""
    terminal = {"completed", "failed", "cancelled"}
    last_line = None
    while True:
        status = get_job_progress(job_id)
        line = (
            f"job={status.get('job_id')} | status={status.get('status')} | "
            f"stage={status.get('current_stage')} | total={status.get('total_progress')}% | "
            f"cancel={status.get('cancel_requested')}"
        )
        if line != last_line:
            print(line)
            last_line = line

        if stop_on_terminal and status.get("status") in terminal:
            break
        time.sleep(interval_seconds)


# Usage examples:
# job = watch_for_next_job()
# if job:
#     watch_job_status(job["job_id"])
log.info("Upload / Job progress helper loaded")

# %% [markdown]
# ## 4. Heartbeat 스레드
#
# job 처리 중 30초마다 백엔드에 생존 신호를 전송한다.
# `hb.update(stage, progress)` 로 현재 상태를 갱신하고,
# `hb.stop()` 으로 스레드를 종료한다.

# %%
class HeartbeatThread(threading.Thread):
    def __init__(self, job_id: str):
        super().__init__(daemon=True)
        self.job_id = job_id
        self._stop = threading.Event()
        self._stage: str | None = None
        self._progress: int = 0
        self._message: str | None = None

    def update(self, stage: str, progress: int, message: str | None = None) -> None:
        self._stage = stage
        self._progress = progress
        self._message = message

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.wait(HEARTBEAT_INTERVAL_SECONDS):
            send_heartbeat(self.job_id, self._stage, self._progress, self._message)

log.info("HeartbeatThread 로드 완료")

# %% [markdown]
# ## 5. 파이프라인 연동
#
# Drive에 분석 파이프라인 파일을 업로드한 뒤 이 셀을 실행한다.
# 파이프라인이 로드되지 않았으면 dry-run 모드로 동작한다.

# %%
from google.colab import drive
import importlib
import os
import sys

GARIM_COLAB_DIR = "/content/drive/MyDrive/garim_colab"
PIPELINE_FILENAME = "garim_pipeline.py"

# Drive를 고정 저장소로 사용한다. 런타임이 재시작되어도 Drive 파일은 유지된다.
drive.mount("/content/drive")
os.makedirs(GARIM_COLAB_DIR, exist_ok=True)

if GARIM_COLAB_DIR not in sys.path:
    sys.path.insert(0, GARIM_COLAB_DIR)

pipeline_path = os.path.join(GARIM_COLAB_DIR, PIPELINE_FILENAME)

if not os.path.exists(pipeline_path):
    _pipeline = None
    _PIPELINE_AVAILABLE = False
    log.warning(
        f"{PIPELINE_FILENAME} 없음: {pipeline_path} — "
        "Drive의 garim_colab 폴더에 garim_pipeline.py와 "
        "garim_visual_pii_ocr_pipeline.py를 넣으면 실제 파이프라인으로 실행됩니다. "
        "현재는 dry-run 모드로 실행합니다."
    )
else:
    try:
        import garim_pipeline as _pipeline
        _pipeline = importlib.reload(_pipeline)
        registry = getattr(_pipeline, "PIPELINE_REGISTRY", [])
        _PIPELINE_AVAILABLE = True
        log.info(f"파이프라인 로드 완료 | 경로: {pipeline_path} | analyzer: {[a.stage_name for a in registry]}")
    except Exception as e:
        _pipeline = None
        _PIPELINE_AVAILABLE = False
        log.warning(f"garim_pipeline import 실패 — dry-run 모드로 실행: {e}")

# %% [markdown]
# ## 6. Worker Loop
#
# ### run_once()
# job 1개를 꺼내 처리한다.
# `garim_pipeline` 이 로드되면 실제 파이프라인을 실행하고,
# 없으면 dry-run으로 stage 만 통과한다.
#
# ### run_loop()
# job이 있으면 계속 처리, 없으면 `POLL_INTERVAL_SECONDS` 대기 후 재시도.
# Colab 셀에서 실행하면 `KeyboardInterrupt`(■ 버튼)로 중단 가능.
#
# | phase | stage | total_progress |
# |---|---|---|
# | worker | file_download | 0 → 10 |
# | pipeline | visual_ocr | 10 → 40 |
# | pipeline | audio_extract | 40 → 48 |
# | pipeline | stt | 48 → 68 |
# | pipeline | pii_detect | 68 → 78 |
# | pipeline | beep_render | 78 → 90 |
# | worker | result_upload | 90 → 98 |
# | worker | completed | 100 |

# %%
# dry-run 에서 파이프라인 구간만 통과 (result_upload 는 Phase 3 에서 별도 처리)
_DRY_RUN_STAGES = [
    ("visual_ocr",    40),
    ("audio_extract", 48),
    ("stt",           68),
    ("pii_detect",    78),
    ("beep_render",   90),
]


def _handle_cancel(job_id: str) -> None:
    """취소 감지 시 progress 메시지를 남기고 중단한다."""
    log.info(f"취소 요청 확인 — 처리 중단: {job_id}")
    try:
        report_progress(job_id, "cancelled", 0, 0,
                        "취소 요청을 확인해 worker 처리를 중단했습니다.")
    except Exception:
        pass


def run_once() -> bool:
    """job 하나를 처리한다.

    Returns:
        True  — job을 처리했음 (성공/실패 불문)
        False — 대기 중인 job이 없었음
    """
    job = get_next_job()
    if job is None:
        log.info("대기 중인 작업 없음")
        return False

    job_id    = job["job_id"]
    upload_id = job["upload_id"]
    log.info(f"job 수신: {job_id} | upload: {upload_id} | type: {job.get('job_type')}")

    hb = HeartbeatThread(job_id)
    hb.start()

    try:
        accept_job(job_id)
        log.info(f"job 수락 완료: {job_id}")

        # Phase 1: 파일 다운로드 (0 → 10%)
        report_progress(job_id, "file_download", 0, 0, "파일 다운로드 시작")
        hb.update("file_download", 0)
        file_path = download_file(upload_id)
        report_progress(job_id, "file_download", 100, 10,
                        f"다운로드 완료: {os.path.basename(file_path)}")
        hb.update("file_download", 10)

        if check_cancel(job_id):
            _handle_cancel(job_id)
            return True

        # Phase 2: 분석 파이프라인 (10 → 90%)
        if _PIPELINE_AVAILABLE:
            ctx = _pipeline.PipelineContext(
                job_id=job_id,
                upload_id=upload_id,
                file_path=file_path,
                media_type=job.get("media_type"),
                progress_fn=report_progress,
                cancel_fn=check_cancel,
            )
            try:
                pipeline_result = _pipeline.run_pipeline(ctx)
            except RuntimeError as e:
                if "CANCELLED" in str(e):
                    _handle_cancel(job_id)
                    return True
                raise
            detection_count = pipeline_result.get("detection_count", 0)
            hb.update("beep_render", 90)
            log.info(f"파이프라인 완료 | detection_count={detection_count}")
        else:
            # dry-run 모드
            detection_count = 0
            for stage, total_end in _DRY_RUN_STAGES:
                if check_cancel(job_id):
                    _handle_cancel(job_id)
                    return True
                report_progress(job_id, stage, 100, total_end, f"{stage} 완료 (dry-run)")
                hb.update(stage, total_end)
                log.info(f"  [dry-run] stage={stage} total_progress={total_end}")

        # Phase 3: 결과 저장 (90 → 98%)
        report_progress(job_id, "result_upload", 0, 90, "결과 저장 시작")
        hb.update("result_upload", 90)

        if _PIPELINE_AVAILABLE:
            stt = ctx.results.get("stt", {})
            if stt.get("full_text"):
                try:
                    submit_stt_result(
                        job_id,
                        language=stt.get("language", "unknown"),
                        full_text=stt["full_text"],
                        segment_count=len(stt.get("segments", [])),
                    )
                    log.info(f"STT 결과 저장 완료: {len(stt.get('segments', []))}개 세그먼트")
                except Exception as e:
                    log.warning(f"STT 결과 저장 실패 (무시): {e}")

            pii = ctx.results.get("pii_detect", {})
            if pii.get("pii_segments"):
                try:
                    submit_pii_result(job_id, pii["pii_segments"])
                    log.info(f"PII 결과 저장 완료: {len(pii['pii_segments'])}건")
                except Exception as e:
                    log.warning(f"PII 결과 저장 실패 (무시): {e}")

            beep = ctx.results.get("beep_render", {})
            if beep.get("output_path"):
                try:
                    fsize = os.path.getsize(beep["output_path"]) if os.path.exists(beep["output_path"]) else None
                    submit_artifact(job_id, "beep_output", beep["output_path"], "video/mp4", fsize)
                    log.info(f"beep 결과물 저장 완료: {beep['output_path']}")
                except Exception as e:
                    log.warning(f"beep 결과물 저장 실패 (무시): {e}")

            visual_ocr = ctx.results.get("visual_ocr", {})
            visual_metadata = {
                "scene_count": visual_ocr.get("scene_count", 0),
                "sampled_frame_count": visual_ocr.get("sampled_frame_count", 0),
                "ocr_hit_count": visual_ocr.get("ocr_hit_count", 0),
                "detection_count": visual_ocr.get("detection_count", 0),
                "review_thumbnail_count": len(visual_ocr.get("review_thumbnails", [])),
            }
            for artifact_type, content_type, path_key in (
                ("visual_ocr_json", "application/json", "json"),
                ("visual_ocr_csv", "text/csv", "csv"),
            ):
                stored_path = visual_ocr.get("result_paths", {}).get(path_key)
                if not stored_path:
                    continue
                try:
                    fsize = os.path.getsize(stored_path) if os.path.exists(stored_path) else None
                    submit_artifact(
                        job_id,
                        artifact_type,
                        stored_path,
                        content_type,
                        fsize,
                        visual_metadata,
                    )
                    log.info(f"시각 OCR 결과물 저장 완료: {stored_path}")
                except Exception as e:
                    log.warning(f"시각 OCR 결과물 저장 실패 (무시): {e}")

        report_progress(job_id, "result_upload", 100, 98, "결과 저장 완료")
        hb.update("result_upload", 98)

        # Phase 4: 완료
        complete_job(job_id, detection_count=detection_count)
        log.info(f"job 완료: {job_id}")
        return True

    except Exception as e:
        log.error(f"job 처리 실패: {e}")
        fail_job(job_id, error_code="WORKER_ERROR", error_message=str(e))
        return False

    finally:
        hb.stop()


def run_loop() -> None:
    """job을 계속 polling하며 처리한다. Colab ■ 버튼으로 중단."""
    log.info(f"worker 루프 시작 | WORKER_ID={WORKER_ID} | POLL_INTERVAL={POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            has_job = run_once()
            if not has_job:
                time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log.info("worker 루프 종료 (KeyboardInterrupt)")
            break
        except Exception as e:
            log.error(f"루프 오류 (재시도 대기): {e}")
            time.sleep(POLL_INTERVAL_SECONDS)

log.info("Worker Loop 함수 로드 완료")

# %% [markdown]
# ## 7. 실행
#
# ### 단건 테스트
# ```python
# run_once()
# ```
#
# ### 루프 실행
# ```python
# run_loop()
# ```
#
# > Colab ■(중단) 버튼으로 루프를 종료할 수 있다.

# %%
# ===== 실행 방식 선택 =====
# 단건 테스트: job 1개만 처리하고 종료
# run_once()

# 루프 실행: 대기 job을 계속 처리 (■ 로 중단)
run_loop()
