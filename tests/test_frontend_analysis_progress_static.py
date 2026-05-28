from pathlib import Path


PROGRESS_PAGE = Path("frontend/src/pages/garim/AnalysisProgress.jsx")
UPLOAD_PAGE = Path("frontend/src/pages/garim/Upload.jsx")
API_FILE = Path("frontend/src/utils/api.js")


def test_analysis_progress_uses_live_job_polling():
    source = PROGRESS_PAGE.read_text(encoding="utf-8")

    assert "getAnalysisJob" in source
    assert "useLocation" in source
    assert "useSearchParams" in source
    assert "setInterval" in source
    assert "family_picnic_2026.mp4" not in source
    assert 'width: "46%"' not in source
    assert "46%" not in source


def test_upload_navigates_with_job_context():
    source = UPLOAD_PAGE.read_text(encoding="utf-8")

    assert "jobId" in source
    assert "uploadId" in source
    assert "fileName" in source
    assert "fileSize" in source
    assert "/analysis-progress?jobId=" in source


def test_api_exposes_analysis_cancel():
    source = API_FILE.read_text(encoding="utf-8")

    assert "export async function cancelAnalysisJob" in source
    assert "/analysis/jobs/${jobId}/cancel" in source
