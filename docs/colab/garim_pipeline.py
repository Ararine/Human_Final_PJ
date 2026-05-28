# %% [markdown]
# # Garim Analysis Pipeline
#
# analyzer 단위 확장 구조로 분석 파이프라인을 구현한다.
#
# **새 analyzer 추가 방법**
# 1. `Analyzer` 를 상속해 클래스 작성
# 2. `stage_name`, `total_start`, `total_end` 설정
# 3. `run(input_path, ctx)` 구현 — 결과 dict 반환
# 4. `PIPELINE_REGISTRY` 리스트에 인스턴스 추가
#
# worker loop, progress API, 프론트 진행 화면을 수정할 필요 없음.
#
# **참고 문서**: `docs/upload&progress/GARIM_front_back_colab_upload_progress_db_v7_IMPLEMENTATION_MASTER.md`
# **참고 노트북**: `docs/colab/korean_pii_beep_pipeline_colab_v2.ipynb`

# %% [markdown]
# ## 1. 설치

# %%
import subprocess, sys
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "faster-whisper", "transformers", "accelerate", "pydub"],
    check=True,
)
subprocess.run(["apt-get", "install", "-y", "-q", "ffmpeg"], check=True)

# %% [markdown]
# ## 2. Config
#
# | 변수 | 설명 |
# |---|---|
# | `WHISPER_MODEL_SIZE` | Whisper 모델 크기 (base/small/medium/large) |
# | `NER_MODEL_NAME` | 한국어 개인정보 NER 모델 |
# | `AUDIO_DIR` | 추출된 오디오 임시 저장 경로 |
# | `BEEP_FREQ` | beep 주파수 (Hz) |
# | `BEEP_GAIN_DB` | beep 볼륨 게인 (dB) |
# | `PAD_SEC` | 탐지 구간 앞뒤 여유 시간 (초) |

# %%
import os
import re
import subprocess
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable

# ===== 여기만 수정 =====
WHISPER_MODEL_SIZE = "large"   # base / small / medium / large
NER_MODEL_NAME     = "YakuzaNeko/kr-dlp-ner-roberta-large"
AUDIO_DIR          = "/content/garim_audio"
BEEP_FREQ          = 1000       # Hz
BEEP_GAIN_DB       = -8        # dB
PAD_SEC            = 0.08      # 구간 앞뒤 여유
# ======================

os.makedirs(AUDIO_DIR, exist_ok=True)
print(f"Pipeline Config 로드 | 모델: {WHISPER_MODEL_SIZE} | NER: {NER_MODEL_NAME}")

# %% [markdown]
# ## 3. PipelineContext / Analyzer 인터페이스
#
# `PipelineContext` 는 분석 전체에서 공유되는 상태 객체다.
# 각 analyzer는 `ctx.results[stage_name]` 으로 이전 단계 결과를 읽는다.

# %%
@dataclass
class PipelineContext:
    job_id: str
    upload_id: str
    file_path: str
    results: dict = field(default_factory=dict)
    progress_fn: Callable | None = None   # report_progress(job_id, stage, s_pct, t_pct, msg)
    cancel_fn:   Callable | None = None   # check_cancel(job_id) -> bool

    def report(
        self,
        stage: str,
        stage_pct: int,
        total_pct: int,
        msg: str | None = None,
    ) -> None:
        if self.progress_fn:
            self.progress_fn(self.job_id, stage, stage_pct, total_pct, msg)

    def is_cancelled(self) -> bool:
        return bool(self.cancel_fn and self.cancel_fn(self.job_id))


class Analyzer:
    """모든 analyzer의 기반 클래스.

    Attributes:
        stage_name  : job_stage_logs 에 기록될 stage 이름
        total_start : 이 analyzer 시작 시점의 total_progress
        total_end   : 이 analyzer 완료 시점의 total_progress
    """

    stage_name:  str = "unknown"
    total_start: int = 0
    total_end:   int = 100

    def run(self, input_path: str, ctx: PipelineContext) -> dict:
        """분석을 실행하고 결과 dict 를 반환한다."""
        raise NotImplementedError(f"{self.__class__.__name__}.run() 미구현")


print("PipelineContext / Analyzer 인터페이스 로드 완료")

# %% [markdown]
# ## 4. PII 탐지 헬퍼
#
# 정규식 패턴, 텍스트 정규화, word timestamp 정밀 매칭 함수.
# `korean_pii_beep_pipeline_colab_v2.ipynb` 셀 6–10 기반.

