"""Adaptive visual PII OCR pipeline for Garim.

This module is designed for Google Colab but keeps its pure helpers importable
without OpenCV, PySceneDetect, or PaddleOCR. Raw PII is not written to results.
"""

from __future__ import annotations

import csv
import json
import os
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass
class VisualPIIConfig:
    base_fps: float = 0.5
    boundary_fps: float = 2.0
    burst_fps: float = 4.0
    boundary_radius_sec: float = 0.5
    burst_radius_sec: float = 0.75
    motion_probe_fps: float = 1.0
    motion_threshold: float = 12.0
    scene_threshold: float = 18.0
    dedupe_hamming_threshold: int = 4
    min_confidence: float = 0.55
    text_heavy_region_count: int = 6
    recognition_batch_size: int = 16
    merge_gap_sec: float = 0.7
    interval_padding_sec: float = 0.4
    bbox_iou_threshold: float = 0.25
    thumbnail_limit: int = 20


@dataclass(frozen=True)
class VideoMeta:
    fps: float
    frame_count: int
    width: int
    height: int
    duration_sec: float


@dataclass(frozen=True)
class Scene:
    scene_id: int
    start_sec: float
    end_sec: float


@dataclass(frozen=True)
class SampledFrame:
    frame_no: int
    timestamp_sec: float
    image: Any = field(repr=False, compare=False)


@dataclass(frozen=True)
class OCRHit:
    frame_no: int
    timestamp_sec: float
    bbox: tuple[int, int, int, int]
    text: str
    confidence: float


@dataclass(frozen=True)
class ClassifiedHit:
    frame_no: int
    timestamp_sec: float
    bbox: tuple[int, int, int, int]
    pii_type: str
    text_masked: str
    confidence: float


PHONE_RE = re.compile(r"(?<!\d)(01[016789])[\s.-]?(\d{3,4})[\s.-]?(\d{4})(?!\d)")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PLATE_RE = re.compile(r"(?<!\d)(\d{2,3})\s*([가-힣])\s*(\d{4})(?!\d)")
ADDRESS_RE = re.compile(
    r"((?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
    r"(?:특별자치도|특별자치시|특별시|광역시|도|시)?\s+"
    r"[가-힣0-9 -]{1,40}(?:로|길|대로|번길)\s*\d{1,5}(?:-\d{1,5})?)"
)


def get_video_meta(video_path: str | Path) -> VideoMeta:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if fps <= 0:
        raise RuntimeError("Video FPS is missing or invalid.")
    return VideoMeta(fps, frame_count, width, height, frame_count / fps)


def detect_scenes(video_path: str | Path, meta: VideoMeta, threshold: float = 18.0) -> list[Scene]:
    from scenedetect import SceneManager, open_video
    from scenedetect.detectors import ContentDetector

    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold))
    manager.detect_scenes(open_video(str(video_path)))
    raw_scenes = manager.get_scene_list()
    if not raw_scenes:
        return [Scene(0, 0.0, meta.duration_sec)]
    return [
        Scene(index, float(start.get_seconds()), float(end.get_seconds()))
        for index, (start, end) in enumerate(raw_scenes)
    ]


def _timestamp_range(start: float, end: float, fps: float, duration: float) -> set[float]:
    if fps <= 0 or end < start:
        return set()
    start = max(0.0, start)
    end = min(duration, end)
    count = max(0, int(math.floor((end - start) * fps)))
    return {round(start + index / fps, 6) for index in range(count + 1)}


def build_candidate_timestamps(
    meta: VideoMeta,
    scenes: Sequence[Scene],
    config: VisualPIIConfig,
    motion_timestamps: Iterable[float] = (),
    burst_centers: Iterable[float] = (),
) -> list[float]:
    timestamps = _timestamp_range(0.0, meta.duration_sec, config.base_fps, meta.duration_sec)
    for scene in scenes:
        for boundary in (scene.start_sec, scene.end_sec):
            timestamps |= _timestamp_range(
                boundary - config.boundary_radius_sec,
                boundary + config.boundary_radius_sec,
                config.boundary_fps,
                meta.duration_sec,
            )
    for center in list(motion_timestamps) + list(burst_centers):
        timestamps |= _timestamp_range(
            center - config.burst_radius_sec,
            center + config.burst_radius_sec,
            config.burst_fps,
            meta.duration_sec,
        )
    return sorted(ts for ts in timestamps if 0.0 <= ts <= meta.duration_sec)


