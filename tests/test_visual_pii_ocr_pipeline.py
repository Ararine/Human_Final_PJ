from pathlib import Path
import sys


COLAB_DIR = Path(__file__).resolve().parents[1] / "docs" / "colab"
sys.path.insert(0, str(COLAB_DIR))

from garim_visual_pii_ocr_pipeline import (  # noqa: E402
    ClassifiedHit,
    Scene,
    VideoMeta,
    VisualPIIConfig,
    build_candidate_timestamps,
    classify_text,
    merge_hits,
)
import garim_visual_pii_ocr_pipeline as visual_pipeline  # noqa: E402


def test_candidate_timestamps_include_base_and_boundary_burst_samples():
    meta = VideoMeta(fps=30.0, frame_count=300, width=1920, height=1080, duration_sec=10.0)
    config = VisualPIIConfig(base_fps=2.0, boundary_fps=5.0, boundary_radius_sec=0.5)

    timestamps = build_candidate_timestamps(meta, [Scene(0, 0.0, 5.0), Scene(1, 5.0, 10.0)], config)

    assert 2.5 in timestamps
    assert 4.7 in timestamps
    assert 5.1 in timestamps
    assert len(timestamps) > 21


def test_classify_text_masks_raw_pii():
    assert classify_text("연락처 010-1234-5678") == ("phone", "010-****-5678")
    assert classify_text("메일 user@example.com") == ("email", "u***@example.com")
    assert classify_text("차량 12가3456") == ("vehicle_plate", "12가****")


def test_merge_hits_builds_blur_interval_without_raw_text():
    config = VisualPIIConfig(merge_gap_sec=0.7, interval_padding_sec=0.4, bbox_iou_threshold=0.25)
    hits = [
        ClassifiedHit(30, 1.0, (10, 20, 110, 60), "phone", "010-****-5678", 0.91),
        ClassifiedHit(45, 1.5, (12, 20, 112, 60), "phone", "010-****-5678", 0.96),
    ]
    detections = merge_hits(hits, config, duration_sec=3.0)

    assert detections == [
        {
            "type": "phone",
            "text_masked": "010-****-5678",
            "start_sec": 0.6,
            "end_sec": 1.9,
            "bbox": [10, 20, 112, 60],
            "confidence": 0.96,
            "source_frames": [30, 45],
            "replacement": "blur",
            "start_display": "00:00.600",
            "end_display": "00:01.900",
        }
    ]


def test_run_visual_pipeline_passes_sampled_frames_to_ocr(monkeypatch, tmp_path):
    meta = VideoMeta(fps=30.0, frame_count=300, width=1920, height=1080, duration_sec=10.0)
    frames = [visual_pipeline.SampledFrame(30, 1.0, object())]

    class Backend:
        def __init__(self):
            self.received = []

        def recognize(self, sampled_frames):
            self.received.extend(sampled_frames)
            return []

    backend = Backend()
    monkeypatch.setattr(visual_pipeline, "get_video_meta", lambda path: meta)
    monkeypatch.setattr(visual_pipeline, "detect_scenes", lambda path, video_meta, threshold: [Scene(0, 0.0, 10.0)])
    monkeypatch.setattr(visual_pipeline, "find_motion_timestamps", lambda path, video_meta, config: [])
    monkeypatch.setattr(visual_pipeline, "read_unique_frames", lambda path, video_meta, timestamps, config: frames)
    monkeypatch.setattr(visual_pipeline, "save_results", lambda output, upload_id, detections: {"json": "out.json", "csv": "out.csv"})
    monkeypatch.setattr(visual_pipeline, "save_blurred_thumbnails", lambda *args: [])

    result = visual_pipeline.run_visual_pii_pipeline("sample.mp4", "upload-1", tmp_path, backend=backend)

    assert backend.received == frames
    assert result["sampled_frame_count"] == 1
    assert result["ocr_hit_count"] == 0


def test_colab_worker_registers_visual_ocr_pipeline_and_artifacts():
    pipeline_source = (COLAB_DIR / "garim_pipeline.py").read_text(encoding="utf-8")
    worker_source = (COLAB_DIR / "garim_colab_worker.py").read_text(encoding="utf-8")

    assert "VisualOCRAnalyzer()," in pipeline_source
    assert 'ctx.results.get("visual_ocr", {})' in worker_source
    assert '("visual_ocr_json", "application/json", "json")' in worker_source
    assert '("visual_ocr_csv", "text/csv", "csv")' in worker_source