# %%
# ── 정규식 패턴 ────────────────────────────────────────────────────

PHONE_REGEX = re.compile(
    r"""
    (?:
        01[016789]
        \s*[-.]?\s*
        \d{3,4}
        \s*[-.]?\s*
        \d{4}
    )
    """,
    re.VERBOSE,
)

ADDRESS_REGEX = re.compile(
    r"""
    (
        (?:
            서울특별시|서울시|부산광역시|부산시|대구광역시|대구시|인천광역시|인천시|
            광주광역시|광주시|대전광역시|대전시|울산광역시|울산시|세종특별자치시|세종시|
            경기도|강원특별자치도|강원도|충청북도|충북|충청남도|충남|전라북도|전북|
            전라남도|전남|경상북도|경북|경상남도|경남|제주특별자치도|제주도
        )
        \s*
        [가-힣]{1,20}(?:시|군|구)
        (?:\s*[가-힣]{1,20}(?:구|읍|면|동|리))?
        \s*
        [가-힣0-9]{1,30}(?:로|길|대로|번길)
        \s*
        \d{1,5}
        (?:-\d{1,5})?
    )
    """,
    re.VERBOSE,
)

NAME_PATTERNS = [
    r"([가-힣]{2,4})\s*(?:입니다|이에요|예요)",
    r"([가-힣]{2,4})\s?(?:고객님|님|기사님|선생님)",
]

# ── 텍스트 정규화 ──────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    return re.sub(r"[\s\-\.\,\:\;]", "", text or "")

def _only_digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")

# ── word timestamp 정밀 매칭 ───────────────────────────────────────
# words: [{"word": str, "start": float, "end": float}, ...]

def _find_entity_time(entity_text: str, words: list, pad_sec: float = PAD_SEC) -> dict | None:
    if not words:
        return None
    entity_norm = _normalize_text(entity_text)
    if not entity_norm:
        return None
    max_window = min(12, len(words))
    best = None
    best_score = 0.0
    for size in range(1, max_window + 1):
        for i in range(len(words) - size + 1):
            chunk = words[i:i + size]
            chunk_text = "".join(w["word"] for w in chunk)
            chunk_norm = _normalize_text(chunk_text)
            if not chunk_norm:
                continue
            score = SequenceMatcher(None, entity_norm, chunk_norm).ratio()
            if entity_norm in chunk_norm or chunk_norm in entity_norm:
                score = max(score, 0.95)
            if score > best_score:
                best_score = score
                best = {
                    "start": max(0.0, float(chunk[0]["start"]) - pad_sec),
                    "end": float(chunk[-1]["end"]) + pad_sec,
                    "match_score": round(score, 4),
                }
    return best if best and best_score >= 0.72 else None


def _find_phone_time(phone_text: str, words: list, pad_sec: float = PAD_SEC) -> dict | None:
    if not words:
        return None
    target_digits = _only_digits(phone_text)
    if not target_digits or len(target_digits) < 9:
        return None
    max_window = min(16, len(words))
    best = None
    best_score = 0.0
    for size in range(1, max_window + 1):
        for i in range(len(words) - size + 1):
            chunk = words[i:i + size]
            chunk_digits = _only_digits("".join(w["word"] for w in chunk))
            if not chunk_digits:
                continue
            if target_digits == chunk_digits:
                return {
                    "start": max(0.0, float(chunk[0]["start"]) - pad_sec),
                    "end": float(chunk[-1]["end"]) + pad_sec,
                    "match_score": 1.0,
                }
            score = SequenceMatcher(None, target_digits, chunk_digits).ratio()
            if target_digits in chunk_digits or chunk_digits in target_digits:
                score = max(score, min(len(target_digits), len(chunk_digits)) / len(target_digits))
            if score > best_score:
                best_score = score
                best = {
                    "start": max(0.0, float(chunk[0]["start"]) - pad_sec),
                    "end": float(chunk[-1]["end"]) + pad_sec,
                    "match_score": round(score, 4),
                }
    return best if best and best_score >= 0.85 else None


print("PII 탐지 헬퍼 로드 완료")