def find_motion_timestamps(
    video_path: str | Path, meta: VideoMeta, config: VisualPIIConfig
) -> list[float]:
    """Probe low resolution frames and return timestamps with notable changes."""
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    previous = None
    motion = []
    for timestamp in _timestamp_range(0.0, meta.duration_sec, config.motion_probe_fps, meta.duration_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
        if previous is not None:
            score = float(cv2.absdiff(previous, gray).mean())
            if score >= config.motion_threshold:
                motion.append(timestamp)
        previous = gray
    cap.release()
    return motion


def _dhash(image: Any) -> int:
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = resized[:, 1:] > resized[:, :-1]
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return value


def _hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def read_unique_frames(
    video_path: str | Path,
    meta: VideoMeta,
    timestamps: Iterable[float],
    config: VisualPIIConfig,
) -> list[SampledFrame]:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    sampled: list[SampledFrame] = []
    recent_hashes: list[int] = []
    for timestamp in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        frame_hash = _dhash(frame)
        if any(
            _hamming_distance(frame_hash, previous) <= config.dedupe_hamming_threshold
            for previous in recent_hashes[-8:]
        ):
            continue
        frame_no = int(round(timestamp * meta.fps))
        sampled.append(SampledFrame(frame_no, round(timestamp, 3), frame))
        recent_hashes.append(frame_hash)
    cap.release()
    return sampled


def _to_bbox(points: Any) -> tuple[int, int, int, int]:
    if len(points) == 4 and all(isinstance(value, (int, float)) for value in points):
        x1, y1, x2, y2 = points
    else:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
    return tuple(int(round(value)) for value in (x1, y1, x2, y2))


class PaddleOCRBackend:
    """Small compatibility adapter for PaddleOCR 2.x and 3.x."""

    def __init__(self, use_gpu: bool = True, lang: str = "korean", recognition_batch_size: int = 16):
        # PaddleOCR 3.x can select a broken OneDNN PIR execution path on Colab.
        # Disable OneDNN and prefer CUDA when a GPU runtime is available.
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        import paddle
        from paddleocr import PaddleOCR

        use_cuda = use_gpu and paddle.device.is_compiled_with_cuda()
        device = "gpu" if use_cuda else "cpu"
        print(f"[OCR] PaddleOCR 초기화 (device={device}, detector=mobile)")

        try:
            self.engine = PaddleOCR(
                lang=lang,
                device=device,
                enable_mkldnn=False,
                text_detection_model_name="PP-OCRv5_mobile_det",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                text_recognition_batch_size=recognition_batch_size,
            )
        except TypeError:
            self.engine = PaddleOCR(
                lang=lang,
                use_angle_cls=True,
                use_gpu=use_gpu,
                rec_batch_num=recognition_batch_size,
                show_log=False,
            )

    def recognize(self, frames: Sequence[SampledFrame]) -> list[OCRHit]:
        hits: list[OCRHit] = []
        for frame in frames:
            hits.extend(self._recognize_frame(frame))
        return hits

    def _recognize_frame(self, frame: SampledFrame) -> list[OCRHit]:
        if hasattr(self.engine, "predict"):
            result = list(self.engine.predict(frame.image))
            return self._parse_v3(frame, result)
        return self._parse_v2(frame, self.engine.ocr(frame.image, cls=True))

    @staticmethod
    def _parse_v3(frame: SampledFrame, results: Sequence[Any]) -> list[OCRHit]:
        hits = []
        for result in results:
            payload = getattr(result, "json", result)
            if callable(payload):
                payload = payload()
            if isinstance(payload, str):
                payload = json.loads(payload)
            payload = payload.get("res", payload) if isinstance(payload, dict) else {}
            for box, text, score in zip(
                payload.get("rec_boxes", []),
                payload.get("rec_texts", []),
                payload.get("rec_scores", []),
            ):
                hits.append(OCRHit(frame.frame_no, frame.timestamp_sec, _to_bbox(box), str(text), float(score)))
        return hits

    @staticmethod
    def _parse_v2(frame: SampledFrame, results: Sequence[Any]) -> list[OCRHit]:
        hits = []
        for page in results or []:
            for line in page or []:
                box, recognition = line
                text, score = recognition
                hits.append(OCRHit(frame.frame_no, frame.timestamp_sec, _to_bbox(box), str(text), float(score)))
        return hits


def mask_phone(match: re.Match[str]) -> str:
    return f"{match.group(1)}-****-{match.group(3)}"


def mask_email(match: re.Match[str]) -> str:
    local, domain = match.groups()
    return f"{local[:1]}***@{domain}"


def mask_plate(match: re.Match[str]) -> str:
    return f"{match.group(1)}{match.group(2)}****"


def mask_address(match: re.Match[str]) -> str:
    text = match.group(1).strip()
    return f"{text[: min(6, len(text))]}***"


def classify_text(text: str) -> tuple[str, str] | None:
    compact = " ".join((text or "").split())
    for pii_type, pattern, masker in (
        ("phone", PHONE_RE, mask_phone),
        ("email", EMAIL_RE, mask_email),
        ("vehicle_plate", PLATE_RE, mask_plate),
        ("address", ADDRESS_RE, mask_address),
    ):
        match = pattern.search(compact)
        if match:
            return pii_type, masker(match)
    return None


def classify_hits(hits: Iterable[OCRHit], min_confidence: float = 0.55) -> list[ClassifiedHit]:
    classified = []
    for hit in hits:
        if hit.confidence < min_confidence:
            continue
        result = classify_text(hit.text)
        if result:
            pii_type, masked = result
            classified.append(
                ClassifiedHit(hit.frame_no, hit.timestamp_sec, hit.bbox, pii_type, masked, hit.confidence)
            )
    return classified


def bbox_iou(left: Sequence[int], right: Sequence[int]) -> float:
    x1 = max(left[0], right[0])
    y1 = max(left[1], right[1])
    x2 = min(left[2], right[2])
    y2 = min(left[3], right[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    left_area = max(0, left[2] - left[0]) * max(0, left[3] - left[1])
    right_area = max(0, right[2] - right[0]) * max(0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def _union_bbox(left: Sequence[int], right: Sequence[int]) -> list[int]:
    return [min(left[0], right[0]), min(left[1], right[1]), max(left[2], right[2]), max(left[3], right[3])]


def _display_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    minutes, remainder = divmod(milliseconds, 60_000)
    sec, millis = divmod(remainder, 1000)
    return f"{minutes:02d}:{sec:02d}.{millis:03d}"


def merge_hits(
    hits: Iterable[ClassifiedHit],
    config: VisualPIIConfig,
    duration_sec: float | None = None,
) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for hit in sorted(hits, key=lambda item: item.timestamp_sec):
        matched = None
        for track in reversed(tracks):
            if hit.timestamp_sec - track["_last_seen"] > config.merge_gap_sec:
                break
            if hit.pii_type != track["type"] or hit.text_masked != track["text_masked"]:
                continue
            if bbox_iou(hit.bbox, track["bbox"]) < config.bbox_iou_threshold:
                continue
            matched = track
            break
        if matched is None:
            tracks.append(
                {
                    "type": hit.pii_type,
                    "text_masked": hit.text_masked,
                    "start_sec": hit.timestamp_sec,
                    "end_sec": hit.timestamp_sec,
                    "bbox": list(hit.bbox),
                    "confidence": hit.confidence,
                    "source_frames": [hit.frame_no],
                    "replacement": "blur",
                    "_last_seen": hit.timestamp_sec,
                }
            )
            continue
        matched["end_sec"] = hit.timestamp_sec
        matched["bbox"] = _union_bbox(matched["bbox"], hit.bbox)
        matched["confidence"] = max(matched["confidence"], hit.confidence)
        matched["source_frames"].append(hit.frame_no)
        matched["_last_seen"] = hit.timestamp_sec

    for track in tracks:
        track.pop("_last_seen")
        track["start_sec"] = round(max(0.0, track["start_sec"] - config.interval_padding_sec), 3)
        end = track["end_sec"] + config.interval_padding_sec
        track["end_sec"] = round(min(duration_sec, end) if duration_sec is not None else end, 3)
        track["confidence"] = round(float(track["confidence"]), 4)
        track["source_frames"] = sorted(set(track["source_frames"]))
        track["start_display"] = _display_time(track["start_sec"])
        track["end_display"] = _display_time(track["end_sec"])
    return tracks


def _text_heavy_centers(hits: Iterable[OCRHit], threshold: int) -> list[float]:
    counts: dict[float, int] = {}
    for hit in hits:
        counts[hit.timestamp_sec] = counts.get(hit.timestamp_sec, 0) + 1
    return [timestamp for timestamp, count in counts.items() if count >= threshold]


def save_results(output_dir: str | Path, upload_id: str, detections: Sequence[dict[str, Any]]) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "visual_pii_detections.json"
    csv_path = output / "visual_pii_detections.csv"
    payload = {"upload_id": upload_id, "detections": list(detections)}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "type", "text_masked", "start_sec", "end_sec", "start_display",
                "end_display", "bbox", "confidence", "source_frames", "replacement",
            ],
        )
        writer.writeheader()
        for detection in detections:
            row = dict(detection)
            row["bbox"] = json.dumps(row["bbox"])
            row["source_frames"] = json.dumps(row["source_frames"])
            writer.writerow(row)
    return {"json": str(json_path), "csv": str(csv_path)}


def save_blurred_thumbnails(
    video_path: str | Path,
    output_dir: str | Path,
    meta: VideoMeta,
    detections: Sequence[dict[str, Any]],
    limit: int = 20,
) -> list[str]:
    """Save privacy-safe review thumbnails with detected regions blurred."""
    import cv2

    output = Path(output_dir) / "review_thumbnails"
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    paths = []
    for index, detection in enumerate(detections[:limit]):
        timestamp = float(detection["start_sec"])
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        x1, y1, x2, y2 = detection["bbox"]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(meta.width, x2), min(meta.height, y2)
        region = frame[y1:y2, x1:x2]
        if region.size:
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(region, (51, 51), 0)
        path = output / f"detection_{index:03d}.jpg"
        cv2.imwrite(str(path), frame)
        paths.append(str(path))
    cap.release()
    return paths


def run_visual_pii_pipeline(
    video_path: str | Path,
    upload_id: str,
    output_dir: str | Path,
    config: VisualPIIConfig | None = None,
    backend: Any | None = None,
) -> dict[str, Any]:
    """Run scene-aware OCR and emit masked time-coded detections."""
    config = config or VisualPIIConfig()
    meta = get_video_meta(video_path)
    scenes = detect_scenes(video_path, meta, config.scene_threshold)
    print(f"[OCR] 장면 탐지 완료: {len(scenes)}개")
    motion = find_motion_timestamps(video_path, meta, config)
    print(f"[OCR] 모션 후보 탐지 완료: {len(motion)}개")
    initial_timestamps = build_candidate_timestamps(meta, scenes, config, motion)
    frames = read_unique_frames(video_path, meta, initial_timestamps, config)
    print(f"[OCR] OCR 전달 프레임: {len(frames)}개")
    backend = backend or PaddleOCRBackend(recognition_batch_size=config.recognition_batch_size)
    ocr_hits = backend.recognize(frames)
    print(f"[OCR] 1차 OCR 완료: {len(ocr_hits)}건")

    burst_centers = _text_heavy_centers(ocr_hits, config.text_heavy_region_count)
    if burst_centers:
        burst_timestamps = build_candidate_timestamps(meta, (), config, burst_centers=burst_centers)
        existing = {frame.frame_no for frame in frames}
        burst_frames = [
            frame for frame in read_unique_frames(video_path, meta, burst_timestamps, config)
            if frame.frame_no not in existing
        ]
        ocr_hits.extend(backend.recognize(burst_frames))
        frames.extend(burst_frames)

    classified = classify_hits(ocr_hits, config.min_confidence)
    detections = merge_hits(classified, config, meta.duration_sec)
    paths = save_results(output_dir, upload_id, detections)
    thumbnails = save_blurred_thumbnails(video_path, output_dir, meta, detections, config.thumbnail_limit)
    return {
        "upload_id": upload_id,
        "video_meta": asdict(meta),
        "scene_count": len(scenes),
        "motion_probe_count": len(motion),
        "sampled_frame_count": len(frames),
        "ocr_hit_count": len(ocr_hits),
        "detections": detections,
        "result_paths": paths,
        "review_thumbnails": thumbnails,
    }


__all__ = [
    "ClassifiedHit",
    "OCRHit",
    "PaddleOCRBackend",
    "Scene",
    "VideoMeta",
    "VisualPIIConfig",
    "bbox_iou",
    "build_candidate_timestamps",
    "classify_hits",
    "classify_text",
    "merge_hits",
    "run_visual_pii_pipeline",
    "save_results",
]