# %% [markdown]
# ## 5. Analyzers
#
# | Analyzer | stage | total_progress |
# |---|---|---|
# | AudioExtractAnalyzer | audio_extract | 10 → 20 |
# | STTAnalyzer | stt | 20 → 55 |
# | PIIDetectAnalyzer | pii_detect | 55 → 75 |
# | BeepRenderAnalyzer | beep_render | 75 → 90 |

# %%
class AudioExtractAnalyzer(Analyzer):
    """ffmpeg 로 영상에서 16kHz 모노 WAV 추출 (STT 입력용)"""

    stage_name  = "audio_extract"
    total_start = 10
    total_end   = 20

    def run(self, input_path: str, ctx: PipelineContext) -> dict:
        ctx.report(self.stage_name, 0, self.total_start, "오디오 추출 시작")

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1", input_path],
            capture_output=True, text=True,
        )
        if "audio" not in probe.stdout:
            ctx.report(self.stage_name, 100, self.total_end, "오디오 스트림 없음")
            return {"audio_path": None, "has_audio": False}

        audio_path = os.path.join(AUDIO_DIR, f"{ctx.upload_id}.wav")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
             audio_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg 오디오 추출 실패: {r.stderr[-300:]}")

        size_mb = os.path.getsize(audio_path) / 1024 / 1024
        ctx.report(self.stage_name, 100, self.total_end,
                   f"오디오 추출 완료 ({size_mb:.1f} MB)")
        return {"audio_path": audio_path, "has_audio": True}


# %%
class STTAnalyzer(Analyzer):
    """faster-whisper 음성 인식 — word timestamps 포함 (PII 탐지에 필요)"""

    stage_name  = "stt"
    total_start = 20
    total_end   = 55

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            import torch
            device       = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            print(f"[STT] WhisperModel '{WHISPER_MODEL_SIZE}' 로드 중 (device={device})")
            self._model = WhisperModel(
                WHISPER_MODEL_SIZE, device=device, compute_type=compute_type
            )
        return self._model

    def run(self, input_path: str, ctx: PipelineContext) -> dict:
        ctx.report(self.stage_name, 0, self.total_start, "STT 시작")

        audio_result = ctx.results.get("audio_extract", {})
        if not audio_result.get("has_audio"):
            ctx.report(self.stage_name, 100, self.total_end, "오디오 없음 — STT 건너뜀")
            return {"language": "none", "full_text": "", "segments": []}

        audio_path = audio_result["audio_path"]
        ctx.report(self.stage_name, 10, self.total_start + 4, "WhisperModel 로드 중")
        model = self._load_model()

        ctx.report(self.stage_name, 30, self.total_start + 10, "음성 인식 중")
        segments_iter, info = model.transcribe(
            audio_path,
            language="ko",
            word_timestamps=True,
            vad_filter=True,
        )
        raw_segments = list(segments_iter)

        segments = []
        for i, seg in enumerate(raw_segments):
            words = []
            if seg.words:
                words = [
                    {"word": w.word, "start": float(w.start), "end": float(w.end)}
                    for w in seg.words
                ]
            segments.append({
                "id": i,
                "start_ms": int(seg.start * 1000),
                "end_ms":   int(seg.end   * 1000),
                "text":     seg.text.strip(),
                "words":    words,
                "no_speech_prob": round(float(getattr(seg, "no_speech_prob", 0.0)), 4),
            })

        full_text = " ".join(s["text"] for s in segments)
        ctx.report(self.stage_name, 100, self.total_end,
                   f"STT 완료 — {len(segments)}개 세그먼트, 언어: {info.language}")
        return {
            "language": info.language,
            "full_text": full_text,
            "segments": segments,
        }


# %%
class PIIDetectAnalyzer(Analyzer):
    """Regex + NER + word timestamp 정밀 매칭으로 개인정보 구간 탐지

    입력: ctx.results["stt"]["segments"]  (words 필드 포함)
    출력: {"pii_count": int, "pii_segments": list[dict]}

    pii_segments 항목 형식:
        start_time_sec, end_time_sec, detected_text, label, confidence
    """

    stage_name  = "pii_detect"
    total_start = 55
    total_end   = 75

    _BEEP_TYPES = {"name", "phone", "address"}

    def __init__(self):
        self._ner = None

    def _load_ner(self):
        if self._ner is None:
            from transformers import pipeline as hf_pipeline
            import torch
            device = 0 if torch.cuda.is_available() else -1
            print(f"[PII] NER 모델 로드 중: {NER_MODEL_NAME}")
            self._ner = hf_pipeline(
                "token-classification",
                model=NER_MODEL_NAME,
                tokenizer=NER_MODEL_NAME,
                aggregation_strategy="simple",
                device=device,
            )
        return self._ner

    def _detect_regex(self, text: str) -> list:
        results = []
        for m in PHONE_REGEX.finditer(text):
            results.append({"type": "phone", "text": m.group().strip(),
                             "confidence": 0.98, "source": "regex"})
        for m in ADDRESS_REGEX.finditer(text):
            results.append({"type": "address", "text": m.group().strip(),
                             "confidence": 0.92, "source": "regex"})
        for pattern in NAME_PATTERNS:
            for m in re.finditer(pattern, text):
                name = m.group(1).strip() if m.groups() else m.group().strip()
                if len(name) >= 2:
                    results.append({"type": "name", "text": name,
                                    "confidence": 0.82, "source": "regex"})
        return results

    def _detect_ner(self, text: str) -> list:
        results = []
        try:
            ner = self._load_ner()
            for item in ner(text):
                label = item.get("entity_group", "").upper()
                if any(x in label for x in ["PER", "PERSON", "NAME"]):
                    ent_type = "name"
                elif any(x in label for x in ["LOC", "LOCATION", "ADDRESS", "ADDR"]):
                    ent_type = "address"
                elif any(x in label for x in ["PHONE", "TEL", "MOBILE"]):
                    ent_type = "phone"
                else:
                    continue
                word = item.get("word", "").strip()
                if not word:
                    continue
                if ent_type == "phone" and len(_only_digits(word)) < 9:
                    continue
                results.append({"type": ent_type, "text": word,
                                 "confidence": float(item.get("score", 0.0)),
                                 "source": "ner"})
        except Exception as e:
            print(f"[PII] NER 오류 (무시): {e}")
        return results

    def run(self, input_path: str, ctx: PipelineContext) -> dict:
        ctx.report(self.stage_name, 0, self.total_start, "개인정보 탐지 시작")

        stt_result = ctx.results.get("stt", {})
        segments   = stt_result.get("segments", [])
        if not segments:
            ctx.report(self.stage_name, 100, self.total_end, "STT 결과 없음 — 탐지 건너뜀")
            return {"pii_count": 0, "pii_segments": []}

        ctx.report(self.stage_name, 5, self.total_start + 1, "NER 모델 로드 중")
        self._load_ner()   # 미리 로드

        pii_segments = []
        n = len(segments)
        for idx, seg in enumerate(segments):
            text  = seg.get("text", "").strip()
            words = seg.get("words", [])
            if not text:
                continue

            for ent in self._detect_regex(text) + self._detect_ner(text):
                if ent["type"] not in self._BEEP_TYPES or not ent["text"]:
                    continue
                if ent["type"] == "phone":
                    t = _find_phone_time(ent["text"], words)
                else:
                    t = _find_entity_time(ent["text"], words)
                if t is None:
                    continue
                pii_segments.append({
                    "start_time_sec": round(t["start"], 3),
                    "end_time_sec":   round(t["end"],   3),
                    "detected_text":  ent["text"],
                    "label":          ent["type"],
                    "confidence":     round(float(ent.get("confidence", 0.0)), 4),
                })

            stage_pct = int(10 + 85 * (idx + 1) / n)
            total_pct = int(self.total_start + (self.total_end - self.total_start) * (idx + 1) / n)
            ctx.report(self.stage_name, stage_pct, total_pct)

        ctx.report(self.stage_name, 100, self.total_end,
                   f"개인정보 탐지 완료 — {len(pii_segments)}건")
        return {"pii_count": len(pii_segments), "pii_segments": pii_segments}


# %%
class BeepRenderAnalyzer(Analyzer):
    """pydub + ffmpeg 로 개인정보 구간에 beep 삽입 후 영상 합성

    입력: ctx.results["pii_detect"]["pii_segments"]
    출력: {"output_path": str | None, "beep_count": int}
    """

    stage_name  = "beep_render"
    total_start = 75
    total_end   = 90

    def run(self, input_path: str, ctx: PipelineContext) -> dict:
        ctx.report(self.stage_name, 0, self.total_start, "beep 처리 시작")

        pii_segments = ctx.results.get("pii_detect", {}).get("pii_segments", [])
        if not pii_segments:
            ctx.report(self.stage_name, 100, self.total_end,
                       "탐지된 개인정보 없음 — beep 건너뜀")
            return {"output_path": None, "beep_count": 0}

        from pydub import AudioSegment
        from pydub.generators import Sine

        # 1) 44100Hz 스테레오 오디오 추출 (beep 품질 유지용)
        ctx.report(self.stage_name, 10, self.total_start + 3, "원본 오디오 추출 중")
        audio_hq_path = os.path.join(AUDIO_DIR, f"{ctx.upload_id}_hq.wav")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
             audio_hq_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"오디오 추출 실패: {r.stderr[-300:]}")

        # 2) beep 삽입
        ctx.report(self.stage_name, 30, self.total_start + 5, "beep 삽입 중")
        audio      = AudioSegment.from_wav(audio_hq_path)
        beep_count = 0
        for seg in pii_segments:
            start_ms    = int(seg["start_time_sec"] * 1000)
            end_ms      = int(seg["end_time_sec"]   * 1000)
            duration_ms = max(0, end_ms - start_ms)
            if duration_ms <= 0:
                continue
            beep = (
                Sine(BEEP_FREQ)
                .to_audio_segment(duration=duration_ms)
                .apply_gain(BEEP_GAIN_DB)
            )
            beep = beep.set_frame_rate(audio.frame_rate)
            beep = beep.set_channels(audio.channels)
            beep = beep.set_sample_width(audio.sample_width)
            audio = audio[:start_ms] + beep + audio[end_ms:]
            beep_count += 1

        beeped_audio_path = os.path.join(AUDIO_DIR, f"{ctx.upload_id}_beeped.wav")
        audio.export(beeped_audio_path, format="wav")
        ctx.report(self.stage_name, 70, self.total_start + 10,
                   f"beep {beep_count}건 완료, 영상 합성 중")

        # 3) 원본 영상 + beeped 오디오 합성
        output_path = os.path.join(AUDIO_DIR, f"{ctx.upload_id}_output.mp4")
        r = subprocess.run(
            ["ffmpeg", "-y",
             "-i", input_path,
             "-i", beeped_audio_path,
             "-map", "0:v:0", "-map", "1:a:0",
             "-c:v", "copy", "-c:a", "aac", "-shortest",
             output_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"영상 합성 실패: {r.stderr[-300:]}")

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        ctx.report(self.stage_name, 100, self.total_end,
                   f"beep 처리 완료 — {beep_count}건, {size_mb:.1f} MB")
        return {"output_path": output_path, "beep_count": beep_count}


print("Analyzer 클래스 로드 완료 (AudioExtract / STT / PIIDetect / BeepRender)")

# %% [markdown]
# ## 6. Pipeline Registry
#
# `PIPELINE_REGISTRY` 에 analyzer를 추가하면 `run_pipeline()` 이 순서대로 실행한다.
# worker loop, progress API, 프론트 진행 화면을 건드리지 않아도 된다.
#
# **새 analyzer 추가 예시**:
# ```python
# class SceneDetectAnalyzer(Analyzer):
#     stage_name  = "scene_detect"
#     total_start = 90   # beep_render 뒤에 배치
#     total_end   = 95
#     def run(self, input_path, ctx): ...
#
# PIPELINE_REGISTRY.append(SceneDetectAnalyzer())
# ```

# %%
PIPELINE_REGISTRY: list[Analyzer] = [
    AudioExtractAnalyzer(),
    STTAnalyzer(),
    PIIDetectAnalyzer(),
    BeepRenderAnalyzer(),
]


def run_pipeline(ctx: PipelineContext) -> dict:
    """PIPELINE_REGISTRY 순서대로 analyzer 를 실행한다.

    Returns:
        {"detection_count": int, "results": dict}

    Raises:
        RuntimeError("CANCELLED") — 취소 감지 시
        RuntimeError            — analyzer 실패 시
    """
    for analyzer in PIPELINE_REGISTRY:
        if ctx.is_cancelled():
            raise RuntimeError("CANCELLED")
        result = analyzer.run(ctx.file_path, ctx)
        ctx.results[analyzer.stage_name] = result

    detection_count = ctx.results.get("pii_detect", {}).get("pii_count", 0)
    return {"detection_count": detection_count, "results": ctx.results}


print(f"Pipeline Registry 로드 완료")
print(f"등록된 analyzer: {[a.stage_name for a in PIPELINE_REGISTRY]}")
